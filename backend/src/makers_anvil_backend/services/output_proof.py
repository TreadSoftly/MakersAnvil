"""Purpose: Derive expected artifacts and evidence from route previews.

Used by: ``AppStateService`` after metadata-only route planning.
Inputs: Output policy, workspace policy, and a coherent route snapshot.
Outputs: Logical bundle plans with nonexistent artifacts and incomplete proof.
Side effects: None; no output directory, file, preview, or proof is created.
Safety: Planned output is never presented as produced or verified output.
Failure behavior: Invalid policy or route joins raise clear validation errors.
Related proof: ``tests/test_output_proof.py`` and output schemas.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[4]
OUTPUT_SAFETY_FLAGS = {
    "outputDirectoryCreated",
    "outputFileCreated",
    "outputFileOpened",
    "proofCaptured",
    "sourceFileOpened",
    "routeExecuted",
    "toolLaunched",
}
ARTIFACT_ROLES = {"primary", "manifest", "proof"}
EVIDENCE_TYPES = {"record", "log", "digest"}


class OutputProofError(ValueError):
    """Purpose: Raised when output policy could invent, create, open, or overstate evidence.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``OutputProofError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Planned output is never presented as produced or verified output.
    Example: Construct with ``instance = OutputProofError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_output_proof.py`` and output schemas.
    """


class OutputProofService:
    """Purpose: Derive non-writing output plans from route previews and committed policy.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``OutputProofService`` exposing the state and operations defined below.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Planned output is never presented as produced or verified output.
    Example: Construct with ``instance = OutputProofService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_output_proof.py`` and output schemas.
    """

    def __init__(
        self,
        root: Path | None = None,
        route_preview: RoutePreviewService | None = None,
        workspace_config: WorkspaceConfigService | None = None,
    ) -> None:
        """Purpose: Bind route planning, workspace policy, and the non-writing output contract.

        Inputs: Caller-supplied ``root``, ``route_preview``, ``workspace_config`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Planned output is never presented as produced or verified output.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        self.root = root or ROOT
        self.route_preview = route_preview or RoutePreviewService(self.root)
        self.workspace_config = workspace_config or self.route_preview.intake_catalog.workspace_config
        self.policy_path = self.root / "config" / "output_policy.json"

    def output_policy(self) -> dict[str, Any]:
        """Purpose: Load and validate output planning, route coverage, and false safety state.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Planned output is never presented as produced or verified output.
        Example: Call ``result = instance.output_policy(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise OutputProofError("output policy must be a structured record")
        if policy.get("schemaVersion") != "makers-anvil.config.output-policy.v1":
            raise OutputProofError("output policy schema version is not supported")
        if policy.get("mode") != "route-derived-read-only":
            raise OutputProofError("output policy must remain route-derived and read-only")
        logical_root = self.workspace_config.logical_runtime_path("outputs")
        if policy.get("logicalRoot") != logical_root:
            raise OutputProofError("output policy logical root must match app-owned output storage")
        safety = policy.get("safety")
        if not isinstance(safety, dict) or set(safety) != OUTPUT_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise OutputProofError("output policy cannot create, open, execute, launch, or capture proof")

        bundles = policy.get("bundles")
        proof = policy.get("requiredProof")
        if not isinstance(bundles, list) or not bundles:
            raise OutputProofError("output policy requires bundle definitions")
        if not isinstance(proof, list) or not proof:
            raise OutputProofError("output policy requires proof definitions")
        self._validate_bundles(bundles)
        self._validate_proof(proof)

        configured_routes = {route["id"] for route in self.route_preview.route_catalog()["routes"]}
        covered_routes = {bundle["routeId"] for bundle in bundles}
        if covered_routes != configured_routes:
            raise OutputProofError("output policy must cover every configured route exactly once")
        return policy

    def preview_catalog(self, route_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        """Purpose: Return planned bundles and incomplete proof items for one route snapshot.

        Inputs: Caller-supplied ``route_snapshot`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Planned output is never presented as produced or verified output.
        Example: Call ``result = instance.preview_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        routes = route_snapshot if route_snapshot is not None else self.route_preview.preview_catalog()
        policy = self.output_policy()
        policies_by_route = {bundle["routeId"]: bundle for bundle in policy["bundles"]}
        bundles: list[dict[str, Any]] = []
        unmatched_count = 0
        for route in routes["previews"]:
            bundle_policy = policies_by_route.get(route["route"]["id"])
            if bundle_policy is None:
                unmatched_count += 1
                continue
            bundles.append(self._build_bundle(route, bundle_policy, policy))

        artifact_count = sum(len(bundle["artifacts"]) for bundle in bundles)
        required_proof_count = sum(len(bundle["proof"]) for bundle in bundles)
        return {
            "schemaVersion": "makers-anvil.api.output-proof.v1",
            "claimState": "failed" if routes.get("claimState") == "failed" or unmatched_count else "preview-only",
            "mode": policy["mode"],
            "logicalRoot": policy["logicalRoot"],
            "summary": {
                "routePreviewCount": len(routes["previews"]),
                "bundleCount": len(bundles),
                "unmatchedRouteCount": unmatched_count,
                "artifactCount": artifact_count,
                "requiredProofCount": required_proof_count,
                "completedProofCount": 0,
            },
            "bundles": bundles,
            "safety": policy["safety"],
            "actions": {
                "create": {"claimState": "blocked", "enabledInApi": False},
                "open": {"claimState": "blocked", "enabledInApi": False},
            },
        }

    @staticmethod
    def _validate_bundles(bundles: list[dict[str, Any]]) -> None:
        """Purpose: Reject ambiguous routes, malformed artifacts, and unsupported artifact roles.

        Inputs: Caller-supplied ``bundles`` values from the signature.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Planned output is never presented as produced or verified output.
        Example: Call ``result = instance._validate_bundles(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        bundle_ids: set[str] = set()
        route_ids: set[str] = set()
        for bundle in bundles:
            if not isinstance(bundle, dict):
                raise OutputProofError("every output bundle must be a structured record")
            if not all(isinstance(bundle.get(field), str) and bundle[field] for field in ("id", "routeId", "label")):
                raise OutputProofError("output bundles require ids, route ids, and labels")
            if bundle["id"] in bundle_ids or bundle["routeId"] in route_ids:
                raise OutputProofError("bundle ids and route ids must be unique")
            artifacts = bundle.get("artifacts")
            if not isinstance(artifacts, list) or not artifacts or not all(isinstance(item, dict) for item in artifacts):
                raise OutputProofError("every output bundle requires artifact definitions")
            artifact_ids = [item.get("id") for item in artifacts]
            if len(set(artifact_ids)) != len(artifact_ids):
                raise OutputProofError("artifact ids must be unique within a bundle")
            if not all(
                isinstance(item.get("id"), str)
                and item["id"]
                and isinstance(item.get("label"), str)
                and item["label"]
                and item.get("role") in ARTIFACT_ROLES
                and isinstance(item.get("suggestedExtension"), str)
                and re.fullmatch(r"\.[a-z0-9]+", item["suggestedExtension"]) is not None
                for item in artifacts
            ):
                raise OutputProofError("artifacts require ids, labels, roles, and suggested extensions")
            bundle_ids.add(bundle["id"])
            route_ids.add(bundle["routeId"])

    @staticmethod
    def _validate_proof(proof: list[dict[str, Any]]) -> None:
        """Purpose: Require unique proof definitions with supported evidence types.

        Inputs: Caller-supplied ``proof`` values from the signature.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It checks conditions.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Planned output is never presented as produced or verified output.
        Example: Call ``result = instance._validate_proof(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        if not all(isinstance(item, dict) for item in proof):
            raise OutputProofError("proof definitions must be structured records")
        proof_ids = [item.get("id") for item in proof]
        if len(set(proof_ids)) != len(proof_ids):
            raise OutputProofError("proof ids must be unique")
        if not all(
            isinstance(item.get("id"), str)
            and item["id"]
            and isinstance(item.get("label"), str)
            and item["label"]
            and item.get("evidenceType") in EVIDENCE_TYPES
            for item in proof
        ):
            raise OutputProofError("proof definitions require ids, labels, and supported evidence types")

    @staticmethod
    def _build_bundle(
        route: dict[str, Any],
        bundle_policy: dict[str, Any],
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Purpose: Translate one route preview into a bundle plan with no completed evidence.

        Inputs: Caller-supplied ``route``, ``bundle_policy``, ``policy`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Planned output is never presented as produced or verified output.
        Example: Call ``result = instance._build_bundle(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_output_proof.py`` and output schemas.
        """

        blockers = list(dict.fromkeys([
            *route["readiness"]["blockers"],
            "output creation blocked",
            "output opening blocked",
            "proof capture not proven",
        ]))
        return {
            "id": f"bundle-{route['id']}-{bundle_policy['id']}",
            "claimState": "preview-only",
            "routePreviewId": route["id"],
            "source": dict(route["source"]),
            "output": {
                "bundleType": bundle_policy["id"],
                "label": bundle_policy["label"],
                "logicalDirectory": f"{policy['logicalRoot']}/{route['source']['intakeId']}",
            },
            "artifacts": [
                {
                    **artifact,
                    "claimState": "planned",
                    "exists": False,
                    "openEnabled": False,
                }
                for artifact in bundle_policy["artifacts"]
            ],
            "proof": [
                {
                    **proof,
                    "claimState": "not proven",
                    "complete": False,
                }
                for proof in policy["requiredProof"]
            ],
            "readiness": {
                "bundlePlanAvailable": True,
                "creationReady": False,
                "openReady": False,
                "proofComplete": False,
                "blockers": blockers,
            },
        }
