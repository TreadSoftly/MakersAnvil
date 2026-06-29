# Previous App Merger Audit

## Decision

The ignored previous application is a verified behavior and design source, not a second product tree. Makers Anvil will keep one backend, one frontend, one contract vocabulary, one runtime-data policy, and one desktop packaging path. Features migrate only after their behavior, safety boundaries, tests, and instructional coverage fit the current architecture.

The old source is preserved in place. Two generated local artifacts explain its first-party source without editing the baseline:

- `Previous Working MA For References/MAKERS ANVIL/Application/REFERENCE_SOURCE_LINE_BY_LINE_GUIDE.md`
- `Previous Working MA For References/MAKERS ANVIL/Application/REFERENCE_SOURCE_LEARNING_COVERAGE.json`

The generator selects 29 first-party files and explains all 14,611 physical lines. It excludes `.venv`, `node_modules`, `dist`, caches, logs, ingress records, project outputs, and generated artifacts.

## Disk Audit

- Entire extracted reference tree: 85,952 files and 3,744,850,136 bytes.
- The tree contains a complete Python virtual environment, frontend dependencies, compiled frontend output, runtime logs, intake records, screenshots, project source banks, and generated job outputs. None is suitable for direct product import.
- Previous backend first-party files: seven modules; the largest are `state.py` at 1,542 lines, `cad_derivative_adapter.py` at 785 lines, and `app.py` at 664 lines.
- Previous frontend first-party source: `App.tsx` at 3,201 lines and `styles.css` at 5,356 lines, plus smaller API, type, component, test, and configuration files.
- Surviving baseline proof: 32 Python tests and 20 React tests pass on this machine.

## Reuse Matrix

| Previous behavior or design | Decision | Product destination |
| --- | --- | --- |
| Dense industrial workbench, rail, command search, tool strip, Work Flow/Plans/Dev views, output inspector | Already adopted and continue refining | Current static frontend modules |
| Intake tile, drag/drop/paste, selected file, classification, preview | Rebuild behind explicit authorization and app-owned storage | Intake service plus future native/browser adapters |
| Contextual help and capability lanes | Migrate as modular read-only views | Focused frontend renderers and strict API contracts |
| Tool cards and route-aware tool selection | Reuse concepts and verified wording | Existing tool detection/dry-run services |
| Event history and notices | Rebuild with redaction and append-only schema | Future audit service, not source-tree logs |
| Route execution, external tool launch, output open, file copying | Do not copy | Rebuild only after authorization, containment, cancellation, logging, and proof gates pass |
| CAD review/derivative behavior | Study tests and output contracts | Separate route adapters after tool-version and clean-input proof |
| Source-adjacent project/workspace layout | Reject | OS-standard per-user runtime storage |
| Absolute workspace and executable paths | Reject | Private runtime resolution with public logical identifiers |
| Monolithic React/Python/CSS files | Reject | Focused modules with file/component/block/line teaching coverage |

## Confirmed Legacy Risks

- `app.py` exposes and mutates workspace files, accepts uploads, copies files, starts tools, and opens paths.
- `state.py` returns the resolved workspace path to the frontend.
- `app.py` derives the workspace from a fixed parent depth, coupling runtime behavior to one extracted tree shape.
- `cad_derivative_adapter.py` includes a developer-specific FreeCAD executable location.
- Runtime records and logs live inside the source/reference tree.
- Major frontend and backend responsibilities are concentrated in files too large for safe incremental maintenance.
- Generated dependencies and outputs account for most of the 3.7 GB tree and must never enter product history or packaging.

## Migration Rules

1. Preserve the old app until each retained behavior has a tested replacement.
2. Never copy `.venv`, `node_modules`, `dist`, caches, logs, runtime records, screenshots, generated jobs, or private project media.
3. Port behavior through current config, schema, service, API, frontend, test, verifier, and proof layers.
4. Split migrated UI and backend responsibilities before they approach legacy monolith size.
5. Keep private paths out of public state and use OS-standard user-data roots.
6. Keep execution and launch behavior blocked until the current gate chain is complete.
7. Apply direct component/block documentation and generated every-line coverage to every migrated product file.
8. Update `state/previous_app_migration.json` so no capability is duplicated or silently forgotten.

## Completion Meaning

The merge is complete only when every retained feature is implemented in the real product, rejected features are recorded, all tests and package proof pass, and the application no longer requires the ignored previous tree. At that point the user may choose to remove the reference folder; the product will never delete it automatically.
