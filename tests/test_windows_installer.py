"""Purpose: Prove installer gates and clean-machine scenarios remain declarative and safe.

Used by: Developers and CI whenever Windows packaging or release truth changes.
Inputs: Committed policies plus pytest-owned policy mutations.
Outputs: Assertions for MSIX scope, preservation, blocked execution, and zero proof.
Side effects: Reads source policy and creates isolated temporary copies only.
Safety: Never builds, signs, installs, upgrades, repairs, removes, publishes, or deletes.
Failure behavior: Widened policy, missing scenario, or false readiness fails immediately.
Related proof: ``windows_installer.py``, focused APIs, schemas, and harness CLI.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from makers_anvil_backend.services.windows_installer import (
    SCENARIO_IDS,
    WindowsInstallerPolicyError,
    WindowsInstallerService,
)
from scripts import check_clean_machine


ROOT = Path(__file__).resolve().parents[1]


def _isolated_root(tmp_path: Path) -> Path:
    """Purpose: Copy only installer policies into one isolated application root.

    Inputs: Pytest-owned empty temporary directory.
    Outputs: Root containing the two required config files.
    How it works: Creates config and copies reviewed source fixtures byte-for-byte.
    Side effects: Writes only inside pytest temporary storage.
    Failure behavior: Copy errors propagate and fail setup.
    Safety: No user data, installer artifact, certificate, or machine state is copied.
    Example: A test mutates one copied action without touching committed policy.
    Related proof: All policy weakening tests use this helper.
    """

    config = tmp_path / "config"
    config.mkdir()
    for name in ("windows_installer_policy.json", "clean_machine_scenarios.json"):
        shutil.copyfile(ROOT / "config" / name, config / name)
    return tmp_path


def test_readiness_separates_valid_foundation_from_installer_release() -> None:
    """Purpose: Lock current planning progress and all unproven release gates.

    Inputs: Current committed installer policy.
    Outputs: Exact format, gate counts, passed ids, and false release readiness assertions.
    How it works: Requests one deterministic readiness response from the service.
    Side effects: Reads one policy JSON file.
    Failure behavior: Added claims or removed gates fail exact assertions.
    Safety: No package or operating-system state is inspected or changed.
    Example: Three planning gates pass while six proof gates remain blocked.
    Related proof: Installer readiness schema and API test.
    """

    readiness = WindowsInstallerService().readiness()

    assert readiness["package"]["format"] == "msix"
    assert readiness["summary"] == {
        "gateCount": 9,
        "passedGateCount": 3,
        "blockedGateCount": 6,
        "foundationReady": True,
        "installerReady": False,
        "releaseReady": False,
    }
    assert [gate["id"] for gate in readiness["gates"] if gate["passed"]] == ["target-platform", "package-format", "portable-payload"]
    assert readiness["identity"]["publisher"] == "not-proven"
    assert readiness["identity"]["locked"] is False
    assert all(value is False for value in readiness["safety"].values())


def test_clean_machine_harness_has_six_unexecuted_zero_evidence_scenarios() -> None:
    """Purpose: Require complete clean-machine coverage without inventing execution proof.

    Inputs: Current committed scenario registry.
    Outputs: Exact scenario order, zero counters, empty evidence, and false proof assertions.
    How it works: Validates and composes the declarative harness.
    Side effects: Reads two JSON files only.
    Failure behavior: Missing, reordered, run, or evidenced scenarios fail.
    Safety: No VM, package, process, registry, certificate, network, or deletion occurs.
    Example: Upgrade preservation exists as a planned scenario with no evidence.
    Related proof: Clean-machine schema, CLI, API, and frontend panel.
    """

    harness = WindowsInstallerService().clean_machine_harness()

    assert harness["summary"] == {"scenarioCount": 6, "executedCount": 0, "passedCount": 0, "failedCount": 0, "cleanMachineProven": False}
    assert [scenario["id"] for scenario in harness["scenarios"]] == list(SCENARIO_IDS)
    assert all(scenario["executionState"] == "not-run" and scenario["evidence"] == [] for scenario in harness["scenarios"])
    assert harness["environment"]["sourceCheckoutPresent"] is False
    assert harness["actions"] == {"inspectEnabled": True, "executeEnabled": False, "recordEvidenceEnabled": False}
    assert all(value is False for value in harness["safety"].values())


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("identity", "locked", True),
        ("upgrade", "executionEnabled", True),
        ("removal", "userDataPurgeEnabled", True),
        ("signing", "signatureVerified", True),
        ("actions", "installerBuildEnabled", True),
        ("safety", "registryMutationEnabled", True),
    ],
)
def test_installer_policy_rejects_unproven_or_mutating_claims(tmp_path: Path, section: str, key: str, value: object) -> None:
    """Purpose: Fail closed when policy claims proof or enables an installer effect.

    Inputs: Isolated policy plus one parameterized unsafe or unproven value.
    Outputs: Expected typed policy error.
    How it works: Mutates one copied JSON field and requests strict validation.
    Side effects: Writes only one pytest-owned policy copy.
    Failure behavior: Returning a policy fails because the expected exception is absent.
    Safety: Values are never converted into commands or applied to the machine.
    Example: ``installerBuildEnabled=true`` is rejected before building.
    Related proof: Policy schema constants and verifier safety checks.
    """

    root = _isolated_root(tmp_path)
    path = root / "config" / "windows_installer_policy.json"
    policy = json.loads(path.read_text(encoding="utf-8"))
    policy[section][key] = value
    path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(WindowsInstallerPolicyError):
        WindowsInstallerService(root=root).policy()


def test_scenario_registry_rejects_missing_coverage(tmp_path: Path) -> None:
    """Purpose: Prevent a machine-proof claim from omitting upgrade or removal coverage.

    Inputs: Isolated scenario registry with one scenario removed.
    Outputs: Expected coverage error.
    How it works: Rewrites the copied registry and requests harness composition.
    Side effects: Writes only pytest-owned JSON.
    Failure behavior: Returning a five-scenario harness fails the test.
    Safety: No scenario is executed and no machine state is touched.
    Example: Removing reinstall-after-removal makes the harness invalid.
    Related proof: Six-item clean-machine schema constraint.
    """

    root = _isolated_root(tmp_path)
    path = root / "config" / "clean_machine_scenarios.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["scenarios"].pop()
    path.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(WindowsInstallerPolicyError, match="coverage"):
        WindowsInstallerService(root=root).clean_machine_harness()


def test_harness_cli_reports_plan_without_writing(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    """Purpose: Prove the public harness command is inspection-only and machine-readable.

    Inputs: Current source policy with captured standard output.
    Outputs: Zero exit code and six not-run scenario JSON.
    How it works: Calls the CLI function directly and parses its output.
    Side effects: Reads policy and writes captured standard output only.
    Failure behavior: Invalid JSON, nonzero exit, or execution count fails.
    Safety: Direct invocation avoids even spawning a child process in this test.
    Example: The result reports cleanMachineProven false.
    Related proof: CI runs the same script as a separate verification step.
    """

    monkeypatch.setattr(check_clean_machine, "ROOT", ROOT)
    result = check_clean_machine.main()
    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["summary"]["scenarioCount"] == 6
    assert payload["summary"]["executedCount"] == 0
    assert payload["summary"]["cleanMachineProven"] is False
