# Makers Anvil Architecture

## Product Shape

Makers Anvil is a local-first control panel for maker workflows. The current application is intentionally small and read-only while safety gates are built. The browser dashboard reads JSON state from a loopback Python server. Explicit local scripts may create app-owned runtime records, but the HTTP API cannot mutate state.

## Major Layers

### Browser UI

`frontend/public/` contains static HTML, CSS, JavaScript, and the product mark. The browser calls only `GET` endpoints. It renders current completion, workspace state, portable runtime-location policy, intake status, capabilities, and blocked actions.

### HTTP Boundary

`backend/src/makers_anvil_backend/server.py` serves static files and delegates `/api/*` requests to `MakersAnvilApi`. The server listens on loopback by default. Every non-GET API request returns a blocked `405` response.

### API Facade

`backend/src/makers_anvil_backend/api/app.py` maps stable read-only routes to service methods. It owns HTTP-like status codes and error records, but it does not own filesystem rules or business state.

### Services

- `AppStateService` composes the dashboard state from smaller services.
- `WorkspaceStatusService` reads committed status and pass-ledger truth.
- `RuntimePathsService` resolves OS-standard per-user data locations without exposing personal paths.
- `WorkspaceConfigService` validates settings and creates contained app-owned directories.
- `IntakeCatalogService` records metadata for one explicit regular file without storing its path or contents.

### Schemas And Durable State

`schemas/` defines the intended JSON contracts. `config/` contains safe defaults. `state/` contains committed machine-readable build truth and the complete source manifest. These files are code contracts, not informal notes.

### Scripts And Tests

`scripts/` contains explicit local entrypoints for running, initializing, staging metadata, checking explainability, and verifying the project. `tests/` provides executable examples of API behavior, containment, privacy, portability, and governance.

## Read Flow

```text
Browser
  -> GET /api/state and supporting GET endpoints
  -> MakersAnvilApi
  -> AppStateService and focused services
  -> committed config/state plus app-owned runtime metadata
  -> JSON response
  -> browser render
```

## Explicit Mutation Flow

```text
Human invokes a local script
  -> script validates one narrow request
  -> service applies containment and safety rules
  -> app-owned user-data record is written
  -> source file remains unchanged
```

The browser and HTTP API do not participate in this mutation flow yet.

## Trust And Safety Boundaries

- User files are untrusted inputs.
- Source files are never copied, moved, deleted, extracted, executed, or handed to tools by current intake code.
- Runtime records live in OS user-data storage or an explicit absolute override, never beside the source checkout.
- Resolved source and home paths are not returned by APIs.
- Route execution, external tool launch, installers, archive extraction, folder import, packaging, and clean-machine claims remain blocked until separate proof gates pass.

## How To Extend The App

1. Add or change a focused domain/service contract rather than expanding one monolithic file.
2. Add a schema for new structured records.
3. Add service tests before enabling an action.
4. Expose read-only preview state before adding mutation.
5. Add UI rendering after the API shape is stable.
6. Update architecture, source manifest, status, pass report, and verifier gates in the same pass.

The next planned capability is route preview. Preview must remain non-executing and must consume metadata records rather than reopening or launching source files.
