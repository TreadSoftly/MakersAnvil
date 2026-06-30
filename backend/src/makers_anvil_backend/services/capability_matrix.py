"""Purpose: Summarize supported maker input lanes from existing truthful contracts.

Used by: App state and the workbench capability-lane renderer.
Inputs: Intake policy/catalog, route previews, output plans, and tool detection.
Outputs: Path-redacted lane comparison with preview and execution boundaries.
Side effects: Reads existing service snapshots only.
Safety: Never launches, hands off, opens, installs, or changes a file or tool.
Failure behavior: Missing route coverage fails instead of inventing a capability.
Related proof: ``tests/test_capability_matrix.py`` and capability schema.
"""

from __future__ import annotations

from typing import Any

from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.route_preview import RoutePreviewService


class CapabilityMatrixError(ValueError):
    """Purpose: Reject inconsistent capability-source contracts explicitly.

    Inputs: Reviewed diagnostic naming a missing or duplicate capability mapping.
    Outputs: Typed ``ValueError`` for callers and tests.
    How it works: Uses standard exception behavior.
    Side effects: None.
    Failure behavior: No partial matrix is returned.
    Safety: Prevents unsupported lanes from appearing available.
    Example: An allowed kind without a route raises an error.
    Related proof: ``tests/test_capability_matrix.py``.
    """


class CapabilityMatrixService:
    """Purpose: Derive a concise capability matrix without duplicating policy truth.

    Inputs: Intake and route services plus coherent state snapshots.
    Outputs: One lane per upload-enabled kind with detected tools and blockers.
    How it works: Joins kind, route, preview, output, and tool-family records by ids.
    Side effects: None beyond dependency reads when policy is requested.
    Failure behavior: Incomplete or duplicate route coverage raises explicitly.
    Safety: Every lane reports executionReady false and all action flags false.
    Example: Mesh maps to the slicer family and mesh-to-toolpath preview route.
    Related proof: ``tests/test_capability_matrix.py``.
    """

    def __init__(self, *, intake_catalog: IntakeCatalogService, route_preview: RoutePreviewService) -> None:
        """Purpose: Bind the existing intake and route policy authorities.

        Inputs: Focused services already used by app-state composition.
        Outputs: Initialized matrix service; constructors return ``None``.
        How it works: Stores dependency references without reading or mutating state.
        Side effects: None.
        Failure behavior: Missing dependencies remain normal Python errors.
        Safety: No independent permissive capability configuration is introduced.
        Example: App state injects its shared catalog and preview services.
        Related proof: Composition and identity tests.
        """

        self.intake_catalog = intake_catalog
        self.route_preview = route_preview

    def matrix(
        self,
        intake: dict[str, Any],
        routes: dict[str, Any],
        outputs: dict[str, Any],
        tools: dict[str, Any],
    ) -> dict[str, Any]:
        """Purpose: Join coherent snapshots into honest user-facing input lanes.

        Inputs: Catalog, route preview, output proof, and detection snapshots.
        Outputs: ``makers-anvil.api.capability-matrix.v1`` contract.
        How it works: Builds closed route/tool indexes and counts current records.
        Side effects: Reads committed intake/route policy through shared services.
        Failure behavior: Missing/duplicate route definitions raise explicitly.
        Safety: Paths and commands are absent; execution remains false in every lane.
        Example: A copied PNG makes the image lane preview-ready, not executable.
        Related proof: Matrix join, zero-state, and privacy tests.
        """

        policy = self.intake_catalog.policy()
        route_policy = self.route_preview.route_catalog()
        route_by_kind: dict[str, dict[str, Any]] = {}
        for route in route_policy["routes"]:
            for kind in route["acceptedKinds"]:
                if kind in route_by_kind:
                    raise CapabilityMatrixError("capability kind maps to multiple routes")
                route_by_kind[kind] = route
        extensions_by_kind = {group["id"]: group["extensions"] for group in policy["fileKinds"]}
        previews_by_kind: dict[str, int] = {}
        for preview in routes["previews"]:
            kind = preview["source"]["kind"]
            previews_by_kind[kind] = previews_by_kind.get(kind, 0) + 1
        outputs_by_kind: dict[str, int] = {}
        preview_kind_by_id = {preview["id"]: preview["source"]["kind"] for preview in routes["previews"]}
        for bundle in outputs["bundles"]:
            kind = preview_kind_by_id.get(bundle.get("routePreviewId"))
            if kind:
                outputs_by_kind[kind] = outputs_by_kind.get(kind, 0) + 1
        lanes = []
        for kind in policy["uploadAllowedKinds"]:
            route = route_by_kind.get(kind)
            if route is None:
                raise CapabilityMatrixError(f"capability kind {kind!r} has no route")
            matching_tools = [
                {"id": tool["id"], "label": tool["label"], "claimState": tool["claimState"]}
                for tool in tools["tools"] if route["toolFamily"] in tool["families"]
            ]
            record_count = sum(record["source"]["kind"] == kind for record in intake["records"])
            preview_count = previews_by_kind.get(kind, 0)
            detected_count = sum(tool["claimState"] == "detected" for tool in matching_tools)
            lanes.append({
                "id": kind,
                "label": kind.title(),
                "claimState": "preview-only" if preview_count else "staged",
                "status": "preview-ready" if preview_count else "available",
                "currentCount": record_count,
                "inputExamples": extensions_by_kind[kind],
                "route": {"id": route["id"], "label": route["label"], "toolFamily": route["toolFamily"]},
                "toolSummary": {"candidateCount": len(matching_tools), "detectedCount": detected_count},
                "tools": matching_tools,
                "plannedOutputCount": outputs_by_kind.get(kind, 0),
                "whatWorks": "Metadata can be copied into app-owned storage and mapped to a read-only plan.",
                "nextStep": "Prove contained execution, cancellation, audit, and output evidence before enabling this lane.",
                "executionReady": False,
            })
        return {
            "schemaVersion": "makers-anvil.api.capability-matrix.v1",
            "claimState": "preview-only" if any(lane["status"] == "preview-ready" for lane in lanes) else "staged",
            "summary": {
                "laneCount": len(lanes),
                "supportedInputCount": sum(len(lane["inputExamples"]) for lane in lanes),
                "previewReadyLaneCount": sum(lane["status"] == "preview-ready" for lane in lanes),
                "detectedToolCount": tools["summary"]["detectedCount"],
                "plannedOutputCount": outputs["summary"]["bundleCount"],
            },
            "ingressMethods": [
                {"id": "file-picker", "label": "Choose one file", "claimState": "staged", "enabled": True},
                {"id": "drag-drop", "label": "Drag and drop", "claimState": "blocked", "enabled": False},
                {"id": "clipboard", "label": "Clipboard paste", "claimState": "blocked", "enabled": False},
                {"id": "folder", "label": "Folder import", "claimState": "blocked", "enabled": False},
            ],
            "lanes": lanes,
            "honesty": ["Preview-ready is not execution-ready.", "Detected tools are not launched.", "Planned outputs are not completed artifacts."],
            "safety": {"sourcePathExposed": False, "selectedFileHandoffEnabled": False, "routeExecutionEnabled": False, "toolLaunchEnabled": False, "outputOpenEnabled": False},
        }


__all__ = ["CapabilityMatrixError", "CapabilityMatrixService"]
