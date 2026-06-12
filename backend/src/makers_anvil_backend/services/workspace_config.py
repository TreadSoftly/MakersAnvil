"""Local workspace configuration and app-owned data layout."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]


class WorkspaceConfigError(ValueError):
    """Raised when local workspace settings would escape the app root."""


class WorkspaceConfigService:
    """Read and initialize the safe local Makers Anvil workspace layout."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self.settings_path = self.root / "config" / "default_settings.json"

    def settings(self) -> dict[str, Any]:
        return json.loads(self.settings_path.read_text(encoding="utf-8"))

    def config(self) -> dict[str, Any]:
        settings = self.settings()
        return {
            "schemaVersion": "makers-anvil.api.workspace-config.v1",
            "claimState": settings["claimState"],
            "settingsPath": "config/default_settings.json",
            "runtimeRoot": settings["runtimeRoot"],
            "safety": settings["safety"],
            "directories": self.layout()["directories"],
            "boundaries": [
                "Runtime workspace initialization creates only app-owned directories.",
                "No user files are imported, moved, copied, deleted, or executed.",
                "Upload, route execution, tool launch, archive extraction, and folder import remain blocked.",
            ],
        }

    def layout(self) -> dict[str, Any]:
        settings = self.settings()
        runtime_root = self._safe_runtime_root(settings["runtimeRoot"])
        directories = []
        for entry in settings["directories"]:
            safe_relative = self._safe_relative_path(entry["relativePath"])
            target = runtime_root / safe_relative
            directories.append(
                {
                    "id": entry["id"],
                    "purpose": entry["purpose"],
                    "relativePath": f"{settings['runtimeRoot']}/{safe_relative.as_posix()}",
                    "exists": target.exists(),
                    "claimState": "detected" if target.exists() else "planned",
                }
            )
        return {
            "schemaVersion": "makers-anvil.api.workspace-layout.v1",
            "claimState": "staged",
            "runtimeRoot": settings["runtimeRoot"],
            "runtimeRootExists": runtime_root.exists(),
            "directories": directories,
            "creationAction": {
                "id": "local-workspace-init-script",
                "claimState": "staged",
                "enabledInApi": False,
                "script": "python scripts/init_workspace.py",
            },
        }

    def initialize(self) -> dict[str, Any]:
        settings = self.settings()
        runtime_root = self._safe_runtime_root(settings["runtimeRoot"])
        runtime_root.mkdir(exist_ok=True)
        created: list[str] = []
        for entry in settings["directories"]:
            safe_relative = self._safe_relative_path(entry["relativePath"])
            target = runtime_root / safe_relative
            target.mkdir(parents=True, exist_ok=True)
            created.append(f"{settings['runtimeRoot']}/{safe_relative.as_posix()}")
        manifest = {
            "schemaVersion": "makers-anvil.runtime-workspace-manifest.v1",
            "claimState": "staged",
            "runtimeRoot": settings["runtimeRoot"],
            "directories": created,
            "blockedActions": [
                name for name, enabled in settings["safety"].items() if enabled is False
            ],
        }
        (runtime_root / "workspace_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest

    def _safe_runtime_root(self, runtime_root: str) -> Path:
        candidate = Path(runtime_root)
        if candidate.is_absolute() or ".." in candidate.parts or candidate.as_posix() != ".makers-anvil":
            raise WorkspaceConfigError("runtime root must be the app-owned .makers-anvil directory")
        resolved = (self.root / candidate).resolve()
        root = self.root.resolve()
        if root != resolved and root not in resolved.parents:
            raise WorkspaceConfigError("runtime root escapes source root")
        return resolved

    def _safe_relative_path(self, relative_path: str) -> Path:
        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise WorkspaceConfigError("workspace directory path must be relative and contained")
        return candidate
