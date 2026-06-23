"""Portable source and per-user runtime path resolution for Makers Anvil."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR_ENV = "MAKERS_ANVIL_DATA_DIR"
LOGICAL_DATA_ROOT = "makers-anvil-data://user"


class RuntimePathError(ValueError):
    """Raised when a runtime path would depend on an unsafe or ambiguous location."""


@dataclass(frozen=True)
class RuntimeLocation:
    """Resolved private location plus safe public metadata."""

    root: Path
    provider: str
    label: str
    override_used: bool


class RuntimePathsService:
    """Resolve app data independently from the source checkout or working directory."""

    def __init__(
        self,
        source_root: Path | None = None,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
        platform_name: str | None = None,
    ) -> None:
        self.source_root = (source_root or ROOT).resolve()
        self.environ = dict(os.environ if environ is None else environ)
        self.home = (home or Path.home()).resolve()
        self.platform_name = platform_name or sys.platform

    def location(self) -> RuntimeLocation:
        """Resolve the private data root from an override or OS convention."""

        override = self.environ.get(DATA_DIR_ENV)
        if override:
            # Overrides must be absolute so moving the current working
            # directory cannot silently redirect user data.
            root = self._absolute_path(override, DATA_DIR_ENV)
            return RuntimeLocation(root, "environment-override", "Environment override", True)

        # Each default follows the host operating system's per-user data
        # convention. Vendor scoping avoids collisions with unrelated apps.
        if self.platform_name.startswith("win"):
            local_app_data = self.environ.get("LOCALAPPDATA")
            base = self._absolute_path(local_app_data, "LOCALAPPDATA") if local_app_data else self.home / "AppData" / "Local"
            return RuntimeLocation(
                (base / "TreadSoftly" / "MakersAnvil").resolve(),
                "windows-local-app-data",
                "Windows local app data",
                False,
            )

        if self.platform_name == "darwin":
            return RuntimeLocation(
                (self.home / "Library" / "Application Support" / "TreadSoftly" / "MakersAnvil").resolve(),
                "macos-application-support",
                "macOS Application Support",
                False,
            )

        xdg_data_home = self.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            base = self._absolute_path(xdg_data_home, "XDG_DATA_HOME")
        else:
            base = self.home / ".local" / "share"
        return RuntimeLocation(
            (base / "treadsoftly" / "makers-anvil").resolve(),
            "linux-xdg-data",
            "Linux XDG data",
            False,
        )

    def public_info(self) -> dict[str, object]:
        """Return location metadata that deliberately omits the resolved filesystem path."""

        location = self.location()
        return {
            "schemaVersion": "makers-anvil.runtime-location.v1",
            "mode": "platform-user-data",
            "provider": location.provider,
            "label": location.label,
            "logicalRoot": LOGICAL_DATA_ROOT,
            "environmentOverride": DATA_DIR_ENV,
            "environmentOverrideUsed": location.override_used,
            "sourceRootDependency": False,
            "absolutePathExposed": False,
        }

    def data_path(self, relative_path: str | Path) -> Path:
        """Resolve one contained child path and reject absolute or escaping input."""

        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
            raise RuntimePathError("runtime data path must be relative and contained")
        root = self.location().root
        target = (root / candidate).resolve()
        if root != target and root not in target.parents:
            raise RuntimePathError("runtime data path escapes the app-owned user-data directory")
        return target

    def logical_path(self, relative_path: str | Path) -> str:
        """Return a stable API-safe identifier for a contained runtime child path."""

        candidate = Path(relative_path)
        self.data_path(candidate)
        return f"{LOGICAL_DATA_ROOT}/{candidate.as_posix()}"

    def _absolute_path(self, value: str, variable_name: str) -> Path:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            raise RuntimePathError(f"{variable_name} must be an absolute path")
        return candidate.resolve()
