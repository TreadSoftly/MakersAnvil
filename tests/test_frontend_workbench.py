"""Purpose: Prove the promoted React workbench and its portable adapter boundaries.

Used by: Developers and CI whenever the accepted previous-app experience changes.
Inputs: Checked-in React, TypeScript, CSS, HTML, and Vite configuration source.
Outputs: Assertions for navigation, workflows, intake gestures, safety, and motion.
Side effects: Reads product source only and never starts a browser or server.
Safety: Guarded one-file intake is allowed while private paths and legacy actions stay absent.
Failure behavior: Missing experience features or weakened adapter boundaries fail CI.
Related proof: Frontend Vitest, runtime resource tests, and browser/native smoke checks.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "frontend" / "src" / "App.tsx"
API_PATH = ROOT / "frontend" / "src" / "api.ts"
CSS_PATH = ROOT / "frontend" / "src" / "styles.css"
HTML_PATH = ROOT / "frontend" / "index.html"
VITE_PATH = ROOT / "frontend" / "vite.config.ts"


def test_promoted_workbench_keeps_the_accepted_navigation_and_workflow_surfaces() -> None:
    """Purpose: Preserve the prior app's recognizable rail, tools, workflow, plans, proof, and settings surfaces.

    Inputs: The checked-in React application source.
    Outputs: No value; passing assertions prove the named visible surfaces remain implemented.
    How it works: Reads source and checks stable user-facing labels and component composition.
    Side effects: Reads one text file only.
    Failure behavior: A removed surface or accidental replacement fails at its expected label.
    Safety: Structural inspection cannot perform an application action.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k promoted_workbench``.
    Related proof: ``frontend/src/App.test.tsx`` exercises these surfaces in jsdom.
    """

    app = APP_PATH.read_text(encoding="utf-8")
    for label in ("Workbench", "Intake", "Plans", "Tools", "Files", "Components", "Simulation", "Outputs", "Settings"):
        assert f'label: "{label}"' in app
    for component in ("CommandSearch", "DropZone", "MediaBoard", "ToolDock", "ModeTabs", "ContextInspector"):
        assert component in app
    assert 'label: "Work Flow"' in app
    assert 'label: "Dev"' in app


def test_drop_picker_and_paste_share_one_guarded_file_adapter() -> None:
    """Purpose: Prove picker, drop, and paste gestures converge on the same one-file authorization function.

    Inputs: React event wiring and the TypeScript API adapter.
    Outputs: No value; assertions prove accepted gestures without legacy multipart upload.
    How it works: Checks event handlers, one-file validation, token use, and two-step endpoints.
    Side effects: Reads two text files only.
    Failure behavior: Missing gestures, widened selection, or bypassed authorization fails the test.
    Safety: Archives, folders, source paths, and arbitrary multipart endpoints remain absent.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k drop_picker``.
    Related proof: Vitest drop and paste tests inspect the actual browser events.
    """

    app = APP_PATH.read_text(encoding="utf-8")
    api = API_PATH.read_text(encoding="utf-8")
    assert "onDrop=" in app
    assert 'addEventListener("paste"' in app
    assert "uploadFiles(selectedFiles)" in app
    assert "selected.length !== 1" in api
    assert 'jsonFetch<JsonRecord>("/api/intake/session")' in api
    assert '"X-Makers-Anvil-Request-Token"' in api
    assert "/api/files/upload" not in api


def test_legacy_machine_specific_actions_remain_visibly_blocked() -> None:
    """Purpose: Prevent the promoted interface from restoring unsafe prior backend endpoints.

    Inputs: The portable TypeScript API adapter.
    Outputs: No value; assertions prove explicit blockers and absence of retired endpoints.
    How it works: Searches adapter source for reviewed blocker messages and forbidden URLs.
    Side effects: Reads one text file only.
    Failure behavior: A missing blocker or legacy endpoint string fails immediately.
    Safety: This gate protects private paths, process launch, native handoff, and folder opening.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k machine_specific``.
    Related proof: Vitest expects each attempted legacy action to show its blocker.
    """

    api = API_PATH.read_text(encoding="utf-8")
    for retired in ("/api/tools/open", "/api/tools/open-output", "/api/intake/open-folder", "/api/open", "/api/jobs/run"):
        assert retired not in api
    assert "Tool launch is blocked" in api
    assert "Native output handoff is blocked" in api
    assert "Intake storage is private app-owned data" in api
    assert "private path not exposed" in api


def test_styles_retain_motion_responsive_layout_and_reduced_motion() -> None:
    """Purpose: Preserve the accepted visual character while keeping desktop/mobile geometry usable.

    Inputs: The promoted stylesheet.
    Outputs: No value; assertions prove responsive and motion primitives remain present.
    How it works: Checks stable selectors, media queries, animations, overflow, and reduced motion.
    Side effects: Reads one text file only.
    Failure behavior: Removing a required visual or accessibility contract fails the test.
    Safety: CSS inspection cannot change files, data, tools, or routes.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k styles_retain``.
    Related proof: Browser screenshots verify the compiled visual result.
    """

    styles = CSS_PATH.read_text(encoding="utf-8")
    assert ".desktop-shell" in styles
    assert ".app-rail" in styles
    assert ".tool-carousel" in styles
    assert "@keyframes" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert "@media (max-width:" in styles
    assert "overflow" in styles


def test_vite_build_has_one_minimal_document_root_and_compiled_output() -> None:
    """Purpose: Prove the React source compiles into the portable runtime resource directory.

    Inputs: The Vite configuration and root HTML document.
    Outputs: No value; assertions prove one mount point and ``dist`` output.
    How it works: Checks the explicit build directory, loopback proxy, and root/module tags.
    Side effects: Reads two text files only.
    Failure behavior: A changed output root, remote proxy, or duplicate mount fails CI.
    Safety: The trusted document contains no inline privileged behavior or remote dependency.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k vite_build``.
    Related proof: ``npm run build`` and Python runtime-resource tests inspect the result.
    """

    vite = VITE_PATH.read_text(encoding="utf-8")
    html = HTML_PATH.read_text(encoding="utf-8")
    assert 'outDir: "dist"' in vite
    assert '"/api": "http://127.0.0.1:8765"' in vite
    assert html.count('id="root"') == 1
    assert 'src="/src/main.tsx"' in html
    assert "http://" not in html and "https://" not in html
