"""Purpose: Run the deterministic repository, schema, safety, and API gates.

Used by: Developers, pytest, CI, and every completed ``Continue`` pass.
Inputs: Tracked product files, committed policies/schemas/state, and local Python.
Outputs: Human-readable pass/fail lines and a nonzero exit on any broken contract.
Side effects: Reads files and uses isolated temporary directories only.
Safety: Verification never imports reference folders or changes user data.
Failure behavior: Each gate reports its contract before the process fails.
Related proof: ``tests/test_verify_project.py`` and CI workflow.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.api.app import MakersAnvilApi  # noqa: E402
from makers_anvil_backend.domain.claim_state import ALLOWED_CLAIM_STATES  # noqa: E402
from makers_anvil_backend.runtime_resources import frontend_root  # noqa: E402
from makers_anvil_backend.server import require_loopback_host  # noqa: E402
from scripts.build_windows_exe import package_plan  # noqa: E402
from scripts.check_explainability import run_checks as check_explainability  # noqa: E402

REQUIRED_FILES = [
    ".gitignore",
    "README.md",
    "package.json",
    "pyproject.toml",
    "backend/src/makers_anvil_backend/api/app.py",
    "backend/src/makers_anvil_backend/desktop.py",
    "backend/src/makers_anvil_backend/runtime_resources.py",
    "backend/src/makers_anvil_backend/server.py",
    "backend/src/makers_anvil_backend/services/activity_log.py",
    "backend/src/makers_anvil_backend/services/app_state.py",
    "backend/src/makers_anvil_backend/services/capability_matrix.py",
    "backend/src/makers_anvil_backend/services/contained_execution.py",
    "backend/src/makers_anvil_backend/services/execution_audit.py",
    "backend/src/makers_anvil_backend/services/execution_gate.py",
    "backend/src/makers_anvil_backend/services/execution_request.py",
    "backend/src/makers_anvil_backend/services/intake_catalog.py",
    "backend/src/makers_anvil_backend/services/intake_preview.py",
    "backend/src/makers_anvil_backend/services/job_records.py",
    "backend/src/makers_anvil_backend/services/job_workspace.py",
    "backend/src/makers_anvil_backend/services/lifecycle_dry_run.py",
    "backend/src/makers_anvil_backend/services/local_request_guard.py",
    "backend/src/makers_anvil_backend/services/output_proof.py",
    "backend/src/makers_anvil_backend/services/route_preview.py",
    "backend/src/makers_anvil_backend/services/runtime_paths.py",
    "backend/src/makers_anvil_backend/services/tool_detection.py",
    "backend/src/makers_anvil_backend/services/tool_dry_run.py",
    "backend/src/makers_anvil_backend/services/tool_launch.py",
    "backend/src/makers_anvil_backend/services/tool_version.py",
    "backend/src/makers_anvil_backend/services/workbench_experience.py",
    "backend/src/makers_anvil_backend/services/windows_installer.py",
    "backend/src/makers_anvil_backend/services/workspace_config.py",
    "backend/src/makers_anvil_backend/services/workspace_status.py",
    "config/default_settings.json",
    "config/contained_execution_policy.json",
    "config/execution_gate_policy.json",
    "config/execution_request_policy.json",
    "config/intake_policy.json",
    "config/intake_preview_policy.json",
    "config/job_workspace_policy.json",
    "config/lifecycle_dry_run_policy.json",
    "config/output_policy.json",
    "config/route_catalog.json",
    "config/tool_catalog.json",
    "config/tool_dry_run_policy.json",
    "config/tool_launch_policy.json",
    "config/workbench_experience.json",
    "config/windows_installer_policy.json",
    "config/clean_machine_scenarios.json",
    "frontend/index.html",
    "frontend/package.json",
    "frontend/package-lock.json",
    "frontend/src/App.tsx",
    "frontend/src/api.ts",
    "frontend/src/main.tsx",
    "frontend/src/styles.css",
    "frontend/src/types.ts",
    "frontend/vite.config.ts",
    "schemas/activity-event.schema.json",
    "schemas/activity-history.schema.json",
    "schemas/claim-state.schema.json",
    "schemas/app-state.schema.json",
    "schemas/capability-matrix.schema.json",
    "schemas/contained-execution-policy.schema.json",
    "schemas/contained-artifact.schema.json",
    "schemas/contained-execution-record.schema.json",
    "schemas/contained-execution-catalog.schema.json",
    "schemas/current-status.schema.json",
    "schemas/execution-gate-policy.schema.json",
    "schemas/execution-gates.schema.json",
    "schemas/execution-request-policy.schema.json",
    "schemas/execution-request-preview.schema.json",
    "schemas/execution-cancellation.schema.json",
    "schemas/execution-audit-event.schema.json",
    "schemas/execution-audit-history.schema.json",
    "schemas/execution-proof.schema.json",
    "schemas/local-settings.schema.json",
    "schemas/runtime-location.schema.json",
    "schemas/intake-policy.schema.json",
    "schemas/intake-preview-policy.schema.json",
    "schemas/intake-record.schema.json",
    "schemas/job-cancellation-record.schema.json",
    "schemas/job-workspace-catalog.schema.json",
    "schemas/job-workspace-policy.schema.json",
    "schemas/job-workspace-record.schema.json",
    "schemas/lifecycle-dry-run-catalog.schema.json",
    "schemas/lifecycle-dry-run-policy.schema.json",
    "schemas/windows-installer-policy.schema.json",
    "schemas/windows-installer-readiness.schema.json",
    "schemas/clean-machine-harness.schema.json",
    "schemas/output-policy.schema.json",
    "schemas/output-proof.schema.json",
    "schemas/route-catalog.schema.json",
    "schemas/route-preview.schema.json",
    "schemas/tool-catalog.schema.json",
    "schemas/tool-detection.schema.json",
    "schemas/tool-dry-run-policy.schema.json",
    "schemas/tool-dry-run.schema.json",
    "schemas/tool-launch-catalog.schema.json",
    "schemas/tool-launch-policy.schema.json",
    "schemas/stl-preflight-report.schema.json",
    "schemas/workbench-experience-policy.schema.json",
    "schemas/workbench-experience.schema.json",
    "schemas/workbench-preferences.schema.json",
    "scripts/init_workspace.py",
    "scripts/build_learning_guide.py",
    "scripts/build_previous_app_learning_guide.py",
    "scripts/build_windows_exe.py",
    "scripts/check_explainability.py",
    "scripts/check_clean_machine.py",
    "scripts/prepare_job.py",
    "scripts/request_job_cancel.py",
    "scripts/run_desktop.py",
    "scripts/stage_intake.py",
    "state/current_status.json",
    "state/learning_coverage.json",
    "state/pass_ledger.json",
    "state/previous_app_migration.json",
    "state/source_manifest.json",
    "docs/ARCHITECTURE.md",
    "docs/BUILD_STATUS.md",
    "docs/CODE_EXPLAINABILITY_STANDARD.md",
    "docs/FILE_MAP.md",
    "docs/IMPLEMENTATION_GUIDE.md",
    "docs/DESKTOP_ARCHITECTURE.md",
    "docs/LEARNING_RESOURCES.md",
    "docs/LINE_BY_LINE_CODE_GUIDE.md",
    "docs/PASS_REPORT_TEMPLATE.md",
    "docs/PREVIOUS_APP_REFERENCE_STUDY.md",
    "docs/PREVIOUS_APP_MERGER_AUDIT.md",
    "docs/REFERENCE_POLICY.md",
    "docs/ROADMAP.md",
    "docs/SOURCE_WALKTHROUGH.md",
    "docs/START_HERE.md",
    "docs/passes/PASS_001_REPORT.md",
    "docs/passes/PASS_002_REPORT.md",
    "docs/passes/PASS_003_REPORT.md",
    "docs/passes/PASS_004_REPORT.md",
    "docs/passes/PASS_005_REPORT.md",
    "docs/passes/PASS_006_REPORT.md",
    "docs/passes/PASS_007_REPORT.md",
    "docs/passes/PASS_008_REPORT.md",
    "docs/passes/PASS_009_REPORT.md",
    "docs/passes/PASS_010_REPORT.md",
    "docs/passes/PASS_011_REPORT.md",
    "docs/passes/PASS_012_REPORT.md",
    "docs/passes/PASS_013_REPORT.md",
    "docs/passes/PASS_014_REPORT.md",
    "docs/passes/PASS_015_REPORT.md",
    "docs/passes/PASS_016_REPORT.md",
    "docs/passes/PASS_017_REPORT.md",
    "docs/passes/PASS_018_REPORT.md",
    "docs/passes/PASS_019_REPORT.md",
    "docs/passes/PASS_020_REPORT.md",
    "docs/passes/PASS_021_REPORT.md",
    "docs/passes/PASS_022_REPORT.md",
    "docs/passes/PASS_023_REPORT.md",
    "docs/passes/PASS_024_REPORT.md",
    "docs/passes/PASS_025_REPORT.md",
    "docs/passes/PASS_026_REPORT.md",
    "docs/passes/PASS_027_REPORT.md",
    "schemas/learning-coverage.schema.json",
    "schemas/previous-app-migration.schema.json",
    "schemas/windows-package-plan.schema.json",
    "tests/test_desktop.py",
    "tests/test_contained_execution.py",
    "tests/test_lifecycle_dry_run.py",
    "tests/test_intake_preview.py",
    "tests/test_previous_app_learning_guide.py",
    "tests/test_runtime_resources.py",
    "tests/test_server.py",
    "tests/test_windows_packaging.py",
    "tests/test_windows_installer.py",
    "tests/test_tool_launch.py",
    "tests/test_tool_version.py",
]

REFERENCE_FOLDERS = [
    "Refrences For Makers Anvil Application",
    "References For Makers Anvil Application",
    "Previous Working MA For References",
]

FORBIDDEN_PRODUCT_TEXT = [
    "C:" + "\\Users\\",
    "/" + "Users/",
    "/" + "home/",
    "One" + "Drive",
    "Mr" + "Dra",
    "BUILD" + "_PASS_009_IMAGE_ROUTE_UI_OUTPUT_PROOF_COMPLETE",
    "makers" + "_anvil_build_pass_012_release_backup_uninstall_dry_run",
]


def product_files() -> list[Path]:
    """Purpose: Return committed-style product files while excluding generated and reference data.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[Path]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = product_files(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    ignored_parts = {
        ".build",
        ".git",
        ".makers-anvil",
        ".pytest_cache",
        "__pycache__",
        "artifacts",
        "node_modules",
    }
    ignored_parts.update(REFERENCE_FOLDERS)
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in ignored_parts for part in path.relative_to(ROOT).parts):
            continue
        files.append(path)
    return files


