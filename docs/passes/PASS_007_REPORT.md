# PASS-007 Report - Metadata-Derived Route Preview Foundation

## Status

Claim state: `staged`.

## What Changed

- Added a committed route catalog for mesh, CAD, image, toolpath, document, and archive metadata kinds.
- Added schemas for route-catalog configuration and route-preview API responses.
- Added `RoutePreviewService`, which consumes only validated intake records.
- Added read-only `GET /api/routes/preview` and composed route-preview app state.
- Added a responsive dashboard panel for preview status, candidate steps, tool family, and blockers.
- Added isolated service tests and project-verifier coverage.

## Proven Boundaries

- Recognized intake kinds map to one deterministic route candidate.
- Unknown kinds are counted as unmatched instead of being guessed into a route.
- Preview generation still works after the original source file is unavailable.
- Display names are rendered through DOM text nodes rather than injected HTML.
- Route steps are `planned`, preview readiness is false, and every action remains disabled.
- Source-path use, content reads, file opening, archive extraction, route execution, tool launch, and output creation remain false.

## Blocked Or Not Proven

- Browser/API upload and selected-file handoff.
- Source-content inspection and archive extraction.
- Tool detection or launch.
- Route execution.
- Output creation or opening.
- Install, update, uninstall, or repair actions.
- Packaged release and clean-machine proof.
- Full macOS, Linux, and browser-hosted runtime proof.

## Track Percentages

- Real app completion: `17.5000%`
- Windows local app: `17.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Verification

```text
python scripts/check_explainability.py -> passed; 69 tracked files covered
python scripts/verify_project.py -> passed; all eight check groups passed
python -m pytest -q -> passed; 40 tests
node --check frontend/public/assets/app.js -> passed
normal HTTP smoke -> passed; PASS-007, 17.5000%, PASS-008 next, zero-preview state
isolated runtime HTTP smoke -> passed; one mesh candidate with four disabled steps
state-changing HTTP smoke -> passed; POST remained blocked with 405
desktop browser regression -> passed for empty and populated preview states at 1280x900
mobile browser regression -> passed for empty and populated preview states at 390x844
browser layout and runtime checks -> no horizontal overflow, enabled route buttons, load failures, or page errors
```

## Next Pass

PASS-008 - output bundle and proof panels.
