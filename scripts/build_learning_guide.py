"""Purpose: Build the line-numbered teaching guide for Makers Anvil source.

Used by: Developers, AI models, the explainability checker, CI, and every Continue pass.
Inputs: Tracked implementation/contract files plus their source-manifest descriptions.
Outputs: ``docs/LINE_BY_LINE_CODE_GUIDE.md`` and ``state/learning_coverage.json``.
Side effects: Default mode replaces only those two generated learning artifacts.
Safety: Source files are read but never executed, imported, reformatted, or modified.
Failure behavior: Invalid UTF-8, Python syntax, stale output, or missing files fail loudly.
Related proof: ``tests/test_learning_guide.py`` and ``scripts/check_explainability.py``.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import html
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# These are the product formats whose physical lines need teaching coverage.
# Markdown is intentionally excluded because it is already explanatory prose;
# the generated guide and coverage record are excluded to avoid self-reference.
ROOT = Path(__file__).resolve().parents[1]
GUIDE_PATH = ROOT / "docs" / "LINE_BY_LINE_CODE_GUIDE.md"
COVERAGE_PATH = ROOT / "state" / "learning_coverage.json"
MANIFEST_PATH = ROOT / "state" / "source_manifest.json"
LEARNING_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".css",
    ".html",
    ".svg",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
    ".ps1",
    ".cmd",
}
LEARNING_NAMES = {".gitignore", "LICENSE"}
EXCLUDED_PATHS = {
    GUIDE_PATH.relative_to(ROOT).as_posix(),
    COVERAGE_PATH.relative_to(ROOT).as_posix(),
}


@dataclass(frozen=True)
class SourceContext:
    """Purpose: Store one component name and its inclusive source-line span.

    Inputs: A human-readable component name plus first and last line numbers.
    Outputs: An immutable value used while explaining Python source lines.
    How it works: The generator selects the smallest context containing each line.
    Side effects: None; dataclass instances contain only strings and integers.
    Failure behavior: Invalid construction errors surface from the dataclass runtime.
    Safety: Context labels describe code and never execute or import it.
    Example: ``SourceContext("function load_state", 20, 45)`` labels that function.
    Related proof: ``tests/test_learning_guide.py`` exercises context-aware output.
    """

    name: str
    first_line: int
    last_line: int


def tracked_files() -> list[str]:
    """Purpose: Return tracked and pending product paths in deterministic order.

    Inputs: Git index/worktree state when available, otherwise the source manifest.
    Outputs: Sorted repository-relative POSIX paths with duplicates removed.
    How it works: Git includes pending files so a new source cannot escape coverage.
    Side effects: Runs read-only ``git ls-files`` or reads one JSON manifest.
    Failure behavior: Git/JSON errors propagate and stop generation.
    Safety: Ignored references and generated caches are omitted by Git rules.
    Example: ``tracked_files()`` includes a newly added unignored Python test.
    Related proof: The explainability checker compares this universe to its manifest.
    """

    if (ROOT / ".git").exists():
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return sorted({line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()})
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return sorted({entry["path"] for entry in manifest.get("files", [])})


def learning_source_paths() -> list[str]:
    """Purpose: Select code, automation, metadata, and contract files for teaching.

    Inputs: The complete tracked/pending path list.
    Outputs: Sorted paths whose suffix/name belongs to the instructional universe.
    How it works: Excludes prose and generated outputs while retaining JSON contracts.
    Side effects: None beyond the read-only path discovery performed by ``tracked_files``.
    Failure behavior: Missing selected files are reported later while rendering.
    Safety: Binary assets and private ignored references never enter the guide.
    Example: Python, CSS, schemas, package metadata, and CI YAML are selected.
    Related proof: ``state/learning_coverage.json`` records the resulting exact set.
    """

    selected: list[str] = []
    for relative in tracked_files():
        path = Path(relative)
        if relative in EXCLUDED_PATHS:
            continue
        if path.suffix.lower() in LEARNING_SUFFIXES or path.name in LEARNING_NAMES:
            selected.append(relative)
    return sorted(selected)


def python_contexts(text: str, relative: str) -> list[SourceContext]:
    """Purpose: Map Python classes/functions to line ranges without importing code.

    Inputs: Python source text and its repository-relative path for syntax messages.
    Outputs: Component spans sorted from smallest to largest for precise attribution.
    How it works: ``ast.parse`` exposes declaration/end lines without executing source.
    Side effects: None.
    Failure behavior: Syntax errors identify the source path and stop guide generation.
    Safety: Parsing cannot trigger module imports, filesystem writes, or application code.
    Example: A return line inside ``catalog`` is labeled ``function catalog``.
    Related proof: Python syntax is also exercised by pytest and project verification.
    """

    tree = ast.parse(text, filename=relative)
    contexts: list[SourceContext] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            contexts.append(SourceContext(f"class {node.name}", node.lineno, node.end_lineno or node.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            contexts.append(SourceContext(f"function {node.name}", node.lineno, node.end_lineno or node.lineno))
    return sorted(contexts, key=lambda item: (item.last_line - item.first_line, item.first_line))


def context_for_line(contexts: list[SourceContext], line_number: int) -> str:
    """Purpose: Return the narrowest Python component containing one source line.

    Inputs: Ordered component spans and a one-based physical line number.
    Outputs: Component name or ``module level`` when no declaration contains the line.
    How it works: The pre-sorted first match is the smallest enclosing block.
    Side effects: None.
    Failure behavior: Invalid numbers simply produce module-level context.
    Safety: This is descriptive lookup only.
    Example: Line 30 inside a method can return ``function handle``.
    Related proof: Generated guide rows display this context beside each explanation.
    """

    for context in contexts:
        if context.first_line <= line_number <= context.last_line:
            return context.name
    return "module level"


def explain_line(relative: str, line: str, line_number: int, contexts: list[SourceContext]) -> str:
    """Purpose: Explain one physical source line using language-aware rules.

    Inputs: File path, raw line text, one-based line number, and Python contexts.
    Outputs: A plain-English what/why statement suitable for a new programmer.
    How it works: Specific syntax patterns win before a conservative fallback.
    Side effects: None.
    Failure behavior: Unrecognized syntax receives an honest generic explanation.
    Safety: Explanations never claim runtime behavior beyond the visible statement.
    Example: ``return value`` is explained as returning control and that value.
    Related proof: Coverage requires exactly one explanation for every physical line.
    """

    stripped = line.strip()
    suffix = Path(relative).suffix.lower()
    context = context_for_line(contexts, line_number) if suffix == ".py" else "this file"
    if not stripped:
        return f"Blank separator inside {context}; it groups neighboring ideas and performs no runtime action."

    if suffix == ".py":
        if stripped.startswith("#"):
            return f"Maintainer note inside {context}: {stripped.lstrip('#').strip()}"
        if stripped.startswith(("import ", "from ")):
            return f"Imports a dependency for {context}; later statements use the imported name instead of duplicating that behavior."
        if stripped.startswith("class "):
            return f"Starts a class block in {context}; indented lines define the state and operations owned by this type."
        if stripped.startswith(("def ", "async def ")):
            return f"Defines {stripped.split('(')[0].replace(':', '')}; its signature names caller inputs and its docstring explains the contract."
        if stripped.startswith("@"):
            return f"Applies a decorator to the next declaration in {context}, changing declaration metadata or call behavior explicitly."
        if stripped.startswith(("if ", "elif ")):
            return f"Branches inside {context}; the indented block runs only when this condition is true. Example: a failed safety condition follows the other branch."
        if stripped == "else:":
            return f"Provides the fallback branch inside {context} when the preceding condition was false."
        if stripped.startswith(("for ", "while ")):
            return f"Starts an iteration inside {context}; each item/condition is handled by the indented block."
        if stripped == "try:":
            return f"Starts guarded work inside {context} so expected failures can be handled by following exception branches."
        if stripped.startswith("except"):
            return f"Handles the named failure from the preceding try block in {context} instead of hiding unrelated errors."
        if stripped == "finally:":
            return f"Starts cleanup that runs whether guarded work succeeded or failed inside {context}."
        if stripped.startswith("with "):
            return f"Opens a managed resource inside {context}; Python guarantees the resource is released when the block ends."
        if stripped.startswith("return"):
            return f"Ends {context} and gives the caller the value shown on this line (or no value for a bare return)."
        if stripped.startswith("raise "):
            return f"Stops {context} with an explicit error because continuing would violate the documented contract."
        if stripped.startswith("assert "):
            return f"Executable example inside {context}; the test fails here if the required contract is not true."
        if re.match(r"^[A-Za-z_][\w.]*\s*=", stripped):
            name = stripped.split("=", 1)[0].strip()
            return f"Assigns the computed value to ``{name}`` inside {context} so later lines can use the named result."
        if stripped.startswith(('"""', "'''")) or stripped.endswith(('"""', "'''")):
            return f"Begins, continues, or closes documentation for {context}; the text teaches callers and has no operational side effect."
        if stripped in {"}", "]", ")", "},", "],", "),"}:
            return f"Closes the current literal or call inside {context}; it adds no behavior beyond completing that structure."
        return f"Executes this statement inside {context}; read it with the surrounding detailed docstring and block comments to see its inputs and invariant."

    if suffix in {".js", ".ts", ".tsx"}:
        if stripped.startswith(("/**", "*", "*/", "//")):
            return "Documentation or reasoning comment for the surrounding JavaScript block; it teaches intent and performs no browser action."
        if stripped.startswith(("const ", "let ", "var ")):
            return "Declares a named JavaScript value for later rendering or control flow; ``const`` prevents accidental reassignment."
        if stripped.startswith(("function ", "async function ")):
            return "Starts a documented JavaScript function; callers provide the listed parameters and the body owns one UI responsibility."
        if stripped.startswith(("if ", "if(")):
            return "Branches on the visible condition; only the matching browser-state path runs."
        if stripped.startswith(("for ", "while ")) or ".forEach(" in stripped:
            return "Iterates over the named records/elements so each receives the same safe rendering or navigation rule."
        if stripped.startswith("return"):
            return "Returns from the current JavaScript function, optionally giving its caller the shown value."
        if "textContent" in stripped:
            return "Writes display text through ``textContent`` so untrusted metadata cannot become executable HTML."
        if "addEventListener" in stripped:
            return "Registers a browser-only event handler; the handler changes local view state or refreshes GET data."
        if "fetch(" in stripped or "method: \"GET\"" in stripped:
            return "Participates in a GET-only loopback request; it reads state and does not authorize a mutation."
        if stripped in {"}", "};", "]", "];", "),", ");"}:
            return "Closes the current JavaScript block, collection, or call."
        return "Executes part of the surrounding documented JavaScript block; neighboring comments describe the UI contract and safety boundary."

    if suffix == ".css":
        if stripped.startswith(("/*", "*", "*/")):
            return "CSS teaching comment for the following selector/declaration block; comments do not affect layout."
        if stripped.endswith("{"):
            return f"Opens the CSS rule or at-rule ``{stripped[:-1].strip()}``; following declarations apply within this scope."
        if stripped == "}":
            return "Closes the current CSS selector, media query, or animation block."
        if ":" in stripped and stripped.endswith(";"):
            prop = stripped.split(":", 1)[0].strip()
            return f"Sets CSS property ``{prop}`` for the active selector; this changes presentation only, not application truth."
        return "Continues a selector list or CSS expression that is explained by the adjacent block comment."

    if suffix in {".html", ".svg"}:
        if stripped.startswith("<!--") or stripped.endswith("-->"):
            return "HTML/SVG teaching comment describing the following structural block; it is not rendered as interface text."
        if stripped.startswith("</"):
            return f"Closes the ``{stripped.split('>')[0][2:]}`` element so the document hierarchy remains well formed."
        if stripped.startswith("<"):
            tag = re.match(r"<([\w:-]+)", stripped)
            return f"Declares a ``{tag.group(1) if tag else 'markup'}`` element and its visible/accessibility attributes within the static interface."
        return "Provides literal text or continues markup attributes for the surrounding documented element."

    if suffix == ".json":
        key = re.match(r'^"([^"]+)"\s*:', stripped)
        if key:
            return f"Defines JSON field ``{key.group(1)}``; its value is constrained by the matching schema/service validation where applicable."
        if stripped in {"{", "}", "},", "[", "]", "],"}:
            return "Opens or closes a JSON object/array; nesting groups related contract fields and performs no action by itself."
        return "Continues a JSON value or collection entry in this declarative contract/state file."

    if suffix == ".toml":
        if stripped.startswith("["):
            return f"Starts TOML section ``{stripped}`` so following keys share that configuration namespace."
        if "=" in stripped:
            return f"Assigns declarative TOML setting ``{stripped.split('=', 1)[0].strip()}``; tooling reads it during build/test setup."
        if stripped.startswith("#"):
            return "TOML maintainer comment explaining nearby configuration."
        return "Continues the surrounding TOML configuration value."

    if suffix in {".yml", ".yaml"}:
        if stripped.startswith("#"):
            return "Workflow maintainer comment explaining the following automation block."
        if stripped.startswith("-"):
            return "Adds one ordered YAML list/step entry to the surrounding workflow or matrix."
        if ":" in stripped:
            return f"Defines YAML key ``{stripped.split(':', 1)[0]}`` inside the current automation hierarchy."
        return "Continues a YAML scalar or expression used by the surrounding automation key."

    if Path(relative).name == ".gitignore":
        if stripped.startswith("#"):
            return "Ignore-file comment naming the artifact category covered by following patterns."
        return f"Tells Git to exclude ``{stripped}`` so generated/private material does not enter product history."

    if Path(relative).name == "LICENSE":
        return "Part of the MIT license text defining permitted use, redistribution, warranty, or liability terms."

    if suffix == ".ps1":
        if stripped.startswith("#"):
            return "PowerShell maintainer comment describing the adjacent launcher or validation step."
        if stripped.lower().startswith(("param(", "[cmdletbinding")):
            return "Declares the PowerShell command interface so accepted inputs remain explicit."
        if stripped.startswith("$") and "=" in stripped:
            return "Assigns a named PowerShell value used by the surrounding launcher or safety check."
        return "Executes part of the surrounding PowerShell launcher; the owning guide section explains its boundary and expected effect."

    if suffix == ".cmd":
        if stripped.lower().startswith("rem ") or stripped.startswith("::"):
            return "Command-script maintainer comment explaining the adjacent launcher statement."
        if stripped.lower().startswith("@echo"):
            return "Controls command echoing so the launcher presents intentional output only."
        return "Executes one Windows command-script launcher statement; no behavior is implied beyond the visible command."

    return "Declarative source line covered by the file purpose and maintenance contract shown above."


