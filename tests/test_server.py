"""Purpose: Prove loopback ownership and injectable static server behavior.

Used by: Developers and CI before browser or desktop runtime proof.
Inputs: Temporary static bundles, local sockets, and the bounded local API facade.
Outputs: Assertions for host rejection, static serving, health, and mutation block.
Side effects: Opens short-lived loopback sockets and temporary files only.
Safety: Tests never bind a LAN interface or mutate application/user state.
Failure behavior: Exposure, routing, or shutdown regressions fail explicitly.
Related proof: ``server.py`` and ``tests/test_desktop.py``.
"""

import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from makers_anvil_backend.server import create_server, require_loopback_host
from makers_anvil_backend.api.app import MakersAnvilApi
from makers_anvil_backend.services.app_state import AppStateService
from test_authorized_intake import build_transfer, valid_metadata


def make_bundle(root: Path) -> None:
    """Purpose: Create one complete static bundle root for server tests.

    Inputs: Pytest temporary directory.
    Outputs: ``None`` after writing a minimal index document.
    How it works: Reproduces the packaged ``frontend/public`` layout.
    Side effects: Writes only inside pytest-owned storage.
    Failure behavior: Filesystem failures propagate.
    Safety: Fixture HTML contains no script, remote URL, or user data.
    Example: ``create_server(static_root=tmp_path)`` can then serve the fixture.
    Related proof: The following server test uses this exact layout.
    """

    public = root / "frontend" / "public"
    public.mkdir(parents=True)
    (public / "index.html").write_text("<!doctype html><title>fixture</title>", encoding="utf-8")


def test_only_loopback_hosts_are_accepted() -> None:
    """Purpose: Prevent development or desktop APIs from binding to a network.

    Inputs: Loopback, wildcard, LAN, public, and invalid host examples.
    Outputs: Accepted loopbacks and ``ValueError`` for every other example.
    How it works: Exercises hostname and ``ipaddress`` validation branches.
    Side effects: Opens no socket.
    Failure behavior: Any remotely reachable example passing fails the test.
    Safety: This is the pre-socket network exposure boundary.
    Example: ``127.0.0.1`` passes while ``0.0.0.0`` is rejected.
    Related proof: ``server.require_loopback_host`` owns this invariant.
    """

    assert require_loopback_host("127.0.0.1") == "127.0.0.1"
    assert require_loopback_host("::1") == "::1"
    assert require_loopback_host("localhost") == "localhost"
    for host in ("0.0.0.0", "192.168.1.4", "8.8.8.8", "makers-anvil.example"):
        with pytest.raises(ValueError, match="only binds to loopback"):
            require_loopback_host(host)


