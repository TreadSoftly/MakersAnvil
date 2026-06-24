"""Current read-only app state for the real Makers Anvil build."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from makers_anvil_backend.services.execution_gate import ExecutionGateService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.output_proof import OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.tool_detection import ToolDetectionService
from makers_anvil_backend.services.tool_dry_run import ToolDryRunService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService
from makers_anvil_backend.services.workspace_status import WorkspaceStatusService


class AppStateService:
    """Build deterministic state records for the browser dashboard."""

    api_build = "makers-anvil-real-pass-011-execution-gates"

    def __init__(
        self,
        workspace_status: WorkspaceStatusService | None = None,
        workspace_config: WorkspaceConfigService | None = None,
        intake_catalog: IntakeCatalogService | None = None,
        route_preview: RoutePreviewService | None = None,
        output_proof: OutputProofService | None = None,
        tool_detection: ToolDetectionService | None = None,
        tool_dry_run: ToolDryRunService | None = None,
        execution_gate: ExecutionGateService | None = None,
    ) -> None:
        self._workspace_status = workspace_status or WorkspaceStatusService()
        self._workspace_config = workspace_config or WorkspaceConfigService()
        self._intake_catalog = intake_catalog or IntakeCatalogService()
        self._route_preview = route_preview or RoutePreviewService(intake_catalog=self._intake_catalog)
        self._output_proof = output_proof or OutputProofService(
            route_preview=self._route_preview,
            workspace_config=self._workspace_config,
        )
        self._tool_detection = tool_detection or ToolDetectionService()
        self._tool_dry_run = tool_dry_run or ToolDryRunService(
            route_preview=self._route_preview,
            output_proof=self._output_proof,
            tool_detection=self._tool_detection,
        )
        self._execution_gate = execution_gate or ExecutionGateService(tool_dry_run=self._tool_dry_run)

    def health(self) -> dict[str, Any]:
        """Describe the live API build without claiming that mutations are enabled."""

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
        """Compose the complete dashboard record from durable and runtime services."""

        current_status = self._workspace_status.current_status()
        intake_catalog = self._intake_catalog.catalog()
        route_preview = self._route_preview.preview_catalog(intake_catalog)
        output_proof = self._output_proof.preview_catalog(route_preview)
        tool_detection = self._tool_detection.detection_catalog()
        tool_dry_run = self._tool_dry_run.plan_catalog(route_preview, output_proof, tool_detection)
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
            "intakeCatalog": intake_catalog,
            "routePreview": route_preview,
            "outputProof": output_proof,
            "toolDetection": tool_detection,
            "toolDryRun": tool_dry_run,
            "executionGates": self._execution_gate.gate_catalog(tool_dry_run),
            "tracks": self._tracks(),
            "capabilities": self._capabilities(),
            "blockedActions": current_status["blockedOrNotProven"],
            "nextPass": current_status["nextPass"],
        }

    def workspace_status(self) -> dict[str, Any]:
        """Return committed current-pass truth through the workspace status service."""

        return self._workspace_status.workspace_status()

    def pass_ledger(self) -> dict[str, Any]:
        """Return the ordered durable pass history without modifying it."""

        return self._workspace_status.pass_ledger()

    def workspace_config(self) -> dict[str, Any]:
        """Return safe workspace policy with resolved personal paths withheld."""

        return self._workspace_config.config()

    def workspace_layout(self) -> dict[str, Any]:
        """Report app-owned directory presence using relative and logical identifiers."""

        return self._workspace_config.layout()

    def intake_policy(self) -> dict[str, Any]:
        """Return metadata-intake rules and their blocked action boundaries."""

        return self._intake_catalog.policy_response()

    def intake_catalog(self) -> dict[str, Any]:
        """Return validated app-owned intake records through a read-only response."""

        return self._intake_catalog.catalog()

    def route_preview(self) -> dict[str, Any]:
        """Return metadata-derived candidate steps while every action stays disabled."""

        return self._route_preview.preview_catalog()

    def output_proof(self) -> dict[str, Any]:
        """Return planned output bundles and explicitly incomplete proof state."""

        return self._output_proof.preview_catalog()

    def tool_detection(self) -> dict[str, Any]:
        """Return path-redacted tool presence without executing or changing software."""

        return self._tool_detection.detection_catalog()

    def tool_dry_run(self) -> dict[str, Any]:
        """Return semantic route/tool/output plans with every action still blocked."""

        return self._tool_dry_run.plan_catalog()

    def execution_gates(self) -> dict[str, Any]:
        """Return one route's required evidence while execution remains disabled."""

        return self._execution_gate.gate_catalog()

    def _tracks(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "windows-local",
                "label": "Windows local app",
                "claimState": "staged",
                "summary": "Read-only local server, browser shell, portable user-data paths, status records, and metadata intake are present.",
            },
            {
                "id": "mac-linux",
                "label": "macOS and Linux",
                "claimState": "planned",
                "summary": "Portable runtime paths are CI-tested; full macOS and Linux app runtime proof remains planned.",
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
                "summary": "Runtime data uses OS user-data locations or an absolute override, independent from the source checkout.",
                "actionsEnabled": False,
            },
            {
                "id": "file-intake",
                "label": "File intake",
                "claimState": "staged",
                "summary": "Local metadata records can be staged without storing paths, copying content, importing folders, or enabling uploads.",
                "actionsEnabled": False,
            },
            {
                "id": "source-explainability",
                "label": "Source explainability",
                "claimState": "proven",
                "summary": "Every tracked file is mapped and Python/frontend explanation coverage is machine-verified.",
                "actionsEnabled": False,
            },
            {
                "id": "route-preview",
                "label": "Route preview",
                "claimState": "preview-only",
                "summary": "Metadata records map to candidate steps and explicit readiness blockers without executing a route.",
                "actionsEnabled": False,
            },
            {
                "id": "output-proof",
                "label": "Output and proof",
                "claimState": "preview-only",
                "summary": "Route previews map to planned artifacts and required evidence without creating or opening outputs.",
                "actionsEnabled": False,
            },
            {
                "id": "tool-detection",
                "label": "Tool detection",
                "claimState": "staged",
                "summary": "Known maker tools are checked through PATH and standard locations without execution or path exposure.",
                "actionsEnabled": False,
            },
            {
                "id": "tool-dry-run",
                "label": "Tool dry run",
                "claimState": "preview-only",
                "summary": "Routes, detected tool families, and logical outputs compose into non-runnable invocation plans.",
                "actionsEnabled": False,
            },
            {
                "id": "execution-gates",
                "label": "Execution gates",
                "claimState": "staged",
                "summary": "One route has explicit authorization, containment, compatibility, control, logging, and proof gates.",
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
