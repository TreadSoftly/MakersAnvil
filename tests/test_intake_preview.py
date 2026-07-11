"""Purpose: Prove read-only raster previews preserve intake containment and integrity.

Used by: Developers and CI whenever preview policy, transport, or frontend URLs change.
Inputs: Isolated authorized image records, app-owned bytes, API calls, and loopback HTTP.
Outputs: Assertions for policy, media responses, digest/signature checks, and closed failures.
Side effects: Writes pytest-owned config/intake fixtures and opens one short-lived loopback socket.
Safety: Tests never inspect a user path, launch a process, or serve active/non-raster content.
Failure behavior: Any path leak, tamper acceptance, type widening, or transport drift fails CI.
Related proof: ``services/intake_preview.py`` and the intake-preview policy schema.
"""

from __future__ import annotations

import json
import hashlib
import shutil
import threading
from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from makers_anvil_backend.api.app import MakersAnvilApi
from makers_anvil_backend.server import create_server
from makers_anvil_backend.services.app_state import AppStateService
from makers_anvil_backend.services.intake_preview import IntakePreviewError, IntakePreviewService
from test_authorized_intake import build_transfer, valid_context
from test_server import make_bundle


ROOT = Path(__file__).resolve().parents[1]
PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"makers-anvil-preview"


def build_preview(tmp_path: Path) -> tuple[IntakePreviewService, str, Path]:
    """Purpose: Create one valid authorized PNG and a preview service over isolated storage.

    Inputs: Pytest temporary directory.
    Outputs: Preview service, generated intake id, and private content path.
    How it works: Reuses guarded intake, copies preview policy, authorizes metadata, and ingests bytes.
    Side effects: Writes only pytest-owned policy, authorization, record, and content files.
    Failure behavior: Unexpected intake or fixture failures propagate and fail the calling test.
    Safety: The helper uses generated app-owned storage and never consults real user data.
    Example: ``preview, intake_id, path = build_preview(tmp_path)``.
    Related proof: Authorized-intake tests prove the shared transfer boundary.
    """

    transfer, _data_root = build_transfer(tmp_path)
    source_root = tmp_path / "portable-source"
    shutil.copy2(ROOT / "config" / "intake_preview_policy.json", source_root / "config" / "intake_preview_policy.json")
    authorization = transfer.authorize(
        {
            "displayName": "reference.png",
            "sizeBytes": len(PNG_BYTES),
            "modifiedUtc": "2026-06-29T11:30:00Z",
        },
        valid_context(),
    )["authorization"]
    record = transfer.ingest(authorization["id"], BytesIO(PNG_BYTES), len(PNG_BYTES), valid_context())["record"]
    service = IntakePreviewService(transfer.intake_catalog, root=source_root)
    content_path = transfer.intake_catalog.authorized_content_path(record)
    return service, record["id"], content_path


def test_preview_revalidates_and_returns_only_generated_raster_metadata(tmp_path: Path) -> None:
    """Purpose: Prove a valid authorized PNG becomes one path-free verified preview.

    Inputs: Isolated valid PNG fixture.
    Outputs: Assertions for exact bytes, media type, generated name, digest, and policy safety.
    How it works: Calls policy and preview through the focused service.
    Side effects: Reads pytest-owned fixture files after helper creation.
    Failure behavior: Any incorrect response metadata or missing safety proof fails.
    Safety: No original filename or physical path appears in the preview value or policy.
    Example: The returned filename is ``preview.png``, never ``reference.png``.
    Related proof: API and HTTP tests below use the same service value.
    """

    service, intake_id, _content_path = build_preview(tmp_path)
    policy = service.policy_response()
    preview = service.preview(intake_id)

    assert policy["mode"] == "verified-app-owned-raster"
    assert policy["safety"]["sizeAndDigestReverified"] is True
    assert preview.content == PNG_BYTES
    assert preview.content_type == "image/png"
    assert preview.generated_name == "preview.png"
    assert preview.intake_id == intake_id
    assert "reference" not in preview.generated_name


