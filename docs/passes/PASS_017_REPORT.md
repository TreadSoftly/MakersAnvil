# PASS-017 Report - Previous-App Unification And Windows Desktop Executable Foundation

## Status

- Pass: `PASS-017 - previous-app unification and Windows desktop executable foundation`
- Claim: `staged`
- Completion date: `2026-06-29`
- Branch: `codex/pass-001-clean-foundation`
- Implementation commit: `bd90840959e027902c960eacfd209683d5e24d01`.
- CI-maintenance commit: `8afa1d4034d7fc4b73da434d5c48d2823d7e2d4e`.

## Objective

Turn the old working application and current researched core into one governed Makers Anvil product path. Preserve the old app as tested evidence, prevent duplicate or generated legacy trees from entering product source, establish a secure native desktop lifecycle, and produce a smoke-testable Windows one-file executable foundation.

## Scope And Files

- Added a disk/source/test audit and an explicit capability migration registry for the previous app.
- Added local first-party previous-source line-guide generation without editing the legacy source or traversing its dependencies and outputs.
- Added source/PyInstaller resource resolution, loopback-only server construction, native pywebview lifecycle, and binary smoke mode.
- Added a deterministic pinned Windows PyInstaller build/check script and Windows CI artifact job.
- Added strict migration and package-plan schemas plus focused resource, server, desktop, packaging, and old-guide tests.
- Updated architecture, implementation, walkthrough, learning, Continue, start, roadmap, README, status, ledger, API marker, verifier, and source manifest.
- Non-goals: copying old monoliths, enabling upload, accepting authorization, selected-file handoff, constructing runnable tool commands, route execution, tool launch, output open/create, signing, installer publication, updates, removal, or clean-machine proof.

## Explainability Proof

- Every new Python component carries Purpose, Inputs, Outputs, How it works, Side effects, Failure behavior, Safety, Example, and Related proof.
- The current generated line guide and source manifest are regenerated after final source changes.
- The ignored previous app has a separate local generated guide covering 29 first-party files and all 14,611 physical lines.
- Legacy `.venv`, `node_modules`, `dist`, caches, logs, ingress records, Projects, and generated outputs are explicitly outside guide and migration scope.

## Proven

- The current and previous-app learning guides cover every selected physical source line and reject stale hashes.
- The source server and packaged executable both expose the PASS-017 build marker, current status, and blocked mutation truth.
- The production executable starts without the source checkout, serves bundled frontend/config/schema/state resources, and passes health and state smoke checks.
- Chromium renders the workbench at desktop and mobile dimensions without page-level horizontal overflow, console errors, or page errors.
- A native Windows window loaded the real workbench and current state through the packaged executable.

## Blocked Or Not Proven

Browser/native file upload, selected-file handoff, authorization acceptance, runnable commands, route execution, tool launch, output creation/opening, signing, installer behavior, update/uninstall behavior, public release, clean-machine setup, full macOS/Linux runtime, and browser-hosted runtime remain blocked or not proven.

## Track Percentages

- Full real application: `37.5000%`
- Windows local application: `40.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `5.0000%`
- Clean-machine proof: `0.0000%`

## Exact Verification

- `python scripts/build_learning_guide.py --check`: passed; 105 current source files and 18,204 physical lines explained.
- `python scripts/check_explainability.py`: passed; all 140 manifested files satisfy the maintained source-context contract.
- `python scripts/build_previous_app_learning_guide.py --check`: passed; 29 selected first-party previous-app files and all 14,611 physical lines explained.
- `python scripts/verify_project.py`: passed; API, explainability, forbidden-text, JSON, portable-path, reference-policy, required-file, and status-record checks are green.
- `python -m pytest -q -p no:cacheprovider`: passed; 110 tests.
- `npm test -- --run`: passed; the root test contract reran the same 110-test Python suite.
- Four durable JSON records passed their Draft 2020-12 schemas: current status, source manifest, learning coverage, and previous-app migration.
- `python scripts/build_windows_exe.py --check`: passed and emitted the pinned, one-file, windowed Windows build plan.
- `MakersAnvil.exe --smoke`: passed; bundled `/api/health` and `/api/state` returned the PASS-017 marker, 37.5% real-app completion, and disabled mutations.
- `git diff --check`: passed; only host line-ending conversion notices were emitted.
- Local artifact: 14,228,285 bytes; SHA-256 `E538FC86D650C999B6A2FB4EB1851FC4DB6810997D9D0322F19486C268A193E0`.

## Runtime And Visual Proof

- Chromium desktop proof: 1366x768, HTTP 200, correct title/build marker/completion, no page-level horizontal overflow, no console errors, and no page errors.
- Chromium mobile proof: 390x844, HTTP 200, correct title/build marker/completion, no page-level horizontal overflow, no console errors, and no page errors.
- Native executable proof: a real `Makers Anvil` Windows window loaded the synchronized workbench and PASS-017 state rather than the offline fallback; closing it left no Makers Anvil process running.
- The source server remains loopback-only. The packaged desktop server selects an ephemeral loopback port and shuts it down with the window lifecycle.

## Safety Proof

No previous-app source, dependency, generated output, user project, external maker tool, installed software, registry entry, or user runtime data is copied, deleted, launched, or modified by the migration audit. Local build dependencies and artifacts, if created, stay in ignored build/output locations and are reported explicitly.

## GitHub And CI

- Draft PR: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-017`.
- GitHub Actions run `28392774025` passed at commit `8afa1d4034d7fc4b73da434d5c48d2823d7e2d4e`.
- Windows, Ubuntu, and macOS each passed the canonical verifier and all 110 tests.
- The hosted Windows job built and smoked the executable, then uploaded artifact `MakersAnvil-windows-x64-pass-017`.

## Next Pass

PASS-018 builds explicit authorization and portable native/browser intake. It may select and stage an authorized file into app-owned storage, but route execution, external tool launch, arbitrary path opening, output claims, package installation, and release publication remain blocked.
