"""Purpose: Generate exact local teaching coverage for the previous app's own source.

Used by: Merger passes that study the ignored previous Makers Anvil application.
Inputs: First-party previous-app source only; dependencies and generated data excluded.
Outputs: A Markdown line guide and JSON coverage record inside the reference tree.
Side effects: Default mode replaces only those two ignored reference artifacts.
Safety: Never edits old source, dependencies, logs, outputs, archives, or user files.
Failure behavior: Missing baseline, invalid UTF-8/Python, or stale check output fails.
Related proof: ``tests/test_previous_app_learning_guide.py`` and merger audit.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Sequence

try:
    from scripts.build_learning_guide import explain_line, python_contexts
except (ImportError, ModuleNotFoundError):
    from build_learning_guide import explain_line, python_contexts


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE_ROOT = ROOT / "Previous Working MA For References" / "MAKERS ANVIL"
GUIDE_RELATIVE = Path("Application") / "REFERENCE_SOURCE_LINE_BY_LINE_GUIDE.md"
COVERAGE_RELATIVE = Path("Application") / "REFERENCE_SOURCE_LEARNING_COVERAGE.json"
SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".css", ".html", ".json", ".ps1", ".cmd"}


class PreviousAppGuideError(RuntimeError):
    """Purpose: Identify an invalid previous-app root or source universe.

    Inputs: Precise diagnostic produced by selection or rendering.
    Outputs: Typed failure for CLI and tests.
    How it works: Uses standard ``RuntimeError`` storage and propagation.
    Side effects: None until raised.
    Failure behavior: Keeps the guide from silently covering the wrong folder.
    Safety: Prevents broad recursion through dependencies or unrelated user files.
    Example: A root without ``Application/control_panel`` raises immediately.
    Related proof: ``tests/test_previous_app_learning_guide.py``.
    """


def validate_reference_root(reference_root: Path) -> Path:
    """Purpose: Confirm one root has the expected previous-app product shape.

    Inputs: Caller-provided or default reference root.
    Outputs: Resolved root containing the known control-panel source boundary.
    How it works: Resolves the path and checks two first-party source folders.
    Side effects: Reads filesystem metadata only.
    Failure behavior: Raises ``PreviousAppGuideError`` for missing markers.
    Safety: Selection cannot broaden to the workspace or home directory by accident.
    Example: The ignored ``Previous Working.../MAKERS ANVIL`` root passes.
    Related proof: Temporary valid/invalid roots are tested independently.
    """

    resolved = reference_root.resolve()
    required = [
        resolved / "Application" / "control_panel" / "backend" / "makers_anvil_panel",
        resolved / "Application" / "control_panel" / "frontend" / "src",
    ]
    if not all(path.is_dir() for path in required):
        raise PreviousAppGuideError(f"Previous app source markers are missing under: {resolved}")
    return resolved


def source_paths(reference_root: Path) -> list[Path]:
    """Purpose: Select only maintainable first-party previous-app source files.

    Inputs: Validated previous-app root.
    Outputs: Sorted resolved paths excluding dependencies, generated files, and logs.
    How it works: Applies narrow product globs and an explicit launcher allowlist.
    Side effects: Reads directory metadata only.
    Failure behavior: Empty selection raises instead of claiming coverage.
    Safety: Never traverses ``.venv``, ``node_modules``, ``dist``, logs, or projects.
    Example: Selects backend Python, React/TypeScript/CSS, tests, and launchers.
    Related proof: Coverage tests assert generated/dependency paths are absent.
    """

    root = validate_reference_root(reference_root)
    control = root / "Application" / "control_panel"
    selected: set[Path] = set()
    for folder in (
        control / "backend" / "makers_anvil_panel",
        control / "tests",
        control / "frontend" / "src",
        control / "frontend" / "e2e",
    ):
        for path in folder.rglob("*"):
            if path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES and "__pycache__" not in path.parts:
                selected.add(path.resolve())
    explicit = [
        control / "frontend" / "index.html",
        control / "frontend" / "package.json",
        control / "frontend" / "tsconfig.json",
        control / "frontend" / "vite.config.ts",
        control / "frontend" / "playwright.config.ts",
        root / "Application" / "Run-MakersAnvilApp.ps1",
        root / "Application" / "Run-MakersAnvilControlPanel.ps1",
        root / "00_MAKERS_ANVIL_APP.cmd",
        root / "00_RUN_MAKERS_ANVIL_PANEL.cmd",
    ]
    selected.update(path.resolve() for path in explicit if path.is_file())
    if not selected:
        raise PreviousAppGuideError("No first-party previous-app source files were selected.")
    return sorted(selected, key=lambda path: path.relative_to(root).as_posix().lower())


def file_purpose(relative: str) -> str:
    """Purpose: Describe one selected previous-app file without executing it.

    Inputs: Reference-root-relative POSIX path.
    Outputs: Concise ownership statement for the guide section header.
    How it works: Maps known source areas and suffixes to conservative roles.
    Side effects: None.
    Failure behavior: Unknown selected paths receive an honest generic description.
    Safety: Does not infer that old behavior is approved for migration.
    Example: ``frontend/src/App.tsx`` is labeled as the legacy React workbench.
    Related proof: Merger audit decides separately what can enter product source.
    """

    if relative.endswith("frontend/src/App.tsx"):
        return "Previous React workbench composition and interaction monolith; evidence only until split and migrated."
    if "/frontend/src/" in f"/{relative}":
        return "Previous frontend source used as visual, interaction, type, or test evidence."
    if "/backend/makers_anvil_panel/" in f"/{relative}":
        return "Previous Python control-panel behavior requiring safety and portability review before migration."
    if "/tests/" in f"/{relative}" or "/e2e/" in f"/{relative}":
        return "Executable previous-app behavior example used to identify proven migration candidates."
    if relative.endswith((".ps1", ".cmd")):
        return "Previous launcher evidence; fixed workspace and process assumptions are not product contracts."
    return "First-party previous-app configuration or interface source retained for merger study."


def build_outputs(reference_root: Path) -> tuple[str, str, dict[str, Any]]:
    """Purpose: Render deterministic previous-source guide and coverage text.

    Inputs: Valid previous-app root and its narrowly selected first-party sources.
    Outputs: Markdown, JSON text, and parsed coverage record.
    How it works: Hashes and explains every physical line using shared rules.
    Side effects: Reads selected source only; the caller chooses whether to write.
    Failure behavior: Decode or Python parse errors stop generation with the file.
    Safety: Old source is never imported, executed, formatted, or modified.
    Example: A 100-line selected file contributes exactly 100 guide rows.
    Related proof: ``--check`` and unit tests require deterministic byte equality.
    """

    root = validate_reference_root(reference_root)
    paths = source_paths(root)
    guide = [
        "# Previous Makers Anvil First-Party Source Line Guide",
        "",
        "This local, generated guide explains every physical line in the previous app's first-party implementation and tests. It deliberately excludes `.venv`, `node_modules`, `dist`, caches, logs, ingress data, project outputs, and third-party/generated content. The previous app remains evidence: only separately reviewed code may migrate into the real product.",
        "",
    ]
    entries: list[dict[str, Any]] = []
    total = 0
    for index, path in enumerate(paths, start=1):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        contexts = python_contexts(text, relative) if path.suffix.lower() == ".py" else []
        anchor = f"previous-source-{index:03d}"
        guide.extend(
            [
                f'<a id="{anchor}"></a>',
                f"## `{relative}`",
                "",
                f"**Purpose:** {file_purpose(relative)}",
                "",
                f"**SHA-256:** `{hashlib.sha256(text.encode('utf-8')).hexdigest()}`",
                "",
                "| Line | Source | Explanation |",
                "| ---: | --- | --- |",
            ]
        )
        for number, line in enumerate(lines, start=1):
            source = "<em>blank</em>" if not line else f"<code>{html.escape(line)}</code>"
            explanation = html.escape(explain_line(relative, line, number, contexts))
            guide.append(f"| {number} | {source} | {explanation} |")
        guide.append("")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        entries.append(
            {
                "path": relative,
                "sha256": digest,
                "lineCount": len(lines),
                "explainedLineCount": len(lines),
                "guideAnchor": anchor,
            }
        )
        total += len(lines)
    coverage = {
        "schemaVersion": "makers-anvil.previous-source-learning-coverage.v1",
        "claimState": "proven",
        "scope": "first-party-previous-app-source-only",
        "sourceCount": len(entries),
        "totalLineCount": total,
        "explainedLineCount": total,
        "excluded": [".venv", "node_modules", "dist", "caches", "logs", "ingress", "Projects", "generated outputs"],
        "files": entries,
    }
    guide_text = "\n".join(guide).rstrip() + "\n"
    coverage_text = json.dumps(coverage, indent=2, ensure_ascii=True, sort_keys=True) + "\n"
    return guide_text, coverage_text, coverage


def write_or_check(reference_root: Path, check: bool) -> dict[str, Any]:
    """Purpose: Write local reference guide artifacts or verify exact freshness.

    Inputs: Reference root and true for read-only check mode.
    Outputs: Machine-readable result with counts and mismatch messages.
    How it works: Compares deterministic expected bytes or replaces two outputs.
    Side effects: Write mode changes only the two documented ignored artifacts.
    Failure behavior: Missing/stale check artifacts return a failed result.
    Safety: Source files and excluded trees are never written.
    Example: Merger passes run write once, then ``--check`` after auditing.
    Related proof: Unit tests exercise both write and stale-check behavior.
    """

    root = validate_reference_root(reference_root)
    guide_text, coverage_text, coverage = build_outputs(root)
    outputs = [(root / GUIDE_RELATIVE, guide_text), (root / COVERAGE_RELATIVE, coverage_text)]
    messages: list[str] = []
    if check:
        for path, expected in outputs:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                messages.append(f"stale or missing generated reference guide artifact: {path.relative_to(root).as_posix()}")
    else:
        for path, expected in outputs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    return {
        "schemaVersion": "makers-anvil.previous-source-learning-build.v1",
        "claimState": "proven" if not messages else "failed",
        "passed": not messages,
        "mode": "check" if check else "write",
        "sourceCount": coverage["sourceCount"],
        "explainedLineCount": coverage["explainedLineCount"],
        "messages": messages,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Purpose: Parse reference-guide root/check options and report exact result.

    Inputs: Optional ``--check`` and ``--reference-root`` CLI arguments.
    Outputs: JSON result and zero only when generation/check succeeds.
    How it works: Resolves one root, delegates, and serializes the result.
    Side effects: Delegated write mode changes only two ignored guide artifacts.
    Failure behavior: Invalid roots or source errors produce failed JSON/nonzero.
    Safety: No deletion, dependency traversal, source edit, or code execution occurs.
    Example: ``python scripts/build_previous_app_learning_guide.py --check``.
    Related proof: ``tests/test_previous_app_learning_guide.py``.
    """

    parser = argparse.ArgumentParser(description="Build previous Makers Anvil first-party source teaching coverage.")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--reference-root", type=Path, default=DEFAULT_REFERENCE_ROOT)
    args = parser.parse_args(argv)
    try:
        result = write_or_check(args.reference_root, args.check)
    except (OSError, UnicodeError, SyntaxError, PreviousAppGuideError, ValueError) as exc:
        result = {
            "schemaVersion": "makers-anvil.previous-source-learning-build.v1",
            "claimState": "failed",
            "passed": False,
            "mode": "check" if args.check else "write",
            "messages": [str(exc)],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
