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
9. `state/current_status.json` - machine-readable current truth.
10. `state/pass_ledger.json` - ordered history of completed passes.
11. `state/source_manifest.json` - purpose and maintenance notes for every tracked file.
12. The report named by `currentPass.reportPath` in `state/current_status.json`.

## Before Editing

- Run `git status -sb` and preserve unrelated work.
- Run `python scripts/verify_project.py` and `python -m pytest -q` when the current checkout should be healthy.
- Identify one bounded pass and its explicit non-goals.
- Read every file that owns the behavior being changed, including its tests, schema, status record, and source-manifest entry.

## While Editing

- Keep source paths portable and runtime data outside the source checkout.
- Keep unsafe or unproven actions blocked.
- Explain each changed file and every component according to the explainability standard.
- Comment decisions, invariants, boundaries, and failure behavior; do not narrate obvious syntax.
- Update tests as executable examples of the intended behavior.
- Update `state/source_manifest.json` when files are added, removed, renamed, or given new responsibilities.

## Before Declaring Done

Run:

```powershell
python scripts/check_explainability.py
python scripts/verify_project.py
python -m pytest -q
```

Then run the pass-specific smoke tests, update durable status and the pass report using `docs/PASS_REPORT_TEMPLATE.md`, commit, push, and wait for CI. A chat summary without those durable updates is not a completed `continue` pass.
