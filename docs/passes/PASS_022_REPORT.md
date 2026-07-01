# PASS-022 Report - Windows Installer Foundation

## Scope

- Selected MSIX as the Windows x64 per-user installer target.
- Added explicit package identity, upgrade, removal, signing, and runtime contracts.
- Added nine read-only release-readiness gates and six clean-machine proof scenarios.
- Kept installer build/execution, signing, package registration, registry changes, publication, and user-data deletion blocked.

## Implemented

- `WindowsInstallerService` strictly validates two closed bundled policies and exposes deterministic readiness.
- Three foundation gates pass: Windows x64 target, MSIX selection, and source-independent payload design.
- Six proof gates remain blocked: locked identity, built installer, trusted signature, upgrade, removal, and clean-machine proof.
- Upgrade requires the same identity and a higher version while preserving user data and rejecting downgrade.
- Removal preserves user data by default; future purge requires explicit consent and remains disabled.
- Clean-machine scenarios cover fresh install, first launch, upgrade, repair, removal, and reinstall with zero runs and zero evidence.
- Three GET-only API routes and the Dev workbench expose installer truth without command controls.
- `scripts/check_clean_machine.py` validates and prints the harness but has no execution mode.

## Architecture Decision

- Microsoft documents MSIX as the modern Windows package format with package identity, reliable install/removal, updates, and integrity metadata.
- Microsoft requires a trusted signature before an MSIX can be installed; production signing choice and publisher identity are therefore real blockers, not placeholders disguised as readiness.
- The one-file PyInstaller executable remains the payload foundation. An MSIX manifest, visual assets, package build, and isolated installation execution belong to later proof passes.

## Safety Boundary

- Enabled: policy reads, schema validation, gate evaluation, scenario inspection, API rendering, and CLI inspection.
- Still blocked: MSIX build, certificate creation/import, signing, timestamping, package registration, installation, upgrade, downgrade, repair, removal, purge, network access, external processes, release publication, and clean-machine success claims.
- No API or browser mutation route was added.
- No package, registry key, certificate store, installed software, or user data was changed by the product implementation.

## Completion

- Full real application: `72.5000%`
- Windows local application: `80.0000%`
- macOS/Linux application: `0.0000%`
- Browser-hosted application: `0.0000%`
- Packaged release: `30.0000%`
- Clean-machine proof: `5.0000%` for the completed harness foundation; `0/6` scenarios are executed.

## Verification

- `python scripts/verify_project.py`: passed all eight project gates.
- `python -m pytest -q`: 163 tests passed.
- Explainability: 195 tracked files mapped; 155 selected sources and 27,895 physical lines explained with current hashes.
- Windows installer policy, installer readiness, clean-machine harness, and Windows package-plan schemas validated against current outputs.
- Inspection CLI reported six scenarios, zero executions, zero evidence, and false clean-machine proof.
- Isolated loopback proof reported PASS-022 at `72.5%`, MSIX format, exactly two inspection actions, `3/9` gates, `0/6` scenarios, and all safety effects false.
- The isolated app-data tree was byte/metadata-identical before and after installer policy, readiness, harness, and state reads.
- Live browser screenshot and viewport interaction proof was not run because the in-app browser surface was unavailable; static DOM/CSS, responsive, purity, API, and full test proof passed.
- Fresh source desktop smoke exited 0 with PASS-022, `72.5%`, unchanged bounded mutation scopes, and route execution false.
- Fresh Windows one-file build completed at `artifacts/windows/MakersAnvil.exe`; packaged `--smoke` exited 0 with bundled PASS-022 contracts.
- Final local artifact identity: 14,404,632-byte `artifacts/windows/MakersAnvil.exe` with SHA-256 `62da24dbd2298fea5d241174814d7db58b5e18e41ff63e7e96b25461ae1fc0c5`.
- Implementation commit `ac97f1a7eeeddf01b5a9d622a72357d4beb85446` is published on `codex/pass-001-clean-foundation` through draft PR #1.
- GitHub Actions run `28525413654` passed Windows, macOS, and Ubuntu verifier, harness, and test jobs plus the Windows executable build, smoke, and artifact upload job.

## Next Pass

PASS-023 builds the MSIX manifest and development package path plus isolated install execution foundations. It must not claim production trust, publication, destructive removal, or clean-machine success without those exact proofs.
