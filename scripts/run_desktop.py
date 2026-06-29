"""Purpose: Start the native Makers Anvil desktop application from source or a bundle.

Used by: Developers, PyInstaller, Windows shortcuts, and future platform bundles.
Inputs: Script location and the optional documented ``--smoke`` CLI switch.
Outputs: Native desktop window behavior or package-smoke JSON and an exit code.
Side effects: Delegates one bounded desktop/session lifecycle to the backend.
Safety: Resolves source locally and accepts no path, URL, command, or tool argument.
Failure behavior: Import, resource, webview, or server errors return a nonzero exit.
Related proof: ``tests/test_desktop.py`` and Windows packaging CI.
"""

from __future__ import annotations

import sys
from pathlib import Path


# Source checkouts need the backend package on sys.path; frozen builds already
# contain analyzed modules, so this stable relative path introduces no machine tie.
ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.desktop import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
