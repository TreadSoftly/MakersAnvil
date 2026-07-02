# PASS-026 Report - Execution History And Cooperative Cancellation

## Status

- Pass: `PASS-026 - contained execution history and cooperative cancellation controls`
- Claim: locally proven
- Branch: `codex/pass-001-clean-foundation`

## Objective

Make contained STL preflight lifecycle visible and controllable from the real Makers Anvil workbench without widening execution to an external process, tool, arbitrary route, or filesystem path.

## Scope And Files

- `frontend/src/api.ts` maps strict execution/catalog truth, exposes generated identity before Run completes, targets selected proof records, and sends guarded cancellation.
- `frontend/src/types.ts` defines closed history and lifecycle presentation contracts.
- `frontend/src/App.tsx` renders compact history, selected proof commands, active-run identity, distinct cancelled outcomes, and one cooperative cancel control.
- `frontend/src/styles.css` provides stable responsive history geometry and state treatment.
- `schemas/contained-execution-catalog.schema.json` closes the summary and action shapes used by history/cancellation.
- Adapter and React tests provide executable examples for mapping, early identity, selected proof, cancellation POST, and visible false-signal behavior.
- Full route execution, OS signaling, tool launch, selected-file handoff, host output opening, archive work, and lifecycle execution are explicit non-goals.

## Explainability Proof

- New frontend functions carry purpose, inputs, outputs, mechanics, effects, failure, safety, examples, and related proof.
- Changed files remain mapped in `state/source_manifest.json`.
- The generated exact line guide and coverage counts are recorded after final source edits.

## Proven

- Valid execution catalog entries become newest-first path-redacted history rows.
- Every row distinguishes authorized, running, completed, cancelled, and failed lifecycle truth.
- Proof-bearing history can request that exact run's report or proof.
- Generated execution identity reaches the workbench before the threaded Run request completes.
- Cancel validates generated-id syntax, live nonterminal state, action availability, and process-local token before one bodyless POST.
- Existing service tests prove pre-start and in-flight cancellation, observed intent, no proof outputs after cancellation, and `processSignalSent: false`.

## Blocked Or Not Proven

- Operating-system cancellation signaling and process-stop proof remain blocked.
- Full mesh-to-toolpath, slicing, repair, G-code, external tools, and selected-file handoff remain blocked.
- Packaged release, MSIX, signing, publication, clean-machine execution, macOS/Linux runtime, and hosted-web runtime remain unproven.

## Track Percentages

- Full real application: `87.5000%`
- Windows local application: `90.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `30.0000%`
- Clean-machine proof: `5.0000%`

## Exact Verification

- Frontend Vitest: passed, 27 tests across 2 files.
- TypeScript and Vite production build: passed.
- Full Python suite: passed, 170 tests.
- Project verifier: all API, required-file, JSON, status, portability, reference, forbidden-text, and explanation groups passed.
- Explainability verifier: passed for all 223 tracked/pending product files.
- Every-line learning guide: passed for 167 selected sources and 37,854 explained physical lines.
- Native source smoke: passed with PASS-026, `87.5%`, history/cancellation build marker, and full route execution false.
- Browser screenshot and live viewport proof: not claimed because the in-app browser was unavailable; jsdom interaction and responsive source gates passed.
- Fresh Windows one-file build: succeeded; packaged `MakersAnvil.exe --smoke` passed with bundled PASS-026 frontend, schema, and state resources.
- Windows executable proof: 14,499,782 bytes with SHA-256 `4c8696c66506f2c6e0c57eed3f0884d74dbbc47850f1510966369f9033afadfc`.
- GitHub Actions run `28561477840`: Windows verification, Ubuntu verification, macOS verification, and Windows executable build/smoke/upload all passed.

## Safety Proof

No user file, external process, external tool, registry key, package, archive, runtime location, or remote service is selected or modified by the new history presentation. Cancellation changes only the app-owned execution control/record/audit state already owned by the contained preflight service.

## Next Pass

PASS-027 establishes allowlisted tool version proof and launch confirmation while keeping actual launch, selected-file handoff, installation, and arbitrary commands blocked.
