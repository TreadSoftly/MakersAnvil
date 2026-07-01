# Source Walkthrough

## How To Read The Code

This guide connects the actual files, call order, data contracts, effects, and proof. Start with the file's structured header, then read each component docstring, then follow the related test named here. Open that file's anchor in `docs/LINE_BY_LINE_CODE_GUIDE.md` whenever you need a numbered explanation of every physical line. JSON cannot carry comments, so the generated line guide supplies its per-line teaching layer while its source-manifest entry, schema, service validation, and test explain ownership and behavior.

## One Browser Request

```text
frontend/index.html
  -> frontend/src/main.tsx mounts App
  -> frontend/src/App.tsx calls getState()
  -> frontend/src/api.ts fetches /api/state
  -> backend/src/makers_anvil_backend/server.py RequestHandler
  -> backend/src/makers_anvil_backend/api/app.py MakersAnvilApi.handle()
  -> backend/src/makers_anvil_backend/services/app_state.py
  -> focused service reads validated config/runtime state
  -> schema-shaped dictionary returns through API
  -> api.ts maps path-redacted records into the promoted view contract
  -> React escapes text values while App.tsx renders the workbench
  -> frontend/src/styles.css lays the result out responsively
```

The browser performs state GETs plus the closed guarded intake, preference, and contained-STL-preflight mutations. Lifecycle planning performs GET requests only and creates no command control. Local scripts remain separate mutation boundaries.

For intake, follow picker/drop/paste -> `App.handleFilesUpload()` -> `api.uploadFiles()` -> `MakersAnvilApi` -> `AuthorizedIntakeService.authorize()` -> `AuthorizedIntakeService.ingest()`. The first POST creates path-free short-lived consent; the second streams, hashes, atomically publishes, and catalogs one generated-name app-owned copy.

## Backend Package

