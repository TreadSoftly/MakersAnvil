"""Purpose: Explain and prove the complete read-only API surface.

Used by: Developers and CI whenever services, routes, or response contracts change.
Inputs: Isolated app state and HTTP-style method/path calls.
Outputs: Assertions over status codes, JSON shapes, joins, and blocked mutations.
Side effects: Uses temporary runtime directories; never touches user data.
Safety: Every mutating method and unsupported route must fail closed.
Failure behavior: A changed or weakened API contract fails the named example.
Related proof: ``backend/.../api/app.py`` and public response schemas.
"""

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
    assert response.body["completion"]["realApp"] == 32.5
    assert response.body["currentPass"]["id"] == "PASS-014"
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
    assert workspace.body["currentPass"]["id"] == "PASS-014"
    assert workspace.body["sourceTruth"]["statusPath"] == "state/current_status.json"
    assert workspace.body["referencePolicy"]["runtimeDependency"] is False
    assert ledger.status == 200
    assert ledger.body["passes"][-1]["id"] == "PASS-014"


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


def test_tool_dry_run_is_semantic_only_and_execution_blocked() -> None:
    """Tool dry runs expose no command, resolved path, handoff, process, or write action."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/tools/dry-run")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["mode"] == "semantic-invocation-read-only"
    assert all(value is False for value in response.body["safety"].values())
    assert response.body["executionAction"] == {"claimState": "blocked", "enabledInApi": False}
    assert all(plan["invocation"]["commandString"] is None for plan in response.body["plans"])
    assert all(plan["readiness"]["executionReady"] is False for plan in response.body["plans"])
    assert state.body["toolDryRun"]["schemaVersion"] == "makers-anvil.api.tool-dry-run.v1"


def test_execution_gates_allowlist_one_route_but_enable_nothing() -> None:
    """Execution gates expose required evidence without authorizing or creating a job."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/execution/gates")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["mode"] == "read-only-gate-evaluation"
    assert response.body["scope"]["routeId"] == "mesh-to-toolpath"
    assert response.body["scope"]["singleRoute"] is True
    assert response.body["scope"]["maxConcurrentExecutions"] == 1
    assert response.body["scope"]["executionEnabled"] is False
    assert all(value is False for value in response.body["safety"].values())
    assert response.body["executionAction"] == {"claimState": "blocked", "enabledInApi": False}
    assert all(item["readiness"]["executionReady"] is False for item in response.body["evaluations"])
    assert state.body["executionGates"]["schemaVersion"] == "makers-anvil.api.execution-gates.v1"


def test_execution_request_preview_records_no_intent_authorization_or_audit_event() -> None:
    """Request preview exposes the disabled contract without creating any runtime record."""

    api = MakersAnvilApi()
    response = api.handle("GET", "/api/execution/requests/preview")
    state = api.handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["mode"] == "read-only-request-preview"
    assert response.body["scope"]["routeId"] == "mesh-to-toolpath"
    assert response.body["summary"]["persistedRequestCount"] == 0
    assert response.body["summary"]["acceptedAuthorizationCount"] == 0
    assert response.body["summary"]["writtenAuditEventCount"] == 0
    assert response.body["summary"]["executionReadyCount"] == 0
    assert all(value is False for value in response.body["safety"].values())
    assert all(action["enabledInApi"] is False for action in response.body["actions"].values())
    assert state.body["executionRequestPreview"]["schemaVersion"] == "makers-anvil.api.execution-request-preview.v1"


def test_job_catalog_is_path_redacted_and_http_mutations_remain_blocked() -> None:
    """Job APIs expose contained local-script state without enabling browser writes."""

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/jobs/policy")
    catalog = api.handle("GET", "/api/jobs/catalog")
    state = api.handle("GET", "/api/state")

    assert policy.status == 200
    assert policy.body["mode"] == "contained-local-preparation"
    assert policy.body["jobsPath"] == "makers-anvil-data://user/jobs"
    assert policy.body["localActions"] == {
        "preparationEnabled": True,
        "cancellationRequestEnabled": True,
        "apiMutationEnabled": False,
        "browserMutationEnabled": False,
    }
    assert catalog.status == 200
    assert catalog.body["summary"]["executionReadyCount"] == 0
    assert all(value is False for value in catalog.body["safety"].values())
    assert all(action["enabledInApi"] is False for action in catalog.body["actions"].values())
    assert state.body["jobWorkspaceCatalog"]["schemaVersion"] == "makers-anvil.api.job-workspace-catalog.v1"
    assert api.handle("POST", "/api/jobs/catalog").status == 405
