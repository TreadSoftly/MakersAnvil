# Desktop And Packaging Architecture

## Selected Architecture

Makers Anvil keeps one Python core and one frontend. Desktop mode starts the same bounded local HTTP application on a kernel-selected loopback port, opens that URL in a native pywebview window, and shuts the server down when the final window closes. Browser development mode uses the same server, assets, process-token intake contract, and app-owned data policy.

Windows packaging uses PyInstaller one-file mode. The frontend is bundled as read-only data and resolved from PyInstaller's runtime extraction directory rather than a checkout path. Runtime settings, intake records, jobs, logs, and outputs continue to use the operating system's per-user application-data location and are never written into bundled resources.

## Why This Path

- pywebview directly supports native windows around web content and requires backend work to run outside its blocking GUI loop. Its current API supports explicit window size, private mode, storage control, and renderer selection: <https://pywebview.idepy.com/en/guide/api>.
- pywebview's current freezing guidance recommends PyInstaller for Windows/Linux and warns that unused GUI dependencies can increase bundles: <https://pywebview.idepy.com/en/guide/freezing>.
- PyInstaller documents one-file executables and `--add-data` resource bundling; one-file data expands into a temporary `_MEI...` directory at runtime: <https://pyinstaller.org/en/stable/usage.html> and <https://pyinstaller.org/en/latest/spec-files.html>.
- Windows' native EdgeChromium path depends on the WebView2 Runtime. Microsoft recommends checking/installing Evergreen during setup and notes Windows 11 includes it while some Windows 10 systems may not: <https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution>.

## Why Not Tauri Yet

Tauri remains a possible later shell if the core is rewritten in Rust. Today it would require a Rust toolchain plus a separately frozen Python sidecar for every target architecture. Tauri's own sidecar documentation requires platform/architecture-specific binary names and permissions: <https://v2.tauri.app/develop/sidecar/>. That adds a second process contract and cross-platform packaging matrix without removing the Python core, so it is not the minimal reliable Windows-first route.

## Desktop Security Boundary

- Bind only `127.0.0.1`, `localhost`, or another literal loopback address; wildcard/LAN/public binds fail.
- Use port zero so the operating system selects an available private port.
- Expose no direct Python-to-JavaScript bridge in the initial shell.
- Disable downloads, file URLs, automatic devtools, and remote debugging in desktop mode.
- Permit only the two authorized intake POST routes; retain blocked behavior for every other non-GET route.
- Keep file choice in the webview/browser picker rather than exposing a direct Python-to-JavaScript filesystem bridge.
- Stop and close the owned server when the native window exits.
- Accept no desktop CLI path, URL, command, tool, authorization, or launch argument.

## Windows Artifact Flow

1. Install the pinned build dependencies in an isolated build environment.
2. Run `python scripts/build_windows_exe.py --check` to inspect the plan.
3. Run `python scripts/build_windows_exe.py` on Windows.
4. Run `artifacts/windows/MakersAnvil.exe --smoke` to prove bundled assets and health without opening a GUI.
5. Open the executable and inspect the native window on a real Windows desktop.
6. Upload an ephemeral CI artifact for tester access.
7. Later, add icon/version metadata, code signing, an installer, WebView2 prerequisite detection, upgrade/uninstall behavior, and clean-machine proof before publishing a release.

## Current Non-Claims

An executable that launches and passes smoke is not yet a signed release, installer, automatic updater, clean-machine proof, or macOS/Linux bundle. Each platform must build on that platform and receive its own runtime, packaging, signing, installation, update, removal, and clean-machine evidence.
