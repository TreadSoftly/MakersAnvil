"""Purpose: Explain and prove read APIs plus bounded intake/settings mutations.

Used by: Developers and CI whenever services, routes, or response contracts change.
Inputs: Isolated app state and HTTP-style method/path calls.
Outputs: Assertions over status codes, JSON shapes, joins, and blocked mutations.
Side effects: Uses temporary runtime directories; never touches user data.
Safety: Only guarded intake and preferences may mutate; all other routes fail closed.
Failure behavior: A changed or weakened API contract fails the named example.
Related proof: ``backend/.../api/app.py`` and public response schemas.
"""

from makers_anvil_backend.api.app import MakersAnvilApi


def test_health_exposes_only_bounded_local_mutations() -> None:
    """Purpose: Health identifies guarded intake/settings and blocked execution.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_health_exposes_only_bounded_intake_mutation``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    response = MakersAnvilApi().handle("GET", "/api/health")

    assert response.status == 200
    assert response.body["claimState"] == "proven"
    assert response.body["mutatingActionsEnabled"] is True
    assert response.body["enabledMutationScopes"] == ["authorized-file-intake", "contained-stl-preflight", "workbench-preferences"]
    assert response.body["builtInStlPreflightEnabled"] is True
    assert response.body["authorizedRasterPreviewEnabled"] is True
    assert response.body["containedArtifactViewerEnabled"] is True
    assert response.body["containedExecutionHistoryEnabled"] is True
    assert response.body["cooperativeCancellationUiEnabled"] is True
    assert response.body["windowsInstallerFoundationEnabled"] is True
    assert response.body["cleanMachineExecutionEnabled"] is False
    assert response.body["routeExecutionEnabled"] is False
    assert response.body["toolLaunchEnabled"] is False


def test_state_limits_actions_to_intake_and_preferences() -> None:
    """Purpose: Dashboard state enables only guarded intake and preferences.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_state_limits_actions_to_file_intake``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    response = MakersAnvilApi().handle("GET", "/api/state")

    assert response.status == 200
    assert response.body["completion"]["realApp"] == 87.5
    assert response.body["currentPass"]["id"] == "PASS-026"
    assert response.body["completion"]["packagedRelease"] == 30.0
    assert response.body["completion"]["cleanMachineProof"] == 5.0
    enabled_capabilities = [capability["id"] for capability in response.body["capabilities"] if capability["actionsEnabled"]]
    assert enabled_capabilities == ["file-intake", "workbench-preferences", "contained-stl-preflight"]
    assert any("full route execution" in action for action in response.body["blockedActions"])


def test_contained_execution_reads_expose_one_partial_operation_only() -> None:
    """Purpose: Prove public execution reads expose one bounded built-in operation.

    Inputs: Default composed API and exact policy/catalog GET routes.
    Outputs: Scope, action, safety, empty-state, and state-composition assertions.
    How it works: Reads all three contracts and compares their shared catalog.
    Side effects: Reads app-owned execution storage only.
    Failure behavior: Scope widening, path exposure, or missing composition fails.
    Safety: Full route, process, tool, software, and output-open effects stay false.
    Example: Fresh data has zero executions but authorization remains available.
    Related proof: Contained execution schemas and service tests.
    """

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/executions/policy")
    catalog = api.handle("GET", "/api/executions/catalog")
    state = api.handle("GET", "/api/state")

    assert policy.status == 200
    assert policy.body["scope"]["operationId"] == "built-in-stl-preflight"
    assert policy.body["scope"]["allowedExtensions"] == [".stl"]
    assert all(value is False for value in policy.body["safety"].values())
    assert catalog.status == 200
    assert catalog.body["actions"]["run"]["enabledInApi"] is True
    assert catalog.body["actions"]["viewArtifact"]["allowedKinds"] == ["report", "proof"]
    assert catalog.body["actions"]["openOutput"]["enabledInApi"] is False
    assert state.body["containedExecutions"] == catalog.body
    assert state.body["containedExecutions"]["executionsPath"] == "makers-anvil-data://user/executions"


