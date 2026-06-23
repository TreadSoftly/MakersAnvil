import json
from pathlib import Path

import pytest

from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService


def write_config(root: Path) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "default_settings.json").write_text(
        json.dumps(
            {
                "schemaVersion": "makers-anvil.config.local-settings.v1",
                "claimState": "staged",
                "runtimeRoot": ".makers-anvil",
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


def test_stage_file_records_metadata_without_copying_source(tmp_path: Path) -> None:
    write_config(tmp_path)
    source_dir = tmp_path / "user-files"
    source_dir.mkdir()
    source = source_dir / "fixture.STL"
    original = b"solid fixture\nendsolid fixture\n"
    source.write_bytes(original)
    service = IntakeCatalogService(tmp_path)

    record = service.stage_file_metadata(source)

    assert source.read_bytes() == original
    assert record["source"]["displayName"] == "fixture.STL"
    assert record["source"]["kind"] == "mesh"
    assert record["privacy"] == {"sourcePathStored": False, "sourceContentStored": False}
    assert str(source.resolve()) not in json.dumps(record)
    records_root = tmp_path / ".makers-anvil" / "intake" / "records"
    record_files = list(records_root.iterdir())
    assert len(record_files) == 1
    assert record_files[0].suffix == ".json"
    assert service.catalog()["summary"]["recordCount"] == 1


def test_stage_file_rejects_folder_intake(tmp_path: Path) -> None:
    write_config(tmp_path)
    source_dir = tmp_path / "folder"
    source_dir.mkdir()

    with pytest.raises(IntakeCatalogError, match="not a folder"):
        IntakeCatalogService(tmp_path).stage_file_metadata(source_dir)


def test_archive_is_detected_without_extraction(tmp_path: Path) -> None:
    write_config(tmp_path)
    source = tmp_path / "bundle.zip"
    source.write_bytes(b"not extracted")

    record = IntakeCatalogService(tmp_path).stage_file_metadata(source)

    assert record["source"]["kind"] == "archive"
    assert record["safety"]["archiveExtracted"] is False
    assert source.read_bytes() == b"not extracted"


def test_catalog_excludes_record_missing_required_safety_flags(tmp_path: Path) -> None:
    write_config(tmp_path)
    records_root = tmp_path / ".makers-anvil" / "intake" / "records"
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

    catalog = IntakeCatalogService(tmp_path).catalog()

    assert catalog["claimState"] == "failed"
    assert catalog["summary"]["recordCount"] == 0
    assert catalog["summary"]["invalidRecordCount"] == 1
