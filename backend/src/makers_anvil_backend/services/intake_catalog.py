"""Metadata-only local file intake records for Makers Anvil."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[4]
REQUIRED_PRIVACY_FLAGS = {"sourcePathStored", "sourceContentStored"}
REQUIRED_SOURCE_FIELDS = {"displayName", "extension", "kind", "sizeBytes", "modifiedUtc"}
REQUIRED_RECORD_SAFETY_FLAGS = {
    "sourceFileCopied",
    "sourceFileMoved",
    "sourceFileDeleted",
    "archiveExtracted",
    "routeExecuted",
    "toolLaunched",
}


class IntakeCatalogError(ValueError):
    """Raised when a source cannot be safely staged as metadata."""


class IntakeCatalogService:
    """Stage and list app-owned metadata records without copying source files."""

    def __init__(
        self,
        root: Path | None = None,
        workspace_config: WorkspaceConfigService | None = None,
    ) -> None:
        self.root = root or ROOT
        self.workspace_config = workspace_config or WorkspaceConfigService(self.root)
        self.policy_path = self.root / "config" / "intake_policy.json"

    def policy(self) -> dict[str, Any]:
        """Load the committed metadata-only intake policy from the source package."""

        return json.loads(self.policy_path.read_text(encoding="utf-8"))

    def policy_response(self) -> dict[str, Any]:
        """Expose intake policy through logical paths and explicit safety boundaries."""

        policy = self.policy()
        return {
            **policy,
            "recordsPath": self.workspace_config.logical_runtime_path(policy["recordsDirectory"]),
            "boundaries": [
                "Intake stores app-owned metadata records only.",
                "Source paths and source file contents are not stored.",
                "Source files are not copied, moved, deleted, extracted, executed, or handed to tools.",
                "Browser and API intake mutations remain blocked.",
            ],
        }

    def catalog(self) -> dict[str, Any]:
        """Read valid runtime records, count rejected records, and expose no source paths."""

        policy = self.policy()
        records_root = self._records_root(policy)
        records: list[dict[str, Any]] = []
        invalid_record_count = 0
        # Runtime records are untrusted local data. Invalid JSON or weakened
        # safety flags are counted but never returned as usable intake records.
        if records_root.exists():
            for path in sorted(records_root.glob("*.json")):
                try:
                    record = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    invalid_record_count += 1
                    continue
                if not isinstance(record, dict) or not self._valid_runtime_record(record):
                    invalid_record_count += 1
                    continue
                records.append(record)

        by_kind: dict[str, int] = {}
        for record in records:
            kind = record["source"]["kind"]
            by_kind[kind] = by_kind.get(kind, 0) + 1

        return {
            "schemaVersion": "makers-anvil.api.intake-catalog.v1",
            "claimState": "staged" if invalid_record_count == 0 else "failed",
            "mode": policy["mode"],
            "recordsPath": self.policy_response()["recordsPath"],
            "recordsRootExists": records_root.exists(),
            "summary": {
                "recordCount": len(records),
                "invalidRecordCount": invalid_record_count,
                "byKind": by_kind,
            },
            "records": records,
            "safety": policy["safety"],
            "creationAction": {
                "id": "metadata-intake-script",
                "claimState": "staged",
                "enabledInApi": False,
                "script": "python scripts/stage_intake.py --path <file>",
            },
        }

    def stage_file_metadata(self, source_path: str | Path) -> dict[str, Any]:
        """Write metadata for one regular file without storing its path or changing it."""

        source = Path(source_path).expanduser()
        if not source.exists():
            raise IntakeCatalogError("source file does not exist")
        if source.is_symlink():
            raise IntakeCatalogError("symbolic-link sources are not accepted")
        if not source.is_file():
            raise IntakeCatalogError("intake accepts one regular file, not a folder")

        policy = self.policy()
        stat = source.stat()
        extension = source.suffix.lower()
        record = {
            "schemaVersion": "makers-anvil.runtime.intake-record.v1",
            "id": f"intake-{uuid4().hex}",
            "claimState": "staged",
            "createdUtc": datetime.now(UTC).isoformat(),
            "source": {
                "displayName": source.name,
                "extension": extension,
                "kind": self._classify(extension, policy),
                "sizeBytes": stat.st_size,
                "modifiedUtc": datetime.fromtimestamp(stat.st_mtime, UTC).isoformat(),
            },
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
        records_root = self._records_root(policy)
        records_root.mkdir(parents=True, exist_ok=True)
        destination = records_root / f"{record['id']}.json"
        temporary = records_root / f".{record['id']}.tmp"
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        # Replace only after a complete write so readers never observe a
        # partially-written JSON record if the process stops unexpectedly.
        temporary.replace(destination)
        return record

    def _records_root(self, policy: dict[str, Any]) -> Path:
        relative = Path(policy["recordsDirectory"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "intake":
            raise IntakeCatalogError("records directory must stay under the app-owned intake directory")
        return self.workspace_config.runtime_path(relative)

    @staticmethod
    def _classify(extension: str, policy: dict[str, Any]) -> str:
        for file_kind in policy["fileKinds"]:
            if extension in file_kind["extensions"]:
                return file_kind["id"]
        return "unknown"

    @staticmethod
    def _valid_runtime_record(record: dict[str, Any]) -> bool:
        source = record.get("source", {})
        privacy = record.get("privacy", {})
        safety = record.get("safety", {})
        return (
            record.get("schemaVersion") == "makers-anvil.runtime.intake-record.v1"
            and isinstance(record.get("id"), str)
            and isinstance(source, dict)
            and set(source) == REQUIRED_SOURCE_FIELDS
            and isinstance(source.get("displayName"), str)
            and isinstance(source.get("extension"), str)
            and isinstance(source.get("kind"), str)
            and isinstance(source.get("sizeBytes"), int)
            and not isinstance(source.get("sizeBytes"), bool)
            and source.get("sizeBytes", -1) >= 0
            and isinstance(source.get("modifiedUtc"), str)
            and set(privacy) == REQUIRED_PRIVACY_FLAGS
            and privacy.get("sourcePathStored") is False
            and privacy.get("sourceContentStored") is False
            and set(safety) == REQUIRED_RECORD_SAFETY_FLAGS
            and all(value is False for value in safety.values())
        )
