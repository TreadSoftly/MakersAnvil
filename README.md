# Makers Anvil

Makers Anvil is a local-first control panel for DIY makers. It helps organize source files, tool readiness, route previews, output proof, and setup/release safety without pretending unproven actions are ready.

Current status: real application build pass 002 is staged. The app has a read-only local backend, a visible browser dashboard, durable status records, project governance, schemas, tests, and verification scripts. File intake, route execution, tool launch, installers, packaging, and clean-machine proof remain blocked until their own gates are built and tested.

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

## Repository Policy

The folder `Refrences For Makers Anvil Application/` is reference-only. It is ignored by git and must not be required by runtime code, tests, or packaged app files.

Makers Anvil is built Windows-first, with macOS, Linux, and browser-hosted support kept as planned targets until their own proof gates exist.
