# Start Here

This is the durable entrypoint for a new developer, AI model, reviewer, or future maintainer. Do not begin by guessing from chat history. Read the current repository state in this order:

1. `README.md` - product purpose, local commands, and portability contract.
2. `docs/BUILD_STATUS.md` - current pass, proven behavior, blocked behavior, and percentages.
3. `docs/CONTINUE_PROTOCOL.md` - exact rules for the next bounded implementation pass.
4. `docs/ARCHITECTURE.md` - system parts, data flow, trust boundaries, and extension points.
5. `docs/CODE_EXPLAINABILITY_STANDARD.md` - required comments, docstrings, tests, and file-map maintenance.
6. `docs/IMPLEMENTATION_GUIDE.md` - complete code, contract, data-flow, safety, extension, and debugging map.
7. `docs/LEARNING_RESOURCES.md` - local study order and authoritative external references.
8. `docs/PASS_REPORT_TEMPLATE.md` - mandatory evidence and reporting structure.
9. `docs/SOURCE_WALKTHROUGH.md` - file-by-file code reading order and call chains.
10. `docs/PREVIOUS_APP_REFERENCE_STUDY.md` - accepted prototype layout/workflow lessons and rejected legacy risks.
11. `docs/PREVIOUS_APP_MERGER_AUDIT.md` - verified old-app inventory, reuse decisions, exclusions, and migration rules.
12. `docs/DESKTOP_ARCHITECTURE.md` - native window, packaging, WebView2, and release boundaries.
13. `state/current_status.json` - machine-readable current truth.
14. `state/pass_ledger.json` - ordered history of completed passes.
15. `state/previous_app_migration.json` - no-duplicate capability migration registry.
16. `state/source_manifest.json` - purpose and maintenance notes for every tracked file.
17. `state/learning_coverage.json` - exact hashes and line totals for the generated learning guide.
18. The relevant file section in `docs/LINE_BY_LINE_CODE_GUIDE.md` - numbered explanation for every physical source line.
19. The report named by `currentPass.reportPath` in `state/current_status.json`.

## Before Editing

- Run `git status -sb` and preserve unrelated work.
- Run `python scripts/verify_project.py` and `python -m pytest -q` when the current checkout should be healthy.
- Identify one bounded pass and its explicit non-goals.
- Read every file that owns the behavior being changed, including its tests, schema, status record, and source-manifest entry.
- For merger work, read the matching previous-source guide section and update the migration registry before rewriting behavior.

## While Editing

- Keep source paths portable and runtime data outside the source checkout.
- Keep unsafe or unproven actions blocked.
- Explain each changed file and every component according to the explainability standard, including the visible structured source header and all nine component fields.
- Add teaching comments to changed CSS/HTML blocks and reasoning comments to changed logic.
- Update tests as executable examples of the intended behavior.
- Update `state/source_manifest.json` when files are added, removed, renamed, or given new responsibilities.
- Regenerate the line-by-line guide after the last covered source edit so even syntax and blank lines retain exact numbered explanations.

## Before Declaring Done

Run:

```powershell
python scripts/build_learning_guide.py --check
python scripts/build_previous_app_learning_guide.py --check
python scripts/check_explainability.py
python scripts/verify_project.py
python -m pytest -q
```

Then run the pass-specific smoke tests, update durable status and the pass report using `docs/PASS_REPORT_TEMPLATE.md`, commit, push, and wait for CI. A chat summary without those durable updates is not a completed `continue` pass.
