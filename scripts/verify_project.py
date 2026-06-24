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
from scripts.check_explainability import run_checks as check_explainability  # noqa: E402

REQUIRED_FILES = [
    ".gitignore",
    "README.md",
    "package.json",
    "pyproject.toml",
    "backend/src/makers_anvil_backend/api/app.py",
    "backend/src/makers_anvil_backend/server.py",
    "backend/src/makers_anvil_backend/services/execution_gate.py",
    "backend/src/makers_anvil_backend/services/execution_request.py",
    "backend/src/makers_anvil_backend/services/intake_catalog.py",
    "backend/src/makers_anvil_backend/services/job_records.py",
    "backend/src/makers_anvil_backend/services/job_workspace.py",
    "backend/src/makers_anvil_backend/services/output_proof.py",
    "backend/src/makers_anvil_backend/services/route_preview.py",
    "backend/src/makers_anvil_backend/services/runtime_paths.py",
    "backend/src/makers_anvil_backend/services/tool_detection.py",
    "backend/src/makers_anvil_backend/services/tool_dry_run.py",
    "backend/src/makers_anvil_backend/services/workspace_config.py",
    "backend/src/makers_anvil_backend/services/workspace_status.py",
    "config/default_settings.json",
    "config/execution_gate_policy.json",
    "config/execution_request_policy.json",
    "config/intake_policy.json",
    "config/job_workspace_policy.json",
    "config/output_policy.json",
    "config/route_catalog.json",
    "config/tool_catalog.json",
    "config/tool_dry_run_policy.json",
    "frontend/public/index.html",
    "frontend/public/assets/app.js",
    "frontend/public/assets/styles.css",
    "schemas/claim-state.schema.json",
    "schemas/app-state.schema.json",
    "schemas/current-status.schema.json",
    "schemas/execution-gate-policy.schema.json",
    "schemas/execution-gates.schema.json",
    "schemas/execution-request-policy.schema.json",
    "schemas/execution-request-preview.schema.json",
    "schemas/local-settings.schema.json",
    "schemas/runtime-location.schema.json",
    "schemas/intake-policy.schema.json",
    "schemas/intake-record.schema.json",
    "schemas/job-cancellation-record.schema.json",
    "schemas/job-workspace-catalog.schema.json",
    "schemas/job-workspace-policy.schema.json",
    "schemas/job-workspace-record.schema.json",
    "schemas/output-policy.schema.json",
    "schemas/output-proof.schema.json",
    "schemas/route-catalog.schema.json",
    "schemas/route-preview.schema.json",
    "schemas/tool-catalog.schema.json",
    "schemas/tool-detection.schema.json",
    "schemas/tool-dry-run-policy.schema.json",
    "schemas/tool-dry-run.schema.json",
    "scripts/init_workspace.py",
    "scripts/check_explainability.py",
    "scripts/prepare_job.py",
    "scripts/request_job_cancel.py",
    "scripts/stage_intake.py",
    "state/current_status.json",
    "state/pass_ledger.json",
    "state/source_manifest.json",
    "docs/ARCHITECTURE.md",
    "docs/BUILD_STATUS.md",
    "docs/CODE_EXPLAINABILITY_STANDARD.md",
    "docs/FILE_MAP.md",
    "docs/IMPLEMENTATION_GUIDE.md",
    "docs/LEARNING_RESOURCES.md",
    "docs/PASS_REPORT_TEMPLATE.md",
    "docs/PREVIOUS_APP_REFERENCE_STUDY.md",
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
    """Return committed-style product files while excluding generated and reference data."""

    ignored_parts = {".git", ".makers-anvil", "__pycache__", ".pytest_cache", "node_modules"}
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
    """Report every required architecture, schema, status, and pass file that is missing."""

    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (ROOT / name).exists()]


def check_reference_policy() -> list[str]:
    """Ensure both historical spellings of the reference-only folder remain ignored."""

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    errors = []
    for folder in REFERENCE_FOLDERS:
        if f"{folder}/" not in gitignore:
            errors.append(f"reference folder not ignored: {folder}")
    return errors