| File | What it owns | Read next / proof |
| --- | --- | --- |
| `backend/src/makers_anvil_backend/__init__.py` | Package identity/version without startup effects. | `tests/test_api.py` |
| `backend/src/makers_anvil_backend/__main__.py` | Module-execution handoff to the server. | `server.py` |
| `backend/src/makers_anvil_backend/api/app.py` | Read routing, guarded intake/preferences POST dispatch, media checks, status codes, and 404/405 behavior. | `tests/test_api.py`, `tests/test_authorized_intake.py` |
| `backend/src/makers_anvil_backend/domain/claim_state.py` | Closed proof-state vocabulary. | `schemas/claim-state.schema.json` |
| `backend/src/makers_anvil_backend/server.py` | Loopback HTTP, static containment, security headers, bounded JSON, exact content streaming, and response encoding. | `tests/test_server.py` and runtime smoke |
| `backend/src/makers_anvil_backend/runtime_resources.py` | Source/PyInstaller resource resolution without fixed paths. | `tests/test_runtime_resources.py` |
| `backend/src/makers_anvil_backend/desktop.py` | Native window, ephemeral server ownership, shutdown, and binary smoke. | `tests/test_desktop.py` |
| `backend/src/makers_anvil_backend/services/app_state.py` | Constructs services and composes one coherent dashboard snapshot. | `schemas/app-state.schema.json` |
| `backend/src/makers_anvil_backend/services/activity_log.py` | Creates and reads fixed redacted immutable completion events under portable user data. | `tests/test_workbench_experience.py`, activity schemas |
| `backend/src/makers_anvil_backend/services/capability_matrix.py` | Joins current intake, route, output, and tool snapshots into five nonexecuting lanes. | `tests/test_capability_matrix.py`, matrix schema |
| `backend/src/makers_anvil_backend/services/local_request_guard.py` | Applies one process token and exact same-origin loopback rules to bounded mutations. | `tests/test_local_request_guard.py` |
| `backend/src/makers_anvil_backend/services/workbench_experience.py` | Validates help policy and atomically stores three portable presentation preferences. | `tests/test_workbench_experience.py`, experience schemas |
| `backend/src/makers_anvil_backend/services/workspace_status.py` | Reads current status and pass history. | `state/*.json` |
| `backend/src/makers_anvil_backend/services/runtime_paths.py` | Separates private resolved paths from public logical location truth. | `tests/test_runtime_paths.py` |
| `backend/src/makers_anvil_backend/services/workspace_config.py` | Validates settings and creates contained app directories. | `tests/test_workspace_config.py` |
| `backend/src/makers_anvil_backend/services/authorized_intake.py` | Validates one-time consent and creates one hashed app-owned quarantine copy transactionally. | `tests/test_authorized_intake.py` |
| `backend/src/makers_anvil_backend/services/intake_catalog.py` | Stores and validates legacy metadata plus path-redacted authorized-copy records. | `tests/test_intake_catalog.py` |
| `backend/src/makers_anvil_backend/services/route_preview.py` | Maps intake kinds to non-executing work candidates. | `tests/test_route_preview.py` |
| `backend/src/makers_anvil_backend/services/output_proof.py` | Plans logical artifacts and required proof without writing output. | `tests/test_output_proof.py` |
| `backend/src/makers_anvil_backend/services/tool_detection.py` | Detects tool presence while withholding paths and avoiding processes. | `tests/test_tool_detection.py` |
| `backend/src/makers_anvil_backend/services/tool_dry_run.py` | Builds semantic plans with no runnable command or file handoff. | `tests/test_tool_dry_run.py` |
| `backend/src/makers_anvil_backend/services/execution_gate.py` | Evaluates planning and operational evidence for one route. | `tests/test_execution_gate.py` |
| `backend/src/makers_anvil_backend/services/execution_request.py` | Previews intent, unaccepted consent, and required audit lifecycle. | `tests/test_execution_request.py` |
| `backend/src/makers_anvil_backend/services/job_records.py` | Constructs strict path-redacted job/cancellation records. | `tests/test_job_workspace.py` |
| `backend/src/makers_anvil_backend/services/job_workspace.py` | Creates contained empty job structure and cancellation intent only. | `tests/test_job_workspace.py` |
| `backend/src/makers_anvil_backend/services/contained_execution.py` | Runs one authorized built-in STL structural preflight with cooperative cancellation and real proof artifacts. | `tests/test_contained_execution.py` |
| `backend/src/makers_anvil_backend/services/execution_audit.py` | Creates strict immutable lifecycle events for contained preflight. | `tests/test_contained_execution.py` and audit schemas |
| `backend/src/makers_anvil_backend/services/lifecycle_dry_run.py` | Counts bounded app-owned metadata and composes five preservation-first non-executable lifecycle plans. | `tests/test_lifecycle_dry_run.py` and lifecycle schemas |
| `backend/src/makers_anvil_backend/services/windows_installer.py` | Validates MSIX foundation policy, nine release gates, and six unexecuted clean-machine scenarios. | `tests/test_windows_installer.py` and installer schemas |

Package-marker `__init__.py` files only establish namespaces. Their headers explicitly state that import has no side effects.

## Frontend

| File | What it owns | Important blocks |
| --- | --- | --- |
| `frontend/index.html` | Minimal trusted React mount document and local product identity metadata. | One root -> module entry -> local favicon/manifest. |
| `frontend/src/main.tsx` | Creates the one StrictMode React tree. | Root lookup -> App mount -> shared styles. |
| `frontend/src/App.tsx` | Promoted rail, command search, source board, tool carousel, workflows, plans, proof, help, and settings. | State/actions -> workbench regions -> component helpers -> presentation helpers. |
| `frontend/src/api.ts` | Current-state adaptation, guarded intake, contained preflight, activity reads, and explicit blockers. | JSON guard -> adapters -> reads -> allowed mutations -> blocked legacy actions. |
| `frontend/src/components/ContextHelp.tsx` | Accessible viewport-contained help dialog with Escape close and focus restoration. | Position -> listeners -> dialog portal. |
| `frontend/src/components/ModeTabs.tsx` | Keyboard-operable Work Flow, Plans, and Dev selection. | ARIA tabs -> arrow/Home/End movement -> tab panels. |
| `frontend/src/components/StatusPill.tsx` | Conservative status-to-tone presentation that retains original text. | Normalize -> choose tone -> render. |
| `frontend/src/styles.css` | Accepted industrial tokens, animation, desktop geometry, and mobile flow. | Tokens -> shell -> zones -> dialogs -> motion -> responsive/reduced-motion rules. |
| `frontend/src/App.test.tsx` | Twenty retained interaction and portable-safety examples. | Fixture -> API mocks -> workflow assertions -> blocker assertions. |

