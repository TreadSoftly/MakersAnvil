"""Initialize the app-owned local Makers Anvil workspace directory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService  # noqa: E402


def main() -> int:
    manifest = WorkspaceConfigService(ROOT).initialize()
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
