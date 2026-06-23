# Makers Anvil Build Status

## Current Pass

PASS-006 - durable explainability and handoff contract.

## Track Percentages

- Real app completion: `15.0000%`
- Windows local app: `15.0000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Proven

- Local git repository tracks `https://github.com/TreadSoftly/MakersAnvil.git`.
- Reference material is ignored and not required by runtime source.
- Read-only Python backend exposes `GET /api/health`, `GET /api/state`, and `GET /api/claim-states`.
- Read-only Python backend exposes `GET /api/workspace/status` and `GET /api/passes/ledger`.
- Read-only Python backend exposes `GET /api/workspace/config` and `GET /api/workspace/layout`.
- Read-only Python backend exposes `GET /api/intake/policy` and `GET /api/intake/catalog`.
- State-changing API methods return a blocked response.
- Browser dashboard renders app state from the read-only API.
- Browser dashboard renders current pass, next pass, and source-truth path from durable status records.
- Browser dashboard renders the local workspace runtime root, detected directories, and init script status.
- Default local settings keep upload, route execution, tool launch, archive extraction, folder import, deletion, and packaging disabled.
- Metadata-only intake records do not store source paths or contents and do not copy, move, delete, extract, execute, or launch source files.
- Browser dashboard renders intake mode, record counts, source-data privacy, and API action status.
- Runtime data uses OS-standard per-user locations or an explicit absolute override, never the source checkout location.
- API and dashboard records expose logical storage metadata without resolved personal filesystem paths.
- Source discovery is based on installed module/script locations rather than the current working directory.
- Every tracked file has a machine-readable purpose and maintenance record.
- Python modules and public components are required to have docstrings.
- Frontend and workflow source files are required to have purpose comments.
- A start guide, architecture guide, file map, and code-explanation standard are committed repository truth.
- The explainability verifier prevents future passes from silently dropping documentation coverage.
- Project verifier and tests exist.
- PASS-002 browser smoke passed at desktop and mobile widths with current-pass and source-truth status visible.
- PASS-003 local verifier, pytest, HTTP smoke, workspace init, and browser smoke passed.
- PASS-004 verifier, 20 tests, metadata staging smoke, HTTP smoke, and desktop/mobile browser smoke passed.
- PASS-005 verifier, 29 tests, relocated-checkout smoke, external-working-directory launch, HTTP smoke, and desktop/mobile browser smoke passed.
- PASS-006 explainability checker covers all 63 tracked files; verifier, 31 tests, HTTP smoke, and desktop/mobile browser regression passed.

## Blocked Or Not Proven

- Browser/API file upload and direct selected-file handoff.
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

PASS-007 - route preview foundation.
