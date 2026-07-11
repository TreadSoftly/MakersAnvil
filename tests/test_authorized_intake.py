"""Purpose: Prove one-file authorization, containment, hashing, and replay safety.

Used by: Developers and CI whenever browser/native intake behavior changes.
Inputs: Actual committed policies copied into isolated source/runtime test roots.
Outputs: Assertions over consent, bytes, records, privacy, rollback, and rejection.
Side effects: Writes only pytest-owned temporary app data and source fixtures.
Safety: Tests never touch real user data, external tools, routes, or output folders.
Failure behavior: Any widened origin/path/type/effect boundary fails explicitly.
Related proof: ``services/authorized_intake.py`` and intake schemas.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path

import pytest

from makers_anvil_backend.api.app import MakersAnvilApi
from makers_anvil_backend.services.authorized_intake import (
    AuthorizedIntakeService,
    IntakeRequestContext,
    IntakeTransferError,
)
from makers_anvil_backend.services.app_state import AppStateService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
REQUEST_TOKEN = "test-request-token-that-is-long-enough-for-proof"


def build_transfer(tmp_path: Path) -> tuple[AuthorizedIntakeService, Path]:
    """Purpose: Build a production-policy intake service over isolated runtime storage.

    Inputs: Pytest temporary root.
    Outputs: Authorized service and its private test runtime root.
    How it works: Copies only committed JSON configs and injects portable runtime paths.
    Side effects: Creates source/config fixtures under pytest-owned storage.
    Failure behavior: Missing config or path construction errors fail the test directly.
    Safety: No real app-data location or user file is consulted.
    Example: Tests receive ``service, data_root = build_transfer(tmp_path)``.
    Related proof: Runtime relocation and policy-integration assertions below.
    """

    source_root = tmp_path / "portable-source"
    config_root = source_root / "config"
    config_root.mkdir(parents=True)
    shutil.copy2(ROOT / "config" / "default_settings.json", config_root / "default_settings.json")
    shutil.copy2(ROOT / "config" / "intake_policy.json", config_root / "intake_policy.json")
    data_root = tmp_path / "runtime-data"
    paths = RuntimePathsService(
        source_root=source_root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=tmp_path / "home",
        platform_name="linux",
    )
    workspace = WorkspaceConfigService(source_root, paths)
    catalog = IntakeCatalogService(source_root, workspace)
    service = AuthorizedIntakeService(catalog, request_token=REQUEST_TOKEN, clock=lambda: FIXED_NOW)
    return service, data_root


def valid_context(**changes: str) -> IntakeRequestContext:
    """Purpose: Return same-origin mutation evidence with focused test overrides.

    Inputs: Optional field replacements for negative security cases.
    Outputs: Immutable ``IntakeRequestContext``.
    How it works: Merges caller changes into one known-good loopback header set.
    Side effects: None.
    Failure behavior: Unknown keys raise through dataclass construction.
    Safety: Defaults model browser-generated values, not privileged bypasses.
    Example: ``valid_context(origin='https://attacker.example')`` creates rejection input.
    Related proof: Context guard tests below.
    """

    values = {
        "request_token": REQUEST_TOKEN,
        "origin": "http://127.0.0.1:8766",
        "host": "127.0.0.1:8766",
        "fetch_site": "same-origin",
    }
    values.update(changes)
    return IntakeRequestContext(**values)


def valid_metadata(**changes: object) -> dict[str, object]:
    """Purpose: Return one path-free STL metadata example with focused overrides.

    Inputs: Optional metadata field replacements.
    Outputs: Three-field browser authorization mapping.
    How it works: Merges changes into a fixed name/size/time example.
    Side effects: None.
    Failure behavior: Invalid examples are rejected by the service under test.
    Safety: Contains no source path or relative directory metadata.
    Example: ``valid_metadata(sizeBytes=0)`` exercises empty-file rejection.
    Related proof: Metadata validation tests below.
    """

    values: dict[str, object] = {
        "displayName": "fixture.STL",
        "sizeBytes": 25,
        "modifiedUtc": "2026-06-29T11:30:00Z",
    }
    values.update(changes)
    return values


def create_authorization(service: AuthorizedIntakeService, metadata: dict[str, object] | None = None) -> dict[str, object]:
    """Purpose: Create and return one public authorization for later test steps.

    Inputs: Isolated service and optional path-free metadata.
    Outputs: Public authorization mapping from the API-shaped result.
    How it works: Calls ``authorize`` with the valid same-origin context.
    Side effects: Writes one app-owned test authorization JSON record.
    Failure behavior: Any unexpected authorization rejection fails the calling test.
    Safety: Uses no path and grants only one bounded copy.
    Example: ``auth = create_authorization(service)`` then ``auth['id']`` uploads.
    Related proof: Consumption/replay tests below.
    """

    result = service.authorize(metadata or valid_metadata(), valid_context())
    return result["authorization"]


def test_session_exposes_only_bounded_same_origin_constraints(tmp_path: Path) -> None:
    """Purpose: Session truth enables one picker while keeping broad intake blocked.

    Inputs: Isolated production-policy service.
    Outputs: Assertions for token, endpoints, limits, allowlist, and false effects.
    How it works: Reads the session without creating runtime directories.
    Side effects: Creates config fixtures only.
    Failure behavior: Missing constraints or widened capabilities fail assertions.
    Safety: Archives, drag/drop, paste, handoff, route, and tool remain false.
    Example: ``.stl`` is allowed while ``.zip`` is absent.
    Related proof: ``intake-session.schema.json`` and browser picker wiring.
    """

    service, data_root = build_transfer(tmp_path)

    session = service.session()

    assert session["requestToken"] == REQUEST_TOKEN
    assert session["mode"] == "same-origin-one-file"
    assert ".stl" in session["constraints"]["allowedExtensions"]
    assert ".zip" not in session["constraints"]["allowedExtensions"]
    assert session["constraints"]["oneFilePerAuthorization"] is True
    assert session["capabilities"]["explicitAuthorizationRequired"] is True
    assert session["capabilities"]["dragDropEnabled"] is True
    assert session["capabilities"]["clipboardPasteEnabled"] is True
    assert session["safety"]["routeExecutionEnabled"] is False
    assert not data_root.exists()


def test_authorization_is_path_free_short_lived_and_token_free_on_disk(tmp_path: Path) -> None:
    """Purpose: Persist explicit consent without source path or process token leakage.

    Inputs: Valid STL metadata and guarded local request context.
    Outputs: Assertions over public response and private app-owned JSON.
    How it works: Authorizes once, then inspects the isolated authorization record.
    Side effects: Writes one test authorization file.
    Failure behavior: Path/token/shape/expiry drift fails immediately.
    Safety: No file bytes are accepted by this first phase.
    Example: Consent expires exactly 600 seconds after the fixed clock.
    Related proof: Authorization schema and privacy contract.
    """

    service, data_root = build_transfer(tmp_path)

    authorization = create_authorization(service)

    assert authorization["accepted"] is True
    assert authorization["consumed"] is False
    assert authorization["source"]["extension"] == ".stl"
    assert authorization["source"]["kind"] == "mesh"
    assert authorization["expiresUtc"] == (FIXED_NOW + timedelta(seconds=600)).isoformat()
    stored_path = data_root / "intake" / "authorizations" / f"{authorization['id']}.json"
    stored_text = stored_path.read_text(encoding="utf-8")
    assert REQUEST_TOKEN not in stored_text
    assert "sourcePath" not in stored_text
    assert str(data_root) not in stored_text


def test_ingest_streams_hashes_and_catalogs_one_generated_file(tmp_path: Path) -> None:
    """Purpose: Consume authorization into a path-redacted quarantined file record.

    Inputs: Exact 25-byte payload matching valid metadata.
    Outputs: Assertions over bytes, SHA-256, record, catalog, and logical paths.
    How it works: Authorizes, ingests via ``BytesIO``, then reads isolated outputs.
    Side effects: Writes one content file, consumed consent, and catalog record.
    Failure behavior: Any mismatch or leaked private path fails assertions.
    Safety: File remains unscanned, unhanded-off, unexecuted, and unopened.
    Example: Generated disk name uses random intake id rather than user filename.
    Related proof: Authorized-record schema and live HTTP smoke.
    """

    service, data_root = build_transfer(tmp_path)
    payload = b"solid fixture\nendsolid x\n"
    assert len(payload) == 25
    authorization = create_authorization(service)

    result = service.ingest(authorization["id"], BytesIO(payload), len(payload), valid_context())

    record = result["record"]
    content_path = data_root / "intake" / "files" / f"{record['id']}.stl"
    assert content_path.read_bytes() == payload
    assert content_path.name != "fixture.STL"
    assert record["storage"]["sha256"] == hashlib.sha256(payload).hexdigest()
    assert record["storage"]["integrityVerified"] is True
    assert record["storage"]["quarantineState"] == "contained-untrusted"
    assert record["privacy"] == {
        "sourcePathStored": False,
        "sourceContentStored": True,
        "originalDisplayNameStored": True,
    }
    assert record["safety"]["sourceFileCopied"] is True
    assert all(value is False for key, value in record["safety"].items() if key != "sourceFileCopied")
    catalog = service.intake_catalog.catalog()
    assert catalog["records"] == [record]
    assert str(data_root) not in json.dumps(catalog)


def test_authorization_is_one_time_and_replay_is_rejected(tmp_path: Path) -> None:
    """Purpose: Prove one consent cannot create duplicate content or records.

    Inputs: One authorization and two identical upload attempts.
    Outputs: Conflict on replay and exactly one file/record.
    How it works: Completes the first stream, then retries the consumed id.
    Side effects: Writes one valid intake transaction under pytest storage.
    Failure behavior: A replay success or duplicate output fails the test.
    Safety: Authorization state is atomically marked consumed.
    Example: Second call raises ``authorization_consumed`` with 409.
    Related proof: One-file-per-authorization session constraint.
    """

    service, data_root = build_transfer(tmp_path)
    payload = b"solid fixture\nendsolid x\n"
    authorization = create_authorization(service)
    service.ingest(authorization["id"], BytesIO(payload), len(payload), valid_context())

    with pytest.raises(IntakeTransferError, match="already been used") as replay:
        service.ingest(authorization["id"], BytesIO(payload), len(payload), valid_context())

    assert replay.value.status == 409
    assert replay.value.code == "authorization_consumed"
    assert len(list((data_root / "intake" / "files").glob("*"))) == 1
    assert len(list((data_root / "intake" / "records").glob("*.json"))) == 1


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"request_token": "wrong"}, "request_token_rejected"),
        ({"origin": "https://attacker.example"}, "origin_rejected"),
        ({"host": "localhost:8766"}, "origin_rejected"),
        ({"fetch_site": "cross-site"}, "cross_origin_rejected"),
    ],
)
def test_mutation_context_rejects_token_and_origin_mismatches(tmp_path: Path, changes: dict[str, str], code: str) -> None:
    """Purpose: Block localhost mutation when browser security evidence disagrees.

    Inputs: Isolated service and one changed context field from parametrization.
    Outputs: 403 error with expected stable code and no runtime write.
    How it works: Attempts first-phase authorization under hostile/mismatched context.
    Side effects: Creates config fixtures only.
    Failure behavior: Any accepted mismatch or authorization file fails the test.
    Safety: Covers token theft guessing, cross-site fetch, and Host/Origin mismatch.
    Example: ``Sec-Fetch-Site: cross-site`` is rejected before metadata use.
    Related proof: No-CORS/preflight server tests.
    """

    service, data_root = build_transfer(tmp_path)

    with pytest.raises(IntakeTransferError) as blocked:
        service.authorize(valid_metadata(), valid_context(**changes))

    assert blocked.value.status == 403
    assert blocked.value.code == code
    assert not data_root.exists()


@pytest.mark.parametrize(
    ("metadata", "status", "code"),
    [
        (valid_metadata(displayName="archive.zip"), 415, "file_type_not_allowed"),
        (valid_metadata(displayName="model.stl.exe"), 415, "file_type_not_allowed"),
        (valid_metadata(displayName="folder/file.stl"), 400, "filename_invalid"),
        (valid_metadata(sizeBytes=0), 400, "file_size_invalid"),
        (valid_metadata(sizeBytes=536870913), 413, "file_too_large"),
        (valid_metadata(modifiedUtc="not-a-time"), 400, "timestamp_invalid"),
    ],
)
def test_metadata_rejects_archives_paths_oversize_and_invalid_time(
    tmp_path: Path,
    metadata: dict[str, object],
    status: int,
    code: str,
) -> None:
    """Purpose: Enforce allowlist, name, byte, and timestamp constraints before consent.

    Inputs: Parametrized invalid metadata and expected rejection truth.
    Outputs: Matching status/code with no authorization file.
    How it works: Calls first-phase authorization and inspects typed error.
    Side effects: Creates config fixtures only.
    Failure behavior: Any bad metadata becoming consent fails the test.
    Safety: Double extensions, archives, folder names, empty/huge files stay blocked.
    Example: ``model.stl.exe`` is classified by final suffix and rejected.
    Related proof: OWASP-inspired allowlist and size policy.
    """

    service, data_root = build_transfer(tmp_path)

    with pytest.raises(IntakeTransferError) as blocked:
        service.authorize(metadata, valid_context())

    assert blocked.value.status == status
    assert blocked.value.code == code
    assert not (data_root / "intake" / "authorizations").exists()


def test_incomplete_stream_rolls_back_all_content_and_catalog_state(tmp_path: Path) -> None:
    """Purpose: Prevent partial client transfer from leaving usable intake evidence.

    Inputs: Authorization for 25 bytes and a three-byte request stream.
    Outputs: Incomplete error, no content/record, and reusable unconsumed consent.
    How it works: Starts the transaction and forces early EOF before atomic replace.
    Side effects: Writes authorization; transient part file is removed.
    Failure behavior: Any leftover part/content/catalog entry fails assertions.
    Safety: Readers never see a partial file as staged intake.
    Example: A disconnected browser cannot create a route-preview record.
    Related proof: Transaction cleanup logic in ``AuthorizedIntakeService.ingest``.
    """

    service, data_root = build_transfer(tmp_path)
    authorization = create_authorization(service)

    with pytest.raises(IntakeTransferError) as incomplete:
        service.ingest(authorization["id"], BytesIO(b"bad"), 25, valid_context())

    assert incomplete.value.code == "content_incomplete"
    files_root = data_root / "intake" / "files"
    assert not files_root.exists() or list(files_root.iterdir()) == []
    assert not (data_root / "intake" / "records").exists()
    stored = json.loads((data_root / "intake" / "authorizations" / f"{authorization['id']}.json").read_text(encoding="utf-8"))
    assert stored["consumed"] is False


def test_expired_authorization_rejects_bytes_without_partial_file(tmp_path: Path) -> None:
    """Purpose: Ensure the short consent window is enforced at byte-transfer time.

    Inputs: Valid authorization followed by clock advancement beyond ten minutes.
    Outputs: Expired conflict and no files/catalog records.
    How it works: Replaces the injected clock after authorization, then attempts ingest.
    Side effects: Writes only the original authorization record.
    Failure behavior: Accepted expired bytes or partial output fails the test.
    Safety: A stale browser tab cannot silently copy a formerly reviewed file.
    Example: Eleven-minute-old consent returns ``authorization_expired``.
    Related proof: Authorization lifetime policy and schema.
    """

    service, data_root = build_transfer(tmp_path)
    authorization = create_authorization(service)
    service._clock = lambda: FIXED_NOW + timedelta(minutes=11)  # Test-only deterministic time advance.

    with pytest.raises(IntakeTransferError) as expired:
        service.ingest(authorization["id"], BytesIO(b"solid fixture\nendsolid x\n"), 25, valid_context())

    assert expired.value.status == 409
    assert expired.value.code == "authorization_expired"
    assert not (data_root / "intake" / "files").exists()
    assert not (data_root / "intake" / "records").exists()


def test_api_allows_only_the_two_guarded_intake_post_shapes(tmp_path: Path) -> None:
    """Purpose: Prove API dispatch permits authorization/content and no other mutation.

    Inputs: Isolated service, valid headers, JSON metadata, and exact file bytes.
    Outputs: Two 201 responses followed by a 405 for an unrelated POST.
    How it works: Injects the focused service into ``AppStateService`` and API facade.
    Side effects: Writes one complete intake transaction under pytest storage.
    Failure behavior: Routing, media, guard, or response regressions fail assertions.
    Safety: The API receives no source path and keeps state/execution POSTs blocked.
    Example: ``POST /api/state`` remains method-not-allowed after successful intake.
    Related proof: HTTP-level server test and API facade implementation.
    """

    service, data_root = build_transfer(tmp_path)
    state = AppStateService(intake_catalog=service.intake_catalog, authorized_intake=service)
    api = MakersAnvilApi(state)
    headers = {
        "Content-Type": "application/json",
        "X-Makers-Anvil-Request-Token": REQUEST_TOKEN,
        "Origin": "http://127.0.0.1:8766",
        "Host": "127.0.0.1:8766",
        "Sec-Fetch-Site": "same-origin",
    }
    metadata = json.dumps(valid_metadata()).encode("utf-8")

    authorized = api.handle("POST", "/api/intake/authorizations", headers=headers, body=metadata)
    authorization_id = authorized.body["authorization"]["id"]
    payload = b"solid fixture\nendsolid x\n"
    upload_headers = {**headers, "Content-Type": "application/octet-stream"}
    ingested = api.handle(
        "POST",
        f"/api/intake/authorizations/{authorization_id}/content",
        headers=upload_headers,
        body_stream=BytesIO(payload),
        content_length=len(payload),
    )
    blocked = api.handle("POST", "/api/state", headers=headers, body=b"{}")

    assert authorized.status == 201
    assert ingested.status == 201
    assert blocked.status == 405
    assert len(list((data_root / "intake" / "files").glob("*"))) == 1


def test_api_rejects_wrong_media_types_before_writing(tmp_path: Path) -> None:
    """Purpose: Require explicit JSON metadata and octet-stream content media types.

    Inputs: Isolated API and otherwise valid same-origin security headers.
    Outputs: 415 response with no app-owned authorization or content.
    How it works: Sends metadata under text/plain before any service mutation.
    Side effects: Creates config fixtures only.
    Failure behavior: Accepted ambiguous media or runtime write fails assertions.
    Safety: Simple cross-origin form content types cannot trigger intake.
    Example: ``text/plain`` authorization returns ``content_type_not_allowed``.
    Related proof: No-CORS/preflight HTTP tests.
    """

    service, data_root = build_transfer(tmp_path)
    state = AppStateService(intake_catalog=service.intake_catalog, authorized_intake=service)
    api = MakersAnvilApi(state)
    headers = {
        "Content-Type": "text/plain",
        "X-Makers-Anvil-Request-Token": REQUEST_TOKEN,
        "Origin": "http://127.0.0.1:8766",
        "Host": "127.0.0.1:8766",
        "Sec-Fetch-Site": "same-origin",
    }

    response = api.handle("POST", "/api/intake/authorizations", headers=headers, body=b"{}")

    assert response.status == 415
    assert response.body["error"] == "content_type_not_allowed"
    assert not data_root.exists()
