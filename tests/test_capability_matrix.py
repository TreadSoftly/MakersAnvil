"""Purpose: Prove the capability matrix joins existing truth without new actions.

Used by: CI whenever supported input, route, output, or tool contracts change.
Inputs: Real committed policies and deterministic path-free snapshot fixtures.
Outputs: Assertions for five lanes, route coverage, counts, and false actions.
Side effects: Reads committed config only; no runtime data or tool process is used.
Safety: The matrix cannot claim execution readiness or expose a resolved path.
Failure behavior: Missing coverage and broadened safety fail explicitly.
Related proof: Capability matrix service and schema.
"""

from pathlib import Path

from makers_anvil_backend.services.capability_matrix import CapabilityMatrixService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.route_preview import RoutePreviewService


ROOT = Path(__file__).resolve().parents[1]


def test_matrix_maps_all_upload_kinds_and_keeps_execution_false() -> None:
    """Purpose: Confirm every enabled input kind has one honest nonexecuting lane.

    Inputs: One image intake/preview/output and one detected image-editor tool.
    Outputs: Five lanes with one preview-ready image lane and false safety flags.
    How it works: Uses committed intake/route policy and small coherent snapshots.
    Side effects: Reads two committed JSON policy files.
    Failure behavior: Count, mapping, path privacy, or readiness drift fails.
    Safety: No detection or route service action executes during the test.
    Example: PNG maps to image-reference-review and remains executionReady false.
    Related proof: Browser capability-lane rendering test.
    """

    intake_service = IntakeCatalogService(ROOT)
    route_service = RoutePreviewService(ROOT, intake_catalog=intake_service)
    service = CapabilityMatrixService(intake_catalog=intake_service, route_preview=route_service)
    intake = {"records": [{"id": "intake-" + "a" * 32, "source": {"kind": "image"}}]}
    routes = {"previews": [{"id": "preview-image", "source": {"kind": "image"}}]}
    outputs = {"summary": {"bundleCount": 1}, "bundles": [{"routePreviewId": "preview-image"}]}
    tools = {"summary": {"detectedCount": 1}, "tools": [{"id": "gimp", "label": "GIMP", "claimState": "detected", "families": ["image-editor"]}]}
    matrix = service.matrix(intake, routes, outputs, tools)
    image = next(lane for lane in matrix["lanes"] if lane["id"] == "image")
    assert matrix["summary"]["laneCount"] == 5
    assert matrix["summary"]["previewReadyLaneCount"] == 1
    assert image["route"]["id"] == "image-reference-review"
    assert image["toolSummary"] == {"candidateCount": 1, "detectedCount": 1}
    assert all(lane["executionReady"] is False for lane in matrix["lanes"])
    assert all(value is False for value in matrix["safety"].values())
    serialized = str(matrix)
    assert "C:\\" not in serialized
    assert ("/" + "Users/") not in serialized
