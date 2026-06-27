"""Purpose: Compose coherent dashboard snapshots from focused services.

Used by: ``MakersAnvilApi`` for state, policy, preview, and catalog routes.
Inputs: Repository roots, runtime configuration, and optional injected services.
Outputs: JSON-shaped status records assembled from one observation chain.
Side effects: Reads committed policy and app-owned runtime records only.
Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
Failure behavior: Invalid policy or runtime records fail through their service.
Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from makers_anvil_backend.services.execution_gate import ExecutionGateService
from makers_anvil_backend.services.execution_request import ExecutionRequestService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.job_workspace import JobWorkspaceService
from makers_anvil_backend.services.output_proof import OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.tool_detection import ToolDetectionService
from makers_anvil_backend.services.tool_dry_run import ToolDryRunService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService
from makers_anvil_backend.services.workspace_status import WorkspaceStatusService


class AppStateService:
    """Purpose: Build deterministic state records for the browser dashboard.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``AppStateService`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
    Example: Construct with ``instance = AppStateService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
    """

    api_build = "makers-anvil-real-pass-016-line-by-line-learning"

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
        execution_request: ExecutionRequestService | None = None,
        job_workspace: JobWorkspaceService | None = None,
    ) -> None:
        """Purpose: Compose injected or default services so one request uses coherent snapshots.

        Inputs: Caller-supplied ``workspace_status``, ``workspace_config``, ``intake_catalog``, ``route_preview``, ``output_proof``, ``tool_detection``, ``tool_dry_run``, ``execution_gate``, ``execution_request``, ``job_workspace`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

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
        self._execution_request = execution_request or ExecutionRequestService(
            tool_dry_run=self._tool_dry_run,
            execution_gate=self._execution_gate,
        )
        self._job_workspace = job_workspace or JobWorkspaceService(
            workspace_config=self._workspace_config,
            execution_request=self._execution_request,
        )

    def health(self) -> dict[str, Any]:
        """Purpose: Describe the live API build without claiming that mutations are enabled.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.health(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

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
        """Purpose: Compose the complete dashboard record from durable and runtime services.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.state(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        current_status = self._workspace_status.current_status()
        intake_catalog = self._intake_catalog.catalog()
        route_preview = self._route_preview.preview_catalog(intake_catalog)
        output_proof = self._output_proof.preview_catalog(route_preview)
        tool_detection = self._tool_detection.detection_catalog()
        tool_dry_run = self._tool_dry_run.plan_catalog(route_preview, output_proof, tool_detection)
        execution_gates = self._execution_gate.gate_catalog(tool_dry_run)
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
            "executionGates": execution_gates,
            "executionRequestPreview": self._execution_request.preview_catalog(tool_dry_run, execution_gates),
            "jobWorkspaceCatalog": self._job_workspace.catalog(),
            "tracks": self._tracks(),
            "capabilities": self._capabilities(),
            "blockedActions": current_status["blockedOrNotProven"],
            "nextPass": current_status["nextPass"],
        }

    def workspace_status(self) -> dict[str, Any]:
        """Purpose: Return committed current-pass truth through the workspace status service.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.workspace_status(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._workspace_status.workspace_status()

    def pass_ledger(self) -> dict[str, Any]:
        """Purpose: Return the ordered durable pass history without modifying it.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.pass_ledger(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._workspace_status.pass_ledger()

    def workspace_config(self) -> dict[str, Any]:
        """Purpose: Return safe workspace policy with resolved personal paths withheld.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.workspace_config(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._workspace_config.config()

    def workspace_layout(self) -> dict[str, Any]:
        """Purpose: Report app-owned directory presence using relative and logical identifiers.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.workspace_layout(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._workspace_config.layout()

    def intake_policy(self) -> dict[str, Any]:
        """Purpose: Return metadata-intake rules and their blocked action boundaries.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.intake_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._intake_catalog.policy_response()

    def intake_catalog(self) -> dict[str, Any]:
        """Purpose: Return validated app-owned intake records through a read-only response.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.intake_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._intake_catalog.catalog()

    def route_preview(self) -> dict[str, Any]:
        """Purpose: Return metadata-derived candidate steps while every action stays disabled.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.route_preview(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._route_preview.preview_catalog()

    def output_proof(self) -> dict[str, Any]:
        """Purpose: Return planned output bundles and explicitly incomplete proof state.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.output_proof(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._output_proof.preview_catalog()

    def tool_detection(self) -> dict[str, Any]:
        """Purpose: Return path-redacted tool presence without executing or changing software.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.tool_detection(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._tool_detection.detection_catalog()

    def tool_dry_run(self) -> dict[str, Any]:
        """Purpose: Return semantic route/tool/output plans with every action still blocked.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.tool_dry_run(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._tool_dry_run.plan_catalog()

    def execution_gates(self) -> dict[str, Any]:
        """Purpose: Return one route's required evidence while execution remains disabled.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.execution_gates(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._execution_gate.gate_catalog()

    def execution_request_preview(self) -> dict[str, Any]:
        """Purpose: Return path-free intent and an empty audit plan without persisting either.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.execution_request_preview(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._execution_request.preview_catalog()

    def job_workspace_policy(self) -> dict[str, Any]:
        """Purpose: Return contained job policy and local-script boundaries through a read-only API.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.job_workspace_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._job_workspace.policy_response()

    def job_workspace_catalog(self) -> dict[str, Any]:
        """Purpose: Return prepared job and cancellation records without exposing private paths.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance.job_workspace_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return self._job_workspace.catalog()

    def _tracks(self) -> list[dict[str, Any]]:
        """Purpose: Describe platform delivery tracks without claiming untested runtime support.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``list[dict[str, Any]]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance._tracks(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return [
            {
                "id": "windows-local",
                "label": "Windows local app",
                "claimState": "staged",
                "summary": "Read-only local server, browser shell, portable user data, metadata planning, execution gates, and request previews are present.",
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
        """Purpose: List visible capability truth while keeping every action control disabled.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``list[dict[str, Any]]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Call ``result = instance._capabilities(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

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
                "id": "execution-request-preview",
                "label": "Execution request preview",
                "claimState": "preview-only",
                "summary": "Logical intent, explicit consent fields, and required audit events are modeled without persisting a request or accepting authorization.",
                "actionsEnabled": False,
            },
            {
                "id": "contained-job-workspace",
                "label": "Contained job workspace",
                "claimState": "staged",
                "summary": "Explicit local scripts can prepare app-owned logical job records and request cancellation without starting or signaling a process.",
                "actionsEnabled": False,
            },
            {
                "id": "route-execution",
                "label": "Route execution",
                "claimState": "blocked",
                "summary": "Routes cannot run until contained workspaces, accepted authorization, cancellation, audit persistence, and output proof are proven.",
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
