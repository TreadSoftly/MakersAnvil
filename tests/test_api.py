"""Executable examples for the read-only HTTP-style API contract."""

from makers_anvil_backend.api.app import MakersAnvilApi


def test_health_is_read_only_and_proven() -> None:
    """Health identifies a proven read-only service with mutations disabled."""

    response = MakersAnvilApi().handle("GET", "/api/health")

    assert response.status == 200
    assert response.body["claimState"] == "proven"
    assert response.body["mutatingActionsEnabled"] is False


def test_state_keeps_actions_blocked() -> None:
    """Dashboard state reports current progress without enabling capabilities."""

    response = MakersAnvilApi().handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["completion"]["realApp"] == 22.5
    assert response.body["currentPass"]["id"] == "PASS-009"
    assert response.body["completion"]["packagedRelease"] == 0.0
    assert response.body["completion"]["cleanMachineProof"] == 0.0
    assert all(not capability["actionsEnabled"] for capability in response.body["capabilities"])
    assert "route execution" in response.body["blockedActions"]


def test_mutating_requests_are_blocked() -> None:
    """Every POST request receives the shared blocked response."""

    response = MakersAnvilApi().handle("POST", "/api/state")

    assert response.status == 405
    assert response.body["claimState"] == "blocked"


def test_unknown_read_route_is_not_proven() -> None:
    """Unknown GET routes return a not-proven record instead of invented data."""

    response = MakersAnvilApi().handle("GET", "/api/unknown")

    assert response.status == 404
    assert response.body["claimState"] == "not proven"


def test_workspace_status_endpoints_are_read_only_truth() -> None:
    """Workspace and ledger endpoints mirror committed durable status files."""

    api = MakersAnvilApi()
    workspace = api.handle("GET", "/api/workspace/status")
    ledger = api.handle("GET", "/api/passes/ledger")

    assert workspace.status == 200
    assert workspace.body["currentPass"]["id"] == "PASS-009"
    assert workspace.body["sourceTruth"]["statusPath"] == "state/current_status.json"
    assert workspace.body["referencePolicy"]["runtimeDependency"] is False
    assert ledger.status == 200
    assert ledger.body["passes"][-1]["id"] == "PASS-009"


def test_workspace_config_keeps_unsafe_actions_disabled() -> None:
    """Workspace APIs expose portable policy while withholding absolute paths."""

    api = MakersAnvilApi()
    config = api.handle("GET", "/api/workspace/config")
    layout = api.handle("GET", "/api/workspace/layout")

    assert config.status == 200
    runtime_location = config.body["runtimeLocation"]
    assert runtime_location["mode"] == "platform-user-data"
    assert runtime_location["sourceRootDependency"] is False
    assert runtime_location["absolutePathExposed"] is False
    assert "runtimeRoot" not in config.body
    assert all(value is False for value in config.body["safety"].values())
    assert layout.status == 200
    assert layout.body["runtimeLocation"]["logicalRoot"] == "makers-anvil-data://user"
    assert all(not item["relativePath"].startswith(("/", "\\")) for item in layout.body["directories"])
    assert layout.body["creationAction"]["enabledInApi"] is False
    assert layout.body["creationAction"]["script"] == "python scripts/init_workspace.py"


def test_intake_endpoints_are_metadata_only_and_read_only() -> None:
    """Intake APIs expose metadata policy and never enable upload or mutation."""

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/intake/policy")
    catalog = api.handle("GET", "/api/intake/catalog")

    assert policy.status == 200
    assert policy.body["mode"] == "metadata-only"
    assert all(value is False for value in policy.body["safety"].values())
    assert catalog.status == 200
    assert catalog.body["creationAction"]["enabledInApi"] is False
    assert catalog.body["safety"]["sourcePathStored"] is False
    assert catalog.body["safety"]["sourceContentStored"] is False
    assert catalog.body["recordsPath"] == "makers-anvil-data://user/intake/records"


def test_route_preview_is_metadata_derived_and_non_executing() -> None:
    """Route preview exposes planning state while every source and action gate stays false."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/routes/preview")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["claimState"] in {"preview-only", "failed"}
    assert response.body["mode"] == "metadata-derived-read-only"
    assert all(value is False for value in response.body["safety"].values())
    assert response.body["executionAction"] == {"claimState": "blocked", "enabledInApi": False}
    assert state.body["routePreview"]["schemaVersion"] == "makers-anvil.api.route-preview.v1"


def test_output_preview_has_no_files_or_completed_proof() -> None:
    """Output preview exposes plans while creation, opening, and proof stay blocked."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/outputs/preview")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["claimState"] in {"preview-only", "failed"}
    assert response.body["mode"] == "route-derived-read-only"
    assert response.body["logicalRoot"] == "makers-anvil-data://user/outputs"
    assert response.body["summary"]["completedProofCount"] == 0
    assert all(value is False for value in response.body["safety"].values())
    assert all(action["enabledInApi"] is False for action in response.body["actions"].values())
    assert state.body["outputProof"]["schemaVersion"] == "makers-anvil.api.output-proof.v1"


def test_tool_detection_is_path_redacted_and_non_executing() -> None:
    """Tool detection reports presence evidence without versions, paths, or actions."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/tools/detection")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["mode"] == "read-only-presence"
    assert response.body["summary"]["toolCount"] == 6
    assert all(value is False for value in response.body["safety"].values())
    assert all(action["enabledInApi"] is False for action in response.body["actions"].values())
    assert all(tool["detection"]["absolutePathExposed"] is False for tool in response.body["tools"])
    assert all(tool["version"]["claimState"] == "not proven" for tool in response.body["tools"])
    assert all(tool["actionsEnabled"] is False for tool in response.body["tools"])
    assert state.body["toolDetection"]["schemaVersion"] == "makers-anvil.api.tool-detection.v1"
