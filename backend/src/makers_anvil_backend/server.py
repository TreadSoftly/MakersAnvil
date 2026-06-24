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
    """Serve static UI files and the read-only API on loopback."""

    api = MakersAnvilApi()

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Bind the standard handler to the repository's static dashboard root."""

        super().__init__(*args, directory=str(STATIC_ROOT), **kwargs)

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        """Serve an API response or a static dashboard asset for one GET request."""

        if self.path.startswith("/api/"):
            self._send_api(self.api.handle("GET", self.path))
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        """Send the API's standard blocked response for a POST request."""

        self._send_api(self.api.handle("POST", self.path))

    def do_PUT(self) -> None:  # noqa: N802 - stdlib handler API
        """Send the API's standard blocked response for a PUT request."""

        self._send_api(self.api.handle("PUT", self.path))

    def do_DELETE(self) -> None:  # noqa: N802 - stdlib handler API
        """Send the API's standard blocked response for a DELETE request."""

        self._send_api(self.api.handle("DELETE", self.path))

    def _send_api(self, response: ApiResponse) -> None:
        """Serialize one API result with explicit JSON, cache, and length headers."""

        payload = json.dumps(response.body, indent=2).encode("utf-8")
        self.send_response(response.status)
        for key, value in response.headers.items():
            self.send_header(key, value)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the local server until interrupted."""

    server = ThreadingHTTPServer((host, port), MakersAnvilRequestHandler)
    print(f"Makers Anvil running at http://{host}:{port}")
    server.serve_forever()


def main() -> int:
    """Parse host and port arguments, then run the loopback development server."""

    parser = argparse.ArgumentParser(description="Run the Makers Anvil local app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()
    run(args.host, args.port)
    return 0
