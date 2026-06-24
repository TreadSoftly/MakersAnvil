"""Purpose: Start Makers Anvil from any working directory in a source checkout.

Used by: Developers and local smoke tests.
Inputs: Script location plus host/port arguments handled by the backend server.
Outputs: A long-running loopback dashboard process.
Side effects: Adds the source backend to this process and opens a local socket.
Safety: Source discovery is relative to this file, never a personal fixed path.
Failure behavior: Import or server startup failures return a nonzero exit.
Related proof: Relocation and runtime smoke checks in ``verify_project.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.server import main  # noqa: E402

raise SystemExit(main())
