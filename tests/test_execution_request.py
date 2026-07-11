"""Purpose: Explain and prove path-free request and audit-preview behavior.

Used by: Developers and CI when request, consent, or lifecycle contracts change.
Inputs: Isolated policy plus coherent and deliberately broken planning snapshots.
Outputs: Assertions for logical intent, unaccepted consent, and empty audits.
Side effects: Temporary files only; no request or event is persisted.
Safety: Command, path, process, launch, write, and proof effects remain false.
Failure behavior: Missing joins and weakened policies must fail closed.
Related proof: ``services/execution_request.py`` and request schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.execution_request import ExecutionRequestError, ExecutionRequestService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _StubDryRun:
    """Purpose: Provide isolated semantic plans without reading runtime intake or tools.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``_StubDryRun`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Construct with ``instance = _StubDryRun(...)`` using values described by ``__init__``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    def __init__(self, root: Path, snapshot: dict) -> None:
        """Purpose: Store the temporary project root and injected dry-run snapshot.

        Inputs: Caller-supplied ``root``, ``snapshot`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Command, path, process, launch, write, and proof effects remain false.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``services/execution_request.py`` and request schemas.
        """

        self.root = root
        self._snapshot = snapshot

    def plan_catalog(self) -> dict:
        """Purpose: Return the injected non-runnable planning snapshot.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Command, path, process, launch, write, and proof effects remain false.
        Example: Call ``result = instance.plan_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``services/execution_request.py`` and request schemas.
        """

        return self._snapshot


class _StubGate:
    """Purpose: Provide matching gate policy and evaluation snapshots for request tests.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``_StubGate`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Construct with ``instance = _StubGate(...)`` using values described by ``__init__``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    def __init__(self, snapshot: dict) -> None:
        """Purpose: Store one isolated gate snapshot.

        Inputs: Caller-supplied ``snapshot`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Command, path, process, launch, write, and proof effects remain false.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``services/execution_request.py`` and request schemas.
        """

        self._snapshot = snapshot

    def execution_gate_policy(self) -> dict:
        """Purpose: Return the single-route scope required for policy coherence checks.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Command, path, process, launch, write, and proof effects remain false.
        Example: Call ``result = instance.execution_gate_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``services/execution_request.py`` and request schemas.
        """

        return {"scope": {"routeId": "mesh-to-toolpath"}}

    def gate_catalog(self, dry_run_snapshot: dict) -> dict:
        """Purpose: Return the injected gate snapshot while accepting the coherent dry run.

        Inputs: Caller-supplied ``dry_run_snapshot`` values from the signature.
        Outputs: Returns ``dict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Command, path, process, launch, write, and proof effects remain false.
        Example: Call ``result = instance.gate_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``services/execution_request.py`` and request schemas.
        """

        assert dry_run_snapshot["plans"]
        return self._snapshot


def make_plan(with_tool: bool = True) -> dict:
    """Purpose: Create one path-free mesh toolpath plan consumed by request previewing.

    Inputs: Caller-supplied ``with_tool`` values from the signature.
    Outputs: Returns ``dict``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Call ``result = instance.make_plan(...)`` with values satisfying the documented inputs.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    tool = {"id": "prusaslicer", "label": "PrusaSlicer"} if with_tool else None
    return {
        "id": "dry-run-route-preview-intake-123-mesh-to-toolpath",
        "source": {
            "intakeId": "intake-123",
            "logicalReference": "makers-anvil-intake://records/intake-123",
        },
        "route": {"id": "mesh-to-toolpath", "label": "Mesh to Toolpath"},
        "output": {
            "bundleId": "output-bundle-123",
            "logicalDirectory": "makers-anvil-data://user/outputs/output-bundle-123",
        },
        "toolSelection": {"selectedTool": tool},
        "invocation": {"operation": {"id": "slice-mesh", "label": "Slice mesh"}},
    }


