"""Governance examples that keep product source portable, safe, and current."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reference_folder_is_not_tracked_product_source() -> None:
    """Both known reference-folder spellings remain outside product history."""

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "Refrences For Makers Anvil Application/" in gitignore
    assert "References For Makers Anvil Application/" in gitignore


def test_frontend_has_no_mutating_api_calls() -> None:
    """Browser code may fetch state but cannot call mutation or tool routes."""

    app_js = (ROOT / "frontend" / "public" / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'method: "GET"' in app_js
    assert 'method: "POST"' not in app_js
    assert 'method: "DELETE"' not in app_js
    assert "/api/tools/open" not in app_js


def test_reference_material_names_are_not_runtime_dependencies() -> None:
    """Historical reference-build identifiers cannot leak into product runtime code."""

    product_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".makers-anvil" not in path.parts
        and ".pytest_cache" not in path.parts
        and "Refrences For Makers Anvil Application" not in path.parts
        and "References For Makers Anvil Application" not in path.parts
        and "__pycache__" not in path.parts
    ]

    forbidden = "makers" + "_anvil_build_pass_012_release_backup_uninstall_dry_run"
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in product_files
        if forbidden in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []


def test_durable_status_records_are_current_and_relative() -> None:
    """Current status and pass history agree on the active bounded pass."""

    import json

    current = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))

    assert current["currentPass"]["id"] == "PASS-013"
    assert current["trackPercentages"]["realApp"] == 32.5
    assert current["product"]["sourceRoot"] == "."
    assert current["referencePolicy"]["runtimeDependency"] is False
    assert ledger["passes"][-1]["id"] == "PASS-013"


def test_default_settings_are_safe_and_relative() -> None:
    """Committed defaults preserve user-data portability and disabled actions."""

    import json

    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))

    assert settings["runtimeData"]["mode"] == "platform-user-data"
    assert settings["runtimeData"]["sourceRootDependency"] is False
    assert settings["runtimeData"]["absolutePathExposed"] is False
    assert all(value is False for value in settings["safety"].values())
    assert all(".." not in item["relativePath"] for item in settings["directories"])


def test_product_source_contains_no_personal_machine_paths() -> None:
    """Tracked product text contains no username, home, or cloud-folder path."""

    markers = [
        "C:" + "\\Users\\",
        "/" + "Users/",
        "/" + "home/",
        "One" + "Drive",
        "Mr" + "Dra",
    ]
    ignored = {".git", ".makers-anvil", ".pytest_cache", "__pycache__"}
    offenders = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix.lower() not in {".py", ".js", ".html", ".css", ".json", ".md", ".toml", ".yml", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(marker in text for marker in markers):
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []


def test_intake_policy_never_enables_data_or_action_mutations() -> None:
    """Every intake safety flag remains false in committed policy."""

    import json

    policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))

    assert policy["mode"] == "metadata-only"
    assert policy["recordsDirectory"] == "intake/records"
    assert all(value is False for value in policy["safety"].values())


def test_route_catalog_is_preview_only_and_action_free() -> None:
    """Committed route definitions cannot enable source access or route actions."""

    import json

    catalog = json.loads((ROOT / "config" / "route_catalog.json").read_text(encoding="utf-8"))

    assert catalog["mode"] == "metadata-derived-read-only"
    assert catalog["routes"]
    assert catalog["requiredProof"]
    assert all(value is False for value in catalog["safety"].values())


def test_output_policy_is_logical_preview_only_and_action_free() -> None:
    """Committed output policy uses logical storage and cannot claim produced proof."""

    import json

    policy = json.loads((ROOT / "config" / "output_policy.json").read_text(encoding="utf-8"))

    assert policy["mode"] == "route-derived-read-only"
    assert policy["logicalRoot"] == "makers-anvil-data://user/outputs"
    assert policy["bundles"]
    assert policy["requiredProof"]
    assert all(value is False for value in policy["safety"].values())


def test_tool_catalog_is_read_only_and_contains_no_personal_roots() -> None:
    """Tool candidates use generic providers and cannot claim process or software actions."""

    import json

    policy = json.loads((ROOT / "config" / "tool_catalog.json").read_text(encoding="utf-8"))
    serialized = json.dumps(policy)

    assert policy["mode"] == "read-only-presence"
    assert len(policy["tools"]) == 6
    assert all(value is False for value in policy["safety"].values())
    assert "C:" + "\\Users\\" not in serialized
    assert "/" + "Users/" not in serialized
    assert "/" + "home/" not in serialized


def test_tool_dry_run_policy_is_non_runnable_and_path_free() -> None:
    """Dry-run policy covers routes while every command, path, handoff, and action stays false."""

    import json

    policy = json.loads((ROOT / "config" / "tool_dry_run_policy.json").read_text(encoding="utf-8"))
    route_catalog = json.loads((ROOT / "config" / "route_catalog.json").read_text(encoding="utf-8"))
    serialized = json.dumps(policy)

    assert policy["mode"] == "semantic-invocation-read-only"
    assert {item["routeId"] for item in policy["routes"]} == {item["id"] for item in route_catalog["routes"]}
    assert all(value is False for value in policy["safety"].values())
    assert "commandString" not in serialized
    assert "C:" + "\\Users\\" not in serialized
    assert "/" + "Users/" not in serialized
    assert "/" + "home/" not in serialized


def test_execution_gate_policy_is_single_route_and_side_effect_free() -> None:
    """Execution policy defines complete evidence while authorization and execution stay false."""

    import json

    policy = json.loads((ROOT / "config" / "execution_gate_policy.json").read_text(encoding="utf-8"))
    serialized = json.dumps(policy)

    assert policy["mode"] == "read-only-gate-evaluation"
    assert policy["scope"] == {"routeId": "mesh-to-toolpath", "maxConcurrentExecutions": 1, "executionEnabled": False}
    assert len(policy["gates"]) == 10
    assert len({gate["evidenceSource"] for gate in policy["gates"]}) == 10
    assert all(gate["required"] is True for gate in policy["gates"])
    assert all(value is False for value in policy["safety"].values())
    assert "C:" + "\\Users\\" not in serialized
    assert "/" + "Users/" not in serialized
    assert "/" + "home/" not in serialized


def test_execution_request_policy_is_preview_only_and_writes_nothing() -> None:
    """Request policy models consent and audit requirements while all effects remain false."""

    import json

    policy = json.loads((ROOT / "config" / "execution_request_policy.json").read_text(encoding="utf-8"))
    serialized = json.dumps(policy)

    assert policy["mode"] == "read-only-request-preview"
    assert policy["scope"] == {
        "routeId": "mesh-to-toolpath",
        "requestPersistenceEnabled": False,
        "authorizationEnabled": False,
        "auditWriteEnabled": False,
    }
    assert policy["audit"]["appendOnly"] is True
    assert policy["audit"]["eventWritesEnabled"] is False
    assert len(policy["audit"]["requiredEventTypes"]) == 6
    assert all(value is False for value in policy["safety"].values())
    assert "C:" + "\\Users\\" not in serialized
    assert "/" + "Users/" not in serialized
    assert "/" + "home/" not in serialized


def test_job_workspace_policy_allows_only_contained_local_record_writes() -> None:
    """Prepared jobs use app-owned storage while every execution-side effect stays false."""

    import json

    policy = json.loads((ROOT / "config" / "job_workspace_policy.json").read_text(encoding="utf-8"))
    serialized = json.dumps(policy)

    assert policy["mode"] == "contained-local-preparation"
    assert policy["scope"] == {"routeId": "mesh-to-toolpath", "maxPreparedJobsPerRequest": 1}
    assert policy["storage"]["jobsDirectory"] == "jobs"
    assert set(policy["storage"]["workspaceDirectories"]) == {"control", "working", "logs", "outputs"}
    assert policy["localActions"] == {
        "preparationEnabled": True,
        "cancellationRequestEnabled": True,
        "apiMutationEnabled": False,
        "browserMutationEnabled": False,
    }
    assert all(value is False for value in policy["safety"].values())
    assert "C:" + "\\Users\\" not in serialized
    assert "/" + "Users/" not in serialized
    assert "/" + "home/" not in serialized
