# Makers Anvil Implementation Guide

## Purpose

This guide is the durable code roadmap for a developer, student, reviewer, or AI model. It explains where behavior lives, how one request moves through the application, which safety rules must remain true, and how to extend the app without relying on private chat history.

Use this guide with `docs/START_HERE.md`, the current status files, source-manifest entries, schemas, and tests. The repository is authoritative when this guide and code disagree; repair the stale guide in the same change.

## Application Shape

Makers Anvil is currently a local-first browser dashboard served by a small Python backend. The checked-in frontend has no compilation step. The backend serves static files and read-only JSON APIs from loopback. Product data and runtime records belong in OS-standard user-data storage, not in the source checkout.

```text
Browser HTML/CSS/JavaScript
  -> GET request
  -> RequestHandler in server.py
  -> MakersAnvilApi route table
  -> focused service
  -> committed policy plus private app-owned runtime records
  -> schema-shaped JSON
  -> JavaScript renderer
  -> visible dashboard region
```

The current HTTP boundary rejects every non-GET API request. Local scripts are the only bounded mutation entrypoints, and each script must delegate to a service that validates containment and safety.

## Durable Truth Order

1. `docs/START_HERE.md` tells a new contributor what to read and run.
2. `state/current_status.json` states the current pass, percentages, proof, blockers, and next pass.
3. `state/pass_ledger.json` records completed passes in order.
4. `docs/BUILD_STATUS.md` explains the same truth for humans.
5. `docs/passes/PASS_NNN_REPORT.md` records one pass's exact evidence and non-goals.
6. `state/source_manifest.json` explains ownership and maintenance requirements for every tracked file.
7. Schemas, tests, and implementation establish the actual behavioral contract.

Do not infer current truth from an old chat, commit message, screenshot, or historical pass report.

## Folder Ownership

| Folder | Responsibility | Must not contain |
| --- | --- | --- |
| `backend/` | Python HTTP, API, domain vocabulary, and focused services | Personal paths, frontend presentation, hidden install actions |
| `frontend/` | Accessible read-only dashboard structure, presentation, and rendering | Filesystem access, tool execution, trust decisions |
| `config/` | Portable committed policy and allowlists | Runtime records, secrets, personal directories |
| `schemas/` | Strict JSON contracts for config, state, and API records | Informal or unconstrained truth labels |
| `state/` | Current build truth, pass history, and source ownership | Runtime user data or chat-only claims |
| `scripts/` | Explicit local commands and verification entrypoints | Business rules that belong in services |
| `tests/` | Executable behavior and safety examples | Dependence on one user's machine state |
| `docs/` | Human-readable architecture, procedures, evidence, and learning paths | Claims unsupported by current tests or runtime proof |

## Backend Layers

### Server

`backend/src/makers_anvil_backend/server.py` owns loopback serving, static-asset resolution, response encoding, and API delegation. It must prevent path traversal, send no-store headers for API state, and centralize blocked mutation responses. It must not contain workflow business rules.

### API Facade

`backend/src/makers_anvil_backend/api/app.py` owns the read-only route table. Each path maps to one `AppStateService` method. The API facade normalizes the method and URL path and returns explicit `404` or `405` records. It must not read config or files directly.

### App Composition

`backend/src/makers_anvil_backend/services/app_state.py` constructs services once and composes coherent snapshots. When one response combines intake, route, output, tool, and gate records, each later service receives the earlier snapshot so a single request cannot accidentally mix different observations.

### Focused Services

| Service | Input | Output | Safety boundary |
| --- | --- | --- | --- |
| `WorkspaceStatusService` | committed state JSON | current status and ledger | read only |
| `RuntimePathsService` | platform and optional absolute override | private resolved root plus public redacted record | never expose personal resolved paths |
| `WorkspaceConfigService` | settings policy | validated config and app-owned layout | directories remain contained under one runtime root |
| `IntakeCatalogService` | intake policy and private runtime records | metadata-only catalog | never expose path/content or modify source |
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
6. `MakersAnvilApi` exposes a read-only route.
7. Frontend HTML provides a labeled region.
8. Frontend JavaScript renders untrusted text with `textContent` or equivalent safe node creation.
9. CSS gives the region stable responsive dimensions.
10. Tests prove happy paths, malformed policy rejection, privacy, and disabled actions.
11. `scripts/verify_project.py` validates cross-file invariants and schemas.
12. Status, architecture, roadmap, pass report, and source manifest are updated together.

Skipping a link makes a capability incomplete even if one isolated file works.

## Frontend Flow

`frontend/public/index.html` declares the dashboard regions. `frontend/public/assets/app.js` performs GET requests, creates DOM nodes, and renders each service contract. `frontend/public/assets/styles.css` owns layout and responsive behavior.

Frontend rules:

- Treat every API string as untrusted display data.
- Use text nodes rather than HTML string interpolation.
- Show claim states and blockers exactly; do not convert staged or preview-only work into a success claim.
- Do not render enabled action controls until a mutation endpoint and its authorization, cancellation, containment, logging, and proof gates are independently proven.
- Keep rendering functions focused on one contract so schema changes have an obvious update location.

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

A mutation is not a read-only feature with a button added. Before one is enabled, the same pass must prove:

- explicit user intent and authorization;
- allowlisted operation and bounded input;
- source and output containment;
- command and argument construction without shell injection;
- one-job concurrency policy;
- cancellation that reaches the owned process;
- append-only audit events with redaction;
- output evidence and failure reporting;
- restart/recovery behavior;
- negative tests and visible browser state.

Until all required gates pass, policy, API, service, and UI values must keep the mutation disabled.

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
5. Call the exact GET endpoint directly.
6. Inspect browser console/network/rendering only after the API record is correct.
7. Run explainability, project verification, and the full test suite.
8. Update durable records if the observed truth changed.

## Completion Definition

A pass is complete only when implementation, schemas, tests, verifier, visible runtime proof, explanations, durable status, commit, push, and CI all agree. Anything not directly observed is reported as blocked, planned, staged, preview-only, detected, or not proven using the closed claim-state vocabulary.
