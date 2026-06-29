"""Purpose: Resolve bundled and source-checkout resources without fixed machine paths.

Used by: The HTTP server, desktop launcher, packaging smoke tests, and verifier.
Inputs: This module's location plus PyInstaller's documented frozen-app marker.
Outputs: Validated absolute paths to packaged read-only frontend resources.
Side effects: Reads process attributes and filesystem metadata only.
Safety: Never derives resources from a username, current directory, or reference app.
Failure behavior: Missing or incomplete resource trees raise explicit exceptions.
Related proof: ``tests/test_runtime_resources.py`` and desktop package smoke proof.
"""

from __future__ import annotations

import sys
from pathlib import Path


class ResourceResolutionError(RuntimeError):
    """Purpose: Identify a missing or malformed bundled resource tree.

    Inputs: A precise diagnostic string supplied at the failed boundary.
    Outputs: A typed exception that callers can report without guessing.
    How it works: Inherits normal ``RuntimeError`` behavior without adding state.
    Side effects: None until a caller raises an instance.
    Failure behavior: Preserves the diagnostic text and normal exception chain.
    Safety: Prevents startup from silently serving an unintended directory.
    Example: ``raise ResourceResolutionError("index.html is missing")``.
    Related proof: ``tests/test_runtime_resources.py`` exercises failure cases.
    """


def application_root() -> Path:
    """Purpose: Return the read-only source or frozen bundle root.

    Inputs: ``sys._MEIPASS`` when PyInstaller is running, otherwise this file.
    Outputs: An absolute ``Path`` containing bundled application resources.
    How it works: Uses PyInstaller's runtime marker or walks from installed source.
    Side effects: Resolves paths but creates, changes, and deletes nothing.
    Failure behavior: Invalid path values surface through ``Path.resolve``.
    Safety: The caller's working directory and personal home are never consulted.
    Example: Source mode returns the repository root; one-file mode returns ``_MEIPASS``.
    Related proof: PyInstaller runtime docs and ``tests/test_runtime_resources.py``.
    """

    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    return Path(__file__).resolve().parents[3]


def frontend_root(root: Path | None = None) -> Path:
    """Purpose: Locate and validate the one authoritative static frontend tree.

    Inputs: Optional test/build root; normal callers use ``application_root``.
    Outputs: Absolute directory containing ``index.html`` and local assets.
    How it works: Appends the package-stable ``frontend/public`` relative path.
    Side effects: Checks directory and file existence only.
    Failure behavior: Raises ``ResourceResolutionError`` with the missing location.
    Safety: Never falls back to a nearby directory that could expose private files.
    Example: ``frontend_root(Path("bundle"))`` validates ``bundle/frontend/public``.
    Related proof: ``tests/test_runtime_resources.py`` and PyInstaller data config.
    """

    base = (root or application_root()).resolve()
    candidate = (base / "frontend" / "public").resolve()
    index = candidate / "index.html"
    if not candidate.is_dir() or not index.is_file():
        raise ResourceResolutionError(f"Makers Anvil frontend resources are incomplete: {candidate}")
    return candidate
