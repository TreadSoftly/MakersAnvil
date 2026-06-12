# Makers Anvil Build Status

## Current Pass

PASS-002 — workspace state and durable status records.

## Track Percentages

- Real app completion: `5.0000%`
- Windows local app: `5.0000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Proven

- Local git repository tracks `https://github.com/TreadSoftly/MakersAnvil.git`.
- Reference material is ignored and not required by runtime source.
- Read-only Python backend exposes `GET /api/health`, `GET /api/state`, and `GET /api/claim-states`.
- Read-only Python backend exposes `GET /api/workspace/status` and `GET /api/passes/ledger`.
- State-changing API methods return a blocked response.
- Browser dashboard renders app state from the read-only API.
- Browser dashboard renders current pass, next pass, and source-truth path from durable status records.
- Project verifier and tests exist.
- PASS-002 browser smoke passed at desktop and mobile widths with current-pass and source-truth status visible.

## Blocked Or Not Proven

- Runtime file intake.
- Route execution.
- Output open actions.
- External tool launch.
- Selected-file handoff.
- Install, update, uninstall, or repair actions.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine setup proof.
- macOS, Linux, and browser-hosted runtime support.

## Next Pass

PASS-003 — workspace data directory and safe local settings.
