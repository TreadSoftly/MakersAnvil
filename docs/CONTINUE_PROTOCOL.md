# Continue Protocol

When the user says `Continue`, inspect disk and git state first, then do the next bounded Makers Anvil build pass.

## Required Loop

1. Read `docs/BUILD_STATUS.md`.
2. Check `git status -sb` and `git remote -v`.
3. Run the existing verifier and tests before broadening scope when useful.
4. Build one bounded pass.
5. Keep unproven or unsafe actions blocked.
6. Run `python scripts/verify_project.py`.
7. Run `python -m pytest -q`.
8. Update build status, pass report, and next-pass notes.
9. Commit and push if the working tree is cleanly scoped and GitHub authentication is available.
10. Report what is proven, what remains blocked, the exact commands run, and track-specific percentages.

## Stop Before

- Installing, updating, uninstalling, or repairing software.
- Deleting or moving user-created files.
- Extracting archives or importing folders.
- Launching Blender, FreeCAD, slicers, or other external tools.
- Publishing releases or claiming clean-machine proof.
- Sending private logs, files, screenshots, or diagnostics to remote services.
