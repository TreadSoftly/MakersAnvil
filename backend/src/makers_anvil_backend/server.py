"""Purpose: Serve the static dashboard and read-only API on loopback.

Used by: ``scripts/run_dev.py`` and ``python -m makers_anvil_backend``.
Inputs: Host/port settings, HTTP requests, and checked-in frontend assets.
Outputs: Static responses or JSON responses delegated to ``MakersAnvilApi``.
Side effects: Opens a loopback listening socket while the process is running.
Safety: Static paths are contained and all mutating API methods stay blocked.
Failure behavior: Missing assets return 404; startup and socket errors surface.
Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from makers_anvil_backend.api.app import ApiResponse, MakersAnvilApi
from makers_anvil_backend.runtime_resources import frontend_root


DEFAULT_STATIC_ROOT = frontend_root()


class MakersAnvilRequestHandler(SimpleHTTPRequestHandler):
    """Purpose: Serve static UI files and the read-only API on loopback.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``MakersAnvilRequestHandler`` exposing the state and operations defined below.
    How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Static paths are contained and all mutating API methods stay blocked.
    Example: Construct with ``instance = MakersAnvilRequestHandler(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
    """

    def __init__(
        self,
        *args: Any,
        api: MakersAnvilApi | None = None,
        static_root: Path | None = None,
        **kwargs: Any,
    ) -> None:
        """Purpose: Bind the standard handler to the repository's static dashboard root.

        Inputs: Caller-supplied ``*args``, ``**kwargs`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        self.api = api or MakersAnvilApi()
        super().__init__(*args, directory=str(static_root or DEFAULT_STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        """Purpose: Serve an API response or a static dashboard asset for one GET request.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Call ``result = instance.do_GET(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        if self.path.startswith("/api/"):
            self._send_api(self.api.handle("GET", self.path))
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        """Purpose: Send the API's standard blocked response for a POST request.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Call ``result = instance.do_POST(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        self._send_api(self.api.handle("POST", self.path))

    def do_PUT(self) -> None:  # noqa: N802 - stdlib handler API
        """Purpose: Send the API's standard blocked response for a PUT request.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Call ``result = instance.do_PUT(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        self._send_api(self.api.handle("PUT", self.path))

    def do_DELETE(self) -> None:  # noqa: N802 - stdlib handler API
        """Purpose: Send the API's standard blocked response for a DELETE request.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Call ``result = instance.do_DELETE(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        self._send_api(self.api.handle("DELETE", self.path))

    def _send_api(self, response: ApiResponse) -> None:
        """Purpose: Serialize one API result with explicit JSON, cache, and length headers.

        Inputs: Caller-supplied ``response`` values from the signature.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It iterates over bounded records.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Static paths are contained and all mutating API methods stay blocked.
        Example: Call ``result = instance._send_api(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
        """

        payload = json.dumps(response.body, indent=2).encode("utf-8")
        self.send_response(response.status)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def require_loopback_host(host: str) -> str:
    """Purpose: Reject any server bind that could expose the local API remotely.

    Inputs: Hostname or IP text supplied by a development/desktop caller.
    Outputs: The unchanged host only when it identifies a loopback interface.
    How it works: Accepts localhost or asks ``ipaddress`` for loopback truth.
    Side effects: None; no socket is opened by validation.
    Failure behavior: Invalid, wildcard, LAN, and public hosts raise ``ValueError``.
    Safety: Prevents accidental ``0.0.0.0`` or network exposure in every mode.
    Example: ``require_loopback_host("127.0.0.1")`` passes; ``0.0.0.0`` fails.
    Related proof: ``tests/test_server.py`` covers accepted and rejected hosts.
    """

    normalized = host.strip().lower()
    if normalized == "localhost":
        return host
    try:
        address = ipaddress.ip_address(normalized)
    except ValueError as exc:
        raise ValueError(f"Makers Anvil only binds to loopback hosts, not {host!r}") from exc
    if not address.is_loopback:
        raise ValueError(f"Makers Anvil only binds to loopback hosts, not {host!r}")
    return host


def create_server(
    host: str = "127.0.0.1",
    port: int = 8765,
    *,
    api: MakersAnvilApi | None = None,
    static_root: Path | None = None,
) -> ThreadingHTTPServer:
    """Purpose: Construct one loopback HTTP server for browser or desktop ownership.

    Inputs: Loopback host, port including zero, optional API, and static test root.
    Outputs: Bound ``ThreadingHTTPServer`` that has not started serving yet.
    How it works: Validates host/port and binds a handler with explicit dependencies.
    Side effects: Reserves one local listening socket until the server is closed.
    Failure behavior: Invalid input, missing resources, or socket errors propagate.
    Safety: Remote hosts are rejected and static files stay under a validated root.
    Example: Desktop mode uses port zero, then owns serving and shutdown itself.
    Related proof: ``tests/test_server.py`` and ``tests/test_desktop.py``.
    """

    require_loopback_host(host)
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    resolved_static_root = frontend_root(static_root) if static_root else DEFAULT_STATIC_ROOT
    handler = partial(MakersAnvilRequestHandler, api=api, static_root=resolved_static_root)
    return ThreadingHTTPServer((host, port), handler)


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Purpose: Run the local server until interrupted.

    Inputs: Caller-supplied ``host``, ``port`` values from the signature.
    Outputs: Returns ``None``, or raises before returning when validation fails.
    How it works: It executes the focused statements in source order.
    Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Static paths are contained and all mutating API methods stay blocked.
    Example: Call ``result = instance.run(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
    """

    with create_server(host, port) as server:
        print(f"Makers Anvil running at http://{host}:{server.server_address[1]}")
        server.serve_forever()


def main() -> int:
    """Purpose: Parse host and port arguments, then run the loopback development server.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``int``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: Performs only the bounded filesystem/process effect stated in the purpose and guarded by the surrounding validation.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Static paths are contained and all mutating API methods stay blocked.
    Example: Call ``result = main(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_api.py`` and runtime/browser smoke tests.
    """

    parser = argparse.ArgumentParser(description="Run the Makers Anvil local app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run(args.host, args.port)
    return 0
