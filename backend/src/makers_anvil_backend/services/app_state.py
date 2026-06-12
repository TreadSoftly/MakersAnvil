"""Current read-only app state for the real Makers Anvil build."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService
from makers_anvil_backend.services.workspace_status import WorkspaceStatusService


class AppStateService:
    """Build deterministic state records for the browser dashboard."""

    api_build = "makers-anvil-real-pass-003-workspace-settings"

    def __init__(
        self,
        workspace_status: WorkspaceStatusService | None = None,
        workspace_config: WorkspaceConfigService | None = None,
    ) -> None:
        self._workspace_status = workspace_status or WorkspaceStatusService()
        self._workspace_config = workspace_config or WorkspaceConfigService()

    def health(self) -> dict[str, Any]:
        return {
            "schemaVersion": "makers-anvil.api.health.v1",
            "appName": "Makers Anvil",
            "apiBuild": self.api_build,
            "claimState": "proven",
            "service": "read-only-local-api",
            "timeUtc": datetime.now(UTC).isoformat(),
            "mutatingActionsEnabled": False,
        }

    def state(self) -> dict[str, Any]:
        current_status = self._workspace_status.current_status()
        return {
            "schemaVersion": "makers-anvil.api.state.v1",
            "appName": "Makers Anvil",
            "apiBuild": self.api_build,
            "claimState": current_status["claimState"],
            "mode": "local-read-only",
            "completion": current_status["trackPercentages"],
            "currentPass": current_status["currentPass"],
            "sourceTruth": current_status["sourceTruth"],
            "workspaceConfig": self._workspace_config.layout(),
            "tracks": self._tracks(),
            "capabilities": self._capabilities(),
            "blockedActions": current_status["blockedOrNotProven"],
            "nextPass": current_status["nextPass"],
        }

    def workspace_status(self) -> dict[str, Any]:
        return self._workspace_status.workspace_status()

    def pass_ledger(self) -> dict[str, Any]:
        return self._workspace_status.pass_ledger()

    def workspace_config(self) -> dict[str, Any]:
        return self._workspace_config.config()

    def workspace_layout(self) -> dict[str, Any]:
        return self._workspace_config.layout()

    def _tracks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "windows-local",
                "label": "Windows local app",
                "claimState": "staged",
                "summary": "Read-only local server, browser shell, status records, and app-owned workspace settings are present.",
            },
            {
                "id": "mac-linux",
                "label": "macOS and Linux",
                "claimState": "planned",
                "summary": "Architecture keeps these targets separate until tested.",
            },
            {
                "id": "web-hosted",
                "label": "Browser-hosted app",
                "claimState": "planned",
                "summary": "Future mode; local file and tool actions must be redesigned for hosting.",
            },
        ]

    def _capabilities(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "api-health",
                "label": "API health",
                "claimState": "proven",
                "summary": "GET /api/health returns a read-only health record.",
                "actionsEnabled": False,
            },
            {
                "id": "dashboard-shell",
                "label": "Dashboard shell",
                "claimState": "staged",
                "summary": "The browser UI renders current app state and blocked capabilities.",
                "actionsEnabled": False,
            },
            {
                "id": "workspace-status",
                "label": "Workspace status",
                "claimState": "proven",
                "summary": "Committed status files are exposed through read-only API records.",
                "actionsEnabled": False,
            },
            {
                "id": "workspace-settings",
                "label": "Workspace settings",
                "claimState": "staged",
                "summary": "Default local settings define an app-owned data directory without importing user files.",
                "actionsEnabled": False,
            },
            {
                "id": "file-intake",
                "label": "File intake",
                "claimState": "planned",
                "summary": "No runtime upload or folder import exists yet.",
                "actionsEnabled": False,
            },
            {
                "id": "route-execution",
                "label": "Route execution",
                "claimState": "blocked",
                "summary": "Routes cannot run until intake, route preview, tool, and proof gates exist.",
                "actionsEnabled": False,
            },
            {
                "id": "tool-launch",
                "label": "Tool launch",
                "claimState": "blocked",
                "summary": "External tools cannot launch until tool-specific proof gates exist.",
                "actionsEnabled": False,
            },
            {
                "id": "release-package",
                "label": "Release package",
                "claimState": "not proven",
                "summary": "No packaged release or installer has been built.",
                "actionsEnabled": False,
            },
        ]
