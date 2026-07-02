"""Purpose: Execute one authorized built-in STL preflight in app-owned containment.

Used by: ``AppStateService`` and the guarded contained-execution API routes.
Inputs: One authorized app-owned STL intake id plus explicit local authorization.
Outputs: Execution lifecycle, cooperative cancellation, report, log, proof, and audit.
Side effects: Reads quarantine content and writes only app-owned execution artifacts.
Safety: No original path, external command/process/tool, archive, or software change exists.
Failure behavior: Scope, consent, content, containment, concurrency, and corruption fail closed.
Related proof: ``tests/test_contained_execution.py`` and contained-execution schemas.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.execution_audit import (
    EXECUTION_ID_PATTERN,
    ExecutionAuditError,
    ExecutionAuditService,
)
from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService
from makers_anvil_backend.services.job_records import atomic_write_json
from makers_anvil_backend.services.local_request_guard import LocalRequestContext, LocalRequestGuard
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = application_root()
POLICY_SAFETY_FIELDS = {
    "originalSourcePathStored", "originalSourceModified", "archiveExtractionEnabled",
    "externalCommandConstructed", "externalProcessStarted", "externalToolLaunched",
    "softwareChangeEnabled", "outputOpenEnabled",
}
RECORD_FIELDS = {
    "schemaVersion", "id", "claimState", "createdUtc", "updatedUtc", "route",
    "operation", "source", "authorization", "lifecycle", "workspace", "proof", "safety",
}
CANCELLATION_FIELDS = {
    "schemaVersion", "executionId", "claimState", "state", "requestId",
    "requestedUtc", "observedUtc", "cooperative", "processSignalSent",
}
LIFECYCLE_STATES = {"authorized", "running", "completed", "cancelled", "failed"}
TERMINAL_STATES = {"completed", "cancelled", "failed"}


class ContainedExecutionError(ValueError):
    """Purpose: Carry stable HTTP-safe contained-execution rejection details.

    Inputs: HTTP status, machine code, and reviewed path-free message.
    Outputs: Typed exception exposing ``status`` and ``code``.
    How it works: Stores bounded response metadata before initializing ``ValueError``.
    Side effects: None until raised and handled by the API facade.
    Failure behavior: Invalid caller constants remain visible programming defects.
    Safety: Messages never include private paths, file bytes, tokens, or stack data.
    Example: Duplicate execution authorization raises status 409.
    Related proof: API error-mapping and service rejection tests.
    """

    def __init__(self, status: int, code: str, message: str) -> None:
        """Purpose: Initialize one stable execution rejection.

        Inputs: HTTP status, snake-case code, and path-free diagnostic.
        Outputs: Initialized exception; constructors return ``None``.
        How it works: Saves public fields and delegates message storage.
        Side effects: None.
        Failure behavior: Values are not silently normalized.
        Safety: Callers must use reviewed messages without private evidence.
        Example: API reads ``status`` and ``code`` after catching.
        Related proof: ``tests/test_contained_execution.py``.
        """

        super().__init__(message)
        self.status = status
        self.code = code


class ContainedExecutionService:
    """Purpose: Orchestrate one truthful cancellable STL preflight operation.

    Inputs: Portable storage, authorized intake, shared request guard, audit, and clock.
    Outputs: Policy/catalog plus authorized, running, terminal, and proof records.
    How it works: Validates consent, streams/hash-checks STL, writes report/log/proof atomically.
    Side effects: Creates only one execution workspace and its declared artifacts.
    Failure behavior: Invalid or concurrent work raises typed fail-closed errors.
    Safety: This is partial route preflight, not slicing, G-code, or external tool execution.
    Example: An app-owned binary STL produces a verified preflight report and proof.
    Related proof: ``tests/test_contained_execution.py``.
    """

    def __init__(
        self,
        root: Path | None = None,
        *,
        workspace_config: WorkspaceConfigService,
        intake_catalog: IntakeCatalogService,
        request_guard: LocalRequestGuard,
        audit: ExecutionAuditService | None = None,
        clock: Callable[[], datetime] | None = None,
        chunk_hook: Callable[[str, int], None] | None = None,
    ) -> None:
        """Purpose: Bind policy and shared dependencies without creating runtime data.

        Inputs: Application root, portable workspace, intake catalog, guard, audit, clock, hook.
        Outputs: Initialized service with a one-execution in-process concurrency lock.
        How it works: Stores focused dependencies and initializes no active execution.
        Side effects: Allocates thread synchronization state only.
        Failure behavior: Dependency construction errors propagate before use.
        Safety: The test hook observes generated ids/counts only and is absent in production.
        Example: App state injects the same workspace, intake catalog, and request guard.
        Related proof: Dependency-sharing and concurrency tests.
        """

        self.root = (root or application_root()).resolve()
        self.workspace_config = workspace_config
        self.intake_catalog = intake_catalog
        self.request_guard = request_guard
        self.clock = clock or (lambda: datetime.now(UTC))
        self.audit = audit or ExecutionAuditService(workspace_config=workspace_config, clock=self.clock)
        self.chunk_hook = chunk_hook
        self.policy_path = self.root / "config" / "contained_execution_policy.json"
        self._lock = threading.RLock()
        self._active_execution_id: str | None = None

    def policy(self) -> dict[str, Any]:
        """Purpose: Strictly validate single-operation execution policy and boundaries.

        Inputs: Committed ``config/contained_execution_policy.json``.
        Outputs: Validated policy mapping used by all operations.
        How it works: Checks exact identities, scope, storage, limits, actions, and safety.
        Side effects: Reads one committed UTF-8 JSON file.
        Failure behavior: Missing, malformed, broadened, or weakened policy raises.
        Safety: Scope remains built-in STL preflight with no external execution effects.
        Example: Adding ``.zip`` or concurrent slot two causes validation failure.
        Related proof: Policy schema and mutation tests.
        """

        try:
            policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution policy is unavailable.") from exc
        if not isinstance(policy, dict) or set(policy) != {"schemaVersion", "claimState", "mode", "scope", "storage", "limits", "actions", "safety"}:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution policy shape is invalid.")
        if policy["schemaVersion"] != "makers-anvil.config.contained-execution.v1" or policy["claimState"] != "staged" or policy["mode"] != "built-in-cooperative-single-operation":
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution policy identity is invalid.")
        expected_scope = {
            "routeId": "mesh-to-toolpath", "operationId": "built-in-stl-preflight",
            "allowedKind": "mesh", "allowedExtensions": [".stl"], "maxConcurrentExecutions": 1,
        }
        if policy["scope"] != expected_scope:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution scope must remain one built-in STL preflight.")
        expected_storage = {
            "executionsDirectory": "executions", "recordFileName": "execution.json",
            "cancellationFileName": "cancellation.json", "executionLogFileName": "execution.log",
            "reportFileName": "stl-preflight-report.json", "proofFileName": "execution-proof.json",
            "auditDirectory": "logs/audit",
        }
        if policy["storage"] != expected_storage:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution storage policy is invalid.")
        if policy["limits"] != {"maxSourceBytes": 536870912, "readChunkBytes": 1048576, "maxArtifactBytes": 262144}:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution limits are invalid.")
        expected_actions = {
            "authorizationEnabled": True, "executionEnabled": True,
            "cooperativeCancellationEnabled": True, "apiMutationEnabled": True,
            "browserMutationEnabled": True, "verifiedArtifactReadEnabled": True,
        }
        if policy["actions"] != expected_actions:
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution actions are invalid.")
        safety = policy["safety"]
        if not isinstance(safety, dict) or set(safety) != POLICY_SAFETY_FIELDS or any(value is not False for value in safety.values()):
            raise ContainedExecutionError(500, "execution_policy_invalid", "Contained execution cannot enable external or source effects.")
        return policy

    def policy_response(self) -> dict[str, Any]:
        """Purpose: Expose execution scope, logical storage, and honest partial-route boundary.

        Inputs: Validated committed policy.
        Outputs: Public path-redacted policy response.
        How it works: Adds logical storage and explicit boundary statements.
        Side effects: Reads policy only.
        Failure behavior: Policy errors propagate rather than enabling controls.
        Safety: Clearly distinguishes STL preflight from slicing and toolpath generation.
        Example: Frontend uses allowedExtensions and operation id for authorization.
        Related proof: API policy and frontend wiring tests.
        """

        policy = self.policy()
        return {
            **policy,
            "executionsPath": self.workspace_config.logical_runtime_path(policy["storage"]["executionsDirectory"]),
            "endpoints": {
                "authorize": "/api/executions/authorizations",
                "runTemplate": "/api/executions/{executionId}/run",
                "cancelTemplate": "/api/executions/{executionId}/cancel",
                "artifactTemplate": "/api/executions/{executionId}/artifacts/{artifactKind}",
            },
            "boundaries": [
                "This executes only Makers Anvil's built-in STL preflight stage.",
                "It does not slice, generate G-code, launch a tool, or complete mesh-to-toolpath.",
                "Only an explicitly authorized app-owned STL copy can be read.",
                "Cancellation is cooperative and sends no operating-system process signal.",
            ],
        }

    def catalog(self) -> dict[str, Any]:
        """Purpose: Return valid execution, cancellation, audit, and proof truth.

        Inputs: App-owned execution directories and strict stored records.
        Outputs: Path-redacted newest-first execution catalog and state counts.
        How it works: Validates each directory/record before joining cancellation and audit.
        Side effects: Reads app-owned execution data only.
        Failure behavior: Invalid entries are counted and never exposed as usable executions.
        Safety: Private paths, source bytes, and output file contents remain absent.
        Example: Completed preflight shows proof available and five audit events.
        Related proof: Catalog corruption and privacy tests.
        """

        policy = self.policy()
        root = self._executions_root(policy)
        executions: list[dict[str, Any]] = []
        invalid_count = 0
        if root.exists():
            if root.is_symlink() or not root.is_dir():
                invalid_count += 1
            else:
                for execution_root in sorted(root.iterdir()):
                    if execution_root.is_symlink() or not execution_root.is_dir() or not EXECUTION_ID_PATTERN.fullmatch(execution_root.name):
                        invalid_count += 1
                        continue
                    record_path = execution_root / policy["storage"]["recordFileName"]
                    cancellation_path = execution_root / "control" / policy["storage"]["cancellationFileName"]
                    try:
                        record = json.loads(record_path.read_text(encoding="utf-8"))
                        cancellation = json.loads(cancellation_path.read_text(encoding="utf-8"))
                        self._validate_record(record, policy)
                        self._validate_cancellation(cancellation, record["id"])
                        audit = self.audit.history(record["id"])
                    except (OSError, json.JSONDecodeError, ValueError):
                        invalid_count += 1
                        continue
                    executions.append({"record": record, "cancellation": cancellation, "audit": audit})
        executions.sort(key=lambda item: item["record"]["createdUtc"], reverse=True)
        states = {state: sum(item["record"]["lifecycle"]["state"] == state for item in executions) for state in LIFECYCLE_STATES}
        return {
            "schemaVersion": "makers-anvil.api.contained-execution-catalog.v1",
            "claimState": "staged" if invalid_count == 0 else "failed",
            "mode": policy["mode"],
            "scope": policy["scope"],
            "executionsPath": self.workspace_config.logical_runtime_path(policy["storage"]["executionsDirectory"]),
            "summary": {
                "executionCount": len(executions), "invalidExecutionCount": invalid_count,
                "authorizedCount": states["authorized"], "runningCount": states["running"],
                "completedCount": states["completed"], "cancelledCount": states["cancelled"],
                "failedCount": states["failed"],
                "proofCount": sum(item["record"]["proof"] is not None for item in executions),
            },
            "executions": executions,
            "safety": policy["safety"],
            "actions": {
                "authorize": {"enabledInApi": True, "endpoint": "/api/executions/authorizations"},
                "run": {"enabledInApi": True, "endpointTemplate": "/api/executions/{executionId}/run"},
                "cancel": {"enabledInApi": True, "endpointTemplate": "/api/executions/{executionId}/cancel"},
                "viewArtifact": {"enabledInApi": True, "endpointTemplate": "/api/executions/{executionId}/artifacts/{artifactKind}", "allowedKinds": ["report", "proof"]},
                "openOutput": {"enabledInApi": False},
            },
        }

    def artifact(self, execution_id: str, artifact_kind: str) -> dict[str, Any]:
        """Purpose: Return one verified proof artifact as bounded in-app JSON.

        Inputs: Generated execution id and the closed artifact kind ``report`` or ``proof``.
        Outputs: Path-redacted JSON content plus explicit integrity and safety evidence.
        How it works: Loads the strict terminal record, derives a fixed path, bounds and parses bytes, then rechecks proof binding.
        Side effects: Reads one execution marker and one app-owned JSON artifact only.
        Failure behavior: Unknown kinds, non-terminal work, symlinks, drift, oversize, or malformed JSON fail closed.
        Safety: Browser input cannot select a filename; no physical path, process, tool, or output-open effect exists.
        Example: ``artifact(execution_id, 'report')`` returns the hash-matched STL preflight report.
        Related proof: ``tests/test_contained_execution.py`` and dynamic API route tests.
        """

        policy = self.policy()
        if artifact_kind not in {"report", "proof"}:
            raise ContainedExecutionError(404, "execution_artifact_not_found", "That execution artifact is not available.")
        record = self._load_record(execution_id, policy)
        if record["lifecycle"]["state"] not in {"completed", "failed"} or not isinstance(record["proof"], dict):
            raise ContainedExecutionError(409, "execution_artifact_not_ready", "Verified execution artifacts are not ready yet.")
        file_name = policy["storage"]["reportFileName" if artifact_kind == "report" else "proofFileName"]
        artifact_path = self._execution_root(execution_id, policy) / "outputs" / file_name
        if artifact_path.parent.is_symlink() or artifact_path.is_symlink() or not artifact_path.is_file():
            raise ContainedExecutionError(404, "execution_artifact_not_found", "The verified execution artifact is unavailable.")
        try:
            size = artifact_path.stat().st_size
            if size <= 0 or size > policy["limits"]["maxArtifactBytes"]:
                raise ContainedExecutionError(413, "execution_artifact_too_large", "The execution artifact exceeds the in-app viewing limit.")
            content_bytes = artifact_path.read_bytes()
            if len(content_bytes) != size or len(content_bytes) > policy["limits"]["maxArtifactBytes"]:
                raise ContainedExecutionError(422, "execution_artifact_changed", "The execution artifact changed during verification.")
            content = json.loads(content_bytes.decode("utf-8"))
        except ContainedExecutionError:
            raise
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContainedExecutionError(422, "execution_artifact_invalid", "The execution artifact is invalid.") from exc
        if not isinstance(content, dict) or content.get("executionId") != execution_id:
            raise ContainedExecutionError(422, "execution_artifact_invalid", "The execution artifact identity is invalid.")
        digest = hashlib.sha256(content_bytes).hexdigest()
        if artifact_kind == "report":
            expected = record["proof"]["report"]
            try:
                self._validate_report(content, record)
            except ValueError as exc:
                raise ContainedExecutionError(422, "execution_artifact_invalid", "The execution report shape is invalid.") from exc
            if not hmac.compare_digest(digest, expected["sha256"]):
                raise ContainedExecutionError(422, "execution_artifact_integrity_failed", "The report no longer matches its execution proof.")
            logical_path = expected["logicalPath"]
            digest_matched = True
        else:
            if content != record["proof"] or content.get("schemaVersion") != "makers-anvil.runtime.execution-proof.v1":
                raise ContainedExecutionError(422, "execution_artifact_integrity_failed", "The proof file no longer matches the execution record.")
            logical_path = f"{record['workspace']['logicalRoot']}/outputs/{file_name}"
            digest_matched = True
        return {
            "schemaVersion": "makers-anvil.api.contained-artifact.v1",
            "claimState": record["claimState"],
            "mode": "verified-in-app-json",
            "executionId": execution_id,
            "artifactKind": artifact_kind,
            "title": "STL preflight report" if artifact_kind == "report" else "Execution proof",
            "logicalPath": logical_path,
            "content": content,
            "integrity": {"recordMatched": True, "sha256": digest, "digestMatched": digest_matched, "sizeBytes": len(content_bytes)},
            "safety": {"readOnly": True, "physicalPathExposed": False, "outputOpened": False, "externalProcessStarted": False, "externalToolLaunched": False},
        }

    def authorize(self, payload: dict[str, Any], context: LocalRequestContext) -> dict[str, Any]:
        """Purpose: Record explicit consent and prepare one contained execution workspace.

        Inputs: Exact intake/route/operation/accepted fields and guarded local context.
        Outputs: Authorized execution with cancellation and first two audit events.
        How it works: Validates app-owned intake, uniqueness, consent, then writes marker last.
        Side effects: Creates one execution workspace, cancellation record, audits, and manifest.
        Failure behavior: Invalid consent/scope/content/duplicate/storage raises typed error.
        Safety: No original path, source modification, command, process, or tool is used.
        Example: User authorizes built-in preflight for one copied ``part.stl``.
        Related proof: Authorization, duplicate, origin, and rollback-boundary tests.
        """

        self.request_guard.validate(context)
        policy = self.policy()
        expected_keys = {"intakeId", "routeId", "operationId", "accepted"}
        if not isinstance(payload, dict) or set(payload) != expected_keys or payload.get("accepted") is not True:
            raise ContainedExecutionError(400, "execution_authorization_invalid", "Execution authorization requires the exact accepted request fields.")
        if payload.get("routeId") != policy["scope"]["routeId"] or payload.get("operationId") != policy["scope"]["operationId"]:
            raise ContainedExecutionError(422, "execution_scope_rejected", "Only the built-in STL preflight operation is enabled.")
        try:
            intake = self.intake_catalog.authorized_record(payload.get("intakeId"))
            self.intake_catalog.authorized_content_path(intake)
        except (IntakeCatalogError, TypeError) as exc:
            raise ContainedExecutionError(422, "execution_source_rejected", "The authorized app-owned intake is unavailable.") from exc
        source = intake["source"]
        if source["kind"] != policy["scope"]["allowedKind"] or source["extension"] not in policy["scope"]["allowedExtensions"]:
            raise ContainedExecutionError(415, "execution_source_type_rejected", "Only an authorized app-owned STL can run this preflight.")
        if source["sizeBytes"] > policy["limits"]["maxSourceBytes"]:
            raise ContainedExecutionError(413, "execution_source_too_large", "The authorized STL exceeds the execution size limit.")
        if any(item["record"]["source"]["intakeId"] == intake["id"] for item in self.catalog()["executions"]):
            raise ContainedExecutionError(409, "execution_already_exists", "This intake already has a contained execution record.")

        execution_id = f"execution-{uuid4().hex}"
        execution_root = self._execution_root(execution_id, policy)
        for directory in ("control", "working", "logs", "outputs"):
            (execution_root / directory).mkdir(parents=True, exist_ok=False)
        now = self._utc_now().isoformat()
        logical_root = f"makers-anvil-data://user/executions/{execution_id}"
        cancellation = self._initial_cancellation(execution_id)
        record = {
            "schemaVersion": "makers-anvil.runtime.contained-execution.v1",
            "id": execution_id,
            "claimState": "staged",
            "createdUtc": now,
            "updatedUtc": now,
            "route": {"id": "mesh-to-toolpath", "label": "Mesh to toolpath"},
            "operation": {"id": "built-in-stl-preflight", "label": "Built-in STL preflight", "executor": "makers-anvil-built-in"},
            "source": {
                "intakeId": intake["id"], "displayName": source["displayName"],
                "extension": source["extension"], "kind": source["kind"],
                "sizeBytes": source["sizeBytes"], "sha256": intake["storage"]["sha256"],
                "logicalReference": intake["storage"]["logicalReference"],
            },
            "authorization": {"required": True, "accepted": True, "actor": "local-user", "acceptedUtc": now},
            "lifecycle": {"state": "authorized", "startedUtc": None, "completedUtc": None, "failureCode": None},
            "workspace": {"logicalRoot": logical_root, "absolutePathExposed": False},
            "proof": None,
            "safety": dict(policy["safety"]),
        }
        self._validate_record(record, policy)
        self._validate_cancellation(cancellation, execution_id)
        atomic_write_json(execution_root / "control" / policy["storage"]["cancellationFileName"], cancellation)
        self.audit.append(execution_id, "request-created", "accepted")
        self.audit.append(execution_id, "authorization-recorded", "accepted")
        atomic_write_json(execution_root / policy["storage"]["recordFileName"], record)
        return {"schemaVersion": "makers-anvil.api.contained-execution-result.v1", "claimState": "staged", "record": record, "cancellation": cancellation, "audit": self.audit.history(execution_id)}

    def run(self, execution_id: str, context: LocalRequestContext) -> dict[str, Any]:
        """Purpose: Run the authorized built-in preflight and capture real output proof.

        Inputs: Generated execution id and guarded local request context.
        Outputs: Terminal execution, cancellation, audit, report/log/proof references.
        How it works: Claims one slot, streams/hash-checks source, writes artifacts, finalizes.
        Side effects: Reads app-owned STL and writes app-owned report, log, proof, audit, state.
        Failure behavior: Invalid state/concurrency/corruption fails; failed STL records honest proof.
        Safety: No external command/process/tool or original user source is touched.
        Example: Valid binary STL finishes completed with passing proof.
        Related proof: Success, invalid-format, cancellation, and concurrency tests.
        """

        self.request_guard.validate(context)
        policy = self.policy()
        with self._lock:
            if self._active_execution_id is not None:
                raise ContainedExecutionError(409, "execution_slot_busy", "The single contained execution slot is already in use.")
            record = self._load_record(execution_id, policy)
            if record["lifecycle"]["state"] != "authorized":
                raise ContainedExecutionError(409, "execution_state_rejected", "A terminal or already-started execution cannot start.")
            self._active_execution_id = execution_id
        try:
            if self._cancellation_requested(execution_id, policy):
                return self._finish_cancelled(record, policy)
            started = self._utc_now().isoformat()
            record["updatedUtc"] = started
            record["lifecycle"] = {"state": "running", "startedUtc": started, "completedUtc": None, "failureCode": None}
            atomic_write_json(self._record_path(execution_id, policy), record)
            self.audit.append(execution_id, "execution-started", "running")
            intake = self.intake_catalog.authorized_record(record["source"]["intakeId"])
            source_path = self.intake_catalog.authorized_content_path(intake)
            inspection = self._inspect_source(execution_id, source_path, record, policy)
            if inspection["cancelled"]:
                return self._finish_cancelled(record, policy)
            return self._finish_with_proof(record, inspection, policy)
        except ContainedExecutionError:
            raise
        except (OSError, IntakeCatalogError, ExecutionAuditError, ValueError) as exc:
            self._mark_operational_failure(execution_id, policy, "execution_io_failed")
            raise ContainedExecutionError(500, "execution_failed", "Contained STL preflight could not complete.") from exc
        finally:
            with self._lock:
                self._active_execution_id = None

    def cancel(self, execution_id: str, context: LocalRequestContext) -> dict[str, Any]:
        """Purpose: Request cooperative cancellation and finalize idle authorized work.

        Inputs: Generated execution id and guarded same-origin context.
        Outputs: Current record, requested/observed cancellation, and audit history.
        How it works: Atomically records intent; authorized work cancels immediately.
        Side effects: Replaces cancellation/state JSON and may append one cancel event.
        Failure behavior: Terminal/invalid executions reject repeated state changes.
        Safety: Sends no process signal and changes no source or external resource.
        Example: Cancel before Run moves authorized execution directly to cancelled.
        Related proof: Pre-start, in-flight, terminal, and idempotency tests.
        """

        self.request_guard.validate(context)
        policy = self.policy()
        record = self._load_record(execution_id, policy)
        state = record["lifecycle"]["state"]
        if state in TERMINAL_STATES:
            raise ContainedExecutionError(409, "execution_state_rejected", "A terminal execution cannot be cancelled.")
        path = self._cancellation_path(execution_id, policy)
        cancellation = self._load_cancellation(execution_id, policy)
        if cancellation["state"] == "not-requested":
            cancellation = {
                **cancellation,
                "state": "requested",
                "requestId": f"execution-cancel-{uuid4().hex}",
                "requestedUtc": self._utc_now().isoformat(),
            }
            atomic_write_json(path, cancellation)
        if state == "authorized":
            return self._finish_cancelled(record, policy)
        return {"schemaVersion": "makers-anvil.api.contained-execution-result.v1", "claimState": "staged", "record": record, "cancellation": cancellation, "audit": self.audit.history(execution_id)}

    def _inspect_source(self, execution_id: str, source_path: Path, record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Stream bytes once for size, digest, STL signature, and cancellation.

        Inputs: Execution id, private app-owned path, validated record, and limits.
        Outputs: Bounded inspection facts with no retained source content.
        How it works: Hashes chunks, retains small prefix/suffix windows, checks cancellation.
        Side effects: Reads authorized app-owned content only and calls an optional test hook.
        Failure behavior: I/O failures propagate to operational failure handling.
        Safety: No parsing library, archive extraction, file copy, path response, or write occurs.
        Example: Binary STL size equals ``84 + triangleCount * 50``.
        Related proof: Binary/ASCII, digest, size, and in-flight cancellation tests.
        """

        digest = hashlib.sha256()
        total = 0
        prefix = bytearray()
        suffix = bytearray()
        with source_path.open("rb") as stream:
            while True:
                chunk = stream.read(policy["limits"]["readChunkBytes"])
                if not chunk:
                    break
                digest.update(chunk)
                total += len(chunk)
                if len(prefix) < 8192:
                    prefix.extend(chunk[: 8192 - len(prefix)])
                suffix.extend(chunk)
                if len(suffix) > 8192:
                    del suffix[:-8192]
                if self.chunk_hook is not None:
                    self.chunk_hook(execution_id, total)
                if self._cancellation_requested(execution_id, policy):
                    return {"cancelled": True}
        digest_hex = digest.hexdigest()
        detected_format = "unknown"
        triangle_count: int | None = None
        structure_consistent = False
        if total >= 84 and len(prefix) >= 84:
            candidate_count = int.from_bytes(prefix[80:84], "little")
            if 84 + candidate_count * 50 == total:
                detected_format = "binary-stl"
                triangle_count = candidate_count
                structure_consistent = candidate_count > 0
        lowered_prefix = bytes(prefix).lstrip().lower()
        lowered_suffix = bytes(suffix).lower()
        if detected_format == "unknown" and lowered_prefix.startswith(b"solid"):
            detected_format = "ascii-stl"
            structure_consistent = b"facet" in lowered_prefix and b"endsolid" in lowered_suffix
        return {
            "cancelled": False,
            "sizeBytes": total,
            "sha256": digest_hex,
            "sizeMatched": total == record["source"]["sizeBytes"],
            "digestMatched": digest_hex == record["source"]["sha256"],
            "detectedFormat": detected_format,
            "triangleCount": triangle_count,
            "formatRecognized": detected_format != "unknown",
            "structureConsistent": structure_consistent,
        }

    def _finish_with_proof(self, record: dict[str, Any], inspection: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Write report, log, proof, audits, and one honest terminal record.

        Inputs: Running record, completed inspection facts, and validated policy.
        Outputs: Complete terminal API result.
        How it works: Writes report/log, hashes both, writes proof, audits, then manifest.
        Side effects: Creates three output/evidence files and two audit events.
        Failure behavior: Any write/hash/audit failure propagates for failed-state handling.
        Safety: Artifacts contain ids, counts, hashes, outcomes, and logical paths only.
        Example: Recognized hash-matching STL yields ``completed`` and passing proof.
        Related proof: Artifact content, hash, ordering, and failed-result tests.
        """

        execution_id = record["id"]
        completed = self._utc_now().isoformat()
        passed = all((inspection["sizeMatched"], inspection["digestMatched"], inspection["formatRecognized"], inspection["structureConsistent"]))
        outcome = "passed" if passed else "failed"
        claim_state = "proven" if passed else "failed"
        root = self._execution_root(execution_id, policy)
        logical_root = record["workspace"]["logicalRoot"]
        report = {
            "schemaVersion": "makers-anvil.runtime.stl-preflight-report.v1",
            "executionId": execution_id,
            "claimState": claim_state,
            "completedUtc": completed,
            "source": {"intakeId": record["source"]["intakeId"], "sizeBytes": inspection["sizeBytes"], "sha256": inspection["sha256"]},
            "detectedFormat": inspection["detectedFormat"],
            "triangleCount": inspection["triangleCount"],
            "checks": {
                "extensionAllowed": True, "sizeMatched": inspection["sizeMatched"],
                "digestMatched": inspection["digestMatched"], "formatRecognized": inspection["formatRecognized"],
                "structureConsistent": inspection["structureConsistent"],
            },
            "result": {"passed": passed, "fullRouteCompleted": False, "toolpathGenerated": False},
        }
        report_path = root / "outputs" / policy["storage"]["reportFileName"]
        atomic_write_json(report_path, report)
        log_path = root / "logs" / policy["storage"]["executionLogFileName"]
        log_text = "\n".join([
            "Makers Anvil contained execution log", f"execution={execution_id}",
            "operation=built-in-stl-preflight", f"outcome={outcome}",
            f"source-bytes={inspection['sizeBytes']}", f"detected-format={inspection['detectedFormat']}",
            "external-process=false", "external-tool=false", "full-route-completed=false", "",
        ])
        self._write_exclusive_text(log_path, log_text)
        report_hash = self._hash_file(report_path)
        log_hash = self._hash_file(log_path)
        proof = {
            "schemaVersion": "makers-anvil.runtime.execution-proof.v1",
            "executionId": execution_id,
            "claimState": claim_state,
            "outcome": outcome,
            "generatedUtc": completed,
            "sourceDigestMatched": inspection["digestMatched"],
            "detectedFormat": inspection["detectedFormat"],
            "report": {"logicalPath": f"{logical_root}/outputs/{policy['storage']['reportFileName']}", "sha256": report_hash},
            "executionLog": {"logicalPath": f"{logical_root}/logs/{policy['storage']['executionLogFileName']}", "sha256": log_hash},
            "fullRouteCompleted": False,
            "toolpathGenerated": False,
            "outputOpened": False,
        }
        proof_path = root / "outputs" / policy["storage"]["proofFileName"]
        atomic_write_json(proof_path, proof)
        self.audit.append(execution_id, "execution-completed", outcome)
        self.audit.append(execution_id, "proof-recorded", outcome, "execution-proof")
        record["claimState"] = claim_state
        record["updatedUtc"] = completed
        record["lifecycle"] = {
            "state": "completed" if passed else "failed",
            "startedUtc": record["lifecycle"]["startedUtc"],
            "completedUtc": completed,
            "failureCode": None if passed else "stl_preflight_failed",
        }
        record["proof"] = proof
        self._validate_record(record, policy)
        atomic_write_json(self._record_path(execution_id, policy), record)
        return {"schemaVersion": "makers-anvil.api.contained-execution-result.v1", "claimState": claim_state, "record": record, "cancellation": self._load_cancellation(execution_id, policy), "audit": self.audit.history(execution_id)}

    def _finish_cancelled(self, record: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Finalize cooperative cancellation with no process-stop claim.

        Inputs: Current authorized/running record and validated policy.
        Outputs: Cancelled execution result with observed cancellation and audit.
        How it works: Ensures request exists, marks observed, appends event, writes manifest.
        Side effects: Replaces cancellation/record JSON and appends one immutable event.
        Failure behavior: Storage or audit errors propagate instead of claiming cancellation.
        Safety: No OS signal is sent and no processStopped field is invented.
        Example: Run observes cancellation after one source chunk and stops before outputs.
        Related proof: Pre-start and in-flight cancellation tests.
        """

        execution_id = record["id"]
        cancellation = self._load_cancellation(execution_id, policy)
        now = self._utc_now().isoformat()
        if cancellation["state"] == "not-requested":
            cancellation = {**cancellation, "state": "requested", "requestId": f"execution-cancel-{uuid4().hex}", "requestedUtc": now}
        cancellation["state"] = "observed"
        cancellation["observedUtc"] = now
        self._validate_cancellation(cancellation, execution_id)
        atomic_write_json(self._cancellation_path(execution_id, policy), cancellation)
        existing_types = {event["eventType"] for event in self.audit.history(execution_id)["events"]}
        if "execution-cancelled" not in existing_types:
            self.audit.append(execution_id, "execution-cancelled", "cancelled")
        record["claimState"] = "blocked"
        record["updatedUtc"] = now
        record["lifecycle"] = {
            "state": "cancelled", "startedUtc": record["lifecycle"]["startedUtc"],
            "completedUtc": now, "failureCode": None,
        }
        self._validate_record(record, policy)
        atomic_write_json(self._record_path(execution_id, policy), record)
        return {"schemaVersion": "makers-anvil.api.contained-execution-result.v1", "claimState": "blocked", "record": record, "cancellation": cancellation, "audit": self.audit.history(execution_id)}

    def _mark_operational_failure(self, execution_id: str, policy: dict[str, Any], code: str) -> None:
        """Purpose: Persist honest failed lifecycle after an unexpected operational error.

        Inputs: Valid execution id, policy, and fixed internal failure code.
        Outputs: ``None`` after best-effort record replacement.
        How it works: Reloads current record and changes only terminal lifecycle fields.
        Side effects: Replaces one app-owned execution manifest when possible.
        Failure behavior: Secondary load/write failure is contained by the caller's original error.
        Safety: No exception detail or private path is persisted.
        Example: Disk write failure records ``execution_io_failed`` when manifest remains writable.
        Related proof: Injected operational failure tests.
        """

        try:
            record = self._load_record(execution_id, policy)
            now = self._utc_now().isoformat()
            record["claimState"] = "failed"
            record["updatedUtc"] = now
            record["lifecycle"] = {"state": "failed", "startedUtc": record["lifecycle"]["startedUtc"], "completedUtc": now, "failureCode": code}
            atomic_write_json(self._record_path(execution_id, policy), record)
        except (OSError, ValueError):
            return

    def _load_record(self, execution_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Decode and strictly validate one contained execution marker.

        Inputs: Generated execution id and validated policy.
        Outputs: Mutable validated execution mapping for orchestration.
        How it works: Resolves exact path, rejects symlinks, decodes JSON, validates fields.
        Side effects: Reads one app-owned JSON file.
        Failure behavior: Missing/malformed/weakened records raise typed 404 or 422 errors.
        Safety: Invalid ids fail before filesystem access.
        Example: Run loads only the exact record created by authorization.
        Related proof: Traversal and corrupted-record tests.
        """

        path = self._record_path(execution_id, policy)
        if path.is_symlink() or not path.is_file():
            raise ContainedExecutionError(404, "execution_not_found", "Contained execution does not exist.")
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            self._validate_record(record, policy)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ContainedExecutionError(422, "execution_record_invalid", "Contained execution record is invalid.") from exc
        return record

    @staticmethod
    def _validate_record(record: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Enforce complete execution identity, lifecycle, proof, and privacy shape.

        Inputs: Candidate decoded record and validated policy.
        Outputs: ``None`` only when all state-dependent invariants pass.
        How it works: Checks exact fields, ids, closed values, logical references, and claims.
        Side effects: None.
        Failure behavior: Raises ``ValueError`` before an invalid record is exposed or used.
        Safety: Private paths, commands, process ids, tool claims, and arbitrary fields fail.
        Example: Completed requires proven claim, timestamps, and non-null proof.
        Related proof: Runtime record schema and corruption tests.
        """

        if not isinstance(record, dict) or set(record) != RECORD_FIELDS or record.get("schemaVersion") != "makers-anvil.runtime.contained-execution.v1":
            raise ValueError("contained execution record shape is invalid")
        execution_id = record.get("id")
        if not isinstance(execution_id, str) or not EXECUTION_ID_PATTERN.fullmatch(execution_id):
            raise ValueError("contained execution id is invalid")
        state = record.get("lifecycle", {}).get("state") if isinstance(record.get("lifecycle"), dict) else None
        expected_claim = {"authorized": "staged", "running": "staged", "completed": "proven", "cancelled": "blocked", "failed": "failed"}.get(state)
        if state not in LIFECYCLE_STATES or record.get("claimState") != expected_claim:
            raise ValueError("contained execution lifecycle claim is invalid")
        if record.get("route") != {"id": "mesh-to-toolpath", "label": "Mesh to toolpath"}:
            raise ValueError("contained execution route is invalid")
        if record.get("operation") != {"id": "built-in-stl-preflight", "label": "Built-in STL preflight", "executor": "makers-anvil-built-in"}:
            raise ValueError("contained execution operation is invalid")
        source = record.get("source")
        if not isinstance(source, dict) or set(source) != {"intakeId", "displayName", "extension", "kind", "sizeBytes", "sha256", "logicalReference"}:
            raise ValueError("contained execution source shape is invalid")
        if not re.fullmatch(r"intake-[a-f0-9]{32}", str(source.get("intakeId", ""))) or source.get("extension") != ".stl" or source.get("kind") != "mesh":
            raise ValueError("contained execution source identity is invalid")
        if not isinstance(source.get("displayName"), str) or not isinstance(source.get("sizeBytes"), int) or isinstance(source.get("sizeBytes"), bool) or source["sizeBytes"] <= 0:
            raise ValueError("contained execution source metadata is invalid")
        if not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256", ""))) or source.get("logicalReference") != f"makers-anvil-data://user/intake/files/{source['intakeId']}":
            raise ValueError("contained execution source digest or reference is invalid")
        authorization = record.get("authorization")
        if not isinstance(authorization, dict) or set(authorization) != {"required", "accepted", "actor", "acceptedUtc"} or authorization.get("required") is not True or authorization.get("accepted") is not True or authorization.get("actor") != "local-user" or not isinstance(authorization.get("acceptedUtc"), str):
            raise ValueError("contained execution authorization is invalid")
        lifecycle = record["lifecycle"]
        if set(lifecycle) != {"state", "startedUtc", "completedUtc", "failureCode"}:
            raise ValueError("contained execution lifecycle shape is invalid")
        if state == "authorized" and lifecycle != {"state": "authorized", "startedUtc": None, "completedUtc": None, "failureCode": None}:
            raise ValueError("authorized execution lifecycle is invalid")
        if state == "running" and (not isinstance(lifecycle["startedUtc"], str) or lifecycle["completedUtc"] is not None or lifecycle["failureCode"] is not None):
            raise ValueError("running execution lifecycle is invalid")
        if state in TERMINAL_STATES and not isinstance(lifecycle["completedUtc"], str):
            raise ValueError("terminal execution requires completion time")
        workspace = record.get("workspace")
        if workspace != {"logicalRoot": f"makers-anvil-data://user/executions/{execution_id}", "absolutePathExposed": False}:
            raise ValueError("contained execution workspace is invalid")
        safety = record.get("safety")
        if not isinstance(safety, dict) or set(safety) != POLICY_SAFETY_FIELDS or safety != policy["safety"]:
            raise ValueError("contained execution safety is invalid")
        proof = record.get("proof")
        if state in {"authorized", "running", "cancelled"} and proof is not None:
            raise ValueError("non-proof execution state cannot contain proof")
        if state == "completed" and (not isinstance(proof, dict) or proof.get("outcome") != "passed"):
            raise ValueError("completed execution requires passing proof")
        if state == "failed" and proof is not None and proof.get("outcome") != "failed":
            raise ValueError("failed execution proof outcome is invalid")
        if isinstance(proof, dict):
            ContainedExecutionService._validate_proof(proof, record, policy)

    @staticmethod
    def _validate_proof(proof: dict[str, Any], record: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Bind terminal proof fields to one execution and its fixed artifacts.

        Inputs: Candidate proof, owning execution record, and validated storage policy.
        Outputs: ``None`` only when identity, claims, hashes, paths, and false boundaries match.
        How it works: Enforces exact fields plus generated logical references and digest syntax.
        Side effects: None.
        Failure behavior: Any extra, missing, widened, or mismatched field raises ``ValueError``.
        Safety: A changed record cannot redirect the viewer or claim route/tool/output completion.
        Example: Report reference must end in the committed report filename below this execution.
        Related proof: Artifact tamper, catalog corruption, and runtime schema tests.
        """

        fields = {
            "schemaVersion", "executionId", "claimState", "outcome", "generatedUtc",
            "sourceDigestMatched", "detectedFormat", "report", "executionLog",
            "fullRouteCompleted", "toolpathGenerated", "outputOpened",
        }
        execution_id = record["id"]
        logical_root = record["workspace"]["logicalRoot"]
        expected_outcome = "passed" if record["lifecycle"]["state"] == "completed" else "failed"
        if set(proof) != fields or proof.get("schemaVersion") != "makers-anvil.runtime.execution-proof.v1" or proof.get("executionId") != execution_id:
            raise ValueError("execution proof identity is invalid")
        if proof.get("claimState") != record["claimState"] or proof.get("outcome") != expected_outcome or not isinstance(proof.get("generatedUtc"), str):
            raise ValueError("execution proof claim is invalid")
        if not isinstance(proof.get("sourceDigestMatched"), bool) or proof.get("detectedFormat") not in {"binary-stl", "ascii-stl", "unknown"}:
            raise ValueError("execution proof inspection result is invalid")
        expected_paths = {
            "report": f"{logical_root}/outputs/{policy['storage']['reportFileName']}",
            "executionLog": f"{logical_root}/logs/{policy['storage']['executionLogFileName']}",
        }
        for artifact_name, logical_path in expected_paths.items():
            artifact = proof.get(artifact_name)
            if not isinstance(artifact, dict) or set(artifact) != {"logicalPath", "sha256"} or artifact.get("logicalPath") != logical_path or not re.fullmatch(r"[a-f0-9]{64}", str(artifact.get("sha256", ""))):
                raise ValueError("execution proof artifact binding is invalid")
        if any(proof.get(field) is not False for field in ("fullRouteCompleted", "toolpathGenerated", "outputOpened")):
            raise ValueError("execution proof boundary is invalid")

    @staticmethod
    def _validate_report(report: dict[str, Any], record: dict[str, Any]) -> None:
        """Purpose: Validate the complete STL report before returning its JSON content.

        Inputs: Decoded report and strict owning execution record.
        Outputs: ``None`` only for the generated closed structural-report contract.
        How it works: Checks exact top-level/nested fields, source identity, checks, and false route claims.
        Side effects: None.
        Failure behavior: Missing, extra, mistyped, or inconsistent report data raises ``ValueError``.
        Safety: Viewer content cannot inject paths, commands, HTML, or completed manufacturing claims.
        Example: Passing binary STL reports a nonnegative triangle count and no toolpath generation.
        Related proof: Viewer corruption tests and ``stl-preflight-report.schema.json``.
        """

        fields = {"schemaVersion", "executionId", "claimState", "completedUtc", "source", "detectedFormat", "triangleCount", "checks", "result"}
        if set(report) != fields or report.get("schemaVersion") != "makers-anvil.runtime.stl-preflight-report.v1" or report.get("executionId") != record["id"]:
            raise ValueError("STL report identity is invalid")
        if report.get("claimState") != record["claimState"] or not isinstance(report.get("completedUtc"), str):
            raise ValueError("STL report claim is invalid")
        source = report.get("source")
        if not isinstance(source, dict) or set(source) != {"intakeId", "sizeBytes", "sha256"} or source.get("intakeId") != record["source"]["intakeId"] or source.get("sizeBytes") != record["source"]["sizeBytes"] or source.get("sha256") != record["source"]["sha256"]:
            raise ValueError("STL report source binding is invalid")
        if report.get("detectedFormat") not in {"binary-stl", "ascii-stl", "unknown"} or not isinstance(report.get("triangleCount"), int) or isinstance(report.get("triangleCount"), bool) or report["triangleCount"] < 0:
            raise ValueError("STL report format result is invalid")
        checks = report.get("checks")
        check_fields = {"extensionAllowed", "sizeMatched", "digestMatched", "formatRecognized", "structureConsistent"}
        if not isinstance(checks, dict) or set(checks) != check_fields or any(not isinstance(value, bool) for value in checks.values()):
            raise ValueError("STL report checks are invalid")
        result = report.get("result")
        expected_passed = record["lifecycle"]["state"] == "completed"
        if result != {"passed": expected_passed, "fullRouteCompleted": False, "toolpathGenerated": False}:
            raise ValueError("STL report result boundary is invalid")

    @staticmethod
    def _initial_cancellation(execution_id: str) -> dict[str, Any]:
        """Purpose: Create cooperative cancellation state with no process signal.

        Inputs: Generated execution id.
        Outputs: Exact not-requested cancellation mapping.
        How it works: Populates fixed false/null initial values.
        Side effects: None until caller persists the record.
        Failure behavior: Invalid id is caught by surrounding record validation.
        Safety: Process signaling is constant false.
        Example: Every authorization begins with no cancellation request.
        Related proof: Cancellation schema and initial-state tests.
        """

        return {
            "schemaVersion": "makers-anvil.runtime.execution-cancellation.v1",
            "executionId": execution_id,
            "claimState": "staged",
            "state": "not-requested",
            "requestId": None,
            "requestedUtc": None,
            "observedUtc": None,
            "cooperative": True,
            "processSignalSent": False,
        }

    @staticmethod
    def _validate_cancellation(record: dict[str, Any], execution_id: str) -> None:
        """Purpose: Enforce exact state-dependent cooperative cancellation fields.

        Inputs: Candidate cancellation mapping and owner execution id.
        Outputs: ``None`` only for not-requested, requested, or observed state.
        How it works: Checks field set, owner, closed state, ids, times, and false signal.
        Side effects: None.
        Failure behavior: Raises ``ValueError`` before cancellation is trusted.
        Safety: No record can claim an operating-system process signal.
        Example: Observed requires request id plus requested and observed UTC text.
        Related proof: Cancellation mutation and corruption tests.
        """

        if not isinstance(record, dict) or set(record) != CANCELLATION_FIELDS or record.get("schemaVersion") != "makers-anvil.runtime.execution-cancellation.v1" or record.get("executionId") != execution_id or record.get("claimState") != "staged" or record.get("cooperative") is not True or record.get("processSignalSent") is not False:
            raise ValueError("execution cancellation shape is invalid")
        state = record.get("state")
        if state == "not-requested":
            if any(record[key] is not None for key in ("requestId", "requestedUtc", "observedUtc")):
                raise ValueError("initial cancellation values are invalid")
        elif state == "requested":
            if not re.fullmatch(r"execution-cancel-[a-f0-9]{32}", str(record.get("requestId", ""))) or not isinstance(record.get("requestedUtc"), str) or record.get("observedUtc") is not None:
                raise ValueError("requested cancellation values are invalid")
        elif state == "observed":
            if not re.fullmatch(r"execution-cancel-[a-f0-9]{32}", str(record.get("requestId", ""))) or not isinstance(record.get("requestedUtc"), str) or not isinstance(record.get("observedUtc"), str):
                raise ValueError("observed cancellation values are invalid")
        else:
            raise ValueError("execution cancellation state is invalid")

    def _load_cancellation(self, execution_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Decode and validate one execution's cooperative control record.

        Inputs: Valid execution id and policy.
        Outputs: Valid cancellation mapping.
        How it works: Reads exact control filename and applies state-dependent validation.
        Side effects: Reads one app-owned JSON file.
        Failure behavior: Missing or malformed control state raises typed execution error.
        Safety: No private path is included in the public error.
        Example: Running preflight checks this record after each read chunk.
        Related proof: Missing and corrupt cancellation tests.
        """

        path = self._cancellation_path(execution_id, policy)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            self._validate_cancellation(record, execution_id)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise ContainedExecutionError(422, "execution_cancellation_invalid", "Execution cancellation record is invalid.") from exc
        return record

    def _cancellation_requested(self, execution_id: str, policy: dict[str, Any]) -> bool:
        """Purpose: Return whether cooperative cancellation has been requested or observed.

        Inputs: Valid execution id and policy.
        Outputs: Boolean cancellation state.
        How it works: Loads the strict control record and compares its closed state.
        Side effects: Reads one app-owned JSON file.
        Failure behavior: Corruption raises rather than continuing execution.
        Safety: No process or thread is signaled by this check.
        Example: A requested record stops the next source-read iteration.
        Related proof: In-flight cancellation test hook.
        """

        return self._load_cancellation(execution_id, policy)["state"] in {"requested", "observed"}

    def _executions_root(self, policy: dict[str, Any]) -> Path:
        """Purpose: Resolve the private app-owned executions root.

        Inputs: Validated policy.
        Outputs: Contained runtime path for ``executions``.
        How it works: Uses fixed policy value through workspace containment.
        Side effects: None.
        Failure behavior: Workspace path errors propagate.
        Safety: Source checkout and browser input do not select this root.
        Example: Windows resolves under local app data while API shows logical root.
        Related proof: Relocated-source and override tests.
        """

        return self.workspace_config.runtime_path(policy["storage"]["executionsDirectory"])

    def _execution_root(self, execution_id: str, policy: dict[str, Any]) -> Path:
        """Purpose: Resolve one exact contained execution directory.

        Inputs: Generated execution id and policy.
        Outputs: Path below the app-owned executions root.
        How it works: Applies anchored id regex before joining.
        Side effects: None.
        Failure behavior: Invalid ids raise typed 400 error before filesystem access.
        Safety: Traversal, separators, globs, and filenames cannot select a path.
        Example: ``execution-<hex>`` maps to exactly one directory.
        Related proof: Invalid-id and symlink tests.
        """

        if not isinstance(execution_id, str) or not EXECUTION_ID_PATTERN.fullmatch(execution_id):
            raise ContainedExecutionError(400, "execution_id_invalid", "Execution id is invalid.")
        root = self._executions_root(policy) / execution_id
        if root.exists() and root.is_symlink():
            raise ContainedExecutionError(422, "execution_containment_rejected", "Execution workspace containment is invalid.")
        return root

    def _record_path(self, execution_id: str, policy: dict[str, Any]) -> Path:
        """Purpose: Return the exact private execution marker path.

        Inputs: Valid execution id and policy.
        Outputs: ``executions/<id>/execution.json`` path.
        How it works: Resolves execution root and appends the fixed marker name.
        Side effects: None.
        Failure behavior: Invalid ids/symlinks fail in root resolution.
        Safety: Browser data cannot choose a filename.
        Example: Run and catalog use the same completion marker.
        Related proof: Containment tests.
        """

        return self._execution_root(execution_id, policy) / policy["storage"]["recordFileName"]

    def _cancellation_path(self, execution_id: str, policy: dict[str, Any]) -> Path:
        """Purpose: Return the exact private cooperative-control path.

        Inputs: Valid execution id and policy.
        Outputs: ``executions/<id>/control/cancellation.json`` path.
        How it works: Resolves execution root and appends fixed components.
        Side effects: None.
        Failure behavior: Invalid ids/symlinks fail in root resolution.
        Safety: No arbitrary control file can be selected.
        Example: Cancel and source loop share this exact record.
        Related proof: Cancellation containment tests.
        """

        return self._execution_root(execution_id, policy) / "control" / policy["storage"]["cancellationFileName"]

    @staticmethod
    def _write_exclusive_text(path: Path, text: str) -> None:
        """Purpose: Create one immutable execution log and refuse overwrite.

        Inputs: Service-derived contained path and fixed server-authored text.
        Outputs: ``None`` after flush and fsync.
        How it works: Opens with OS exclusive-create flags and writes UTF-8 once.
        Side effects: Creates one app-owned text log.
        Failure behavior: Existing destination or I/O error raises.
        Safety: Caller supplies no browser text or private source path.
        Example: Each execution can create exactly one ``execution.log``.
        Related proof: Replay and immutable-log tests.
        """

        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())

    @staticmethod
    def _hash_file(path: Path) -> str:
        """Purpose: Compute SHA-256 evidence for one generated app-owned artifact.

        Inputs: Service-derived report or log path.
        Outputs: Lowercase 64-character SHA-256 digest.
        How it works: Reads fixed-size chunks until EOF.
        Side effects: Reads one generated file only.
        Failure behavior: I/O failures propagate to operational failure handling.
        Safety: Digest leaves private path and content out of API records.
        Example: Proof binds report bytes to their recorded logical artifact.
        Related proof: Artifact hash recomputation tests.
        """

        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _utc_now(self) -> datetime:
        """Purpose: Normalize the execution clock to timezone-aware UTC.

        Inputs: Constructor-provided clock callable.
        Outputs: Aware UTC datetime for authorization/lifecycle/proof fields.
        How it works: Calls once, rejects naive values, and converts timezone.
        Side effects: Reads current time only.
        Failure behavior: Invalid clocks raise typed internal execution error.
        Safety: Records never guess local timezone.
        Example: Tests inject deterministic sequential UTC values.
        Related proof: Timestamp and deterministic fixture tests.
        """

        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ContainedExecutionError(500, "execution_clock_invalid", "Contained execution clock is invalid.")
        return value.astimezone(UTC)


__all__ = ["ContainedExecutionError", "ContainedExecutionService"]
