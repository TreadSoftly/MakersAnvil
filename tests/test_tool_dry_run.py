"""Behavior examples for path-free, non-runnable tool dry-run planning."""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.output_proof import OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.tool_detection import ToolDetectionService
from makers_anvil_backend.services.tool_dry_run import ToolDryRunError, ToolDryRunService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_services(root: Path, data_root: Path, detected_command: str | None = None) -> tuple[IntakeCatalogService, ToolDryRunService]:
    """Build an isolated planning graph with optional injected PATH detection."""

    config_root = root / "config"
    config_root.mkdir(parents=True)
    for name in (
        "default_settings.json",
        "intake_policy.json",
        "route_catalog.json",
        "output_policy.json",
        "tool_catalog.json",
        "tool_dry_run_policy.json",
    ):
        config_root.joinpath(name).write_text(PROJECT_ROOT.joinpath("config", name).read_text(encoding="utf-8"), encoding="utf-8")
    paths = RuntimePathsService(root, {DATA_DIR_ENV: str(data_root)}, root.parent / "home", "windows")
    workspace = WorkspaceConfigService(root, paths)
    intake = IntakeCatalogService(root, workspace)
    routes = RoutePreviewService(root, intake)
    outputs = OutputProofService(root, routes, workspace)

    def path_lookup(command: str, path: str | None) -> str | None:
        """Return one private fake result without running the named command."""

        return str(root.parent / "private-bin" / command) if command == detected_command else None

    tools = ToolDetectionService(root, "windows", {"PATH": "injected"}, path_lookup=path_lookup)
    return intake, ToolDryRunService(root, routes, outputs, tools)


def test_mesh_plan_selects_cura_without_building_or_running_a_command(tmp_path: Path) -> None:
    """A detected preferred slicer yields semantic references but no runnable command."""

    intake, planner = build_services(tmp_path / "source", tmp_path / "runtime", "UltiMaker-Cura.exe")
    source = tmp_path / "fixture.stl"
    source.write_bytes(b"mesh remains user-owned")
    record = intake.stage_file_metadata(source)
    original = source.read_bytes()

    result = planner.plan_catalog()

    assert result["claimState"] == "preview-only"
    assert result["summary"] == {
        "routePreviewCount": 1,
        "planCount": 1,
        "selectedToolCount": 1,
        "blockedPlanCount": 1,
        "unmatchedPlanCount": 0,
    }
    plan = result["plans"][0]
    assert plan["toolSelection"]["selectedTool"]["id"] == "ultimaker-cura"
    assert plan["invocation"]["commandString"] is None
    assert plan["invocation"]["resolvedExecutablePath"] is None
    assert plan["invocation"]["processExecuted"] is False
    assert plan["source"]["logicalReference"] == f"makers-anvil-intake://records/{record['id']}"
    assert all(argument["pathResolved"] is False and argument["handoffEnabled"] is False for argument in plan["invocation"]["arguments"])
    assert all(value is False for value in result["safety"].values())
    assert plan["readiness"]["executionReady"] is False
    assert source.read_bytes() == original
    assert str(source.resolve()) not in json.dumps(result)


def test_missing_detected_tool_keeps_selection_and_execution_not_proven(tmp_path: Path) -> None:
    """A route remains planned and blocked when no preferred tool is detected."""

    intake, planner = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "fixture.fcstd"
    source.write_bytes(b"cad metadata")
    intake.stage_file_metadata(source)

    plan = planner.plan_catalog()["plans"][0]

    assert plan["route"]["id"] == "cad-to-mesh"
    assert plan["toolSelection"]["selectedTool"] is None
    assert plan["toolSelection"]["claimState"] == "not proven"
    assert "no detected preferred tool for required family" in plan["readiness"]["blockers"]
    assert plan["invocation"]["executableName"] is None


def test_unconfigured_tool_family_is_reported_without_guessing(tmp_path: Path) -> None:
    """Document planning names the missing catalog coverage instead of inventing a viewer."""

    intake, planner = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "reference.pdf"
    source.write_bytes(b"document metadata")
    intake.stage_file_metadata(source)

    plan = planner.plan_catalog()["plans"][0]

    assert plan["route"]["toolFamily"] == "document-viewer"
    assert plan["toolSelection"]["preferredToolIds"] == []
    assert "no configured tool candidate for required family" in plan["readiness"]["blockers"]


def test_policy_rejects_enabled_or_missing_safety_flags(tmp_path: Path) -> None:
    """Dry-run policy cannot silently gain command, handoff, execution, or write behavior."""

    _, planner = build_services(tmp_path / "source", tmp_path / "runtime")
    policy = json.loads(planner.policy_path.read_text(encoding="utf-8"))
    policy["safety"]["commandConstructed"] = True
    planner.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ToolDryRunError, match="cannot construct"):
        planner.plan_catalog()

    policy["safety"]["commandConstructed"] = False
    policy["safety"].pop("sourcePathResolved")
    planner.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(ToolDryRunError, match="cannot construct"):
        planner.plan_catalog()


def test_policy_rejects_tool_outside_required_family(tmp_path: Path) -> None:
    """A preferred tool must advertise the family required by its route."""

    _, planner = build_services(tmp_path / "source", tmp_path / "runtime")
    policy = json.loads(planner.policy_path.read_text(encoding="utf-8"))
    policy["routes"][0]["preferredToolIds"] = ["gimp"]
    planner.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ToolDryRunError, match="required family"):
        planner.plan_catalog()
