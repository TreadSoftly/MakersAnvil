"""Purpose: Compose coherent dashboard snapshots from focused services.

Used by: ``MakersAnvilApi`` for state, policy, preview, and catalog routes.
Inputs: Repository roots, runtime configuration, and optional injected services.
Outputs: JSON-shaped status records assembled from one observation chain.
Side effects: Reads state; explicit intake methods can write authorized app-owned files.
Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
Failure behavior: Invalid policy or runtime records fail through their service.
Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from makers_anvil_backend.services.activity_log import ActivityLogService
from makers_anvil_backend.services.authorized_intake import AuthorizedIntakeService, IntakeRequestContext
from makers_anvil_backend.services.capability_matrix import CapabilityMatrixService
from makers_anvil_backend.services.contained_execution import ContainedExecutionService
from makers_anvil_backend.services.execution_gate import ExecutionGateService
from makers_anvil_backend.services.execution_request import ExecutionRequestService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.job_workspace import JobWorkspaceService
from makers_anvil_backend.services.lifecycle_dry_run import LifecycleDryRunService
from makers_anvil_backend.services.output_proof import OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.tool_detection import ToolDetectionService
from makers_anvil_backend.services.tool_dry_run import ToolDryRunService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService
from makers_anvil_backend.services.workspace_status import WorkspaceStatusService
from makers_anvil_backend.services.workbench_experience import WorkbenchExperienceService


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

    api_build = "makers-anvil-real-pass-021-lifecycle-dry-runs"

    def __init__(
        self,
        workspace_status: WorkspaceStatusService | None = None,
        workspace_config: WorkspaceConfigService | None = None,
        intake_catalog: IntakeCatalogService | None = None,
        authorized_intake: AuthorizedIntakeService | None = None,
        route_preview: RoutePreviewService | None = None,
        output_proof: OutputProofService | None = None,
        tool_detection: ToolDetectionService | None = None,
        tool_dry_run: ToolDryRunService | None = None,
        execution_gate: ExecutionGateService | None = None,
        execution_request: ExecutionRequestService | None = None,
        job_workspace: JobWorkspaceService | None = None,
        workbench_experience: WorkbenchExperienceService | None = None,
        activity_log: ActivityLogService | None = None,
        capability_matrix: CapabilityMatrixService | None = None,
        contained_execution: ContainedExecutionService | None = None,
        lifecycle_dry_run: LifecycleDryRunService | None = None,
    ) -> None:
        """Purpose: Compose injected or default services so one request uses coherent snapshots.

        Inputs: Caller-supplied workspace, intake, planning, tool, gate, request, and job service values.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Reuses earlier snapshots so one response cannot mix incompatible truth.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        self._workspace_status = workspace_status or WorkspaceStatusService()
        self._workspace_config = workspace_config or (intake_catalog.workspace_config if intake_catalog is not None else WorkspaceConfigService())
        self._intake_catalog = intake_catalog or IntakeCatalogService(workspace_config=self._workspace_config)
        self._authorized_intake = authorized_intake or AuthorizedIntakeService(self._intake_catalog)
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
        self._workbench_experience = workbench_experience or WorkbenchExperienceService(
            workspace_config=self._workspace_config,
            request_guard=self._authorized_intake.request_guard,
        )
        self._activity_log = activity_log or ActivityLogService(
            workspace_config=self._workspace_config,
            experience=self._workbench_experience,
        )
        self._capability_matrix = capability_matrix or CapabilityMatrixService(
            intake_catalog=self._intake_catalog,
            route_preview=self._route_preview,
        )
        # Contained execution shares the exact intake catalog, workspace policy,
        # and process-local request guard already used by authorized intake.
        self._contained_execution = contained_execution or ContainedExecutionService(
            workspace_config=self._workspace_config,
            intake_catalog=self._intake_catalog,
            request_guard=self._authorized_intake.request_guard,
        )
        self._lifecycle_dry_run = lifecycle_dry_run or LifecycleDryRunService(
            workspace_config=self._workspace_config,
        )

    def health(self) -> dict[str, Any]:
        """Purpose: Describe the live API and its one bounded mutation scope honestly.

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
            "service": "bounded-local-api",
            "timeUtc": datetime.now(UTC).isoformat(),
            "mutatingActionsEnabled": True,
            "enabledMutationScopes": ["authorized-file-intake", "contained-stl-preflight", "workbench-preferences"],
            "builtInStlPreflightEnabled": True,
            "lifecycleDryRunEnabled": True,
            "routeExecutionEnabled": False,
            "toolLaunchEnabled": False,
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
        capability_matrix = self._capability_matrix.matrix(intake_catalog, route_preview, output_proof, tool_detection)
        return {
            "schemaVersion": "makers-anvil.api.state.v1",
            "appName": "Makers Anvil",
            "apiBuild": self.api_build,
            "claimState": current_status["claimState"],
            "mode": "local-bounded-actions",
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
            "containedExecutions": self._contained_execution.catalog(),
            "lifecycleDryRuns": self._lifecycle_dry_run.catalog(),
            "capabilityMatrix": capability_matrix,
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

    def intake_session(self) -> dict[str, Any]:
        """Purpose: Return the process-local browser intake token and safe constraints.

        Inputs: No request body; the token belongs to this running app process.
        Outputs: Same-origin session record consumed only by the workbench controller.
        How it works: Delegates to the focused authorization service.
        Side effects: Reads policy and process memory only.
        Failure behavior: Policy/service failures propagate instead of enabling intake.
        Safety: The response exposes no filesystem path and is never placed in app state.
        Example: ``GET /api/intake/session`` supplies file-picker accept constraints.
        Related proof: API, server, and authorized-intake tests.
        """

        return self._authorized_intake.session()

    def create_intake_authorization(
        self,
        metadata: dict[str, Any],
        context: IntakeRequestContext,
    ) -> dict[str, Any]:
        """Purpose: Record explicit one-file consent after server-side validation.

        Inputs: Path-free browser metadata and same-origin request context.
        Outputs: Short-lived public authorization response.
        How it works: Delegates all validation/persistence to ``AuthorizedIntakeService``.
        Side effects: Writes one app-owned authorization JSON record.
        Failure behavior: Typed transfer errors propagate to the API facade.
        Safety: Does not receive source paths or file bytes and cannot run a route.
        Example: The UI calls this only after the user selects Authorize copy.
        Related proof: Authorization API and service tests.
        """

        result = self._authorized_intake.authorize(metadata, context)
        self._record_activity("intake-authorized", result["authorization"]["intakeId"])
        return result

    def ingest_authorized_file(
        self,
        authorization_id: str,
        stream: Any,
        content_length: int,
        context: IntakeRequestContext,
    ) -> dict[str, Any]:
        """Purpose: Consume one authorization and contain its exact byte stream.

        Inputs: Random authorization id, binary stream, exact length, and request context.
        Outputs: Path-redacted authorized intake result.
        How it works: Delegates streaming, hashing, atomic commit, and replay protection.
        Side effects: Writes only app-owned quarantined content and intake records.
        Failure behavior: Typed transfer errors and I/O failures propagate for honest status.
        Safety: No handoff, parsing, extraction, route, tool, or output action occurs.
        Example: The second browser POST sends the selected ``File`` as octet-stream.
        Related proof: Server streaming and authorized-intake transaction tests.
        """

        result = self._authorized_intake.ingest(authorization_id, stream, content_length, context)
        self._record_activity("intake-copied", result["record"]["id"])
        return result

    def workbench_experience(self) -> dict[str, Any]:
        """Purpose: Return contextual help and current portable presentation preferences.

        Inputs: No request body or caller-specific data.
        Outputs: Path-redacted workbench experience contract.
        How it works: Delegates policy and runtime overlay to the focused service.
        Side effects: Reads one optional app-owned preference file.
        Failure behavior: Invalid policy/runtime records propagate honestly.
        Safety: The response cannot enable route, tool, output, or software actions.
        Example: ``GET /api/workbench/experience`` initializes UI controls.
        Related proof: Experience service and API tests.
        """

        return self._workbench_experience.experience()

    def update_workbench_experience(
        self,
        preferences: dict[str, Any],
        context: IntakeRequestContext,
    ) -> dict[str, Any]:
        """Purpose: Persist one complete guarded workbench preference selection.

        Inputs: Exact preference mapping and same-origin local request context.
        Outputs: Updated public experience contract.
        How it works: Delegates validation/atomic write, then records fixed activity.
        Side effects: Replaces one settings file and normally creates one event file.
        Failure behavior: Preference errors propagate; journal failure does not undo success.
        Safety: Uses the same process token and origin guard as file intake.
        Example: Settings chooses compact density, reduced motion, and help enabled.
        Related proof: API guard, persistence, and activity tests.
        """

        result = self._workbench_experience.update(preferences, context)
        self._record_activity("preferences-updated")
        return result

    def activity_history(self) -> dict[str, Any]:
        """Purpose: Return bounded server-authored activity without private details.

        Inputs: No caller-supplied values.
        Outputs: Newest-first activity history contract.
        How it works: Delegates strict create-only record reads to the activity service.
        Side effects: Reads app-owned event JSON files only.
        Failure behavior: Corrupt events propagate instead of being reported as valid.
        Safety: No arbitrary browser event write endpoint exists.
        Example: ``GET /api/activity/recent`` lists completed intake/settings actions.
        Related proof: Activity log and API route tests.
        """

        return self._activity_log.recent()

    def capability_matrix(self) -> dict[str, Any]:
        """Purpose: Return a coherent capability comparison from current snapshots.

        Inputs: No caller-supplied values.
        Outputs: Five supported input lanes with route/tool/output truth.
        How it works: Builds one state snapshot and returns its matrix member.
        Side effects: Performs read-only policy, record, and tool-presence checks.
        Failure behavior: Inconsistent source contracts fail instead of guessing.
        Safety: Every route/tool/output action remains false.
        Example: ``GET /api/capabilities/matrix`` drives the lane renderer.
        Related proof: Matrix service, API consistency, and browser tests.
        """

        return self.state()["capabilityMatrix"]

    def _record_activity(self, event_type: str, subject_id: str | None = None) -> None:
        """Purpose: Add secondary activity evidence without corrupting a completed action.

        Inputs: Server-owned event type and optional generated subject id.
        Outputs: ``None`` after a successful record or contained journal failure.
        How it works: Calls the focused logger and contains expected storage/data errors.
        Side effects: Normally creates one immutable event file.
        Failure behavior: Journal failure cannot turn an already committed intake into 500.
        Safety: Only fixed server event values reach the logger.
        Example: Completed intake remains completed if its activity disk is unavailable.
        Related proof: App-state orchestration fault-containment tests.
        """

        try:
            self._activity_log.record(event_type, subject_id)
        except (OSError, ValueError):
            return

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

    def contained_execution_policy(self) -> dict[str, Any]:
        """Purpose: Return the exact built-in STL preflight execution boundary.

        Inputs: No request body or user path.
        Outputs: Path-redacted scope, action endpoints, and disabled external effects.
        How it works: Delegates strict committed-policy validation to the service.
        Side effects: Reads policy only.
        Failure behavior: Invalid policy fails instead of widening execution.
        Safety: Full routes, tools, commands, G-code, and output opening stay disabled.
        Example: The browser reads this before offering a preflight command.
        Related proof: Contained execution service and API tests.
        """

        return self._contained_execution.policy_response()

    def contained_execution_catalog(self) -> dict[str, Any]:
        """Purpose: Return path-redacted preflight lifecycle, audit, and proof truth.

        Inputs: No caller-supplied values.
        Outputs: Valid contained execution records plus conservative invalid counts.
        How it works: Delegates strict app-owned runtime record reads.
        Side effects: Reads execution storage only.
        Failure behavior: Invalid entries are counted and never exposed as usable.
        Safety: Catalog reads cannot start, cancel, launch, or open anything.
        Example: A completed preflight exposes report hashes but no disk path.
        Related proof: Contained execution catalog and privacy tests.
        """

        return self._contained_execution.catalog()

    def authorize_contained_execution(self, payload: dict[str, Any], context: IntakeRequestContext) -> dict[str, Any]:
        """Purpose: Record explicit consent for one authorized STL preflight.

        Inputs: Exact intake, route, operation, consent fields and guarded context.
        Outputs: One authorized execution workspace record.
        How it works: Delegates scope, source, uniqueness, and audit validation.
        Side effects: Creates only app-owned execution control/audit records.
        Failure behavior: Invalid scope, source, consent, or guard fails closed.
        Safety: Authorization does not execute or construct an external command.
        Example: A copied STL receives one built-in preflight authorization.
        Related proof: Contained execution authorization tests.
        """

        return self._contained_execution.authorize(payload, context)

    def run_contained_execution(self, execution_id: str, context: IntakeRequestContext) -> dict[str, Any]:
        """Purpose: Run one authorized in-process STL structural preflight.

        Inputs: Generated execution id and guarded same-origin context.
        Outputs: Completed, failed, or cancelled record with hashed evidence.
        How it works: Delegates streaming inspection and cooperative cancellation.
        Side effects: Reads one quarantine copy and writes app-owned proof artifacts.
        Failure behavior: Invalid state, content, or storage produces explicit failure.
        Safety: Starts no process/tool and creates no toolpath or G-code.
        Example: Valid binary STL produces a passing preflight report.
        Related proof: Contained execution success/failure/cancellation tests.
        """

        return self._contained_execution.run(execution_id, context)

    def cancel_contained_execution(self, execution_id: str, context: IntakeRequestContext) -> dict[str, Any]:
        """Purpose: Request or observe cooperative cancellation for one preflight.

        Inputs: Generated execution id and guarded same-origin context.
        Outputs: Updated cancellation and lifecycle truth.
        How it works: Writes a control record observed between bounded read chunks.
        Side effects: Replaces app-owned control/manifest records and appends audit.
        Failure behavior: Invalid or terminal execution rejects repeated mutation.
        Safety: Sends no operating-system process signal because none exists.
        Example: Cancelling before Run reaches cancelled with no output files.
        Related proof: Contained execution cancellation tests.
        """

        return self._contained_execution.cancel(execution_id, context)

    def lifecycle_dry_run_policy(self) -> dict[str, Any]:
        """Purpose: Return strict preview-only lifecycle scope and preservation rules.

        Inputs: No request body or caller-controlled path.
        Outputs: Validated operation definitions, logical backup target, actions, and safety.
        How it works: Delegates closed policy validation to ``LifecycleDryRunService``.
        Side effects: Reads bundled policy and workspace settings only.
        Failure behavior: Invalid or incomplete policy propagates instead of widening behavior.
        Safety: No lifecycle mutation endpoint, command, archive, process, or private path exists.
        Example: ``GET /api/lifecycle/policy`` lists five preview operations.
        Related proof: Lifecycle service and API tests.
        """

        return self._lifecycle_dry_run.policy_response()

    def lifecycle_dry_runs(self) -> dict[str, Any]:
        """Purpose: Return current backup, restore, update, uninstall, and repair previews.

        Inputs: App-owned directory metadata and bundled resource existence.
        Outputs: Five plans plus bounded path-redacted inventory and current evidence.
        How it works: Delegates metadata inventory and deterministic plan composition.
        Side effects: Reads directory entries and size metadata only.
        Failure behavior: Scan/policy/resource problems remain failed or propagate honestly.
        Safety: Reads no file content/name and performs no network, archive, installer, or deletion.
        Example: Backup plan reports aggregate bytes while creation remains blocked.
        Related proof: Lifecycle catalog, no-write, privacy, and API consistency tests.
        """

        return self._lifecycle_dry_run.catalog()

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
                "summary": "Read-only local core, native desktop shell, portable user data, planning contracts, and package smoke are present.",
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
                "id": "desktop-shell",
                "label": "Native desktop shell",
                "claimState": "staged",
                "summary": "A secured pywebview window owns one ephemeral loopback app session and deterministic shutdown.",
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
                "summary": "One reviewed file can be explicitly authorized and copied into path-redacted app-owned quarantine storage.",
                "actionsEnabled": True,
            },
            {
                "id": "workbench-preferences",
                "label": "Workbench preferences",
                "claimState": "staged",
                "summary": "Density, motion, and contextual help persist in portable app-owned user data.",
                "actionsEnabled": True,
            },
            {
                "id": "context-help",
                "label": "Contextual help",
                "claimState": "staged",
                "summary": "Focused help explains each major surface and its current safety boundary.",
                "actionsEnabled": False,
            },
            {
                "id": "activity-history",
                "label": "Activity history",
                "claimState": "staged",
                "summary": "Completed intake and setting actions create redacted immutable local events.",
                "actionsEnabled": False,
            },
            {
                "id": "capability-matrix",
                "label": "Capability matrix",
                "claimState": "preview-only",
                "summary": "Supported input kinds are compared against route previews and detected tool families.",
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
                "id": "contained-stl-preflight",
                "label": "Contained STL preflight",
                "claimState": "staged",
                "summary": "One authorized app-owned STL can receive an in-process structural preflight with audit and proof.",
                "actionsEnabled": True,
            },
            {
                "id": "lifecycle-dry-runs",
                "label": "Lifecycle dry runs",
                "claimState": "preview-only",
                "summary": "Backup, restore, update, uninstall, and repair are modeled with preservation evidence while every execution effect stays blocked.",
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
