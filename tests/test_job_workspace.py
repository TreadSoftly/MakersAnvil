"""Purpose: Explain and prove contained preparation and cancellation intent.

Used by: Developers and CI before execution/process work can be introduced.
Inputs: Isolated request previews, policies, runtime roots, and malformed cases.
Outputs: Assertions over folders, records, idempotency, and blocked effects.
Side effects: Creates only temporary app-owned job structures.
Safety: No authorization, command, process, signal, source, output, or proof escapes.
Failure behavior: Traversal, symlinks, drift, and malformed records fail closed.
Related proof: Job services, scripts, policies, and schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.job_workspace import JobWorkspaceError, JobWorkspaceService
from makers_anvil_backend.services.job_records import job_id_for_preview
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _StubExecutionRequest:
    """Purpose: Provide one path-free request preview without the upstream planning graph.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``_StubExecutionRequest`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Construct with ``instance = _StubExecutionRequest(...)`` using values described by ``__init__``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    def __init__(self, preview: dict) -> None:
        """Purpose: Store the preview returned by isolated preparation tests.

        Inputs: Caller-supplied ``preview`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: No authorization, command, process, signal, source, output, or proof escapes.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: Job services, scripts, policies, and schemas.
        """

        self._preview = preview

    def execution_request_policy(self) -> dict:
        """Purpose: Return the single route required for job-policy coherence.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: No authorization, command, process, signal, source, output, or proof escapes.
        Example: Call ``result = instance.execution_request_policy(...)`` with values satisfying the documented inputs.
        Related proof: Job services, scripts, policies, and schemas.
        """

        return {"scope": {"routeId": "mesh-to-toolpath"}}

    def preview_catalog(self) -> dict:
        """Purpose: Return one blocked request preview as the preparation source.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: No authorization, command, process, signal, source, output, or proof escapes.
        Example: Call ``result = instance.preview_catalog(...)`` with values satisfying the documented inputs.
        Related proof: Job services, scripts, policies, and schemas.
        """

        return {"previews": [self._preview]}


def make_preview() -> dict:
    """Purpose: Build a valid logical request preview with no accepted authorization.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``dict``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Call ``result = make_preview(...)`` with values satisfying the documented inputs.
    Related proof: Job services, scripts, policies, and schemas.
    """

    return {
        "id": "execution-request-preview-dry-run-intake-123-mesh-to-toolpath",
        "route": {"id": "mesh-to-toolpath", "label": "Mesh to Toolpath"},
        "operation": {"id": "prepare-toolpath", "label": "Prepare mesh for toolpath generation"},
        "intent": {
            "source": {
                "intakeId": "intake-123",
                "logicalReference": "makers-anvil-intake://records/intake-123",
            },
            "output": {
                "bundleId": "output-bundle-123",
                "logicalDirectory": "makers-anvil-data://user/outputs/output-bundle-123",
            },
            "tool": {"id": "prusaslicer", "label": "PrusaSlicer", "claimState": "detected"},
        },
        "authorization": {"required": True, "accepted": False, "actor": None, "acceptedAt": None},
    }


def write_config(root: Path) -> None:
    """Purpose: Write committed job policy plus minimal portable workspace settings.

    Inputs: Caller-supplied ``root`` values from the signature.
    Outputs: Returns ``None``, or raises before returning when validation fails.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Call ``result = instance.write_config(...)`` with values satisfying the documented inputs.
    Related proof: Job services, scripts, policies, and schemas.
    """

    config = root / "config"
    config.mkdir(parents=True)
    config.joinpath("job_workspace_policy.json").write_text(
        PROJECT_ROOT.joinpath("config", "job_workspace_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    config.joinpath("default_settings.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.local-settings.v1",
                "claimState": "staged",
                "runtimeData": {
                    "mode": "platform-user-data",
                    "logicalRoot": "makers-anvil-data://user",
                    "environmentOverride": DATA_DIR_ENV,
                    "sourceRootDependency": False,
                    "absolutePathExposed": False,
                },
                "directories": [{"id": "jobs", "relativePath": "jobs", "purpose": "prepared jobs"}],
                "safety": {
                    "userUploadEnabled": False,
                    "routeExecutionEnabled": False,
                    "toolLaunchEnabled": False,
                    "archiveExtractionEnabled": False,
                    "folderImportEnabled": False,
                    "deleteUserDataEnabled": False,
                    "releasePackagingEnabled": False,
                },
            }
        ),
        encoding="utf-8",
    )


def build_service(tmp_path: Path, preview: dict | None = None) -> tuple[JobWorkspaceService, Path]:
    """Purpose: Build a service whose source and runtime roots are deliberately separate.

    Inputs: Caller-supplied ``tmp_path``, ``preview`` values from the signature.
    Outputs: Returns ``tuple[JobWorkspaceService, Path]``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Call ``result = instance.build_service(...)`` with values satisfying the documented inputs.
    Related proof: Job services, scripts, policies, and schemas.
    """

    source_root = tmp_path / "source"
    data_root = tmp_path / "runtime"
    write_config(source_root)
    paths = RuntimePathsService(
        source_root=source_root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=tmp_path / "home",
        platform_name="linux",
    )
    workspace = WorkspaceConfigService(source_root, paths)
    request = _StubExecutionRequest(preview or make_preview())
    return JobWorkspaceService(source_root, workspace, request), data_root


def test_empty_catalog_is_read_only_and_does_not_create_runtime_storage(tmp_path: Path) -> None:
    """Purpose: Reading job state never creates the app-owned jobs directory.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_empty_catalog_is_read_only_and_does_not_create_runtime_storage``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, data_root = build_service(tmp_path)

    result = service.catalog()

    assert result["summary"] == {
        "preparedJobCount": 0,
        "cancellationRequestedCount": 0,
        "invalidJobCount": 0,
        "executionReadyCount": 0,
    }
    assert result["jobsPath"] == "makers-anvil-data://user/jobs"
    assert result["recordsRootExists"] is False
    assert not data_root.exists()
    assert all(value is False for value in result["safety"].values())
    assert all(action["enabledInApi"] is False for action in result["actions"].values())


