"""Purpose: Inspect the clean-machine proof harness without changing the machine.

Used by: Developers and CI before any future isolated Windows install testing.
Inputs: Bundled installer policy and declarative clean-machine scenarios only.
Outputs: Machine-readable harness JSON with every scenario explicitly not run.
Side effects: Reads two policy files and writes JSON to standard output.
Safety: Never invokes an installer, process, registry, certificate store, network, VM, or deletion.
Failure behavior: Invalid policy prints a failed record and exits nonzero.
Related proof: ``tests/test_windows_installer.py`` and project verification.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "src"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from makers_anvil_backend.services.windows_installer import WindowsInstallerPolicyError, WindowsInstallerService  # noqa: E402


def main() -> int:
    """Purpose: Validate and print the non-executing clean-machine harness.

    Inputs: No command, path, package, or machine arguments.
    Outputs: Harness JSON and zero, or a path-free failure JSON and one.
    How it works: Builds the service from repository resources and requests its harness.
    Side effects: Reads policy and writes standard output only.
    Failure behavior: Typed policy failures become deterministic failed JSON.
    Safety: Having no execution mode prevents accidental install testing on a workstation.
    Example: ``python scripts/check_clean_machine.py`` reports six not-run scenarios.
    Related proof: CLI output and no-write tests.
    """

    try:
        print(json.dumps(WindowsInstallerService(root=ROOT).clean_machine_harness(), indent=2, sort_keys=True))
        return 0
    except WindowsInstallerPolicyError as exc:
        print(json.dumps({"schemaVersion": "makers-anvil.clean-machine-check.v1", "claimState": "failed", "message": str(exc)}, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