def check_required_files() -> list[str]:
    """Purpose: Report every required architecture, schema, status, and pass file that is missing.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_required_files(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (ROOT / name).exists()]


def check_reference_policy() -> list[str]:
    """Purpose: Ensure both historical spellings of the reference-only folder remain ignored.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_reference_policy(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    errors = []
    for folder in REFERENCE_FOLDERS:
        if f"{folder}/" not in gitignore:
            errors.append(f"reference folder not ignored: {folder}")
    return errors


def check_forbidden_text() -> list[str]:
    """Purpose: Reject personal paths and stale reference-build markers from product source.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_forbidden_text(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    errors: list[str] = []
    for path in product_files():
        if path.suffix.lower() not in {".py", ".js", ".html", ".css", ".json", ".md", ".toml", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for forbidden in FORBIDDEN_PRODUCT_TEXT:
            if forbidden in text:
                errors.append(f"forbidden product text {forbidden!r} in {path.relative_to(ROOT).as_posix()}")
    return errors


def check_api() -> list[str]:
    """Purpose: Exercise API contracts and confine mutation to authorized one-file intake.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_api(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    api = MakersAnvilApi()
    errors: list[str] = []
    health = api.handle("GET", "/api/health")
    state = api.handle("GET", "/api/state")
    workspace = api.handle("GET", "/api/workspace/status")
    ledger = api.handle("GET", "/api/passes/ledger")
    config = api.handle("GET", "/api/workspace/config")
    layout = api.handle("GET", "/api/workspace/layout")
    intake_policy = api.handle("GET", "/api/intake/policy")
    intake_catalog = api.handle("GET", "/api/intake/catalog")
    intake_session = api.handle("GET", "/api/intake/session")
    intake_preview_policy = api.handle("GET", "/api/intake/previews/policy")
    route_preview = api.handle("GET", "/api/routes/preview")
    output_proof = api.handle("GET", "/api/outputs/preview")
    tool_detection = api.handle("GET", "/api/tools/detection")
    tool_launch = api.handle("GET", "/api/tools/launches/preview")
    tool_dry_run = api.handle("GET", "/api/tools/dry-run")
    execution_gates = api.handle("GET", "/api/execution/gates")
    execution_request = api.handle("GET", "/api/execution/requests/preview")
    job_policy = api.handle("GET", "/api/jobs/policy")
    job_catalog = api.handle("GET", "/api/jobs/catalog")
    experience = api.handle("GET", "/api/workbench/experience")
    activity = api.handle("GET", "/api/activity/recent")
    capability_matrix = api.handle("GET", "/api/capabilities/matrix")
    contained_policy = api.handle("GET", "/api/executions/policy")
    contained_catalog = api.handle("GET", "/api/executions/catalog")
    lifecycle_policy = api.handle("GET", "/api/lifecycle/policy")
    lifecycle_catalog = api.handle("GET", "/api/lifecycle/dry-runs")
    windows_installer_policy = api.handle("GET", "/api/windows/installer/policy")
    windows_installer_readiness = api.handle("GET", "/api/windows/installer/readiness")
    clean_machine_harness = api.handle("GET", "/api/windows/clean-machine/harness")
    blocked = api.handle("POST", "/api/state")
    missing = api.handle("GET", "/api/missing")
    if health.status != 200 or health.body.get("claimState") != "proven":
        errors.append("GET /api/health did not return proven health")
    if health.body.get("mutatingActionsEnabled") is not True:
        errors.append("GET /api/health does not report the bounded intake mutation")
    if health.body.get("enabledMutationScopes") != ["authorized-file-intake", "contained-stl-preflight", "workbench-preferences"]:
        errors.append("GET /api/health exposes an unexpected mutation scope")
    if health.body.get("builtInStlPreflightEnabled") is not True:
        errors.append("GET /api/health does not expose the bounded built-in STL preflight")
    if health.body.get("authorizedRasterPreviewEnabled") is not True:
        errors.append("GET /api/health does not expose verified authorized raster previews")
    if health.body.get("containedArtifactViewerEnabled") is not True:
        errors.append("GET /api/health does not expose the verified contained artifact viewer")
    if health.body.get("containedExecutionHistoryEnabled") is not True or health.body.get("cooperativeCancellationUiEnabled") is not True:
        errors.append("GET /api/health does not expose contained execution history and cancellation UI")
    if health.body.get("toolVersionMetadataEnabled") is not True or health.body.get("toolLaunchReviewEnabled") is not True:
        errors.append("GET /api/health does not expose metadata version and launch-review capability")
    if health.body.get("lifecycleDryRunEnabled") is not True:
        errors.append("GET /api/health does not expose read-only lifecycle planning")
    if health.body.get("windowsInstallerFoundationEnabled") is not True or health.body.get("cleanMachineExecutionEnabled") is not False:
        errors.append("GET /api/health does not expose the blocked Windows installer foundation")
    if health.body.get("routeExecutionEnabled") is not False or health.body.get("toolLaunchEnabled") is not False:
        errors.append("GET /api/health unexpectedly enables route execution or tool launch")
    if state.status != 200 or state.body.get("claimState") not in ALLOWED_CLAIM_STATES:
        errors.append("GET /api/state did not return an allowed claim state")
    enabled_capabilities = [
        capability.get("id")
        for capability in state.body.get("capabilities", [])
        if capability.get("actionsEnabled")
    ]
    if enabled_capabilities != ["file-intake", "workbench-preferences", "contained-stl-preflight"]:
        errors.append("GET /api/state does not limit actions to intake, preferences, and contained STL preflight")
    if state.body.get("currentPass", {}).get("id") != "PASS-027":
        errors.append("GET /api/state does not report PASS-027")
    if state.body.get("capabilityMatrix") != capability_matrix.body:
        errors.append("GET /api/state capability matrix differs from its focused route")
    if workspace.status != 200 or workspace.body.get("currentPass", {}).get("id") != "PASS-027":
        errors.append("GET /api/workspace/status does not report PASS-027")
    if ledger.status != 200 or ledger.body.get("passes", [{}])[-1].get("id") != "PASS-027":
        errors.append("GET /api/passes/ledger does not report PASS-027 as latest")
    desktop_capability = next(
        (item for item in state.body.get("capabilities", []) if item.get("id") == "desktop-shell"),
        None,
    )
    if not desktop_capability or desktop_capability.get("actionsEnabled") is not False:
        errors.append("GET /api/state does not expose the staged non-actionable desktop shell")
    runtime_location = config.body.get("runtimeLocation", {})
    if config.status != 200 or runtime_location.get("mode") != "platform-user-data":
        errors.append("GET /api/workspace/config does not report platform user-data mode")
    if runtime_location.get("sourceRootDependency") is not False:
        errors.append("workspace config unexpectedly depends on the source root")
    if runtime_location.get("absolutePathExposed") is not False:
        errors.append("workspace config unexpectedly exposes an absolute path")
    if "runtimeRoot" in config.body:
        errors.append("workspace config exposes legacy source-adjacent runtimeRoot")
    expected_workspace_safety = {
        "userUploadEnabled": True,
        "routeExecutionEnabled": False,
        "toolLaunchEnabled": False,
        "archiveExtractionEnabled": False,
        "folderImportEnabled": False,
        "deleteUserDataEnabled": False,
        "releasePackagingEnabled": False,
    }
    if config.body.get("safety") != expected_workspace_safety:
        errors.append("workspace config does not limit enabled behavior to user upload")
    if layout.status != 200 or layout.body.get("creationAction", {}).get("enabledInApi") is not False:
        errors.append("GET /api/workspace/layout does not keep API init action disabled")
    if layout.body.get("runtimeLocation", {}).get("logicalRoot") != "makers-anvil-data://user":
        errors.append("GET /api/workspace/layout does not report the logical user-data root")
    if any(Path(item.get("relativePath", "")).is_absolute() for item in layout.body.get("directories", [])):
        errors.append("workspace layout exposes an absolute directory path")
    if intake_policy.status != 200 or intake_policy.body.get("mode") != "authorized-local-copy":
        errors.append("GET /api/intake/policy does not report authorized-local-copy mode")
    if any(intake_policy.body.get("safety", {}).values()):
        errors.append("one or more intake policy safety flags unexpectedly enable unsafe actions")
    expected_intake_capabilities = {
        "apiMutationEnabled": True,
        "browserFilePickerEnabled": True,
        "explicitAuthorizationRequired": True,
        "appOwnedCopyEnabled": True,
        "dragDropEnabled": True,
        "clipboardPasteEnabled": True,
    }
    if intake_policy.body.get("capabilities") != expected_intake_capabilities:
        errors.append("GET /api/intake/policy does not preserve the bounded capability set")
    if "archive" in intake_policy.body.get("uploadAllowedKinds", []):
        errors.append("GET /api/intake/policy unexpectedly allows archive upload")
    if intake_catalog.status != 200 or intake_catalog.body.get("creationAction", {}).get("enabledInApi") is not True:
        errors.append("GET /api/intake/catalog does not expose authorized intake truth")
    if intake_session.status != 200 or intake_session.body.get("mode") != "same-origin-one-file":
        errors.append("GET /api/intake/session does not report same-origin-one-file mode")
    if len(intake_session.body.get("requestToken", "")) < 32:
        errors.append("GET /api/intake/session does not expose a process-local request token")
    if intake_session.body.get("constraints", {}).get("oneFilePerAuthorization") is not True:
        errors.append("GET /api/intake/session does not enforce one file per authorization")
    if intake_preview_policy.status != 200 or intake_preview_policy.body.get("mode") != "verified-app-owned-raster":
        errors.append("GET /api/intake/previews/policy does not expose verified app-owned raster mode")
    preview_safety = intake_preview_policy.body.get("safety", {})
    if not all(preview_safety.get(key) is True for key in ("readOnly", "authorizedRecordRequired", "appOwnedContentRequired", "sizeAndDigestReverified", "rasterSignatureRequired")):
        errors.append("intake preview policy is missing required read and verification proofs")
    if any(preview_safety.get(key) is not False for key in ("sourcePathExposed", "activeContentAllowed", "archiveReadEnabled", "selectedFileHandoffEnabled", "externalProcessEnabled")):
        errors.append("intake preview policy unexpectedly enables an unsafe effect")
    if experience.status != 200 or experience.body.get("schemaVersion") != "makers-anvil.api.workbench-experience.v1":
        errors.append("GET /api/workbench/experience does not expose the staged experience contract")
    if len(experience.body.get("helpTopics", [])) != 6 or any(experience.body.get("safety", {}).values()):
        errors.append("workbench experience help or safety policy is incomplete")
    if activity.status != 200 or activity.body.get("mode") != "server-authored-create-only":
        errors.append("GET /api/activity/recent does not expose create-only server activity")
    if any(activity.body.get("safety", {}).values()):
        errors.append("activity history unexpectedly enables source paths or event changes")
    if capability_matrix.status != 200 or capability_matrix.body.get("summary", {}).get("laneCount") != 5:
        errors.append("GET /api/capabilities/matrix does not expose five supported lanes")
    if any(lane.get("executionReady") is not False for lane in capability_matrix.body.get("lanes", [])):
        errors.append("one or more capability lanes unexpectedly claim execution readiness")
    if any(capability_matrix.body.get("safety", {}).values()):
        errors.append("capability matrix unexpectedly enables a source, route, tool, or output action")
    if ".zip" in intake_session.body.get("constraints", {}).get("allowedExtensions", []):
        errors.append("GET /api/intake/session unexpectedly allows archive extensions")
    if state.body.get("intakeCatalog", {}).get("mode") != "authorized-local-copy":
        errors.append("GET /api/state does not include authorized intake status")
    if route_preview.status != 200 or route_preview.body.get("mode") != "metadata-derived-read-only":
        errors.append("GET /api/routes/preview does not report metadata-derived read-only mode")
    if any(route_preview.body.get("safety", {}).values()):
        errors.append("one or more route preview safety flags unexpectedly enable an action")
    if route_preview.body.get("executionAction", {}).get("enabledInApi") is not False:
        errors.append("route preview unexpectedly enables API execution")
    if state.body.get("routePreview", {}).get("mode") != "metadata-derived-read-only":
        errors.append("GET /api/state does not include route preview status")
    if output_proof.status != 200 or output_proof.body.get("mode") != "route-derived-read-only":
        errors.append("GET /api/outputs/preview does not report route-derived read-only mode")
    if any(output_proof.body.get("safety", {}).values()):
        errors.append("one or more output preview safety flags unexpectedly claim an action")
    if any(action.get("enabledInApi") for action in output_proof.body.get("actions", {}).values()):
        errors.append("output preview unexpectedly enables create or open actions")
    if output_proof.body.get("summary", {}).get("completedProofCount") != 0:
        errors.append("output preview unexpectedly reports completed proof")
    if state.body.get("outputProof", {}).get("mode") != "route-derived-read-only":
        errors.append("GET /api/state does not include output proof status")
    if tool_detection.status != 200 or tool_detection.body.get("mode") != "read-only-presence":
        errors.append("GET /api/tools/detection does not report read-only presence mode")
    if any(tool_detection.body.get("safety", {}).values()):
        errors.append("one or more tool detection safety flags unexpectedly claim an action")
    if any(action.get("enabledInApi") for action in tool_detection.body.get("actions", {}).values()):
        errors.append("tool detection unexpectedly enables a tool or software action")
    if any(tool.get("actionsEnabled") for tool in tool_detection.body.get("tools", [])):
        errors.append("one or more detected tools unexpectedly enable actions")
    if any(tool.get("detection", {}).get("absolutePathExposed") for tool in tool_detection.body.get("tools", [])):
        errors.append("tool detection unexpectedly exposes an absolute path")
    if any(tool.get("version", {}).get("claimState") not in {"proven", "not proven"} for tool in tool_detection.body.get("tools", [])):
        errors.append("tool detection returns an unsupported version claim")
    if any(tool.get("version", {}).get("commandExecuted") is not False for tool in tool_detection.body.get("tools", [])):
        errors.append("tool detection unexpectedly runs a version command")
    if any(tool.get("version", {}).get("absolutePathExposed") is not False for tool in tool_detection.body.get("tools", [])):
        errors.append("tool version evidence unexpectedly exposes an absolute path")
    if state.body.get("toolDetection", {}).get("mode") != "read-only-presence":
        errors.append("GET /api/state does not include tool detection status")
    if tool_launch.status != 200 or tool_launch.body.get("mode") != "confirmation-preview-only":
        errors.append("GET /api/tools/launches/preview does not report preview-only mode")
    if tool_launch.body.get("actions", {}).get("review", {}).get("enabledInApi") is not True:
        errors.append("tool launch catalog does not expose its GET-only review action")
    if any(tool_launch.body.get("actions", {}).get(action, {}).get("enabledInApi") for action in ("confirm", "launch")):
        errors.append("tool launch catalog unexpectedly enables confirmation or launch")
    if any(tool_launch.body.get("safety", {}).values()):
        errors.append("tool launch catalog unexpectedly constructs, persists, exposes, writes, or executes")
    if any(item.get("confirmation", {}).get("accepted") is not False for item in tool_launch.body.get("tools", [])):
        errors.append("tool launch catalog unexpectedly accepts confirmation")
    if any(item.get("binding", {}).get("selectedFileIncluded") is not False or item.get("binding", {}).get("argumentsIncluded") is not False or item.get("binding", {}).get("absolutePathExposed") is not False for item in tool_launch.body.get("tools", [])):
        errors.append("tool launch catalog unexpectedly includes a file, argument, or path")
    if state.body.get("toolLaunchCatalog") != tool_launch.body:
        errors.append("GET /api/state tool launch catalog differs from its focused route")
    if tool_dry_run.status != 200 or tool_dry_run.body.get("mode") != "semantic-invocation-read-only":
        errors.append("GET /api/tools/dry-run does not report semantic read-only mode")
    if any(tool_dry_run.body.get("safety", {}).values()):
        errors.append("tool dry-run unexpectedly constructs, resolves, hands off, executes, launches, or writes")
    if tool_dry_run.body.get("executionAction", {}).get("enabledInApi") is not False:
        errors.append("tool dry-run unexpectedly enables API execution")
    if any(plan.get("invocation", {}).get("commandString") is not None for plan in tool_dry_run.body.get("plans", [])):
        errors.append("tool dry-run unexpectedly returns a runnable command")
    if any(plan.get("readiness", {}).get("executionReady") for plan in tool_dry_run.body.get("plans", [])):
        errors.append("tool dry-run unexpectedly reports execution readiness")
    if state.body.get("toolDryRun", {}).get("mode") != "semantic-invocation-read-only":
        errors.append("GET /api/state does not include tool dry-run status")
    if execution_gates.status != 200 or execution_gates.body.get("mode") != "read-only-gate-evaluation":
        errors.append("GET /api/execution/gates does not report read-only gate evaluation")
    if execution_gates.body.get("scope", {}).get("routeId") != "mesh-to-toolpath":
        errors.append("execution gates do not remain scoped to the single mesh route")
    if execution_gates.body.get("scope", {}).get("executionEnabled") is not False:
        errors.append("execution gate scope unexpectedly enables execution")
    if any(execution_gates.body.get("safety", {}).values()):
        errors.append("execution gates unexpectedly authorize, resolve, construct, execute, write, log, cancel, or prove")
    if execution_gates.body.get("executionAction", {}).get("enabledInApi") is not False:
        errors.append("execution gates unexpectedly enable an API execution action")
    if any(item.get("readiness", {}).get("executionReady") for item in execution_gates.body.get("evaluations", [])):
        errors.append("an execution gate evaluation unexpectedly reports execution readiness")
    if state.body.get("executionGates", {}).get("mode") != "read-only-gate-evaluation":
        errors.append("GET /api/state does not include execution gate status")
    if execution_request.status != 200 or execution_request.body.get("mode") != "read-only-request-preview":
        errors.append("GET /api/execution/requests/preview does not report read-only request preview mode")
    if execution_request.body.get("scope", {}).get("routeId") != "mesh-to-toolpath":
        errors.append("execution request preview does not remain scoped to the single mesh route")
    if any(execution_request.body.get("safety", {}).values()):
        errors.append("execution request preview unexpectedly persists, authorizes, writes, resolves, executes, or proves")
    if any(action.get("enabledInApi") for action in execution_request.body.get("actions", {}).values()):
        errors.append("execution request preview unexpectedly enables an API action")
    if execution_request.body.get("summary", {}).get("persistedRequestCount") != 0:
        errors.append("execution request preview unexpectedly reports a persisted request")
    if execution_request.body.get("summary", {}).get("acceptedAuthorizationCount") != 0:
        errors.append("execution request preview unexpectedly reports accepted authorization")
    if execution_request.body.get("summary", {}).get("writtenAuditEventCount") != 0:
        errors.append("execution request preview unexpectedly reports a written audit event")
    if state.body.get("executionRequestPreview", {}).get("mode") != "read-only-request-preview":
        errors.append("GET /api/state does not include execution request preview status")
    if job_policy.status != 200 or job_policy.body.get("mode") != "contained-local-preparation":
        errors.append("GET /api/jobs/policy does not report contained local preparation")
    if job_policy.body.get("jobsPath") != "makers-anvil-data://user/jobs":
        errors.append("job policy does not expose the logical app-owned jobs root")
    expected_local_actions = {
        "preparationEnabled": True,
        "cancellationRequestEnabled": True,
        "apiMutationEnabled": False,
        "browserMutationEnabled": False,
    }
    if job_policy.body.get("localActions") != expected_local_actions:
        errors.append("job policy local actions do not preserve explicit-script-only mutation")
    if job_catalog.status != 200 or job_catalog.body.get("mode") != "contained-local-preparation":
        errors.append("GET /api/jobs/catalog does not report contained local preparation")
    if job_catalog.body.get("summary", {}).get("executionReadyCount") != 0:
        errors.append("job catalog unexpectedly reports an execution-ready job")
    if any(job_catalog.body.get("safety", {}).values()):
        errors.append("job catalog unexpectedly persists executable intent, authorizes, executes, signals, writes outputs, or proves")
    if any(action.get("enabledInApi") for action in job_catalog.body.get("actions", {}).values()):
        errors.append("job catalog unexpectedly enables an API mutation or execution action")
    if state.body.get("jobWorkspaceCatalog", {}).get("mode") != "contained-local-preparation":
        errors.append("GET /api/state does not include contained job workspace status")
    if contained_policy.status != 200 or contained_policy.body.get("scope", {}).get("operationId") != "built-in-stl-preflight":
        errors.append("GET /api/executions/policy does not preserve the single built-in STL operation")
    if any(contained_policy.body.get("safety", {}).values()):
        errors.append("contained execution policy unexpectedly enables an external or source effect")
    if contained_catalog.status != 200 or contained_catalog.body.get("mode") != "built-in-cooperative-single-operation":
        errors.append("GET /api/executions/catalog does not expose contained preflight truth")
    if contained_catalog.body.get("actions", {}).get("run", {}).get("enabledInApi") is not True:
        errors.append("contained execution catalog does not expose its bounded run action")
    if contained_catalog.body.get("actions", {}).get("openOutput", {}).get("enabledInApi") is not False:
        errors.append("contained execution catalog unexpectedly enables output opening")
    if state.body.get("containedExecutions") != contained_catalog.body:
        errors.append("GET /api/state contained execution catalog differs from focused route")
    if lifecycle_policy.status != 200 or lifecycle_policy.body.get("mode") != "read-only-lifecycle-planning":
        errors.append("GET /api/lifecycle/policy does not expose read-only lifecycle planning")
    if [item.get("id") for item in lifecycle_policy.body.get("operations", [])] != ["backup", "restore", "update", "uninstall", "repair"]:
        errors.append("lifecycle policy does not cover the exact five operations")
    if lifecycle_policy.body.get("backupTarget") != "makers-anvil-data://user/backups":
        errors.append("lifecycle policy does not expose the logical app-owned backup target")
    if any(lifecycle_policy.body.get("safety", {}).values()):
        errors.append("lifecycle policy unexpectedly enables a read, network, archive, installer, mutation, or delete effect")
    if lifecycle_catalog.status != 200 or lifecycle_catalog.body.get("summary", {}).get("operationCount") != 5:
        errors.append("GET /api/lifecycle/dry-runs does not expose five operation previews")
    if lifecycle_catalog.body.get("summary", {}).get("executionReadyCount") != 0:
        errors.append("lifecycle dry runs unexpectedly report execution readiness")
    if any(lifecycle_catalog.body.get("safety", {}).values()):
        errors.append("lifecycle dry runs unexpectedly enable an effect")
    if any(plan.get("readiness", {}).get("executionReady") for plan in lifecycle_catalog.body.get("plans", [])):
        errors.append("a lifecycle plan unexpectedly reports execution readiness")
    if state.body.get("lifecycleDryRuns") != lifecycle_catalog.body:
        errors.append("GET /api/state lifecycle catalog differs from its focused route")
    if windows_installer_policy.status != 200 or windows_installer_policy.body.get("package", {}).get("format") != "msix":
        errors.append("GET /api/windows/installer/policy does not expose the MSIX foundation")
    true_installer_actions = {key for key, enabled in windows_installer_policy.body.get("actions", {}).items() if enabled}
    if true_installer_actions != {"foundationInspectionEnabled", "harnessInspectionEnabled"}:
        errors.append("Windows installer policy enables unexpected actions")
    if any(windows_installer_policy.body.get("safety", {}).values()):
        errors.append("Windows installer policy enables an operating-system or release effect")
    installer_summary = windows_installer_readiness.body.get("summary", {})
    if windows_installer_readiness.status != 200 or installer_summary.get("gateCount") != 9 or installer_summary.get("passedGateCount") != 3:
        errors.append("GET /api/windows/installer/readiness does not expose exact foundation gates")
    if installer_summary.get("installerReady") is not False or installer_summary.get("releaseReady") is not False:
        errors.append("Windows installer readiness makes an unproven release claim")
    harness_summary = clean_machine_harness.body.get("summary", {})
    if clean_machine_harness.status != 200 or harness_summary.get("scenarioCount") != 6 or harness_summary.get("executedCount") != 0:
        errors.append("GET /api/windows/clean-machine/harness does not expose six unexecuted scenarios")
    if harness_summary.get("cleanMachineProven") is not False or any(clean_machine_harness.body.get("safety", {}).values()):
        errors.append("clean-machine harness claims proof or enables a machine effect")
    if state.body.get("windowsInstaller") != windows_installer_readiness.body or state.body.get("cleanMachineHarness") != clean_machine_harness.body:
        errors.append("GET /api/state installer foundation differs from focused routes")
    if blocked.status != 405 or blocked.body.get("claimState") != "blocked":
        errors.append("state-changing API request was not blocked")
    if missing.status != 404 or missing.body.get("claimState") != "not proven":
        errors.append("unknown API request did not return not proven")
    return errors


def check_status_records() -> list[str]:
    """Purpose: Keep status, ledger, settings, planning, request, and job policies synchronized.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_status_records(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    errors: list[str] = []
    status = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))
    intake_policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))
    intake_preview_policy = json.loads((ROOT / "config" / "intake_preview_policy.json").read_text(encoding="utf-8"))
    route_catalog = json.loads((ROOT / "config" / "route_catalog.json").read_text(encoding="utf-8"))
    output_policy = json.loads((ROOT / "config" / "output_policy.json").read_text(encoding="utf-8"))
    tool_catalog = json.loads((ROOT / "config" / "tool_catalog.json").read_text(encoding="utf-8"))
    tool_launch_policy = json.loads((ROOT / "config" / "tool_launch_policy.json").read_text(encoding="utf-8"))
    dry_run_policy = json.loads((ROOT / "config" / "tool_dry_run_policy.json").read_text(encoding="utf-8"))
    execution_gate_policy = json.loads((ROOT / "config" / "execution_gate_policy.json").read_text(encoding="utf-8"))
    execution_request_policy = json.loads((ROOT / "config" / "execution_request_policy.json").read_text(encoding="utf-8"))
    job_workspace_policy = json.loads((ROOT / "config" / "job_workspace_policy.json").read_text(encoding="utf-8"))
    contained_execution_policy = json.loads((ROOT / "config" / "contained_execution_policy.json").read_text(encoding="utf-8"))
    lifecycle_dry_run_policy = json.loads((ROOT / "config" / "lifecycle_dry_run_policy.json").read_text(encoding="utf-8"))
    windows_installer_policy = json.loads((ROOT / "config" / "windows_installer_policy.json").read_text(encoding="utf-8"))
    clean_machine_scenarios = json.loads((ROOT / "config" / "clean_machine_scenarios.json").read_text(encoding="utf-8"))
    experience_policy = json.loads((ROOT / "config" / "workbench_experience.json").read_text(encoding="utf-8"))
    migration = json.loads((ROOT / "state" / "previous_app_migration.json").read_text(encoding="utf-8"))
    windows_plan = package_plan()
    if status.get("currentPass", {}).get("id") != "PASS-027":
        errors.append("current status does not report PASS-027")
    if status.get("trackPercentages", {}).get("realApp") != 89.5:
        errors.append("real app completion is not 89.5 for PASS-027")
    if status.get("referencePolicy", {}).get("runtimeDependency") is not False:
        errors.append("reference policy must keep runtimeDependency false")
    if ledger.get("passes", [{}])[-1].get("id") != "PASS-027":
        errors.append("pass ledger latest pass is not PASS-027")
    if migration.get("runtimeDependency") is not False:
        errors.append("previous app migration registry unexpectedly creates a runtime dependency")
    if any(migration.get("safety", {}).values()):
        errors.append("previous app migration registry unexpectedly imports, enables, or deletes legacy state")
    capability_ids = [item.get("id") for item in migration.get("capabilities", [])]
    if len(capability_ids) != len(set(capability_ids)):
        errors.append("previous app migration registry contains duplicate capability ids")
    if windows_plan.get("expectedArtifact") != "artifacts/windows/MakersAnvil.exe":
        errors.append("Windows package plan does not target the portable MakersAnvil.exe artifact")
    if any(windows_plan.get("safety", {}).values()):
        errors.append("Windows package check plan unexpectedly claims build, signing, publish, install, or clean-machine proof")
    installer_foundation = windows_plan.get("installerFoundation", {})
    if installer_foundation.get("format") != "msix" or installer_foundation.get("expectedArtifact") != "artifacts/windows/MakersAnvil.msix" or installer_foundation.get("installerBuilt") is not False:
        errors.append("Windows executable plan does not expose the blocked MSIX foundation")
    try:
        require_loopback_host("127.0.0.1")
        frontend_root()
    except (OSError, RuntimeError, ValueError) as exc:
        errors.append(f"desktop runtime resource or loopback precondition failed: {exc}")
    runtime_data = settings.get("runtimeData", {})
    if runtime_data.get("mode") != "platform-user-data":
        errors.append("default settings do not use platform user-data mode")
    if runtime_data.get("sourceRootDependency") is not False:
        errors.append("default settings unexpectedly depend on the source root")
    if runtime_data.get("absolutePathExposed") is not False:
        errors.append("default settings unexpectedly expose absolute paths")
    expected_settings_safety = {
        "userUploadEnabled": True,
        "routeExecutionEnabled": False,
        "toolLaunchEnabled": False,
        "archiveExtractionEnabled": False,
        "folderImportEnabled": False,
        "deleteUserDataEnabled": False,
        "releasePackagingEnabled": False,
    }
    if settings.get("safety") != expected_settings_safety:
        errors.append("default settings do not limit enabled behavior to user upload")
    if intake_policy.get("mode") != "authorized-local-copy":
        errors.append("intake policy is not authorized-local-copy")
    if any(intake_policy.get("safety", {}).values()):
        errors.append("intake policy unexpectedly enables an unsafe action")
    expected_intake_capabilities = {
        "apiMutationEnabled": True,
        "browserFilePickerEnabled": True,
        "explicitAuthorizationRequired": True,
        "appOwnedCopyEnabled": True,
        "dragDropEnabled": True,
        "clipboardPasteEnabled": True,
    }
    if intake_policy.get("capabilities") != expected_intake_capabilities:
        errors.append("intake policy capabilities are broader or narrower than PASS-019")
    if "archive" in intake_policy.get("uploadAllowedKinds", []):
        errors.append("intake policy unexpectedly permits archive upload")
    if intake_preview_policy.get("mode") != "verified-app-owned-raster" or intake_preview_policy.get("maxPreviewBytes") != 26_214_400:
        errors.append("intake preview policy identity or size ceiling is invalid")
    preview_safety = intake_preview_policy.get("safety", {})
    if not all(preview_safety.get(key) is True for key in ("readOnly", "authorizedRecordRequired", "appOwnedContentRequired", "sizeAndDigestReverified", "rasterSignatureRequired")):
        errors.append("intake preview policy verification gates are incomplete")
    if any(preview_safety.get(key) is not False for key in ("sourcePathExposed", "activeContentAllowed", "archiveReadEnabled", "selectedFileHandoffEnabled", "externalProcessEnabled")):
        errors.append("intake preview policy enables an unsafe effect")
    if experience_policy.get("schemaVersion") != "makers-anvil.config.workbench-experience.v1":
        errors.append("workbench experience policy schema identity is invalid")
    if any(experience_policy.get("safety", {}).values()):
        errors.append("workbench experience policy unexpectedly enables an unsafe action")
    if experience_policy.get("activity", {}).get("allowedEventTypes") != ["intake-authorized", "intake-copied", "preferences-updated"]:
        errors.append("workbench activity policy event allowlist is invalid")
    if contained_execution_policy.get("mode") != "built-in-cooperative-single-operation":
        errors.append("contained execution policy mode is invalid")
    if contained_execution_policy.get("scope", {}).get("operationId") != "built-in-stl-preflight":
        errors.append("contained execution policy operation scope is invalid")
    if contained_execution_policy.get("scope", {}).get("maxConcurrentExecutions") != 1:
        errors.append("contained execution policy concurrency is not exactly one")
    if any(contained_execution_policy.get("safety", {}).values()):
        errors.append("contained execution policy enables an unsafe effect")
    if lifecycle_dry_run_policy.get("mode") != "read-only-lifecycle-planning":
        errors.append("lifecycle dry-run policy mode is invalid")
    if [item.get("id") for item in lifecycle_dry_run_policy.get("operations", [])] != ["backup", "restore", "update", "uninstall", "repair"]:
        errors.append("lifecycle dry-run policy operation coverage is invalid")
    if lifecycle_dry_run_policy.get("actions", {}).get("previewEnabled") is not True or any(value for key, value in lifecycle_dry_run_policy.get("actions", {}).items() if key != "previewEnabled"):
        errors.append("lifecycle dry-run policy actions are broader or narrower than PASS-021")
    if any(lifecycle_dry_run_policy.get("safety", {}).values()):
        errors.append("lifecycle dry-run policy enables an unsafe effect")
    if windows_installer_policy.get("mode") != "read-only-installer-foundation" or windows_installer_policy.get("package", {}).get("format") != "msix":
        errors.append("Windows installer policy identity is invalid")
    if {key for key, value in windows_installer_policy.get("actions", {}).items() if value} != {"foundationInspectionEnabled", "harnessInspectionEnabled"}:
        errors.append("Windows installer policy action scope is invalid")
    if any(windows_installer_policy.get("safety", {}).values()) or windows_installer_policy.get("removal", {}).get("userDataPurgeEnabled") is not False:
        errors.append("Windows installer policy enables a machine effect or user-data purge")
    if [item.get("id") for item in clean_machine_scenarios.get("scenarios", [])] != ["fresh-install", "first-launch", "upgrade-preserves-data", "repair", "uninstall-preserves-data", "reinstall-after-removal"]:
        errors.append("clean-machine scenario registry coverage is invalid")
    if clean_machine_scenarios.get("actions") != {"inspectEnabled": True, "executeEnabled": False, "recordEvidenceEnabled": False} or any(clean_machine_scenarios.get("safety", {}).values()):
        errors.append("clean-machine scenario registry enables execution, evidence, or a machine effect")
    directory_ids = [item.get("id") for item in settings.get("directories", [])]
    if "backups" not in directory_ids or len(directory_ids) != len(set(directory_ids)):
        errors.append("default settings do not declare one unique app-owned backups directory")
    if route_catalog.get("mode") != "metadata-derived-read-only":
        errors.append("route catalog is not metadata-derived read-only")
    if any(route_catalog.get("safety", {}).values()):
        errors.append("route catalog unexpectedly enables an unsafe action")
    if output_policy.get("mode") != "route-derived-read-only":
        errors.append("output policy is not route-derived read-only")
    if any(output_policy.get("safety", {}).values()):
        errors.append("output policy unexpectedly claims an output or proof action")
    if tool_catalog.get("mode") != "read-only-presence":
        errors.append("tool catalog is not read-only presence detection")
    if any(tool_catalog.get("safety", {}).values()):
        errors.append("tool catalog unexpectedly claims a process or software action")
    if tool_launch_policy.get("mode") != "confirmation-preview-only":
        errors.append("tool launch policy is not confirmation-preview-only")
    if tool_launch_policy.get("scope") != {"launchMode": "tool-only", "requireDetectedTool": True, "requireVersionProof": True, "selectedFileAllowed": False, "argumentsAllowed": False}:
        errors.append("tool launch policy scope is broader or narrower than PASS-027")
    if tool_launch_policy.get("confirmation") != {"required": True, "accepted": False, "persisted": False, "endpointEnabled": False}:
        errors.append("tool launch policy confirmation is not required and unaccepted")
    if tool_launch_policy.get("actions") != {"reviewEnabledInApi": True, "confirmEnabledInApi": False, "launchEnabledInApi": False}:
        errors.append("tool launch policy unexpectedly enables confirmation or launch")
    if any(tool_launch_policy.get("safety", {}).values()):
        errors.append("tool launch policy unexpectedly enables an execution-side effect")
    if dry_run_policy.get("mode") != "semantic-invocation-read-only":
        errors.append("tool dry-run policy is not semantic read-only planning")
    if any(dry_run_policy.get("safety", {}).values()):
        errors.append("tool dry-run policy unexpectedly enables a command, path, handoff, execution, or write action")
    if execution_gate_policy.get("mode") != "read-only-gate-evaluation":
        errors.append("execution gate policy is not read-only evaluation")
    if execution_gate_policy.get("scope", {}).get("routeId") != "mesh-to-toolpath":
        errors.append("execution gate policy does not remain scoped to mesh-to-toolpath")
    if execution_gate_policy.get("scope", {}).get("executionEnabled") is not False:
        errors.append("execution gate policy unexpectedly enables execution")
    if any(execution_gate_policy.get("safety", {}).values()):
        errors.append("execution gate policy unexpectedly claims an execution-side effect")
    if execution_request_policy.get("mode") != "read-only-request-preview":
        errors.append("execution request policy is not read-only preview")
    if execution_request_policy.get("scope", {}).get("routeId") != "mesh-to-toolpath":
        errors.append("execution request policy does not remain scoped to mesh-to-toolpath")
    if any(execution_request_policy.get("safety", {}).values()):
        errors.append("execution request policy unexpectedly claims persistence, authorization, audit, execution, or proof")
    if job_workspace_policy.get("mode") != "contained-local-preparation":
        errors.append("job workspace policy is not contained local preparation")
    if job_workspace_policy.get("scope", {}).get("routeId") != "mesh-to-toolpath":
        errors.append("job workspace policy does not remain scoped to mesh-to-toolpath")
    if job_workspace_policy.get("localActions", {}).get("apiMutationEnabled") is not False:
        errors.append("job workspace policy unexpectedly enables API mutation")
    if any(job_workspace_policy.get("safety", {}).values()):
        errors.append("job workspace policy unexpectedly claims an execution-side effect")
    return errors


def _string_values(value: object) -> list[str]:
    """Purpose: Flatten nested JSON-like values so private-path scanning sees every string.

    Inputs: Caller-supplied ``value`` values from the signature.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = instance._string_values(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in _string_values(child)]
    if isinstance(value, list):
        return [text for child in value for text in _string_values(child)]
    return []


def check_portable_paths() -> list[str]:
    """Purpose: Fail when an API payload exposes the resolved source or user home path.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_portable_paths(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    api = MakersAnvilApi()
    payloads = [
        api.handle("GET", "/api/state").body,
        api.handle("GET", "/api/workspace/config").body,
        api.handle("GET", "/api/workspace/layout").body,
        api.handle("GET", "/api/intake/catalog").body,
        api.handle("GET", "/api/routes/preview").body,
        api.handle("GET", "/api/outputs/preview").body,
        api.handle("GET", "/api/tools/detection").body,
        api.handle("GET", "/api/tools/dry-run").body,
        api.handle("GET", "/api/execution/gates").body,
        api.handle("GET", "/api/execution/requests/preview").body,
        api.handle("GET", "/api/jobs/policy").body,
        api.handle("GET", "/api/jobs/catalog").body,
        api.handle("GET", "/api/windows/installer/policy").body,
        api.handle("GET", "/api/windows/installer/readiness").body,
        api.handle("GET", "/api/windows/clean-machine/harness").body,
    ]
    values = [text for payload in payloads for text in _string_values(payload)]
    private_paths = {str(ROOT.resolve()), str(Path.home().resolve())}
    errors = []
    for private_path in private_paths:
        if any(private_path and private_path in value for value in values):
            errors.append("read-only API exposes a resolved source or home path")
            break
    return errors


def check_json_files() -> list[str]:
    """Purpose: Parse every product JSON file so malformed contracts fail verification.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then handles expected failures explicitly, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = check_json_files(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    errors = []
    for path in product_files():
        if path.suffix.lower() != ".json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"json parse failed: {path.relative_to(ROOT).as_posix()}: {exc}")
    return errors


def main() -> int:
    """Purpose: Run all project gates, print one machine-readable result, and set the exit code.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``int``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Verification never imports reference folders or changes user data.
    Example: Call ``result = main(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_verify_project.py`` and CI workflow.
    """

    checks = {
        "required_files": check_required_files(),
        "reference_policy": check_reference_policy(),
        "forbidden_text": check_forbidden_text(),
        "api": check_api(),
        "json_files": check_json_files(),
        "status_records": check_status_records(),
        "portable_paths": check_portable_paths(),
        "explainability": check_explainability(),
    }
    failures = [message for messages in checks.values() for message in messages]
    result = {
        "schemaVersion": "makers-anvil.verify-project.v1",
        "claimState": "proven" if not failures else "failed",
        "checks": {name: {"passed": not messages, "messages": messages} for name, messages in checks.items()},
        "passed": not failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
