"""Purpose: Prove source and frozen desktop resources resolve without machine paths.

Used by: Developers and CI when resource or packaging layout changes.
Inputs: Isolated bundle trees and monkeypatched PyInstaller runtime markers.
Outputs: Assertions for valid source, frozen, and fail-closed resource lookup.
Side effects: Creates pytest-owned temporary files only.
Safety: No real bundle, user directory, or reference app is modified.
Failure behavior: Path coupling or incomplete resources fail the named test.
Related proof: ``runtime_resources.py`` and Windows package smoke checks.
"""

from pathlib import Path

import pytest

from makers_anvil_backend import runtime_resources


def make_bundle(root: Path) -> Path:
    """Purpose: Create the smallest valid frontend resource tree for one test.

    Inputs: Pytest-owned temporary root.
    Outputs: The created ``frontend/dist`` directory.
    How it works: Makes directories and writes one harmless HTML fixture.
    Side effects: Writes only below the supplied temporary root.
    Failure behavior: Filesystem errors propagate to pytest.
    Safety: The function cannot reach source or user-data paths.
    Example: ``make_bundle(tmp_path)`` returns a valid bundle static root.
    Related proof: Resource tests below consume this fixture helper.
    """

    dist = root / "frontend" / "dist"
    dist.mkdir(parents=True)
    (dist / "index.html").write_text("<!doctype html><title>test</title>", encoding="utf-8")
    return dist


def test_source_application_root_is_repository_relative() -> None:
    """Purpose: Source mode derives the repository from the installed module.

    Inputs: Real checked-out module location with no frozen marker.
    Outputs: Assertion that the expected frontend exists under the derived root.
    How it works: Calls both public resource functions in normal source mode.
    Side effects: Reads path metadata only.
    Failure behavior: A fixed path or wrong parent depth fails immediately.
    Safety: Does not depend on current working directory or a username.
    Example: The test passes after cloning the checkout to a different directory.
    Related proof: ``tests/test_project_purity.py`` also scans personal paths.
    """

    root = runtime_resources.application_root()

    assert (root / "frontend" / "dist" / "index.html").is_file()
    assert runtime_resources.frontend_root() == root / "frontend" / "dist"


def test_frozen_application_root_uses_pyinstaller_marker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Purpose: Frozen mode reads bundled assets from PyInstaller's extraction root.

    Inputs: Temporary bundle plus monkeypatched ``sys._MEIPASS`` marker.
    Outputs: Assertions that both root and frontend resolve to the fixture.
    How it works: Simulates the documented one-file runtime directory.
    Side effects: Creates one temporary resource tree.
    Failure behavior: Ignoring the frozen marker exposes the source path and fails.
    Safety: No process, package, or real frozen bundle is changed.
    Example: Mirrors how ``MakersAnvil.exe`` finds its compressed frontend.
    Related proof: PyInstaller data-file docs and package smoke CI.
    """

    public = make_bundle(tmp_path)
    monkeypatch.setattr(runtime_resources.sys, "_MEIPASS", str(tmp_path), raising=False)

    assert runtime_resources.application_root() == tmp_path.resolve()
    assert runtime_resources.frontend_root() == public.resolve()


def test_incomplete_resource_tree_fails_closed(tmp_path: Path) -> None:
    """Purpose: Missing frontend files cannot fall back to an unintended directory.

    Inputs: Empty pytest-owned temporary root.
    Outputs: Expected ``ResourceResolutionError`` naming the candidate path.
    How it works: Requests frontend resolution before creating any index file.
    Side effects: Reads temporary path metadata only.
    Failure behavior: Returning an invalid path would fail this assertion.
    Safety: Prevents a packaged HTTP server from exposing arbitrary nearby files.
    Example: A packaging omission produces a startup error instead of a blank app.
    Related proof: ``scripts/build_windows_exe.py`` validates the same inputs.
    """

    with pytest.raises(runtime_resources.ResourceResolutionError, match="resources are incomplete"):
        runtime_resources.frontend_root(tmp_path)
