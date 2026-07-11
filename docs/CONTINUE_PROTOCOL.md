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
11. `docs/PREVIOUS_APP_MERGER_AUDIT.md`
12. `state/previous_app_migration.json`
13. `docs/DESKTOP_ARCHITECTURE.md`
14. `state/learning_coverage.json`
15. The relevant file section in `docs/LINE_BY_LINE_CODE_GUIDE.md`; do not load the entire generated guide when one section answers the question.
16. For old-app merger work, the relevant section in the locally generated `REFERENCE_SOURCE_LINE_BY_LINE_GUIDE.md`.
17. `docs/PASS_REPORT_TEMPLATE.md`
18. The latest pass report named by `currentPass.reportPath`

## Required Loop

1. Read the required truth and explanation files.
2. Check `git status -sb` and `git remote -v`.
3. Run the existing verifier and tests before broadening scope when useful.
4. Check accepted previous-app patterns and the migration registry; inspect only selected first-party ignored source and never import dependency/generated trees.
5. Define one bounded pass, its proof gates, and its non-goals.
6. Build that pass while keeping unproven or unsafe actions blocked.
7. Update structured file headers, all nine labeled component docstring/JSDoc fields, CSS/HTML block teaching comments, reasoning comments, tests, architecture, the source walkthrough, and `state/source_manifest.json` for every responsibility changed.
8. Regenerate the per-line guide with `python scripts/build_learning_guide.py` after the final implementation, automation, config, schema, state, or workflow edit.
9. Run `python scripts/build_learning_guide.py --check` and `python scripts/check_explainability.py`.
10. Run `python scripts/verify_project.py`.
11. Run `python -m pytest -q`.
12. Run pass-specific runtime, API, browser, native-window, executable, relocation, or platform smoke tests.
13. Update build status, pass report, pass ledger, source manifest, and next-pass notes.
14. Regenerate and re-check the line guide if those durable updates changed a covered source file.
15. Commit and push if the working tree is cleanly scoped and GitHub authentication is available.
16. Wait for CI and report proven, blocked, not-proven, exact commands, and track-specific percentages.

## Explainability Is Part Of Done

- Every tracked file must have a current entry in `state/source_manifest.json`.
- Every Python module must visibly state purpose, user/caller, inputs, outputs, side effects, safety, failure behavior, and related proof.
- Every Python component, including private helpers and tests, must contain Purpose, Inputs, Outputs, How it works, Side effects, Failure behavior, Safety, Example, and Related proof.
- Every top-level JavaScript function must contain the same nine JSDoc fields.
- Every CSS rule and semantic HTML block must retain its required teaching comment.
- Every physical covered source line, including blank lines and comment-free JSON/TOML/YAML contracts, must have an exact numbered explanation in the generated line guide.
- Comments and guide explanations must cover syntax plus intent, data flow, invariants, safety, and failure behavior at the appropriate layer.
- Every changed logical block must be understandable from its component documentation, nearby reasoning comment, names/types, and linked test. A technically passing but visibly under-explained file is unfinished.
- A pass with stale or missing explanations fails even when its functional tests pass.
- Merger passes must keep the local previous app's generated first-party line guide current without editing dependency or generated trees.

## Required User Report

Every completed `Continue` response must state the pass objective and changed responsibilities; explainability proof; proven behavior; blocked or not-proven behavior; exact verification commands and results; runtime, API, browser, screenshot, and CI proof; all six track percentages; safety effects; branch, commit, push, and pull-request state; app URL; and the exact next pass. Use `docs/PASS_REPORT_TEMPLATE.md` as the durable source for this report.

## Stop Before

- Installing, updating, uninstalling, or repairing software.
- Deleting or moving user-created files.
- Extracting archives or importing folders.
- Launching Blender, FreeCAD, slicers, or other external tools.
- Publishing releases or claiming clean-machine proof.
- Sending private logs, files, screenshots, or diagnostics to remote services.
