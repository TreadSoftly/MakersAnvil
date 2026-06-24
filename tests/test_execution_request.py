"""Behavior examples for non-persisting execution request and audit previews."""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.execution_request import ExecutionRequestError, ExecutionRequestService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class _StubDryRun:
    """Provide isolated semantic plans without reading runtime intake or tools."""

    def __init__(self, root: Path, snapshot: dict) -> None:
        """Store the temporary project root and injected dry-run snapshot."""

        self.root = root
        self._snapshot = snapshot

    def plan_catalog(self) -> dict:
        """Return the injected non-runnable planning snapshot."""

        return self._snapshot


class _StubGate:
    """Provide matching gate policy and evaluation snapshots for request tests."""

    def __init__(self, snapshot: dict) -> None:
        """Store one isolated gate snapshot."""

        self._snapshot = snapshot

    def execution_gate_policy(self) -> dict:
        """Return the single-route scope required for policy coherence checks."""

        return {"scope": {"routeId": "mesh-to-toolpath"}}

    def gate_catalog(self, dry_run_snapshot: dict) -> dict:
        """Return the injected gate snapshot while accepting the coherent dry run."""

        assert dry_run_snapshot["plans"]
        return self._snapshot


def make_plan(with_tool: bool = True) -> dict:
    """Create one path-free mesh toolpath plan consumed by request previewing."""

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
    """Create blocked gate evidence matching one semantic plan."""

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
    """Build an isolated service using committed policy and injected snapshots."""

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
    """One coherent plan produces deterministic intent while every action remains false."""

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
    """A request preview never invents tool identity when detection found no candidate."""

    preview = build_service(tmp_path, make_plan(with_tool=False)).preview_catalog()["previews"][0]

    assert preview["intent"]["tool"] is None
    assert preview["readiness"]["executionReady"] is False


def test_missing_gate_evaluation_fails_closed_without_a_preview(tmp_path: Path) -> None:
    """Planning intent cannot become a request preview without its matching gate record."""

    result = build_service(tmp_path, make_plan(), include_evaluation=False).preview_catalog()

    assert result["claimState"] == "failed"
    assert result["previews"] == []
    assert result["summary"]["unmatchedPlanCount"] == 1


def test_policy_rejects_enabled_persistence_authorization_or_effects(tmp_path: Path) -> None:
    """Policy edits cannot silently enable request writes, consent, processes, or outputs."""

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
    """Removing or duplicating an audit event cannot weaken future observability."""

    service = build_service(tmp_path, make_plan())
    policy = json.loads(service.policy_path.read_text(encoding="utf-8"))
    policy["audit"]["requiredEventTypes"].pop()
    service.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ExecutionRequestError, match="complete append-only audit lifecycle"):
        service.preview_catalog()
