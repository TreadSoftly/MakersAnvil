"""Purpose: Create the portable app-owned runtime directory layout explicitly.

Used by: A human running ``python scripts/init_workspace.py``.
Inputs: Platform environment and optional runtime-data override.
Outputs: A redacted JSON layout summary printed to standard output.
Side effects: Creates only validated app-owned runtime directories.
Safety: Never imports user files or prints a resolved personal path.
Failure behavior: Invalid settings or containment errors exit nonzero.
Related proof: ``tests/test_workspace_config.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService  # noqa: E402


def main() -> int:
    """Create the portable app-owned directory layout and print its redacted manifest."""

    manifest = WorkspaceConfigService(ROOT).initialize()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
