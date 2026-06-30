"""Purpose: Prove workbench structure plus bounded choose-review-authorize intake.

Used by: Developers and CI whenever dashboard layout or client navigation changes.
Inputs: Checked-in HTML, CSS, and JavaScript frontend source.
Outputs: Assertions for required zones, render targets, controls, and responsive rules.
Side effects: Reads product source only and never starts a browser or server.
Safety: Permits only explicit one-file intake; all operational actions stay absent.
Failure behavior: Missing zones, duplicate IDs, unsafe controls, or stale wiring fail CI.
Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
"""

import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "frontend" / "public" / "index.html"
CSS_PATH = ROOT / "frontend" / "public" / "assets" / "styles.css"
JS_PATH = ROOT / "frontend" / "public" / "assets" / "app.js"
JS_PATHS = sorted((ROOT / "frontend" / "public" / "assets").glob("*.js"))


class WorkbenchParser(HTMLParser):
    """Purpose: Collect element IDs and input/button attributes with no third-party parser.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``WorkbenchParser`` exposing the state and operations defined below.
    How it works: It checks conditions.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Construct with ``instance = WorkbenchParser(...)`` using values described by ``__init__``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    def __init__(self) -> None:
        """Purpose: Initialize empty collections before feeding checked-in HTML.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Prevents visual restructuring from adding upload or mutation behavior.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
        """

        super().__init__()
        self.ids: list[str] = []
        self.controls: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Purpose: Record IDs and user-control attributes for structural assertions.

        Inputs: Caller-supplied ``tag``, ``attrs`` values from the signature.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It checks conditions.
        Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Prevents visual restructuring from adding upload or mutation behavior.
        Example: Call ``result = instance.handle_starttag(...)`` with values satisfying the documented inputs.
        Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
        """

        attributes = dict(attrs)
        if "id" in attributes and attributes["id"] is not None:
            self.ids.append(attributes["id"])
        if tag in {"button", "input", "form"}:
            self.controls.append((tag, attributes))


def parse_workbench() -> WorkbenchParser:
    """Purpose: Return a parsed representation of the static workbench document.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``WorkbenchParser``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Call ``result = parse_workbench(...)`` with values satisfying the documented inputs.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    parser = WorkbenchParser()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    return parser


def test_primary_workbench_zones_and_views_exist_once() -> None:
    """Purpose: The first screen retains one source, tool, workflow, proof, and dev surface.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k test_primary_workbench_zones_and_views_exist_once``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    parser = parse_workbench()
    counts = Counter(parser.ids)
    required = {
        "workbench",
        "intake-zone",
        "selected-input-zone",
        "tools-zone",
        "capability-matrix",
        "workflow-surface",
        "plan-surface",
        "dev-surface",
        "proof-inspector",
    }

    assert required <= set(parser.ids)
    assert all(counts[element_id] == 1 for element_id in required)
    assert all(count == 1 for count in counts.values())


def test_every_javascript_id_target_exists_in_html() -> None:
    """Purpose: Controller render targets cannot silently drift away from the static shell.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k test_every_javascript_id_target_exists_in_html``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    parser = parse_workbench()
    javascript = "\n".join(path.read_text(encoding="utf-8") for path in JS_PATHS)
    target_ids = set(re.findall(r'querySelector\("#([^"]+)"\)', javascript))

    assert target_ids <= set(parser.ids)


def test_workbench_controls_allow_only_one_file_with_separate_consent() -> None:
    """Purpose: Require one file picker, one consent command, and no folder/form intake.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k test_workbench_controls_allow_only_one_file_with_separate_consent``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    parser = parse_workbench()
    buttons = [attributes for tag, attributes in parser.controls if tag == "button"]
    inputs = [attributes for tag, attributes in parser.controls if tag == "input"]
    forms = [attributes for tag, attributes in parser.controls if tag == "form"]

    add_file = next(attributes for attributes in buttons if attributes.get("id") == "intake-add-button")
    authorize = next(attributes for attributes in buttons if attributes.get("id") == "intake-authorize-button")
    cancel = next(attributes for attributes in buttons if attributes.get("id") == "intake-cancel-button")
    file_input = next(attributes for attributes in inputs if attributes.get("id") == "intake-file-input")
    assert "disabled" in add_file
    assert "disabled" in authorize
    assert cancel.get("aria-label") == "Cancel selected file"
    assert file_input.get("type") == "file"
    assert "multiple" not in file_input
    assert "webkitdirectory" not in file_input
    assert forms == []
    assert {attributes.get("type") for attributes in inputs} == {"search", "file", "radio", "checkbox"}
    assert all("onclick" not in attributes for attributes in buttons)


def test_controller_wires_guarded_intake_and_safe_text_summaries() -> None:
    """Purpose: Tabs stay local while intake uses two guarded POSTs and text-only names.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k test_controller_wires_guarded_intake_and_safe_text_summaries``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    javascript = "\n".join(path.read_text(encoding="utf-8") for path in JS_PATHS)

    assert "function selectWorkbenchView" in javascript
    assert "function initializeWorkbenchControls" in javascript
    assert "function initializeIntakeControls" in javascript
    assert "function reviewSelectedIntakeFile" in javascript
    assert "async function authorizePendingIntake" in javascript
    assert "function renderWorkbenchSummary" in javascript
    assert 'document.querySelector("#selected-input-title").textContent' in javascript
    assert 'method: "GET"' in javascript
    assert javascript.count('method: "POST"') == 4
    assert 'mode: "same-origin"' in javascript
    assert '"X-Makers-Anvil-Request-Token"' in javascript
    assert "dragover" not in javascript.lower()
    assert 'addEventListener("paste"' not in javascript
    assert "renderCapabilityMatrix" in javascript
    assert "configureContextHelp" in javascript
    assert "renderActivityHistory" in javascript
    assert "renderContainedExecutions" in javascript
    assert "Authorize preflight" in javascript
    assert "Run preflight" in javascript
    assert "toolpathGenerated" not in javascript


def test_styles_define_bounded_desktop_and_mobile_workbenches() -> None:
    """Purpose: Desktop uses a fixed work area while narrow screens restore document flow.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents visual restructuring from adding upload or mutation behavior.
    Example: Run ``python -m pytest tests/test_frontend_workbench.py -k test_styles_define_bounded_desktop_and_mobile_workbenches``.
    Related proof: Browser viewport evidence and ``docs/PREVIOUS_APP_REFERENCE_STUDY.md``.
    """

    styles = CSS_PATH.read_text(encoding="utf-8")

    assert "height: 100dvh" in styles
    assert "grid-template-columns: minmax(0, 1fr) minmax(300px, 360px)" in styles
    assert "@media (max-width: 900px)" in styles
    assert "overflow: auto" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
    assert ".intake-review" in styles
    assert ".authorize-command:disabled" in styles
