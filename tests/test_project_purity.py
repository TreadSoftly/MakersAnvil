"""Purpose: Prove repository purity, portability, and durable-truth invariants.

Used by: Developers and CI after every policy, state, source, or reference change.
Inputs: Tracked product text, ignored reference roots, policies, and state files.
Outputs: Assertions against personal paths, runtime coupling, and enabled effects.
Side effects: Reads repository files only.
Safety: Reference material and one developer's machine can never become dependencies.
Failure behavior: Any forbidden string, stale marker, or weakened policy fails CI.
Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reference_folder_is_not_tracked_product_source() -> None:
    """Purpose: All planning and previous-app reference roots remain outside product history.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_reference_folder_is_not_tracked_product_source``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "Refrences For Makers Anvil Application/" in gitignore
    assert "References For Makers Anvil Application/" in gitignore
    assert "Previous Working MA For References/" in gitignore


def test_frontend_mutation_is_limited_to_two_authorized_intake_calls() -> None:
    """Purpose: Browser mutation is limited to metadata consent and matching file bytes.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_frontend_mutation_is_limited_to_two_authorized_intake_calls``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    app_js = (ROOT / "frontend" / "public" / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'method: "GET"' in app_js
    assert app_js.count('method: "POST"') == 2
    assert 'const intakeSessionUrl = "/api/intake/session"' in app_js
    assert '"X-Makers-Anvil-Request-Token"' in app_js
    assert 'mode: "same-origin"' in app_js
    assert 'method: "DELETE"' not in app_js
    assert "/api/tools/open" not in app_js
    assert "/api/jobs/run" not in app_js


def test_reference_material_names_are_not_runtime_dependencies() -> None:
    """Purpose: Historical reference-build identifiers cannot leak into product runtime code.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_reference_material_names_are_not_runtime_dependencies``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    product_files = [
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and ".makers-anvil" not in path.parts
        and ".pytest_cache" not in path.parts
        and "Refrences For Makers Anvil Application" not in path.parts
        and "References For Makers Anvil Application" not in path.parts
        and "Previous Working MA For References" not in path.parts
        and "__pycache__" not in path.parts
    ]

    forbidden = "makers" + "_anvil_build_pass_012_release_backup_uninstall_dry_run"
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in product_files
        if forbidden in path.read_text(encoding="utf-8", errors="ignore")
    ]
    assert offenders == []


def test_previous_app_migration_registry_keeps_legacy_runtime_outside_product() -> None:
    """Purpose: The old working app remains evidence rather than a second runtime.

    Inputs: Committed migration registry and tracked product source text.
    Outputs: Assertions for unique decisions and all-false legacy effects.
    How it works: Parses the registry and scans Python imports for legacy package names.
    Side effects: Reads repository files only.
    Failure behavior: Duplicate ids, imported runtime, or enabled legacy effect fails.
    Safety: Prevents copying the old source tree while still preserving its lessons.
    Example: ``native-desktop-window`` rebuilds in current source; monoliths reject.
    Related proof: ``docs/PREVIOUS_APP_MERGER_AUDIT.md`` and migration schema.
    """

    import json

    migration = json.loads((ROOT / "state" / "previous_app_migration.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in migration["capabilities"]]
    python_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "backend").rglob("*.py")
        if "__pycache__" not in path.parts
    )

    assert migration["runtimeDependency"] is False
    assert len(ids) == len(set(ids))
    assert all(value is False for value in migration["safety"].values())
    assert "makers_anvil_panel" not in python_text


def test_desktop_build_outputs_are_ignored_local_artifacts() -> None:
    """Purpose: Build environments and executable outputs cannot enter product history.

    Inputs: Root ``.gitignore`` packaging patterns.
    Outputs: Assertions for ignored build and artifact directories.
    How it works: Reads ignore text and checks exact portable directory patterns.
    Side effects: Reads one file only.
    Failure behavior: Missing exclusions fail before a local binary is committed.
    Safety: Prevents virtual environments, PyInstaller work, and binaries becoming source.
    Example: ``.build/`` and ``artifacts/`` remain local/CI output locations.
    Related proof: ``scripts/build_windows_exe.py`` writes only those trees.
    """

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert ".build/" in gitignore
    assert "artifacts/" in gitignore


