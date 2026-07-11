# PASS-027 Report - Metadata Tool Version And Launch Review

## Status

- Pass: `PASS-027 - metadata tool version proof and launch confirmation review`
- Claim: locally and hosted-CI proven
- Completion date: `2026-07-11`
- Branch and product commit: `codex/pass-001-clean-foundation` at `869e568`

## Objective

Prove maker-tool versions from operating-system metadata without starting the tool, then let a user inspect the exact tool-only launch binding before any confirmation or process action exists.

## Scope And Files

- `tool_version.py` reads Windows fixed VERSIONINFO or a macOS app bundle's bounded version keys.
- `tool_detection.py` privately passes detected targets to that reader, validates closed evidence, and returns no resolved path.
- `tool_launch.py`, its config, and two schemas define detected-plus-versioned launch-review readiness with confirmation and process actions disabled.
- `AppStateService` and `MakersAnvilApi` expose the coherent review at `GET /api/tools/launches/preview` and in `/api/state`.
- The frontend adapter, types, workbench, and styles render metadata versions and an accessible close-only review dialog.
- Focused Python, API, adapter, React, package-smoke, and verifier coverage protect the behavior.
- Actual confirmation submission, consent persistence, executable-path exposure, command construction, arguments, selected-file handoff, process start, output opening, and tool correctness are explicit non-goals.

## Explainability Proof

- Every new Python class/function and changed React function carries purpose, inputs, outputs, mechanics, side effects, failure, safety, example, and related proof.
- New CSS blocks explain dialog geometry, wrapping, blocker presentation, and mobile reflow beside the rules.
- `state/source_manifest.json`, architecture, implementation, walkthrough, file-map, and learning-resource documents map the new ownership and study path.
- Focused service, API, adapter, and React tests are executable examples.
- Explainability passes for all 231 tracked/pending product files; the generated guide explains 39,431 physical lines across 174 current sources.
- The ignored previous app remains reference-only and its separate checked guide still explains 14,611 lines across 29 selected first-party files.

## Proven

- Windows numeric file/product versions are read through `GetFileVersionInfoW` and `VerQueryValueW` without loading or starting the executable.
- macOS short/bundle versions are read from a bounded nearest-app `Info.plist` without LaunchServices or a process.
- Unsupported Linux metadata, links, missing resources, invalid version text, malformed evidence, and reader failures remain not proven.
- Public version records expose only bounded values and evidence method; command and absolute-path flags remain false.
- Launch review requires both detected presence and proven metadata version.
- Review binding contains only stable tool id, executable name, version, evidence method, and tool-only mode.
- Confirmation is required but unaccepted, unpersisted, and has no endpoint; launch has no endpoint.
- The workbench review dialog has only close controls and explicitly lists excluded selected files/arguments plus launch blockers.
- A live read of Windows `notepad.exe` produced metadata version `10.0.26100.8737` without starting Notepad, proving the native API path on this machine.
- The live Makers Anvil catalog detected zero of six configured tools, so no installed maker-tool version is claimed on this device.

## Blocked Or Not Proven

- External maker-tool launch, command construction, process audit, and process cancellation are blocked.
- Launch-confirmation acceptance, expiry, replay prevention, persistence, and authorization audit are not implemented.
- Selected-file and generated-output handoff remain blocked.
- Linux metadata version proof and live macOS runtime proof remain unproven.
- Publisher signature/authenticity, malware safety, workflow compatibility, and output correctness are not inferred from metadata versions.
- Full route execution, G-code/toolpath creation, arbitrary host opening, lifecycle execution, MSIX release, signing, publication, and clean-machine proof remain blocked or unproven.

## Track Percentages