def test_lifecycle_reads_expose_five_non_mutating_preservation_plans() -> None:
    """Purpose: Prove lifecycle APIs expose complete planning without executable effects.

    Inputs: Default composed API and exact lifecycle policy/catalog/state GET routes.
    Outputs: Five-operation coverage, zero readiness, privacy, preservation, and consistency assertions.
    How it works: Reads all contracts and compares the focused catalog with app state.
    Side effects: Reads app-owned metadata only and sends no mutation.
    Failure behavior: Missing operations, enabled effects, paths, or state drift fails.
    Safety: No content, archive, network, installer, process, mutation, or deletion occurs.
    Example: Update evidence exposes current version but no available release claim.
    Related proof: Lifecycle service tests and public schemas.
    """

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/lifecycle/policy")
    catalog = api.handle("GET", "/api/lifecycle/dry-runs")
    state = api.handle("GET", "/api/state")

    assert policy.status == 200
    assert [item["id"] for item in policy.body["operations"]] == ["backup", "restore", "update", "uninstall", "repair"]
    assert policy.body["backupTarget"] == "makers-anvil-data://user/backups"
    assert policy.body["executionAction"] == {"claimState": "blocked", "enabledInApi": False}
    assert all(value is False for value in policy.body["safety"].values())
    assert catalog.status == 200
    assert catalog.body["summary"]["operationCount"] == 5
    assert catalog.body["summary"]["previewReadyCount"] == 5
    assert catalog.body["summary"]["executionReadyCount"] == 0
    assert catalog.body["inventory"]["contentRead"] is False
    assert catalog.body["inventory"]["namesExposed"] is False
    assert all(plan["preservation"]["existingDataPreserved"] is True for plan in catalog.body["plans"])
    assert all(plan["preservation"]["userDataDeletionAllowed"] is False for plan in catalog.body["plans"])
    assert all(not any(plan["effects"].values()) for plan in catalog.body["plans"])
    assert state.body["lifecycleDryRuns"] == catalog.body


def test_windows_installer_reads_expose_foundation_without_release_claims() -> None:
    """Purpose: Prove installer APIs distinguish planning, readiness, and machine proof.

    Inputs: Default API and three exact Windows installer GET routes.
    Outputs: MSIX scope, gate counts, zero scenario execution, safety, and state consistency assertions.
    How it works: Reads focused contracts and compares readiness/harness with composed state.
    Side effects: Reads bundled policy files only.
    Failure behavior: Missing routes, enabled effects, false readiness, or state drift fails.
    Safety: No package, signing, registry, process, installation, removal, or deletion occurs.
    Example: Three gates pass while installerReady and cleanMachineProven stay false.
    Related proof: Windows installer service tests and public schemas.
    """

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/windows/installer/policy")
    readiness = api.handle("GET", "/api/windows/installer/readiness")
    harness = api.handle("GET", "/api/windows/clean-machine/harness")
    state = api.handle("GET", "/api/state")

    assert policy.status == 200
    assert policy.body["package"]["format"] == "msix"
    assert policy.body["identity"]["publisher"] == "not-proven"
    assert {key for key, value in policy.body["actions"].items() if value} == {"foundationInspectionEnabled", "harnessInspectionEnabled"}
    assert all(value is False for value in policy.body["safety"].values())
    assert readiness.status == 200
    assert readiness.body["summary"]["gateCount"] == 9
    assert readiness.body["summary"]["passedGateCount"] == 3
    assert readiness.body["summary"]["installerReady"] is False
    assert readiness.body["summary"]["releaseReady"] is False
    assert harness.status == 200
    assert harness.body["summary"]["scenarioCount"] == 6
    assert harness.body["summary"]["executedCount"] == 0
    assert harness.body["summary"]["cleanMachineProven"] is False
    assert state.body["windowsInstaller"] == readiness.body
    assert state.body["cleanMachineHarness"] == harness.body


def test_non_intake_mutating_requests_are_blocked() -> None:
    """Purpose: POST outside authorized intake plus PUT and DELETE remain blocked.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_non_intake_mutating_requests_are_blocked``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    response = MakersAnvilApi().handle("POST", "/api/state")

    assert response.status == 405
    assert response.body["claimState"] == "blocked"


def test_workbench_experience_activity_and_capability_reads_are_path_free() -> None:
    """Purpose: Prove migrated workbench contracts are readable and nonexecuting.

    Inputs: Default composed local API and three exact read routes.
    Outputs: Schema identities, five lanes, help topics, and false safety assertions.
    How it works: Reads public contracts and scans their serialized values for paths.
    Side effects: Reads app-owned settings/activity when present but writes nothing.
    Failure behavior: Missing routes, action widening, or path exposure fails.
    Safety: This test performs GET only and every matrix action remains false.
    Example: Capability matrix returns image, mesh, CAD, toolpath, and document.
    Related proof: Focused service tests and public schemas.
    """

    api = MakersAnvilApi()
    experience = api.handle("GET", "/api/workbench/experience")
    activity = api.handle("GET", "/api/activity/recent")
    matrix = api.handle("GET", "/api/capabilities/matrix")
    assert experience.status == activity.status == matrix.status == 200
    assert len(experience.body["helpTopics"]) == 6
    assert activity.body["safety"]["arbitraryEventAccepted"] is False
    assert matrix.body["summary"]["laneCount"] == 5
    assert all(lane["executionReady"] is False for lane in matrix.body["lanes"])
    assert all(value is False for value in matrix.body["safety"].values())


def test_unknown_read_route_is_not_proven() -> None:
    """Purpose: Unknown GET routes return a not-proven record instead of invented data.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_unknown_read_route_is_not_proven``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    response = MakersAnvilApi().handle("GET", "/api/unknown")

    assert response.status == 404
    assert response.body["claimState"] == "not proven"


