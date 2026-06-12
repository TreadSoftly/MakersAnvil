"""Current read-only app state for the first real Makers Anvil build."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class AppStateService:
    """Build deterministic state records for the browser dashboard."""

    api_build = "makers-anvil-real-pass-001-clean-foundation"

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
        return {
            "schemaVersion": "makers-anvil.api.state.v1",
            "appName": "Makers Anvil",
            "apiBuild": self.api_build,
            "claimState": "staged",
            "mode": "local-read-only",
            "completion": {
                "realApp": 2.5,
                "windowsLocal": 2.5,
                "macLinux": 0.0,
                "webHosted": 0.0,
                "packagedRelease": 0.0,
                "cleanMachineProof": 0.0,
            },
            "tracks": self._tracks(),
            "capabilities": self._capabilities(),
            "blockedActions": self._blocked_actions(),
            "nextPass": {
                "id": "PASS-002",
                "title": "workspace state and durable status",
                "claimState": "planned",
            },
        }

    def _tracks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "windows-local",
                "label": "Windows local app",
                "claimState": "staged",
                "summary": "Read-only local server and browser shell are present.",
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

    def _blocked_actions(self) -> list[str]:
        return [
            "runtime user upload",
            "route execution",
            "output open action",
            "external tool launch",
            "selected-file handoff",
            "software install/update/uninstall/repair",
            "archive extraction",
            "folder import",
            "release packaging",
            "clean-machine claim",
        ]