def test_owned_server_serves_static_health_and_blocked_post(tmp_path: Path) -> None:
    """Purpose: One injectable server instance serves UI/API and blocks mutation.

    Inputs: Temporary bundle, ephemeral port, and three loopback requests.
    Outputs: Static HTML, proven health JSON, and blocked POST status.
    How it works: Starts ``serve_forever`` on a daemon thread and closes in finally.
    Side effects: Opens one short-lived loopback socket and reads a fixture file.
    Failure behavior: HTTP/status/content mismatches fail before deterministic cleanup.
    Safety: Uses port zero, local requests, and no application mutation.
    Example: This is the same ownership model used by the native desktop session.
    Related proof: ``tests/test_desktop.py`` proves the higher-level lifecycle.
    """

    make_bundle(tmp_path)
    server = create_server(port=0, static_root=tmp_path)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(base, timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            assert "fixture" in response.read().decode("utf-8")
            assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers.get("Access-Control-Allow-Origin") is None
        with urlopen(f"{base}/api/health", timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            health = json.loads(response.read().decode("utf-8"))
        assert health["claimState"] == "proven"
        request = Request(f"{base}/api/state", data=b"{}", method="POST")
        with pytest.raises(HTTPError) as blocked:
            urlopen(request, timeout=5)  # noqa: S310 - test-owned loopback URL
        assert blocked.value.code == 405
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_http_intake_uses_one_shared_token_and_rejects_preflight(tmp_path: Path) -> None:
    """Purpose: Prove a real loopback server completes the two-step intake contract.

    Inputs: Temporary frontend, injected runtime service, and urllib HTTP requests.
    Outputs: Session, authorization, content result, catalog bytes, and blocked OPTIONS.
    How it works: Starts one server, reads its stable token, then posts metadata and bytes.
    Side effects: Opens one local socket and writes one pytest-owned intake transaction.
    Failure behavior: Token churn, routing, header, stream, or CORS regression fails.
    Safety: Uses no source path; preflight receives no cross-origin permission.
    Example: Mirrors browser fetch over a kernel-selected loopback port.
    Related proof: Browser live intake and packaged executable smoke.
    """

    make_bundle(tmp_path)
    transfer, data_root = build_transfer(tmp_path)
    state = AppStateService(intake_catalog=transfer.intake_catalog, authorized_intake=transfer)
    server = create_server(port=0, static_root=tmp_path, api=MakersAnvilApi(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urlopen(f"{base}/api/intake/session", timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            session = json.loads(response.read().decode("utf-8"))
        common_headers = {
            "X-Makers-Anvil-Request-Token": session["requestToken"],
            "Origin": base,
            "Sec-Fetch-Site": "same-origin",
        }
        payload = b"solid fixture\nfacet normal 0 0 0\nouter loop\nendloop\nendfacet\nendsolid fixture\n"
        metadata = json.dumps(valid_metadata(sizeBytes=len(payload))).encode("utf-8")
        authorize_request = Request(
            f"{base}/api/intake/authorizations",
            data=metadata,
            method="POST",
            headers={**common_headers, "Content-Type": "application/json"},
        )
        with urlopen(authorize_request, timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            assert response.status == 201
            authorization = json.loads(response.read().decode("utf-8"))["authorization"]
        content_request = Request(
            f"{base}/api/intake/authorizations/{authorization['id']}/content",
            data=payload,
            method="POST",
            headers={**common_headers, "Content-Type": "application/octet-stream"},
        )
        with urlopen(content_request, timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            assert response.status == 201
            result = json.loads(response.read().decode("utf-8"))
        assert result["record"]["storage"]["sizeBytes"] == len(payload)
        assert len(list((data_root / "intake" / "files").glob("*"))) == 1
        execution_authorization = json.dumps(
            {
                "intakeId": result["record"]["id"],
                "routeId": "mesh-to-toolpath",
                "operationId": "built-in-stl-preflight",
                "accepted": True,
            }
        ).encode("utf-8")
        authorize_execution_request = Request(
            f"{base}/api/executions/authorizations",
            data=execution_authorization,
            method="POST",
            headers={**common_headers, "Content-Type": "application/json"},
        )
        with urlopen(authorize_execution_request, timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            assert response.status == 201
            execution = json.loads(response.read().decode("utf-8"))["record"]
        run_request = Request(
            f"{base}/api/executions/{execution['id']}/run",
            data=None,
            method="POST",
            headers=common_headers,
        )
        with urlopen(run_request, timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            assert response.status == 200
            completed = json.loads(response.read().decode("utf-8"))
        assert completed["record"]["lifecycle"]["state"] == "completed"
        assert completed["record"]["proof"]["outcome"] == "passed"
        assert completed["record"]["proof"]["fullRouteCompleted"] is False
        assert completed["record"]["proof"]["toolpathGenerated"] is False
        assert completed["audit"]["summary"]["eventCount"] == 5
        with urlopen(f"{base}/api/executions/catalog", timeout=5) as response:  # noqa: S310 - test-owned loopback URL
            execution_catalog = json.loads(response.read().decode("utf-8"))
        assert execution_catalog["summary"]["completedCount"] == 1
        assert execution_catalog["summary"]["proofCount"] == 1
        assert str(data_root) not in json.dumps(execution_catalog)
        options = Request(
            f"{base}/api/intake/authorizations",
            method="OPTIONS",
            headers={"Origin": "https://attacker.example"},
        )
        with pytest.raises(HTTPError) as preflight:
            urlopen(options, timeout=5)  # noqa: S310 - test-owned loopback URL
        assert preflight.value.code == 405
        assert preflight.value.headers.get("Access-Control-Allow-Origin") is None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
