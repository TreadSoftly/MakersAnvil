# Makers Anvil

Makers Anvil is a local-first control panel for DIY makers. It helps organize source files, tool readiness, route previews, output proof, and setup/release safety without pretending unproven actions are ready.

Current status: real application build pass 016 is staged at `35.0000%`. The preview-first maker workbench is unchanged, while its source now carries detailed component/block teaching documentation and a generated, hash-checked guide explains every physical implementation and contract line. Browser/API upload, authorization acceptance, runnable commands, selected-file handoff, process signaling/execution, output artifacts, tool launch, packaging, and clean-machine proof remain blocked until their own gates are built and tested.

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

Stage metadata for one explicit local file:

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

Set `MAKERS_ANVIL_DATA_DIR` to an absolute directory to use an explicit data location. Resolved personal paths are not exposed through the read-only API or dashboard.

## Repository Policy

The planning roots and `Previous Working MA For References/` are reference-only. They are ignored by git and must not be required by runtime code, tests, or packaged app files. Accepted prior-app design lessons are preserved in `docs/PREVIOUS_APP_REFERENCE_STUDY.md`.

Makers Anvil is built Windows-first, with macOS, Linux, and browser-hosted support kept as planned targets until their own proof gates exist.

## Understanding And Continuing The Build

Start with `docs/START_HERE.md`. It gives the exact reading order for a new developer or AI model. `docs/SOURCE_WALKTHROUGH.md` traces the actual files, `docs/LINE_BY_LINE_CODE_GUIDE.md` explains every covered source line at matching line numbers, `docs/PREVIOUS_APP_REFERENCE_STUDY.md` preserves the intended workbench direction, and `state/source_manifest.json` explains every tracked file.

Documentation quality is machine-checked:

```powershell
python scripts/build_learning_guide.py --check
python scripts/check_explainability.py
```
