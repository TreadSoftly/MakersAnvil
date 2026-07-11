"""Purpose: Preview logical execution intent, consent, and audit requirements.

Used by: ``AppStateService`` after dry-run and execution-gate evaluation.
Inputs: Request policy plus coherent dry-run and gate snapshots.
Outputs: Path-free request previews with unaccepted consent and empty audits.
Side effects: None; previews are never saved and no event is appended.
Safety: Authorization, path resolution, command building, and launch stay false.
Failure behavior: Missing joins or weakened policy fail closed or raise errors.
Related proof: ``tests/test_execution_request.py`` and request schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.execution_gate import ExecutionGateService
from makers_anvil_backend.services.tool_dry_run import ToolDryRunService


from makers_anvil_backend.runtime_resources import application_root


ROOT = application_root()
REQUIRED_AUDIT_EVENTS = {
    "request-created",
    "authorization-recorded",
    "execution-started",
    "execution-cancelled",
    "execution-completed",
    "proof-recorded",
}
REQUEST_SAFETY_FLAGS = {
    "requestPersisted",
    "authorizationAccepted",
    "auditEventWritten",
    "sourcePathResolved",
    "outputPathResolved",
    "commandConstructed",
    "processStarted",
    "toolLaunched",
    "filesystemWritten",
    "proofCaptured",
}


class ExecutionRequestError(ValueError):
    """Purpose: Raised when request policy could persist intent or weaken an action boundary.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ExecutionRequestError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Authorization, path resolution, command building, and launch stay false.
    Example: Construct with ``instance = ExecutionRequestError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_execution_request.py`` and request schemas.
    """


class ExecutionRequestService:
    """Purpose: Compose path-free request and audit previews from coherent planning evidence.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ExecutionRequestService`` exposing the state and operations defined below.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Authorization, path resolution, command building, and launch stay false.
    Example: Construct with ``instance = ExecutionRequestService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_execution_request.py`` and request schemas.
    """

    def __init__(
        self,
        root: Path | None = None,
        tool_dry_run: ToolDryRunService | None = None,
        execution_gate: ExecutionGateService | None = None,
    ) -> None:
        """Purpose: Bind one dry-run source, its gate evaluator, and the committed preview policy.

        Inputs: Caller-supplied ``root``, ``tool_dry_run``, ``execution_gate`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, path resolution, command building, and launch stay false.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_execution_request.py`` and request schemas.
        """

        self.tool_dry_run = tool_dry_run or ToolDryRunService(root or ROOT)
        self.root = root or self.tool_dry_run.root
        self.execution_gate = execution_gate or ExecutionGateService(self.root, self.tool_dry_run)
        self.policy_path = self.root / "config" / "execution_request_policy.json"

    def execution_request_policy(self) -> dict[str, Any]:
        """Purpose: Validate single-route scope, complete audit events, and constant-false effects.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Authorization, path resolution, command building, and launch stay false.
        Example: Call ``result = instance.execution_request_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_execution_request.py`` and request schemas.
        """

        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise ExecutionRequestError("execution request policy must be a structured record")
        if policy.get("schemaVersion") != "makers-anvil.config.execution-request-policy.v1":
            raise ExecutionRequestError("execution request policy schema version is not supported")
        if policy.get("mode") != "read-only-request-preview":
            raise ExecutionRequestError("execution request policy must remain a read-only preview")

        safety = policy.get("safety")
        if not isinstance(safety, dict) or set(safety) != REQUEST_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise ExecutionRequestError("execution request policy cannot persist, authorize, write audit events, resolve, execute, or prove")

        scope = policy.get("scope")
        expected_scope = {
            "routeId": "mesh-to-toolpath",
            "requestPersistenceEnabled": False,
            "authorizationEnabled": False,
            "auditWriteEnabled": False,
        }
        if scope != expected_scope:
            raise ExecutionRequestError("execution request scope must remain one disabled mesh-to-toolpath preview")

        audit = policy.get("audit")
        event_types = audit.get("requiredEventTypes") if isinstance(audit, dict) else None
        if (
            not isinstance(audit, dict)
            or audit.get("appendOnly") is not True
            or audit.get("eventWritesEnabled") is not False
            or not isinstance(event_types, list)
            or len(event_types) != len(set(event_types))
            or set(event_types) != REQUIRED_AUDIT_EVENTS
        ):
            raise ExecutionRequestError("execution request policy requires the complete append-only audit lifecycle with writes disabled")

        gate_scope = self.execution_gate.execution_gate_policy()["scope"]["routeId"]
        if gate_scope != scope["routeId"]:
            raise ExecutionRequestError("execution request and gate policies must use the same single route")
        return policy

    def preview_catalog(
        self,
        dry_run_snapshot: dict[str, Any] | None = None,
        gate_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Purpose: Return deterministic request previews while all persistence and actions stay false.

        Inputs: Caller-supplied ``dry_run_snapshot``, ``gate_snapshot`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, path resolution, command building, and launch stay false.
        Example: Call ``result = instance.preview_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_execution_request.py`` and request schemas.
        """

        dry_run = dry_run_snapshot if dry_run_snapshot is not None else self.tool_dry_run.plan_catalog()
        gates = gate_snapshot if gate_snapshot is not None else self.execution_gate.gate_catalog(dry_run)
        policy = self.execution_request_policy()
        route_id = policy["scope"]["routeId"]
        in_scope_plans = [plan for plan in dry_run["plans"] if plan["route"]["id"] == route_id]
        evaluations = {
            evaluation["dryRunPlanId"]: evaluation
            for evaluation in gates["evaluations"]
            if evaluation["route"]["id"] == route_id
        }
        previews = [
            self._build_preview(plan, evaluations[plan["id"]], policy)
            for plan in in_scope_plans
            if plan["id"] in evaluations
        ]
        unmatched_count = len(in_scope_plans) - len(previews)
        upstream_failed = dry_run.get("claimState") == "failed" or gates.get("claimState") == "failed"
        blocked_action = {"claimState": "blocked", "enabledInApi": False}
        return {
            "schemaVersion": "makers-anvil.api.execution-request-preview.v1",
            "claimState": "failed" if upstream_failed or unmatched_count else "blocked",
            "mode": policy["mode"],
            "scope": policy["scope"],
            "summary": {
                "dryRunPlanCount": len(in_scope_plans),
                "gateEvaluationCount": len(evaluations),
                "previewCount": len(previews),
                "unmatchedPlanCount": unmatched_count,
                "persistedRequestCount": 0,
                "acceptedAuthorizationCount": 0,
                "writtenAuditEventCount": 0,
                "executionReadyCount": 0,
            },
            "previews": previews,
            "safety": policy["safety"],
            "actions": {
                "createRequest": blocked_action,
                "recordAuthorization": blocked_action.copy(),
                "execute": blocked_action.copy(),
            },
        }

    @staticmethod
    def _build_preview(plan: dict[str, Any], evaluation: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Translate one coherent plan and gate record into immutable logical intent.

        Inputs: Caller-supplied ``plan``, ``evaluation``, ``policy`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, path resolution, command building, and launch stay false.
        Example: Call ``result = instance._build_preview(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_execution_request.py`` and request schemas.
        """

        selected_tool = plan["toolSelection"]["selectedTool"]
        tool = None if selected_tool is None else {
            "id": selected_tool["id"],
            "label": selected_tool["label"],
            "claimState": "detected",
        }
        # Upstream blockers remain visible, then preview-specific missing capabilities
        # are appended once so planning evidence can never imply execution readiness.
        blockers = list(evaluation["readiness"]["blockers"])
        blockers.extend([
            "request persistence is disabled",
            "user authorization is not accepted",
            "audit event writing is disabled",
        ])
        return {
            "id": f"execution-request-preview-{plan['id']}",
            "claimState": "blocked",
            "dryRunPlanId": plan["id"],
            "gateEvaluationId": evaluation["id"],
            "route": {"id": plan["route"]["id"], "label": plan["route"]["label"]},
            "operation": dict(plan["invocation"]["operation"]),
            "intent": {
                "source": {
                    "intakeId": plan["source"]["intakeId"],
                    "logicalReference": plan["source"]["logicalReference"],
                },
                "output": {
                    "bundleId": plan["output"]["bundleId"],
                    "logicalDirectory": plan["output"]["logicalDirectory"],
                },
                "tool": tool,
            },
            "authorization": {"required": True, "accepted": False, "actor": None, "acceptedAt": None},
            "audit": {
                "appendOnly": True,
                "requiredEventTypes": list(policy["audit"]["requiredEventTypes"]),
                "events": [],
                "recordCreated": False,
            },
            "readiness": {
                "previewAvailable": True,
                "requestPersistenceReady": False,
                "authorizationReady": False,
                "auditReady": False,
                "executionReady": False,
                "blockers": list(dict.fromkeys(blockers)),
            },
        }
