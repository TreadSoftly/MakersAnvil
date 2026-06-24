"""Purpose: Explain and prove portable private runtime-path resolution.

Used by: Developers and CI across Windows, macOS, and Linux runners.
Inputs: Injected platform/environment values and isolated absolute overrides.
Outputs: Assertions for provider selection, containment, and public redaction.
Side effects: None beyond temporary path objects.
Safety: No source-location dependency or resolved personal path may escape.
Failure behavior: Relative overrides and invalid providers raise clear errors.
Related proof: ``services/runtime_paths.py`` and runtime-location schema.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathError, RuntimePathsService


def test_windows_uses_vendor_scoped_local_app_data(tmp_path: Path) -> None:
    """Windows defaults to vendor-scoped local application data."""

    local_app_data = tmp_path / "windows-local"
    service = RuntimePathsService(
        source_root=tmp_path / "source",
        environ={"LOCALAPPDATA": str(local_app_data)},
        home=tmp_path / "home",
        platform_name="win32",
    )

    assert service.location().root == (local_app_data / "TreadSoftly" / "MakersAnvil").resolve()
    assert service.location().provider == "windows-local-app-data"


def test_macos_uses_application_support(tmp_path: Path) -> None:
    """macOS defaults to the vendor/product Application Support directory."""

    home = tmp_path / "home"
    service = RuntimePathsService(tmp_path / "source", {}, home, "darwin")

    assert service.location().root == (home / "Library" / "Application Support" / "TreadSoftly" / "MakersAnvil").resolve()


def test_linux_uses_xdg_data_home(tmp_path: Path) -> None:
    """Linux honors the XDG per-user data convention."""

    xdg = tmp_path / "xdg-data"
    service = RuntimePathsService(
        source_root=tmp_path / "source",
        environ={"XDG_DATA_HOME": str(xdg)},
        home=tmp_path / "home",
        platform_name="linux",
    )

    assert service.location().root == (xdg / "treadsoftly" / "makers-anvil").resolve()


def test_absolute_environment_override_is_independent_from_source(tmp_path: Path) -> None:
    """An absolute override can place runtime data independently from source."""

    source_root = tmp_path / "source-copy"
    data_root = tmp_path / "data-somewhere-else"
    service = RuntimePathsService(
        source_root=source_root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=tmp_path / "home",
        platform_name="win32",
    )

    assert service.location().root == data_root.resolve()
    assert service.location().override_used is True
    assert source_root.resolve() not in service.location().root.parents


def test_relative_environment_override_is_rejected(tmp_path: Path) -> None:
    """Relative overrides are rejected because they depend on working directory."""

    service = RuntimePathsService(
        source_root=tmp_path / "source",
        environ={DATA_DIR_ENV: "relative-data"},
        home=tmp_path / "home",
        platform_name="linux",
    )

    with pytest.raises(RuntimePathError, match="absolute path"):
        service.location()


def test_public_runtime_info_never_exposes_resolved_paths(tmp_path: Path) -> None:
    """Public location metadata contains policy labels but no private path."""

    data_root = tmp_path / "private-data"
    service = RuntimePathsService(
        source_root=tmp_path / "private-source",
        environ={DATA_DIR_ENV: str(data_root)},
        home=tmp_path / "private-home",
        platform_name="linux",
    )

    info = service.public_info()
    serialized = json.dumps(info)

    assert info["logicalRoot"] == "makers-anvil-data://user"
    assert info["sourceRootDependency"] is False
    assert info["absolutePathExposed"] is False
    assert str(tmp_path) not in serialized


def test_runtime_child_paths_remain_contained(tmp_path: Path) -> None:
    """Runtime child paths resolve inside user data and reject traversal."""

    service = RuntimePathsService(
        source_root=tmp_path / "source",
        environ={DATA_DIR_ENV: str(tmp_path / "data")},
        home=tmp_path / "home",
        platform_name="linux",
    )

    assert service.data_path("intake/records") == (tmp_path / "data" / "intake" / "records").resolve()
    with pytest.raises(RuntimePathError):
        service.data_path("../outside")
