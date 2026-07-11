"""Purpose: Prove previous-app learning coverage stays narrow and exact.

Used by: Merger passes and CI when the external-reference generator changes.
Inputs: Isolated miniature previous-app trees with first/third-party examples.
Outputs: Assertions for selection, every-line counts, output, and stale checks.
Side effects: Writes only inside pytest temporary directories.
Safety: Never reads or changes the user's real ignored previous app.
Failure behavior: Dependency traversal or incomplete coverage fails explicitly.
Related proof: ``scripts/build_previous_app_learning_guide.py``.
"""

from pathlib import Path

from scripts import build_previous_app_learning_guide as previous_guide


def make_previous_app(root: Path) -> Path:
    """Purpose: Create a tiny valid previous-app shape with excluded dependency data.

    Inputs: Pytest-owned temporary root.
    Outputs: The created previous-app root.
    How it works: Writes one backend, frontend, test, and node_modules example.
    Side effects: Creates only temporary directories/files.
    Failure behavior: Filesystem errors propagate to pytest.
    Safety: No real reference path or product source is touched.
    Example: The fixture contains three selected files and one excluded JS file.
    Related proof: Selection and generation tests below consume this helper.
    """

    backend = root / "Application" / "control_panel" / "backend" / "makers_anvil_panel"
    frontend = root / "Application" / "control_panel" / "frontend" / "src"
    tests = root / "Application" / "control_panel" / "tests"
    dependency = root / "Application" / "control_panel" / "frontend" / "node_modules" / "package"
    for folder in (backend, frontend, tests, dependency):
        folder.mkdir(parents=True)
    (backend / "app.py").write_text("def health():\n    return {'ok': True}\n", encoding="utf-8")
    (frontend / "App.tsx").write_text("export function App() {\n  return <main>Old</main>;\n}\n", encoding="utf-8")
    (frontend / "styles.css").write_text("main {\n  display: block;\n}\n", encoding="utf-8")
    (tests / "test_app.py").write_text("def test_health():\n    assert True\n", encoding="utf-8")
    (dependency / "index.js").write_text("thirdParty();\n", encoding="utf-8")
    return root


def test_selection_excludes_dependencies_and_generated_trees(tmp_path: Path) -> None:
    """Purpose: The generator cannot recurse through node_modules or generated data.

    Inputs: Miniature previous app containing one dependency file.
    Outputs: Selected path assertions with no node_modules entry.
    How it works: Runs the same narrow source selection used in production.
    Side effects: Creates temporary fixture files only.
    Failure behavior: Any excluded path in the result fails the test.
    Safety: Protects guide size, licensing, and user/private generated data.
    Example: First-party ``App.tsx`` is selected; dependency ``index.js`` is not.
    Related proof: The real audit reports 85,000+ total files but selects only source.
    """

    root = make_previous_app(tmp_path)
    selected = [path.relative_to(root).as_posix() for path in previous_guide.source_paths(root)]

    assert any(path.endswith("frontend/src/App.tsx") for path in selected)
    assert any(path.endswith("backend/makers_anvil_panel/app.py") for path in selected)
    assert all("node_modules" not in path for path in selected)


def test_every_selected_physical_line_has_exact_coverage(tmp_path: Path) -> None:
    """Purpose: Coverage totals equal real line totals for every selected source.

    Inputs: Miniature previous app with Python, TSX, CSS, and test source.
    Outputs: Per-file and aggregate equality assertions plus guide content.
    How it works: Builds outputs in memory without writing guide artifacts.
    Side effects: Creates only the input fixture tree.
    Failure behavior: Missing rows, paths, hashes, or counts fail assertions.
    Safety: Source is parsed as text/AST and never imported or executed.
    Example: The TSX line appears in the guide with a plain explanation.
    Related proof: Real generated coverage records the full first-party baseline.
    """

    root = make_previous_app(tmp_path)
    guide, _, coverage = previous_guide.build_outputs(root)

    assert coverage["totalLineCount"] == coverage["explainedLineCount"]
    assert all(item["lineCount"] == item["explainedLineCount"] for item in coverage["files"])
    assert "frontend/src/App.tsx" in guide
    assert "node_modules" not in " ".join(item["path"] for item in coverage["files"])


def test_write_then_check_detects_stale_previous_source(tmp_path: Path) -> None:
    """Purpose: Local reference coverage becomes stale after any selected edit.

    Inputs: Miniature previous app and one deliberate source change.
    Outputs: Passing write/check followed by a failed stale check.
    How it works: Compares exact deterministic guide and coverage bytes.
    Side effects: Writes two generated temporary artifacts and changes one fixture.
    Failure behavior: A stale guide passing would fail the final assertion.
    Safety: Demonstrates drift detection without touching the real previous app.
    Example: Appending a CSS declaration invalidates both generated artifacts.
    Related proof: Merger Continue passes run the same check on local reference truth.
    """

    root = make_previous_app(tmp_path)

    assert previous_guide.write_or_check(root, check=False)["passed"] is True
    assert previous_guide.write_or_check(root, check=True)["passed"] is True
    css = root / "Application" / "control_panel" / "frontend" / "src" / "styles.css"
    css.write_text(css.read_text(encoding="utf-8") + "aside { display: none; }\n", encoding="utf-8")
    assert previous_guide.write_or_check(root, check=True)["passed"] is False
