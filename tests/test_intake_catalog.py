"""Purpose: Explain and prove metadata-only intake privacy and containment.

Used by: Developers and CI whenever file intake policy or records change.
Inputs: Temporary files, isolated runtime roots, and valid/invalid policies.
Outputs: Assertions over metadata records, source preservation, and rejection.
Side effects: Writes temporary app-owned records only.
Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
Failure behavior: Unsafe or malformed input must raise or become invalid evidence.
Related proof: ``services/intake_catalog.py`` and intake schemas.
"""

import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


def write_config(root: Path) -> None:
    """Purpose: Write the smallest safe settings and intake policy used by isolated tests.

    Inputs: Caller-supplied ``root`` values from the signature.
    Outputs: Returns ``None``, or raises before returning when validation fails.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Call ``result = instance.write_config(...)`` with values satisfying the documented inputs.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "default_settings.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.local-settings.v1",
                "claimState": "staged",
                "runtimeData": {
                    "mode": "platform-user-data",
                    "logicalRoot": "makers-anvil-data://user",
                    "environmentOverride": DATA_DIR_ENV,
                    "sourceRootDependency": False,
                    "absolutePathExposed": False,
                },
                "directories": [
                    {"id": "intake", "relativePath": "intake", "purpose": "metadata-only intake records"}
                ],
                "safety": {
                    "userUploadEnabled": False,
                    "routeExecutionEnabled": False,
                    "toolLaunchEnabled": False,
                    "archiveExtractionEnabled": False,
                    "folderImportEnabled": False,
                    "deleteUserDataEnabled": False,
                    "releasePackagingEnabled": False,
                },
            }
        ),
        encoding="utf-8",
    )
    (config_dir / "intake_policy.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.intake-policy.v1",
                "claimState": "staged",
                "mode": "metadata-only",
                "recordsDirectory": "intake/records",
                "fileKinds": [
                    {"id": "mesh", "extensions": [".stl"]},
                    {"id": "archive", "extensions": [".zip"]},
                ],
                "safety": {
                    "apiMutationEnabled": False,
                    "browserUploadEnabled": False,
                    "sourcePathStored": False,
                    "sourceContentStored": False,
                    "sourceFileCopied": False,
                    "sourceFileMoved": False,
                    "sourceFileDeleted": False,
                    "folderImportEnabled": False,
                    "archiveExtractionEnabled": False,
                    "routeExecutionEnabled": False,
                    "toolLaunchEnabled": False,
                },
            }
        ),
        encoding="utf-8",
    )


def build_service(root: Path, data_root: Path) -> IntakeCatalogService:
    """Purpose: Build an intake service whose source and runtime roots are deliberately separate.

    Inputs: Caller-supplied ``root``, ``data_root`` values from the signature.
    Outputs: Returns ``IntakeCatalogService``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Call ``result = instance.build_service(...)`` with values satisfying the documented inputs.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    paths = RuntimePathsService(
        source_root=root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=root.parent / "home",
        platform_name="linux",
    )
    workspace = WorkspaceConfigService(root, paths)
    return IntakeCatalogService(root, workspace)


def test_stage_file_records_metadata_without_copying_source(tmp_path: Path) -> None:
    """Purpose: Staging records metadata while preserving bytes and withholding source paths.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_stage_file_records_metadata_without_copying_source``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    source_dir = tmp_path / "user-files"
    source_dir.mkdir()
    source = source_dir / "fixture.STL"
    original = b"solid fixture\nendsolid fixture\n"
    source.write_bytes(original)
    data_root = tmp_path / "runtime-data"
    service = build_service(tmp_path, data_root)

    record = service.stage_file_metadata(source)

    assert source.read_bytes() == original
    assert record["source"]["displayName"] == "fixture.STL"
    assert record["source"]["kind"] == "mesh"
    assert record["privacy"] == {"sourcePathStored": False, "sourceContentStored": False}
    assert str(source.resolve()) not in json.dumps(record)
    records_root = data_root / "intake" / "records"
    record_files = list(records_root.iterdir())
    assert len(record_files) == 1
    assert record_files[0].suffix == ".json"
    catalog = service.catalog()
    assert catalog["summary"]["recordCount"] == 1
    assert catalog["recordsPath"] == "makers-anvil-data://user/intake/records"
    assert str(data_root) not in json.dumps(catalog)


def test_stage_file_rejects_folder_intake(tmp_path: Path) -> None:
    """Purpose: Intake accepts one regular file and rejects folder import.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_stage_file_rejects_folder_intake``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    source_dir = tmp_path / "folder"
    source_dir.mkdir()

    with pytest.raises(IntakeCatalogError, match="not a folder"):
        build_service(tmp_path, tmp_path / "runtime-data").stage_file_metadata(source_dir)


