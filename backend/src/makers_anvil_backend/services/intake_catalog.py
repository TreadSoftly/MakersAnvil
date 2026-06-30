"""Purpose: Record and list metadata-only and explicitly authorized intake files.

Used by: The staging script, authorized transfer service, and app-state routes.
Inputs: Metadata-only local paths or validated app-owned authorized records.
Outputs: Path-redacted JSON records for catalog and planning consumers.
Side effects: Writes/removes only validated app-owned intake record files.
Safety: Source paths, folders, symlinks, extraction, handoff, and launch are denied.
Failure behavior: Invalid input or malformed records fail closed with errors.
Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


from makers_anvil_backend.runtime_resources import application_root


ROOT = application_root()
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
AUTHORIZED_PRIVACY_FLAGS = {"sourcePathStored", "sourceContentStored", "originalDisplayNameStored"}
AUTHORIZED_STORAGE_FIELDS = {
    "logicalReference",
    "generatedName",
    "sizeBytes",
    "sha256",
    "integrityVerified",
    "quarantineState",
    "contentTypeVerified",
    "malwareScanPassed",
}
AUTHORIZED_SAFETY_FLAGS = {
    "sourceFileCopied",
    "sourceFileMoved",
    "sourceFileDeleted",
    "archiveExtracted",
    "selectedFileHandedOff",
    "routeExecuted",
    "toolLaunched",
}


class IntakeCatalogError(ValueError):
    """Purpose: Raised when a source cannot be safely staged as metadata.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``IntakeCatalogError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
    Example: Construct with ``instance = IntakeCatalogError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
    """


class IntakeCatalogService:
    """Purpose: Persist and list path-redacted intake records for both safe modes.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``IntakeCatalogService`` exposing the state and operations defined below.
    How it works: It checks conditions, then iterates over bounded records, then handles expected failures explicitly, then returns the resulting contract value.
    Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Source paths, folders, symlinks, extraction, handoff, and launch are denied.
    Example: Construct with ``instance = IntakeCatalogService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
    """

    def __init__(
        self,
        root: Path | None = None,
        workspace_config: WorkspaceConfigService | None = None,
    ) -> None:
        """Purpose: Bind intake policy and app-owned record storage without retaining source paths.

        Inputs: Caller-supplied ``root``, ``workspace_config`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        self.root = root or ROOT
        self.workspace_config = workspace_config or WorkspaceConfigService(self.root)
        self.policy_path = self.root / "config" / "intake_policy.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load the committed authorized-local-copy intake policy.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance.policy(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        return json.loads(self.policy_path.read_text(encoding="utf-8"))

    def policy_response(self) -> dict[str, Any]:
        """Purpose: Expose intake policy through logical paths and explicit safety boundaries.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance.policy_response(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        policy = self.policy()
        return {
            **policy,
            "recordsPath": self.workspace_config.logical_runtime_path(policy["recordsDirectory"]),
            "boundaries": [
                "One chosen file requires a separate explicit authorization action.",
                "The original source path is never transmitted or stored.",
                "Authorized content is copied once into app-owned quarantine storage with a SHA-256 digest.",
                "Folder import, archive upload/extraction, selected-file handoff, route execution, and tool launch remain blocked.",
            ],
        }

    def catalog(self) -> dict[str, Any]:
        """Purpose: Read valid runtime records, count rejected records, and expose no source paths.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then handles expected failures explicitly, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance.catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

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

        # Random record ids deliberately carry no ordering meaning. Showing the
        # newest ISO-UTC record first keeps the workbench selection deterministic.
        records.sort(key=lambda item: item.get("createdUtc", ""), reverse=True)
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
                "id": "authorized-browser-intake",
                "claimState": "staged",
                "enabledInApi": policy["capabilities"]["apiMutationEnabled"],
                "requiresExplicitAuthorization": True,
                "authorizeEndpoint": "/api/intake/authorizations",
                "contentEndpointTemplate": "/api/intake/authorizations/{authorizationId}/content",
            },
        }

    def stage_file_metadata(self, source_path: str | Path) -> dict[str, Any]:
        """Purpose: Write metadata for one regular file without storing its path or changing it.

        Inputs: Caller-supplied ``source_path`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance.stage_file_metadata(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

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
        self._write_record(record, policy)
        return record

    def store_authorized_record(self, record: dict[str, Any]) -> None:
        """Purpose: Persist one validated authorized-content record atomically.

        Inputs: Complete v1 authorized intake record produced after byte receipt.
        Outputs: ``None`` after the public catalog record is durable.
        How it works: Validates the strict record shape, then replaces one temp JSON file.
        Side effects: Creates the app-owned records directory and one JSON record.
        Failure behavior: Invalid records raise ``IntakeCatalogError`` before writing.
        Safety: Never accepts a source path, content bytes, command, or external target.
        Example: ``catalog.store_authorized_record(record)`` publishes contained intake metadata.
        Related proof: ``tests/test_authorized_intake.py`` covers valid and weakened records.
        """

        if not self._valid_authorized_record(record):
            raise IntakeCatalogError("authorized intake record does not satisfy the strict catalog contract")
        self._write_record(record, self.policy())

    def remove_record(self, record_id: str) -> None:
        """Purpose: Roll back one app-owned record after an incomplete intake transaction.

        Inputs: Validated random intake identifier generated by the current service.
        Outputs: ``None`` whether the rollback file exists or is already absent.
        How it works: Resolves the exact record filename under the contained records root.
        Side effects: Deletes only that app-owned JSON record during failure cleanup.
        Failure behavior: Invalid identifiers raise before any filesystem action.
        Safety: Cannot accept paths, separators, traversal, globs, or user filenames.
        Example: Failed authorization finalization calls ``remove_record(intake_id)``.
        Related proof: ``tests/test_authorized_intake.py`` exercises transactional cleanup.
        """

        path = self._record_path(record_id, self.policy())
        path.unlink(missing_ok=True)

    def record_exists(self, record_id: str) -> bool:
        """Purpose: Detect an existing app-owned record before consuming authorization.

        Inputs: Validated random intake identifier, never a path.
        Outputs: Boolean existence result for the exact contained JSON record.
        How it works: Resolves the identifier through the same strict path helper as writes.
        Side effects: Reads filesystem metadata only.
        Failure behavior: Invalid identifiers raise instead of probing another location.
        Safety: No path text from a browser reaches the filesystem.
        Example: The transfer service rejects a duplicate id when this returns true.
        Related proof: ``tests/test_authorized_intake.py`` covers one-time consumption.
        """

        return self._record_path(record_id, self.policy()).exists()

    def classify_extension(self, extension: str) -> str:
        """Purpose: Classify one normalized extension through committed intake policy.

        Inputs: Lowercase suffix beginning with a period.
        Outputs: Configured kind id or the honest ``unknown`` value.
        How it works: Delegates to the deterministic policy classifier used by metadata mode.
        Side effects: Reads the committed policy only.
        Failure behavior: Missing or malformed policy data propagates explicitly.
        Safety: Extension classification never reads file bytes or enables a route.
        Example: ``classify_extension('.stl')`` returns ``mesh``.
        Related proof: ``tests/test_intake_catalog.py`` and authorized-intake tests.
        """

        return self._classify(extension, self.policy())

    def _write_record(self, record: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Atomically write one already-validated intake catalog record.

        Inputs: Metadata or authorized record plus current committed policy.
        Outputs: ``None`` after the destination JSON file is complete.
        How it works: Writes a sibling temporary file and atomically replaces destination.
        Side effects: Creates the contained records directory and writes one JSON file.
        Failure behavior: Filesystem errors propagate; callers can roll back related content.
        Safety: Destination derives only from a validated random record id.
        Example: Both intake modes share this all-or-complete JSON write primitive.
        Related proof: Intake and authorized-intake failure tests.
        """

        records_root = self._records_root(policy)
        records_root.mkdir(parents=True, exist_ok=True)
        destination = self._record_path(record["id"], policy)
        temporary = records_root / f".{record['id']}.tmp"
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        # Replace only after a complete write so readers never observe a
        # partially-written JSON record if the process stops unexpectedly.
        temporary.replace(destination)

    def _record_path(self, record_id: str, policy: dict[str, Any]) -> Path:
        """Purpose: Resolve one random record id to an exact contained JSON path.

        Inputs: Intake id and current policy.
        Outputs: Path below the app-owned intake records directory.
        How it works: Enforces the fixed prefix, 32 lowercase hex characters, and no separators.
        Side effects: None; the path need not exist.
        Failure behavior: Malformed identifiers raise ``IntakeCatalogError``.
        Safety: Prevents traversal and arbitrary record deletion or overwrite.
        Example: ``intake-<32 hex>`` maps to ``intake/records/<id>.json``.
        Related proof: ``tests/test_authorized_intake.py`` probes invalid ids.
        """

        suffix = record_id.removeprefix("intake-")
        if not record_id.startswith("intake-") or len(suffix) != 32 or any(char not in "0123456789abcdef" for char in suffix):
            raise IntakeCatalogError("intake record id is invalid")
        return self._records_root(policy) / f"{record_id}.json"

    def _records_root(self, policy: dict[str, Any]) -> Path:
        """Purpose: Resolve the policy's contained intake directory inside app-owned storage.

        Inputs: Caller-supplied ``policy`` values from the signature.
        Outputs: Returns ``Path``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance._records_root(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        relative = Path(policy["recordsDirectory"])
        if relative.is_absolute() or ".." in relative.parts or not relative.parts or relative.parts[0] != "intake":
            raise IntakeCatalogError("records directory must stay under the app-owned intake directory")
        return self.workspace_config.runtime_path(relative)

    @staticmethod
    def _classify(extension: str, policy: dict[str, Any]) -> str:
        """Purpose: Map one normalized extension to a configured kind or the honest unknown state.

        Inputs: Caller-supplied ``extension``, ``policy`` values from the signature.
        Outputs: Returns ``str``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance._classify(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        for file_kind in policy["fileKinds"]:
            if extension in file_kind["extensions"]:
                return file_kind["id"]
        return "unknown"

    @staticmethod
    def _valid_runtime_record(record: dict[str, Any]) -> bool:
        """Purpose: Accept only one strict metadata or authorized intake record version.

        Inputs: Caller-supplied ``record`` values from the signature.
        Outputs: Returns ``bool``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Folders, symlinks, extraction, copying, execution, and launch are denied.
        Example: Call ``result = instance._valid_runtime_record(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_intake_catalog.py`` and intake schemas.
        """

        if record.get("schemaVersion") == "makers-anvil.runtime.intake-record.v1":
            return IntakeCatalogService._valid_metadata_record(record)
        if record.get("schemaVersion") == "makers-anvil.runtime.authorized-intake-record.v1":
            return IntakeCatalogService._valid_authorized_record(record)
        return False

    @staticmethod
    def _valid_metadata_record(record: dict[str, Any]) -> bool:
        """Purpose: Validate the historical metadata-only runtime record contract.

        Inputs: Untrusted decoded JSON mapping from the records directory.
        Outputs: Boolean strict-shape and constant-false safety result.
        How it works: Checks every source, privacy, and safety field without coercion.
        Side effects: None.
        Failure behavior: Unexpected types return false rather than becoming usable evidence.
        Safety: Preserves compatibility without weakening source privacy.
        Example: PASS-004 records remain readable after authorized intake is added.
        Related proof: ``tests/test_intake_catalog.py`` covers malformed variants.
        """

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

    @staticmethod
    def _valid_authorized_record(record: dict[str, Any]) -> bool:
        """Purpose: Validate a contained authorized-copy record before catalog use.

        Inputs: Untrusted decoded JSON or a newly composed transfer record.
        Outputs: Boolean result covering identity, hash, authorization, privacy, and safety.
        How it works: Requires exact field sets and fixed true/false containment claims.
        Side effects: None.
        Failure behavior: Any missing, extra, mistyped, or weakened field returns false.
        Safety: A stored file remains quarantined, unscanned, unhanded-off, and unexecuted.
        Example: A copied STL with a 64-hex SHA-256 can pass while a routeExecuted record fails.
        Related proof: ``tests/test_authorized_intake.py`` covers valid and weakened examples.
        """

        source = record.get("source", {})
        authorization = record.get("authorization", {})
        storage = record.get("storage", {})
        privacy = record.get("privacy", {})
        safety = record.get("safety", {})
        digest = storage.get("sha256")
        record_id = record.get("id")
        record_suffix = record_id.removeprefix("intake-") if isinstance(record_id, str) else ""
        return (
            record.get("schemaVersion") == "makers-anvil.runtime.authorized-intake-record.v1"
            and isinstance(record_id, str)
            and record_id.startswith("intake-")
            and len(record_suffix) == 32
            and all(char in "0123456789abcdef" for char in record_suffix)
            and isinstance(record.get("createdUtc"), str)
            and record.get("claimState") == "staged"
            and isinstance(source, dict)
            and set(source) == REQUIRED_SOURCE_FIELDS
            and isinstance(source.get("displayName"), str)
            and 0 < len(source.get("displayName", "")) <= 180
            and isinstance(source.get("extension"), str)
            and isinstance(source.get("kind"), str)
            and isinstance(source.get("sizeBytes"), int)
            and not isinstance(source.get("sizeBytes"), bool)
            and source.get("sizeBytes", 0) > 0
            and isinstance(source.get("modifiedUtc"), str)
            and isinstance(authorization, dict)
            and set(authorization) == {"id", "scope", "accepted", "acceptedUtc", "consumedUtc"}
            and isinstance(authorization.get("id"), str)
            and authorization.get("scope") == "copy-one-file-into-app-storage"
            and authorization.get("accepted") is True
            and isinstance(authorization.get("acceptedUtc"), str)
            and isinstance(authorization.get("consumedUtc"), str)
            and isinstance(storage, dict)
            and set(storage) == AUTHORIZED_STORAGE_FIELDS
            and storage.get("logicalReference") == f"makers-anvil-data://user/intake/files/{record.get('id')}"
            and storage.get("generatedName") == f"content{source.get('extension')}"
            and storage.get("sizeBytes") == source.get("sizeBytes")
            and isinstance(digest, str)
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
            and storage.get("integrityVerified") is True
            and storage.get("quarantineState") == "contained-untrusted"
            and storage.get("contentTypeVerified") is False
            and storage.get("malwareScanPassed") is False
            and set(privacy) == AUTHORIZED_PRIVACY_FLAGS
            and privacy == {
                "sourcePathStored": False,
                "sourceContentStored": True,
                "originalDisplayNameStored": True,
            }
            and set(safety) == AUTHORIZED_SAFETY_FLAGS
            and safety.get("sourceFileCopied") is True
            and all(value is False for key, value in safety.items() if key != "sourceFileCopied")
        )
