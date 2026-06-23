# Makers Anvil

Makers Anvil is a local-first control panel for DIY makers. It helps organize source files, tool readiness, route previews, output proof, and setup/release safety without pretending unproven actions are ready.

Current status: real application build pass 004 is staged. The app has a read-only local backend, a visible browser dashboard, durable status records, safe local workspace settings, metadata-only intake records, project governance, schemas, tests, and verification scripts. Browser/API upload, route execution, tool launch, installers, packaging, and clean-machine proof remain blocked until their own gates are built and tested.

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
python scripts/verify_project.py
python -m pytest -q
```

Initialize the app-owned local workspace directory when needed:

```powershell
python scripts/init_workspace.py
```

That command only creates `.makers-anvil/` app folders and a local manifest. It does not import files, extract archives, run routes, launch tools, or delete user data.

Stage metadata for one explicit local file:

```powershell
python scripts/stage_intake.py --path "C:\path\to\one-file.stl"
```

That command writes one app-owned JSON record containing the file name, extension, classified kind, size, and modified time. It does not store the source path or contents, copy or move the source, import folders, extract archives, run routes, or launch tools.

## Repository Policy

The folder `Refrences For Makers Anvil Application/` is reference-only. It is ignored by git and must not be required by runtime code, tests, or packaged app files.

Makers Anvil is built Windows-first, with macOS, Linux, and browser-hosted support kept as planned targets until their own proof gates exist.
