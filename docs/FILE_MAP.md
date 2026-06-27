# File And Folder Map

The machine-checkable explanation for every tracked file is `state/source_manifest.json`. This document explains how the folders fit together so a reader knows where to look first. For a numbered explanation of every physical implementation and structured-contract line, use `docs/LINE_BY_LINE_CODE_GUIDE.md` and verify its exact hashes in `state/learning_coverage.json`.

## Root

- `README.md` is the user/developer overview and command reference.
- `package.json` and `pyproject.toml` declare JavaScript/Python project metadata and test commands.
- `.gitignore` keeps generated, local, and reference-only material outside product history.
- `LICENSE` defines reuse terms.

## `.github/`

Contains repository automation. The CI workflow runs the verifier and tests on Windows, Ubuntu, and macOS.

## `backend/`

Contains the Python application package. `server.py` owns loopback HTTP serving, `api/` owns route mapping, `domain/` owns shared vocabulary, and `services/` owns focused business and filesystem rules.

## `frontend/`

Contains the static dashboard. It has no build step and performs read-only API calls. HTML defines structure, CSS defines responsive presentation, JavaScript fetches and renders state, and the SVG is the product mark.

## `config/`

Contains safe committed defaults. These files describe policy; resolved personal paths and runtime records do not belong here.

## `schemas/`

Contains JSON Schema contracts for API, state, settings, intake, runtime location, and source-manifest records.

## `state/`

Contains durable machine-readable truth: current progress, pass history, and the explanation/ownership record for every tracked file.

## `scripts/`

Contains explicit developer and local-user entrypoints. Scripts resolve the repository from their own file location and must work from unrelated current working directories.

## `tests/`

Contains executable behavior examples. Tests cover API safety, intake privacy, runtime containment, portability, source purity, documentation governance, and verifier integrity.

## `docs/`

Contains durable human-readable truth. `START_HERE.md` is the entrypoint, `SOURCE_WALKTHROUGH.md` traces actual files, `PREVIOUS_APP_REFERENCE_STUDY.md` preserves the accepted workbench direction, `IMPLEMENTATION_GUIDE.md` explains extension flows, `CONTINUE_PROTOCOL.md` defines the pass loop, and `passes/` preserves bounded pass evidence.
