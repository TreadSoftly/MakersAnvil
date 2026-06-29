"""Purpose: Prove loopback ownership and injectable static server behavior.

Used by: Developers and CI before browser or desktop runtime proof.
Inputs: Temporary static bundles, local sockets, and the read-only API facade.
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
