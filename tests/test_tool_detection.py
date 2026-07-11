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
    version_lookup=None,
) -> ToolDetectionService:
    """Purpose: Build an isolated detector using the committed catalog and injected machine state.

    Inputs: Caller-supplied root, platform, environment, path, and metadata adapters.
    Outputs: Returns ``ToolDetectionService``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Call ``result = instance.build_detector(...)`` with values satisfying the documented inputs.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

    config_root = root / "config"
    config_root.mkdir(parents=True)
    config_root.joinpath("tool_catalog.json").write_text(
        PROJECT_ROOT.joinpath("config", "tool_catalog.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return ToolDetectionService(
        root,
        platform_name,
        environ,
        path_lookup=path_lookup,
        version_lookup=version_lookup,
    )


def test_windows_standard_location_detects_blender_without_exposing_path(tmp_path: Path) -> None:
    """Purpose: A standard-location match reports Blender but withholds its resolved path.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Run ``python -m pytest tests/test_tool_detection.py -k test_windows_standard_location_detects_blender_without_exposing_path``.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

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
    assert blender["version"] == {
        "claimState": "not proven",
        "value": None,
        "fileVersion": None,
        "productVersion": None,
        "evidenceMethod": "none",
        "commandExecuted": False,
        "absolutePathExposed": False,
    }
    assert str(program_files.resolve()) not in json.dumps(result)
    assert executable.read_bytes() == b"not executed"


def test_path_command_detection_redacts_lookup_result(tmp_path: Path) -> None:
    """Purpose: A PATH lookup can prove presence without returning its private resolved location.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It checks conditions.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Run ``python -m pytest tests/test_tool_detection.py -k test_path_command_detection_redacts_lookup_result``.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

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


def test_windows_metadata_version_is_proven_without_path_or_command(tmp_path: Path) -> None:
    """Purpose: Prove injected PE metadata becomes a closed path-redacted version record.

    Inputs: Isolated PATH detection plus a deterministic metadata-reader adapter.
    Outputs: Assertions for version value, evidence method, and false command/path flags.
    How it works: The adapter records the private input while returning fixed metadata.
    Side effects: Creates no executable and starts no process; only in-memory calls occur.
    Failure behavior: A missing proof field or leaked private path fails the test.
    Safety: The public catalog cannot contain the adapter's resolved installation path.
    Example: Blender ``4.5.0.0`` is proven from VERSIONINFO, not ``--version``.
    Related proof: ``services/tool_detection.py`` and ``services/tool_version.py``.
    """

    private_match = tmp_path / "private-bin" / "blender.exe"
    observed: list[tuple[Path, str]] = []

    def version_lookup(path: Path, platform_name: str):
        """Purpose: Return deterministic version metadata while recording private inputs.

        Inputs: Private detected path and normalized platform id.
        Outputs: One valid Windows version-evidence mapping.
        How it works: Appends the call for assertion, then returns fixed metadata.
        Side effects: Mutates only the test-local ``observed`` list.
        Failure behavior: Unexpected arguments remain visible in the final assertion.
        Safety: Does not open, execute, write, or serialize the private target.
        Example: The detector calls this once for the Blender match.
        Related proof: The enclosing test.
        """

        observed.append((path, platform_name))
        return {
            "value": "4.5.0.0",
            "fileVersion": "4.5.0.0",
            "productVersion": "4.5.0.0",
            "evidenceMethod": "windows-version-resource",
        }

    detector = build_detector(
        tmp_path / "source",
        "win32",
        {"PATH": "injected-path"},
        path_lookup=lambda command, path: str(private_match) if command == "blender.exe" else None,
        version_lookup=version_lookup,
    )

    result = detector.detection_catalog()
    blender = next(tool for tool in result["tools"] if tool["id"] == "blender")

    assert observed[0] == (private_match, "windows")
    assert blender["version"] == {
        "claimState": "proven",
        "value": "4.5.0.0",
        "fileVersion": "4.5.0.0",
        "productVersion": "4.5.0.0",
        "evidenceMethod": "windows-version-resource",
        "commandExecuted": False,
        "absolutePathExposed": False,
    }
    assert str(private_match) not in json.dumps(result)


def test_unknown_platform_returns_no_invented_detections(tmp_path: Path) -> None:
    """Purpose: An unsupported platform produces not-proven results instead of guesses.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Run ``python -m pytest tests/test_tool_detection.py -k test_unknown_platform_returns_no_invented_detections``.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

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
    """Purpose: True or absent safety flags cannot bypass non-executing detection policy.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Run ``python -m pytest tests/test_tool_detection.py -k test_tool_catalog_rejects_enabled_or_missing_safety``.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

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
    """Purpose: Candidate patterns cannot escape their narrowly scoped provider root.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Install paths, versions, launch, install, update, and repair stay private.
    Example: Run ``python -m pytest tests/test_tool_detection.py -k test_tool_catalog_rejects_candidate_traversal``.
    Related proof: ``services/tool_detection.py`` and tool schemas.
    """

    detector = build_detector(tmp_path / "source", "windows", {}, path_lookup=lambda command, path: None)
    catalog = json.loads(detector.catalog_path.read_text(encoding="utf-8"))
    catalog["tools"][0]["candidates"][0]["pattern"] = "../outside/blender.exe"
    detector.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(ToolDetectionError, match="stay relative"):
        detector.detection_catalog()
