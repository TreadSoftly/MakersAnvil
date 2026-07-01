"""Purpose: Build or inspect the deterministic Windows one-file executable plan.

Used by: Developers and Windows GitHub Actions package verification.
Inputs: Repository source, pinned PyInstaller/pywebview dependencies, and ``--check``.
Outputs: Build-plan JSON or ``artifacts/windows/MakersAnvil.exe``.
Side effects: Build mode writes only ignored ``.build`` and ``artifacts`` trees.
Safety: Never installs dependencies, publishes releases, or modifies user data.
Failure behavior: Wrong platform, missing dependencies/resources, or build errors fail.
Related proof: ``tests/test_windows_packaging.py`` and Windows package CI smoke.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = ROOT / "scripts" / "run_desktop.py"
FRONTEND = ROOT / "frontend" / "public"
DIST = ROOT / "artifacts" / "windows"
WORK = ROOT / ".build" / "pyinstaller"


class PackagingPreconditionError(RuntimeError):
    """Purpose: Identify a missing platform, dependency, or package resource.

    Inputs: A precise precondition diagnostic from the packaging boundary.
    Outputs: Typed failure used by the CLI and tests.
    How it works: Retains standard ``RuntimeError`` semantics.
    Side effects: None until raised.
    Failure behavior: Preserves the original diagnostic without fallback builds.
    Safety: Prevents incomplete executables from being reported as successful.
    Example: Linux build attempts raise before writing Windows artifacts.
    Related proof: ``tests/test_windows_packaging.py`` covers each precondition.
    """


def build_arguments(root: Path = ROOT) -> list[str]:
    """Purpose: Return the exact PyInstaller arguments for the Windows bundle.

    Inputs: Repository root, overridden only by isolated tests.
    Outputs: Ordered argument list with one entrypoint and bundled frontend tree.
    How it works: Uses repository-relative inputs and ignored repository outputs.
    Side effects: None; this function only constructs strings.
    Failure behavior: Missing files are rejected by ``validate_source`` first.
    Safety: No personal path, external download, signing key, or publish target exists.
    Example: The plan includes ``--onefile``, ``--windowed``, and ``MakersAnvil``.
    Related proof: ``tests/test_windows_packaging.py`` locks every critical option.
    """

    return [
        "--onefile",
        "--windowed",
        "--name",
        "MakersAnvil",
        "--paths",
        str(root / "backend" / "src"),
        "--add-data",
        f"{root / 'frontend' / 'public'}:frontend/public",
        "--add-data",
        f"{root / 'config'}:config",
        "--add-data",
        f"{root / 'schemas'}:schemas",
        "--add-data",
        f"{root / 'state'}:state",
        "--hidden-import",
        "webview",
        "--distpath",
        str(root / "artifacts" / "windows"),
        "--workpath",
        str(root / ".build" / "pyinstaller" / "work"),
        "--specpath",
        str(root / ".build" / "pyinstaller" / "spec"),
        "--clean",
        "--noconfirm",
        str(root / "scripts" / "run_desktop.py"),
    ]


def validate_source(root: Path = ROOT) -> None:
    """Purpose: Reject a package plan whose entrypoint or frontend is incomplete.

    Inputs: Repository root containing expected source locations.
    Outputs: ``None`` only when required package inputs exist.
    How it works: Checks the launcher plus frontend index and local assets folder.
    Side effects: Reads filesystem metadata only.
    Failure behavior: Raises ``PackagingPreconditionError`` naming the missing item.
    Safety: Does not create output folders before validation succeeds.
    Example: A checkout missing ``index.html`` cannot create a misleading executable.
    Related proof: ``tests/test_windows_packaging.py`` exercises missing inputs.
    """

    required = [
        root / "scripts" / "run_desktop.py",
        root / "frontend" / "public" / "index.html",
        root / "frontend" / "public" / "assets",
        root / "config",
        root / "config" / "windows_installer_policy.json",
        root / "config" / "clean_machine_scenarios.json",
        root / "schemas",
        root / "state" / "current_status.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise PackagingPreconditionError(f"Windows package source is incomplete: {', '.join(missing)}")


def package_plan(root: Path = ROOT) -> dict[str, object]:
    """Purpose: Expose a path-portable, non-building Windows package preview.

    Inputs: A repository root whose required inputs pass validation.
    Outputs: Machine-readable source, output, dependency, and safety plan.
    How it works: Normalizes all paths relative to the supplied root.
    Side effects: Reads source metadata only and writes nothing.
    Failure behavior: Invalid source layout raises before a plan is returned.
    Safety: The plan cannot install, sign, publish, or claim clean-machine proof.
    Example: ``python scripts/build_windows_exe.py --check`` prints this record.
    Related proof: ``tests/test_windows_packaging.py`` validates portable fields.
    """

    validate_source(root)
    arguments = build_arguments(root)
    return {
        "schemaVersion": "makers-anvil.windows-package-plan.v1",
        "claimState": "staged",
        "platform": "windows",
        "format": "one-file-executable",
        "entrypoint": "scripts/run_desktop.py",
        "frontend": "frontend/public",
        "bundledReadOnlyData": ["config", "schemas", "state"],
        "expectedArtifact": "artifacts/windows/MakersAnvil.exe",
        "installerFoundation": {
            "format": "msix",
            "expectedArtifact": "artifacts/windows/MakersAnvil.msix",
            "policy": "config/windows_installer_policy.json",
            "cleanMachineScenarios": "config/clean_machine_scenarios.json",
            "installerBuilt": False,
        },
        "dependencies": {"pywebview": "6.2.1", "pyinstaller": "6.21.0", "webview2": "evergreen-runtime"},
        "arguments": arguments,
        "safety": {
            "dependencyInstallPerformed": False,
            "artifactBuilt": False,
            "artifactSigned": False,
            "artifactPublished": False,
            "cleanMachineProven": False,
        },
    }


def build(root: Path = ROOT) -> Path:
    """Purpose: Invoke installed PyInstaller for one local Windows executable.

    Inputs: Valid Windows source plus already-installed pinned build dependencies.
    Outputs: Absolute path to the created ``MakersAnvil.exe``.
    How it works: Calls PyInstaller's Python API with the deterministic arguments.
    Side effects: Writes ignored build intermediates and one ignored artifact.
    Failure behavior: Non-Windows, missing modules, build errors, or absent output fail.
    Safety: Does not install dependencies, sign code, publish, or touch user files.
    Example: A prepared build environment runs ``python scripts/build_windows_exe.py``.
    Related proof: Windows CI runs the resulting executable with ``--smoke``.
    """

    if sys.platform != "win32":
        raise PackagingPreconditionError("The Windows executable must be built on Windows.")
    validate_source(root)
    if importlib.util.find_spec("PyInstaller") is None or importlib.util.find_spec("webview") is None:
        raise PackagingPreconditionError("Pinned PyInstaller and pywebview dependencies must already be installed.")
    from PyInstaller.__main__ import run as run_pyinstaller

    run_pyinstaller(build_arguments(root))
    artifact = root / "artifacts" / "windows" / "MakersAnvil.exe"
    if not artifact.is_file():
        raise PackagingPreconditionError(f"PyInstaller completed without the expected artifact: {artifact}")
    return artifact


def main(argv: Sequence[str] | None = None) -> int:
    """Purpose: Dispatch non-writing plan inspection or the explicit Windows build.

    Inputs: Optional argument sequence containing only the ``--check`` flag.
    Outputs: JSON plan/check result and a process exit code.
    How it works: Parses one switch, then calls ``package_plan`` or ``build``.
    Side effects: Check mode is read-only; build mode writes ignored artifacts only.
    Failure behavior: Preconditions print a failed JSON result and return nonzero.
    Safety: No CLI argument accepts arbitrary source, output, command, or URL values.
    Example: CI invokes build mode, then runs ``MakersAnvil.exe --smoke``.
    Related proof: ``tests/test_windows_packaging.py`` covers dispatch contracts.
    """

    parser = argparse.ArgumentParser(description="Build the Makers Anvil Windows executable.")
    parser.add_argument("--check", action="store_true", help="Print the deterministic plan without building.")
    args = parser.parse_args(argv)
    try:
        if args.check:
            print(json.dumps(package_plan(), indent=2, sort_keys=True))
            return 0
        artifact = build()
        print(json.dumps({"claimState": "staged", "artifact": str(artifact), "built": True}, indent=2))
        return 0
    except PackagingPreconditionError as exc:
        print(json.dumps({"claimState": "failed", "built": False, "message": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
