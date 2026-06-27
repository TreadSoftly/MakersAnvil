"""Purpose: Explain and prove portable app-owned workspace initialization.

Used by: Developers and CI when settings or runtime directory layout changes.
Inputs: Isolated runtime roots and valid/invalid default-settings documents.
Outputs: Assertions over contained directories and redacted public records.
Side effects: Creates directories only inside temporary roots.
Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
Failure behavior: Invalid policy or escaping paths raise ``ValueError``.
Related proof: ``services/workspace_config.py`` and local-settings schema.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigError, WorkspaceConfigService


def write_settings(root: Path, source_root_dependency: bool = False) -> None:
    """Purpose: Write isolated settings, optionally weakening one field for rejection tests.

    Inputs: Caller-supplied ``root``, ``source_root_dependency`` values from the signature.
    Outputs: Returns ``None``, or raises before returning when validation fails.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
    Example: Call ``result = instance.write_settings(...)`` with values satisfying the documented inputs.
    Related proof: ``services/workspace_config.py`` and local-settings schema.
    """

    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "default_settings.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.local-settings.v1",
                "claimState": "staged",
                "runtimeData": {
                    "mode": "platform-user-data",
                    "logicalRoot": "makers-anvil-data://user",
                    "environmentOverride": DATA_DIR_ENV,
                    "sourceRootDependency": source_root_dependency,
                    "absolutePathExposed": False,
                },
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


def build_service(source_root: Path, data_root: Path) -> WorkspaceConfigService:
    """Purpose: Build a workspace service with deliberately unrelated source and data roots.

    Inputs: Caller-supplied ``source_root``, ``data_root`` values from the signature.
    Outputs: Returns ``WorkspaceConfigService``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
    Example: Call ``result = instance.build_service(...)`` with values satisfying the documented inputs.
    Related proof: ``services/workspace_config.py`` and local-settings schema.
    """

    paths = RuntimePathsService(
        source_root=source_root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=source_root.parent / "home",
        platform_name="linux",
    )
    return WorkspaceConfigService(source_root, paths)


def test_initialize_keeps_runtime_data_outside_source_checkout(tmp_path: Path) -> None:
    """Purpose: Initialization writes only to user data and returns a path-redacted manifest.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
    Example: Run ``python -m pytest tests/test_workspace_config.py -k test_initialize_keeps_runtime_data_outside_source_checkout``.
    Related proof: ``services/workspace_config.py`` and local-settings schema.
    """

    source_root = tmp_path / "copied-anywhere" / "makers-anvil"
    data_root = tmp_path / "unrelated-user-data"
    write_settings(source_root)
    service = build_service(source_root, data_root)

    manifest = service.initialize()

    assert (data_root / "settings").is_dir()
    assert (data_root / "jobs").is_dir()
    assert not (source_root / ".makers-anvil").exists()
    written = json.loads((data_root / "workspace_manifest.json").read_text(encoding="utf-8"))
    assert written["schemaVersion"] == "makers-anvil.runtime-workspace-manifest.v2"
    assert written["runtimeLocation"]["sourceRootDependency"] is False
    assert written["runtimeLocation"]["absolutePathExposed"] is False
    assert written["directories"] == ["settings", "jobs"]
    serialized = json.dumps(manifest)
    assert str(source_root) not in serialized
    assert str(data_root) not in serialized


def test_workspace_relative_path_cannot_escape_user_data_root(tmp_path: Path) -> None:
    """Purpose: Workspace child paths reject traversal outside app-owned user data.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
    Example: Run ``python -m pytest tests/test_workspace_config.py -k test_workspace_relative_path_cannot_escape_user_data_root``.
    Related proof: ``services/workspace_config.py`` and local-settings schema.
    """

    source_root = tmp_path / "source"
    write_settings(source_root)
    service = build_service(source_root, tmp_path / "data")

    with pytest.raises(WorkspaceConfigError):
        service.runtime_path("../outside")


def test_settings_cannot_reintroduce_source_root_dependency(tmp_path: Path) -> None:
    """Purpose: A changed setting cannot reconnect runtime data to the source checkout.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Traversal, source coupling, private-path exposure, and actions stay denied.
    Example: Run ``python -m pytest tests/test_workspace_config.py -k test_settings_cannot_reintroduce_source_root_dependency``.
    Related proof: ``services/workspace_config.py`` and local-settings schema.
    """

    source_root = tmp_path / "source"
    write_settings(source_root, source_root_dependency=True)
    service = build_service(source_root, tmp_path / "data")

    with pytest.raises(WorkspaceConfigError, match="portable user-data policy"):
        service.layout()
