"""Purpose: Record a cancellation request without claiming a stopped process.

Used by: A human targeting one existing prepared-job ID.
Inputs: One logical job ID and optional runtime-data override.
Outputs: A path-redacted cancellation-intent record on standard output.
Side effects: Writes one idempotent app-owned control record.
Safety: Sends no signal and cannot terminate, kill, or launch a process.
Failure behavior: Unknown jobs or malformed records return a nonzero exit.
Related proof: ``tests/test_job_workspace.py``.
"""

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
