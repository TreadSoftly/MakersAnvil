"""Purpose: Enforce durable, visible explanations throughout product source.

Used by: The project verifier, CI, direct developer checks, and tests.
Inputs: Tracked files, source manifest, module headers, component docs, and guides.
Outputs: One JSON result listing every missing or stale explanation requirement.
Side effects: Reads repository files and Git metadata; writes nothing.
Safety: Deterministic checks prevent functional work from bypassing handoff quality.
Failure behavior: Any gap produces a nonzero exit with an actionable file location.
Related proof: ``tests/test_explainability.py`` and source-manifest schema.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path
from typing import Any

try:
    from scripts import build_learning_guide
except (ImportError, ModuleNotFoundError):  # Direct execution places ``scripts`` first.
    import build_learning_guide  # type: ignore[no-redef]


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "state" / "source_manifest.json"
PYTHON_ROOTS = (ROOT / "backend", ROOT / "scripts", ROOT / "tests")
REQUIRED_GUIDES = {
    "implementationGuidePath": "docs/IMPLEMENTATION_GUIDE.md",
    "learningResourcesPath": "docs/LEARNING_RESOURCES.md",
    "passReportTemplatePath": "docs/PASS_REPORT_TEMPLATE.md",
    "sourceWalkthroughPath": "docs/SOURCE_WALKTHROUGH.md",
    "referenceStudyPath": "docs/PREVIOUS_APP_REFERENCE_STUDY.md",
    "lineByLineGuidePath": "docs/LINE_BY_LINE_CODE_GUIDE.md",
    "learningCoveragePath": "state/learning_coverage.json",
}
REQUIRED_CONTEXT_LABELS = (
    "Purpose:",
    "Used by:",
    "Inputs:",
    "Outputs:",
    "Side effects:",
    "Safety:",
    "Failure behavior:",
    "Related proof:",
)
REQUIRED_COMPONENT_LABELS = (
    "Purpose:",
    "Inputs:",
    "Outputs:",
    "How it works:",
    "Side effects:",
    "Failure behavior:",
    "Safety:",
    "Example:",
    "Related proof:",
)


def tracked_files() -> list[str]:
    """Purpose: Return tracked and pending product paths, or manifest paths outside Git.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = tracked_files(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        paths = (line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip())
        return sorted(relative for relative in paths if (ROOT / relative).is_file())
    manifest = load_manifest()
    return sorted(entry["path"] for entry in manifest.get("files", []))


def load_manifest() -> dict[str, Any]:
    """Purpose: Load the machine-readable explanation and ownership record.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = load_manifest(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_manifest_coverage() -> list[str]:
    """Purpose: Require one detailed, unique manifest entry for every product file.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_manifest_coverage(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

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
    """Purpose: Require structured module context and component docs throughout Python.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_python_docstrings(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    errors: list[str] = []
    paths = sorted(path for root in PYTHON_ROOTS for path in root.rglob("*.py") if "__pycache__" not in path.parts)
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative = path.relative_to(ROOT).as_posix()
        module_doc = ast.get_docstring(tree, clean=False)
        if module_doc is None:
            errors.append(f"Python module docstring missing: {relative}")
        else:
            for label in REQUIRED_CONTEXT_LABELS:
                if label not in module_doc:
                    errors.append(f"Python module context missing {label} {relative}:1")
        for node in ast.walk(tree):
            if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            component_doc = ast.get_docstring(node)
            if component_doc is None:
                errors.append(f"Python component docstring missing: {relative}:{node.lineno} {node.name}")
            else:
                for label in REQUIRED_COMPONENT_LABELS:
                    if label not in component_doc:
                        errors.append(f"Python component context missing {label} {relative}:{node.lineno} {node.name}")
    return errors


def check_javascript_function_comments() -> list[str]:
    """Purpose: Require nearby JSDoc for every exported frontend operation/component.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_javascript_function_comments(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    errors: list[str] = []
    declaration = re.compile(r"^export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(")
    for path in sorted((ROOT / "frontend" / "src").rglob("*.ts*")):
        relative = path.relative_to(ROOT).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = declaration.match(line.strip())
            if not match:
                continue
            nearby = "\n".join(lines[max(0, index - 12):index])
            if "/**" not in nearby or "*/" not in nearby:
                errors.append(f"frontend export JSDoc missing: {relative}:{index + 1} {match.group(1)}")
    return errors


def check_frontend_block_comments() -> list[str]:
    """Purpose: Require structured teaching headers plus generated every-line frontend coverage.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_frontend_block_comments(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    styles = (ROOT / "frontend" / "src" / "styles.css").read_text(encoding="utf-8")
    app = (ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")
    errors: list[str] = []
    if "Purpose:" not in "\n".join(styles.splitlines()[:16]):
        errors.append("frontend stylesheet teaching header missing: frontend/src/styles.css:1")
    if "Purpose:" not in "\n".join(app.splitlines()[:16]):
        errors.append("frontend application teaching header missing: frontend/src/App.tsx:1")
    return errors


def check_learning_coverage() -> list[str]:
    """Purpose: Require generated teaching artifacts to match every selected source byte.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then handles expected failures explicitly, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_learning_coverage(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    errors: list[str] = []
    try:
        expected_guide, expected_coverage, coverage = build_learning_guide.build_outputs()
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError) as error:
        return [f"learning guide generation failed: {error}"]
    if not build_learning_guide.GUIDE_PATH.is_file():
        errors.append("line-by-line code guide is missing")
    elif build_learning_guide.GUIDE_PATH.read_text(encoding="utf-8") != expected_guide:
        errors.append("line-by-line code guide is stale")
    if not build_learning_guide.COVERAGE_PATH.is_file():
        errors.append("learning coverage record is missing")
    elif build_learning_guide.COVERAGE_PATH.read_text(encoding="utf-8") != expected_coverage:
        errors.append("learning coverage record is stale")
    if coverage["totalLineCount"] != coverage["explainedLineCount"]:
        errors.append("learning guide does not explain every selected physical line")
    return errors


def check_text_file_headers() -> list[str]:
    """Purpose: Require structured context headers in frontend assets and CI workflow.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = check_text_file_headers(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    rules = {".github/workflows/ci.yml": "#"}
    for path in sorted((ROOT / "frontend" / "src").rglob("*.ts")) + sorted((ROOT / "frontend" / "src").rglob("*.tsx")):
        rules[path.relative_to(ROOT).as_posix()] = "/**"
    rules["frontend/src/styles.css"] = "/*"
    rules["frontend/vite.config.ts"] = "/**"
    errors: list[str] = []
    for relative, prefix in rules.items():
        text = (ROOT / relative).read_text(encoding="utf-8").lstrip()
        if not text.startswith(prefix):
            errors.append(f"purpose comment missing from file header: {relative}")
            continue
        header = "\n".join(text.splitlines()[:16])
        for label in REQUIRED_CONTEXT_LABELS:
            if label not in header:
                errors.append(f"structured header missing {label} {relative}:1")
    html = (ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
    if "<!--" not in "\n".join(html.splitlines()[:12]):
        errors.append("purpose comment missing from HTML header: frontend/index.html")
    html_header = "\n".join(html.splitlines()[:18])
    for label in REQUIRED_CONTEXT_LABELS:
        if label not in html_header:
            errors.append(f"structured header missing {label} frontend/index.html:1")
    return errors


def run_checks() -> list[str]:
    """Purpose: Run all explainability gates and return human-readable failures.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``list[str]``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = run_checks(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

    return [
        *check_manifest_coverage(),
        *check_python_docstrings(),
        *check_javascript_function_comments(),
        *check_frontend_block_comments(),
        *check_text_file_headers(),
        *check_learning_coverage(),
    ]


def main() -> int:
    """Purpose: Print one machine-readable explainability result and return its exit code.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``int``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Deterministic checks prevent functional work from bypassing handoff quality.
    Example: Call ``result = main(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_explainability.py`` and source-manifest schema.
    """

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
