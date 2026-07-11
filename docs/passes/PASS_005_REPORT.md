# PASS-005 Report - Portable Runtime Paths And Relocation Safety

## Status

Claim state: `staged`.

## What Changed

- Added a platform runtime-path service independent from the source checkout and current working directory.
- Added OS-standard per-user data policies:
  - Windows local application data
  - macOS Application Support
  - Linux XDG data
- Added the absolute `MAKERS_ANVIL_DATA_DIR` override for explicit deployments and portable launchers.
- Moved workspace and intake runtime records away from source-adjacent storage.
- Replaced resolved path output with logical storage metadata in API and dashboard records.
- Added Windows, macOS, Linux, override, containment, redaction, and relocation tests.
- Extended verification to reject personal machine paths in committed product source.

## Proven Boundaries

- The application source does not contain a required username, home directory, desktop folder, cloud-sync folder, or drive-specific path.
- Runtime data does not depend on the source checkout location.
- Source checkout and runtime data can reside in unrelated directories.
- Relative or escaping runtime overrides are rejected.
- API and dashboard records do not expose resolved personal filesystem paths.
- Existing intake, execution, launch, extraction, deletion, packaging, and release gates remain blocked.

## Blocked Or Not Proven

- Browser/API upload.
- Direct selected-file handoff.
- Route execution.
- Output open actions.
- External tool launch.
- Tool install/update/uninstall/repair.
- Archive extraction.
- Folder import.
- Packaged release.
- Clean-machine proof.
- Full macOS, Linux, and browser-hosted runtime proof.

## Track Percentages

- Real app completion: `12.5000%`
- Windows local app: `12.5000%`
- macOS/Linux app: `0.0000%`
- Browser-hosted app: `0.0000%`
- Packaged release: `0.0000%`
- Clean-machine proof: `0.0000%`

## Verification

```text
python scripts/verify_project.py -> PASS, including portable_paths
python -m pytest -q -> 29 passed
relocated checkout verifier and test run -> PASS
server launch from a different working directory -> PASS
runtime data outside relocated source checkout -> PASS
local HTTP smoke for logical runtime metadata, path redaction, and blocked POST -> PASS
Chromium browser smoke at 1280px and true 390px device emulation -> PASS; no horizontal overflow
```

## Next Pass

PASS-006 - route preview foundation.
