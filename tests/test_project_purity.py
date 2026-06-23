from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_reference_folder_is_not_tracked_product_source() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "Refrences For Makers Anvil Application/" in gitignore
    assert "References For Makers Anvil Application/" in gitignore


def test_frontend_has_no_mutating_api_calls() -> None:
    app_js = (ROOT / "frontend" / "public" / "assets" / "app.js").read_text(encoding="utf-8")

    assert 'method: "GET"' in app_js
    assert 'method: "POST"' not in app_js
    assert 'method: "DELETE"' not in app_js
    assert "/api/tools/open" not in app_js


def test_reference_material_names_are_not_runtime_dependencies() -> None:
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
    import json

    current = json.loads((ROOT / "state" / "current_status.json").read_text(encoding="utf-8"))
    ledger = json.loads((ROOT / "state" / "pass_ledger.json").read_text(encoding="utf-8"))

    assert current["currentPass"]["id"] == "PASS-005"
    assert current["trackPercentages"]["realApp"] == 12.5
    assert current["product"]["sourceRoot"] == "."
    assert current["referencePolicy"]["runtimeDependency"] is False
    assert ledger["passes"][-1]["id"] == "PASS-005"


def test_default_settings_are_safe_and_relative() -> None:
    import json

    settings = json.loads((ROOT / "config" / "default_settings.json").read_text(encoding="utf-8"))

    assert settings["runtimeData"]["mode"] == "platform-user-data"
    assert settings["runtimeData"]["sourceRootDependency"] is False
    assert settings["runtimeData"]["absolutePathExposed"] is False
    assert all(value is False for value in settings["safety"].values())
    assert all(".." not in item["relativePath"] for item in settings["directories"])


def test_product_source_contains_no_personal_machine_paths() -> None:
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
    import json

    policy = json.loads((ROOT / "config" / "intake_policy.json").read_text(encoding="utf-8"))

    assert policy["mode"] == "metadata-only"
    assert policy["recordsDirectory"] == "intake/records"
    assert all(value is False for value in policy["safety"].values())
