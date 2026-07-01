"""Purpose: Prove the Windows executable plan is portable and non-publishing.

Used by: Developers and CI before invoking PyInstaller on Windows.
Inputs: Current checkout plus isolated incomplete package trees.
Outputs: Assertions for pinned tools, relative contracts, and fail-closed inputs.
Side effects: Creates pytest-owned temporary fixture trees only.
Safety: Tests never install, build, sign, execute, or publish an artifact.
Failure behavior: Personal paths or weakened package safety fail immediately.
Related proof: ``scripts/build_windows_exe.py`` and Windows package CI.
"""

from pathlib import Path

import pytest

from scripts import build_windows_exe


def test_package_plan_is_one_file_portable_and_non_publishing() -> None:
    """Purpose: Lock the Windows package identity, inputs, outputs, and safety state.

    Inputs: Current repository's validated package source.
    Outputs: Assertions over format, dependencies, arguments, and false claims.
    How it works: Reads the deterministic ``--check`` plan without building.
    Side effects: Reads source metadata only.
    Failure behavior: Missing options, changed pins, or enabled claims fail.
    Safety: Ensures check mode cannot masquerade as build/release proof.
    Example: The expected artifact is ``artifacts/windows/MakersAnvil.exe``.
    Related proof: GitHub's Windows job builds and smokes that exact artifact.
    """

    plan = build_windows_exe.package_plan()
    arguments = plan["arguments"]

    assert plan["format"] == "one-file-executable"
    assert plan["entrypoint"] == "scripts/run_desktop.py"
    assert plan["expectedArtifact"] == "artifacts/windows/MakersAnvil.exe"
    assert plan["installerFoundation"] == {
        "format": "msix",
        "expectedArtifact": "artifacts/windows/MakersAnvil.msix",
        "policy": "config/windows_installer_policy.json",
        "cleanMachineScenarios": "config/clean_machine_scenarios.json",
        "installerBuilt": False,
    }
    assert plan["bundledReadOnlyData"] == ["config", "schemas", "state"]
    assert plan["dependencies"] == {
        "pywebview": "6.2.1",
        "pyinstaller": "6.21.0",
        "webview2": "evergreen-runtime",
    }
    assert "--onefile" in arguments
    assert "--windowed" in arguments
    assert "webview" in arguments
    assert any("config:config" in value for value in arguments)
    assert any("schemas:schemas" in value for value in arguments)
    assert any("state:state" in value for value in arguments)
    assert all(value is False for value in plan["safety"].values())


def test_package_plan_rejects_incomplete_source(tmp_path: Path) -> None:
    """Purpose: An incomplete checkout cannot produce package-ready truth.

    Inputs: Empty pytest-owned temporary directory.
    Outputs: Expected precondition error naming missing package source.
    How it works: Calls source validation before any builder is imported.
    Side effects: Reads temporary filesystem metadata only.
    Failure behavior: Returning a plan for missing assets fails this test.
    Safety: Prevents blank or misleading executables from entering CI artifacts.
    Example: Missing launcher and index produce one bounded diagnostic.
    Related proof: Runtime resource validation repeats the defense at startup.
    """

    with pytest.raises(build_windows_exe.PackagingPreconditionError, match="source is incomplete"):
        build_windows_exe.package_plan(tmp_path)


def test_build_arguments_derive_every_path_from_supplied_root(tmp_path: Path) -> None:
    """Purpose: Package construction never embeds this developer's checkout path.

    Inputs: Arbitrary temporary root supplied to pure argument construction.
    Outputs: Assertions that every path-bearing argument contains that root.
    How it works: Examines paths following known PyInstaller path switches.
    Side effects: None.
    Failure behavior: A fixed or personal path fails the containment assertions.
    Safety: Protects clone, copy, rename, and CI portability.
    Example: A relocated root changes entrypoint, data, work, and output paths.
    Related proof: ``tests/test_project_purity.py`` scans product text too.
    """

    arguments = build_windows_exe.build_arguments(tmp_path)
    path_switches = {"--paths", "--add-data", "--distpath", "--workpath", "--specpath"}
    for index, argument in enumerate(arguments[:-1]):
        if argument in path_switches:
            assert str(tmp_path) in arguments[index + 1]
    assert str(tmp_path) in arguments[-1]
