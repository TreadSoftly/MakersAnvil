"""Prepare contained app-owned job records without executing a maker workflow."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.execution_request import ExecutionRequestService
from makers_anvil_backend.services.job_records import (
    JOB_ID_PATTERN,
    JOB_SAFETY_FLAGS,
    PREVIEW_ID_PATTERN,
    REQUIRED_WORKSPACE_DIRECTORIES,
    atomic_write_json,
    initial_cancellation_record,
    job_id_for_preview,
    requested_cancellation_record,
    valid_cancellation_record,
    valid_id_label,
    valid_intent,
    valid_job_record,
)
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[4]


class JobWorkspaceError(ValueError):
    """Raised when job preparation or cancellation would violate containment."""


class JobWorkspaceService:
    """Create and read path-redacted prepared jobs plus cancellation requests."""

    def __init__(
        self,
        root: Path | None = None,
        workspace_config: WorkspaceConfigService | None = None,
        execution_request: ExecutionRequestService | None = None,
    ) -> None:
        """Bind app-owned storage and the read-only request-preview source."""

        self.root = root or ROOT
        self.workspace_config = workspace_config or WorkspaceConfigService(self.root)
        self.execution_request = execution_request or ExecutionRequestService(self.root)
        self.policy_path = self.root / "config" / "job_workspace_policy.json"

    def policy(self) -> dict[str, Any]:
        """Validate one-route storage, local actions, and constant-false unsafe effects."""

        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise JobWorkspaceError("job workspace policy must be a structured record")
        if policy.get("schemaVersion") != "makers-anvil.config.job-workspace-policy.v1":
            raise JobWorkspaceError("job workspace policy schema version is not supported")
        if policy.get("mode") != "contained-local-preparation":
            raise JobWorkspaceError("job workspace policy must remain contained local preparation")
        if policy.get("scope") != {"routeId": "mesh-to-toolpath", "maxPreparedJobsPerRequest": 1}:
            raise JobWorkspaceError("job workspace scope must remain one prepared job for mesh-to-toolpath")
        storage = policy.get("storage")
        workspace_directories = storage.get("workspaceDirectories") if isinstance(storage, dict) else None
        if (
            not isinstance(storage, dict)
            or storage.get("jobsDirectory") != "jobs"
            or storage.get("manifestFileName") != "job.json"
            or storage.get("cancellationFileName") != "cancellation.json"
            or not isinstance(workspace_directories, list)
            or set(workspace_directories) != REQUIRED_WORKSPACE_DIRECTORIES
            or len(workspace_directories) != len(REQUIRED_WORKSPACE_DIRECTORIES)
        ):
            raise JobWorkspaceError("job workspace storage must remain inside the app-owned jobs directory")
        expected_actions = {
            "preparationEnabled": True,
            "cancellationRequestEnabled": True,
            "apiMutationEnabled": False,
            "browserMutationEnabled": False,
        }
        if policy.get("localActions") != expected_actions:
            raise JobWorkspaceError("only explicit local preparation and cancellation scripts may mutate job records")
        safety = policy.get("safety")
        if not isinstance(safety, dict) or set(safety) != JOB_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise JobWorkspaceError("job workspace policy cannot persist executable intent, authorize, resolve, execute, signal, or prove")
        request_scope = self.execution_request.execution_request_policy()["scope"]["routeId"]
        if request_scope != policy["scope"]["routeId"]:
            raise JobWorkspaceError("job workspace and execution request policies must use the same route")
        return policy

    def policy_response(self) -> dict[str, Any]:
        """Return public policy with logical storage and explicit script boundaries."""

        policy = self.policy()
        return {
            **policy,
            "jobsPath": self.workspace_config.logical_runtime_path(policy["storage"]["jobsDirectory"]),
            "boundaries": [
                "Only explicit local scripts may prepare or cancel a job record.",
                "Prepared jobs contain logical references and empty app-owned directories only.",
                "Cancellation records never claim that a process received or honored a signal.",
                "The browser and HTTP API remain read-only.",
            ],
        }

    def catalog(self) -> dict[str, Any]:
        """Read valid prepared jobs and cancellation state without exposing private paths."""

        policy = self.policy()
        jobs_root = self._jobs_root(policy)
        jobs: list[dict[str, Any]] = []
        invalid_job_count = 0
        if jobs_root.exists():
            for job_root in sorted(jobs_root.iterdir()):
                if job_root.is_symlink() or not job_root.is_dir() or not JOB_ID_PATTERN.fullmatch(job_root.name):
                    invalid_job_count += 1
                    continue
                try:
                    self._validate_workspace_paths(job_root, policy)
                    if not self._workspace_complete(job_root, policy):
                        raise JobWorkspaceError("prepared job workspace is incomplete")
                    job = json.loads((job_root / policy["storage"]["manifestFileName"]).read_text(encoding="utf-8"))
                    cancellation = json.loads((job_root / "control" / policy["storage"]["cancellationFileName"]).read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError, JobWorkspaceError):
                    invalid_job_count += 1
                    continue
                if not valid_job_record(job, policy) or not valid_cancellation_record(cancellation, job["id"]):
                    invalid_job_count += 1
                    continue
                jobs.append({"record": job, "cancellation": cancellation})

        requested_count = sum(job["cancellation"]["state"] == "requested" for job in jobs)
        return {
            "schemaVersion": "makers-anvil.api.job-workspace-catalog.v1",
            "claimState": "staged" if invalid_job_count == 0 else "failed",
            "mode": policy["mode"],
            "jobsPath": self.workspace_config.logical_runtime_path(policy["storage"]["jobsDirectory"]),
            "recordsRootExists": jobs_root.exists(),
            "summary": {
                "preparedJobCount": len(jobs),
                "cancellationRequestedCount": requested_count,
                "invalidJobCount": invalid_job_count,
                "executionReadyCount": 0,
            },
            "jobs": jobs,
            "safety": policy["safety"],
            "actions": {
                "prepare": {
                    "claimState": "staged",
                    "enabledInApi": False,
                    "script": "python scripts/prepare_job.py --request-preview-id <id>",
                },
                "cancel": {
                    "claimState": "staged",
                    "enabledInApi": False,
                    "script": "python scripts/request_job_cancel.py --job-id <id>",
                },
                "execute": {"claimState": "blocked", "enabledInApi": False},
            },
        }

    def prepare(self, request_preview_id: str, preview_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create one idempotent contained workspace from an existing request preview."""

        if not PREVIEW_ID_PATTERN.fullmatch(request_preview_id):
            raise JobWorkspaceError("request preview id has an invalid format")
        policy = self.policy()
        previews = preview_snapshot if preview_snapshot is not None else self.execution_request.preview_catalog()
        preview = next((item for item in previews["previews"] if item["id"] == request_preview_id), None)
        if (
            preview is None
            or not valid_id_label(preview.get("route"), policy["scope"]["routeId"])
            or not valid_id_label(preview.get("operation"))
            or not valid_intent(preview.get("intent"))
            or preview.get("authorization") != {"required": True, "accepted": False, "actor": None, "acceptedAt": None}
        ):
            raise JobWorkspaceError("request preview is unavailable or outside the job workspace scope")

        job_id = job_id_for_preview(request_preview_id)
        job_root = self._job_root(job_id, policy)
        self._validate_workspace_paths(job_root, policy)
        manifest_path = job_root / policy["storage"]["manifestFileName"]
        cancellation_path = job_root / "control" / policy["storage"]["cancellationFileName"]
        if manifest_path.exists():
            if not self._workspace_complete(job_root, policy):
                raise JobWorkspaceError("existing job workspace is incomplete or invalid")
            return self._existing_job(manifest_path, cancellation_path, request_preview_id, policy)

        for directory in policy["storage"]["workspaceDirectories"]:
            (job_root / directory).mkdir(parents=True, exist_ok=True)
        logical_root = self.workspace_config.logical_runtime_path(Path("jobs") / job_id)
        job = {
            "schemaVersion": "makers-anvil.runtime.job-workspace.v1",
            "id": job_id,
            "claimState": "staged",
            "createdUtc": datetime.now(UTC).isoformat(),
            "requestPreviewId": request_preview_id,
            "route": dict(preview["route"]),
            "operation": dict(preview["operation"]),
            "intent": preview["intent"],
            "authorization": {"required": True, "accepted": False},
            "lifecycle": {
                "state": "prepared",
                "processId": None,
                "startedAt": None,
                "completedAt": None,
            },
            "workspace": {
                "logicalRoot": logical_root,
                "absolutePathExposed": False,
                "directories": [
                    {"id": name, "logicalPath": f"{logical_root}/{name}"}
                    for name in policy["storage"]["workspaceDirectories"]
                ],
            },
            "cancellationRecord": f"{logical_root}/control/{policy['storage']['cancellationFileName']}",
            "safety": dict(policy["safety"]),
        }
        cancellation = initial_cancellation_record(job_id)
        atomic_write_json(cancellation_path, cancellation)
        # The manifest is the completion marker. Catalog readers ignore a
        # partially-created directory until this final atomic write succeeds.
        atomic_write_json(manifest_path, job)
        return {"record": job, "cancellation": cancellation}

    def request_cancellation(self, job_id: str) -> dict[str, Any]:
        """Record cancellation intent without signaling or claiming a running process."""

        policy = self.policy()
        job_root = self._job_root(job_id, policy)
        self._validate_workspace_paths(job_root, policy)
        if not self._workspace_complete(job_root, policy):
            raise JobWorkspaceError("prepared job workspace is incomplete")
        manifest_path = job_root / policy["storage"]["manifestFileName"]
        cancellation_path = job_root / "control" / policy["storage"]["cancellationFileName"]
        try:
            job = json.loads(manifest_path.read_text(encoding="utf-8"))
            cancellation = json.loads(cancellation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise JobWorkspaceError("prepared job and cancellation records are required") from exc
        if not valid_job_record(job, policy) or not valid_cancellation_record(cancellation, job_id):
            raise JobWorkspaceError("prepared job or cancellation record is invalid")
        if cancellation["state"] == "requested":
            return cancellation
        cancellation = requested_cancellation_record(cancellation)
        atomic_write_json(cancellation_path, cancellation)
        return cancellation

    def _existing_job(
        self,
        manifest_path: Path,
        cancellation_path: Path,
        request_preview_id: str,
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Return an existing coherent job so preparation is safely idempotent."""

        try:
            job = json.loads(manifest_path.read_text(encoding="utf-8"))
            cancellation = json.loads(cancellation_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise JobWorkspaceError("existing job workspace is incomplete or invalid") from exc
        if (
            job.get("requestPreviewId") != request_preview_id
            or not valid_job_record(job, policy)
            or not valid_cancellation_record(cancellation, job["id"])
        ):
            raise JobWorkspaceError("existing job workspace does not match the request preview")
        return {"record": job, "cancellation": cancellation}

    def _jobs_root(self, policy: dict[str, Any]) -> Path:
        """Resolve the policy-owned jobs directory inside private runtime storage."""

        relative = Path(policy["storage"]["jobsDirectory"])
        if relative != Path("jobs"):
            raise JobWorkspaceError("jobs directory must remain the app-owned jobs root")
        return self.workspace_config.runtime_path(relative)

    def _job_root(self, job_id: str, policy: dict[str, Any]) -> Path:
        """Resolve one validated job id without permitting traversal or symlink escape."""

        if not JOB_ID_PATTERN.fullmatch(job_id):
            raise JobWorkspaceError("job id has an invalid format")
        root = self._jobs_root(policy) / job_id
        if root.is_symlink():
            raise JobWorkspaceError("job workspace cannot be a symbolic link")
        return root

    @staticmethod
    def _validate_workspace_paths(job_root: Path, policy: dict[str, Any]) -> None:
        """Reject symlinked or non-directory children before any contained record access."""

        for name in policy["storage"]["workspaceDirectories"]:
            child = job_root / name
            if child.is_symlink() or (child.exists() and not child.is_dir()):
                raise JobWorkspaceError("job workspace children must be app-owned directories")
        record_paths = [
            job_root / policy["storage"]["manifestFileName"],
            job_root / "control" / policy["storage"]["cancellationFileName"],
        ]
        if any(path.is_symlink() for path in record_paths):
            raise JobWorkspaceError("job workspace records cannot be symbolic links")

    @staticmethod
    def _workspace_complete(job_root: Path, policy: dict[str, Any]) -> bool:
        """Require every configured workspace child to exist as a real directory."""

        return all(
            (job_root / name).is_dir() and not (job_root / name).is_symlink()
            for name in policy["storage"]["workspaceDirectories"]
        )
