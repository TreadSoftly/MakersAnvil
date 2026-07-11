"""Purpose: Prepare one non-executable job workspace through an explicit command.

Used by: A human after obtaining a valid execution-request preview ID.
Inputs: One logical request-preview ID and optional runtime-data override.
Outputs: A path-redacted prepared-job JSON record on standard output.
Side effects: Creates only allowlisted app-owned job folders and records.
Safety: Accepts no source path, authorization, command, or launch argument.
Failure behavior: Invalid IDs, records, or containment return a nonzero exit.
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
    """Purpose: Parse one preview id, prepare its app-owned workspace, and print redacted JSON.

    Inputs: No caller-supplied values beyond an implicit instance/class when present.
    Outputs: Returns ``int``, or raises before returning when validation fails.
    How it works: It handles expected failures explicitly, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Accepts no source path, authorization, command, or launch argument.
    Example: Call ``result = main(...)`` with values satisfying the documented inputs.
    Related proof: ``tests/test_job_workspace.py``.
    """

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
