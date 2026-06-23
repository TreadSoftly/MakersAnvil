"""Verify the current Makers Anvil product source boundary."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.api.app import MakersAnvilApi  # noqa: E402
from makers_anvil_backend.domain.claim_state import ALLOWED_CLAIM_STATES  # noqa: E402

REQUIRED_FILES = [
    ".gitignore",
    "README.md",
    "package.json",
    "pyproject.toml",
    "backend/src/makers_anvil_backend/api/app.py",
    "backend/src/makers_anvil_backend/server.py",
    "backend/src/makers_anvil_backend/services/intake_catalog.py",
    "backend/src/makers_anvil_backend/services/runtime_paths.py",
    "backend/src/makers_anvil_backend/services/workspace_config.py",
    "backend/src/makers_anvil_backend/services/workspace_status.py",
    "config/default_settings.json",
    "config/intake_policy.json",
    "frontend/public/index.html",
    "frontend/public/assets/app.js",
    "frontend/public/assets/styles.css",
    "schemas/claim-state.schema.json",
    "schemas/app-state.schema.json",
    "schemas/current-status.schema.json",
    "schemas/local-settings.schema.json",
    "schemas/runtime-location.schema.json",
    "schemas/intake-policy.schema.json",
    "schemas/intake-record.schema.json",
    "scripts/init_workspace.py",
    "scripts/stage_intake.py",
    "state/current_status.json",
    "state/pass_ledger.json",
    "docs/BUILD_STATUS.md",
    "docs/passes/PASS_001_REPORT.md",
    "docs/passes/PASS_002_REPORT.md",
    "docs/passes/PASS_003_REPORT.md",
    "docs/passes/PASS_004_REPORT.md",
    "docs/passes/PASS_005_REPORT.md",
]

REFERENCE_FOLDERS = [
    "Refrences For Makers Anvil Application",
    "References For Makers Anvil Application",
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
    return [f"missing required file: {name}" for name in REQUIRED_FILES if not (ROOT / name).exists()]


def check_reference_policy() -> list[str]:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    errors = []
    for folder in REFERENCE_FOLDERS:
        if f"{folder}/" not in gitignore:
            errors.append(f"reference folder not ignored: {folder}")
    return errors


def check_forbidden_text() -> list[str]:
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
    blocked = api.handle("POST", "/api/state")
    missing = api.handle("GET", "/api/missing")
    if health.status != 200 or health.body.get("claimState") != "proven":
        errors.append("GET /api/health did not return proven health")
    if state.status != 200 or state.body.get("claimState") not in ALLOWED_CLAIM_STATES:
        errors.append("GET /api/state did not return an allowed claim state")
    if any(capability.get("actionsEnabled") for capability in state.body.get("capabilities", [])):
        errors.append("one or more capabilities unexpectedly enable actions")
    if state.body.get("currentPass", {}).get("id") != "PASS-005":
        errors.append("GET /api/state does not report PASS-005")
    if workspace.status != 200 or workspace.body.get("currentPass", {}).get("id") != "PASS-005":
        errors.append("GET /api/workspace/status does not report PASS-005")
    if ledger.status != 200 or ledger.body.get("passes", [{}])[-1].get("id") != "PASS-005":
        errors.append("GET /api/passes/ledger does not report PASS-005 as latest")
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
    if blocked.status != 405 or blocked.body.get("claimState") != "blocked":
        errors.append("state-changing API request was not blocked")
    if missing.status != 404 or missing.body.get("claimState") != "not proven":
        errors.append("unknown API request did not return not proven")
    return errors


def check_status_records() -> list[str]:
    errors: list[str] = []
    status = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))
    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))
    intake_policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))
    if status.get("currentPass", {}).get("id") != "PASS-005":
        errors.append("current status does not report PASS-005")
    if status.get("trackPercentages", {}).get("realApp") != 12.5:
        errors.append("real app completion is not 12.5 for PASS-005")
    if status.get("referencePolicy", {}).get("runtimeDependency") is not False:
        errors.append("reference policy must keep runtimeDependency false")
    if ledger.get("passes", [{}])[-1].get("id") != "PASS-005":
        errors.append("pass ledger latest pass is not PASS-005")
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
    return errors


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for child in value.values() for text in _string_values(child)]
    if isinstance(value, list):
        return [text for child in value for text in _string_values(child)]
    return []


def check_portable_paths() -> list[str]:
    api = MakersAnvilApi()
    payloads = [
        api.handle("GET", "/api/state").body,
        api.handle("GET", "/api/workspace/config").body,
        api.handle("GET", "/api/workspace/layout").body,
        api.handle("GET", "/api/intake/catalog").body,
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
    checks = {
        "required_files": check_required_files(),
        "reference_policy": check_reference_policy(),
        "forbidden_text": check_forbidden_text(),
        "api": check_api(),
        "json_files": check_json_files(),
        "status_records": check_status_records(),
        "portable_paths": check_portable_paths(),
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
