import json
from pathlib import Path

from makers_anvil_backend.services.workspace_config import WorkspaceConfigError, WorkspaceConfigService


def write_settings(root: Path, runtime_root: str = ".makers-anvil") -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "default_settings.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.local-settings.v1",
                "claimState": "staged",
                "runtimeRoot": runtime_root,
                "directories": [
                    {"id": "settings", "relativePath": "settings", "purpose": "local user settings"},
                    {"id": "jobs", "relativePath": "jobs", "purpose": "future job records"},
                ],
                "safety": {
                    "userUploadEnabled": False,
                    "routeExecutionEnabled": False,
                    "toolLaunchEnabled": False,
                    "archiveExtractionEnabled": False,
                    "folderImportEnabled": False,
                    "deleteUserDataEnabled": False,
                    "releasePackagingEnabled": False,
                },
            }
        ),
        encoding="utf-8",
    )


def test_initialize_creates_only_app_owned_workspace(tmp_path: Path) -> None:
    write_settings(tmp_path)
    service = WorkspaceConfigService(tmp_path)

    manifest = service.initialize()

    assert manifest["runtimeRoot"] == ".makers-anvil"
    assert (tmp_path / ".makers-anvil" / "settings").is_dir()
    assert (tmp_path / ".makers-anvil" / "jobs").is_dir()
    written = json.loads((tmp_path / ".makers-anvil" / "workspace_manifest.json").read_text(encoding="utf-8"))
    assert written["claimState"] == "staged"
    assert all(path.startswith(".makers-anvil/") for path in written["directories"])


def test_workspace_root_cannot_escape_source_root(tmp_path: Path) -> None:
    write_settings(tmp_path, "../outside")
    service = WorkspaceConfigService(tmp_path)

    try:
        service.layout()
    except WorkspaceConfigError:
        return

    raise AssertionError("unsafe workspace root was not rejected")
