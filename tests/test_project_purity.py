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