React escapes values originating outside the document. A renderer must never convert planned route/tool/output state into a ready action. Picker, drop, and paste retain one `File` object only in browser memory and submit metadata plus exact bytes through the same authorization; they never submit a source path. Folders, archives, and multi-file intake remain absent.

## Explicit Local Commands

| File | Human action | Allowed effect |
| --- | --- | --- |
| `scripts/run_dev.py` | Start local dashboard. | Opens loopback server process. |
| `scripts/run_desktop.py` | Start native desktop app or package smoke. | Owns one window/session; accepts no path or command. |
| `scripts/build_windows_exe.py` | Inspect/build Windows one-file artifact. | Writes ignored build/artifact trees only in build mode. |
| `scripts/check_clean_machine.py` | Inspect the clean-machine scenario registry. | Reads policy and prints six not-run scenarios; has no execution mode. |
| `scripts/build_previous_app_learning_guide.py` | Explain selected old-app first-party lines. | Writes two ignored guide artifacts; never edits source. |
| `scripts/init_workspace.py` | Initialize app data. | Creates allowlisted app-owned directories. |
| `scripts/stage_intake.py` | Stage one file. | Writes metadata record only. |
| `scripts/prepare_job.py` | Prepare one request preview. | Creates empty contained job folders and records. |
| `scripts/request_job_cancel.py` | Request cancellation. | Writes intent; sends no process signal. |
| `scripts/check_explainability.py` | Audit source explanations. | Reads source and prints JSON result. |
| `scripts/build_learning_guide.py` | Generate or check every-line teaching coverage. | Writes only the committed guide and coverage record unless `--check` is used. |
| `scripts/verify_project.py` | Run all repository gates. | Reads source and uses isolated temporary data. |

Each command parses only its documented arguments and delegates behavior to a service. Business rules do not belong in argument parsing.

## Config And Schemas

`config/*.json` defines committed allowlists and constant safety flags. The matching `schemas/*.schema.json` constrains structure. The focused service validates semantic cross-field rules that JSON Schema cannot fully express. Tests then try both valid and deliberately weakened policies.

Contract families are:

- Local settings and runtime location.
- Intake policy, session, one-time authorization, legacy metadata record, and authorized-copy record.
- Route catalog and previews.
- Output policy and proof plans.
- Tool catalog, detection, and semantic dry runs.
- Execution gate policy/evaluations.
- Execution request policy/previews.
- Job workspace policy, prepared jobs, cancellations, and catalogs.
- Contained execution policy, records, cancellation, audit, report, proof, and catalog.
- Lifecycle dry-run policy, bounded inventory, bundled-core evidence, operation plans, and catalog.
- Windows installer policy/readiness plus declarative clean-machine scenario/harness contracts.
- Current status, pass ledger, app state, and source manifest.

## Tests

Every test module header explains its scope and every test function docstring names the behavior it proves. Read the test matching a service before changing that service. `tests/test_project_purity.py` protects cross-cutting portability/reference rules; `tests/test_explainability.py` protects this learning layer; `tests/test_verify_project.py` proves the canonical verifier remains green.

## Durable State And Documentation

- `state/current_status.json`: current percentages, proof, blockers, and next pass.
- `state/pass_ledger.json`: append-only pass history.
- `state/source_manifest.json`: purpose and maintenance contract for every tracked file.
- `state/learning_coverage.json`: exact source hashes, physical-line totals, explanation totals, and guide anchors.
- `docs/LINE_BY_LINE_CODE_GUIDE.md`: generated numbered source and explanations for every covered line.
- `docs/ARCHITECTURE.md`: layer ownership and trust boundaries.
- `docs/IMPLEMENTATION_GUIDE.md`: extension and debugging recipes.
- `docs/PREVIOUS_APP_REFERENCE_STUDY.md`: governed design direction from the old prototype.
- `docs/passes/PASS_NNN_REPORT.md`: exact evidence for one bounded pass.

When a file changes responsibility, update its header, component/block explanations, tests, this walkthrough if the call path changed, architecture, source manifest, and pass evidence together.
