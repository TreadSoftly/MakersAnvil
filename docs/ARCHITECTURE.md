# Makers Anvil Architecture

## Product Shape

Makers Anvil is a local-first control panel for maker workflows. The browser dashboard reads JSON state from a loopback Python server and may perform one bounded mutation: an explicitly authorized copy of one reviewed file into private app-owned quarantine storage. Every route, tool, output, archive, folder, software, and release action remains gated.

## Experience Direction

The implemented application shell is a preview-first maker workbench: left navigation rail, compact command/header area, source intake, selected-input preview, tool context, work plans/workflow, latest output proof, and a synchronized preview/proof inspector. `docs/PREVIOUS_APP_REFERENCE_STUDY.md` records the evidence and responsive expectations. It informs presentation and workflow only; the ignored prototype is never imported or required.

Beginner-facing labels use source files, work plans, workflow, preview, tools, output, and proof. Internal route identifiers remain stable contract vocabulary. Planned, blocked, and not-proven state must remain visually and semantically distinct from completed proof.

## Major Layers

### Browser UI

`frontend/` contains the promoted React/TypeScript application, reviewed tool icons, accepted industrial styling, and Vite build. `frontend/src/api.ts` maps current path-redacted backend records into the workbench and permits only guarded one-file intake plus the contained STL preflight. Picker, drop, and paste share that intake path. Rail navigation, quick-jump search, tool carousel, and Work Flow/Plans/Dev tabs preserve the accepted previous-app experience without importing its Python backend or private paths.

### HTTP Boundary

`backend/src/makers_anvil_backend/server.py` serves static files and delegates `/api/*` requests to `MakersAnvilApi`. It listens on loopback, emits restrictive browser security headers, refuses CORS preflight, bounds authorization JSON, and streams content by exact declared length. Every POST except the two intake routes returns `405`.

### API Facade

`backend/src/makers_anvil_backend/api/app.py` maps stable reads and the exact intake authorization/content routes to service methods. It owns status codes, media-type checks, request-context translation, and typed error records; filesystem and authorization rules remain in focused services.

### Services

- `AppStateService` composes the dashboard state from smaller services.
- `WorkspaceStatusService` reads committed status and pass-ledger truth.
- `RuntimePathsService` resolves OS-standard per-user data locations without exposing personal paths.
- `WorkspaceConfigService` validates settings and creates contained app-owned directories.
- `IntakeCatalogService` validates legacy metadata records and authorized app-owned copy records without exposing source paths.
- `AuthorizedIntakeService` verifies same-origin process tokens, creates one-time short-lived consent records, streams exact bytes in bounded chunks, hashes content, atomically publishes a generated-name quarantine copy, and rolls back failed transfers.
- `RoutePreviewService` maps validated intake metadata to deterministic candidate steps without reopening files or enabling actions.
- `OutputProofService` maps route previews to expected artifacts and required evidence without creating, opening, or proving outputs.
- `ToolDetectionService` checks PATH and narrow platform locations while withholding resolved paths and executing nothing.
- `ToolDryRunService` joins route, output, and tool evidence into semantic invocation plans without constructing commands, resolving paths, handing off files, or executing processes.
- `ExecutionGateService` evaluates ten required evidence classes for one allowlisted route while authorization and execution remain disabled.
- `ExecutionRequestService` joins coherent dry-run and gate snapshots into path-free intent, unaccepted authorization fields, and an empty audit plan without persistence.
- `JobWorkspaceService` creates deterministic app-owned prepared workspaces and cancellation-request records through explicit local scripts while processes remain impossible.
- `ContainedExecutionService` runs only the explicitly authorized built-in STL structural preflight and records cancellation, audit, report, log, and proof evidence.
- `ExecutionAuditService` creates fixed-vocabulary immutable ordered events for contained preflight lifecycles.
- `LifecycleDryRunService` inventories bounded app-owned metadata and models backup, restore, update, uninstall, and repair while every lifecycle effect remains false.

### Schemas And Durable State

`schemas/` defines the intended JSON contracts. `config/` contains safe defaults. `state/` contains committed machine-readable build truth and the complete source manifest. These files are code contracts, not informal notes.

### Scripts And Tests

`scripts/` contains explicit local entrypoints for running, initializing, staging metadata, checking explainability, and verifying the project. `tests/` provides executable examples of API behavior, containment, privacy, portability, and governance.

### Desktop Delivery