def check_forbidden_text() -> list[str]:
    """Reject personal paths and stale reference-build markers from product source."""

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
    """Exercise read-only API contracts and confirm every mutation remains blocked."""

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
    route_preview = api.handle("GET", "/api/routes/preview")
    output_proof = api.handle("GET", "/api/outputs/preview")
    tool_detection = api.handle("GET", "/api/tools/detection")
    tool_dry_run = api.handle("GET", "/api/tools/dry-run")
    execution_gates = api.handle("GET", "/api/execution/gates")
    execution_request = api.handle("GET", "/api/execution/requests/preview")
    job_policy = api.handle("GET", "/api/jobs/policy")
    job_catalog = api.handle("GET", "/api/jobs/catalog")
    blocked = api.handle("POST", "/api/state")
    missing = api.handle("GET", "/api/missing")
    if health.status != 200 or health.body.get("claimState") != "proven":
        errors.append("GET /api/health did not return proven health")
    if state.status != 200 or state.body.get("claimState") not in ALLOWED_CLAIM_STATES:
        errors.append("GET /api/state did not return an allowed claim state")
    if any(capability.get("actionsEnabled") for capability in state.body.get("capabilities", [])):
        errors.append("one or more capabilities unexpectedly enable actions")
    if state.body.get("currentPass", {}).get("id") != "PASS-015":
        errors.append("GET /api/state does not report PASS-015")
    if workspace.status != 200 or workspace.body.get("currentPass", {}).get("id") != "PASS-015":
        errors.append("GET /api/workspace/status does not report PASS-015")
    if ledger.status != 200 or ledger.body.get("passes", [{}])[-1].get("id") != "PASS-015":
        errors.append("GET /api/passes/ledger does not report PASS-015 as latest")
    runtime_location = config.body.get("runtimeLocation", {})
    if config.status != 200 or runtime_location.get("mode") != "platform-user-data":
        errors.append("GET /api/workspace/config does not report platform user-data mode")
    if runtime_location.get("sourceRootDependency") is not False:
        errors.append("workspace config unexpectedly depends on the source root")
    if runtime_location.get("absolutePathExposed") is not False:
        errors.append("workspace config unexpectedly exposes an absolute path")
    if "runtimeRoot" in config.body:
        errors.append("workspace config exposes legacy source-adjacent runtimeRoot")
    if any(config.body.get("safety", {}).values()):
        errors.append("one or more workspace config safety flags unexpectedly enable unsafe actions")
    if layout.status != 200 or layout.body.get("creationAction", {}).get("enabledInApi") is not False:
        errors.append("GET /api/workspace/layout does not keep API init action disabled")
    if layout.body.get("runtimeLocation", {}).get("logicalRoot") != "makers-anvil-data://user":
        errors.append("GET /api/workspace/layout does not report the logical user-data root")
    if any(Path(item.get("relativePath", "")).is_absolute() for item in layout.body.get("directories", [])):
        errors.append("workspace layout exposes an absolute directory path")
    if intake_policy.status != 200 or intake_policy.body.get("mode") != "metadata-only":
        errors.append("GET /api/intake/policy does not report metadata-only mode")
    if any(intake_policy.body.get("safety", {}).values()):
        errors.append("one or more intake policy safety flags unexpectedly enable unsafe actions")
    if intake_catalog.status != 200 or intake_catalog.body.get("creationAction", {}).get("enabledInApi") is not False:
        errors.append("GET /api/intake/catalog does not keep API intake action disabled")
    if state.body.get("intakeCatalog", {}).get("mode") != "metadata-only":
        errors.append("GET /api/state does not include metadata-only intake status")
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
    if any(tool.get("version", {}).get("claimState") != "not proven" for tool in tool_detection.body.get("tools", [])):
        errors.append("tool detection unexpectedly claims version proof")
    if state.body.get("toolDetection", {}).get("mode") != "read-only-presence":
        errors.append("GET /api/state does not include tool detection status")
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
    if blocked.status != 405 or blocked.body.get("claimState") != "blocked":
        errors.append("state-changing API request was not blocked")
    if missing.status != 404 or missing.body.get("claimState") != "not proven":
        errors.append("unknown API request did not return not proven")
    return errors


def check_status_records() -> list[str]:
    """Keep status, ledger, settings, planning, request, and job policies synchronized."""

    errors: list[str] = []
    status = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))
    intake_policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))
    route_catalog = json.loads((ROOT / "config" / "route_catalog.json").read_text(encoding="utf-8"))
    output_policy = json.loads((ROOT / "config" / "output_policy.json").read_text(encoding="utf-8"))
    tool_catalog = json.loads((ROOT / "config" / "tool_catalog.json").read_text(encoding="utf-8"))
    dry_run_policy = json.loads((ROOT / "config" / "tool_dry_run_policy.json").read_text(encoding="utf-8"))
    execution_gate_policy = json.loads((ROOT / "config" / "execution_gate_policy.json").read_text(encoding="utf-8"))
    execution_request_policy = json.loads((ROOT / "config" / "execution_request_policy.json").read_text(encoding="utf-8"))
    job_workspace_policy = json.loads((ROOT / "config" / "job_workspace_policy.json").read_text(encoding="utf-8"))
    if status.get("currentPass", {}).get("id") != "PASS-015":
        errors.append("current status does not report PASS-015")
    if status.get("trackPercentages", {}).get("realApp") != 35.0:
        errors.append("real app completion is not 35.0 for PASS-015")
    if status.get("referencePolicy", {}).get("runtimeDependency") is not False:
        errors.append("reference policy must keep runtimeDependency false")
    if ledger.get("passes", [{}])[-1].get("id") != "PASS-015":
        errors.append("pass ledger latest pass is not PASS-015")
    runtime_data = settings.get("runtimeData", {})
    if runtime_data.get("mode") != "platform-user-data":
        errors.append("default settings do not use platform user-data mode")
    if runtime_data.get("sourceRootDependency") is not False:
        errors.append("default settings unexpectedly depend on the source root")
    if runtime_data.get("absolutePathExposed") is not False:
        errors.append("default settings unexpectedly expose absolute paths")
    if any(settings.get("safety", {}).values()):
        errors.append("default settings unexpectedly enable an unsafe action")
    if intake_policy.get("mode") != "metadata-only":
        errors.append("intake policy is not metadata-only")
    if any(intake_policy.get("safety", {}).values()):
        errors.append("intake policy unexpectedly enables an unsafe action")
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
    """Flatten nested JSON-like values so private-path scanning sees every string."""

    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in _string_values(child)]
    if isinstance(value, list):
        return [text for child in value for text in _string_values(child)]
    return []


def check_portable_paths() -> list[str]:
    """Fail when an API payload exposes the resolved source or user home path."""

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
    """Parse every product JSON file so malformed contracts fail verification."""

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
    """Run all project gates, print one machine-readable result, and set the exit code."""

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
