# Makers Anvil Implementation Guide

## Purpose

This guide is the durable code roadmap for a developer, student, reviewer, or AI model. It explains where behavior lives, how one request moves through the application, which safety rules must remain true, and how to extend the app without relying on private chat history.

Use this guide with `docs/START_HERE.md`, `docs/SOURCE_WALKTHROUGH.md`, `docs/LINE_BY_LINE_CODE_GUIDE.md`, `docs/PREVIOUS_APP_REFERENCE_STUDY.md`, the current status files, source-manifest entries, schemas, and tests. The repository is authoritative when this guide and code disagree; repair the stale guide in the same change.

## Application Shape

Makers Anvil is currently a local-first browser dashboard served by a small Python backend. The checked-in frontend has no compilation step. The backend serves static files, read APIs, and one bounded two-request intake mutation from loopback. Product data and runtime records belong in OS-standard user-data storage, not in the source checkout.

The same frontend/backend now has a native desktop delivery path. pywebview supplies the operating-system window, while PyInstaller bundles the Python core and static frontend for Windows. This is a delivery adapter, not a second application implementation.

```text
Browser HTML/CSS/JavaScript
  -> GET request or exact intake authorization/content POST
  -> RequestHandler in server.py
  -> MakersAnvilApi route table
  -> focused service
  -> committed policy plus private app-owned runtime records
  -> schema-shaped JSON
  -> JavaScript renderer
  -> visible dashboard region
```

The HTTP boundary accepts POST only for intake authorization metadata, its exact matching content stream, and one complete workbench-preference record. Every other non-GET API request is rejected. Local scripts retain separate bounded entrypoints, and every mutation delegates to a focused service that validates authorization, containment, and safety.

## Durable Truth Order

1. `docs/START_HERE.md` tells a new contributor what to read and run.
2. `state/current_status.json` states the current pass, percentages, proof, blockers, and next pass.
3. `state/pass_ledger.json` records completed passes in order.
4. `docs/BUILD_STATUS.md` explains the same truth for humans.
5. `docs/passes/PASS_NNN_REPORT.md` records one pass's exact evidence and non-goals.
6. `state/source_manifest.json` explains ownership and maintenance requirements for every tracked file.
7. `docs/SOURCE_WALKTHROUGH.md` connects each source file to its caller, contract, effect, and test.
8. `docs/PREVIOUS_APP_REFERENCE_STUDY.md` preserves accepted workbench design evidence without runtime coupling.
9. Schemas, tests, and implementation establish the actual behavioral contract.
10. `state/learning_coverage.json` and the generated line guide prove that every physical implementation and contract line has a current explanation.

Do not infer current truth from an old chat, commit message, screenshot, or historical pass report.

## Folder Ownership

| Folder | Responsibility | Must not contain |
| --- | --- | --- |
| `backend/` | Python HTTP, API, domain vocabulary, and focused services | Personal paths, frontend presentation, hidden install actions |
| `frontend/` | Accessible dashboard structure, rendering, and reviewed one-file selection | Filesystem paths, tool execution, policy decisions |
| `config/` | Portable committed policy and allowlists | Runtime records, secrets, personal directories |
| `schemas/` | Strict JSON contracts for config, state, and API records | Informal or unconstrained truth labels |
| `state/` | Current build truth, pass history, and source ownership | Runtime user data or chat-only claims |
| `scripts/` | Explicit local commands and verification entrypoints | Business rules that belong in services |
| `tests/` | Executable behavior and safety examples | Dependence on one user's machine state |
| `docs/` | Human-readable architecture, procedures, evidence, and learning paths | Claims unsupported by current tests or runtime proof |

The ignored previous application is governed through `docs/PREVIOUS_APP_MERGER_AUDIT.md` and `state/previous_app_migration.json`. Migrate one capability through the existing contract chain; never copy the legacy virtual environment, dependencies, generated output, runtime records, paths, or monoliths.

## Backend Layers

### Server

`backend/src/makers_anvil_backend/server.py` owns loopback serving, static-asset resolution, response encoding, bounded metadata reads, exact-length content streaming, browser security headers, and API delegation. It must prevent path traversal and CORS access, send no-store headers for API state, and centralize blocked mutation responses. It must not contain workflow business rules.

### API Facade

`backend/src/makers_anvil_backend/api/app.py` owns the read route table plus the two exact intake POST patterns. It normalizes method/path, enforces media types and declared content length, creates the request-context value, and returns explicit typed errors. It must not implement storage or authorization policy directly.

### App Composition

`backend/src/makers_anvil_backend/services/app_state.py` constructs services once and composes coherent snapshots. When one response combines intake, route, output, tool, and gate records, each later service receives the earlier snapshot so a single request cannot accidentally mix different observations.

### Focused Services

| Service | Input | Output | Safety boundary |
| --- | --- | --- | --- |
| `WorkspaceStatusService` | committed state JSON | current status and ledger | read only |
| `RuntimePathsService` | platform and optional absolute override | private resolved root plus public redacted record | never expose personal resolved paths |
| `WorkspaceConfigService` | settings policy | validated config and app-owned layout | directories remain contained under one runtime root |
| `IntakeCatalogService` | intake policy and private runtime records | validated legacy and authorized-copy catalog | never expose source paths or weaken downstream safety |
| `AuthorizedIntakeService` | reviewed metadata, same-origin token context, and exact byte stream | one-time authorization plus hashed quarantine record | generated destinations, bounded chunks, atomic publish, rollback, no source modification |
| `RoutePreviewService` | validated intake snapshot | deterministic route candidates | never reopen or execute source files |
| `OutputProofService` | route snapshot and workspace policy | logical artifact/proof plan | never create or open outputs |
| `ToolDetectionService` | tool catalog and platform environment | path-redacted presence evidence | never execute version/tool commands |
| `ToolDryRunService` | route, output, and detection snapshots | semantic non-runnable plans | no command strings or file handoff |
| `ExecutionGateService` | dry-run snapshot and gate policy | planning evidence and blocked operational gates | no authorization or process behavior |
| `ExecutionRequestService` | coherent dry-run and gate snapshots | logical intent, consent fields, and audit plan | no persistence, accepted consent, or process behavior |
| `JobWorkspaceService` | request preview plus app-owned job policy | prepared job and cancellation records | no private paths, authorization, commands, process signals, or output artifacts |

