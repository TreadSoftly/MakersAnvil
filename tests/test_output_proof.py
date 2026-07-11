"""Purpose: Explain and prove non-writing artifact and proof planning.

Used by: Developers and CI when route outputs or proof requirements change.
Inputs: Isolated output policy and route-preview snapshots.
Outputs: Assertions over logical bundles, nonexistent artifacts, and proof state.
Side effects: Temporary policy files only; output directories are never created.
Safety: Expected output must never be confused with produced or verified output.
Failure behavior: Missing coverage or enabled effects fail their named examples.
Related proof: ``services/output_proof.py`` and output schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.output_proof import OutputProofError, OutputProofService
from makers_anvil_backend.services.route_preview import RoutePreviewService
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_services(
    root: Path,
    data_root: Path,
) -> tuple[IntakeCatalogService, RoutePreviewService, OutputProofService]:
    """Purpose: Build isolated intake, route, and output services from committed policies.

    Inputs: Caller-supplied ``root``, ``data_root`` values from the signature.
    Outputs: Returns ``tuple[IntakeCatalogService, RoutePreviewService, OutputProofService]``, or raises before returning when validation fails.
    How it works: It iterates over bounded records, then returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Call ``result = instance.build_services(...)`` with values satisfying the documented inputs.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    config_root = root / "config"
    config_root.mkdir(parents=True)
    for name in ("default_settings.json", "intake_policy.json", "route_catalog.json", "output_policy.json"):
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
    routes = RoutePreviewService(root, intake)
    return intake, routes, OutputProofService(root, routes, workspace)


def test_mesh_bundle_plans_artifacts_without_writing_outputs(tmp_path: Path) -> None:
    """Purpose: A mesh route gets a logical bundle and incomplete proof without output files.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Run ``python -m pytest tests/test_output_proof.py -k test_mesh_bundle_plans_artifacts_without_writing_outputs``.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    data_root = tmp_path / "runtime"
    intake, routes, outputs = build_services(tmp_path / "source", data_root)
    source = tmp_path / "fixture.stl"
    source.write_bytes(b"solid fixture\nendsolid fixture\n")
    intake.stage_file_metadata(source)
    source.unlink()

    result = outputs.preview_catalog(routes.preview_catalog())

    assert result["claimState"] == "preview-only"
    assert result["summary"] == {
        "routePreviewCount": 1,
        "bundleCount": 1,
        "unmatchedRouteCount": 0,
        "artifactCount": 3,
        "requiredProofCount": 5,
        "completedProofCount": 0,
    }
    bundle = result["bundles"][0]
    assert bundle["output"]["logicalDirectory"].startswith("makers-anvil-data://user/outputs/")
    assert bundle["artifacts"][0]["suggestedExtension"] == ".gcode"
    assert all(artifact["exists"] is False and artifact["openEnabled"] is False for artifact in bundle["artifacts"])
    assert all(item["complete"] is False and item["claimState"] == "not proven" for item in bundle["proof"])
    assert bundle["readiness"]["creationReady"] is False
    assert bundle["readiness"]["proofComplete"] is False
    assert all(value is False for value in result["safety"].values())
    assert not (data_root / "outputs").exists()
    assert str(data_root.resolve()) not in json.dumps(result)


def test_archive_bundle_does_not_extract_or_create_artifacts(tmp_path: Path) -> None:
    """Purpose: Archive output planning remains manifest-only and leaves source bytes unchanged.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Run ``python -m pytest tests/test_output_proof.py -k test_archive_bundle_does_not_extract_or_create_artifacts``.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    data_root = tmp_path / "runtime"
    intake, routes, outputs = build_services(tmp_path / "source", data_root)
    source = tmp_path / "bundle.zip"
    original = b"archive remains untouched"
    source.write_bytes(original)
    intake.stage_file_metadata(source)

    result = outputs.preview_catalog(routes.preview_catalog())

    bundle = result["bundles"][0]
    assert bundle["output"]["bundleType"] == "archive-review-bundle"
    assert all(artifact["suggestedExtension"] == ".json" for artifact in bundle["artifacts"])
    assert result["actions"]["create"]["enabledInApi"] is False
    assert result["actions"]["open"]["enabledInApi"] is False
    assert source.read_bytes() == original
    assert not (data_root / "outputs").exists()


def test_unmatched_route_is_failed_instead_of_inventing_a_bundle(tmp_path: Path) -> None:
    """Purpose: A route unknown to output policy is counted and never given guessed artifacts.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Run ``python -m pytest tests/test_output_proof.py -k test_unmatched_route_is_failed_instead_of_inventing_a_bundle``.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    intake, routes, outputs = build_services(tmp_path / "source", tmp_path / "runtime")
    source = tmp_path / "fixture.stl"
    source.write_bytes(b"mesh")
    intake.stage_file_metadata(source)
    route_snapshot = routes.preview_catalog()
    route_snapshot["previews"][0]["route"]["id"] = "future-unknown-route"

    result = outputs.preview_catalog(route_snapshot)

    assert result["claimState"] == "failed"
    assert result["bundles"] == []
    assert result["summary"]["unmatchedRouteCount"] == 1


def test_output_policy_rejects_enabled_or_missing_safety(tmp_path: Path) -> None:
    """Purpose: True or absent safety flags cannot be interpreted as a harmless output plan.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Run ``python -m pytest tests/test_output_proof.py -k test_output_policy_rejects_enabled_or_missing_safety``.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    _, _, outputs = build_services(tmp_path / "source", tmp_path / "runtime")
    policy = json.loads(outputs.policy_path.read_text(encoding="utf-8"))
    policy["safety"]["outputFileCreated"] = True
    outputs.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(OutputProofError, match="cannot create"):
        outputs.preview_catalog()

    policy["safety"]["outputFileCreated"] = False
    policy["safety"].pop("proofCaptured")
    outputs.policy_path.write_text(json.dumps(policy), encoding="utf-8")
    with pytest.raises(OutputProofError, match="cannot create"):
        outputs.preview_catalog()


def test_output_policy_requires_complete_route_coverage(tmp_path: Path) -> None:
    """Purpose: Every configured route must have exactly one explicit output-bundle policy.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Expected output must never be confused with produced or verified output.
    Example: Run ``python -m pytest tests/test_output_proof.py -k test_output_policy_requires_complete_route_coverage``.
    Related proof: ``services/output_proof.py`` and output schemas.
    """

    _, _, outputs = build_services(tmp_path / "source", tmp_path / "runtime")
    policy = json.loads(outputs.policy_path.read_text(encoding="utf-8"))
    policy["bundles"].pop()
    outputs.policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(OutputProofError, match="cover every configured route"):
        outputs.preview_catalog()
