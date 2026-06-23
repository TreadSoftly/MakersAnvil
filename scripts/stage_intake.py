"""Stage one file as a metadata-only Makers Anvil intake record."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.services.intake_catalog import IntakeCatalogError, IntakeCatalogService  # noqa: E402


def main() -> int:
    """Parse one explicit file path and stage only its privacy-safe metadata."""

    parser = argparse.ArgumentParser(description="Stage metadata for one local file without copying its contents.")
    parser.add_argument("--path", required=True, help="Path to one regular local file.")
    args = parser.parse_args()
    try:
        record = IntakeCatalogService(ROOT).stage_file_metadata(args.path)
    except IntakeCatalogError as exc:
        print(
            json.dumps(
                {
                    "schemaVersion": "makers-anvil.cli.error.v1",
                    "claimState": "blocked",
                    "error": "intake_rejected",
                    "message": str(exc),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(record, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
