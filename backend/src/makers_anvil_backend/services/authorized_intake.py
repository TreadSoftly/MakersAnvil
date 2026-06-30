"""Purpose: Authorize and contain one browser-selected file in app-owned storage.

Used by: The API facade's two narrowly allowlisted intake POST routes.
Inputs: Same-origin request context, path-free file metadata, and bounded byte streams.
Outputs: Short-lived authorization records and quarantined intake catalog records.
Side effects: Writes only app-owned authorization, content, and catalog files.
Safety: Uses one-time consent, extension/size limits, hashing, and atomic replacement.
Failure behavior: Invalid, expired, cross-origin, replayed, or partial requests fail closed.
Related proof: ``tests/test_authorized_intake.py`` and intake transfer schemas.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Callable
from urllib.parse import urlsplit
from uuid import uuid4

from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService


TRANSFER_SCOPE = "copy-one-file-into-app-storage"
AUTHORIZATION_FIELDS = {
    "schemaVersion",
    "id",
    "intakeId",
    "claimState",
    "scope",
    "createdUtc",
    "expiresUtc",
    "accepted",
    "acceptedUtc",
    "consumed",
    "consumedUtc",
    "source",
}
SOURCE_FIELDS = {"displayName", "extension", "kind", "sizeBytes", "modifiedUtc"}


class IntakeTransferError(ValueError):
    """Purpose: Carry an honest HTTP status and stable code for intake rejection.

    Inputs: Status, machine code, and user-safe diagnostic supplied by a guard.
    Outputs: Exception exposing ``status`` and ``code`` beside normal message text.
    How it works: Stores bounded response metadata, then initializes ``ValueError``.
    Side effects: None until raised and handled by the API facade.
    Failure behavior: The original rejection message remains available to tests/UI.
    Safety: Diagnostics never include source paths, request tokens, or private roots.
    Example: ``raise IntakeTransferError(413, 'file_too_large', 'File exceeds limit.')``.
    Related proof: ``tests/test_authorized_intake.py`` asserts status/code mappings.
    """

    def __init__(self, status: int, code: str, message: str) -> None:
        """Purpose: Initialize one typed transfer rejection.

        Inputs: HTTP status, stable snake-case code, and path-free message.
        Outputs: Initialized exception instance; constructors return ``None``.
        How it works: Saves response fields before delegating message storage.
        Side effects: None.
        Failure behavior: Invalid constructor values remain visible programming errors.
        Safety: Callers control diagnostics and must not include secrets or paths.
        Example: API handlers read ``exc.status`` and ``exc.code`` after catching.
        Related proof: Error-response tests in ``tests/test_authorized_intake.py``.
        """

        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class IntakeRequestContext:
    """Purpose: Describe the browser security headers required for local mutation.

    Inputs: Process token, HTTP Origin/Host, and Fetch Metadata site relationship.
    Outputs: Immutable request context consumed by ``AuthorizedIntakeService``.
    How it works: Dataclass generation provides a typed constructor and attributes.
    Side effects: None.
    Failure behavior: Missing values are rejected by service validation, not guessed.
    Safety: Keeps transport security evidence explicit at the service boundary.
    Example: Same-origin fetch passes token, ``http://127.0.0.1:port``, and host.
    Related proof: Origin, token, and fetch-site rejection tests.
    """

    request_token: str
    origin: str
    host: str
    fetch_site: str


class AuthorizedIntakeService:
    """Purpose: Own one-file consent and transactional app-owned byte intake.

    Inputs: Intake catalog, process token, clock, and user-selected metadata/bytes.
    Outputs: Session policy, authorization response, and authorized intake record.
    How it works: Validates same origin, persists consent, streams/hashes once, commits atomically.
    Side effects: Creates only contained runtime authorization, file, and record entries.
    Failure behavior: Every validation/storage failure raises ``IntakeTransferError``.
    Safety: No source path, archive, folder, executable action, handoff, or tool is accepted.
    Example: Browser authorizes ``part.stl`` then uploads exactly its declared bytes.
    Related proof: ``tests/test_authorized_intake.py`` and live browser intake smoke.
    """

    def __init__(
        self,
        intake_catalog: IntakeCatalogService | None = None,
        *,
        request_token: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Purpose: Bind one process-local token to shared intake storage and policy.

        Inputs: Optional injected catalog, request token, and UTC clock for tests.
        Outputs: Initialized service with a serialization lock.
        How it works: Creates cryptographic token only when the caller did not inject one.
        Side effects: Generates random memory-only token; writes no file at construction.
        Failure behavior: Dependency construction errors propagate before service use.
        Safety: The token is never persisted and changes on every application process.
        Example: Tests inject ``request-token`` while production uses ``token_urlsafe``.
        Related proof: Session and restart-boundary tests.
        """

        self.intake_catalog = intake_catalog or IntakeCatalogService()
        self._request_token = request_token or secrets.token_urlsafe(32)
        self._clock = clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()

    def session(self) -> dict[str, Any]:
        """Purpose: Expose process-local authorization requirements to same-origin UI.

        Inputs: Committed intake policy and in-memory request token.
        Outputs: Path-free endpoint, constraint, capability, and safety record.
        How it works: Flattens allowed-kind extensions and returns conservative policy truth.
        Side effects: Reads committed policy only.
        Failure behavior: Invalid policy data propagates rather than enabling a picker.
        Safety: No CORS header exposes this token to another browser origin.
        Example: The workbench uses ``allowedExtensions`` for its file-input accept list.
        Related proof: Session schema validation and API security tests.
        """

        policy = self.intake_catalog.policy()
        allowed_kinds = set(policy["uploadAllowedKinds"])
        allowed_extensions = sorted(
            extension
            for group in policy["fileKinds"]
            if group["id"] in allowed_kinds
            for extension in group["extensions"]
        )
        return {
            "schemaVersion": "makers-anvil.api.intake-session.v1",
            "claimState": "staged",
            "mode": "same-origin-one-file",
            "requestToken": self._request_token,
            "authorizeEndpoint": "/api/intake/authorizations",
            "contentEndpointTemplate": "/api/intake/authorizations/{authorizationId}/content",
            "constraints": {
                "maxFileBytes": policy["maxFileBytes"],
                "authorizationLifetimeSeconds": policy["authorizationLifetimeSeconds"],
                "allowedExtensions": allowed_extensions,
                "oneFilePerAuthorization": True,
            },
            "capabilities": policy["capabilities"],
            "safety": policy["safety"],
        }

    def authorize(self, metadata: dict[str, Any], context: IntakeRequestContext) -> dict[str, Any]:
        """Purpose: Persist explicit consent for exactly one reviewed file description.

        Inputs: Path-free display name, byte size, modified time, and guarded context.
        Outputs: Public authorization with id, scope, expiry, and normalized source metadata.
        How it works: Validates origin/token, allowlists extension/kind/size, then writes atomically.
        Side effects: Creates one JSON authorization under app-owned runtime storage.
        Failure behavior: Invalid metadata, archives, oversize files, or unsafe context fail.
        Safety: Consent is one-file, short-lived, unconsumed, and contains no source path.
        Example: A reviewed 2 KiB ``part.stl`` yields an authorization valid for ten minutes.
        Related proof: Authorization allowlist, privacy, and expiry tests.
        """

        self._validate_context(context)
        policy = self.intake_catalog.policy()
        source = self._validate_metadata(metadata, policy)
        now = self._utc_now()
        authorization = {
            "schemaVersion": "makers-anvil.runtime.intake-authorization.v1",
            "id": f"intake-auth-{uuid4().hex}",
            "intakeId": f"intake-{uuid4().hex}",
            "claimState": "staged",
            "scope": TRANSFER_SCOPE,
            "createdUtc": now.isoformat(),
            "expiresUtc": (now + timedelta(seconds=policy["authorizationLifetimeSeconds"])).isoformat(),
            "accepted": True,
            "acceptedUtc": now.isoformat(),
            "consumed": False,
            "consumedUtc": None,
            "source": source,
        }
        with self._lock:
            self._write_authorization(authorization, policy)
        return {
            "schemaVersion": "makers-anvil.api.intake-authorization.v1",
            "claimState": "staged",
            "authorization": self._public_authorization(authorization),
        }

    def ingest(
        self,
        authorization_id: str,
        stream: BinaryIO,
        content_length: int,
        context: IntakeRequestContext,
    ) -> dict[str, Any]:
        """Purpose: Stream one authorized file into generated app-owned quarantine storage.

        Inputs: Authorization id, request stream, exact Content-Length, and guarded context.
        Outputs: Authorized intake record with SHA-256 and logical storage reference.
        How it works: Revalidates consent, writes bounded chunks, atomically commits, and consumes once.
        Side effects: Writes one generated content file, catalog record, and consumed authorization.
        Failure behavior: Partial, mismatched, expired, replayed, duplicate, or I/O failures roll back.
        Safety: Bytes stay outside webroot and remain unscanned, unhanded-off, and unexecuted.
        Example: Uploading declared STL bytes returns a staged contained-untrusted record.
        Related proof: Streaming, hash, replay, rollback, and containment tests.
        """

        self._validate_context(context)
        policy = self.intake_catalog.policy()
        temporary: Path | None = None
        destination: Path | None = None
        record_written = False
        with self._lock:
            authorization = self._load_authorization(authorization_id, policy)
            self._require_usable_authorization(authorization)
            expected_size = authorization["source"]["sizeBytes"]
            if content_length != expected_size:
                raise IntakeTransferError(400, "content_length_mismatch", "File bytes do not match the authorized size.")
            files_root = self._runtime_directory(policy["filesDirectory"], "files")
            files_root.mkdir(parents=True, exist_ok=True)
            destination = files_root / f"{authorization['intakeId']}{authorization['source']['extension']}"
            temporary = files_root / f".{authorization['intakeId']}.{uuid4().hex}.part"
            if destination.exists() or self.intake_catalog.record_exists(authorization["intakeId"]):
                raise IntakeTransferError(409, "intake_already_exists", "The authorized intake destination already exists.")
            try:
                digest = self._stream_to_file(stream, temporary, content_length)
                os.replace(temporary, destination)
                consumed_utc = self._utc_now().isoformat()
                record = self._authorized_record(authorization, digest, consumed_utc)
                self.intake_catalog.store_authorized_record(record)
                record_written = True
                authorization["consumed"] = True
                authorization["consumedUtc"] = consumed_utc
                self._write_authorization(authorization, policy)
            except Exception:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
                if destination is not None:
                    destination.unlink(missing_ok=True)
                if record_written:
                    self.intake_catalog.remove_record(authorization["intakeId"])
                raise
        return {
            "schemaVersion": "makers-anvil.api.intake-result.v1",
            "claimState": "staged",
            "record": record,
        }

    def _validate_context(self, context: IntakeRequestContext) -> None:
        """Purpose: Require process token and same-origin browser evidence before mutation.

        Inputs: Token, Origin, Host, and Sec-Fetch-Site values from the HTTP request.
        Outputs: ``None`` only when all local request guards pass.
        How it works: Constant-time compares token and requires exact HTTP origin/host equality.
        Side effects: None.
        Failure behavior: Missing or mismatched evidence raises a path-free 403 error.
        Safety: Cross-site forms/fetches cannot obtain consent or stream bytes.
        Example: ``Origin: http://127.0.0.1:8766`` must match ``Host`` exactly.
        Related proof: Cross-origin, missing-token, and fetch-site tests.
        """

        if not context.request_token or not hmac.compare_digest(context.request_token, self._request_token):
            raise IntakeTransferError(403, "request_token_rejected", "The local intake request token is missing or invalid.")
        if context.fetch_site != "same-origin":
            raise IntakeTransferError(403, "cross_origin_rejected", "Intake mutations require a same-origin browser request.")
        try:
            parsed_origin = urlsplit(context.origin)
        except ValueError as exc:
            raise IntakeTransferError(403, "origin_rejected", "The intake request origin is invalid.") from exc
        if parsed_origin.scheme != "http" or not parsed_origin.hostname or parsed_origin.username or parsed_origin.password:
            raise IntakeTransferError(403, "origin_rejected", "The intake request origin is invalid.")
        if parsed_origin.netloc.lower() != context.host.strip().lower():
            raise IntakeTransferError(403, "origin_rejected", "The intake request origin does not match the local app.")
        if parsed_origin.hostname.lower() not in {"127.0.0.1", "localhost", "::1"}:
            raise IntakeTransferError(403, "origin_rejected", "Intake mutations require a loopback origin.")

    def _validate_metadata(self, metadata: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Normalize and allowlist path-free browser file metadata.

        Inputs: Three-field metadata object and committed size/kind policy.
        Outputs: Normalized source mapping safe for authorization persistence.
        How it works: Rejects separators/control text, derives final suffix, and parses UTC time.
        Side effects: None.
        Failure behavior: Unknown/archive extensions, invalid sizes, and malformed times fail.
        Safety: Browser Content-Type and directory-relative metadata are never trusted.
        Example: ``model.stl`` becomes extension ``.stl`` and kind ``mesh``.
        Related proof: Filename, double-extension, archive, size, and timestamp tests.
        """

        if not isinstance(metadata, dict) or set(metadata) != {"displayName", "sizeBytes", "modifiedUtc"}:
            raise IntakeTransferError(400, "metadata_invalid", "File metadata must contain only name, size, and modified time.")
        display_name = metadata.get("displayName")
        size_bytes = metadata.get("sizeBytes")
        modified_utc = metadata.get("modifiedUtc")
        if (
            not isinstance(display_name, str)
            or not 0 < len(display_name) <= 180
            or display_name != display_name.strip()
            or display_name in {".", ".."}
            or any(character in display_name for character in ("/", "\\", "\x00"))
            or any(ord(character) < 32 for character in display_name)
        ):
            raise IntakeTransferError(400, "filename_invalid", "Choose one file with a normal filename of 180 characters or fewer.")
        extension = Path(display_name).suffix.lower()
        kind = self.intake_catalog.classify_extension(extension)
        if kind not in policy["uploadAllowedKinds"]:
            raise IntakeTransferError(415, "file_type_not_allowed", "This file extension is not enabled for authorized intake.")
        if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes <= 0:
            raise IntakeTransferError(400, "file_size_invalid", "The selected file must contain at least one byte.")
        if size_bytes > policy["maxFileBytes"]:
            raise IntakeTransferError(413, "file_too_large", "The selected file exceeds the configured intake size limit.")
        parsed_modified = self._parse_timestamp(modified_utc, "modifiedUtc")
        return {
            "displayName": display_name,
            "extension": extension,
            "kind": kind,
            "sizeBytes": size_bytes,
            "modifiedUtc": parsed_modified.isoformat(),
        }

    def _require_usable_authorization(self, authorization: dict[str, Any]) -> None:
        """Purpose: Reject expired, consumed, malformed, or unaccepted authorization.

        Inputs: Decoded app-owned authorization record.
        Outputs: ``None`` only while the one-file consent can be consumed.
        How it works: Applies strict shape validation, then checks time and consumption.
        Side effects: Reads the injected clock only.
        Failure behavior: Invalid records fail 409/422 and never accept request bytes.
        Safety: Prevents replay and use beyond the explicit short consent window.
        Example: A second upload against the same authorization returns conflict.
        Related proof: Expiry, replay, and weakened-record tests.
        """

        if not self._valid_authorization(authorization):
            raise IntakeTransferError(422, "authorization_invalid", "The stored intake authorization is invalid.")
        if authorization["consumed"]:
            raise IntakeTransferError(409, "authorization_consumed", "This intake authorization has already been used.")
        if self._parse_timestamp(authorization["expiresUtc"], "expiresUtc") <= self._utc_now():
            raise IntakeTransferError(409, "authorization_expired", "This intake authorization has expired.")

    def _stream_to_file(self, stream: BinaryIO, destination: Path, content_length: int) -> str:
        """Purpose: Write exactly the authorized byte count while calculating SHA-256.

        Inputs: Binary request stream, unique app-owned temp path, and positive length.
        Outputs: Lowercase SHA-256 digest after the complete byte count is durable.
        How it works: Reads at most 1 MiB chunks until the declared length reaches zero.
        Side effects: Creates and writes one temporary file outside the webroot.
        Failure behavior: Early EOF raises and the caller removes every partial artifact.
        Safety: Memory use is bounded and no content is parsed, opened, or executed.
        Example: A 3 MiB file is processed through three bounded chunk iterations.
        Related proof: Hash, short-stream, large-chunk, and cleanup tests.
        """

        remaining = content_length
        digest = hashlib.sha256()
        with destination.open("xb") as handle:
            while remaining:
                chunk = stream.read(min(1024 * 1024, remaining))
                if not chunk:
                    raise IntakeTransferError(400, "content_incomplete", "The file transfer ended before all authorized bytes arrived.")
                handle.write(chunk)
                digest.update(chunk)
                remaining -= len(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        return digest.hexdigest()

    def _authorized_record(self, authorization: dict[str, Any], digest: str, consumed_utc: str) -> dict[str, Any]:
        """Purpose: Compose the public path-redacted record for contained bytes.

        Inputs: Valid authorization, SHA-256 digest, and successful consumption time.
        Outputs: Strict authorized-intake record accepted by the catalog.
        How it works: Copies normalized metadata and fixes every unproven effect false.
        Side effects: None.
        Failure behavior: Catalog validation rejects any future shape drift.
        Safety: Content remains explicitly untrusted, unscanned, and not handed off.
        Example: The record exposes a logical URI but never the runtime filesystem path.
        Related proof: Authorized-record schema and catalog validation tests.
        """

        source = dict(authorization["source"])
        return {
            "schemaVersion": "makers-anvil.runtime.authorized-intake-record.v1",
            "id": authorization["intakeId"],
            "claimState": "staged",
            "createdUtc": consumed_utc,
            "source": source,
            "authorization": {
                "id": authorization["id"],
                "scope": authorization["scope"],
                "accepted": True,
                "acceptedUtc": authorization["acceptedUtc"],
                "consumedUtc": consumed_utc,
            },
            "storage": {
                "logicalReference": f"makers-anvil-data://user/intake/files/{authorization['intakeId']}",
                "generatedName": f"content{source['extension']}",
                "sizeBytes": source["sizeBytes"],
                "sha256": digest,
                "integrityVerified": True,
                "quarantineState": "contained-untrusted",
                "contentTypeVerified": False,
                "malwareScanPassed": False,
            },
            "privacy": {
                "sourcePathStored": False,
                "sourceContentStored": True,
                "originalDisplayNameStored": True,
            },
            "safety": {
                "sourceFileCopied": True,
                "sourceFileMoved": False,
                "sourceFileDeleted": False,
                "archiveExtracted": False,
                "selectedFileHandedOff": False,
                "routeExecuted": False,
                "toolLaunched": False,
            },
        }

    def _load_authorization(self, authorization_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Load one exact app-owned authorization without path interpretation.

        Inputs: Authorization id and committed policy.
        Outputs: Decoded JSON object for strict usability validation.
        How it works: Resolves a fixed filename under the contained authorization root.
        Side effects: Reads one app-owned JSON file.
        Failure behavior: Missing, unreadable, malformed, or non-object data fails closed.
        Safety: The id grammar excludes separators, traversal, and user filenames.
        Example: Unknown random ids produce a 404 path-free response.
        Related proof: Missing and malformed authorization tests.
        """

        path = self._authorization_path(authorization_id, policy)
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise IntakeTransferError(404, "authorization_not_found", "The intake authorization does not exist.") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise IntakeTransferError(422, "authorization_invalid", "The stored intake authorization cannot be used.") from exc
        if not isinstance(value, dict):
            raise IntakeTransferError(422, "authorization_invalid", "The stored intake authorization cannot be used.")
        return value

    def _write_authorization(self, authorization: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Atomically persist one strict authorization state transition.

        Inputs: New or consumed authorization and committed policy.
        Outputs: ``None`` after a complete JSON replacement.
        How it works: Validates shape, writes a sibling temp file, then replaces destination.
        Side effects: Creates app-owned authorization directory and one JSON record.
        Failure behavior: Invalid shape or filesystem errors propagate before success.
        Safety: Token and source path are absent; destination derives from random id only.
        Example: Consumption replaces ``consumed: false`` with true atomically.
        Related proof: Authorization persistence and replay tests.
        """

        if not self._valid_authorization(authorization):
            raise IntakeTransferError(422, "authorization_invalid", "The intake authorization does not satisfy its strict contract.")
        root = self._runtime_directory(policy["authorizationsDirectory"], "authorizations")
        root.mkdir(parents=True, exist_ok=True)
        destination = self._authorization_path(authorization["id"], policy)
        temporary = root / f".{authorization['id']}.{uuid4().hex}.tmp"
        temporary.write_text(json.dumps(authorization, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, destination)

    def _authorization_path(self, authorization_id: str, policy: dict[str, Any]) -> Path:
        """Purpose: Map one random authorization id to a contained JSON filename.

        Inputs: Browser-returned id and committed policy.
        Outputs: Exact path below app-owned authorization storage.
        How it works: Requires fixed prefix and exactly 32 lowercase hexadecimal characters.
        Side effects: None.
        Failure behavior: Malformed ids raise 400 without filesystem probing.
        Safety: Prevents path traversal, globbing, and arbitrary file reads/writes.
        Example: ``intake-auth-<32 hex>`` maps to one ``.json`` file.
        Related proof: Invalid-id HTTP and service tests.
        """

        suffix = authorization_id.removeprefix("intake-auth-")
        if (
            not authorization_id.startswith("intake-auth-")
            or len(suffix) != 32
            or any(character not in "0123456789abcdef" for character in suffix)
        ):
            raise IntakeTransferError(400, "authorization_id_invalid", "The intake authorization id is invalid.")
        return self._runtime_directory(policy["authorizationsDirectory"], "authorizations") / f"{authorization_id}.json"

    def _runtime_directory(self, relative_text: str, expected_leaf: str) -> Path:
        """Purpose: Resolve one policy directory under the app-owned intake root.

        Inputs: Relative policy path and its required final directory name.
        Outputs: Private contained runtime path.
        How it works: Checks lexical ``intake/<leaf>`` shape before workspace resolution.
        Side effects: None; callers explicitly create directories later.
        Failure behavior: Absolute, traversing, renamed, or symlink-escaping paths fail.
        Safety: Keeps uploaded bytes and consent outside source/static trees.
        Example: ``intake/files`` is valid only for the ``files`` responsibility.
        Related proof: Policy-containment and symlink tests.
        """

        relative = Path(relative_text)
        if relative.is_absolute() or relative.parts != ("intake", expected_leaf):
            raise IntakeTransferError(500, "intake_policy_invalid", "The intake storage policy is not contained.")
        try:
            return self.intake_catalog.workspace_config.runtime_path(relative)
        except ValueError as exc:
            raise IntakeTransferError(500, "intake_policy_invalid", "The intake storage policy is not contained.") from exc

    @staticmethod
    def _valid_authorization(value: dict[str, Any]) -> bool:
        """Purpose: Validate the exact one-file authorization record shape.

        Inputs: Newly composed or decoded authorization mapping.
        Outputs: Boolean strict contract result without coercion.
        How it works: Checks field sets, ids, consent constants, timestamps, and source values.
        Side effects: None.
        Failure behavior: Unexpected types return false rather than gaining authority.
        Safety: Prevents local record editing from widening consent or changing scope.
        Example: Adding an arbitrary path field makes the record invalid.
        Related proof: Weakened authorization tests and JSON schema validation.
        """

        source = value.get("source", {})
        auth_id = value.get("id")
        intake_id = value.get("intakeId")
        return (
            set(value) == AUTHORIZATION_FIELDS
            and value.get("schemaVersion") == "makers-anvil.runtime.intake-authorization.v1"
            and isinstance(auth_id, str)
            and auth_id.startswith("intake-auth-")
            and len(auth_id) == 44
            and all(character in "0123456789abcdef" for character in auth_id.removeprefix("intake-auth-"))
            and isinstance(intake_id, str)
            and intake_id.startswith("intake-")
            and len(intake_id) == 39
            and all(character in "0123456789abcdef" for character in intake_id.removeprefix("intake-"))
            and value.get("claimState") == "staged"
            and value.get("scope") == TRANSFER_SCOPE
            and isinstance(value.get("createdUtc"), str)
            and isinstance(value.get("expiresUtc"), str)
            and value.get("accepted") is True
            and isinstance(value.get("acceptedUtc"), str)
            and isinstance(value.get("consumed"), bool)
            and ((value.get("consumed") is False and value.get("consumedUtc") is None) or (value.get("consumed") is True and isinstance(value.get("consumedUtc"), str)))
            and isinstance(source, dict)
            and set(source) == SOURCE_FIELDS
            and isinstance(source.get("displayName"), str)
            and isinstance(source.get("extension"), str)
            and isinstance(source.get("kind"), str)
            and isinstance(source.get("sizeBytes"), int)
            and not isinstance(source.get("sizeBytes"), bool)
            and source.get("sizeBytes", 0) > 0
            and isinstance(source.get("modifiedUtc"), str)
        )

    @staticmethod
    def _public_authorization(authorization: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Return only browser-needed authorization fields.

        Inputs: Strict internal authorization mapping.
        Outputs: Path-free id, intake id, scope, expiry, consumption, and source metadata.
        How it works: Copies an explicit allowlist rather than returning mutable storage data.
        Side effects: None.
        Failure behavior: Missing expected fields raise and prevent a misleading response.
        Safety: Request token and filesystem locations are never part of the record.
        Example: Frontend reads ``authorization.id`` to build the fixed content endpoint.
        Related proof: API response privacy tests.
        """

        return {
            "id": authorization["id"],
            "intakeId": authorization["intakeId"],
            "scope": authorization["scope"],
            "expiresUtc": authorization["expiresUtc"],
            "accepted": authorization["accepted"],
            "consumed": authorization["consumed"],
            "source": dict(authorization["source"]),
        }

    @staticmethod
    def _parse_timestamp(value: Any, field_name: str) -> datetime:
        """Purpose: Parse one timezone-aware ISO timestamp into UTC.

        Inputs: Untrusted value and stable field label for diagnostics.
        Outputs: Aware UTC ``datetime``.
        How it works: Accepts ISO ``Z`` or offset text and rejects naive/non-string values.
        Side effects: None.
        Failure behavior: Malformed values raise a path-free 400 transfer error.
        Safety: Authorization expiry cannot depend on local timezone guessing.
        Example: ``2026-06-29T12:00:00Z`` normalizes to a UTC-aware value.
        Related proof: Timestamp validation and expiry tests.
        """

        if not isinstance(value, str):
            raise IntakeTransferError(400, "timestamp_invalid", f"{field_name} must be a timezone-aware ISO timestamp.")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise IntakeTransferError(400, "timestamp_invalid", f"{field_name} must be a timezone-aware ISO timestamp.") from exc
        if parsed.tzinfo is None:
            raise IntakeTransferError(400, "timestamp_invalid", f"{field_name} must be a timezone-aware ISO timestamp.")
        return parsed.astimezone(UTC)

    def _utc_now(self) -> datetime:
        """Purpose: Normalize the injected clock to timezone-aware UTC.

        Inputs: Constructor-provided clock callable.
        Outputs: Aware UTC datetime used by expiry and audit fields.
        How it works: Calls once and rejects naive clocks before normalization.
        Side effects: Reads current time only.
        Failure behavior: Naive or invalid clock results raise programming errors.
        Safety: Consistent UTC comparisons prevent accidental authorization extension.
        Example: Tests inject a fixed UTC lambda for deterministic expiry.
        Related proof: Deterministic authorization and expiry tests.
        """

        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise IntakeTransferError(500, "clock_invalid", "The intake authorization clock is invalid.")
        return value.astimezone(UTC)


__all__ = ["AuthorizedIntakeService", "IntakeRequestContext", "IntakeTransferError"]
