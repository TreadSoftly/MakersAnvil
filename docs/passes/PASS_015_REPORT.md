# PASS-015 Report - Preview-First Maker Workbench Shell And Responsive Dashboard Foundation

## Status

- Pass: `PASS-015 - preview-first maker workbench shell and responsive dashboard foundation`
- Claim: `staged`
- Completion date: `2026-06-24`
- Branch: `codex/pass-001-clean-foundation`
- Implementation commit: `c735fe40923dd6f13d6a46c152618622ee774804`

## Objective

Replace the long equal-weight status stack with the real application's first governed maker workbench. Existing API truth remains unchanged, but normal users now encounter source intake, selected input, tools, workflow, plans, output preview, and proof before raw developer evidence.

## Scope And Files

- Rebuilt `frontend/public/index.html` as a persistent rail, compact command bar, paired source deck, tool inventory, stable Work Flow/Plans/Dev command deck, and output-proof inspector.
- Rebuilt `frontend/public/assets/styles.css` with bounded desktop geometry, local panel scrolling, responsive mobile flow, reduced-motion handling, explicit truth colors, and card radii no greater than eight pixels.
- Extended `frontend/public/assets/app.js` with selected-input and expected-output summaries, local-only view switching, rail focus navigation, and quick-jump search.
- Added `tests/test_frontend_workbench.py` to lock required zones, unique DOM IDs, renderer targets, read-only controls, local navigation wiring, and responsive CSS contracts.
- Updated architecture, implementation guide, source walkthrough, previous-app study, status, roadmap handoff, source manifest, API marker, verifier, and existing state/API tests.
- Non-goals: browser upload, source contents, selected-file handoff, authorization acceptance, command construction, route execution, process control, tool launch, output creation/opening, proof capture, software changes, packaging, or release proof.

## Explainability Proof

- `state/source_manifest.json` covers all `118` tracked and pending product files.
- Every changed frontend file retains all eight structured context fields and section/block comments.
- Every new controller function has nearby JSDoc explaining data flow and safety.
- The new frontend regression module has structured module context plus class, constructor, method, helper, and test docstrings.
- The source manifest and walkthrough identify the new responsibilities and reading order.

## Proven

- The first viewport is a maker workbench rather than a status-document stack.
- Desktop geometry keeps source, tools, workflow, and proof visible together.
- Work Flow, Plans, and Dev tabs change one stable command deck without server mutation.
- Rail and quick-jump search focus the requested work zone.
- Intake metadata and expected-output summaries remain text-only, path-redacted, and evidence honest.
- The disabled Add files affordance has no file input, form, handler, or mutation endpoint.
- Existing GET-only API rendering and all blocked operational boundaries remain intact.

## Blocked Or Not Proven

Browser/API upload, source-file handoff, route execution, output creation/opening, proof capture, external tool launch, tool version proof, runnable commands, request persistence, authorization acceptance, process signaling/execution, execution logging, package changes, archive extraction, folder import, packaged release, clean-machine proof, full macOS/Linux runtime behavior, and browser-hosted behavior remain blocked or not proven.

## Track Percentages

- Full real application: `35.0000%`
- Windows local application: `35.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Exact Verification

- `python -m pytest -q tests/test_frontend_workbench.py tests/test_project_purity.py -p no:cacheprovider` passed all `19` focused tests.
- `python scripts/check_explainability.py` passed with all `118` files mapped and no structured-source failures.
- `python scripts/verify_project.py` passed all `8` verification groups.
- `python -m pytest -q -p no:cacheprovider` passed all `91` tests.
- `node --check frontend/public/assets/app.js`, duplicate-ID/DOM-target audit, and `git diff --check` passed.
- GitHub and CI results passed and are recorded below.

## Runtime And Visual Proof

- Live empty-state proof used `http://127.0.0.1:8766` and returned `makers-anvil-real-pass-015-preview-first-workbench`, PASS-015, `35.0000%`, and PASS-016 next.
- Chrome/Playwright proof at `1600x980`, `1366x768`, and `1280x720` recorded zero page-level horizontal/vertical overflow, no clipped buttons, six tool cards, and stable command-deck geometry across Work Flow, Plans, and Dev.
- Chrome/Playwright proof at `390x844` recorded zero horizontal overflow, no clipped buttons, and intentional vertical document flow.
- Quick-jump search focused the Tools zone; Plans and Dev became visible; all network methods were GET; console/page error lists were empty.
- Screenshots for desktop Work Flow, Plans, Dev, mobile Work Flow, and populated desktop state were captured to temporary proof storage and visually inspected for overlap, clipping, blank content, and coherent hierarchy.
- An isolated staged `sample-bracket.stl` rendered as metadata-only selected input with one work plan, one output bundle, three expected artifacts, and incomplete proof at desktop/mobile widths.
- The isolated page exposed no private temporary root, used GET only, had zero horizontal overflow, and retained the source SHA-256 `A40A9DE9A77239BFD3E4CB0D29BFC4E659D59BD8AF4009CCC160018AFA2CA472` before and after proof.
- The isolated server and temporary runtime/source root were removed after verification.

## Safety Proof

No reference asset or legacy code was copied into product source. Frontend behavior remains GET-only. The isolated proof created one temporary source fixture and app-owned metadata record, changed neither source bytes nor user data, and removed both afterward. No external tool, registry key, package, or remote service was modified.

## GitHub And CI

- Branch: `codex/pass-001-clean-foundation`.
- Implementation commit: `c735fe40923dd6f13d6a46c152618622ee774804` (`Complete PASS-015 preview-first workbench`).
- Push to `origin/codex/pass-001-clean-foundation` succeeded.
- Draft pull request: `https://github.com/TreadSoftly/MakersAnvil/pull/1`, titled `[codex] Build Makers Anvil passes 001-015`.
- GitHub Actions run `28134548110` passed `Verify on windows-latest`, `Verify on ubuntu-latest`, and `Verify on macos-latest`.

## Next Pass

PASS-016 adds explicit authorization and command preview contracts without accepting consent, resolving private paths, handing off a selected file, or starting a process.
