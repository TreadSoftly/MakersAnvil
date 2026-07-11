# Makers Anvil Pass Report Template

Copy this structure into `docs/passes/PASS_NNN_REPORT.md` and replace every placeholder. Do not leave pending evidence in a completed report.

## Status

- Pass: `PASS-NNN - name`
- Claim: `complete`, `blocked`, or `in progress`
- Completion date: `YYYY-MM-DD`
- Branch and commit: exact names

## Objective

State the one bounded outcome in plain language and explain how it advances the full application.

## Scope And Files

List every added or materially changed file and its responsibility. State explicit non-goals so a preview or contract cannot be mistaken for working execution.

## Explainability Proof

- Source-manifest coverage count and result.
- Python module/component docstring result.
- Frontend file/function comment result.
- New or updated implementation-guide and learning-resource paths.
- Reasoning comments added for non-obvious safety, data-flow, or failure blocks.
- Tests that serve as executable examples.

## Proven

List only behaviors directly demonstrated by automated or live evidence.

## Blocked Or Not Proven

List every unsafe, future, platform, packaging, clean-machine, and external-tool behavior that was not demonstrated. State whether each item is deliberately blocked, planned, staged, or not proven.

## Track Percentages

- Full real application: `0.0000%`
- Windows local application: `0.0000%`
- macOS and Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

Percentages measure their named track only. A planning, documentation, or preview pass must not imply equivalent release readiness.

## Exact Verification

Record every command, exit result, meaningful count, and failure. Required baseline:

```powershell
python scripts/check_explainability.py
python scripts/verify_project.py
python -m pytest -q
```

Also record focused tests, schema validation, API smoke, relocation/platform checks, forbidden-content scans, and working-tree checks used by the pass.

## Runtime And Visual Proof

- Local URL and server command.
- `/api/health` build marker.
- New endpoint response summary.
- Desktop and mobile viewport sizes tested.
- Screenshot paths or browser-test evidence.
- Console/network errors observed.
- Whether the required content was visibly rendered without overlap or overflow.

## Safety Proof

Record disabled actions and negative tests. Explicitly state whether any user file, process, external tool, registry key, package, runtime directory, or remote service was modified.

## GitHub And CI

- Branch.
- Commit hash and message.
- Push result.
- Pull request URL and state.
- CI workflow/check names and final results for each operating system.

## Next Pass

Name the next bounded pass, its intended proof, and the actions that must remain blocked during it.

