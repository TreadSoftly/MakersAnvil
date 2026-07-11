"""Purpose: Explain and prove deterministic metadata-only route planning.

Used by: Developers and CI when intake kinds or work-route policy changes.
Inputs: Isolated route catalogs and valid/invalid intake snapshots.
Outputs: Assertions over matching, steps, blockers, and unmatched records.
Side effects: Temporary policy files only.
Safety: Source access, extraction, tool launch, execution, and output stay false.
Failure behavior: Unsupported input remains unmatched; weakened policy is rejected.
Related proof: ``services/route_preview.py`` and route schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.route_preview import RoutePreviewError, RoutePreviewService
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_services(root: Path, data_root: Path) -> tuple[IntakeCatalogService, RoutePreviewService]:
    """Purpose: Build isolated intake and preview services from committed safe configuration.

    Inputs: Caller-supplied ``root``, ``data_root`` values from the signature.
    Outputs: Returns ``tuple[IntakeCatalogService, RoutePreviewService]``, or raises before returning when validation fails.
    How it works: It iterates over bounded records, then returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Call ``result = instance.build_services(...)`` with values satisfying the documented inputs.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    config_root = root / "config"
    config_root.mkdir(parents=True)
    for name in ("default_settings.json", "intake_policy.json", "route_catalog.json"):
        config_root.joinpath(name).write_text(
            PROJECT_ROOT.joinpath("config", name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    paths = RuntimePathsService(
        source_root=root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=root.parent / "home",
        platform_name="linux",
    )
    workspace = WorkspaceConfigService(root, paths)
    intake = IntakeCatalogService(root, workspace)
    return intake, RoutePreviewService(root, intake)


def test_mesh_preview_uses_metadata_after_source_is_gone(tmp_path: Path) -> None:
    """Purpose: A route preview remains available without reopening or retaining the source file.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Run ``python -m pytest tests/test_route_preview.py -k test_mesh_preview_uses_metadata_after_source_is_gone``.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    intake, routes = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "fixture.stl"
    source.write_bytes(b"solid fixture\nendsolid fixture\n")
    record = intake.stage_file_metadata(source)
    source.unlink()

    result = routes.preview_catalog()

    assert result["claimState"] == "preview-only"
    assert result["summary"] == {
        "sourceRecordCount": 1,
        "previewCount": 1,
        "unmatchedCount": 0,
        "invalidRecordCount": 0,
    }
    preview = result["previews"][0]
    assert preview["source"]["intakeId"] == record["id"]
    assert preview["route"]["id"] == "mesh-to-toolpath"
    assert preview["readiness"]["executionReady"] is False
    assert all(step["actionEnabled"] is False for step in preview["steps"])
    assert all(value is False for value in result["safety"].values())
    assert str(source.resolve()) not in json.dumps(result)


def test_archive_preview_does_not_extract_or_change_source(tmp_path: Path) -> None:
    """Purpose: Archive planning describes a future gate while extraction remains disabled.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Run ``python -m pytest tests/test_route_preview.py -k test_archive_preview_does_not_extract_or_change_source``.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    intake, routes = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "bundle.zip"
    original = b"archive bytes stay untouched"
    source.write_bytes(original)
    intake.stage_file_metadata(source)

    result = routes.preview_catalog()

    preview = result["previews"][0]
    extraction_step = next(step for step in preview["steps"] if step["id"] == "extract-archive")
    assert preview["route"]["id"] == "archive-metadata-review"
    assert extraction_step["claimState"] == "planned"
    assert extraction_step["actionEnabled"] is False
    assert result["safety"]["archiveExtractionEnabled"] is False
    assert source.read_bytes() == original


def test_unknown_kind_is_counted_without_inventing_a_route(tmp_path: Path) -> None:
    """Purpose: Unrecognized metadata is reported as unmatched instead of guessed into a workflow.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Run ``python -m pytest tests/test_route_preview.py -k test_unknown_kind_is_counted_without_inventing_a_route``.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    intake, routes = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "mystery.bin"
    source.write_bytes(b"unknown")
    intake.stage_file_metadata(source)

    result = routes.preview_catalog()

    assert result["previews"] == []
    assert result["summary"]["unmatchedCount"] == 1
    assert result["summary"]["sourceRecordCount"] == 1


def test_route_catalog_rejects_enabled_actions(tmp_path: Path) -> None:
    """Purpose: A changed catalog cannot silently enable execution or tool behavior.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Run ``python -m pytest tests/test_route_preview.py -k test_route_catalog_rejects_enabled_actions``.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    _, routes = build_services(tmp_path / "source", tmp_path / "runtime")
    catalog = json.loads(routes.catalog_path.read_text(encoding="utf-8"))
    catalog["safety"]["toolLaunchEnabled"] = True
    routes.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(RoutePreviewError, match="cannot enable"):
        routes.preview_catalog()


def test_route_catalog_rejects_missing_safety_flags(tmp_path: Path) -> None:
    """Purpose: Removing a required false flag cannot bypass route-catalog safety checks.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source access, extraction, tool launch, execution, and output stay false.
    Example: Run ``python -m pytest tests/test_route_preview.py -k test_route_catalog_rejects_missing_safety_flags``.
    Related proof: ``services/route_preview.py`` and route schemas.
    """

    _, routes = build_services(tmp_path / "source", tmp_path / "runtime")
    catalog = json.loads(routes.catalog_path.read_text(encoding="utf-8"))
    catalog["safety"].pop("sourceContentRead")
    routes.catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    with pytest.raises(RoutePreviewError, match="cannot enable"):
        routes.preview_catalog()
