"""Purpose: Run Makers Anvil as one native desktop window over its local core.

Used by: ``scripts/run_desktop.py`` and the packaged Windows executable.
Inputs: The bundled frontend, read-only API, loopback socket, and pywebview runtime.
Outputs: A native app window or a machine-readable package smoke result.
Side effects: Opens one ephemeral loopback server and, normally, one native window.
Safety: Uses no JavaScript bridge, remote URL, fixed port, or enabled API mutation.
Failure behavior: Missing desktop dependencies or startup failures remain explicit.
Related proof: ``tests/test_desktop.py`` and Windows executable smoke verification.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from dataclasses import dataclass
from http.server import ThreadingHTTPServer
from types import ModuleType
from typing import Sequence
from urllib.request import urlopen

from makers_anvil_backend.server import create_server


class DesktopDependencyError(RuntimeError):
    """Purpose: Explain that the optional native-window dependency is unavailable.

    Inputs: A human-readable dependency/setup diagnostic.
    Outputs: A typed startup error for CLI handling and tests.
    How it works: Uses standard ``RuntimeError`` behavior without hidden fallback.
    Side effects: None until raised.
    Failure behavior: Keeps the original import failure as its exception cause.
    Safety: Never falls back to opening an external browser as fake desktop proof.
    Example: Missing pywebview raises this error with the exact optional setup command.
    Related proof: ``tests/test_desktop.py`` verifies the fail-closed path.
    """


@dataclass
class DesktopServerSession:
    """Purpose: Own the ephemeral loopback server and its background thread.

    Inputs: A bound ``ThreadingHTTPServer`` and its running daemon thread.
    Outputs: The session URL plus an idempotent shutdown operation.
    How it works: Derives the URL from the kernel-selected bound server port.
    Side effects: ``stop`` shuts down and closes only this owned server socket.
    Failure behavior: Server/thread errors remain visible to the invoking launcher.
    Safety: Ownership prevents abandoned fixed-port background processes.
    Example: ``session.stop()`` releases the port after the native window closes.
    Related proof: ``tests/test_desktop.py`` starts, probes, and stops a session.
    """

    server: ThreadingHTTPServer
    thread: threading.Thread

    @property
    def url(self) -> str:
        """Purpose: Return the private URL loaded by the native window.

        Inputs: The bound server address stored in this session.
        Outputs: A loopback HTTP URL with the kernel-selected port.
        How it works: Reads ``server_address`` after socket binding succeeds.
        Side effects: None.
        Failure behavior: Invalid server state raises rather than inventing a URL.
        Safety: Hard-codes the display host to IPv4 loopback, never a LAN address.
        Example: A bound port can produce ``http://127.0.0.1:54321``.
        Related proof: ``tests/test_desktop.py`` asserts loopback URL structure.
        """

        return f"http://127.0.0.1:{self.server.server_address[1]}"

    def stop(self) -> None:
        """Purpose: Stop the owned HTTP loop and release its listening socket.

        Inputs: This session's server and thread.
        Outputs: ``None`` after shutdown and a bounded thread join.
        How it works: Requests server shutdown, closes the socket, then joins.
        Side effects: Stops only the server created for this desktop session.
        Failure behavior: Unexpected shutdown errors propagate to the launcher.
        Safety: Does not signal unrelated processes or scan arbitrary ports.
        Example: The desktop launcher calls ``stop`` in ``finally`` on every exit.
        Related proof: ``tests/test_desktop.py`` proves the URL stops responding.
        """

        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def start_desktop_server() -> DesktopServerSession:
    """Purpose: Start the app core on an available ephemeral loopback port.

    Inputs: The validated server factory and bundled frontend resources.
    Outputs: An owned ``DesktopServerSession`` ready for a native window.
    How it works: Binds port zero, then serves requests on one daemon thread.
    Side effects: Opens one loopback socket and starts one in-process thread.
    Failure behavior: Binding, resource, or thread-start errors propagate.
    Safety: No fixed port, remote bind, subprocess, or external browser is used.
    Example: ``session = start_desktop_server(); urlopen(session.url)``.
    Related proof: ``tests/test_desktop.py`` probes health through the session.
    """

    server = create_server(host="127.0.0.1", port=0)
    thread = threading.Thread(target=server.serve_forever, name="makers-anvil-http", daemon=True)
    thread.start()
    return DesktopServerSession(server=server, thread=thread)


def load_webview() -> ModuleType:
    """Purpose: Import the optional native-window runtime only when requested.

    Inputs: The active Python environment's installed packages.
    Outputs: Imported ``webview`` module implementing create/start APIs.
    How it works: Defers import so server/package smoke remains dependency-light.
    Side effects: Imports pywebview; it does not create a window on import.
    Failure behavior: Wraps import failure in ``DesktopDependencyError``.
    Safety: Never downloads, installs, or substitutes a browser automatically.
    Example: Development setup uses ``pip install -e .[desktop]`` before launch.
    Related proof: ``tests/test_desktop.py`` injects a fake module and tests failure.
    """

    try:
        import webview
    except ImportError as exc:
        raise DesktopDependencyError(
            "Desktop runtime is not installed. Install the pinned desktop dependencies before launching."
        ) from exc
    return webview


def run_desktop(webview_module: ModuleType | None = None) -> int:
    """Purpose: Display the real app in a native window and cleanly own its server.

    Inputs: Optional injected pywebview-compatible module for deterministic tests.
    Outputs: Exit code zero after the final native window closes normally.
    How it works: Starts loopback, configures a bounded window, enters GUI loop.
    Side effects: Opens one native window and one in-process loopback listener.
    Failure behavior: Dependency/window/server errors propagate after cleanup.
    Safety: Downloads, file URLs, remote debugging, and a direct JS API are disabled.
    Example: ``python scripts/run_desktop.py`` opens the Windows Makers Anvil window.
    Related proof: ``tests/test_desktop.py`` verifies arguments and guaranteed cleanup.
    """

    webview = webview_module or load_webview()
    session = start_desktop_server()
    try:
        webview.settings["ALLOW_DOWNLOADS"] = False
        webview.settings["ALLOW_FILE_URLS"] = False
        webview.settings["OPEN_DEVTOOLS_IN_DEBUG"] = False
        webview.settings["REMOTE_DEBUGGING_PORT"] = None
        webview.create_window(
            "Makers Anvil",
            session.url,
            width=1366,
            height=860,
            min_size=(960, 640),
            resizable=True,
            background_color="#080a0b",
            text_select=True,
        )
        start_options = {"debug": False, "private_mode": True}
        if sys.platform == "win32":
            start_options["gui"] = "edgechromium"
        webview.start(**start_options)
    finally:
        session.stop()
    return 0


def run_package_smoke() -> int:
    """Purpose: Prove a source or packaged binary can serve its bundled core.

    Inputs: Bundled static resources and the in-process read-only health endpoint.
    Outputs: JSON result on stdout and zero only for the expected build marker.
    How it works: Starts an ephemeral session, requests health, validates, stops.
    Side effects: Opens one short-lived loopback socket; no native window appears.
    Failure behavior: HTTP, JSON, marker, and resource failures return nonzero.
    Safety: Executes no mutation, tool, selected file, installer, or external process.
    Example: ``MakersAnvil.exe --smoke`` validates a CI-built executable headlessly.
    Related proof: Windows CI package job and ``tests/test_desktop.py``.
    """

    session = start_desktop_server()
    try:
        with urlopen(f"{session.url}/api/health", timeout=5) as health_response:  # noqa: S310 - fixed loopback URL
            payload = json.loads(health_response.read().decode("utf-8"))
        with urlopen(f"{session.url}/api/state", timeout=10) as state_response:  # noqa: S310 - fixed loopback URL
            state = json.loads(state_response.read().decode("utf-8"))
        passed = (
            health_response.status == 200
            and state_response.status == 200
            and payload.get("apiBuild", "").startswith("makers-anvil-real-pass-")
            and state.get("currentPass", {}).get("id") == "PASS-017"
            and state.get("completion", {}).get("realApp") == 37.5
        )
        result = {
            "schemaVersion": "makers-anvil.desktop-smoke.v1",
            "claimState": "proven" if passed else "failed",
            "passed": passed,
            "apiBuild": payload.get("apiBuild", "missing"),
            "currentPass": state.get("currentPass", {}).get("id", "missing"),
            "realAppCompletion": state.get("completion", {}).get("realApp"),
            "mutatingActionsEnabled": payload.get("mutatingActionsEnabled"),
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if passed and payload.get("mutatingActionsEnabled") is False else 1
    finally:
        session.stop()


def main(argv: Sequence[str] | None = None) -> int:
    """Purpose: Select native interactive launch or headless package smoke mode.

    Inputs: Optional CLI argument sequence; normal execution reads ``sys.argv``.
    Outputs: Process exit code from the selected bounded mode.
    How it works: ``argparse`` recognizes only the explicit ``--smoke`` switch.
    Side effects: Delegates to one documented launch mode after parsing.
    Failure behavior: Unknown arguments fail through argparse with nonzero status.
    Safety: No argument accepts paths, commands, URLs, tools, or authorization.
    Example: ``main(["--smoke"])`` verifies resources without opening a window.
    Related proof: ``tests/test_desktop.py`` covers both dispatch branches.
    """

    parser = argparse.ArgumentParser(description="Run the Makers Anvil desktop application.")
    parser.add_argument("--smoke", action="store_true", help="Verify bundled resources without opening a window.")
    args = parser.parse_args(argv)
    return run_package_smoke() if args.smoke else run_desktop()