def test_preview_rejects_tampering_invalid_ids_and_non_raster_signatures(tmp_path: Path) -> None:
    """Purpose: Prove changed bytes and untrusted identifiers fail without fallback serving.

    Inputs: Valid fixture followed by controlled content tampering and invalid ids.
    Outputs: Typed status/code assertions for integrity, missing record, and signature failures.
    How it works: Mutates only pytest content, then invokes the same strict read path.
    Side effects: Replaces bytes inside the temporary app-owned fixture.
    Failure behavior: Acceptance of any altered or path-shaped request fails the test.
    Safety: No traversal, suffix trust, or stale intake digest can expose bytes.
    Example: ``../../secret`` returns preview-not-found rather than probing a path.
    Related proof: Intake catalog containment and server no-sniff headers.
    """

    service, intake_id, content_path = build_preview(tmp_path)
    content_path.write_bytes(b"not-a-png" + b" " * (len(PNG_BYTES) - 9))
    with pytest.raises(IntakePreviewError) as integrity:
        service.preview(intake_id)
    assert integrity.value.code == "preview_integrity_failed"

    with pytest.raises(IntakePreviewError) as missing:
        service.preview("../../secret")
    assert missing.value.status == 404
    assert missing.value.code == "preview_not_found"

    content_path.write_bytes(b"X" * len(PNG_BYTES))
    record_path = service.intake_catalog._record_path(intake_id, service.intake_catalog.policy())
    record = json.loads(record_path.read_text(encoding="utf-8"))
    record["storage"]["sha256"] = hashlib.sha256(content_path.read_bytes()).hexdigest()
    record_path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(IntakePreviewError) as signature:
        service.preview(intake_id)
    assert signature.value.code == "preview_signature_invalid"


def test_api_returns_binary_preview_and_path_free_errors(tmp_path: Path) -> None:
    """Purpose: Prove dynamic API dispatch returns binary media and stable JSON rejections.

    Inputs: Isolated preview service injected into current application state and API facade.
    Outputs: Assertions for policy JSON, binary headers/body, ETag, and invalid-id response.
    How it works: Calls exact GET routes without starting a network server.
    Side effects: Reads pytest-owned fixture files only.
    Failure behavior: JSON encoding of image bytes or path-bearing diagnostics fails assertions.
    Safety: Content disposition uses a generated name and all responses remain read-only.
    Example: ``GET /api/intake/previews/<id>`` returns ``image/png``.
    Related proof: The following test proves equivalent loopback transport.
    """

    preview_service, intake_id, _content_path = build_preview(tmp_path)
    state = AppStateService(
        intake_catalog=preview_service.intake_catalog,
        intake_preview=preview_service,
    )
    api = MakersAnvilApi(state)

    policy = api.handle("GET", "/api/intake/previews/policy")
    response = api.handle("GET", f"/api/intake/previews/{intake_id}")
    rejected = api.handle("GET", "/api/intake/previews/not-an-id")

    assert policy.status == 200
    assert policy.body["maxPreviewBytes"] == 26_214_400
    assert response.status == 200
    assert response.body == PNG_BYTES
    assert response.headers["Content-Type"] == "image/png"
    assert response.headers["Content-Disposition"] == 'inline; filename="preview.png"'
    assert response.headers["ETag"].startswith('"sha256-')
    assert rejected.status == 404
    assert rejected.body["error"] == "preview_not_found"
    assert "path" not in rejected.body


def test_loopback_server_streams_preview_with_no_sniff_and_no_cache(tmp_path: Path) -> None:
    """Purpose: Prove verified preview bytes survive the actual loopback HTTP boundary.

    Inputs: Isolated preview API, minimal compiled static fixture, and ephemeral loopback port.
    Outputs: Assertions for body, media, no-store, no-sniff, same-origin, and closed invalid GET.
    How it works: Starts one owned server thread and performs two local requests before cleanup.
    Side effects: Opens one short-lived loopback socket and reads pytest-owned files.
    Failure behavior: Header, status, body, or cleanup regressions fail directly.
    Safety: The server binds port zero on loopback and returns no CORS permission.
    Example: Browser image decoding receives bytes only after all service checks pass.
    Related proof: General server ownership and desktop lifecycle tests.
    """

    preview_service, intake_id, _content_path = build_preview(tmp_path)
    api = MakersAnvilApi(AppStateService(intake_catalog=preview_service.intake_catalog, intake_preview=preview_service))
    make_bundle(tmp_path)
    server = create_server(port=0, static_root=tmp_path, api=api)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(f"{base}/api/intake/previews/{intake_id}", timeout=5) as response:  # noqa: S310 - owned loopback
            assert response.read() == PNG_BYTES
            assert response.headers["Content-Type"] == "image/png"
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Cross-Origin-Resource-Policy"] == "same-origin"
            assert response.headers.get("Access-Control-Allow-Origin") is None
        with pytest.raises(HTTPError) as rejected:
            urlopen(f"{base}/api/intake/previews/not-an-id", timeout=5)  # noqa: S310 - owned loopback
        assert rejected.value.code == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
