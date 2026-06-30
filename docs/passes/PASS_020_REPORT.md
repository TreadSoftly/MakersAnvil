# PASS-020 Report - Contained Built-In STL Preflight

## Scope

- Enabled one explicitly authorized, app-owned STL structural preflight inside the mesh-to-toolpath lane.
- Added cooperative cancellation, immutable lifecycle audit, real app-owned report/log/proof artifacts, and workbench controls.
- Kept full route execution, slicing, G-code, external commands/processes/tools, output opening, software changes, archives, and release claims blocked.

## Implemented

- `ContainedExecutionService` validates one strict committed policy, authorized STL intake, single-execution ownership, lifecycle transitions, and portable storage.
- Source inspection streams bounded chunks and proves size, SHA-256, and binary/ASCII STL structure without retaining source bytes.
- `ExecutionAuditService` exclusively creates fixed-vocabulary, contiguous, append-only lifecycle events.
- Cancellation uses an app-owned control record observed between chunks; no process signal or process-stop claim exists.
- Successful and failed completion create a structural report, execution log, hashed proof record, and terminal manifest with logical paths only.
- Guarded loopback endpoints expose policy/catalog reads and exact authorize/run/cancel mutations.
- The workbench offers eligible-source authorization, run, cancel, lifecycle, proof, and audit status while stating the partial-operation boundary.

## Explanation And Learning

- New Python classes, functions, methods, tests, and JavaScript functions use the nine-field teaching contract.
- New HTML and CSS blocks include nearby purpose, mechanism, example, and safety context.
- Execution policy, record, cancellation, audit, report, proof, catalog, and app-state schemas make the runtime artifacts independently understandable.
- The generated line-by-line guide and source manifest are refreshed and hash-checked during final verification.

## Safety Boundary

- Enabled: explicit authorization, in-process STL structure inspection, cooperative cancellation, contained evidence writes, and fixed audit events.
- Still blocked: full route completion, slicing, toolpath/G-code generation, arbitrary commands, external processes/tools, selected-file direct handoff, output opening, archive/folder operations, software lifecycle changes, release publication, and clean-machine claims.
- The original selected source is never reopened by the backend; execution reads only the authorization-created app-owned quarantine copy.
- Public records expose generated ids, logical locations, counts, hashes, and outcomes, never resolved private paths.

## Completion

- Full real application: `62.5000%`
- Windows local application: `67.5000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `12.5000%`
- Clean-machine proof: `0.0000%`

## Verification

- `python scripts/verify_project.py`: passed all eight project gates.
- `python -m pytest -q`: 146 tests passed.
- Explainability: 178 tracked files mapped; 140 selected sources and 25,237 physical lines explained with current hashes.
- Seven contained policy/runtime/API schema validations passed for policy, execution, cancellation, audit, report, proof, and catalog shapes.
- Isolated real loopback flow completed intake authorization/copy, execution authorization/run, passing digest and STL checks, five audit events, and one catalog proof.
- The live proof explicitly recorded `fullRouteCompleted=false`, `toolpathGenerated=false`, and `outputOpened=false`.
- Live browser screenshot and viewport interaction proof was not run because the in-app browser surface was unavailable; static DOM/CSS, frontend purity, API, responsive, and complete test proof passed.
- Fresh Windows one-file build completed at `artifacts/windows/MakersAnvil.exe`; the final post-documentation artifact hash is reported with the pass handoff.
- Fresh executable `--smoke`: exit 0 with PASS-020, `62.5%`, all three bounded mutation scopes, and full route execution false.
- GitHub commit and hosted CI evidence are added after publication.

## Next Pass

PASS-021 defines non-destructive backup, restore, update, uninstall, and repair dry-run lifecycle contracts. It must not mutate installed software, delete user data, publish a release, or claim clean-machine readiness.
