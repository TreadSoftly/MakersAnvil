"""Purpose: Evaluate whether one allowlisted route has required evidence.

Used by: ``AppStateService`` after semantic tool dry-run planning.
Inputs: Gate policy plus a coherent dry-run snapshot.
Outputs: Per-plan evidence gates and an always-blocked execution action.
Side effects: None; evaluation does not authorize, persist, or execute work.
Safety: Operational gates remain unsatisfied until real evidence exists.
Failure behavior: Malformed or weakened policy raises ``ValueError``.
Related proof: ``tests/test_execution_gate.py`` and gate schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.tool_dry_run import ToolDryRunService


ROOT = Path(__file__).resolve().parents[4]
GATE_CATEGORIES = {"scope", "planning", "authorization", "containment", "compatibility", "control", "observability", "proof"}
GATE_EVIDENCE_SOURCES = {
    "route-scope",
    "dry-run-plan",
    "tool-candidate",
    "user-authorization",
    "source-containment",
    "output-containment",
    "tool-version",
    "cancellation-channel",
    "execution-log",
    "output-proof",
}
EXECUTION_SAFETY_FLAGS = {
    "executionRequestCreated",
    "userAuthorizationAccepted",
    "sourcePathResolved",
    "outputPathResolved",
    "commandConstructed",
    "processStarted",
    "toolLaunched",
    "filesystemWritten",
    "executionLogWritten",
    "cancellationSignalSent",
    "proofCaptured",
}


class ExecutionGateError(ValueError):
    """Raised when gate policy broadens scope or weakens an execution boundary."""


class ExecutionGateService:
    """Evaluate required evidence for one route while execution remains impossible."""

    def __init__(self, root: Path | None = None, tool_dry_run: ToolDryRunService | None = None) -> None:
        """Bind one dry-run source and the committed single-route gate policy."""

        self.tool_dry_run = tool_dry_run or ToolDryRunService(root or ROOT)
        self.root = root or self.tool_dry_run.root
        self.policy_path = self.root / "config" / "execution_gate_policy.json"

    def execution_gate_policy(self) -> dict[str, Any]:
        """Validate one-route scope, complete gate evidence, and constant-false safety."""

        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise ExecutionGateError("execution gate policy must be a structured record")
        if policy.get("schemaVersion") != "makers-anvil.config.execution-gate-policy.v1":
            raise ExecutionGateError("execution gate policy schema version is not supported")
        if policy.get("mode") != "read-only-gate-evaluation":
            raise ExecutionGateError("execution gate policy must remain read-only evaluation")
        safety = policy.get("safety")
        if not isinstance(safety, dict) or set(safety) != EXECUTION_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise ExecutionGateError("execution gate policy cannot authorize, resolve, construct, execute, launch, write, cancel, or capture proof")
        scope = policy.get("scope")
        if (
            not isinstance(scope, dict)
            or set(scope) != {"routeId", "maxConcurrentExecutions", "executionEnabled"}
            or scope.get("maxConcurrentExecutions") != 1
            or scope.get("executionEnabled") is not False
        ):
            raise ExecutionGateError("execution scope must contain one disabled route and one future concurrency slot")
        known_routes = {item["routeId"] for item in self.tool_dry_run.dry_run_policy()["routes"]}
        if scope.get("routeId") not in known_routes:
            raise ExecutionGateError("execution scope must name one configured dry-run route")
        gates = policy.get("gates")
        if not isinstance(gates, list) or not gates or not all(isinstance(item, dict) for item in gates):
            raise ExecutionGateError("execution gate policy requires structured gates")
        self._validate_gates(gates)
        return policy

    def gate_catalog(self, dry_run_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return read-only gate evaluations for in-scope semantic dry-run plans."""

        dry_run = dry_run_snapshot if dry_run_snapshot is not None else self.tool_dry_run.plan_catalog()
        policy = self.execution_gate_policy()
        route_id = policy["scope"]["routeId"]
        in_scope = [plan for plan in dry_run["plans"] if plan["route"]["id"] == route_id]
        out_of_scope_count = len(dry_run["plans"]) - len(in_scope)
        evaluations = [self._build_evaluation(plan, policy) for plan in in_scope]
        satisfied_count = sum(gate["satisfied"] for evaluation in evaluations for gate in evaluation["gates"])
        required_count = sum(len(evaluation["gates"]) for evaluation in evaluations)
        return {
            "schemaVersion": "makers-anvil.api.execution-gates.v1",
            "claimState": "failed" if dry_run.get("claimState") == "failed" else "blocked",
            "mode": policy["mode"],
            "scope": {
                "routeId": route_id,
                "singleRoute": True,
                "maxConcurrentExecutions": 1,
                "executionEnabled": False,
                "claimState": "staged",
            },
            "summary": {
                "dryRunPlanCount": len(dry_run["plans"]),
                "evaluatedPlanCount": len(evaluations),
                "outOfScopePlanCount": out_of_scope_count,
                "requiredGateCount": required_count,
                "satisfiedGateCount": satisfied_count,
                "blockedPlanCount": len(evaluations),
            },
            "evaluations": evaluations,
            "safety": policy["safety"],
            "executionAction": {"claimState": "blocked", "enabledInApi": False},
        }

    @staticmethod
    def _validate_gates(gates: list[dict[str, Any]]) -> None:
        """Require unique gates and exactly one source for every required evidence class."""

        ids: set[str] = set()
        sources: set[str] = set()
        for gate in gates:
            if not all(isinstance(gate.get(field), str) and gate[field] for field in ("id", "label", "category", "evidenceSource")):
                raise ExecutionGateError("execution gates require identity, labels, categories, and evidence sources")
            if gate["id"] in ids or gate["evidenceSource"] in sources or gate.get("required") is not True:
                raise ExecutionGateError("execution gates and evidence sources must be unique and required")
            if gate["category"] not in GATE_CATEGORIES or gate["evidenceSource"] not in GATE_EVIDENCE_SOURCES:
                raise ExecutionGateError("execution gates use an unsupported category or evidence source")
            ids.add(gate["id"])
            sources.add(gate["evidenceSource"])
        if sources != GATE_EVIDENCE_SOURCES:
            raise ExecutionGateError("execution gate policy must cover every required evidence source exactly once")

    @classmethod
    def _build_evaluation(cls, plan: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Evaluate available planning evidence while leaving operational gates unsatisfied."""

        gates = [cls._evaluate_gate(gate, plan, policy["scope"]["routeId"]) for gate in policy["gates"]]
        selected_tool = plan["toolSelection"]["selectedTool"]
        tool = None if selected_tool is None else {
            "id": selected_tool["id"],
            "label": selected_tool["label"],
            "claimState": "detected",
        }
        blockers = [gate["label"] for gate in gates if not gate["satisfied"]]
        return {
            "id": f"gate-evaluation-{plan['id']}",
            "claimState": "blocked",
            "dryRunPlanId": plan["id"],
            "route": {"id": plan["route"]["id"], "label": plan["route"]["label"], "claimState": "staged"},
            "tool": tool,
            "gates": gates,
            "readiness": {
                "gateContractAvailable": True,
                "authorizationReady": False,
                "containmentReady": False,
                "compatibilityReady": False,
                "cancellationReady": False,
                "loggingReady": False,
                "proofReady": False,
                "executionReady": False,
                "blockers": blockers,
            },
        }

    @staticmethod
    def _evaluate_gate(gate: dict[str, Any], plan: dict[str, Any], route_id: str) -> dict[str, Any]:
        """Map only existing planning evidence; operational sources remain not proven."""

        source = gate["evidenceSource"]
        satisfied = False
        claim_state = "not proven"
        evidence = "not proven"
        if source == "route-scope":
            satisfied = plan["route"]["id"] == route_id
            claim_state = "proven" if satisfied else "not proven"
            evidence = "single-route policy match" if satisfied else "not proven"
        elif source == "dry-run-plan":
            satisfied = plan["readiness"]["planAvailable"] is True
            claim_state = "proven" if satisfied else "not proven"
            evidence = "semantic dry-run plan available" if satisfied else "not proven"
        elif source == "tool-candidate":
            satisfied = plan["readiness"]["toolCandidateAvailable"] is True
            claim_state = "detected" if satisfied else "not proven"
            selected = plan["toolSelection"]["selectedTool"]
            evidence = selected["label"] if satisfied and selected else "not proven"
        return {
            "id": gate["id"],
            "label": gate["label"],
            "category": gate["category"],
            "evidenceSource": source,
            "required": True,
            "satisfied": satisfied,
            "claimState": claim_state,
            "evidence": evidence,
        }
