"""Verify that every tracked file and public code component is explained."""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "state" / "source_manifest.json"
PYTHON_ROOTS = (ROOT / "backend", ROOT / "scripts", ROOT / "tests")
REQUIRED_GUIDES = {
    "implementationGuidePath": "docs/IMPLEMENTATION_GUIDE.md",
    "learningResourcesPath": "docs/LEARNING_RESOURCES.md",
    "passReportTemplatePath": "docs/PASS_REPORT_TEMPLATE.md",
}


def tracked_files() -> list[str]:
    """Return tracked and pending product paths, or manifest paths outside Git."""

    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return sorted(line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
    manifest = load_manifest()
    return sorted(entry["path"] for entry in manifest.get("files", []))


def load_manifest() -> dict[str, Any]:
    """Load the machine-readable explanation and ownership record."""

    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_manifest_coverage() -> list[str]:
    """Require one detailed, unique manifest entry for every product file."""

    manifest = load_manifest()
    entries = manifest.get("files", [])
    paths = [entry.get("path", "") for entry in entries]
    errors: list[str] = []
    if manifest.get("schemaVersion") != "makers-anvil.source-manifest.v1":
        errors.append("source manifest schemaVersion is not makers-anvil.source-manifest.v1")
    for field, expected_path in REQUIRED_GUIDES.items():
        if manifest.get(field) != expected_path:
            errors.append(f"source manifest {field} must be {expected_path}")
        if not (ROOT / expected_path).is_file():
            errors.append(f"required durable guide is missing: {expected_path}")
    if paths != sorted(paths):
        errors.append("source manifest file entries are not sorted by path")
    if len(paths) != len(set(paths)):
        errors.append("source manifest contains duplicate file paths")

    expected = set(tracked_files())
    documented = set(paths)
    for path in sorted(expected - documented):
        errors.append(f"tracked file missing source-manifest explanation: {path}")
    for path in sorted(documented - expected):
        errors.append(f"source-manifest entry does not exist in product files: {path}")

    for entry in entries:
        path = entry.get("path", "<missing path>")
        if len(entry.get("purpose", "").strip()) < 20:
            errors.append(f"source-manifest purpose is too short: {path}")
        if len(entry.get("maintenanceNotes", "").strip()) < 20:
            errors.append(f"source-manifest maintenanceNotes are too short: {path}")
    return errors


def check_python_docstrings() -> list[str]:
    """Require module and component docstrings throughout Python code."""

    errors: list[str] = []
    paths = sorted(path for root in PYTHON_ROOTS for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(ROOT).as_posix()
        if ast.get_docstring(tree) is None:
            errors.append(f"Python module docstring missing: {relative}")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if ast.get_docstring(node) is None:
                errors.append(f"Python component docstring missing: {relative}:{node.lineno} {node.name}")
    return errors


def check_javascript_function_comments() -> list[str]:
    """Require nearby JSDoc for each top-level frontend function declaration."""

    relative = "frontend/public/assets/app.js"
    lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
    declaration = re.compile(r"^(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
    errors: list[str] = []
    for index, line in enumerate(lines):
        match = declaration.match(line.strip())
        if not match:
            continue
        nearby = "\n".join(lines[max(0, index - 6):index])
        if "/**" not in nearby or "*/" not in nearby:
            errors.append(f"frontend function JSDoc missing: {relative}:{index + 1} {match.group(1)}")
    return errors


def check_text_file_headers() -> list[str]:
    """Require non-visible purpose comments in frontend assets and CI workflow."""

    rules = {
        ".github/workflows/ci.yml": "#",
        "frontend/public/assets/app.js": "/**",
        "frontend/public/assets/mark.svg": "<!--",
        "frontend/public/assets/styles.css": "/*",
    }
    errors: list[str] = []
    for relative, prefix in rules.items():
        text = (ROOT / relative).read_text(encoding="utf-8").lstrip()
        if not text.startswith(prefix):
            errors.append(f"purpose comment missing from file header: {relative}")
    html = (ROOT / "frontend" / "public" / "index.html").read_text(encoding="utf-8")
    if "<!--" not in "\n".join(html.splitlines()[:12]):
        errors.append("purpose comment missing from HTML header: frontend/public/index.html")
    return errors


def run_checks() -> list[str]:
    """Run all explainability gates and return human-readable failures."""

    return [
        *check_manifest_coverage(),
        *check_python_docstrings(),
        *check_javascript_function_comments(),
        *check_text_file_headers(),
    ]


def main() -> int:
    """Print one machine-readable explainability result and return its exit code."""

    errors = run_checks()
    result = {
        "schemaVersion": "makers-anvil.verify-explainability.v1",
        "claimState": "proven" if not errors else "failed",
        "passed": not errors,
        "fileCount": len(tracked_files()),
        "messages": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
