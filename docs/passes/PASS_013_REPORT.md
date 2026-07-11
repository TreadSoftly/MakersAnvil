# PASS-013 Report - Contained Job Workspace And Cancellation Record Foundation

## Status

- Pass: `PASS-013 - contained job workspace and cancellation record foundation`
- Claim: `staged`
- Completion date: `2026-06-24`
- Branch: `codex/pass-001-clean-foundation`
- Implementation commit: `c890814d1d5e1300f13900ba20f6456479665742`

## Objective

Add the first real job-runtime records without enabling execution: one explicit local script prepares an empty app-owned workspace from a valid mesh request preview, and another records cancellation intent without signaling a process. This advances the Windows-first application from read-only intent to contained, inspectable runtime state.

## Scope And Files

- Added strict job workspace policy plus policy, manifest, cancellation, and catalog schemas.
- Added focused job-record construction/validation plus `JobWorkspaceService` storage orchestration with deterministic ids, atomic writes, idempotency, containment checks, and fail-closed catalog reads.
- Added explicit `prepare_job.py` and `request_job_cancel.py` local commands.
- Added read-only job policy/catalog APIs, composed app state, and a responsive dashboard panel.
- Added service, API, purity, verifier, explainability, schema, runtime, and browser coverage.
- Non-goals: browser/API mutation, accepted authorization, source-file handoff, resolved output paths, runnable commands, process start/signaling, external tools, output artifacts, audit events, proof capture, packaging, or clean-machine claims.

## Explainability Proof

- Every new policy, schema, script, service, test, UI region, and report is mapped in `state/source_manifest.json`.
- Every Python component and top-level frontend function is covered by the machine explainability gate.
- Non-obvious blocks explain atomic completion markers, fail-closed runtime parsing, symlink/traversal rejection, logical-only persistence, and cancellation-versus-process truth.
- Tests provide executable examples for empty reads, preparation, idempotency, private-data rejection, cancellation, containment, malformed records, and policy weakening.

## Proven

- One valid request preview maps deterministically to one prepared job id.
- Only app-owned job directories and JSON control records are written.
- Public and persisted records contain logical references and no resolved source/runtime path.
- Cancellation intent is recorded once and remains idempotent.
- Cancellation records keep `processSignalSent` and `processStopped` false.
- Invalid runtime records fail closed and are not exposed as usable jobs.
- HTTP remains GET-only and reports zero execution-ready jobs.

## Blocked Or Not Proven

- Executable request persistence, accepted authorization, selected-file handoff, output-path resolution, command construction, process start/signaling/stopping, execution logs, external tool launch, output artifacts, audit events, proof capture, software changes, archive extraction, folder import, packaging, and clean-machine proof remain blocked or not proven.
- Full macOS, Linux, and browser-hosted runtime behavior remains planned and not proven.

## Track Percentages

- Full real application: `32.5000%`
- Windows local application: `32.5000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Exact Verification

- `python scripts/check_explainability.py` passed with all `113` tracked files mapped and no explanation failures.
- `python scripts/verify_project.py` passed all `8` verification groups.
- `python -m pytest -q` passed all `86` tests; one synchronized-folder cache-write warning appeared after cache cleanup.
- `python -m pytest -q -p no:cacheprovider` passed all `86` tests without warnings.
- `node --check frontend/public/assets/app.js` and `git diff --check` passed.
- Draft 2020-12 validation passed for job policy, job record, cancellation record, job catalog, composed app state, and source manifest.
- Live HTTP smoke returned `makers-anvil-real-pass-013-contained-job-workspaces`, PASS-013, `32.5000%`, an honest empty catalog, all-false unsafe effects, and POST `405`.
- Isolated `stage_intake.py`, `prepare_job.py`, and `request_job_cancel.py` completed successfully against temporary app-owned storage.
- Isolated proof produced one prepared job, one cancellation request, two JSON record files, zero output files, zero execution-ready jobs, and no server errors.
- The source SHA-256 remained unchanged, no private runtime path appeared in API JSON, and the fake detected tool file was never executed.
- The temporary runtime, source fixture, fake tool name, logs, and isolated server were removed in `finally`.

## Runtime And Visual Proof

- Local URL: `http://127.0.0.1:8765` using `python scripts/run_dev.py`.
- The built-in app-browser surface was unavailable, so installed local Playwright and Chrome were used after the required connection attempt.
- Real empty state passed at `1280x900` and `390x844`: exact PASS-013 values rendered, overflow was `0`, traffic was GET-only, and console/page errors were empty.
- Isolated populated/cancelled state passed at `1280x900` and `390x844`: one logical job row rendered, cancellation was requested, no process signal was claimed, execution stayed blocked, and overflow/errors remained zero.
- All four full-page screenshots were visually inspected; no blank panel, overlap, clipping, or incoherent mobile wrapping was observed.

## Safety Proof

Only temporary isolated app-owned directories and JSON records were created during proof. The source fixture remained hash-identical; the fake tool name was detected but never executed; process id, start/completion times, process signal, process stop, output artifact, audit event, and proof fields remained absent or false. All isolated artifacts were removed.

## GitHub And CI

- Branch `codex/pass-001-clean-foundation` was pushed to `origin` at implementation commit `c890814d1d5e1300f13900ba20f6456479665742`.
- Draft PR: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-013`.
- GitHub Actions run `28117640620` passed `Verify on windows-latest` in 39 seconds.
- GitHub Actions run `28117640620` passed `Verify on ubuntu-latest` in 19 seconds.
- GitHub Actions run `28117640620` passed `Verify on macos-latest` in 8 seconds.

## Next Pass

PASS-014 - explicit authorization and command preview foundation. It may model bounded consent and non-runnable arguments, but process start, selected-file handoff, and tool launch remain blocked.
