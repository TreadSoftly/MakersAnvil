# PASS-009 Report - Path-Redacted Tool Detection Foundation

## Status

Claim state: `staged`.

## What Changed

- Added a committed catalog for Blender, FreeCAD, UltiMaker Cura, PrusaSlicer, OrcaSlicer, and GIMP.
- Added schemas for tool-catalog configuration and tool-detection API responses.
- Added `ToolDetectionService` with platform normalization, PATH lookup, and narrow standard-location candidates.
- Added read-only `GET /api/tools/detection` and composed tool-detection app state.
- Added responsive dashboard tool inventory and family-coverage status.
- Added isolated detector tests and project-verifier coverage.

## Proven Boundaries

- Detection checks only PATH command names and configured standard-location patterns.
- Provider-relative patterns cannot traverse outside their private roots.
- Resolved paths are used only for presence checks and are never returned through API state.
- No process or version command is executed.
- No registry data is read and no filesystem data is written.
- Missing matches are `not proven`, not a claim that software is absent.
- Launch, install, update, uninstall, and repair actions remain blocked.

## Blocked Or Not Proven

- Tool version proof or compatibility proof.
- Tool launch and selected-file handoff.
- Tool install, update, uninstall, or repair.
- Route execution.
- Output creation/opening and proof capture.
- Archive extraction and folder import.
- Packaged release and clean-machine proof.
- Full macOS, Linux, and browser-hosted runtime proof.

## Track Percentages

- Real app completion: `22.5000%`
- Windows local app: `22.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Verification

- `python scripts/check_explainability.py` passed with all `81` tracked files mapped.
- `python scripts/verify_project.py` passed all `8` verification groups.
- `python -m pytest -q` passed all `54` tests.
- `node --check frontend/public/assets/app.js` and `git diff --check` passed.
- Live real-machine HTTP smoke returned PASS-009, `22.5000%`, PASS-010 next, and `0/6` detected tools without inventing absence claims.
- Live isolated HTTP smoke detected exactly PrusaSlicer from a fake standard location, returned no private test path, left the fixture hash unchanged, kept versions not proven, and rejected POST with `405`.
- Standalone Chrome browser smoke passed real and isolated data at `1280x900` and `390x844`: all four cases rendered without page/console errors, horizontal overflow, tool-action controls, or private-path exposure.
- Desktop and mobile screenshots were visually inspected; the six-tool inventory, family coverage, detected state, and blocked actions remained readable.

## Next Pass

PASS-010 - tool dry-run planning.
