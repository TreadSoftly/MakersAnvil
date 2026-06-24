# PASS-012 Report - Execution Request And Audit Preview Foundation

## Status

- Pass: `PASS-012 - execution request and audit preview foundation`
- Claim: `staged`
- Completion date: `2026-06-24`
- Branch: `codex/pass-001-clean-foundation`
- Implementation commit: `fdfce5e0e27ccfbf44dab0e9032cde996eb7779e`

## Objective

Model one mesh-to-toolpath execution request as deterministic logical intent with explicit authorization and audit requirements, while persisting nothing, accepting no consent, and starting no process. This advances the Windows-first application from gate definition to a visible request contract without crossing the execution boundary.

## Scope And Files

- Added strict request policy and policy/API schemas.
- Added `ExecutionRequestService`, read-only API routing, coherent app-state composition, and a dashboard panel.
- Added isolated service, API, purity, verifier, and explainability coverage.
- Added permanent implementation, learning-resource, and pass-report guides plus stricter component explanation gates.
- Non-goals: request persistence, authorization acceptance, audit writes, path resolution, command construction, file handoff, process start, tool launch, output writes, proof capture, installation, packaging, or clean-machine claims.

## Explainability Proof

- Every tracked file has a detailed source-manifest purpose and maintenance record.
- Every Python module, class, constructor, function, method, private helper, and test function is checked for a docstring.
- Every top-level frontend function is checked for nearby JSDoc; frontend/workflow file headers remain checked.
- `docs/IMPLEMENTATION_GUIDE.md`, `docs/LEARNING_RESOURCES.md`, and `docs/PASS_REPORT_TEMPLATE.md` are required by schema and CI.
- Request join and rendering blocks explain fail-closed matching, logical references, untrusted text, and permanently blocked execution.
- Service tests are executable examples of normal, missing-tool, missing-gate, broadened-policy, and incomplete-audit behavior.

## Proven

- Policy is restricted to `mesh-to-toolpath` and all ten side-effect flags are false.
- A coherent dry-run plan and gate evaluation produce deterministic path-free intent.
- Authorization is required but remains unaccepted, with no actor or timestamp.
- Six append-only audit event types are required while no event or request record is created.
- Missing gate evidence fails closed without a request preview.
- The API and dashboard expose preview truth without any mutation endpoint or enabled action.

## Blocked Or Not Proven

- Request persistence, accepted authorization, audit-event persistence, source/output path resolution, commands, processes, cancellation signaling, execution logging, tool launch, output creation/opening, proof capture, software changes, archive extraction, folder import, packaging, and clean-machine proof remain blocked or not proven.
- Full macOS, Linux, and browser-hosted runtime behavior remains planned and not proven.

## Track Percentages

- Full real application: `30.0000%`
- Windows local application: `30.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Exact Verification

- `python scripts/check_explainability.py` passed with all `102` tracked files mapped and no explanation failures.
- `python scripts/verify_project.py` passed all `8` verification groups.
- `python -m pytest -q` passed all `76` tests.
- `node --check frontend/public/assets/app.js` passed.
- `git diff --check` passed.
- Draft 2020-12 validation passed for execution-request policy, request-preview API, composed app state, and source manifest.
- Live HTTP smoke returned `makers-anvil-real-pass-012-execution-request-preview`, PASS-012, `30.0000%`, all-zero request effects, all-false safety, and POST `405`.
- Isolated HTTP smoke produced one mesh request preview with a detected PrusaSlicer candidate while persistence, authorization, audit writes, and execution remained zero/false.
- The isolated source SHA-256 was unchanged; the temporary source, runtime, fake executable, server, and logs were removed in `finally`.
- The first isolated browser harness run used a shortened expected operation label and failed its own assertion; no product defect was found. The corrected exact-label rerun passed.

## Runtime And Visual Proof

- Local URL: `http://127.0.0.1:8765` using `python scripts/run_dev.py`.
- The built-in app-browser surface was unavailable, so local Playwright used installed Chrome after the required browser connection attempt.
- Real empty state passed at `1280x900` and `390x844`: exact request values rendered, horizontal overflow was `0`, traffic was GET-only, and console/page errors were empty.
- Isolated non-empty state passed at `1280x900`: one row rendered logical source/output references, unaccepted authorization, `6` required audit events, `0` written events, and the complete blocker list.
- Desktop, mobile, and isolated full-page screenshots were visually inspected; no overlap, clipping, blank panel, or incoherent layout was observed.

## Safety Proof

No user file, external tool, installer, package, registry key, or remote runtime service was modified by PASS-012. One temporary empty source fixture and fake executable name were created only for isolated detection, never executed, hash-checked, and deleted with the entire temporary root. Every request safety flag remained false and the public payload exposed no resolved source or home path.

## GitHub And CI

- Branch `codex/pass-001-clean-foundation` was pushed to `origin` at implementation commit `fdfce5e0e27ccfbf44dab0e9032cde996eb7779e`.
- Draft PR: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-012`.
- GitHub Actions run `28115944632` passed `Verify on windows-latest` in 33 seconds.
- GitHub Actions run `28115944632` passed `Verify on ubuntu-latest` in 10 seconds.
- GitHub Actions run `28115944632` passed `Verify on macos-latest` in 11 seconds.

## Next Pass

PASS-013 - contained job workspace and cancellation record foundation. It may model contained job ownership and cancellation records, but external tool launch and route execution remain blocked.
