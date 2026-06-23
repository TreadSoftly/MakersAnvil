# Makers Anvil

Makers Anvil is a local-first control panel for DIY makers. It helps organize source files, tool readiness, route previews, output proof, and setup/release safety without pretending unproven actions are ready.

Current status: real application build pass 008 is staged at `20.0000%`. The app has a read-only local backend, a visible browser dashboard, durable status records, portable per-user runtime storage, metadata-only intake records, metadata-derived route previews, planned output bundles and proof checklists, project governance, schemas, tests, verification scripts, and a machine-enforced source-explainability contract. Browser/API upload, output creation/opening, proof capture, route execution, tool launch, installers, packaging, and clean-machine proof remain blocked until their own gates are built and tested.

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

The folder `Refrences For Makers Anvil Application/` is reference-only. It is ignored by git and must not be required by runtime code, tests, or packaged app files.

Makers Anvil is built Windows-first, with macOS, Linux, and browser-hosted support kept as planned targets until their own proof gates exist.

## Understanding And Continuing The Build

Start with `docs/START_HERE.md`. It gives the exact reading order for a new developer or AI model. `docs/ARCHITECTURE.md` explains data flow and safety boundaries, `docs/CODE_EXPLAINABILITY_STANDARD.md` defines required comments and docstrings, and `state/source_manifest.json` explains every tracked file.

Documentation quality is machine-checked:

```powershell
python scripts/check_explainability.py
```
