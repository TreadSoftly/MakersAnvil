# Continue Protocol

When the user says `Continue`, inspect disk and git state first, then do the next bounded Makers Anvil build pass. Chat history is advisory; durable repository truth controls the work.

## Required Reading Order

1. `docs/START_HERE.md`
2. `docs/BUILD_STATUS.md`
3. `state/current_status.json`
4. `state/pass_ledger.json`
5. `docs/ARCHITECTURE.md`
6. `docs/CODE_EXPLAINABILITY_STANDARD.md`
7. `docs/IMPLEMENTATION_GUIDE.md`
8. `docs/LEARNING_RESOURCES.md`
9. `docs/SOURCE_WALKTHROUGH.md`
10. `docs/PREVIOUS_APP_REFERENCE_STUDY.md`
11. `docs/PASS_REPORT_TEMPLATE.md`
12. The latest pass report named by `currentPass.reportPath`

## Required Loop

1. Read the required truth and explanation files.
2. Check `git status -sb` and `git remote -v`.
3. Run the existing verifier and tests before broadening scope when useful.
4. Check the accepted previous-app patterns for layout, workflow, wording, and visual evidence relevant to the pass; inspect selected ignored reference artifacts only when the tracked study is insufficient.
5. Define one bounded pass, its proof gates, and its non-goals.
6. Build that pass while keeping unproven or unsafe actions blocked.
7. Update structured file headers, component docstrings/JSDoc, reasoning comments, tests, architecture, the source walkthrough, and `state/source_manifest.json` for every responsibility changed.
8. Run `python scripts/check_explainability.py`.
9. Run `python scripts/verify_project.py`.
10. Run `python -m pytest -q`.
11. Run pass-specific runtime, API, browser, relocation, or platform smoke tests.
12. Update build status, pass report, pass ledger, source manifest, and next-pass notes.
13. Commit and push if the working tree is cleanly scoped and GitHub authentication is available.
14. Wait for CI and report proven, blocked, not-proven, exact commands, and track-specific percentages.

## Explainability Is Part Of Done

- Every tracked file must have a current entry in `state/source_manifest.json`.
- Every Python module must visibly state purpose, user/caller, inputs, outputs, side effects, safety, failure behavior, and related proof.
- Every Python component, including private helpers and tests, must satisfy the docstring checks.
- Frontend functions must retain nearby JSDoc; frontend and workflow files must retain purpose and section comments.
- Comments must explain intent, data flow, invariants, safety, and failure behavior rather than repeat syntax.
- Every changed logical block must be understandable from its component documentation, nearby reasoning comment, names/types, and linked test. A technically passing but visibly under-explained file is unfinished.
- A pass with stale or missing explanations fails even when its functional tests pass.

## Required User Report

Every completed `Continue` response must state the pass objective and changed responsibilities; explainability proof; proven behavior; blocked or not-proven behavior; exact verification commands and results; runtime, API, browser, screenshot, and CI proof; all six track percentages; safety effects; branch, commit, push, and pull-request state; app URL; and the exact next pass. Use `docs/PASS_REPORT_TEMPLATE.md` as the durable source for this report.

## Stop Before

- Installing, updating, uninstalling, or repairing software.
- Deleting or moving user-created files.
- Extracting archives or importing folders.
- Launching Blender, FreeCAD, slicers, or other external tools.
- Publishing releases or claiming clean-machine proof.
- Sending private logs, files, screenshots, or diagnostics to remote services.
