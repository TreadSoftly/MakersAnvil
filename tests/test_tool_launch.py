"""Purpose: Prove version-bound tool launch reviews while execution stays absent.

Used by: Developers and CI when launch policy, binding, or blockers change.
Inputs: Isolated policy plus injected path-redacted detection snapshots.
Outputs: Assertions for readiness, confirmation truth, redaction, and fail-closed policy.
Side effects: Writes only pytest temporary config fixtures; starts no process.
Safety: Confirmation, commands, arguments, selected files, and launch remain false.
Failure behavior: Weakened policy raises and missing evidence remains blocked.
Related proof: ``services/tool_launch.py`` and tool-launch schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.tool_launch import ToolLaunchError, ToolLaunchService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_service(tmp_path: Path) -> ToolLaunchService:
    """Purpose: Create an isolated launch-review service with committed policy.

    Inputs: Pytest temporary directory.
    Outputs: ``ToolLaunchService`` rooted at an isolated config tree.
    How it works: Copies only the declarative policy needed by this focused service.
    Side effects: Creates one temporary config file.
    Failure behavior: Filesystem errors propagate and fail the test setup.
    Safety: No real detector or installed executable is consulted.
    Example: ``service = build_service(tmp_path)``.
    Related proof: ``config/tool_launch_policy.json``.
    """

    config = tmp_path / "config"
    config.mkdir()
    config.joinpath("tool_launch_policy.json").write_text(
        PROJECT_ROOT.joinpath("config", "tool_launch_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return ToolLaunchService(root=tmp_path)


def detection_snapshot(*, installed: bool = True, version_proven: bool = True) -> dict:
    """Purpose: Build one minimal path-free detector result for launch-review tests.

    Inputs: Booleans selecting presence and version evidence states.
    Outputs: Detection snapshot containing one allowlisted Blender entry.
    How it works: Uses exact public fields consumed by ``ToolLaunchService``.
    Side effects: None.
    Failure behavior: Invalid combinations are intentionally represented as blocked evidence.
    Safety: No private path, command, selected file, or executable bytes exist.
    Example: ``detection_snapshot(version_proven=False)`` exercises version gating.
    Related proof: ``schemas/tool-detection.schema.json``.
    """

    return {
        "tools": [
            {
                "id": "blender",
                "label": "Blender",
                "detection": {
                    "installed": installed,
                    "executableName": "blender.exe" if installed else None,
                },
                "version": {
                    "claimState": "proven" if version_proven else "not proven",
                    "value": "4.5.0.0" if version_proven else None,
                    "evidenceMethod": "windows-version-resource" if version_proven else "none",
                },
            }
        ]
    }


def test_versioned_detected_tool_is_review_ready_but_not_launchable(tmp_path: Path) -> None:
    """Purpose: Prove version evidence enables review only, never confirmation or launch.

    Inputs: Isolated strict policy and one detected versioned Blender snapshot.
    Outputs: Assertions for binding, review readiness, blockers, actions, and effects.
    How it works: Generates the catalog and checks every execution boundary directly.
    Side effects: Reads one temporary policy file only.
    Failure behavior: Any enabled confirm/launch/effect fails the test.
    Safety: The binding explicitly excludes path, selected file, and arguments.
    Example: Blender ``4.5.0.0`` can be reviewed while process execution stays false.
    Related proof: ``services/tool_launch.py`` and launch catalog schema.
    """

    catalog = build_service(tmp_path).catalog(detection_snapshot())
    preview = catalog["tools"][0]

    assert catalog["claimState"] == "preview-only"
    assert catalog["summary"] == {"toolCount": 1, "reviewReadyCount": 1, "blockedCount": 0}
    assert preview["reviewReady"] is True
    assert preview["binding"] == {
        "toolId": "blender",
        "executableName": "blender.exe",
        "version": "4.5.0.0",
        "versionEvidenceMethod": "windows-version-resource",
        "launchMode": "tool-only",
        "selectedFileIncluded": False,
        "argumentsIncluded": False,
        "absolutePathExposed": False,
    }
    assert preview["confirmation"]["accepted"] is False
    assert any("publisher signature" in reason for reason in preview["blockedReasons"])
    assert catalog["actions"]["review"]["enabledInApi"] is True
    assert catalog["actions"]["confirm"]["enabledInApi"] is False
    assert catalog["actions"]["launch"]["enabledInApi"] is False
    assert all(value is False for value in catalog["safety"].values())


def test_missing_version_blocks_review_without_guessing(tmp_path: Path) -> None:
    """Purpose: Ensure presence alone cannot satisfy launch-review prerequisites.

    Inputs: Detected Blender snapshot with no version evidence.
    Outputs: Assertions for blocked state, null version, and explicit reason.
    How it works: Generates the catalog and inspects the one preview record.
    Side effects: Reads one temporary policy file only.
    Failure behavior: Review readiness or a non-null version fails the test.
    Safety: No version is inferred from executable name or tool label.
    Example: ``blender.exe`` alone remains blocked.
    Related proof: ``services/tool_launch.py``.
    """

    preview = build_service(tmp_path).catalog(detection_snapshot(version_proven=False))["tools"][0]

    assert preview["claimState"] == "blocked"
    assert preview["reviewReady"] is False
    assert preview["binding"]["version"] is None
    assert any("version is not proven" in reason for reason in preview["blockedReasons"])


def test_malformed_version_evidence_cannot_make_review_ready(tmp_path: Path) -> None:
    """Purpose: Ensure injected free text or an unknown method cannot satisfy review gates.

    Inputs: Detected snapshot changed to an unsafe version value and evidence method.
    Outputs: Assertions for blocked readiness and null public version binding.
    How it works: Mutates only the test snapshot before catalog composition.
    Side effects: Reads one temporary policy file only.
    Failure behavior: Review readiness means the launch service trusted malformed evidence.
    Safety: The service independently revalidates detector output before launch review.
    Example: ``../../private`` from ``path-name-guess`` remains blocked.
    Related proof: ``services/tool_launch.py``.
    """

    snapshot = detection_snapshot()
    snapshot["tools"][0]["version"].update({"value": "../../private", "evidenceMethod": "path-name-guess"})

    preview = build_service(tmp_path).catalog(snapshot)["tools"][0]

    assert preview["reviewReady"] is False
    assert preview["binding"]["version"] is None
    assert preview["binding"]["versionEvidenceMethod"] == "none"


def test_weakened_launch_policy_fails_closed(tmp_path: Path) -> None:
    """Purpose: Prove a config edit cannot silently enable the launch endpoint.

    Inputs: Isolated policy changed to set ``launchEnabledInApi`` true.
    Outputs: Typed ``ToolLaunchError`` assertion.
    How it works: Mutates only the fixture then asks the service to validate it.
    Side effects: Rewrites one temporary JSON file.
    Failure behavior: Returning a catalog means the exact policy guard regressed.
    Safety: Failure occurs before detection, confirmation, command, or process work.
    Example: A true launch flag is rejected with an action-boundary error.
    Related proof: ``services/tool_launch.py`` and policy schema.
    """

    service = build_service(tmp_path)
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["actions"]["launchEnabledInApi"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ToolLaunchError, match="confirmation and launch disabled"):
        service.catalog(detection_snapshot())
