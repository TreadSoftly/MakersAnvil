"""Purpose: Validate settings and initialize the app-owned runtime layout.

Used by: Workspace APIs, initialization scripts, and dependent services.
Inputs: Default settings plus a private runtime root from ``RuntimePathsService``.
Outputs: Redacted config/layout records and optionally created safe directories.
Side effects: Initialization creates only allowlisted directories under the root.
Safety: Traversal, source-root coupling, and globally enabled actions are rejected.
Failure behavior: Invalid settings or containment violations raise ``ValueError``.
Related proof: ``tests/test_workspace_config.py`` and local-settings schema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.runtime_paths import LOGICAL_DATA_ROOT, RuntimePathsService


ROOT = Path(__file__).resolve().parents[4]


class WorkspaceConfigError(ValueError):
    """Raised when local workspace settings are invalid or uncontained."""


class WorkspaceConfigService:
    """Read and initialize a user-data workspace independent from source location."""

    def __init__(self, root: Path | None = None, runtime_paths: RuntimePathsService | None = None) -> None:
        """Bind source-independent runtime paths to committed workspace defaults."""

        self.root = (root or ROOT).resolve()
        self.runtime_paths = runtime_paths or RuntimePathsService(source_root=self.root)
        self.settings_path = self.root / "config" / "default_settings.json"

    def settings(self) -> dict[str, Any]:
        """Load defaults and reject any policy that reconnects data to source."""

        settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
        runtime_data = settings.get("runtimeData", {})
        # Exact equality is intentional: adding a permissive field must not
        # weaken source independence or path-redaction without a new schema.
        expected = {
            "mode": "platform-user-data",
            "logicalRoot": LOGICAL_DATA_ROOT,
            "environmentOverride": "MAKERS_ANVIL_DATA_DIR",
            "sourceRootDependency": False,
            "absolutePathExposed": False,
        }
        if runtime_data != expected:
            raise WorkspaceConfigError("runtime data settings must use the portable user-data policy")
        return settings

    def config(self) -> dict[str, Any]:
        """Return public workspace policy, safety flags, and portable directory metadata."""

        settings = self.settings()
        return {
            "schemaVersion": "makers-anvil.api.workspace-config.v1",
            "claimState": settings["claimState"],
            "settingsPath": "config/default_settings.json",
            "runtimeLocation": self.runtime_paths.public_info(),
            "safety": settings["safety"],
            "directories": self.layout()["directories"],
            "boundaries": [
                "Source files and runtime data have independent locations.",
                "Runtime data uses the operating system user-data directory or an explicit absolute override.",
                "Resolved personal filesystem paths are not exposed through API records.",
                "No user files are imported, moved, copied, deleted, or executed.",
                "Upload, route execution, tool launch, archive extraction, and folder import remain blocked.",
            ],
        }

    def layout(self) -> dict[str, Any]:
        """Report which app-owned directories exist without exposing their absolute root."""

        settings = self.settings()
        runtime_root = self.runtime_paths.location().root
        directories = []
        for entry in settings["directories"]:
            safe_relative = self._safe_relative_path(entry["relativePath"])
            target = self.runtime_paths.data_path(safe_relative)
            directories.append(
                {
                    "id": entry["id"],
                    "purpose": entry["purpose"],
                    "relativePath": safe_relative.as_posix(),
                    "exists": target.exists(),
                    "claimState": "detected" if target.exists() else "planned",
                }
            )
        return {
            "schemaVersion": "makers-anvil.api.workspace-layout.v1",
            "claimState": "staged",
            "runtimeLocation": self.runtime_paths.public_info(),
            "runtimeDataExists": runtime_root.exists(),
            "directories": directories,
            "creationAction": {
                "id": "local-workspace-init-script",
                "claimState": "staged",
                "enabledInApi": False,
                "script": "python scripts/init_workspace.py",
            },
        }

    def initialize(self) -> dict[str, Any]:
        """Create only configured app-owned directories and a path-redacted manifest."""

        settings = self.settings()
        runtime_root = self.runtime_paths.location().root
        runtime_root.mkdir(parents=True, exist_ok=True)
        created: list[str] = []
        for entry in settings["directories"]:
            safe_relative = self._safe_relative_path(entry["relativePath"])
            target = self.runtime_paths.data_path(safe_relative)
            target.mkdir(parents=True, exist_ok=True)
            created.append(safe_relative.as_posix())
        manifest = {
            "schemaVersion": "makers-anvil.runtime-workspace-manifest.v2",
            "claimState": "staged",
            "runtimeLocation": self.runtime_paths.public_info(),
            "directories": created,
            "blockedActions": [
                name for name, enabled in settings["safety"].items() if enabled is False
            ],
        }
        (runtime_root / "workspace_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return manifest

    def runtime_path(self, relative_path: str | Path) -> Path:
        """Return a contained path inside the resolved app-owned user-data root."""

        return self.runtime_paths.data_path(self._safe_relative_path(str(relative_path)))

    def logical_runtime_path(self, relative_path: str | Path) -> str:
        """Return a stable non-filesystem identifier safe for API display."""

        return self.runtime_paths.logical_path(self._safe_relative_path(str(relative_path)))

    @staticmethod
    def _safe_relative_path(relative_path: str) -> Path:
        """Reject absolute, empty, or traversing workspace directory declarations."""

        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
            raise WorkspaceConfigError("workspace directory path must be relative and contained")
        return candidate
