"""Purpose: Evaluate Windows installer, upgrade, removal, signing, and clean-machine readiness.

Used by: ``AppStateService``, read-only API routes, and the clean-machine harness CLI.
Inputs: Two committed closed policies describing MSIX foundations and proof scenarios.
Outputs: Path-free installer gates and six explicitly unexecuted clean-machine scenarios.
Side effects: Reads bundled JSON policy files only.
Safety: Never builds, signs, installs, upgrades, repairs, removes, publishes, or starts a process.
Failure behavior: Missing, malformed, broadened, or unsafe policy fails before a response exists.
Related proof: ``tests/test_windows_installer.py`` and three installer JSON schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.runtime_resources import application_root


ROOT = application_root()
POLICY_FIELDS = {
    "schemaVersion", "claimState", "mode", "platform", "package", "identity", "runtime",
    "upgrade", "removal", "signing", "actions", "safety",
}
SCENARIO_FIELDS = {"schemaVersion", "claimState", "mode", "environment", "scenarios", "actions", "safety"}
SCENARIO_IDS = (
    "fresh-install", "first-launch", "upgrade-preserves-data", "repair",
    "uninstall-preserves-data", "reinstall-after-removal",
)
TRUE_ACTIONS = {"foundationInspectionEnabled", "harnessInspectionEnabled"}


class WindowsInstallerPolicyError(ValueError):
    """Purpose: Reject installer or clean-machine policy outside the closed foundation.

    Inputs: Reviewed diagnostic naming the invalid policy concept.
    Outputs: Typed failure for API orchestration, CLI validation, and tests.
    How it works: Preserves standard ``ValueError`` behavior without fallback state.
    Side effects: None.
    Failure behavior: Callers receive no partial readiness or scenario response.
    Safety: Diagnostics contain no machine path, certificate material, or user data.
    Example: Enabling installer execution raises this error before any process exists.
    Related proof: Policy-weakening tests mutate every execution boundary.
    """


class WindowsInstallerService:
    """Purpose: Compose honest release-readiness gates without performing release work.

    Inputs: Bundled Windows installer policy and clean-machine scenario registry.
    Outputs: Validated policy, nine readiness gates, and six not-run scenarios.
    How it works: Applies strict field/value checks and derives only boolean planning evidence.
    Side effects: Reads two JSON files; all operating-system and package effects are absent.
    Failure behavior: Invalid identities, scenarios, actions, or safety flags raise explicitly.
    Safety: No command, private path, secret, package mutation, or API action is produced.
    Example: A valid foundation passes three planning gates while installerReady stays false.
    Related proof: Service, schema, API, frontend, CLI, and package smoke tests.
    """

    def __init__(self, root: Path | None = None) -> None:
        """Purpose: Bind the service to one source or frozen read-only resource root.

        Inputs: Optional application root used by isolated tests.
        Outputs: Initialized service with fixed policy paths.
        How it works: Resolves one root and appends reviewed config filenames.
        Side effects: Resolves paths only.
        Failure behavior: Missing files fail when a public method loads policy.
        Safety: Current directory, user home, and previous app are never consulted.
        Example: Tests inject a temporary root containing copied policy files.
        Related proof: Relocation, package-smoke, and missing-policy tests.
        """

        self.root = (root or ROOT).resolve()
        self.policy_path = self.root / "config" / "windows_installer_policy.json"
        self.scenarios_path = self.root / "config" / "clean_machine_scenarios.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load and validate the complete Windows installer foundation policy.

        Inputs: Committed installer policy JSON.
        Outputs: Closed policy mapping suitable for path-free API exposure.
        How it works: Checks exact fields, target, package, identity, preservation, actions, and safety.
        Side effects: Reads one UTF-8 JSON file.
        Failure behavior: Missing, malformed, widened, or execution-enabled policy raises.
        Safety: Only two inspection actions may be true; every effect must remain false.
        Example: Publisher stays ``not-proven`` until a real signing identity is selected.
        Related proof: Strict-policy and schema tests.
        """

        value = self._read_json(self.policy_path, "Windows installer policy")
        if set(value) != POLICY_FIELDS:
            raise WindowsInstallerPolicyError("Windows installer policy shape is invalid")
        if (value["schemaVersion"], value["claimState"], value["mode"]) != (
            "makers-anvil.config.windows-installer.v1", "staged", "read-only-installer-foundation",
        ):
            raise WindowsInstallerPolicyError("Windows installer policy identity is invalid")
        if value["platform"] != {"operatingSystem": "windows", "architecture": "x64", "minimumVersion": "10-2004"}:
            raise WindowsInstallerPolicyError("Windows installer platform is invalid")
        if value["package"] != {
            "format": "msix", "payloadArtifact": "artifacts/windows/MakersAnvil.exe",
            "installerArtifact": "artifacts/windows/MakersAnvil.msix", "scope": "per-user",
            "elevationRequired": False, "installLocation": "windows-managed-package-location",
        }:
            raise WindowsInstallerPolicyError("Windows installer package contract is invalid")
        self._validate_identity(value["identity"])
        self._validate_runtime(value["runtime"])
        self._validate_preservation(value["upgrade"], value["removal"])
        self._validate_signing(value["signing"])
        if not isinstance(value["actions"], dict) or {key for key, enabled in value["actions"].items() if enabled} != TRUE_ACTIONS:
            raise WindowsInstallerPolicyError("Windows installer actions are invalid")
        if not isinstance(value["safety"], dict) or not value["safety"] or any(value["safety"].values()):
            raise WindowsInstallerPolicyError("Windows installer safety effects must remain false")
        return value

    def readiness(self) -> dict[str, Any]:
        """Purpose: Expose nine deterministic gates separating foundation from a release.

        Inputs: Valid installer policy only; no live installer or registry state is inspected.
        Outputs: Three passed planning gates, six blocked proof gates, and false readiness.
        How it works: Builds fixed gate evidence from closed policy facts and absent proof.
        Side effects: Reads policy JSON only.
        Failure behavior: Invalid policy raises instead of reducing required gate coverage.
        Safety: Gate text cannot execute, build, sign, install, remove, or publish anything.
        Example: Package format selection passes while trusted signing remains blocked.
        Related proof: Exact-gate, API consistency, and schema tests.
        """

        policy = self.policy()
        gates = [
            self._gate("target-platform", "Windows x64 target", True, "Windows 10 2004 or later and x64 are fixed."),
            self._gate("package-format", "MSIX format selected", True, "MSIX is the reviewed Windows package target."),
            self._gate("portable-payload", "Portable payload contract", True, "The payload has no source-checkout or working-directory dependency."),
            self._gate("package-identity", "Package identity locked", False, "Publisher identity is not proven or locked."),
            self._gate("installer-built", "Installer package built", False, "No MakersAnvil.msix artifact has been built."),
            self._gate("trusted-signature", "Trusted signature", False, "No certificate, publisher match, signature, or timestamp is proven."),
            self._gate("upgrade-proof", "Upgrade preserves data", False, "No installer upgrade scenario has run."),
            self._gate("removal-proof", "Removal preserves data", False, "No installer removal scenario has run."),
            self._gate("clean-machine-proof", "Clean-machine workflow", False, "All clean-machine scenarios remain not run."),
        ]
        passed = sum(gate["passed"] for gate in gates)
        return {
            "schemaVersion": "makers-anvil.api.windows-installer-readiness.v1",
            "claimState": "staged",
            "mode": policy["mode"],
            "summary": {
                "gateCount": len(gates), "passedGateCount": passed, "blockedGateCount": len(gates) - passed,
                "foundationReady": True, "installerReady": False, "releaseReady": False,
            },
            "package": dict(policy["package"]), "identity": dict(policy["identity"]),
            "upgrade": dict(policy["upgrade"]), "removal": dict(policy["removal"]),
            "signing": dict(policy["signing"]), "gates": gates,
            "actions": dict(policy["actions"]), "safety": dict(policy["safety"]),
        }

    def clean_machine_harness(self) -> dict[str, Any]:
        """Purpose: Return the complete clean-machine test plan without running a scenario.

        Inputs: Valid scenario registry and installer policy.
        Outputs: Six ordered not-run scenarios, zero evidence, and false proof state.
        How it works: Validates environment and scenario text, then adds execution-state fields.
        Side effects: Reads two bundled JSON files only.
        Failure behavior: Duplicate, missing, empty, or unsafe scenarios raise.
        Safety: No VM, installer, registry, certificate store, process, network, or deletion is touched.
        Example: Fresh install lists assertions but has executionState ``not-run``.
        Related proof: CLI, schema, no-write, and API tests.
        """

        self.policy()
        value = self._read_json(self.scenarios_path, "clean-machine scenario registry")
        if set(value) != SCENARIO_FIELDS or (value["schemaVersion"], value["claimState"], value["mode"]) != (
            "makers-anvil.config.clean-machine-scenarios.v1", "planned", "declarative-no-execution-harness",
        ):
            raise WindowsInstallerPolicyError("clean-machine scenario registry identity is invalid")
        if value["environment"] != {
            "operatingSystem": "windows", "architecture": "x64", "sourceCheckoutPresent": False,
            "developerToolsRequired": False, "administratorRequired": False, "networkRequired": False,
        }:
            raise WindowsInstallerPolicyError("clean-machine environment contract is invalid")
        scenarios = value["scenarios"]
        if not isinstance(scenarios, list) or [item.get("id") for item in scenarios if isinstance(item, dict)] != list(SCENARIO_IDS):
            raise WindowsInstallerPolicyError("clean-machine scenario coverage is invalid")
        for scenario in scenarios:
            if set(scenario) != {"id", "label", "purpose", "assertions"}:
                raise WindowsInstallerPolicyError("clean-machine scenario shape is invalid")
            if not all(isinstance(scenario[key], str) and scenario[key] for key in ("id", "label", "purpose")):
                raise WindowsInstallerPolicyError("clean-machine scenario text is invalid")
            if not isinstance(scenario["assertions"], list) or not scenario["assertions"] or any(not isinstance(item, str) or not item for item in scenario["assertions"]):
                raise WindowsInstallerPolicyError("clean-machine assertions are invalid")
        if value["actions"] != {"inspectEnabled": True, "executeEnabled": False, "recordEvidenceEnabled": False}:
            raise WindowsInstallerPolicyError("clean-machine harness actions are invalid")
        if not isinstance(value["safety"], dict) or not value["safety"] or any(value["safety"].values()):
            raise WindowsInstallerPolicyError("clean-machine harness safety effects must remain false")
        return {
            "schemaVersion": "makers-anvil.api.clean-machine-harness.v1", "claimState": "planned", "mode": value["mode"],
            "summary": {"scenarioCount": len(scenarios), "executedCount": 0, "passedCount": 0, "failedCount": 0, "cleanMachineProven": False},
            "environment": dict(value["environment"]),
            "scenarios": [{**scenario, "executionState": "not-run", "evidence": []} for scenario in scenarios],
            "actions": dict(value["actions"]), "safety": dict(value["safety"]),
        }

    @staticmethod
    def _read_json(path: Path, label: str) -> dict[str, Any]:
        """Purpose: Parse one required object-shaped JSON contract with a path-free error.

        Inputs: Private bundled path and reviewed public policy label.
        Outputs: Parsed dictionary.
        How it works: Reads UTF-8 text, decodes JSON, and requires an object root.
        Side effects: Reads one file.
        Failure behavior: I/O, syntax, or non-object input becomes one typed policy error.
        Safety: Error messages expose the label, never the resolved machine path.
        Example: A missing scenario file reports that its registry is unavailable.
        Related proof: Missing and malformed policy tests.
        """

        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WindowsInstallerPolicyError(f"{label} is unavailable") from exc
        if not isinstance(value, dict):
            raise WindowsInstallerPolicyError(f"{label} must be an object")
        return value

    @staticmethod
    def _validate_identity(value: Any) -> None:
        """Purpose: Lock provisional identity fields without claiming a real publisher.

        Inputs: Candidate package identity mapping.
        Outputs: ``None`` only for the reviewed provisional identity.
        How it works: Compares the complete mapping to fixed current values.
        Side effects: None.
        Failure behavior: Any identity widening or false lock raises.
        Safety: No certificate name or secret is accepted from callers.
        Example: Changing ``locked`` to true fails until signing evidence exists.
        Related proof: Identity mutation tests.
        """

        expected = {
            "name": "TreadSoftly.MakersAnvil", "displayName": "Makers Anvil", "publisher": "not-proven",
            "publisherDisplayName": "TreadSoftly", "version": "0.1.0.0", "locked": False,
        }
        if value != expected:
            raise WindowsInstallerPolicyError("Windows installer identity is invalid")

    @staticmethod
    def _validate_runtime(value: Any) -> None:
        """Purpose: Require installed runtime behavior to remain source-independent.

        Inputs: Candidate runtime contract.
        Outputs: ``None`` for exact WebView2 and portable user-data requirements.
        How it works: Compares every field to the reviewed package runtime values.
        Side effects: None.
        Failure behavior: Source, working-directory, or install-folder data coupling raises.
        Safety: Prevents one developer machine path from becoming an installer dependency.
        Example: ``sourceCheckoutRequired=true`` fails immediately.
        Related proof: Runtime portability and policy tests.
        """

        expected = {
            "webView2Mode": "evergreen-runtime", "sourceCheckoutRequired": False,
            "workingDirectoryRequired": False, "userDataLocation": "makers-anvil-data://user",
            "userDataInsideInstallLocation": False,
        }
        if value != expected:
            raise WindowsInstallerPolicyError("Windows installer runtime contract is invalid")

    @staticmethod
    def _validate_preservation(upgrade: Any, removal: Any) -> None:
        """Purpose: Lock upgrade and removal behavior to preserve user data.

        Inputs: Candidate upgrade and removal mappings.
        Outputs: ``None`` only when downgrade, purge, and execution remain disabled.
        How it works: Compares both complete records to reviewed preservation values.
        Side effects: None.
        Failure behavior: Missing consent, enabled purge, or enabled execution raises.
        Safety: User data cannot be deleted by this foundation.
        Example: Uninstall execution or user-data purge cannot be enabled in policy.
        Related proof: Preservation mutation tests.
        """

        expected_upgrade = {"sameIdentityRequired": True, "higherVersionRequired": True, "downgradeAllowed": False, "preserveUserData": True, "executionEnabled": False}
        expected_removal = {"preserveUserDataByDefault": True, "explicitPurgeConsentRequired": True, "userDataPurgeEnabled": False, "executionEnabled": False}
        if upgrade != expected_upgrade or removal != expected_removal:
            raise WindowsInstallerPolicyError("Windows installer preservation contract is invalid")

    @staticmethod
    def _validate_signing(value: Any) -> None:
        """Purpose: Require signing while keeping every current signing claim false.

        Inputs: Candidate signing state.
        Outputs: ``None`` for required-but-unselected and unproven signing truth.
        How it works: Compares the complete record to one conservative value set.
        Side effects: None.
        Failure behavior: False certificate, publisher, signature, or timestamp claims raise.
        Safety: No secret, key path, password, or signing command can enter policy.
        Example: Production method remains not-selected until a user decision and proof.
        Related proof: Signing-state tests and installer readiness gates.
        """

        expected = {
            "requiredForInstallation": True, "productionMethod": "not-selected", "certificatePresent": False,
            "publisherMatched": False, "signatureVerified": False, "timestampVerified": False,
        }
        if value != expected:
            raise WindowsInstallerPolicyError("Windows installer signing state is invalid")

    @staticmethod
    def _gate(gate_id: str, label: str, passed: bool, evidence: str) -> dict[str, Any]:
        """Purpose: Construct one stable installer readiness gate.

        Inputs: Reviewed id, label, boolean result, and explanatory evidence.
        Outputs: JSON-shaped gate with honest claim state.
        How it works: Maps true to proven and false to blocked.
        Side effects: None.
        Failure behavior: Inputs are internal constants; caller errors propagate normally.
        Safety: Gate records contain no command, path, secret, or action.
        Example: The trusted-signature gate is blocked with current missing evidence.
        Related proof: Exact gate ordering and count tests.
        """

        return {"id": gate_id, "label": label, "claimState": "proven" if passed else "blocked", "passed": passed, "evidence": evidence}


__all__ = ["SCENARIO_IDS", "WindowsInstallerPolicyError", "WindowsInstallerService"]
