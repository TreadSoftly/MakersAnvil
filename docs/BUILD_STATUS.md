# Makers Anvil Build Status

## Current Pass

PASS-020 - contained built-in STL preflight with cancellation, audit, and output proof.

## Track Percentages

- Real app completion: `62.5000%`
- Windows local app: `67.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `12.5000%`
- Clean-machine proof: `0.0000%`

## Proven

- Local git repository tracks `https://github.com/TreadSoftly/MakersAnvil.git`.
- Reference material is ignored and not required by runtime source.
- Read-only Python backend exposes `GET /api/health`, `GET /api/state`, and `GET /api/claim-states`.
- Read-only Python backend exposes `GET /api/workspace/status` and `GET /api/passes/ledger`.
- Read-only Python backend exposes `GET /api/workspace/config` and `GET /api/workspace/layout`.
- Read-only Python backend exposes `GET /api/intake/policy` and `GET /api/intake/catalog`.
- Only guarded intake, complete workbench-preference, and contained STL-preflight routes accept POST; all other state-changing API methods return a blocked response.
- Browser dashboard renders app state and performs only bounded authorized intake, presentation-preference, and contained-preflight mutations.
- Browser dashboard renders current pass, next pass, and source-truth path from durable status records.
- Browser dashboard renders the local workspace runtime root, detected directories, and init script status.
- Default local settings enable only user-authorized intake; route execution, tool launch, archive extraction, folder import, deletion, and release packaging remain disabled.
- Authorized intake records expose no source path, use generated logical names, include exact byte size and SHA-256 proof, and keep every downstream action false.
- Browser dashboard provides choose, review, authorize, cancel, progress, success, and error states for one file without drag/drop or paste.
- Runtime data uses OS-standard per-user locations or an explicit absolute override, never the source checkout location.
- API and dashboard records expose logical storage metadata without resolved personal filesystem paths.
- Source discovery is based on installed module/script locations rather than the current working directory.
- Every tracked file has a machine-readable purpose and maintenance record.
- Every Python component, including private helpers and tests, is required to have a docstring.
- Every top-level frontend function requires JSDoc; frontend and workflow files require purpose comments.
- A start guide, implementation guide, learning-resource map, pass-report template, architecture guide, file map, and code-explanation standard are committed repository truth.
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
- Read-only `GET /api/execution/requests/preview` joins coherent mesh dry-run plans and gate evaluations into deterministic logical intent.
- Request preview records use logical source/output references and never expose resolved private paths.
- Explicit authorization remains required but unaccepted, with no actor or acceptance timestamp.
- Six append-only lifecycle event types are required while the audit event list stays empty and event writes stay disabled.
- Request persistence, authorization acceptance, audit writes, path resolution, command construction, processes, tool launch, filesystem writes, and proof capture remain false.
- Browser request-preview status and rows render authorization, audit, and execution-blocked truth without action controls.
- `python scripts/prepare_job.py --request-preview-id <id>` creates one deterministic prepared job under the app-owned jobs root.
- Prepared workspaces contain only empty `control`, `working`, `logs`, and `outputs` directories plus path-redacted JSON records.
- `python scripts/request_job_cancel.py --job-id <id>` records cancellation intent idempotently without signaling or stopping a process.
- Read-only `GET /api/jobs/policy` and `GET /api/jobs/catalog` expose local-script boundaries, prepared jobs, cancellation state, and zero execution readiness.
- Malformed, weakened, traversing, and symlinked job data fails closed; source and runtime absolute paths remain private.
- Browser job rows render logical workspace locations and distinguish cancellation requests from process-stop proof.
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
- PASS-012 explainability covers 102 files; verifier, 76 tests, four schema validations, live/isolated HTTP smoke, desktop/mobile/non-empty browser checks, and Windows/Ubuntu/macOS CI passed.
- PASS-013 explainability covers 113 files; verifier, 86 tests, six schema validations, live/isolated script and HTTP smoke, empty/populated desktop/mobile browser checks, and Windows/Ubuntu/macOS CI passed.
- PASS-014 preserves the accepted previous-app workbench direction in tracked truth, adds a file-by-file source walkthrough, and replaces weak one-line module headers with machine-enforced structured context. Runtime capability remains `32.5000%` because this remediation pass enables no new action.
- PASS-015 replaces the long equal-weight status stack with a preview-first workbench: persistent rail, compact command bar, intake/selected-input deck, tool inventory, stable Work Flow/Plans/Dev command deck, output-proof inspector, and responsive mobile flow. Navigation is client-side only and all operational actions remain blocked.
- PASS-016 expands every Python and JavaScript component into a nine-field teaching contract, adds purpose/mechanism/example/safety comments to every CSS and semantic HTML block, and generates hash-checked numbered explanations for every physical implementation and contract line. Runtime capability remains `35.0000%` because this remediation pass enables no new action.
- PASS-017 inventories the previous working app without importing its 3.7 GB dependency/generated tree, records every capability migration decision, locally explains all 14,611 lines in 29 first-party legacy source files, and adds a secured native-window plus deterministic one-file Windows executable path over the same current core.
- PASS-018 adds a process-local request token, same-origin checks, a ten-minute one-time authorization, allowlisted one-file intake, bounded exact-length streaming, SHA-256 proof, atomic app-owned quarantine storage, rollback, and the reviewed browser/native workbench flow.
- PASS-019 migrates the prior app's strongest capability-lane, contextual-help, event-history, settings, and restrained-motion ideas into focused current modules. The matrix derives from existing contracts, preferences use portable app-owned settings, activity is fixed/redacted/create-only, and all route/tool/output/software actions remain blocked.
- PASS-020 enables one deliberately partial route stage: an explicitly authorized app-owned STL is streamed through a built-in structural preflight with exact size/hash checks, one concurrency slot, cooperative cancellation, fixed append-only audit events, a report, execution log, and hashed output proof. It starts no external command/process/tool, creates no toolpath or G-code, opens no output, and does not claim full mesh-to-toolpath completion.

## Blocked Or Not Proven

- Full route execution beyond the built-in STL preflight.
- Toolpath and G-code output creation.
- Output open actions.
- Proof capture beyond the contained STL preflight.
- External tool launch.
- Tool version proof.
- Runnable tool command construction.
- Execution request persistence.
- Execution authorization beyond the contained STL preflight.
- Process cancellation signaling and stop proof.
- External-process execution logging.
- Selected-file handoff.
- Drag-and-drop or clipboard-paste intake.
- Archive upload, content-type verification, and malware scanning.
- Install, update, uninstall, or repair actions.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine setup proof.
- macOS, Linux, and browser-hosted runtime support.

## Next Pass

PASS-021 - backup, restore, update, uninstall, and repair dry-run lifecycle contracts.
