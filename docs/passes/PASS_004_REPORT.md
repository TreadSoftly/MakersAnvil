# PASS-004 Report - Safe Runtime File Intake Staging

## Status

Claim state: `staged`.

## What Changed

- Added a schema-backed metadata-only intake policy.
- Added metadata-only runtime intake records under `.makers-anvil/intake/records/`.
- Added `IntakeCatalogService` with contained app-owned record storage.
- Added `scripts/stage_intake.py` for one explicitly selected regular file.
- Added read-only API routes:
  - `GET /api/intake/policy`
  - `GET /api/intake/catalog`
- Updated `GET /api/state` with intake catalog status.
- Added a browser dashboard intake status panel.
- Added verifier and tests for intake containment, privacy, and blocked actions.

## Proven Boundaries

- Intake stores metadata only: display name, extension, kind, size, and modified time.
- Source paths and file contents are not stored.
- Source files are not copied, moved, deleted, extracted, executed, or handed to tools.
- Folder intake and symbolic-link sources are rejected.
- Browser and API intake mutations remain blocked.
- Archive files can be classified, but extraction remains blocked.

## Blocked Or Not Proven

- Browser/API upload.
- Direct selected-file handoff.
- Route execution.
- Output open actions.
- External tool launch.
- Tool install/update/uninstall/repair.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine proof.
- macOS, Linux, and browser-hosted runtime proof.

## Track Percentages

- Real app completion: `10.0000%`
- Windows local app: `10.0000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Verification

```text
python scripts/verify_project.py -> PASS
python -m pytest -q -> 20 passed
metadata staging smoke with an app-owned temporary source file -> PASS; source unchanged and smoke artifacts removed
local HTTP smoke for intake policy/catalog and blocked POST -> PASS
Chromium browser smoke at 1280px and true 390px device emulation -> PASS; no horizontal overflow
```

## Next Pass

PASS-005 - route preview foundation.