- Full real application: `89.5000%`
- Windows local application: `92.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `30.0000%`
- Clean-machine proof: `5.0000%`

## Exact Verification

- Focused tool/version/launch/API tests: passed, 19 selected tests.
- Frontend Vitest: passed, 29 tests across 2 files.
- TypeScript and Vite production build: passed.
- Full Python suite: passed, 181 tests.
- Every-line guide check: passed for 174 sources and 39,431 physical lines; previous-app guide check passed for 29 sources and 14,611 lines.
- Explainability checker: passed for all 231 tracked/pending files.
- Project verifier: all required-file, API, JSON/schema, status, portability, forbidden-text, reference, and explainability groups passed.
- Windows native metadata smoke: passed with `10.0.26100.8737` from a system PE and no process start.
- Native source smoke: passed with PASS-027, `89.5%`, launch review true, and tool launch false.
- Live HTTP smoke at `http://127.0.0.1:8780`: PASS-027 build marker, six configured tools, zero detected/review-ready, six blocked, and tool launch false.
- Playwright desktop/mobile proof: passed at 1366x768 and 390x844 with no horizontal overflow, no console/page errors, viewport-contained dialog, two close controls, and zero help layers above the modal.
- Focused Axe dialog scan: zero violations.
- Fresh pinned PyInstaller 6.21.0/pywebview 6.2.1 build: passed after the system Python correctly reported those package dependencies absent; `uv run` supplied an isolated pinned build environment.
- Packaged `MakersAnvil.exe --smoke`: passed locally and from a generated relocated copy launched with `C:\WINDOWS` as its working directory; the generated temp copy was removed after process release.
- Windows executable: 14,159,660 bytes; SHA-256 `ee99fe5221866b774e4b92df617098520ec2db437a63f93cfa80793905d320ff`.
- GitHub Actions run `29156508141`: Windows verification, Ubuntu verification, macOS verification, and Windows executable build/smoke/upload all passed.

## Runtime And Visual Proof

- App URL: `http://127.0.0.1:8780` from `python scripts/run_dev.py --host 127.0.0.1 --port 8780`.
- API build marker: `makers-anvil-real-pass-027-tool-version-launch-review`.
- The compiled frontend contains the launch-review dialog and its responsive rules.
- jsdom interaction opens the version-bound dialog, verifies evidence/exclusions/blockers, finds only two close controls, and closes it.
- Live API evidence reports six configured tools, zero detected, zero version-proven, zero review-ready, and six blocked on this machine.
- Desktop screenshots: `artifacts/screenshots/pass-027-desktop.png` and `artifacts/screenshots/pass-027-desktop-dialog.png`.
- Mobile screenshots: `artifacts/screenshots/pass-027-mobile-viewport.png` and `artifacts/screenshots/pass-027-mobile-dialog.png`.
- Desktop document geometry was 1366x768 with 1366 scroll width and 768 scroll height; mobile had 390 client/scroll width and intentionally vertical workbench flow.
- Mocked review evidence was used only to render the otherwise unreachable dialog because this machine has no detected catalog tool; the mock did not modify server truth or launch software.

## Safety Proof

No user file, maker tool, external process, registry key, package, archive, runtime directory, or remote service is modified by version detection or launch review. The Windows live smoke reads one system executable's version resource only. Public records and UI contain no resolved path, selected file, argument, command, accepted consent, or process handle.

## GitHub And CI

- Branch: `codex/pass-001-clean-foundation`.
- Product commit: `869e568 add metadata tool version and launch review`; pushed to `origin/codex/pass-001-clean-foundation`.
- Pull request: draft [#1](https://github.com/TreadSoftly/MakersAnvil/pull/1), titled `[codex] Build Makers Anvil through PASS-027`.
- GitHub Actions run `29156508141`: `Verify on windows-latest`, `Verify on ubuntu-latest`, `Verify on macos-latest`, and `Build Windows executable` all completed successfully.

## Next Pass

PASS-028 adds short-lived explicit tool-only launch authorization, executable identity gates, and an allowlisted process adapter. It must preserve path privacy, bind consent to one detected/versioned/trusted target, prevent replay, start no selected file or arbitrary argument, record process truth, and keep tool-output correctness, installation, lifecycle, archive, and release actions blocked.