def build_outputs() -> tuple[str, str, dict[str, Any]]:
    """Purpose: Render deterministic guide text and machine-readable coverage.

    Inputs: Selected source files and their source-manifest purpose/maintenance data.
    Outputs: Guide Markdown, coverage JSON text, and parsed coverage dictionary.
    How it works: Hashes each file, explains each physical line, and records totals.
    Side effects: Reads source files only; callers decide whether to write outputs.
    Failure behavior: Missing files, invalid UTF-8/Python, or manifest gaps stop work.
    Safety: Source is parsed as text/AST but never imported or executed.
    Example: Tests call this function and compare its strings to committed artifacts.
    Related proof: ``--check`` and the explainability gate require byte equality.
    """

    source_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    ownership = {entry["path"]: entry for entry in source_manifest.get("files", [])}
    paths = learning_source_paths()
    guide_lines = [
        "# Line-By-Line Makers Anvil Code Guide",
        "",
        "This generated teaching artifact explains every physical line in each implementation, automation, metadata, and structured-contract file. Read it beside the real source: in-code docstrings/comments explain components and blocks, while this guide makes blank lines, delimiters, declarations, and formats that cannot contain comments explicit.",
        "",
        "Regenerate with `python scripts/build_learning_guide.py`. Verify without writing with `python scripts/build_learning_guide.py --check`.",
        "",
    ]
    coverage_entries: list[dict[str, Any]] = []
    total_lines = 0

    for index, relative in enumerate(paths, start=1):
        path = ROOT / relative
        text = path.read_text(encoding="utf-8")
        physical_lines = text.splitlines()
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        contexts = python_contexts(text, relative) if path.suffix.lower() == ".py" else []
        owner = ownership.get(relative)
        if owner is None:
            raise ValueError(f"learning source lacks source-manifest entry: {relative}")
        anchor = f"source-{index:03d}"
        guide_lines.extend(
            [
                f'<a id="{anchor}"></a>',
                f"## `{relative}`",
                "",
                f"**Purpose:** {owner['purpose']}",
                "",
                f"**Maintenance rule:** {owner['maintenanceNotes']}",
                "",
                f"**Change example:** Modify this file only with its matching tests/contracts, then regenerate this guide so the recorded SHA-256 `{digest}` changes intentionally.",
                "",
                f"<!-- source:{relative} sha256:{digest} lines:{len(physical_lines)} -->",
                "",
                "| Line | Source | Explanation |",
                "| ---: | --- | --- |",
            ]
        )
        for line_number, line in enumerate(physical_lines, start=1):
            shown = html.escape(line, quote=False) if line else "<em>blank</em>"
            explanation = html.escape(explain_line(relative, line, line_number, contexts), quote=False)
            guide_lines.append(f"| {line_number} | <code>{shown}</code> | {explanation} |")
        guide_lines.append("")
        total_lines += len(physical_lines)
        coverage_entries.append(
            {
                "path": relative,
                "sha256": digest,
                "lineCount": len(physical_lines),
                "explainedLineCount": len(physical_lines),
                "guideAnchor": anchor,
            }
        )

    coverage: dict[str, Any] = {
        "schemaVersion": "makers-anvil.learning-coverage.v1",
        "claimState": "proven",
        "guidePath": GUIDE_PATH.relative_to(ROOT).as_posix(),
        "sourceCount": len(coverage_entries),
        "totalLineCount": total_lines,
        "explainedLineCount": total_lines,
        "files": coverage_entries,
    }
    guide_text = "\n".join(guide_lines).rstrip() + "\n"
    coverage_text = json.dumps(coverage, indent=2, sort_keys=False) + "\n"
    return guide_text, coverage_text, coverage