def test_prepare_creates_only_contained_path_redacted_app_records(tmp_path: Path) -> None:
    """Purpose: Preparation creates empty app-owned directories and no executable or private data.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_prepare_creates_only_contained_path_redacted_app_records``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, data_root = build_service(tmp_path)
    result = service.prepare(make_preview()["id"])
    record = result["record"]
    job_root = data_root / "jobs" / record["id"]

    assert {path.name for path in job_root.iterdir()} == {"control", "working", "logs", "outputs", "job.json"}
    assert (job_root / "control" / "cancellation.json").is_file()
    assert all((job_root / name).is_dir() for name in ("control", "working", "logs", "outputs"))
    assert record["workspace"]["absolutePathExposed"] is False
    assert record["workspace"]["logicalRoot"] == f"makers-anvil-data://user/jobs/{record['id']}"
    assert record["authorization"]["accepted"] is False
    assert record["lifecycle"] == {"state": "prepared", "processId": None, "startedAt": None, "completedAt": None}
    assert result["cancellation"]["state"] == "not-requested"
    assert all(value is False for value in record["safety"].values())
    serialized = json.dumps(result)
    assert str(data_root) not in serialized
    assert str(tmp_path) not in serialized


def test_prepare_is_idempotent_for_the_same_request_preview(tmp_path: Path) -> None:
    """Purpose: Repeated preparation returns the existing job without duplicate records or timestamps.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_prepare_is_idempotent_for_the_same_request_preview``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, data_root = build_service(tmp_path)
    first = service.prepare(make_preview()["id"])
    second = service.prepare(make_preview()["id"])

    assert second == first
    assert len(list((data_root / "jobs").iterdir())) == 1


