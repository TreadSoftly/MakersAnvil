"""Purpose: Explain and prove single-route execution-gate evaluation.

Used by: Developers and CI before any operational execution work can advance.
Inputs: Isolated policies and crafted dry-run snapshots.
Outputs: Assertions for evidence mapping, blockers, scope, and false effects.
Side effects: Temporary files only.
Safety: Authorization, process, logging, cancellation, and proof stay unproven.
Failure behavior: Any optimistic or broadened gate result fails its example.
Related proof: ``services/execution_gate.py`` and execution-gate schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.execution_gate import ExecutionGateError, ExecutionGateService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _StubDryRun:
    """Purpose: Provide isolated dry-run policy and plan snapshots to the gate evaluator.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``_StubDryRun`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Construct with ``instance = _StubDryRun(...)`` using values described by ``__init__``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    def __init__(self, root: Path, snapshot: dict) -> None:
        """Purpose: Store the isolated root and dry-run snapshot used by one evaluator test.

        Inputs: Caller-supplied ``root``, ``snapshot`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, process, logging, cancellation, and proof stay unproven.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``services/execution_gate.py`` and execution-gate schemas.
        """

        self.root = root
        self._snapshot = snapshot

    def dry_run_policy(self) -> dict:
        """Purpose: Return the configured route universe needed for scope validation.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, process, logging, cancellation, and proof stay unproven.
        Example: Call ``result = instance.dry_run_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``services/execution_gate.py`` and execution-gate schemas.
        """

        return {"routes": [{"routeId": "mesh-to-toolpath"}, {"routeId": "cad-to-mesh"}]}

    def plan_catalog(self) -> dict:
        """Purpose: Return the injected non-runnable plan snapshot.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Authorization, process, logging, cancellation, and proof stay unproven.
        Example: Call ``result = instance.plan_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``services/execution_gate.py`` and execution-gate schemas.
        """

        return self._snapshot


def make_plan(route_id: str = "mesh-to-toolpath", with_tool: bool = True) -> dict:
    """Purpose: Create the minimum semantic plan record consumed by gate evaluation.

    Inputs: Caller-supplied ``route_id``, ``with_tool`` values from the signature.
    Outputs: Returns ``dict``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Call ``result = instance.make_plan(...)`` with values satisfying the documented inputs.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    selected = {"id": "prusaslicer", "label": "PrusaSlicer"} if with_tool else None
    return {
        "id": f"dry-run-{route_id}",
        "route": {"id": route_id, "label": route_id.replace("-", " ").title()},
        "toolSelection": {"selectedTool": selected},
        "readiness": {"planAvailable": True, "toolCandidateAvailable": with_tool},
    }


def build_service(tmp_path: Path, plans: list[dict]) -> ExecutionGateService:
    """Purpose: Build an isolated evaluator using the committed gate policy and injected plans.

    Inputs: Caller-supplied ``tmp_path``, ``plans`` values from the signature.
    Outputs: Returns ``ExecutionGateService``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Call ``result = instance.build_service(...)`` with values satisfying the documented inputs.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    root = tmp_path / "source"
    config = root / "config"
    config.mkdir(parents=True)
    config.joinpath("execution_gate_policy.json").write_text(
        PROJECT_ROOT.joinpath("config", "execution_gate_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    snapshot = {"claimState": "preview-only", "plans": plans}
    return ExecutionGateService(root, _StubDryRun(root, snapshot))


def test_in_scope_mesh_plan_satisfies_only_available_planning_evidence(tmp_path: Path) -> None:
    """Purpose: Route, dry-run, and tool evidence pass while every operational gate stays blocked.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_in_scope_mesh_plan_satisfies_only_available_planning_evidence``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    service = build_service(tmp_path, [make_plan()])

    result = service.gate_catalog()

    assert result["claimState"] == "blocked"
    assert result["scope"] == {
        "routeId": "mesh-to-toolpath",
        "singleRoute": True,
        "maxConcurrentExecutions": 1,
        "executionEnabled": False,
        "claimState": "staged",
    }
    assert result["summary"] == {
        "dryRunPlanCount": 1,
        "evaluatedPlanCount": 1,
        "outOfScopePlanCount": 0,
        "requiredGateCount": 10,
        "satisfiedGateCount": 3,
        "blockedPlanCount": 1,
    }
    evaluation = result["evaluations"][0]
    assert [gate["id"] for gate in evaluation["gates"] if gate["satisfied"]] == [
        "route-allowlisted",
        "dry-run-plan-available",
        "detected-tool-candidate",
    ]
    assert evaluation["readiness"]["executionReady"] is False
    assert evaluation["readiness"]["authorizationReady"] is False
    assert all(value is False for value in result["safety"].values())


def test_out_of_scope_plan_is_counted_but_never_evaluated(tmp_path: Path) -> None:
    """Purpose: A CAD plan cannot enter the mesh route's single-route execution scope.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_out_of_scope_plan_is_counted_but_never_evaluated``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    result = build_service(tmp_path, [make_plan("cad-to-mesh")]).gate_catalog()

    assert result["evaluations"] == []
    assert result["summary"]["outOfScopePlanCount"] == 1
    assert result["summary"]["evaluatedPlanCount"] == 0
    assert result["executionAction"]["enabledInApi"] is False


def test_missing_tool_keeps_compatibility_gate_not_proven(tmp_path: Path) -> None:
    """Purpose: Planning evidence cannot substitute for a detected compatible tool candidate.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_missing_tool_keeps_compatibility_gate_not_proven``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    evaluation = build_service(tmp_path, [make_plan(with_tool=False)]).gate_catalog()["evaluations"][0]
    tool_gate = next(gate for gate in evaluation["gates"] if gate["id"] == "detected-tool-candidate")

    assert evaluation["tool"] is None
    assert tool_gate["satisfied"] is False
    assert tool_gate["claimState"] == "not proven"
    assert evaluation["readiness"]["compatibilityReady"] is False


def test_policy_rejects_enabled_or_missing_safety_flags(tmp_path: Path) -> None:
    """Purpose: No policy edit can silently create authorization, process, logging, or proof behavior.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_policy_rejects_enabled_or_missing_safety_flags``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    service = build_service(tmp_path, [])
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["safety"]["processStarted"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionGateError, match="cannot authorize"):
        service.gate_catalog()

    policy["safety"]["processStarted"] = False
    policy["safety"].pop("executionRequestCreated")
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionGateError, match="cannot authorize"):
        service.gate_catalog()


def test_policy_rejects_unknown_route_or_broadened_concurrency(tmp_path: Path) -> None:
    """Purpose: Execution scope cannot name an unknown route or allow parallel future jobs.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_policy_rejects_unknown_route_or_broadened_concurrency``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    service = build_service(tmp_path, [])
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["scope"]["routeId"] = "unknown-route"
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionGateError, match="configured dry-run route"):
        service.gate_catalog()

    policy["scope"]["routeId"] = "mesh-to-toolpath"
    policy["scope"]["maxConcurrentExecutions"] = 2
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionGateError, match="one disabled route"):
        service.gate_catalog()


def test_policy_requires_every_unique_evidence_source(tmp_path: Path) -> None:
    """Purpose: Removing or duplicating a gate cannot bypass a required execution concern.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Authorization, process, logging, cancellation, and proof stay unproven.
    Example: Run ``python -m pytest tests/test_execution_gate.py -k test_policy_requires_every_unique_evidence_source``.
    Related proof: ``services/execution_gate.py`` and execution-gate schemas.
    """

    service = build_service(tmp_path, [])
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["gates"].pop()
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ExecutionGateError, match="every required evidence source"):
        service.gate_catalog()
