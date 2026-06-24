"""Prepare one contained Makers Anvil job workspace from a request preview."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND_SRC = ROOT / "backend" / "src"
sys.path.insert(0, str(BACKEND_SRC))

from makers_anvil_backend.services.job_workspace import JobWorkspaceError, JobWorkspaceService  # noqa: E402


def main() -> int:
    """Parse one preview id, prepare its app-owned workspace, and print redacted JSON."""

    parser = argparse.ArgumentParser(description="Prepare an app-owned job workspace without executing a route.")
    parser.add_argument("--request-preview-id", required=True, help="Exact id returned by the request-preview API.")
    args = parser.parse_args()
    try:
        result = JobWorkspaceService(ROOT).prepare(args.request_preview_id)
    except JobWorkspaceError as exc:
        print(
            json.dumps(
                {
                    "schemaVersion": "makers-anvil.cli.error.v1",
                    "claimState": "blocked",
                    "error": "job_preparation_rejected",
                    "message": str(exc),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
