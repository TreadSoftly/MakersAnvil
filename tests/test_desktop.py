"""Purpose: Prove the native desktop lifecycle without requiring a GUI in CI.

Used by: Developers, CI, and Windows package verification.
Inputs: Fake pywebview module plus real ephemeral loopback app sessions.
Outputs: Assertions for window configuration, health, cleanup, and smoke mode.
Side effects: Opens only short-lived local sockets during tests.
Safety: No real window, browser, tool, file dialog, or external process opens.
Failure behavior: Lifecycle leaks or weakened native-window settings fail tests.
Related proof: ``desktop.py`` and the packaged executable ``--smoke`` mode.
"""

import json
from types import SimpleNamespace
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from makers_anvil_backend import desktop


class FakeWebview(SimpleNamespace):
    """Purpose: Record native-window calls while exercising the real local server.

    Inputs: No constructor arguments; tests call ``create_window`` and ``start``.
    Outputs: Captured keyword dictionaries and a successful health observation.
    How it works: Stores calls and probes the URL when the fake GUI loop starts.
    Side effects: Performs one GET against the test-owned loopback session.
    Failure behavior: Missing URL/health or unexpected arguments fail assertions.
    Safety: Creates no OS window and exposes no JavaScript bridge.
    Example: ``run_desktop(FakeWebview())`` proves native configuration headlessly.
    Related proof: ``test_desktop_window_owns_server_and_cleans_up``.
    """

    def __init__(self) -> None:
        """Purpose: Initialize empty settings and call-capture containers.

        Inputs: No caller values.
        Outputs: Ready fake object.
        How it works: Calls ``SimpleNamespace`` then assigns deterministic fields.
        Side effects: None outside this in-memory test object.
        Failure behavior: Standard Python construction errors propagate.
        Safety: Contains no native handle or process behavior.
        Example: A fresh instance has no window URL until launch begins.
        Related proof: Desktop lifecycle test inspects these fields.
        """

        super().__init__()
        self.settings: dict[str, object] = {}
        self.window: dict[str, object] = {}
        self.start_options: dict[str, object] = {}
        self.health: dict[str, object] = {}

    def create_window(self, title: str, url: str, **kwargs: object) -> object:
        """Purpose: Capture the requested native window without displaying it.

        Inputs: Window title, loopback URL, and pywebview options.
        Outputs: Opaque object matching the unused real return contract.
        How it works: Saves all inputs for later assertions.
        Side effects: Mutates only this fake object's capture dictionary.
        Failure behavior: Missing required arguments raise through Python binding.
        Safety: Does not navigate or create an operating-system window.
        Example: Captures a minimum width of 960 and dark startup background.
        Related proof: The desktop lifecycle test asserts exact values.
        """

        self.window = {"title": title, "url": url, **kwargs}
        return object()

    def start(self, **kwargs: object) -> None:
        """Purpose: Simulate the GUI loop while proving the local app is reachable.

        Inputs: Security and renderer options supplied by ``run_desktop``.
        Outputs: ``None`` after reading and saving health JSON.
        How it works: Requests the captured loopback health endpoint synchronously.
        Side effects: Performs one GET to the owned in-process server.
        Failure behavior: Missing URL, failed request, or invalid JSON fails test.
        Safety: Makes no external request and starts no GUI.
        Example: Health proves the server is alive before fake window closure.
        Related proof: The lifecycle test verifies the server is closed afterward.
        """

        self.start_options = kwargs
        with urlopen(f"{self.window['url']}/api/health", timeout=5) as response:  # noqa: S310
            self.health = json.loads(response.read().decode("utf-8"))