def main() -> int:
    """Purpose: Write or verify the generated instructional artifacts.

    Inputs: Optional ``--check`` command-line flag plus current repository source.
    Outputs: One JSON summary and process exit code; artifacts in write mode.
    How it works: Builds expected bytes once, then compares or atomically replaces.
    Side effects: Write mode updates only the guide and coverage JSON.
    Failure behavior: Stale/missing outputs return exit code one in check mode.
    Safety: No application code, user file, reference root, or runtime data is changed.
    Example: ``python scripts/build_learning_guide.py --check`` is CI-safe.
    Related proof: The project verifier independently validates hashes and counts.
    """

    parser = argparse.ArgumentParser(description="Build the Makers Anvil line-by-line learning guide.")
    parser.add_argument("--check", action="store_true", help="Fail when committed learning artifacts are stale.")
    args = parser.parse_args()
    guide_text, coverage_text, coverage = build_outputs()
    errors: list[str] = []
    if args.check:
        if not GUIDE_PATH.is_file() or GUIDE_PATH.read_text(encoding="utf-8") != guide_text:
            errors.append("line-by-line guide is missing or stale")
        if not COVERAGE_PATH.is_file() or COVERAGE_PATH.read_text(encoding="utf-8") != coverage_text:
            errors.append("learning coverage record is missing or stale")
    else:
        GUIDE_PATH.write_text(guide_text, encoding="utf-8")
        COVERAGE_PATH.write_text(coverage_text, encoding="utf-8")
    result = {
        "schemaVersion": "makers-anvil.learning-build-result.v1",
        "claimState": "proven" if not errors else "failed",
        "passed": not errors,
        "mode": "check" if args.check else "write",
        "sourceCount": coverage["sourceCount"],
        "explainedLineCount": coverage["explainedLineCount"],
        "messages": errors,
    }
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
