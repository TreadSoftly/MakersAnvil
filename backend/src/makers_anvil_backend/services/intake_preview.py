"""Purpose: Serve verified raster previews from authorized app-owned intake copies.

Used by: The local API's read-only dynamic intake-preview route.
Inputs: Generated intake ids, strict preview policy, authorized records, and quarantined bytes.
Outputs: Immutable in-memory preview payloads with fixed raster media types.
Side effects: Reads one policy, one record, and one app-owned content file only.
Safety: Rechecks containment, size, SHA-256, extension, and raster signature every request.
Failure behavior: Missing, altered, oversized, active, or unsupported content fails closed.
Related proof: ``tests/test_intake_preview.py`` and HTTP server preview tests.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService


ROOT = application_root()
CONTENT_TYPES = {
    ".bmp": "image/bmp",
    ".gif": "image/gif",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


class IntakePreviewError(ValueError):
    """Purpose: Carry stable status and code data for a rejected preview read.

    Inputs: HTTP status, machine-readable code, and path-free user message.
    Outputs: Exception with ``status`` and ``code`` attributes.
    How it works: Stores bounded metadata before initializing ``ValueError``.
    Side effects: None.
    Failure behavior: The original safe diagnostic remains available to the API facade.
    Safety: Callers must never include physical paths, file bytes, or private identifiers.
    Example: Unsupported content raises status 415 with ``preview_type_not_allowed``.
    Related proof: Preview service and API rejection tests.
    """

    def __init__(self, status: int, code: str, message: str) -> None:
        """Purpose: Initialize one typed preview rejection.

        Inputs: Numeric HTTP status, stable code, and reviewed message.
        Outputs: Initialized exception; constructors return ``None``.
        How it works: Saves status/code and delegates message storage to ``ValueError``.
        Side effects: None.
        Failure behavior: Invalid constructor values remain visible programming errors.
        Safety: The exception contains no path or payload data.
        Example: ``IntakePreviewError(404, 'preview_not_found', 'Preview unavailable.')``.
        Related proof: API error mapping tests.
        """

        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class IntakePreview:
    """Purpose: Hold one fully verified raster response before transport encoding.

    Inputs: Exact bytes, fixed media type, generated filename, digest, and intake id.
    Outputs: Immutable value consumed by the API facade and HTTP server.
    How it works: Dataclass construction binds already-verified response fields.
    Side effects: None.
    Failure behavior: Invalid values remain caller programming errors.
    Safety: The value contains no original name or physical path.
    Example: A PNG produces ``preview.png`` and ``image/png``.
    Related proof: Preview service success tests.
    """

    content: bytes
    content_type: str
    generated_name: str
    sha256: str
    intake_id: str


class IntakePreviewService:
    """Purpose: Revalidate and read one authorized raster without exposing storage paths.

    Inputs: Preview policy plus the existing strict authorized intake catalog.
    Outputs: Verified ``IntakePreview`` values or typed closed failures.
    How it works: Validates policy/record, resolves private content, bounds read, hashes, and checks magic.
    Side effects: Reads app-owned files only and never writes or launches anything.
    Failure behavior: Every missing or weakened invariant raises ``IntakePreviewError``.
    Safety: Metadata-only records, SVG/active content, archives, symlinks, and tampering are denied.
    Example: ``preview('intake-<hex>')`` returns bytes only for a valid authorized PNG.
    Related proof: ``tests/test_intake_preview.py``.
    """

    def __init__(
        self,
        intake_catalog: IntakeCatalogService | None = None,
        *,
        root: Path | None = None,
    ) -> None:
        """Purpose: Bind the preview policy to the same catalog used by intake and execution.

        Inputs: Optional injected catalog and application root for isolated tests.
        Outputs: Initialized read-only preview service.
        How it works: Reuses the catalog root when supplied and records one policy path.
        Side effects: None during construction.
        Failure behavior: Missing policy is reported when preview work is requested.
        Safety: No alternate content root or browser-controlled path is accepted.
        Example: Tests inject a catalog backed by a temporary app-data directory.
        Related proof: Preview fixture isolation tests.
        """

        self.intake_catalog = intake_catalog or IntakeCatalogService(root=root or ROOT)
        self.root = root or self.intake_catalog.root
        self.policy_path = self.root / "config" / "intake_preview_policy.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load and minimally revalidate the strict committed preview policy.

        Inputs: The configured policy JSON file.
        Outputs: Defensive policy mapping used by preview reads and API status.
        How it works: Parses JSON and checks identity, bounds, extensions, and exact safety truth.
        Side effects: Reads one committed JSON file.
        Failure behavior: Missing, malformed, or weakened policy raises a closed server error.
        Safety: Runtime policy cannot silently widen active content or external effects.
        Example: A policy enabling source-path exposure is rejected before file lookup.
        Related proof: Policy schema and weakened-policy tests.
        """

        try:
            policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise IntakePreviewError(500, "preview_policy_invalid", "The intake preview policy is unavailable.") from exc
        expected_safety = {
            "readOnly": True,
            "authorizedRecordRequired": True,
            "appOwnedContentRequired": True,
            "sizeAndDigestReverified": True,
            "rasterSignatureRequired": True,
            "sourcePathExposed": False,
            "activeContentAllowed": False,
            "archiveReadEnabled": False,
            "selectedFileHandoffEnabled": False,
            "externalProcessEnabled": False,
        }
        extensions = policy.get("allowedExtensions")
        if (
            policy.get("schemaVersion") != "makers-anvil.config.intake-preview.v1"
            or policy.get("mode") != "verified-app-owned-raster"
            or policy.get("endpointTemplate") != "/api/intake/previews/{intakeId}"
            or not isinstance(policy.get("maxPreviewBytes"), int)
            or not 0 < policy["maxPreviewBytes"] <= 26_214_400
            or not isinstance(extensions, list)
            or not extensions
            or len(extensions) != len(set(extensions))
            or any(extension not in CONTENT_TYPES for extension in extensions)
            or policy.get("safety") != expected_safety
        ):
            raise IntakePreviewError(500, "preview_policy_invalid", "The intake preview policy is invalid.")
        return json.loads(json.dumps(policy))

    def policy_response(self) -> dict[str, Any]:
        """Purpose: Expose path-free preview capability and safety truth to the workbench.

        Inputs: Valid committed preview policy.
        Outputs: JSON-safe policy mapping with no physical storage details.
        How it works: Returns a defensive policy copy unchanged because it contains only public rules.
        Side effects: Reads one committed JSON file.
        Failure behavior: Invalid policy propagates as a closed preview error.
        Safety: No request token, source name, path, content, or mutable command is included.
        Example: ``GET /api/intake/previews/policy`` can explain the size limit.
        Related proof: API policy route and schema tests.
        """

        return self.policy()

    def preview(self, intake_id: str) -> IntakePreview:
        """Purpose: Return one digest- and signature-verified app-owned raster payload.

        Inputs: Generated authorized intake id from a current catalog record.
        Outputs: Immutable preview bytes and fixed response metadata.
        How it works: Loads strict record/path, enforces size/type, reads once, hashes, and checks signature.
        Side effects: Reads one record and one bounded app-owned content file.
        Failure behavior: Invalid id, missing file, drift, unsupported type, or signature mismatch fails closed.
        Safety: Original names/paths and non-raster or active content never reach the response.
        Example: A valid authorized JPEG returns ``image/jpeg`` and ``preview.jpg``.
        Related proof: Service, API, and HTTP preview tests.
        """

        policy = self.policy()
        try:
            record = self.intake_catalog.authorized_record(intake_id)
            content_path = self.intake_catalog.authorized_content_path(record)
        except IntakeCatalogError as exc:
            raise IntakePreviewError(404, "preview_not_found", "No authorized image preview is available.") from exc
        source = record["source"]
        storage = record["storage"]
        extension = source["extension"]
        if source["kind"] != "image" or extension not in policy["allowedExtensions"]:
            raise IntakePreviewError(415, "preview_type_not_allowed", "Only authorized raster images can be previewed.")
        size = storage["sizeBytes"]
        if size <= 0 or size > policy["maxPreviewBytes"]:
            raise IntakePreviewError(413, "preview_too_large", "This image exceeds the safe preview size limit.")
        try:
            content = content_path.read_bytes()
        except OSError as exc:
            raise IntakePreviewError(404, "preview_not_found", "The authorized image preview is unavailable.") from exc
        digest = hashlib.sha256(content).hexdigest()
        if len(content) != size or not hmac.compare_digest(digest, storage["sha256"]):
            raise IntakePreviewError(422, "preview_integrity_failed", "The authorized image no longer matches its intake proof.")
        if not self._signature_matches(extension, content):
            raise IntakePreviewError(415, "preview_signature_invalid", "The file signature does not match an allowed raster image.")
        return IntakePreview(content, CONTENT_TYPES[extension], f"preview{extension}", digest, intake_id)

    @staticmethod
    def _signature_matches(extension: str, content: bytes) -> bool:
        """Purpose: Match one allowed suffix to a conservative raster file signature.

        Inputs: Normalized extension and already bounded complete file bytes.
        Outputs: ``True`` only for the expected PNG/JPEG/GIF/WebP/BMP/TIFF signature.
        How it works: Uses fixed binary prefixes plus WebP's RIFF form; JPEG also requires its end marker.
        Side effects: None.
        Failure behavior: Short or unknown content returns ``False`` instead of guessing.
        Safety: SVG, HTML, scripts, polyglot text, and unsupported formats are never accepted by suffix alone.
        Example: PNG begins with the eight-byte ``89 50 4E 47 0D 0A 1A 0A`` signature.
        Related proof: Parameterized signature tests cover every accepted extension and mismatches.
        """

        if extension == ".png":
            return content.startswith(b"\x89PNG\r\n\x1a\n")
        if extension in {".jpg", ".jpeg"}:
            return len(content) >= 4 and content.startswith(b"\xff\xd8\xff") and content.endswith(b"\xff\xd9")
        if extension == ".gif":
            return content.startswith((b"GIF87a", b"GIF89a"))
        if extension == ".webp":
            return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
        if extension == ".bmp":
            return content.startswith(b"BM")
        if extension in {".tif", ".tiff"}:
            return content.startswith((b"II*\x00", b"MM\x00*"))
        return False


__all__ = ["IntakePreview", "IntakePreviewError", "IntakePreviewService"]
