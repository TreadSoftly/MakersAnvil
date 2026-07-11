# PASS-025 Report - Verified Contained Artifact Viewer

## Goal

Make the contained STL preflight's real report and proof readable in Makers Anvil without enabling arbitrary filesystem access or operating-system file opening.

## Implemented

- Extended the strict contained-execution policy with a 256 KiB artifact ceiling and an explicit verified read action.
- Added dynamic read-only `GET /api/executions/{executionId}/artifacts/{artifactKind}` handling for exactly `report` and `proof`.
- Added complete runtime validation for terminal execution records, proof fields, logical artifact references, report fields, hashes, size, and fixed false route/tool/output claims.
- Added a schema-backed, path-redacted artifact response carrying JSON content, integrity evidence, and explicit safety state.
- Mapped the newest terminal proof-bearing execution into the promoted workbench's latest-job output region.
- Added an accessible responsive in-app JSON dialog with integrity, result, size, logical location, close-button, backdrop, and Escape behavior.
- Added service, API, adapter, and React tests for success plus unknown, unready, malformed, altered, and oversized rejection paths.

## Safety Boundaries

- Artifact kind is a closed value, not a path or filename.
- Execution ids must match the generated anchored identifier pattern before path resolution.
- Physical storage paths are never returned to the browser.
- Symlinks, missing files, nonterminal executions, malformed JSON, changed proof/report shape, digest drift, and content above 256 KiB fail closed.
- In-app viewing does not invoke a Windows file association, browser tab, shell command, process, external tool, selected-file handoff, archive operation, or software change.
- Full mesh-to-toolpath execution, slicing, G-code creation, repair, and manufacturing readiness remain unproven.

## Completion

- Full real application: `85.0000%`
- Windows local application: `88.0000%`
- Packaged release: `30.0000%`
- Clean-machine proof: `5.0000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`

## Verification

- Focused contained-execution and API tests: passed, 25 tests.
- Frontend Vitest: passed, 24 tests across 2 files.
- TypeScript and Vite production build: passed.
- Full Python suite: passed, 169 tests.
- Project verifier: all API, required-file, JSON, status, portability, reference, forbidden-text, and explanation groups passed.
- Explainability verifier: passed for all 222 tracked/pending product files.
- Every-line learning guide: passed for 167 selected sources and 37,301 explained physical lines.
- Native source smoke: passed with PASS-025, `85.0%`, the contained-artifact API build, artifact viewer enabled, and full route execution false.
- Fresh Windows one-file build: succeeded; packaged `MakersAnvil.exe --smoke` passed with bundled PASS-025 frontend, policy, schema, and state resources.
- Windows executable proof: 14,497,441 bytes with SHA-256 `858e9b5c4c236f8822b06c5c929d94603e0094587e1dcf0942544c79b184af42`.
- Browser screenshot proof: not claimed because the in-app browser was unavailable.
- GitHub Actions run `28559729294`: Windows verification, Ubuntu verification, macOS verification, and Windows executable build/smoke/upload all passed.

## Next Pass

PASS-026 adds contained execution history and cooperative cancellation controls without enabling external process signaling or broad route execution.
