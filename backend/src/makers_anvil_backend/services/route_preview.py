"""Purpose: Match intake metadata to deterministic candidate work routes.

Used by: ``AppStateService`` after the intake catalog snapshot is built.
Inputs: Route catalog policy and validated metadata-only intake records.
Outputs: Planned route steps, tool-family needs, and explicit blockers.
Side effects: None; source files are not reopened, read, extracted, or launched.
Safety: Candidate planning never implies execution or output readiness.
Failure behavior: Unsupported metadata becomes unmatched; bad policy raises errors.
Related proof: ``tests/test_route_preview.py`` and route schemas.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.intake_catalog import IntakeCatalogService


ROOT = Path(__file__).resolve().parents[4]
ROUTE_PHASES = {"validation", "planning", "execution", "proof"}
ROUTE_SAFETY_FLAGS = {
    "sourcePathUsed",
    "sourceContentRead",
    "sourceFileOpened",
    "archiveExtractionEnabled",
    "routeExecutionEnabled",
    "toolLaunchEnabled",
    "outputCreationEnabled",
}


class RoutePreviewError(ValueError):
    """Purpose: Raised when the committed route catalog weakens the preview contract.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``RoutePreviewError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Candidate planning never implies execution or output readiness.
    Example: Construct with ``instance = RoutePreviewError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_route_preview.py`` and route schemas.
    """


class RoutePreviewService:
    """Purpose: Map intake metadata to deterministic plans without reopening source files.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``RoutePreviewService`` exposing the state and operations defined below.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Candidate planning never implies execution or output readiness.
    Example: Construct with ``instance = RoutePreviewService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_route_preview.py`` and route schemas.
    """

    def __init__(
        self,
        root: Path | None = None,
        intake_catalog: IntakeCatalogService | None = None,
    ) -> None:
        """Purpose: Bind metadata intake to committed deterministic route definitions.

        Inputs: Caller-supplied ``root``, ``intake_catalog`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Candidate planning never implies execution or output readiness.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_route_preview.py`` and route schemas.
        """

        self.root = root or ROOT
        self.intake_catalog = intake_catalog or IntakeCatalogService(self.root)
        self.catalog_path = self.root / "config" / "route_catalog.json"

    def route_catalog(self) -> dict[str, Any]:
        """Purpose: Load and validate the committed route definitions and safety flags.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Candidate planning never implies execution or output readiness.
        Example: Call ``result = instance.route_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_route_preview.py`` and route schemas.
        """

        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(catalog, dict):
            raise RoutePreviewError("route catalog must be a structured record")
        if catalog.get("schemaVersion") != "makers-anvil.config.route-catalog.v1":
            raise RoutePreviewError("route catalog schema version is not supported")
        if catalog.get("mode") != "metadata-derived-read-only":
            raise RoutePreviewError("route catalog must remain metadata-derived and read-only")
        routes = catalog.get("routes")
        required_proof = catalog.get("requiredProof")
        safety = catalog.get("safety")
        if not isinstance(routes, list) or not routes:
            raise RoutePreviewError("route catalog requires routes and proof blockers")
        if not isinstance(required_proof, list) or not required_proof or not all(isinstance(item, str) for item in required_proof):
            raise RoutePreviewError("route catalog requires routes and proof blockers")
        if not isinstance(safety, dict) or set(safety) != ROUTE_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise RoutePreviewError("route catalog cannot enable source, execution, tool, or output actions")

        accepted_kinds: set[str] = set()
        route_ids: set[str] = set()
        for route in routes:
            if not isinstance(route, dict):
                raise RoutePreviewError("every route must be a structured record")
            route_id = route.get("id")
            kinds = route.get("acceptedKinds", [])
            steps = route.get("steps", [])
            if not isinstance(route_id, str) or not route_id or route_id in route_ids:
                raise RoutePreviewError("route ids must be non-empty and unique")
            if not all(isinstance(route.get(field), str) and route[field] for field in ("label", "summary", "toolFamily")):
                raise RoutePreviewError("routes require labels, summaries, and tool families")
            if not isinstance(kinds, list) or not kinds or not all(isinstance(kind, str) and kind for kind in kinds):
                raise RoutePreviewError("each route requires one or more intake kinds")
            if len(set(kinds)) != len(kinds) or accepted_kinds.intersection(kinds):
                raise RoutePreviewError("each intake kind must map to at most one route")
            if not isinstance(steps, list) or not steps or not all(isinstance(step, dict) for step in steps):
                raise RoutePreviewError("route steps must be non-empty and unique within a route")
            if len({step.get("id") for step in steps}) != len(steps):
                raise RoutePreviewError("route steps must be non-empty and unique within a route")
            if not all(
                isinstance(step.get("id"), str)
                and step["id"]
                and isinstance(step.get("label"), str)
                and step["label"]
                and step.get("phase") in ROUTE_PHASES
                for step in steps
            ):
                raise RoutePreviewError("route steps require ids, labels, and approved phases")
            route_ids.add(route_id)
            accepted_kinds.update(kinds)
        return catalog

    def preview_catalog(self, intake_snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
        """Purpose: Return route candidates from one validated intake snapshot or a fresh read.

        Inputs: Caller-supplied ``intake_snapshot`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Candidate planning never implies execution or output readiness.
        Example: Call ``result = instance.preview_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_route_preview.py`` and route schemas.
        """

        intake = intake_snapshot if intake_snapshot is not None else self.intake_catalog.catalog()
        catalog = self.route_catalog()
        routes_by_kind = {
            kind: route
            for route in catalog["routes"]
            for kind in route["acceptedKinds"]
        }
        previews: list[dict[str, Any]] = []
        unmatched_count = 0
        for record in intake["records"]:
            route = routes_by_kind.get(record["source"]["kind"])
            if route is None:
                unmatched_count += 1
                continue
            previews.append(self._build_preview(record, route, catalog["requiredProof"]))

        invalid_count = intake["summary"]["invalidRecordCount"]
        return {
            "schemaVersion": "makers-anvil.api.route-preview.v1",
            "claimState": "failed" if invalid_count else "preview-only",
            "mode": catalog["mode"],
            "summary": {
                "sourceRecordCount": len(intake["records"]),
                "previewCount": len(previews),
                "unmatchedCount": unmatched_count,
                "invalidRecordCount": invalid_count,
            },
            "previews": previews,
            "safety": catalog["safety"],
            "executionAction": {
                "claimState": "blocked",
                "enabledInApi": False,
            },
        }

    @staticmethod
    def _build_preview(
        record: dict[str, Any],
        route: dict[str, Any],
        required_proof: list[str],
    ) -> dict[str, Any]:
        """Purpose: Translate one privacy-safe intake record into a non-actionable plan.

        Inputs: Caller-supplied ``record``, ``route``, ``required_proof`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Candidate planning never implies execution or output readiness.
        Example: Call ``result = instance._build_preview(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_route_preview.py`` and route schemas.
        """

        source = record["source"]
        # Only fields allowed by the intake privacy contract cross into preview
        # state; the original path and file bytes are never available here.
        return {
            "id": f"preview-{record['id']}-{route['id']}",
            "claimState": "preview-only",
            "source": {
                "intakeId": record["id"],
                "displayName": source["displayName"],
                "kind": source["kind"],
                "extension": source["extension"],
            },
            "route": {
                "id": route["id"],
                "label": route["label"],
                "summary": route["summary"],
                "toolFamily": route["toolFamily"],
            },
            "steps": [
                {
                    "order": order,
                    **step,
                    "claimState": "planned",
                    "actionEnabled": False,
                }
                for order, step in enumerate(route["steps"], start=1)
            ],
            "readiness": {
                "previewAvailable": True,
                "executionReady": False,
                "blockers": list(required_proof),
            },
        }
