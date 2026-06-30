# PASS-019 Report - Modular Previous-App Capability, Help, Event, And Settings Migration

## Scope

- Migrated the previous app's useful capability-lane, contextual-help, event-history, settings, notice, and restrained-motion ideas into the current application.
- Rebuilt those ideas as focused backend/frontend modules over existing schemas and portable user-data services.
- Kept the previous application optional and ignored; no legacy source, dependency tree, generated output, private path, runtime log, or process behavior became product runtime.

## Implemented

- `LocalRequestGuard` now supplies one process token and one exact same-origin loopback rule to both authorized intake and preference persistence.
- `WorkbenchExperienceService` validates six contextual-help topics and atomically persists compact/comfortable density, full/reduced motion, and help visibility.
- `ActivityLogService` writes only three fixed server-authored completion event types as create-only redacted JSON under app-owned user data.
- `CapabilityMatrixService` derives five lanes from current intake, route, output, and tool contracts; every lane keeps execution readiness false.
- Focused JavaScript modules render capability comparison, an accessible help dialog, preferences, notices, and recent activity with safe DOM text.
- Strict policy, runtime, API, activity, matrix, and app-state schemas protect the new contracts.

## Explanation And Learning

- Every new Python class/function/method and JavaScript function carries the nine required purpose/input/output/mechanism/effect/failure/safety/example/proof fields.
- Every new semantic HTML region and CSS rule has nearby teaching context.
- `docs/LINE_BY_LINE_CODE_GUIDE.md` and `state/learning_coverage.json` explain and hash every selected physical source line.
- `docs/LEARNING_RESOURCES.md` maps the implementation to Python `os.replace`, Fetch Metadata, WAI-ARIA dialog guidance, and reduced-motion documentation.

## Safety Boundary

- Enabled mutations: one explicitly authorized app-owned file copy and one complete guarded presentation-preference update.
- Still blocked: selected-file handoff, route execution, command construction, process launch, output creation/opening, proof capture, software changes, drag/drop, paste, folders, archives, release publication, and clean-machine claims.
- Activity has no browser write endpoint and accepts no arbitrary event type, message, path, token, or personal data.
- Preferences and activity use operating-system user-data storage or the explicit absolute override, never the source checkout.

## Completion

- Full real application: `52.5000%`
- Windows local application: `57.5000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `10.0000%`
- Clean-machine proof: `0.0000%`

## Verification

- `python scripts/verify_project.py`: passed all eight project gates.
- `python -m pytest -q`: 140 tests passed.
- Explainability: 164 tracked files mapped; 127 selected sources and 22,832 physical lines explained with current hashes.
- Real isolated loopback smoke: PASS-019, `52.5%`, portable source-independent storage, persisted comfortable/reduced/help-off preferences, one fixed preference event, five lanes, and zero execution-ready lanes.
- Native desktop smoke: passed with both guarded mutation scopes and route execution false.
- Fresh Windows one-file build: `artifacts/windows/MakersAnvil.exe`, 14,316,382 bytes, SHA-256 `a6a9011c9ca3706d47b0cd6c7ce86130f8d77fd38170a483f0f34c16e35008b1`.
- Fresh executable `--smoke`: exit 0 with PASS-019 bundled API/state and `52.5%` completion.
- Live browser screenshot and keyboard interaction proof: not run because no controllable browser surface was available in this session; static frontend, API, and 140-test proof passed, but visual proof remains an explicit residual gap.
- GitHub commit `b5a5a46` updated draft PR #1 for passes 001-019.
- Hosted CI run `28456149703`: Windows verification, Ubuntu verification, macOS verification, and Windows executable build all passed.

## Previous-App Migration Decisions

- `context-help`: staged in `frontend/public/assets/context-help.js`.
- `capability-lanes`: staged in the capability-matrix service and focused renderer.
- `event-history`: rebuilt as fixed create-only portable activity events.
- `workbench settings`: rebuilt as guarded portable presentation preferences.
- Legacy direct upload/drop/paste, source-tree logs, direct tool/process behavior, source paths, and monoliths remain rejected.

## Next Pass

PASS-020 builds one proof-gated contained route execution path with accepted authorization, cancellation control, append-only execution audit, and real output evidence. It must not broaden into arbitrary commands, unrestricted tools, archive extraction, software installation, release claims, or clean-machine claims.
