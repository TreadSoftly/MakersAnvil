"""Record cancellation intent for one prepared Makers Anvil job."""

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
    """Parse one job id, record cancellation locally, and make no process claim."""

    parser = argparse.ArgumentParser(description="Request cancellation without signaling or stopping a process.")
    parser.add_argument("--job-id", required=True, help="Exact prepared job id returned by the job catalog.")
    args = parser.parse_args()
    try:
        result = JobWorkspaceService(ROOT).request_cancellation(args.job_id)
    except JobWorkspaceError as exc:
        print(
            json.dumps(
                {
                    "schemaVersion": "makers-anvil.cli.error.v1",
                    "claimState": "blocked",
                    "error": "job_cancellation_rejected",
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
