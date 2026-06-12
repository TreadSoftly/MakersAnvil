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
    "backend/src/makers_anvil_backend/services/workspace_status.py",
    "frontend/public/index.html",
    "frontend/public/assets/app.js",
    "frontend/public/assets/styles.css",
    "schemas/claim-state.schema.json",
    "schemas/app-state.schema.json",
    "schemas/current-status.schema.json",
    "state/current_status.json",
    "state/pass_ledger.json",
    "docs/BUILD_STATUS.md",
    "docs/passes/PASS_001_REPORT.md",
    "docs/passes/PASS_002_REPORT.md",
]

REFERENCE_FOLDERS = [
    "Refrences For Makers Anvil Application",
    "References For Makers Anvil Application",
]

FORBIDDEN_PRODUCT_TEXT = [
    "C:" + "\\Users\\",
    "BUILD" + "_PASS_009_IMAGE_ROUTE_UI_OUTPUT_PROOF_COMPLETE",
    "makers" + "_anvil_build_pass_012_release_backup_uninstall_dry_run",
]


def product_files() -> list[Path]:
    ignored_parts = {".git", "__pycache__", ".pytest_cache", "node_modules"}
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
    blocked = api.handle("POST", "/api/state")
    missing = api.handle("GET", "/api/missing")
    if health.status != 200 or health.body.get("claimState") != "proven":
        errors.append("GET /api/health did not return proven health")
    if state.status != 200 or state.body.get("claimState") not in ALLOWED_CLAIM_STATES:
        errors.append("GET /api/state did not return an allowed claim state")
    if any(capability.get("actionsEnabled") for capability in state.body.get("capabilities", [])):
        errors.append("one or more capabilities unexpectedly enable actions")
    if state.body.get("currentPass", {}).get("id") != "PASS-002":
        errors.append("GET /api/state does not report PASS-002")
    if workspace.status != 200 or workspace.body.get("currentPass", {}).get("id") != "PASS-002":
        errors.append("GET /api/workspace/status does not report PASS-002")
    if ledger.status != 200 or ledger.body.get("passes", [{}])[-1].get("id") != "PASS-002":
        errors.append("GET /api/passes/ledger does not report PASS-002 as latest")
    if blocked.status != 405 or blocked.body.get("claimState") != "blocked":
        errors.append("state-changing API request was not blocked")
    if missing.status != 404 or missing.body.get("claimState") != "not proven":
        errors.append("unknown API request did not return not proven")
    return errors


def check_status_records() -> list[str]:
    errors: list[str] = []
    status = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))
    if status.get("currentPass", {}).get("id") != "PASS-002":
        errors.append("current status does not report PASS-002")
    if status.get("trackPercentages", {}).get("realApp") != 5.0:
        errors.append("real app completion is not 5.0 for PASS-002")
    if status.get("referencePolicy", {}).get("runtimeDependency") is not False:
        errors.append("reference policy must keep runtimeDependency false")
    if ledger.get("passes", [{}])[-1].get("id") != "PASS-002":
        errors.append("pass ledger latest pass is not PASS-002")
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
