# Makers Anvil Build Status

## Current Pass

PASS-011 - single-route execution gate foundation.

## Track Percentages

- Real app completion: `27.5000%`
- Windows local app: `27.5000%`
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
- Read-only `GET /api/routes/preview` maps validated intake metadata to deterministic candidate routes.
- Preview records expose planned steps, tool-family requirements, and explicit readiness blockers.
- Preview generation does not reopen source files or enable source access, archive extraction, execution, tool launch, or output creation.
- Browser route-preview status and candidate rows render untrusted display names as text rather than HTML.
- Read-only `GET /api/outputs/preview` maps route previews to planned bundles, artifacts, and proof requirements.
- Output plans use logical app-owned destinations and expose no resolved personal filesystem paths.
- Expected artifacts remain nonexistent and unopened; required proof remains incomplete and not proven.
- Output creation, opening, proof capture, route execution, and tool launch remain disabled.
- Browser output and proof rows render metadata through text nodes and stack responsively on narrow screens.
- Read-only `GET /api/tools/detection` checks six known maker tools through PATH and narrow standard-location candidates.
- Detection returns platform, tool family, method, and executable name without returning resolved installation paths.
- No tool process or version command is executed; no registry data is read and no filesystem data is written.
- Missing candidates and tool versions remain not proven rather than being guessed.
- Launch, install, update, uninstall, and repair actions remain blocked.
- Browser tool inventory and family coverage render without executable controls.
- Read-only `GET /api/tools/dry-run` joins route previews, logical output bundles, and path-redacted tool evidence.
- Dry-run policy covers every configured route and only prefers tools that advertise the required family.
- Dry-run invocation plans expose semantic operations, logical source/output references, and explicit blockers without executable paths.
- No runnable command is constructed; no source/output path is resolved; no file is handed off; no process runs; and no file is written.
- Browser dry-run summaries and plan rows render through text nodes without action controls.
- Read-only `GET /api/execution/gates` evaluates exactly one allowlisted route and keeps execution disabled.
- Ten required gates cover route scope, dry-run availability, tool detection, explicit authorization, source/output containment, version compatibility, cancellation, logging, and output proof.
- Only existing planning evidence can satisfy a gate; operational evidence remains not proven.
- Out-of-scope plans are counted but never receive an execution evaluation.
- No execution request, accepted authorization, resolved path, command, process, launch, write, log, cancellation signal, or proof is produced.
- Browser gate progress and evidence rows render without execution controls.
- Project verifier and tests exist.
- PASS-002 browser smoke passed at desktop and mobile widths with current-pass and source-truth status visible.
- PASS-003 local verifier, pytest, HTTP smoke, workspace init, and browser smoke passed.
- PASS-004 verifier, 20 tests, metadata staging smoke, HTTP smoke, and desktop/mobile browser smoke passed.
- PASS-005 verifier, 29 tests, relocated-checkout smoke, external-working-directory launch, HTTP smoke, and desktop/mobile browser smoke passed.
- PASS-006 explainability checker covers all 63 tracked files; verifier, 31 tests, HTTP smoke, and desktop/mobile browser regression passed.
- PASS-007 explainability covers 69 files; verifier, 40 tests, normal/isolated HTTP smoke, and four desktop/mobile browser regressions passed.
- PASS-008 explainability covers 75 files; verifier, 47 tests, non-writing HTTP smoke, and four desktop/mobile browser regressions passed.
- PASS-009 explainability covers 81 files; verifier, 54 tests, real/isolated HTTP smoke, and four desktop/mobile browser regressions passed.
- PASS-010 explainability covers 87 files; verifier, 61 tests, schema validation, real/isolated HTTP smoke, and four desktop/mobile browser regressions passed.
- PASS-011 explainability covers 93 files; verifier, 69 tests, schema validation, real/isolated HTTP smoke, and four desktop/mobile browser regressions passed.

## Blocked Or Not Proven

- Browser/API file upload and direct selected-file handoff.
- Route execution.
- Output creation.
- Output open actions.
- Proof capture.
- External tool launch.
- Tool version proof.
- Runnable tool command construction.
- Execution request creation.
- User authorization acceptance.
- Cancellation control.
- Execution logging.
- Selected-file handoff.
- Install, update, uninstall, or repair actions.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine setup proof.
- macOS, Linux, and browser-hosted runtime support.

## Next Pass

PASS-012 - execution request and audit record foundation.
