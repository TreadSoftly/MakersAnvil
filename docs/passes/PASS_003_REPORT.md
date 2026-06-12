# PASS-003 Report — Workspace Data Directory And Safe Local Settings

## Status

Claim state: `staged`.

## What Changed

- Added `config/default_settings.json` for safe local workspace defaults.
- Added `WorkspaceConfigService` for app-owned workspace layout policy.
- Added `scripts/init_workspace.py` to create `.makers-anvil/` directories on demand.
- Added read-only API routes:
  - `GET /api/workspace/config`
  - `GET /api/workspace/layout`
- Updated `GET /api/state` to include workspace layout details.
- Updated the browser dashboard to show runtime root, directory detection count, and init-script status.
- Added schema, verifier, and tests for local settings and workspace containment.
- Fixed roadmap numbering.

## Proven

- Default local settings parse and keep all unsafe action flags disabled.
- Workspace layout paths are relative and contained under `.makers-anvil`.
- Workspace initialization creates only app-owned directories and a local manifest.
- The backend exposes workspace config/layout records through read-only endpoints.
- `GET /api/state` reports `PASS-003` and `7.5000%` real app completion.
- State-changing API requests remain blocked.

## Blocked Or Not Proven

- Runtime user upload.
- Route execution.
- Output open actions.
- External tool launch.
- Selected-file handoff.
- Tool install/update/uninstall/repair.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine proof.
- macOS, Linux, and browser-hosted runtime proof.

## Track Percentages

- Real app completion: `7.5000%`
- Windows local app: `7.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Verification

```text
python scripts/verify_project.py -> PASS
python -m pytest -q -> 14 passed
python scripts/init_workspace.py -> created only .makers-anvil/ app-owned directories and manifest
local HTTP smoke for GET /api/workspace/config, GET /api/workspace/layout, and blocked POST /api/workspace/config -> PASS
in-app browser smoke at desktop and 390px widths -> PASS
```

## Next Pass

PASS-004 — safe runtime file intake staging.
