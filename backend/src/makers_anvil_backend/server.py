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
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from makers_anvil_backend.api.app import ApiResponse, MakersAnvilApi


ROOT = Path(__file__).resolve().parents[3]
STATIC_ROOT = ROOT / "frontend" / "public"


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

    api = MakersAnvilApi()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
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

        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

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

    server = ThreadingHTTPServer((host, port), MakersAnvilRequestHandler)
    print(f"Makers Anvil running at http://{host}:{port}")
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