def test_durable_status_records_are_current_and_relative() -> None:
    """Purpose: Current status and pass history agree on the active bounded pass.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_durable_status_records_are_current_and_relative``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    import json

    current = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))

    assert current["currentPass"]["id"] == "PASS-018"
    assert current["trackPercentages"]["realApp"] == 42.5
    assert current["product"]["sourceRoot"] == "."
    assert current["referencePolicy"]["runtimeDependency"] is False
    assert ledger["passes"][-1]["id"] == "PASS-018"


def test_default_settings_enable_only_authorized_intake_and_stay_relative() -> None:
    """Purpose: Defaults enable one intake scope while preserving portable blocked effects.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_default_settings_enable_only_authorized_intake_and_stay_relative``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    import json

    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))

    assert settings["runtimeData"]["mode"] == "platform-user-data"
    assert settings["runtimeData"]["sourceRootDependency"] is False
    assert settings["runtimeData"]["absolutePathExposed"] is False
    assert settings["safety"]["userUploadEnabled"] is True
    assert all(value is False for key, value in settings["safety"].items() if key != "userUploadEnabled")
    assert all(".." not in item["relativePath"] for item in settings["directories"])


def test_product_source_contains_no_personal_machine_paths() -> None:
    """Purpose: Tracked product text contains no username, home, or cloud-folder path.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It checks conditions, then iterates over bounded records.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_product_source_contains_no_personal_machine_paths``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    markers = [
        "C:" + "\\Users\\",
        "/" + "Users/",
        "/" + "home/",
        "One" + "Drive",
        "Mr" + "Dra",
    ]
    ignored = {
        ".git",
        ".build",
        ".makers-anvil",
        ".pytest_cache",
        "__pycache__",
        "Refrences For Makers Anvil Application",
        "References For Makers Anvil Application",
        "Previous Working MA For References",
        "artifacts",
    }
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


def test_intake_policy_enables_only_explicit_one_file_copy() -> None:
    """Purpose: Intake policy enables consent/copy while every downstream effect is false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_intake_policy_enables_only_explicit_one_file_copy``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    import json

    policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))

    assert policy["mode"] == "authorized-local-copy"
    assert policy["recordsDirectory"] == "intake/records"
    assert policy["filesDirectory"] == "intake/files"
    assert policy["authorizationsDirectory"] == "intake/authorizations"
    assert policy["capabilities"] == {
        "apiMutationEnabled": True,
        "browserFilePickerEnabled": True,
        "explicitAuthorizationRequired": True,
        "appOwnedCopyEnabled": True,
        "dragDropEnabled": False,
        "clipboardPasteEnabled": False,
    }
    assert "archive" not in policy["uploadAllowedKinds"]
    assert all(value is False for value in policy["safety"].values())


def test_route_catalog_is_preview_only_and_action_free() -> None:
    """Purpose: Committed route definitions cannot enable source access or route actions.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_route_catalog_is_preview_only_and_action_free``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    import json

    catalog = json.loads((ROOT / "config" / "route_catalog.json").read_text(encoding="utf-8"))

    assert catalog["mode"] == "metadata-derived-read-only"
    assert catalog["routes"]
    assert catalog["requiredProof"]
    assert all(value is False for value in catalog["safety"].values())


def test_output_policy_is_logical_preview_only_and_action_free() -> None:
    """Purpose: Committed output policy uses logical storage and cannot claim produced proof.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_output_policy_is_logical_preview_only_and_action_free``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

    import json

    policy = json.loads((ROOT / "config" / "output_policy.json").read_text(encoding="utf-8"))

    assert policy["mode"] == "route-derived-read-only"
    assert policy["logicalRoot"] == "makers-anvil-data://user/outputs"
    assert policy["bundles"]
    assert policy["requiredProof"]
    assert all(value is False for value in policy["safety"].values())


def test_tool_catalog_is_read_only_and_contains_no_personal_roots() -> None:
    """Purpose: Tool candidates use generic providers and cannot claim process or software actions.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_tool_catalog_is_read_only_and_contains_no_personal_roots``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

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
    """Purpose: Dry-run policy covers routes while every command, path, handoff, and action stays false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_tool_dry_run_policy_is_non_runnable_and_path_free``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

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
    """Purpose: Execution policy defines complete evidence while authorization and execution stay false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_execution_gate_policy_is_single_route_and_side_effect_free``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

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
    """Purpose: Request policy models consent and audit requirements while all effects remain false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_execution_request_policy_is_preview_only_and_writes_nothing``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

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
    """Purpose: Prepared jobs use app-owned storage while every execution-side effect stays false.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Reference material and one developer's machine can never become dependencies.
    Example: Run ``python -m pytest tests/test_project_purity.py -k test_job_workspace_policy_allows_only_contained_local_record_writes``.
    Related proof: ``docs/REFERENCE_POLICY.md`` and ``scripts/verify_project.py``.
    """

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