def make_gate_snapshot(plan: dict, include_evaluation: bool = True) -> dict:
    """Purpose: Create blocked gate evidence matching one semantic plan.

    Inputs: Caller-supplied ``plan``, ``include_evaluation`` values from the signature.
    Outputs: Returns ``dict``, or raises before returning when validation fails.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Call ``result = instance.make_gate_snapshot(...)`` with values satisfying the documented inputs.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    evaluations = []
    if include_evaluation:
        evaluations.append({
            "id": f"gate-evaluation-{plan['id']}",
            "dryRunPlanId": plan["id"],
            "route": {"id": "mesh-to-toolpath"},
            "readiness": {
                "blockers": ["Explicit user authorization is recorded", "Output workspace is resolved and contained"],
            },
        })
    return {"claimState": "blocked", "evaluations": evaluations}


def build_service(tmp_path: Path, plan: dict, include_evaluation: bool = True) -> ExecutionRequestService:
    """Purpose: Build an isolated service using committed policy and injected snapshots.

    Inputs: Caller-supplied ``tmp_path``, ``plan``, ``include_evaluation`` values from the signature.
    Outputs: Returns ``ExecutionRequestService``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Call ``result = instance.build_service(...)`` with values satisfying the documented inputs.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    root = tmp_path / "source"
    config = root / "config"
    config.mkdir(parents=True)
    config.joinpath("execution_request_policy.json").write_text(
        PROJECT_ROOT.joinpath("config", "execution_request_policy.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    dry_run = _StubDryRun(root, {"claimState": "preview-only", "plans": [plan]})
    gate = _StubGate(make_gate_snapshot(plan, include_evaluation))
    return ExecutionRequestService(root, dry_run, gate)


def test_preview_models_logical_intent_without_persistence_or_authorization(tmp_path: Path) -> None:
    """Purpose: One coherent plan produces deterministic intent while every action remains false.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Run ``python -m pytest tests/test_execution_request.py -k test_preview_models_logical_intent_without_persistence_or_authorization``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    result = build_service(tmp_path, make_plan()).preview_catalog()

    assert result["claimState"] == "blocked"
    assert result["summary"] == {
        "dryRunPlanCount": 1,
        "gateEvaluationCount": 1,
        "previewCount": 1,
        "unmatchedPlanCount": 0,
        "persistedRequestCount": 0,
        "acceptedAuthorizationCount": 0,
        "writtenAuditEventCount": 0,
        "executionReadyCount": 0,
    }
    preview = result["previews"][0]
    assert preview["intent"]["source"]["logicalReference"].startswith("makers-anvil-intake://")
    assert preview["intent"]["output"]["logicalDirectory"].startswith("makers-anvil-data://")
    assert preview["authorization"] == {"required": True, "accepted": False, "actor": None, "acceptedAt": None}
    assert preview["audit"]["events"] == []
    assert preview["audit"]["recordCreated"] is False
    assert preview["readiness"]["executionReady"] is False
    assert all(value is False for value in result["safety"].values())
    assert all(action["enabledInApi"] is False for action in result["actions"].values())


def test_missing_tool_remains_an_explicit_null_candidate(tmp_path: Path) -> None:
    """Purpose: A request preview never invents tool identity when detection found no candidate.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Run ``python -m pytest tests/test_execution_request.py -k test_missing_tool_remains_an_explicit_null_candidate``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    preview = build_service(tmp_path, make_plan(with_tool=False)).preview_catalog()["previews"][0]

    assert preview["intent"]["tool"] is None
    assert preview["readiness"]["executionReady"] is False


def test_missing_gate_evaluation_fails_closed_without_a_preview(tmp_path: Path) -> None:
    """Purpose: Planning intent cannot become a request preview without its matching gate record.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Run ``python -m pytest tests/test_execution_request.py -k test_missing_gate_evaluation_fails_closed_without_a_preview``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    result = build_service(tmp_path, make_plan(), include_evaluation=False).preview_catalog()

    assert result["claimState"] == "failed"
    assert result["previews"] == []
    assert result["summary"]["unmatchedPlanCount"] == 1


def test_policy_rejects_enabled_persistence_authorization_or_effects(tmp_path: Path) -> None:
    """Purpose: Policy edits cannot silently enable request writes, consent, processes, or outputs.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Run ``python -m pytest tests/test_execution_request.py -k test_policy_rejects_enabled_persistence_authorization_or_effects``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    service = build_service(tmp_path, make_plan())
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["scope"]["requestPersistenceEnabled"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionRequestError, match="one disabled"):
        service.preview_catalog()

    policy["scope"]["requestPersistenceEnabled"] = False
    policy["safety"]["processStarted"] = True
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ExecutionRequestError, match="cannot persist"):
        service.preview_catalog()


def test_policy_requires_complete_unique_audit_lifecycle(tmp_path: Path) -> None:
    """Purpose: Removing or duplicating an audit event cannot weaken future observability.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Command, path, process, launch, write, and proof effects remain false.
    Example: Run ``python -m pytest tests/test_execution_request.py -k test_policy_requires_complete_unique_audit_lifecycle``.
    Related proof: ``services/execution_request.py`` and request schemas.
    """

    service = build_service(tmp_path, make_plan())
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["audit"]["requiredEventTypes"].pop()
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ExecutionRequestError, match="complete append-only audit lifecycle"):
        service.preview_catalog()