## Contract Chain

Every capability follows this sequence:

1. A config file defines allowed scope and constant safety values.
2. A config schema rejects missing, extra, malformed, or broadened policy fields.
3. A focused service validates policy again at the behavioral boundary.
4. An API schema constrains the public result.
5. `AppStateService` composes the result without weakening it.
6. `MakersAnvilApi` exposes a read route or the smallest explicitly authorized mutation route.
7. Frontend HTML provides a labeled region.
8. Frontend JavaScript renders untrusted text with `textContent` or equivalent safe node creation.
9. CSS gives the region stable responsive dimensions.
10. Tests prove happy paths, malformed policy rejection, privacy, and disabled actions.
11. `scripts/verify_project.py` validates cross-file invariants and schemas.
12. `scripts/build_learning_guide.py` regenerates exact numbered explanations after the final covered source change.
13. Status, architecture, roadmap, pass report, and source manifest are updated together.

Skipping a link makes a capability incomplete even if one isolated file works.

## Frontend Flow

`frontend/public/index.html` declares the rail, top command bar, source deck, reviewed intake controls, tool inventory, stable command deck, output-proof inspector, and Dev evidence regions. `frontend/public/assets/app.js` performs state GETs plus exactly two same-origin intake POSTs, renders each contract, and handles local-only navigation. `frontend/public/assets/styles.css` keeps the desktop workbench inside one viewport and restores normal document flow below 900px.

Frontend rules:

- Treat every API string as untrusted display data.
- Use text nodes rather than HTML string interpolation.
- Show claim states and blockers exactly; do not convert staged or preview-only work into a success claim.
- Enable a control only for the exact proven mutation scope. Intake authorization does not enable route, tool, output, archive, folder, software, or release actions.
- Keep the selected `File` and process token in memory only; never render, persist, or submit a source filesystem path.
- Keep rendering functions focused on one contract so schema changes have an obvious update location.
- Keep Work Flow, Plans, and Dev inside one stable command-deck footprint on desktop.
- Put normal maker tasks before raw implementation evidence; Dev retains the complete proof surface.

## How To Add A Read-Only Capability

1. Define the narrow scope and explicit non-goals in the pass report.
2. Add committed policy under `config/` if behavior is configurable.
3. Add strict policy and response schemas under `schemas/`.
4. Implement one focused service with module/component docstrings and reasoning comments around safety decisions.
5. Add isolated service tests, including malformed or broadened policy cases.
6. Inject the service into `AppStateService` and reuse coherent snapshots.
7. Add a named GET route in `MakersAnvilApi`.
8. Add the state field to `schemas/app-state.schema.json`.
9. Add a semantic HTML region and a JSDoc-documented renderer.
10. Add responsive CSS and browser proof at desktop and mobile sizes.
11. Update verifier invariants and the project-purity scan.
12. Update all durable truth and source-manifest entries.

## How To Add A Mutation

A mutation is not a read-only feature with a button added. Before one is enabled, the same pass must prove every gate relevant to that mutation:

- explicit user intent and authorization;
- allowlisted operation and bounded input;
- source and output containment;
- destination naming and atomic/transactional behavior;
- replay, expiry, partial-failure, and rollback behavior;
- origin, token, media-type, and size enforcement when HTTP is involved;
- command, process, concurrency, cancellation, audit, and output proof when execution is involved;
- restart/recovery behavior when state must survive a process;
- negative tests and visible browser state.

Until operation-specific gates pass, policy, API, service, and UI values must keep that mutation disabled. PASS-018 satisfies app-owned intake copy gates and PASS-019 adds presentation preferences plus fixed redacted activity; execution gates remain false.

## Portability Rules

- Resolve the repository root from the executing file, never from the caller's current directory.
- Store runtime data under an OS-standard user-data root or an explicit absolute override.
- Never check in a username, drive-specific home path, cloud-sync path, or expected installation directory.
- Public API records may expose logical IDs and relative app-owned paths, not resolved personal paths.
- Tests must use temporary directories and relocated copies where path independence matters.
- Windows is the current product target; macOS/Linux CI is compatibility evidence, not full runtime or packaging proof.

## Debugging Order

1. Read the current pass and blockers.
2. Reproduce with the smallest focused test.
3. Inspect the responsible config and schema.
4. Inspect the focused service and its injected dependencies.
5. Call the exact endpoint directly with isolated runtime data; for intake, test authorization and content as one pair.
6. Inspect browser console/network/rendering only after the API record is correct.
7. Run explainability, project verification, and the full test suite.
8. Regenerate and check the line guide.
9. Update durable records if the observed truth changed.

## Completion Definition

A pass is complete only when implementation, schemas, tests, verifier, visible runtime proof, explanations, durable status, commit, push, and CI all agree. Anything not directly observed is reported as blocked, planned, staged, preview-only, detected, or not proven using the closed claim-state vocabulary.
