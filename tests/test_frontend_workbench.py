"""Purpose: Prove the preview-first frontend workbench structure and controls.

Used by: Developers and CI whenever dashboard layout or client navigation changes.
Inputs: Checked-in HTML, CSS, and JavaScript frontend source.
Outputs: Assertions for required zones, render targets, controls, and responsive rules.
Side effects: Reads product source only and never starts a browser or server.
Safety: Prevents visual restructuring from adding upload or mutation behavior.
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


class WorkbenchParser(HTMLParser):
    """Collect element IDs and input/button attributes with no third-party parser."""

    def __init__(self) -> None:
        """Initialize empty collections before feeding checked-in HTML."""

        super().__init__()
        self.ids: list[str] = []
        self.controls: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Record IDs and user-control attributes for structural assertions."""

        attributes = dict(attrs)
        if "id" in attributes and attributes["id"] is not None:
            self.ids.append(attributes["id"])
        if tag in {"button", "input", "form"}:
            self.controls.append((tag, attributes))


def parse_workbench() -> WorkbenchParser:
    """Return a parsed representation of the static workbench document."""

    parser = WorkbenchParser()
    parser.feed(HTML_PATH.read_text(encoding="utf-8"))
    return parser


def test_primary_workbench_zones_and_views_exist_once() -> None:
    """The first screen retains one source, tool, workflow, proof, and dev surface."""

    parser = parse_workbench()
    counts = Counter(parser.ids)
    required = {
        "workbench",
        "intake-zone",
        "selected-input-zone",
        "tools-zone",
        "workflow-surface",
        "plan-surface",
        "dev-surface",
        "proof-inspector",
    }

    assert required <= set(parser.ids)
    assert all(counts[element_id] == 1 for element_id in required)
    assert all(count == 1 for count in counts.values())


def test_every_javascript_id_target_exists_in_html() -> None:
    """Controller render targets cannot silently drift away from the static shell."""

    parser = parse_workbench()
    javascript = JS_PATH.read_text(encoding="utf-8")
    target_ids = set(re.findall(r'querySelector\("#([^"]+)"\)', javascript))

    assert target_ids <= set(parser.ids)


def test_workbench_controls_cannot_upload_or_mutate() -> None:
    """Only view navigation, local search, refresh, and a disabled intake affordance exist."""

    parser = parse_workbench()
    buttons = [attributes for tag, attributes in parser.controls if tag == "button"]
    inputs = [attributes for tag, attributes in parser.controls if tag == "input"]
    forms = [attributes for tag, attributes in parser.controls if tag == "form"]

    add_files = next(attributes for attributes in buttons if attributes.get("class") == "primary-command")
    assert "disabled" in add_files
    assert forms == []
    assert inputs and all(attributes.get("type") == "search" for attributes in inputs)
    assert all("onclick" not in attributes for attributes in buttons)


def test_controller_wires_read_only_views_and_safe_text_summaries() -> None:
    """Tabs and summaries remain browser-only and render source names as text."""

    javascript = JS_PATH.read_text(encoding="utf-8")

    assert "function selectWorkbenchView" in javascript
    assert "function initializeWorkbenchControls" in javascript
    assert "function renderWorkbenchSummary" in javascript
    assert 'document.querySelector("#selected-input-title").textContent' in javascript
    assert 'method: "GET"' in javascript
    assert 'method: "POST"' not in javascript


def test_styles_define_bounded_desktop_and_mobile_workbenches() -> None:
    """Desktop uses a fixed work area while narrow screens restore document flow."""

    styles = CSS_PATH.read_text(encoding="utf-8")

    assert "height: 100dvh" in styles
    assert "grid-template-columns: minmax(0, 1fr) minmax(300px, 360px)" in styles
    assert "@media (max-width: 900px)" in styles
    assert "overflow: auto" in styles
    assert "@media (prefers-reduced-motion: reduce)" in styles
