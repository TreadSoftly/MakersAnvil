"""Purpose: Prove lifecycle previews are complete, bounded, portable, and non-mutating.

Used by: Developers and CI whenever backup, restore, update, uninstall, or repair planning changes.
Inputs: Committed policy copied into isolated source roots and pytest-owned app data.
Outputs: Assertions over inventory, plans, blockers, safety, privacy, limits, and writes.
Side effects: Creates only temporary fixture files needed to test metadata inventory.
Safety: No archive, network, installer, software mutation, user deletion, or process occurs.
Failure behavior: Any widened effect, path/name leak, missing operation, or stale policy fails.
Related proof: ``services/lifecycle_dry_run.py`` and lifecycle JSON schemas.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from makers_anvil_backend.services.lifecycle_dry_run import LifecycleDryRunError, LifecycleDryRunService, OPERATION_IDS
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[1]


def build_service(tmp_path: Path) -> tuple[LifecycleDryRunService, Path, Path]:
    """Purpose: Construct lifecycle planning over separate temporary source and data roots.

    Inputs: Pytest-owned temporary directory.
    Outputs: Service, private runtime root, and copied policy path for focused mutation tests.
    How it works: Copies only required config and injects an absolute runtime override.
    Side effects: Creates temporary config and user-data directories.
    Failure behavior: Fixture copy or construction errors fail the requesting test.
    Safety: Production user data and reference folders are never read or changed.
    Example: A test writes ``settings/example.json`` under the returned data root.
    Related proof: Every lifecycle service test below uses this fixture.
    """

    source_root = tmp_path / "source"
    config_root = source_root / "config"
    config_root.mkdir(parents=True)
    shutil.copy2(ROOT / "config" / "default_settings.json", config_root / "default_settings.json")
    policy_path = config_root / "lifecycle_dry_run_policy.json"
    shutil.copy2(ROOT / "config" / "lifecycle_dry_run_policy.json", policy_path)
    for relative in ("frontend/public/index.html", "state/current_status.json", "schemas/app-state.schema.json"):
        target = source_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture\n", encoding="utf-8")
    data_root = (tmp_path / "user-data").resolve()
    runtime = RuntimePathsService(source_root=source_root, environ={DATA_DIR_ENV: str(data_root)})
    workspace = WorkspaceConfigService(root=source_root, runtime_paths=runtime)
    return LifecycleDryRunService(root=source_root, workspace_config=workspace), data_root, policy_path


def tree_snapshot(root: Path) -> list[tuple[str, int]]:
    """Purpose: Capture relative regular-file names and sizes for no-write comparison.

    Inputs: Pytest-owned runtime root that may or may not exist.
    Outputs: Sorted relative-path and size pairs.
    How it works: Recursively enumerates existing regular non-symlink files.
    Side effects: Reads directory and size metadata only.
    Failure behavior: Filesystem errors fail the test rather than hiding a write.
    Safety: The helper runs only on isolated temporary data.
    Example: Before and after snapshots must be exactly equal around ``catalog``.
    Related proof: The no-write lifecycle test below.
    """

    if not root.exists():
        return []
    return sorted((path.relative_to(root).as_posix(), path.stat().st_size) for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def test_empty_catalog_contains_all_five_non_executable_plans(tmp_path: Path) -> None:
    """Purpose: Prove complete lifecycle coverage exists before any runtime data exists.

    Inputs: Isolated service with no app-owned directories.
    Outputs: Five ordered previews, zero execution readiness, and all-false effects.
    How it works: Reads policy and catalog then checks every operation/action boundary.
    Side effects: Reads copied config only and creates no runtime root.
    Failure behavior: Missing plans, enabled actions, or unexpected paths fail assertions.
    Safety: Empty-state planning cannot create a backup or alter software.
    Example: Operation ids equal backup, restore, update, uninstall, and repair.
    Related proof: Lifecycle policy and catalog schemas.
    """

    service, data_root, _ = build_service(tmp_path)
    catalog = service.catalog()

    assert [plan["operation"]["id"] for plan in catalog["plans"]] == list(OPERATION_IDS)
    assert catalog["summary"] == {"operationCount": 5, "previewReadyCount": 5, "executionReadyCount": 0, "sourceFileCount": 0, "sourceBytes": 0}
    assert catalog["inventory"]["claimState"] == "proven"
    assert catalog["inventory"]["summary"]["existingDirectoryCount"] == 0
    assert all(plan["readiness"]["executionReady"] is False for plan in catalog["plans"])
    assert all(not any(plan["effects"].values()) for plan in catalog["plans"])
    assert all(plan["executionAction"] == {"claimState": "blocked", "enabledInApi": False} for plan in catalog["plans"])
    assert all(plan["preservation"] == {"existingDataPreserved": True, "userDataDeletionAllowed": False} for plan in catalog["plans"])
    assert not data_root.exists()


def test_inventory_counts_metadata_without_returning_names_paths_or_content(tmp_path: Path) -> None:
    """Purpose: Prove backup source inventory exposes only safe aggregate metadata.

    Inputs: Three files under two declared app-owned source directories.
    Outputs: Exact counts/bytes plus logical-only directory records.
    How it works: Writes known bytes, calls catalog, and scans serialized public output.
    Side effects: Creates pytest-owned fixture files only.
    Failure behavior: Wrong totals or leaked private/name text fail assertions.
    Safety: The service reads no file content and does not include backup/tmp sources.
    Example: Settings and intake totals sum to six bytes across three files.
    Related proof: Inventory and path-redaction schemas.
    """

    service, data_root, _ = build_service(tmp_path)
    (data_root / "settings").mkdir(parents=True)
    (data_root / "intake" / "records").mkdir(parents=True)
    (data_root / "backups").mkdir(parents=True)
    (data_root / "tmp").mkdir(parents=True)
    (data_root / "settings" / "private-name.json").write_bytes(b"a")
    (data_root / "intake" / "records" / "secret-record.json").write_bytes(b"bc")
    (data_root / "intake" / "payload.stl").write_bytes(b"def")
    (data_root / "backups" / "ignored.zip").write_bytes(b"ignored")
    (data_root / "tmp" / "ignored.tmp").write_bytes(b"ignored")

    catalog = service.catalog()
    public_text = json.dumps(catalog)

    assert catalog["summary"]["sourceFileCount"] == 3
    assert catalog["summary"]["sourceBytes"] == 6
    assert catalog["inventory"]["contentRead"] is False
    assert catalog["inventory"]["namesExposed"] is False
    assert str(data_root) not in public_text
    assert "private-name" not in public_text
    assert "secret-record" not in public_text
    assert "payload.stl" not in public_text
    assert "ignored.zip" not in public_text


def test_catalog_does_not_write_or_change_fixture_tree(tmp_path: Path) -> None:
    """Purpose: Prove lifecycle preview generation is observational only.

    Inputs: One existing settings file and complete copied policy.
    Outputs: Identical before/after file snapshots and absent backup outputs.
    How it works: Captures metadata, calls policy/catalog repeatedly, then compares.
    Side effects: Test setup writes one fixture before the measured operation.
    Failure behavior: Any service-created/replaced/deleted file fails comparison.
    Safety: No backup, manifest, report, archive, or lifecycle record may be written.
    Example: Calling catalog twice remains deterministic and leaves no backup folder.
    Related proof: Dry-run no-side-effect contract and verifier.
    """

    service, data_root, _ = build_service(tmp_path)
    (data_root / "settings").mkdir(parents=True)
    (data_root / "settings" / "preferences.json").write_text("{}\n", encoding="utf-8")
    before = tree_snapshot(data_root)

    first = service.catalog()
    second = service.catalog()

    assert first == second
    assert tree_snapshot(data_root) == before
    assert not (data_root / "backups").exists()


def test_policy_weakening_or_operation_loss_fails_closed(tmp_path: Path) -> None:
    """Purpose: Prove lifecycle effects and operation coverage cannot silently widen.

    Inputs: Copied policy with one true software effect or missing repair plan.
    Outputs: ``LifecycleDryRunError`` for each mutation.
    How it works: Rewrites isolated JSON between focused validation calls.
    Side effects: Changes only the pytest-owned copied policy.
    Failure behavior: Acceptance of either weakened policy fails the test.
    Safety: No runtime inventory starts after invalid policy is detected.
    Example: ``installerExecutionEnabled=true`` is rejected immediately.
    Related proof: Strict service validator and policy schema.
    """

    service, _, policy_path = build_service(tmp_path)
    original = json.loads(policy_path.read_text(encoding="utf-8"))
    weakened = json.loads(json.dumps(original))
    weakened["safety"]["installerExecutionEnabled"] = True
    policy_path.write_text(json.dumps(weakened), encoding="utf-8")
    with pytest.raises(LifecycleDryRunError, match="safety"):
        service.policy()

    missing = json.loads(json.dumps(original))
    missing["operations"] = missing["operations"][:-1]
    policy_path.write_text(json.dumps(missing), encoding="utf-8")
    with pytest.raises(LifecycleDryRunError, match="coverage"):
        service.policy()


def test_global_entry_limit_marks_inventory_failed_without_overrun(tmp_path: Path) -> None:
    """Purpose: Prove metadata inventory stops at its committed global resource bound.

    Inputs: Three settings files and isolated policy reduced to two entries.
    Outputs: Failed inventory truth, scan-limit marker, and at most two counted files.
    How it works: Changes only the test policy cap then performs one catalog read.
    Side effects: Creates three pytest-owned files and rewrites copied config.
    Failure behavior: Scanning past the cap or reporting proven fails assertions.
    Safety: Resource exhaustion cannot turn into unbounded directory traversal.
    Example: ``maxEntries=2`` reaches the cap before all three files are counted.
    Related proof: Bounded inventory implementation and policy limits.
    """

    service, data_root, policy_path = build_service(tmp_path)
    settings = data_root / "settings"
    settings.mkdir(parents=True)
    for index in range(3):
        (settings / f"item-{index}.json").write_text("{}", encoding="utf-8")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["inventory"]["maxEntries"] = 2
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    catalog = service.catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["inventory"]["claimState"] == "failed"
    assert catalog["inventory"]["summary"]["scanLimitReached"] is True
    assert catalog["inventory"]["summary"]["fileCount"] <= 2
