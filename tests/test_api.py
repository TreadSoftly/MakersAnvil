from makers_anvil_backend.api.app import MakersAnvilApi


def test_health_is_read_only_and_proven() -> None:
    response = MakersAnvilApi().handle("GET", "/api/health")

    assert response.status == 200
    assert response.body["claimState"] == "proven"
    assert response.body["mutatingActionsEnabled"] is False


def test_state_keeps_actions_blocked() -> None:
    response = MakersAnvilApi().handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["completion"]["realApp"] == 5.0
    assert response.body["currentPass"]["id"] == "PASS-002"
    assert response.body["completion"]["packagedRelease"] == 0.0
    assert response.body["completion"]["cleanMachineProof"] == 0.0
    assert all(not capability["actionsEnabled"] for capability in response.body["capabilities"])
    assert "route execution" in response.body["blockedActions"]


def test_mutating_requests_are_blocked() -> None:
    response = MakersAnvilApi().handle("POST", "/api/state")

    assert response.status == 405
    assert response.body["claimState"] == "blocked"


def test_unknown_read_route_is_not_proven() -> None:
    response = MakersAnvilApi().handle("GET", "/api/unknown")

    assert response.status == 404
    assert response.body["claimState"] == "not proven"


def test_workspace_status_endpoints_are_read_only_truth() -> None:
    api = MakersAnvilApi()
    workspace = api.handle("GET", "/api/workspace/status")
    ledger = api.handle("GET", "/api/passes/ledger")

    assert workspace.status == 200
    assert workspace.body["currentPass"]["id"] == "PASS-002"
    assert workspace.body["sourceTruth"]["statusPath"] == "state/current_status.json"
    assert workspace.body["referencePolicy"]["runtimeDependency"] is False
    assert ledger.status == 200
    assert ledger.body["passes"][-1]["id"] == "PASS-002"