def test_archive_is_detected_without_extraction(tmp_path: Path) -> None:
    """Purpose: Archive classification does not imply or perform extraction.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_archive_is_detected_without_extraction``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    source = tmp_path / "bundle.zip"
    source.write_bytes(b"not extracted")

    record = build_service(tmp_path, tmp_path / "runtime-data").stage_file_metadata(source)

    assert record["source"]["kind"] == "archive"
    assert record["safety"]["archiveExtracted"] is False
    assert source.read_bytes() == b"not extracted"


def test_catalog_excludes_record_missing_required_safety_flags(tmp_path: Path) -> None:
    """Purpose: Malformed records are counted as invalid and never returned as usable data.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_catalog_excludes_record_missing_required_safety_flags``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    data_root = tmp_path / "runtime-data"
    records_root = data_root / "intake" / "records"
    records_root.mkdir(parents=True)
    (records_root / "invalid.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.runtime.intake-record.v1",
                "id": "intake-invalid",
                "source": {},
                "privacy": {},
                "safety": {},
            }
        ),
        encoding="utf-8",
    )

    catalog = build_service(tmp_path, data_root).catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["summary"]["recordCount"] == 0
    assert catalog["summary"]["invalidRecordCount"] == 1


def test_catalog_excludes_record_with_incomplete_source_metadata(tmp_path: Path) -> None:
    """Purpose: A record with valid safety flags but incomplete source metadata is unusable.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_catalog_excludes_record_with_incomplete_source_metadata``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    data_root = tmp_path / "runtime-data"
    records_root = data_root / "intake" / "records"
    records_root.mkdir(parents=True)
    (records_root / "invalid-source.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.runtime.intake-record.v1",
                "id": "intake-invalid-source",
                "source": {"displayName": "missing-fields.stl"},
                "privacy": {
                    "sourcePathStored": False,
                    "sourceContentStored": False,
                },
                "safety": {
                    "sourceFileCopied": False,
                    "sourceFileMoved": False,
                    "sourceFileDeleted": False,
                    "archiveExtracted": False,
                    "routeExecuted": False,
                    "toolLaunched": False,
                },
            }
        ),
        encoding="utf-8",
    )

    catalog = build_service(tmp_path, data_root).catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["records"] == []
    assert catalog["summary"]["invalidRecordCount"] == 1


def test_catalog_counts_non_object_json_as_invalid(tmp_path: Path) -> None:
    """Purpose: Valid JSON with the wrong top-level type is rejected without crashing readers.

    Inputs: Pytest fixtures and isolated values named by the function signature.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Source paths/contents, folders, symlinks, archives, and launch stay out.
    Example: Run ``python -m pytest tests/test_intake_catalog.py -k test_catalog_counts_non_object_json_as_invalid``.
    Related proof: ``services/intake_catalog.py`` and intake schemas.
    """

    write_config(tmp_path)
    data_root = tmp_path / "runtime-data"
    records_root = data_root / "intake" / "records"
    records_root.mkdir(parents=True)
    (records_root / "array.json").write_text("[]", encoding="utf-8")

    catalog = build_service(tmp_path, data_root).catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["records"] == []
    assert catalog["summary"]["invalidRecordCount"] == 1
