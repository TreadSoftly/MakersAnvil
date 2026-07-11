"""Purpose: Build path-free external-tool launch confirmation previews.

Used by: ``AppStateService`` and the read-only tool launch preview API.
Inputs: Strict launch policy plus one coherent tool-detection snapshot.
Outputs: Per-tool version-bound review records with confirmation still unaccepted.
Side effects: Reads policy/detection state only; never persists consent or launches.
Safety: Commands, arguments, selected files, paths, and processes remain absent.
Failure behavior: Weakened policy fails closed; missing evidence blocks review readiness.
Related proof: ``tests/test_tool_launch.py`` and tool-launch schemas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.tool_detection import ToolDetectionService


ROOT = application_root()
POLICY_TOP_LEVEL_FIELDS = {"schemaVersion", "claimState", "mode", "scope", "confirmation", "actions", "safety"}
POLICY_SCOPE = {
    "launchMode": "tool-only",
    "requireDetectedTool": True,
    "requireVersionProof": True,
    "selectedFileAllowed": False,
    "argumentsAllowed": False,
}
POLICY_CONFIRMATION = {
    "required": True,
    "accepted": False,
    "persisted": False,
    "endpointEnabled": False,
}
POLICY_ACTIONS = {
    "reviewEnabledInApi": True,
    "confirmEnabledInApi": False,
    "launchEnabledInApi": False,
}
POLICY_SAFETY = {
    "processExecuted": False,
    "toolLaunched": False,
    "commandConstructed": False,
    "argumentsConstructed": False,
    "selectedFileHandedOff": False,
    "absolutePathExposed": False,
    "filesystemWritten": False,
    "confirmationPersisted": False,
}
VERSION_EVIDENCE_METHODS = {"windows-version-resource", "macos-bundle-info"}
VERSION_VALUE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+\-]{0,63}$")


class ToolLaunchError(ValueError):
    """Purpose: Signal a launch-review policy or snapshot contract violation.

    Inputs: A stable explanation passed by the validating service.
    Outputs: A typed exception that prevents weakened preview state from rendering.
    How it works: Inherits normal ``ValueError`` construction and propagation.
    Side effects: None beyond interrupting the invalid request.
    Failure behavior: Callers must surface failure rather than infer readiness.
    Safety: Fail-closed errors cannot trigger confirmation, commands, or processes.
    Example: ``raise ToolLaunchError("tool launch policy is weakened")``.
    Related proof: ``tests/test_tool_launch.py``.
    """


class ToolLaunchService:
    """Purpose: Compose version-bound tool-only confirmation review records.

    Inputs: Repository root and optional shared ``ToolDetectionService``.
    Outputs: Strict launch-review policy and read-only per-tool preview catalog.
    How it works: Validates constant-false effects, then joins detection/version truth.
    Side effects: Reads one JSON policy and detection metadata; writes nothing.
    Failure behavior: Bad policy raises; absent tool/version evidence becomes blocked.
    Safety: No executable target escapes the detector and no launch API is enabled.
    Example: A detected versioned Blender becomes review-ready but not launchable.
    Related proof: ``tests/test_tool_launch.py`` and ``schemas/tool-launch-catalog.schema.json``.
    """

    def __init__(
        self,
        root: Path | None = None,
        tool_detection: ToolDetectionService | None = None,
    ) -> None:
        """Purpose: Capture portable policy location and the shared detector.

        Inputs: Optional application root and injected detection service.
        Outputs: Initialized service state; constructors return ``None``.
        How it works: Resolves bundled resources through the existing root helper.
        Side effects: None until a policy or catalog method is called.
        Failure behavior: Invalid roots fail later through ordinary bounded file reads.
        Safety: Construction performs no lookup, metadata read, persistence, or launch.
        Example: ``ToolLaunchService(root=tmp_path, tool_detection=fake_detector)``.
        Related proof: ``tests/test_tool_launch.py``.
        """

        self.root = root or ROOT
        self.tool_detection = tool_detection or ToolDetectionService(self.root)
        self.policy_path = self.root / "config" / "tool_launch_policy.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load and strictly validate the confirmation-preview boundary.

        Inputs: Committed ``config/tool_launch_policy.json``.
        Outputs: Valid policy mapping whose execution-side effects are all false.
        How it works: Compares exact top-level, scope, confirmation, action, and safety fields.
        Side effects: Reads one UTF-8 JSON file only.
        Failure behavior: Malformed or weakened policy raises ``ToolLaunchError``.
        Safety: Exact equality prevents a config edit from silently enabling launch.
        Example: Setting ``launchEnabledInApi`` true causes catalog generation to fail.
        Related proof: ``tests/test_tool_launch.py`` and policy schema.
        """

        try:
            policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ToolLaunchError("tool launch policy could not be loaded") from exc
        if not isinstance(policy, dict) or set(policy) != POLICY_TOP_LEVEL_FIELDS:
            raise ToolLaunchError("tool launch policy fields are not supported")
        if policy.get("schemaVersion") != "makers-anvil.config.tool-launch-policy.v1":
            raise ToolLaunchError("tool launch policy schema version is not supported")
        if policy.get("claimState") != "staged" or policy.get("mode") != "confirmation-preview-only":
            raise ToolLaunchError("tool launch policy must remain preview-only")
        if policy.get("scope") != POLICY_SCOPE:
            raise ToolLaunchError("tool launch scope must remain detected, versioned, and tool-only")
        if policy.get("confirmation") != POLICY_CONFIRMATION:
            raise ToolLaunchError("tool launch confirmation must remain required and unaccepted")
        if policy.get("actions") != POLICY_ACTIONS:
            raise ToolLaunchError("tool launch actions must keep confirmation and launch disabled")
        if policy.get("safety") != POLICY_SAFETY:
            raise ToolLaunchError("tool launch safety effects must remain false")
        return policy

    def catalog(self, tool_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        """Purpose: Return one review record per allowlisted detected-tool entry.

        Inputs: Optional coherent tool-detection snapshot; otherwise live detection.
        Outputs: Version-bound previews, blockers, read action, and false effects.
        How it works: Requires detected plus proven version evidence for review readiness.
        Side effects: May perform the detector's bounded metadata reads; writes nothing.
        Failure behavior: Invalid snapshots raise; missing evidence yields blocked entries.
        Safety: Binding includes no path, selected file, arguments, command, or consent.
        Example: Missing Cura yields ``reviewReady: false`` with an explicit blocker.
        Related proof: ``tests/test_tool_launch.py`` and API/schema tests.
        """

        policy = self.policy()
        detection = tool_snapshot if tool_snapshot is not None else self.tool_detection.detection_catalog()
        tools = detection.get("tools") if isinstance(detection, dict) else None
        if not isinstance(tools, list) or not all(isinstance(tool, dict) for tool in tools):
            raise ToolLaunchError("tool detection snapshot is invalid")

        previews = [self._tool_preview(tool, policy) for tool in tools]
        review_ready_count = sum(preview["reviewReady"] for preview in previews)
        return {
            "schemaVersion": "makers-anvil.api.tool-launch-catalog.v1",
            "claimState": "preview-only" if review_ready_count else "blocked",
            "mode": policy["mode"],
            "summary": {
                "toolCount": len(previews),
                "reviewReadyCount": review_ready_count,
                "blockedCount": len(previews) - review_ready_count,
            },
            "tools": previews,
            "actions": {
                "review": {
                    "claimState": "preview-only",
                    "enabledInApi": True,
                    "method": "GET",
                    "endpoint": "/api/tools/launches/preview",
                },
                "confirm": {"claimState": "blocked", "enabledInApi": False},
                "launch": {"claimState": "blocked", "enabledInApi": False},
            },
            "safety": policy["safety"],
        }

    @staticmethod
    def _tool_preview(tool: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Join one detected tool to one unaccepted confirmation binding.

        Inputs: Tool-detection entry and already validated launch policy.
        Outputs: Path-free review-ready or blocked preview record.
        How it works: Checks installed/version proof and appends mandatory blockers.
        Side effects: None; it only transforms in-memory mappings.
        Failure behavior: Missing required identity fields raise ``ToolLaunchError``.
        Safety: Mandatory blockers keep confirmation and process launch impossible.
        Example: Proven Blender metadata binds id, executable name, and version only.
        Related proof: ``tests/test_tool_launch.py``.
        """

        tool_id = tool.get("id")
        label = tool.get("label")
        detection = tool.get("detection")
        version = tool.get("version")
        if not isinstance(tool_id, str) or not tool_id or not isinstance(label, str) or not label:
            raise ToolLaunchError("tool launch previews require stable tool identity")
        if not isinstance(detection, dict) or not isinstance(version, dict):
            raise ToolLaunchError("tool launch previews require detection and version records")

        installed = detection.get("installed") is True
        executable_name = detection.get("executableName")
        if installed and (not isinstance(executable_name, str) or not executable_name):
            raise ToolLaunchError("detected tool launch previews require an executable name")
        version_value = version.get("value")
        evidence_method = version.get("evidenceMethod")
        version_proven = (
            version.get("claimState") == "proven"
            and isinstance(version_value, str)
            and VERSION_VALUE.fullmatch(version_value) is not None
            and evidence_method in VERSION_EVIDENCE_METHODS
        )
        review_ready = installed and version_proven
        blockers: list[str] = []
        if not installed:
            blockers.append("The allowlisted tool executable is not detected on this device.")
        if not version_proven:
            blockers.append("A metadata-only tool version is not proven on this device.")
        blockers.extend(
            [
                "Version metadata does not prove publisher signature or executable trust.",
                "Explicit launch confirmation has not been accepted or persisted.",
                "External tool process launch is not enabled in the API.",
            ]
        )
        return {
            "id": tool_id,
            "label": label,
            "claimState": "preview-only" if review_ready else "blocked",
            "reviewReady": review_ready,
            "binding": {
                "toolId": tool_id,
                "executableName": executable_name if installed else None,
                "version": version_value if version_proven else None,
                "versionEvidenceMethod": evidence_method if version_proven else "none",
                "launchMode": policy["scope"]["launchMode"],
                "selectedFileIncluded": False,
                "argumentsIncluded": False,
                "absolutePathExposed": False,
            },
            "confirmation": dict(policy["confirmation"]),
            "blockedReasons": blockers,
        }
