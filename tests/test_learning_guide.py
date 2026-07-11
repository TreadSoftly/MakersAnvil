"""Purpose: Prove every implementation and contract line has current teaching text.

Used by: Developers and CI after any code, config, schema, state, or automation edit.
Inputs: The guide generator, source manifest, generated guide, and coverage record.
Outputs: Assertions for deterministic bytes, hashes, line counts, and file coverage.
Side effects: Builds expected artifacts in memory and never rewrites committed files.
Safety: Prevents stale explanations from passing after functional source changes.
Failure behavior: A changed, missing, skipped, or partially explained line fails CI.
Related proof: ``scripts/build_learning_guide.py`` and learning-coverage schema.
"""

import json

from scripts import build_learning_guide


def test_generated_learning_artifacts_match_current_source() -> None:
    """Purpose: Compare committed guide bytes with a fresh in-memory generation.

    Inputs: Current tracked/pending instructional source and committed artifacts.
    Outputs: No value; assertions prove exact deterministic equality.
    How it works: Calls the generator without its writing command-line boundary.
    Side effects: Reads source files only.
    Failure behavior: Any source/doc drift fails one of the equality assertions.
    Safety: No application modules are imported or executed by the generator.
    Example: Editing one JSON key without regeneration makes this test fail.
    Related proof: The explainability checker performs the same gate in CI.
    """

    guide_text, coverage_text, _ = build_learning_guide.build_outputs()

    assert build_learning_guide.GUIDE_PATH.read_text(encoding="utf-8") == guide_text
    assert build_learning_guide.COVERAGE_PATH.read_text(encoding="utf-8") == coverage_text


def test_coverage_counts_every_selected_physical_line() -> None:
    """Purpose: Prove selected files and all physical lines receive explanations.

    Inputs: Parsed committed learning coverage and current selected source paths.
    Outputs: No value; assertions prove complete, unique coverage.
    How it works: Compares path sets and sums per-file line/explanation counts.
    Side effects: Reads one JSON file and path metadata only.
    Failure behavior: Missing files, duplicate paths, or count differences fail.
    Safety: Zero-line files are allowed but cannot create false positive line counts.
    Example: A 20-line source requires ``explainedLineCount`` equal to 20.
    Related proof: ``schemas/learning-coverage.schema.json`` constrains each record.
    """

    coverage = json.loads(build_learning_guide.COVERAGE_PATH.read_text(encoding="utf-8"))
    paths = [entry["path"] for entry in coverage["files"]]

    assert paths == build_learning_guide.learning_source_paths()
    assert len(paths) == len(set(paths)) == coverage["sourceCount"]
    assert all(entry["lineCount"] == entry["explainedLineCount"] for entry in coverage["files"])
    assert sum(entry["lineCount"] for entry in coverage["files"]) == coverage["totalLineCount"]
    assert coverage["totalLineCount"] == coverage["explainedLineCount"]


def test_line_explanations_include_context_and_examples() -> None:
    """Purpose: Prove generated teaching text is more than a source-code echo.

    Inputs: Representative Python, JSON, CSS, and blank source lines.
    Outputs: No value; assertions require context-specific explanatory language.
    How it works: Calls the line explainer directly with controlled examples.
    Side effects: None.
    Failure behavior: Generic regressions that drop context or purpose fail.
    Safety: Representative strings are never executed.
    Example: A Python ``if`` line must explain conditional branching.
    Related proof: Full artifact equality exercises the rule on actual source.
    """

    context = [build_learning_guide.SourceContext("function example", 1, 10)]

    assert "Branches" in build_learning_guide.explain_line("example.py", "    if ready:", 2, context)
    assert "JSON field" in build_learning_guide.explain_line("example.json", '  "ready": false,', 1, [])
    assert "CSS property" in build_learning_guide.explain_line("example.css", "  display: grid;", 1, [])
    assert "performs no runtime action" in build_learning_guide.explain_line("example.py", "", 3, context)
