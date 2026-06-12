# Makers Anvil Build Status

## Current Pass

PASS-001 — clean product foundation and read-only local app shell.

## Track Percentages

- Real app completion: `2.5000%`
- Windows local app: `2.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Proven

- Local git repository tracks `https://github.com/TreadSoftly/MakersAnvil.git`.
- Reference material is ignored and not required by runtime source.
- Read-only Python backend exposes `GET /api/health`, `GET /api/state`, and `GET /api/claim-states`.
- State-changing API methods return a blocked response.
- Browser dashboard renders app state from the read-only API.
- Project verifier and tests exist.
- Browser smoke passed at desktop and mobile widths with no console errors or horizontal overflow.

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

PASS-002 — workspace state and durable status records.
