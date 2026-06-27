# Source Walkthrough

## How To Read The Code

This guide connects the actual files, call order, data contracts, effects, and proof. Start with the file's structured header, then read each component docstring, then follow the related test named here. Open that file's anchor in `docs/LINE_BY_LINE_CODE_GUIDE.md` whenever you need a numbered explanation of every physical line. JSON cannot carry comments, so the generated line guide supplies its per-line teaching layer while its source-manifest entry, schema, service validation, and test explain ownership and behavior.

## One Browser Request

```text
frontend/public/index.html
  -> frontend/public/assets/app.js loadState()
  -> backend/src/makers_anvil_backend/server.py RequestHandler
  -> backend/src/makers_anvil_backend/api/app.py MakersAnvilApi.handle()
  -> backend/src/makers_anvil_backend/services/app_state.py
  -> focused service reads validated config/runtime state
  -> schema-shaped dictionary returns through API
  -> app.js renderer writes untrusted values with textContent
  -> styles.css lays the result out responsively
```

The browser performs GET requests only. Local scripts are separate, explicit mutation boundaries.

## Backend Package

| File | What it owns | Read next / proof |
| --- | --- | --- |
| `backend/src/makers_anvil_backend/__init__.py` | Package identity/version without startup effects. | `tests/test_api.py` |
| `backend/src/makers_anvil_backend/__main__.py` | Module-execution handoff to the server. | `server.py` |
| `backend/src/makers_anvil_backend/api/app.py` | Method/path routing, status codes, 404/405 behavior. | `tests/test_api.py` |
| `backend/src/makers_anvil_backend/domain/claim_state.py` | Closed proof-state vocabulary. | `schemas/claim-state.schema.json` |
| `backend/src/makers_anvil_backend/server.py` | Loopback HTTP, static containment, JSON encoding, cache headers. | API tests and runtime smoke |
| `backend/src/makers_anvil_backend/services/app_state.py` | Constructs services and composes one coherent dashboard snapshot. | `schemas/app-state.schema.json` |
| `backend/src/makers_anvil_backend/services/workspace_status.py` | Reads current status and pass history. | `state/*.json` |
| `backend/src/makers_anvil_backend/services/runtime_paths.py` | Separates private resolved paths from public logical location truth. | `tests/test_runtime_paths.py` |
| `backend/src/makers_anvil_backend/services/workspace_config.py` | Validates settings and creates contained app directories. | `tests/test_workspace_config.py` |
| `backend/src/makers_anvil_backend/services/intake_catalog.py` | Stages metadata only and lists privacy-safe records. | `tests/test_intake_catalog.py` |
| `backend/src/makers_anvil_backend/services/route_preview.py` | Maps intake kinds to non-executing work candidates. | `tests/test_route_preview.py` |
| `backend/src/makers_anvil_backend/services/output_proof.py` | Plans logical artifacts and required proof without writing output. | `tests/test_output_proof.py` |
| `backend/src/makers_anvil_backend/services/tool_detection.py` | Detects tool presence while withholding paths and avoiding processes. | `tests/test_tool_detection.py` |
| `backend/src/makers_anvil_backend/services/tool_dry_run.py` | Builds semantic plans with no runnable command or file handoff. | `tests/test_tool_dry_run.py` |
| `backend/src/makers_anvil_backend/services/execution_gate.py` | Evaluates planning and operational evidence for one route. | `tests/test_execution_gate.py` |
| `backend/src/makers_anvil_backend/services/execution_request.py` | Previews intent, unaccepted consent, and required audit lifecycle. | `tests/test_execution_request.py` |
| `backend/src/makers_anvil_backend/services/job_records.py` | Constructs strict path-redacted job/cancellation records. | `tests/test_job_workspace.py` |
| `backend/src/makers_anvil_backend/services/job_workspace.py` | Creates contained empty job structure and cancellation intent only. | `tests/test_job_workspace.py` |

Package-marker `__init__.py` files only establish namespaces. Their headers explicitly state that import has no side effects.

## Frontend

| File | What it owns | Important blocks |
| --- | --- | --- |
| `frontend/public/index.html` | Preview-first workbench structure and accessible loading state. | Rail -> command bar -> source deck -> tools -> command deck -> proof inspector -> Dev evidence. |
| `frontend/public/assets/app.js` | GET-only fetch, safe rendering, selected/expected summaries, and local view navigation. | Endpoints -> fallback -> renderers -> workbench summary -> controls -> `renderState` -> `loadState`. |
| `frontend/public/assets/styles.css` | Industrial tokens, one-viewport desktop geometry, stable tabs, local scrolling, and mobile flow. | Tokens -> shell -> rail/topbar -> zones -> command deck -> inspector -> responsive rules. |
| `frontend/public/assets/mark.svg` | Embedded product identity with no remote or script dependency. | Accessible SVG geometry. |

All values originating outside the static page must be written with DOM text APIs. A renderer must never convert a planned or missing value into a ready action. The disabled Add files affordance is visual workflow context only; no file input or form exists.

## Explicit Local Commands

| File | Human action | Allowed effect |
| --- | --- | --- |
| `scripts/run_dev.py` | Start local dashboard. | Opens loopback server process. |
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
- Intake policy and records.
- Route catalog and previews.
- Output policy and proof plans.
- Tool catalog, detection, and semantic dry runs.
- Execution gate policy/evaluations.
- Execution request policy/previews.
- Job workspace policy, prepared jobs, cancellations, and catalogs.
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
