# PASS-018 Report - Explicit Authorization And Portable Native/Browser Intake Foundation

## Status

- Pass: `PASS-018 - explicit authorization and portable native/browser intake foundation`
- Claim: `staged`
- Completion date: `2026-06-29`
- Branch: `codex/pass-001-clean-foundation`

## Objective

Replace the previous app's immediate multi-file upload behavior with one narrow production capability: choose one allowlisted regular file, review its visible metadata, explicitly authorize one copy, and store that copy under an app-generated name in private app-owned quarantine storage. Do not turn intake consent into route execution, selected-file handoff, tool launch, output creation, archive extraction, folder import, or software management permission.

## Implemented Contract

- `GET /api/intake/session` returns current constraints and an opaque process-local request token.
- `POST /api/intake/authorizations` accepts only bounded JSON metadata under same-origin request evidence.
- `POST /api/intake/authorizations/{authorizationId}/content` accepts only the exact declared byte stream for one unexpired, unconsumed authorization.
- Final lowercase suffix and classified kind must match the committed allowlist; archives and double-extension archive disguises fail closed.
- Size must be positive, no larger than 512 MiB, and exactly equal to the transferred content length.
- The service reads in 1 MiB chunks, computes SHA-256, flushes the temporary file, and atomically replaces the generated quarantine destination.
- Partial transfer, record failure, stale authorization, and replay remove incomplete state and return a typed error.
- Public records expose logical app-owned locations and generated names, never selected source paths or private resolved storage paths.
- The workbench implements choose, review, explicit authorize, cancel, progress, success, and error states with one hidden file input.

## Security Decisions

- The loopback server emits a restrictive content-security policy, frame denial, no-sniff, referrer restriction, and cross-origin resource policy.
- CORS is not enabled and preflight is rejected. Mutation additionally requires exact Origin/Host agreement, an allowed Fetch Metadata site value, and constant-time comparison of the process token.
- User file names never choose a storage path. The physical destination is the generated intake identifier plus the validated final suffix.
- Authorization records persist no request token and no source path. The selected browser `File` remains in memory until transfer or cancel.
- MIME/content verification and malware scanning are not claimed. Their false policy flags prevent intake from becoming execution-ready.

## Previous-App Use

The earlier app's prominent intake tile and selected-file review informed the interaction. Its immediate multipart copy, drop/paste/multi-file paths, absolute workspace coupling, direct handoff, and operational endpoints were not copied. `state/previous_app_migration.json` marks only the rebuilt one-file picker/copy portion staged; drag/drop and paste remain blocked.

## Explainability

Every new Python component and test has all nine teaching fields. New HTML blocks, CSS rules, JavaScript functions, JSON contracts, and source-manifest entries are included in the generated line-by-line guide. Official Fetch, Fetch Metadata, CORS, Python temporary-file, and OWASP upload references are linked from `docs/LEARNING_RESOURCES.md`.

## Track Percentages

- Full real application: `42.5000%`
- Windows local application: `47.5000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `7.5000%`
- Clean-machine proof: `0.0000%`

## Verification

- `python scripts/build_learning_guide.py --check`: passed; 110 current source/contract files and 20,643 physical lines explained.
- `python scripts/check_explainability.py`: passed; all 146 manifested files have maintained ownership and explanation contracts.
- `python scripts/verify_project.py`: passed; API, explainability, forbidden-text, JSON, portability, reference, required-file, and status gates are green.
- `python -m pytest -q -p no:cacheprovider`: passed; 130 tests including authorization, streaming, rollback, same-origin, server, no-console desktop, and frontend contracts.
- Ten PASS-018 policy/state/runtime objects passed their Draft 2020-12 schemas, including app state, session, persisted authorization, and authorized intake record.
- Live HTTP proof returned CSP/no-CORS headers, rejected OPTIONS with `405`, rejected a missing process token with `403`, and left zero partial files.
- Playwright at 1366x768 and 390x844 observed zero POST before consent, exactly two authorized POSTs returning `201`, picker readiness after completion, no horizontal overflow, no top-level region overlap, and no console/page errors.
- The Windows one-file artifact is 14,270,874 bytes with SHA-256 `3474A397A707586EC87BB648F3691AE40EEE7E930E34C36972699B2CBD269972`.
- A relocated copy ran `--smoke` from the temporary directory with exit `0`, proving bundled resources and no source-checkout working-directory requirement.
- A real packaged `Makers Anvil` window rendered the PASS-018 build and enabled intake control; normal close removed both one-file processes.
- `git diff --check`: passed with only expected Windows line-ending notices.

## GitHub And CI

- Implementation commit: `d7880d1036729c37cfe94c8c15487b9336297f07`.
- Draft pull request: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-018`.
- GitHub Actions run `28411032843` passed on the implementation commit.
- `windows-latest`, `ubuntu-latest`, and `macos-latest` each passed the canonical project verifier and all 130 tests.
- The hosted Windows job built and smoked the windowed executable, then uploaded `MakersAnvil-windows-x64-pass-018` (14,329,584-byte artifact archive).

## Blocked Or Not Proven

Route execution, execution authorization, selected-file handoff, external tool launch, runnable command creation, output creation/opening, proof capture, archive upload/extraction, folder import, drag/drop, clipboard paste, content-type verification, malware scanning, software install/update/uninstall/repair, signing, installer behavior, public release, clean-machine setup, macOS/Linux runtime packaging, and browser-hosted operation remain blocked or not proven.

## Next Pass

PASS-019 migrates the previous app's useful capability-lane, contextual-help, event-history, and settings concepts into focused schema-backed modules. It must not import previous runtime data, dependencies, paths, generated output, or monolithic source files.