def test_workspace_status_endpoints_are_read_only_truth() -> None:
    """Purpose: Workspace and ledger endpoints mirror committed durable status files.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_workspace_status_endpoints_are_read_only_truth``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    api = MakersAnvilApi()
    workspace = api.handle("GET", "/api/workspace/status")
    ledger = api.handle("GET", "/api/passes/ledger")

    assert workspace.status == 200
    assert workspace.body["currentPass"]["id"] == "PASS-026"
    assert workspace.body["sourceTruth"]["statusPath"] == "state/current_status.json"
    assert workspace.body["referencePolicy"]["runtimeDependency"] is False
    assert ledger.status == 200
    assert ledger.body["passes"][-1]["id"] == "PASS-026"


def test_workspace_config_keeps_unsafe_actions_disabled() -> None:
    """Purpose: Workspace APIs expose portable policy while withholding absolute paths.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_workspace_config_keeps_unsafe_actions_disabled``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    api = MakersAnvilApi()
    config = api.handle("GET", "/api/workspace/config")
    layout = api.handle("GET", "/api/workspace/layout")

    assert config.status == 200
    runtime_location = config.body["runtimeLocation"]
    assert runtime_location["mode"] == "platform-user-data"
    assert runtime_location["sourceRootDependency"] is False
    assert runtime_location["absolutePathExposed"] is False
    assert "runtimeRoot" not in config.body
    assert config.body["safety"]["userUploadEnabled"] is True
    assert all(value is False for key, value in config.body["safety"].items() if key != "userUploadEnabled")
    assert layout.status == 200
    assert layout.body["runtimeLocation"]["logicalRoot"] == "makers-anvil-data://user"
    assert all(not item["relativePath"].startswith(("/", "\\")) for item in layout.body["directories"])
    assert layout.body["creationAction"]["enabledInApi"] is False
    assert layout.body["creationAction"]["script"] == "python scripts/init_workspace.py"


def test_intake_endpoints_expose_guarded_authorized_copy_policy() -> None:
    """Purpose: Intake reads expose one-file authorization without path or execution claims.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_intake_endpoints_expose_guarded_authorized_copy_policy``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

    api = MakersAnvilApi()
    policy = api.handle("GET", "/api/intake/policy")
    catalog = api.handle("GET", "/api/intake/catalog")
    session = api.handle("GET", "/api/intake/session")

    assert policy.status == 200
    assert policy.body["mode"] == "authorized-local-copy"
    assert all(value is False for value in policy.body["safety"].values())
    assert catalog.status == 200
    assert catalog.body["creationAction"]["enabledInApi"] is True
    assert catalog.body["creationAction"]["requiresExplicitAuthorization"] is True
    assert catalog.body["safety"]["sourcePathStored"] is False
    assert catalog.body["recordsPath"] == "makers-anvil-data://user/intake/records"
    assert session.status == 200
    assert session.body["mode"] == "same-origin-one-file"
    assert session.body["constraints"]["oneFilePerAuthorization"] is True
    assert ".zip" not in session.body["constraints"]["allowedExtensions"]


def test_route_preview_is_metadata_derived_and_non_executing() -> None:
    """Purpose: Route preview exposes planning state while every source and action gate stays false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_route_preview_is_metadata_derived_and_non_executing``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Output preview exposes plans while creation, opening, and proof stay blocked.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_output_preview_has_no_files_or_completed_proof``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Tool detection reports presence evidence without versions, paths, or actions.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_tool_detection_is_path_redacted_and_non_executing``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Tool dry runs expose no command, resolved path, handoff, process, or write action.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_tool_dry_run_is_semantic_only_and_execution_blocked``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Execution gates expose required evidence without authorizing or creating a job.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_execution_gates_allowlist_one_route_but_enable_nothing``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Request preview exposes the disabled contract without creating any runtime record.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_execution_request_preview_records_no_intent_authorization_or_audit_event``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
    """Purpose: Job APIs expose contained local-script state without enabling browser writes.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Every mutating method and unsupported route must fail closed.
    Example: Run ``python -m pytest tests/test_api.py -k test_job_catalog_is_path_redacted_and_http_mutations_remain_blocked``.
    Related proof: ``backend/.../api/app.py`` and public response schemas.
    """

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
