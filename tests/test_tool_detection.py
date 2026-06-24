"""Purpose: Explain and prove safe maker-tool presence detection.

Used by: Developers and CI when tool catalogs or platform providers change.
Inputs: Injected PATH/candidate checks, platform identity, and isolated policy.
Outputs: Assertions for family coverage, detection evidence, and redaction.
Side effects: No processes or writes; test probes are injected.
Safety: Install paths, versions, launch, install, update, and repair stay private.
Failure behavior: Missing tools/platforms remain not proven; bad policy is rejected.
Related proof: ``services/tool_detection.py`` and tool schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.tool_detection import ToolDetectionError, ToolDetectionService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_detector(
    root: Path,
    platform_name: str,
    environ: dict[str, str],
    path_lookup=None,
) -> ToolDetectionService:
    """Build an isolated detector using the committed catalog and injected machine state."""

    config_root = root / "config"
    config_root.mkdir(parents=True)
    config_root.joinpath("tool_catalog.json").write_text(
        PROJECT_ROOT.joinpath("config", "tool_catalog.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return ToolDetectionService(root, platform_name, environ, path_lookup=path_lookup)


def test_windows_standard_location_detects_blender_without_exposing_path(tmp_path: Path) -> None:
    """A standard-location match reports Blender but withholds its resolved path."""

    program_files = tmp_path / "private-program-files"
    executable = program_files / "Blender Foundation" / "Blender 4.5" / "blender.exe"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"not executed")
    detector = build_detector(
        tmp_path / "source",
        "win32",
        {"ProgramFiles": str(program_files), "PATH": ""},
        path_lookup=lambda command, path: None,
    )

    result = detector.detection_catalog()

    blender = next(tool for tool in result["tools"] if tool["id"] == "blender")
    assert blender["claimState"] == "detected"
    assert blender["detection"] == {
        "installed": True,
        "method": "standard-location",
        "candidateId": "blender-windows-program-files",
        "executableName": "blender.exe",
        "absolutePathExposed": False,
    }
    assert blender["version"] == {"claimState": "not proven", "value": None, "commandExecuted": False}
    assert str(program_files.resolve()) not in json.dumps(result)
    assert executable.read_bytes() == b"not executed"


def test_path_command_detection_redacts_lookup_result(tmp_path: Path) -> None:
    """A PATH lookup can prove presence without returning its private resolved location."""

    private_match = str(tmp_path / "private-bin" / "blender")
    detector = build_detector(
        tmp_path / "source",
        "linux",
        {"PATH": "injected-path"},
        path_lookup=lambda command, path: private_match if command == "blender" else None,
    )

    result = detector.detection_catalog()

    blender = next(tool for tool in result["tools"] if tool["id"] == "blender")
    assert blender["detection"]["method"] == "path-command"
    assert blender["detection"]["executableName"] == "blender"
    assert private_match not in json.dumps(result)
    assert result["safety"]["processExecuted"] is False


def test_unknown_platform_returns_no_invented_detections(tmp_path: Path) -> None:
    """An unsupported platform produces not-proven results instead of guesses."""

    detector = build_detector(
        tmp_path / "source",
        "plan9",
        {},
        path_lookup=lambda command, path: None,
    )

    result = detector.detection_catalog()

    assert result["claimState"] == "not proven"
    assert result["platform"] == {"id": "unknown", "claimState": "not proven"}
    assert result["summary"]["detectedCount"] == 0
    assert all(tool["claimState"] == "not proven" for tool in result["tools"])
    assert all(action["enabledInApi"] is False for action in result["actions"].values())


def test_tool_catalog_rejects_enabled_or_missing_safety(tmp_path: Path) -> None:
    """True or absent safety flags cannot bypass non-executing detection policy."""

    detector = build_detector(tmp_path / "source", "windows", {}, path_lookup=lambda command, path: None)
    catalog = json.loads(detector.catalog_path.read_text(encoding="utf-8"))
    catalog["safety"]["toolLaunched"] = True
    detector.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    with pytest.raises(ToolDetectionError, match="cannot execute"):
        detector.detection_catalog()

    catalog["safety"]["toolLaunched"] = False
    catalog["safety"].pop("registryRead")
    detector.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    with pytest.raises(ToolDetectionError, match="cannot execute"):
        detector.detection_catalog()


def test_tool_catalog_rejects_candidate_traversal(tmp_path: Path) -> None:
    """Candidate patterns cannot escape their narrowly scoped provider root."""

    detector = build_detector(tmp_path / "source", "windows", {}, path_lookup=lambda command, path: None)
    catalog = json.loads(detector.catalog_path.read_text(encoding="utf-8"))
    catalog["tools"][0]["candidates"][0]["pattern"] = "../outside/blender.exe"
    detector.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(ToolDetectionError, match="stay relative"):
        detector.detection_catalog()
