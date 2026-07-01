# PASS-021 Report - Lifecycle Dry-Run Contracts

## Scope

- Added read-only backup, restore, update, uninstall, and repair lifecycle plans.
- Added bounded aggregate inventory for declared app-owned backup source directories.
- Added a workbench lifecycle view with current evidence, plan depth, preservation truth, and blockers.
- Kept archive, restore, network, package, installer, software mutation, process, deletion, signing, release, and clean-machine behavior blocked.

## Implemented

- `LifecycleDryRunService` validates one closed policy and composes exactly five deterministic operation previews.
- Inventory scans declared settings, intake, jobs, executions, outputs, and logs through non-following directory metadata only.
- Public inventory returns counts, total bytes, link/error counts, logical directory ids, and scan-limit truth without content, names, or private paths.
- Backup and temporary directories are excluded from source inventory; one global 10,000-entry limit prevents unbounded traversal.
- Each plan declares ordered steps, required evidence, explicit blockers, preservation rules, false effects, and a disabled execution action.
- `GET /api/lifecycle/policy` and `GET /api/lifecycle/dry-runs` expose focused contracts; composed app state includes the same catalog.
- The Dev workbench renders all five plans and aggregate inventory with no lifecycle command control.

## Explanation And Learning

- Every new Python and JavaScript component uses the complete nine-field teaching contract.
- Every new HTML and CSS block carries nearby purpose, mechanism, example, and safety context.
- Strict policy/catalog schemas document operation order, preservation, actions, safety, inventory, and plan truth.
- Source manifest and generated line-by-line guide coverage are refreshed and hash-checked before closeout.

## Safety Boundary

- Enabled: policy reads, bounded app-owned metadata inventory, bundled-core existence checks, deterministic lifecycle previews, and workbench rendering.
- Still blocked: file content/name/path exposure, backup manifest/archive creation, archive reading/extraction, restore writes, release lookup, network access, package download, signature claims, installer registration/execution, software mutation, external processes, and user-data deletion.
- Uninstall planning preserves app data by default and cannot accept user confirmation in this pass.
- Update and repair plans report current bundled evidence but cannot claim an available/trusted package.

## Completion

- Full real application: `67.5000%`
- Windows local application: `72.5000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `17.5000%`
- Clean-machine proof: `0.0000%`

## Verification

- `python scripts/verify_project.py`: passed all eight project gates.
- `python -m pytest -q`: 154 tests passed.
- Explainability: 185 tracked files mapped; 146 selected sources and 26,530 physical lines explained with current hashes.
- Lifecycle policy, lifecycle catalog, and local-settings schemas validated against current runtime output.
- Isolated loopback proof reported PASS-021 at `67.5%`, five preview-ready plans, zero execution-ready plans, one 21-byte source file, and logical backup target `makers-anvil-data://user/backups`.
- The isolated before/after app-data tree was identical; content read remained false and every lifecycle effect remained false.
- Live browser screenshot and viewport interaction proof was not run because the in-app browser surface was unavailable; static DOM/CSS, responsive, API, frontend purity, and complete test proof passed.
- Fresh source desktop smoke: exit 0 with PASS-021, `67.5%`, unchanged bounded mutation scopes, and full route execution false.
- Fresh Windows one-file build completed at `artifacts/windows/MakersAnvil.exe`; packaged `--smoke` exited 0 with the bundled PASS-021 lifecycle contracts.
- Final local artifact identity: 14,386,242-byte `artifacts/windows/MakersAnvil.exe` with SHA-256 `9c53da8cc61c69c9d476ca1353ea1208034786e50c7bb3d11500c1ac77fec179`.
- Implementation commit `5eec067a4cedc99d474fd9b640594a1ae25d147c` is published on `codex/pass-001-clean-foundation` through draft PR #1.
- GitHub Actions run `28522933226` passed Windows, macOS, and Ubuntu verification plus the Windows executable build, smoke, and artifact upload jobs.

## Previous-App Decision

- Preserved its reviewed machine-readable planning and explicit-blocker pattern.
- Rejected its source-adjacent generated reports, embedded personal paths, package execution assumptions, and broad setup scope.

## Next Pass

PASS-022 builds a Windows installer foundation plus explicit upgrade/removal gates and a clean-machine test harness. It must not claim signing, publication, destructive uninstall, or clean-machine success until those proofs actually pass.
