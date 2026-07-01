# Makers Anvil

Makers Anvil is a local-first control panel for DIY makers. It helps organize source files, tool readiness, route previews, output proof, and setup/release safety without pretending unproven actions are ready.

Current status: PASS-021 adds read-only backup, restore, update, uninstall, and repair plans with bounded path-redacted app-data inventory and preservation rules. Lifecycle execution, archives, restore writes, network/package access, installers, software mutation, deletion, release, and clean-machine claims remain gated.

## Run Locally

Requirements for the current pass:

- Python 3.11 or newer

Start the local app:

```powershell
python scripts/run_dev.py
```

Open:

```text
http://127.0.0.1:8765
```

Start the native desktop app after installing the pinned optional desktop dependency:

```powershell
python scripts/run_desktop.py
```

Inspect or build the Windows one-file executable:

```powershell
python scripts/build_windows_exe.py --check
python scripts/build_windows_exe.py
artifacts\windows\MakersAnvil.exe --smoke
```

Build outputs are ignored local artifacts. GitHub Actions builds and smoke-tests a Windows executable for the draft pull request; this is not yet a signed installer or public release.

## Verify

```powershell
python scripts/build_learning_guide.py --check
python scripts/check_explainability.py
python scripts/verify_project.py
python -m pytest -q
```

Initialize the app-owned local workspace directory when needed:

```powershell
python scripts/init_workspace.py
```

That command creates app-owned folders in the operating system's per-user application-data location and writes a local manifest. It does not write runtime data beside the source checkout, import files, extract archives, run routes, launch tools, or delete user data.

The workbench now supports the normal intake path:

1. Choose one file.
2. Review its name, kind, and byte size.
3. Select **Authorize copy**.

The browser sends metadata first and bytes second under a short-lived, one-time authorization. The app stores a generated-name quarantine copy and SHA-256 record without storing the source path or changing the selected source file.

The earlier explicit metadata-only learning command remains available:

```powershell
python scripts/stage_intake.py --path "<path-to-one-file.stl>"
```

That command writes one app-owned JSON record containing the file name, extension, classified kind, size, and modified time. It does not store the source path or contents, copy or move the source, import folders, extract archives, run routes, or launch tools.

## Portable Paths

The source checkout can be cloned, copied, moved, or renamed. Source and static-file discovery is based on the installed module or script location, not a username, desktop folder, cloud-sync folder, drive letter, or current working directory.

Runtime data uses standard per-user locations:

- Windows: local application data under `TreadSoftly/MakersAnvil`
- macOS: Application Support under `TreadSoftly/MakersAnvil`
- Linux: XDG data under `treadsoftly/makers-anvil`

Set `MAKERS_ANVIL_DATA_DIR` to an absolute directory to use an explicit data location. Resolved personal paths are not exposed through the API or dashboard.

## Repository Policy

The planning roots and `Previous Working MA For References/` are reference-only. They are ignored by git and must not be required by runtime code, tests, or packaged app files. Accepted design lessons and the no-duplicate migration registry are preserved in `docs/PREVIOUS_APP_REFERENCE_STUDY.md`, `docs/PREVIOUS_APP_MERGER_AUDIT.md`, and `state/previous_app_migration.json`.

Makers Anvil is built Windows-first, with macOS, Linux, and browser-hosted support kept as planned targets until their own proof gates exist.

## Understanding And Continuing The Build

Start with `docs/START_HERE.md`. It gives the exact reading order for a new developer or AI model. `docs/SOURCE_WALKTHROUGH.md` traces the actual files, `docs/LINE_BY_LINE_CODE_GUIDE.md` explains every covered source line at matching line numbers, `docs/PREVIOUS_APP_REFERENCE_STUDY.md` preserves the intended workbench direction, and `state/source_manifest.json` explains every tracked file.

Documentation quality is machine-checked:

```powershell
python scripts/build_learning_guide.py --check
python scripts/check_explainability.py
```
