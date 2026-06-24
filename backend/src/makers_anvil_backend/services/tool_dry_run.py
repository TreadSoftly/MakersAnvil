"""Plan semantic tool invocations without resolving paths or constructing commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from makers_anvil_backend.services.output_proof import OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.tool_detection import ToolDetectionService


ROOT = Path(__file__).resolve().parents[4]
DRY_RUN_SAFETY_FLAGS = {
    "commandConstructed",
    "processExecuted",
    "sourcePathResolved",
    "outputPathResolved",
    "selectedFileHandedOff",
    "toolLaunched",
    "filesystemWritten",
}


class ToolDryRunError(ValueError):
    """Raised when dry-run policy could create a runnable or incoherent plan."""


class ToolDryRunService:
    """Join route, output, and tool evidence into non-runnable invocation plans."""

    def __init__(
        self,
        root: Path | None = None,
        route_preview: RoutePreviewService | None = None,
        output_proof: OutputProofService | None = None,
        tool_detection: ToolDetectionService | None = None,
    ) -> None:
        """Bind coherent route, output, and tool services to semantic planning policy."""

        self.route_preview = route_preview or RoutePreviewService(root or ROOT)
        self.root = root or self.route_preview.root
        self.output_proof = output_proof or OutputProofService(self.root, self.route_preview)
        self.tool_detection = tool_detection or ToolDetectionService(self.root)
        self.policy_path = self.root / "config" / "tool_dry_run_policy.json"

    def dry_run_policy(self) -> dict[str, Any]:
        """Validate route coverage, tool-family compatibility, and false safety state."""

        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(policy, dict):
            raise ToolDryRunError("tool dry-run policy must be a structured record")
        if policy.get("schemaVersion") != "makers-anvil.config.tool-dry-run-policy.v1":
            raise ToolDryRunError("tool dry-run policy schema version is not supported")
        if policy.get("mode") != "semantic-invocation-read-only":
            raise ToolDryRunError("tool dry-run policy must remain semantic and read-only")
        safety = policy.get("safety")
        if not isinstance(safety, dict) or set(safety) != DRY_RUN_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise ToolDryRunError("tool dry-run policy cannot construct commands, resolve paths, hand off files, execute, or write")
        route_plans = policy.get("routes")
        required_blockers = policy.get("requiredBlockers")
        if not isinstance(route_plans, list) or not route_plans or not all(isinstance(item, dict) for item in route_plans):
            raise ToolDryRunError("tool dry-run policy requires route plans")
        if (
            not isinstance(required_blockers, list)
            or not required_blockers
            or len(set(required_blockers)) != len(required_blockers)
            or not all(isinstance(item, str) and item for item in required_blockers)
        ):
            raise ToolDryRunError("tool dry-run policy requires unique readiness blockers")
        self._validate_route_plans(route_plans)
        return policy

    def plan_catalog(
        self,
        route_snapshot: dict[str, Any] | None = None,
        output_snapshot: dict[str, Any] | None = None,
        tool_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return coherent semantic plans from one set of read-only snapshots."""

        routes = route_snapshot if route_snapshot is not None else self.route_preview.preview_catalog()
        outputs = output_snapshot if output_snapshot is not None else self.output_proof.preview_catalog(routes)
        tools = tool_snapshot if tool_snapshot is not None else self.tool_detection.detection_catalog()
        policy = self.dry_run_policy()
        plans_by_route = {item["routeId"]: item for item in policy["routes"]}
        bundles_by_preview = {item["routePreviewId"]: item for item in outputs["bundles"]}
        detected_tools = {
            item["id"]: item
            for item in tools["tools"]
            if item["detection"]["installed"]
        }
        plans: list[dict[str, Any]] = []
        unmatched_count = 0
        for route in routes["previews"]:
            plan_policy = plans_by_route.get(route["route"]["id"])
            output_bundle = bundles_by_preview.get(route["id"])
            if plan_policy is None or output_bundle is None:
                unmatched_count += 1
                continue
            selected_tool = next(
                (detected_tools[tool_id] for tool_id in plan_policy["preferredToolIds"] if tool_id in detected_tools),
                None,
            )
            plans.append(self._build_plan(route, output_bundle, plan_policy, selected_tool, policy["requiredBlockers"]))

        selected_count = sum(plan["toolSelection"]["selectedTool"] is not None for plan in plans)
        upstream_failed = any(snapshot.get("claimState") == "failed" for snapshot in (routes, outputs, tools))
        return {
            "schemaVersion": "makers-anvil.api.tool-dry-run.v1",
            "claimState": "failed" if upstream_failed or unmatched_count else "preview-only",
            "mode": policy["mode"],
            "summary": {
                "routePreviewCount": len(routes["previews"]),
                "planCount": len(plans),
                "selectedToolCount": selected_count,
                "blockedPlanCount": len(plans),
                "unmatchedPlanCount": unmatched_count,
            },
            "plans": plans,
            "safety": policy["safety"],
            "executionAction": {"claimState": "blocked", "enabledInApi": False},
        }

    def _validate_route_plans(self, route_plans: list[dict[str, Any]]) -> None:
        """Require exact route coverage and family-compatible preferred tool ids."""

        routes = {item["id"]: item for item in self.route_preview.route_catalog()["routes"]}
        tools = {item["id"]: item for item in self.tool_detection.tool_catalog()["tools"]}
        configured_route_ids: set[str] = set()
        for plan in route_plans:
            if not all(isinstance(plan.get(field), str) and plan[field] for field in ("routeId", "operationId", "operationLabel")):
                raise ToolDryRunError("route plans require route and operation identity")
            preferred = plan.get("preferredToolIds")
            if not isinstance(preferred, list) or len(set(preferred)) != len(preferred) or not all(isinstance(item, str) and item for item in preferred):
                raise ToolDryRunError("preferred tool ids must be unique strings")
            route = routes.get(plan["routeId"])
            if route is None or plan["routeId"] in configured_route_ids:
                raise ToolDryRunError("tool dry-run routes must be known and unique")
            for tool_id in preferred:
                tool = tools.get(tool_id)
                if tool is None or route["toolFamily"] not in tool["families"]:
                    raise ToolDryRunError("preferred tools must support the route's required family")
            configured_route_ids.add(plan["routeId"])
        if configured_route_ids != set(routes):
            raise ToolDryRunError("tool dry-run policy must cover every configured route exactly once")

    @staticmethod
    def _build_plan(
        route: dict[str, Any],
        output_bundle: dict[str, Any],
        plan_policy: dict[str, Any],
        selected_tool: dict[str, Any] | None,
        required_blockers: list[str],
    ) -> dict[str, Any]:
        """Build one path-free semantic invocation while preserving every action gate."""

        source = route["source"]
        logical_source = f"makers-anvil-intake://records/{source['intakeId']}"
        tool_record = None
        if selected_tool is not None:
            tool_record = {
                "id": selected_tool["id"],
                "label": selected_tool["label"],
                "executableName": selected_tool["detection"]["executableName"],
                "detectionMethod": selected_tool["detection"]["method"],
                "claimState": "detected",
                "absolutePathExposed": False,
            }
        blockers = [item for item in route["readiness"]["blockers"] if item != "tool detection not proven" or tool_record is None]
        blockers.extend(required_blockers)
        if tool_record is None:
            blockers.append(
                "no detected preferred tool for required family"
                if plan_policy["preferredToolIds"]
                else "no configured tool candidate for required family"
            )
        blockers = list(dict.fromkeys(blockers))
        return {
            "id": f"dry-run-{route['id']}",
            "claimState": "preview-only",
            "source": {
                "intakeId": source["intakeId"],
                "displayName": source["displayName"],
                "kind": source["kind"],
                "logicalReference": logical_source,
            },
            "route": {
                "previewId": route["id"],
                "id": route["route"]["id"],
                "label": route["route"]["label"],
                "toolFamily": route["route"]["toolFamily"],
            },
            "output": {
                "bundleId": output_bundle["id"],
                "logicalDirectory": output_bundle["output"]["logicalDirectory"],
            },
            "toolSelection": {
                "requiredFamily": route["route"]["toolFamily"],
                "preferredToolIds": list(plan_policy["preferredToolIds"]),
                "selectedTool": tool_record,
                "claimState": "detected" if tool_record else "not proven",
            },
            "invocation": {
                "claimState": "planned",
                "mode": "semantic-only",
                "operation": {"id": plan_policy["operationId"], "label": plan_policy["operationLabel"]},
                "executableName": tool_record["executableName"] if tool_record else None,
                "resolvedExecutablePath": None,
                "arguments": [
                    {"id": "source", "role": "source", "logicalValue": logical_source, "pathResolved": False, "handoffEnabled": False},
                    {"id": "destination", "role": "destination", "logicalValue": output_bundle["output"]["logicalDirectory"], "pathResolved": False, "handoffEnabled": False},
                ],
                "commandString": None,
                "processExecuted": False,
            },
            "readiness": {
                "planAvailable": True,
                "toolCandidateAvailable": tool_record is not None,
                "handoffReady": False,
                "executionReady": False,
                "blockers": blockers,
            },
        }