`desktop.py` owns an ephemeral loopback server and a native pywebview window over the same frontend/API used in browser development. `runtime_resources.py` resolves source or PyInstaller-bundled static assets. `scripts/build_windows_exe.py` owns the deterministic one-file Windows plan. No separate desktop frontend or legacy backend exists.

Desktop startup accepts no path, URL, tool, command, or authorization argument. It disables direct JavaScript bridging, downloads, file URLs, automatic devtools, and remote debugging. Closing the window shuts down the owned server. See `docs/DESKTOP_ARCHITECTURE.md` for upstream citations and packaging boundaries.

## Read Flow

```text
Browser
  -> GET /api/state and supporting GET endpoints
  -> MakersAnvilApi
  -> AppStateService and focused services
  -> committed config/state plus app-owned runtime metadata
  -> RoutePreviewService derives non-executing candidate steps
  -> OutputProofService derives non-writing bundle and proof plans
  -> ToolDetectionService derives path-redacted presence evidence
  -> ToolDryRunService derives semantic, non-runnable invocation plans
  -> ExecutionGateService separates satisfied planning evidence from blocked operational gates
  -> ExecutionRequestService models logical intent, required consent, and required audit events without saving them
  -> JobWorkspaceService reads path-redacted prepared jobs and unsignaled cancellation requests
  -> LifecycleDryRunService counts app-owned metadata and derives five non-executable lifecycle plans
  -> JSON response
  -> browser render
```

## Authorized Intake Flow

```text
Human chooses one regular file
  -> browser displays name, classified kind, and size for review
  -> human selects Authorize copy
  -> POST metadata with same-origin process token
  -> service validates origin, token, suffix, kind, size, timestamp, and policy
  -> service creates a ten-minute one-time authorization without a source path
  -> POST exact bytes to that authorization
  -> service streams bounded chunks, verifies exact length, and computes SHA-256
  -> atomic replacement publishes an app-generated quarantine file
  -> strict path-redacted record enters the intake catalog
```

The browser never submits a filesystem path. Failed or incomplete streams remove partial content and catalog state. A successful or expired authorization cannot be replayed. Content-type verification and malware scanning are not yet proven, so no intake record becomes execution-ready or eligible for direct tool handoff.

## Explicit Mutation Flow

```text
Human invokes a local script
  -> script validates one narrow request
  -> service applies containment and safety rules
  -> app-owned user-data record is written
  -> source file remains unchanged
```

PASS-013 adds two bounded examples of this flow: job preparation creates empty app-owned directories and logical records, while cancellation recording changes only an app-owned control file. Neither action accepts authorization, resolves a user file, constructs a command, starts or signals a process, writes an output artifact, appends an audit event, or captures proof.

## Trust And Safety Boundaries

- User files are untrusted inputs.
- The browser may read one explicitly authorized file to create an app-owned copy; the selected source is never moved, deleted, renamed, path-exposed, extracted, executed, or handed to a tool.
- Authorization is process-local, same-origin, short-lived, one-file, exact-metadata, exact-length, and one-time.
- Runtime records live in OS user-data storage or an explicit absolute override, never beside the source checkout.
- Resolved source and home paths are not returned by APIs.
- Route execution, external tool launch, installers, archive extraction, folder import, packaging, and clean-machine claims remain blocked until separate proof gates pass.
- Lifecycle previews read only bounded metadata, preserve app data, exclude backup/tmp sources, and cannot create/read archives, restore, use the network, download packages, execute installers, mutate software, start processes, or delete data.
- The Windows installer foundation is a separate read-only layer over the executable payload. It selects MSIX, requires a stable identity and trusted signature, preserves portable user data across upgrade/removal, and exposes nine gates without building or registering a package.
- Clean-machine proof is a six-scenario harness, not a label. Fresh install, first launch, upgrade, repair, removal, and reinstall each remain `not-run` with empty evidence until executed in an isolated Windows environment.

## How To Extend The App

1. Add or change a focused domain/service contract rather than expanding one monolithic file.
2. Add a schema for new structured records.
3. Add service tests before enabling an action.
4. Expose read-only preview state before adding mutation.
5. Add UI rendering after the API shape is stable.
6. Update architecture, source manifest, status, pass report, and verifier gates in the same pass.

Route, output/proof, tool-presence, dry-run, execution-gate, execution-request, lifecycle, installer, and clean-machine records are read-only planning evidence. Intake authorization permits only an app-owned quarantine copy. Contained execution authorization applies only to the built-in STL structural preflight. Prepared jobs, lifecycle plans, installer gates, and machine scenarios remain non-executable.