def test_desktop_window_owns_server_and_cleans_up() -> None:
    """Purpose: Native launch uses secure options and releases its ephemeral port.

    Inputs: Fake pywebview module and the real bounded local app server.
    Outputs: Assertions for URL, dimensions, settings, health, and shutdown.
    How it works: Runs the complete desktop function through fake GUI closure.
    Side effects: Opens and closes one loopback socket.
    Failure behavior: A leaked server remains reachable and fails the final probe.
    Safety: No direct JS bridge, download, file URL, or remote debugger is enabled.
    Example: Models a user opening and closing ``MakersAnvil.exe`` normally.
    Related proof: Windows executable smoke repeats resource/server proof.
    """

    fake = FakeWebview()

    assert desktop.run_desktop(fake) == 0
    assert fake.window["title"] == "Makers Anvil"
    assert str(fake.window["url"]).startswith("http://127.0.0.1:")
    assert fake.window["min_size"] == (960, 640)
    assert fake.start_options["private_mode"] is True
    assert fake.settings["ALLOW_DOWNLOADS"] is False
    assert fake.settings["ALLOW_FILE_URLS"] is False
    assert fake.settings["REMOTE_DEBUGGING_PORT"] is None
    assert fake.health["mutatingActionsEnabled"] is True
    assert fake.health["enabledMutationScopes"] == ["authorized-file-intake"]
    assert fake.health["routeExecutionEnabled"] is False
    with pytest.raises(URLError):
        urlopen(str(fake.window["url"]), timeout=1)  # noqa: S310 - closed loopback URL


def test_package_smoke_proves_bundled_core(capsys: pytest.CaptureFixture[str]) -> None:
    """Purpose: Headless executable mode proves resources/API without a GUI.

    Inputs: Current source resources and captured stdout.
    Outputs: Zero exit plus staged JSON containing the current API build.
    How it works: Invokes the same smoke function packaged into the executable.
    Side effects: Opens and closes one short-lived loopback socket.
    Failure behavior: Resource, HTTP, marker, or safety mismatch returns nonzero.
    Safety: Opens no native window and triggers no mutation.
    Example: Windows CI runs ``MakersAnvil.exe --smoke`` after freezing.
    Related proof: Package workflow executes this behavior from binary form.
    """

    assert desktop.run_package_smoke() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["passed"] is True
    assert result["mutatingActionsEnabled"] is True
    assert result["enabledMutationScopes"] == ["authorized-file-intake"]
    assert result["routeExecutionEnabled"] is False
    assert result["apiBuild"].startswith("makers-anvil-real-pass-")
    assert result["currentPass"] == "PASS-018"
    assert result["realAppCompletion"] == 42.5


def test_package_smoke_handles_windowed_stdout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Purpose: Windowed executable smoke succeeds without a console stream.

    Inputs: Monkeypatched ``sys.stdout`` matching PyInstaller windowed runtime.
    Outputs: Zero exit code after the same bundled-core checks pass.
    How it works: Removes stdout, runs smoke, and relies on its exit status.
    Side effects: Opens and closes one short-lived loopback socket.
    Failure behavior: An unconditional print raises and fails this regression.
    Safety: No native window, intake mutation, tool, or external process opens.
    Example: The production ``--windowed`` executable follows this exact branch.
    Related proof: Relocated ``MakersAnvil.exe --smoke`` package verification.
    """

    monkeypatch.setattr(desktop.sys, "stdout", None)
    monkeypatch.setattr(desktop.sys, "stderr", None)

    assert desktop.run_package_smoke() == 0


def test_cli_dispatches_only_explicit_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    """Purpose: CLI mode selection accepts no paths, URLs, or commands.

    Inputs: Monkeypatched launch functions and explicit argument lists.
    Outputs: Assertions that empty args launch desktop and ``--smoke`` probes.
    How it works: Replaces effects with distinct return codes before parsing.
    Side effects: Mutates test-local module attributes through pytest cleanup.
    Failure behavior: Wrong dispatch or broadened parsing fails assertions.
    Safety: No server or window opens in this unit test.
    Example: ``main([])`` and ``main(["--smoke"])`` choose separate branches.
    Related proof: ``desktop.main`` owns packaged entrypoint parsing.
    """

    monkeypatch.setattr(desktop, "run_desktop", lambda: 7)
    monkeypatch.setattr(desktop, "run_package_smoke", lambda: 9)

    assert desktop.main([]) == 7
    assert desktop.main(["--smoke"]) == 9