def test_prepare_rejects_private_or_accepted_preview_data(tmp_path: Path) -> None:
    """Purpose: A weakened upstream preview cannot persist a source path or accepted authorization.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_prepare_rejects_private_or_accepted_preview_data``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    preview = make_preview()
    preview["intent"]["source"]["logicalReference"] = str(tmp_path / "private.stl")
    service, _ = build_service(tmp_path, preview)
    with pytest.raises(JobWorkspaceError, match="unavailable or outside"):
        service.prepare(preview["id"])

    preview = make_preview()
    preview["authorization"]["accepted"] = True
    service, _ = build_service(tmp_path / "accepted", preview)
    with pytest.raises(JobWorkspaceError, match="unavailable or outside"):
        service.prepare(preview["id"])


def test_cancellation_records_intent_without_signaling_or_stopping_process(tmp_path: Path) -> None:
    """Purpose: Cancellation changes only its control record and remains idempotent.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_cancellation_records_intent_without_signaling_or_stopping_process``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, _ = build_service(tmp_path)
    job = service.prepare(make_preview()["id"])["record"]

    first = service.request_cancellation(job["id"])
    second = service.request_cancellation(job["id"])
    catalog = service.catalog()

    assert first == second
    assert first["state"] == "requested"
    assert first["requestId"].startswith("cancel-")
    assert isinstance(first["requestedAt"], str)
    assert first["processSignalSent"] is False
    assert first["processStopped"] is False
    assert catalog["summary"]["cancellationRequestedCount"] == 1
    assert catalog["summary"]["executionReadyCount"] == 0


def test_job_ids_and_symlink_workspaces_cannot_escape_containment(tmp_path: Path) -> None:
    """Purpose: Traversal ids and symlinked job roots are rejected before record access.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It handles expected failures explicitly.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_job_ids_and_symlink_workspaces_cannot_escape_containment``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, data_root = build_service(tmp_path)
    with pytest.raises(JobWorkspaceError, match="invalid format"):
        service.request_cancellation("../outside")

    job_id = job_id_for_preview(make_preview()["id"])
    jobs_root = data_root / "jobs"
    jobs_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (jobs_root / job_id).symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("test environment does not permit directory symlinks")
    with pytest.raises(JobWorkspaceError, match="symbolic link"):
        service.prepare(make_preview()["id"])


def test_catalog_fails_closed_on_malformed_or_weakened_runtime_records(tmp_path: Path) -> None:
    """Purpose: Invalid prepared records are counted and never returned as usable jobs.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_catalog_fails_closed_on_malformed_or_weakened_runtime_records``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, data_root = build_service(tmp_path)
    job = service.prepare(make_preview()["id"])["record"]
    manifest = data_root / "jobs" / job["id"] / "job.json"
    weakened = json.loads(manifest.read_text(encoding="utf-8"))
    weakened["safety"]["processStarted"] = True
    manifest.write_text(json.dumps(weakened), encoding="utf-8")

    catalog = service.catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["jobs"] == []
    assert catalog["summary"]["invalidJobCount"] == 1

    manifest.write_text(json.dumps(job), encoding="utf-8")
    (data_root / "jobs" / job["id"] / "working").rmdir()
    incomplete = service.catalog()
    assert incomplete["jobs"] == []
    assert incomplete["summary"]["invalidJobCount"] == 1


def test_policy_rejects_api_mutation_or_execution_effects(tmp_path: Path) -> None:
    """Purpose: Policy changes cannot silently enable browser mutation, process start, or signaling.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: No authorization, command, process, signal, source, output, or proof escapes.
    Example: Run ``python -m pytest tests/test_job_workspace.py -k test_policy_rejects_api_mutation_or_execution_effects``.
    Related proof: Job services, scripts, policies, and schemas.
    """

    service, _ = build_service(tmp_path)
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["localActions"]["apiMutationEnabled"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(JobWorkspaceError, match="explicit local"):
        service.catalog()

    policy["localActions"]["apiMutationEnabled"] = False
    policy["safety"]["processStarted"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(JobWorkspaceError, match="cannot persist executable intent"):
        service.catalog()
