# PASS-014 Report - Previous-App Design Assimilation And Source Explanation Remediation

## Status

- Pass: `PASS-014 - previous-app design assimilation and source explanation remediation`
- Claim: `staged`
- Completion date: `2026-06-24`
- Branch: `codex/pass-001-clean-foundation`
- Implementation commit: `7a1046186b43f81906a01739096c30454145b3c6`

## Objective

Repair the gap between technically present documentation and the user's requested visible learning layer, while converting the earlier working Makers Anvil prototype into governed design evidence. This pass advances maintainability and the product's visual direction without pretending that it added runtime behavior.

## Scope And Files

- Added a tracked previous-app study containing accepted layout, workflow, wording, visual, responsive, and proof patterns plus explicit legacy rejections.
- Added a file-by-file source walkthrough connecting browser requests, backend services, scripts, structured contracts, tests, and durable state.
- Expanded every Python module header and every comment-capable frontend/automation header with purpose, caller, inputs, outputs, side effects, safety, failure behavior, and related proof.
- Strengthened the explainability checker, source-manifest schema, Continue protocol, reference policy, start guide, architecture, implementation guide, roadmap, tests, verifier, README, status, and pass ledger.
- Added `Previous Working MA For References/` to ignored/reference-isolation governance.
- Non-goals: new upload behavior, file handoff, authorization acceptance, command construction, process execution, tool launch, outputs, proof capture, packaging, or release claims.

## Explainability Proof

- The source manifest maps all `116` tracked and newly added files, including this report.
- All `43` Python module headers require all eight context labels; every class/function/method/test still requires a meaningful docstring.
- JavaScript, CSS, HTML, SVG, and CI headers require the same eight context labels; top-level frontend functions retain nearby JSDoc.
- The source walkthrough explains every source family and links it to contracts and executable examples.
- The first verifier/test run failed only because this required report did not yet exist; the failure was retained as closure evidence and fixed by adding this report.

## Proven

- The earlier prototype's useful design knowledge survives in tracked repository truth while the 3.9 GB ignored folder remains optional.
- Product source, runtime, tests, and packaging do not depend on any reference root.
- Structured source context is visible in all comment-capable source files and machine-enforced against regression.
- Personal paths and historical runtime/build markers remain absent from product source.
- Existing read-only API, portable storage, planning, tool detection, dry runs, execution gates, request previews, prepared jobs, and cancellation-intent behavior remain intact.

## Blocked Or Not Proven

Browser/API upload, source-file handoff, route execution, output creation/opening, proof capture, external tool launch, tool version proof, runnable commands, request persistence, authorization acceptance, process signaling/execution, execution logging, package changes, archive extraction, folder import, packaged release, clean-machine proof, full macOS/Linux runtime behavior, and browser-hosted behavior remain blocked or not proven.

## Track Percentages

- Full real application: `32.5000%`
- Windows local application: `32.5000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

The application percentages do not increase because this is a remediation/design-assimilation pass, not a new runtime capability.

## Exact Verification

- `python scripts/check_explainability.py` passed with `116` files, all `43` Python modules, all frontend/asset/CI headers, and all components covered.
- Initial `python scripts/verify_project.py` failed only on the intentionally not-yet-created PASS-014 report; all other eight groups passed.
- Initial `python -m pytest -q` passed 85 tests and failed the verifier wrapper for the same missing-report reason.
- Final `python scripts/verify_project.py` passed all `8` verification groups.
- Final `python -m pytest -q -p no:cacheprovider` passed all `86` tests.
- `node --check frontend/public/assets/app.js` and `git diff --check` passed.
- Live `/api/health` returned `makers-anvil-real-pass-014-reference-explainability`; `/api/state` returned PASS-014, `32.5000%`, and PASS-015 next.
- Headless Chrome browser proof passed at `1366x768` and `390x844` with HTTP 200, zero horizontal overflow, and no console/page errors.

## Runtime And Visual Proof

- Local proof URL: `http://127.0.0.1:8766`, started with `python scripts/run_dev.py --port 8766` and stopped after verification.
- The in-app Browser surface was unavailable, so installed Playwright and Chrome provided local visual proof.
- Desktop and mobile screenshots were visually inspected: PASS-014, `32.5000%`, and PASS-015 rendered without overlap or horizontal clipping.
- The screenshots confirm the current UI remains the long read-only scaffold/status layout; the preview-first workbench replacement is correctly assigned to PASS-015 rather than falsely claimed here.
- Server logs showed static assets plus GET-only API traffic and no backend errors.

## Safety Proof

No reference content was copied into product source. No user file, external tool, process, registry key, package, remote service, or non-test runtime directory was modified. The ignored previous-app folder was read only.

## GitHub And CI

- Branch: `codex/pass-001-clean-foundation`.
- Implementation commit: `7a1046186b43f81906a01739096c30454145b3c6` (`Complete PASS-014 reference and explainability remediation`).
- Push to `origin/codex/pass-001-clean-foundation` succeeded.
- Draft pull request: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-014`.
- GitHub Actions run `28133086249` passed `Verify on windows-latest`, `Verify on ubuntu-latest`, and `Verify on macos-latest`.

## Next Pass

PASS-015 rebuilds the current dashboard as the preview-first maker workbench defined by the reference study. It must retain GET-only behavior and keep file handoff, authorization, commands, execution, tool launch, output creation, and package actions blocked.
