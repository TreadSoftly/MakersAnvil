"""Purpose: Build and validate the records stored for prepared local jobs.

Used by: ``JobWorkspaceService`` before writing or exposing job state.
Inputs: Logical request previews, job identifiers, and cancellation metadata.
Outputs: Strict path-redacted job and cancellation dictionaries.
Side effects: None; this module validates data but does not touch the filesystem.
Safety: Commands, private paths, process IDs, outputs, and proof are excluded.
Failure behavior: Contract violations raise ``ValueError`` before persistence.
Related proof: ``tests/test_job_workspace.py`` and job-record schemas.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


JOB_ID_PATTERN = re.compile(r"^job-[a-f0-9]{24}$")
PREVIEW_ID_PATTERN = re.compile(r"^execution-request-preview-[A-Za-z0-9._-]+$")
LOGICAL_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUIRED_WORKSPACE_DIRECTORIES = {"control", "working", "logs", "outputs"}
REQUIRED_JOB_FIELDS = {
    "schemaVersion",
    "id",
    "claimState",
    "createdUtc",
    "requestPreviewId",
    "route",
    "operation",
    "intent",
    "authorization",
    "lifecycle",
    "workspace",
    "cancellationRecord",
    "safety",
}
REQUIRED_CANCELLATION_FIELDS = {
    "schemaVersion",
    "jobId",
    "claimState",
    "state",
    "requestId",
    "requestedAt",
    "processSignalSent",
    "processStopped",
}
JOB_SAFETY_FLAGS = {
    "executableRequestPersisted",
    "authorizationAccepted",
    "sourcePathStored",
    "sourceContentStored",
    "selectedFileHandedOff",
    "outputPathResolved",
    "commandConstructed",
    "processStarted",
    "processSignalSent",
    "toolLaunched",
    "userFileWritten",
    "outputArtifactWritten",
    "auditEventWritten",
    "proofCaptured",
}


def job_id_for_preview(request_preview_id: str) -> str:
    """Derive one stable job id so repeated preparation cannot duplicate a request."""

    digest = hashlib.sha256(request_preview_id.encode("utf-8")).hexdigest()[:24]
    return f"job-{digest}"


def initial_cancellation_record(job_id: str) -> dict[str, Any]:
    """Build initial control state without inventing a signal or stopped process."""

    return {
        "schemaVersion": "makers-anvil.runtime.job-cancellation.v1",
        "jobId": job_id,
        "claimState": "staged",
        "state": "not-requested",
        "requestId": None,
        "requestedAt": None,
        "processSignalSent": False,
        "processStopped": False,
    }


def requested_cancellation_record(record: dict[str, Any]) -> dict[str, Any]:
    """Return cancellation intent while preserving constant-false process outcomes."""

    return {
        **record,
        "claimState": "staged",
        "state": "requested",
        "requestId": f"cancel-{uuid4().hex}",
        "requestedAt": datetime.now(UTC).isoformat(),
    }


def atomic_write_json(path: Path, record: dict[str, Any]) -> None:
    """Replace one app-owned JSON record only after its complete temporary write."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        # A failed replacement must not leave a partial app-owned record that
        # a future catalog or preparation pass could misinterpret.
        if temporary.exists():
            temporary.unlink()


def valid_job_record(record: dict[str, Any], policy: dict[str, Any]) -> bool:
    """Accept only prepared, path-redacted, non-executable job manifests."""

    if (
        not isinstance(record, dict)
        or set(record) != REQUIRED_JOB_FIELDS
        or not JOB_ID_PATTERN.fullmatch(str(record.get("id", "")))
    ):
        return False
    workspace = record.get("workspace", {})
    lifecycle = record.get("lifecycle", {})
    authorization = record.get("authorization", {})
    safety = record.get("safety", {})
    directories = workspace.get("directories", []) if isinstance(workspace, dict) else []
    expected_root = f"makers-anvil-data://user/jobs/{record['id']}"
    return (
        record.get("schemaVersion") == "makers-anvil.runtime.job-workspace.v1"
        and record.get("claimState") == "staged"
        and _valid_timestamp(record.get("createdUtc"))
        and PREVIEW_ID_PATTERN.fullmatch(str(record.get("requestPreviewId", ""))) is not None
        and valid_id_label(record.get("route"), policy["scope"]["routeId"])
        and valid_id_label(record.get("operation"))
        and valid_intent(record.get("intent"))
        and authorization == {"required": True, "accepted": False}
        and lifecycle == {"state": "prepared", "processId": None, "startedAt": None, "completedAt": None}
        and isinstance(workspace, dict)
        and set(workspace) == {"logicalRoot", "absolutePathExposed", "directories"}
        and workspace.get("logicalRoot") == expected_root
        and workspace.get("absolutePathExposed") is False
        and isinstance(directories, list)
        and len(directories) == len(REQUIRED_WORKSPACE_DIRECTORIES)
        and all(isinstance(item, dict) and set(item) == {"id", "logicalPath"} for item in directories)
        and {item.get("id") for item in directories if isinstance(item, dict)} == REQUIRED_WORKSPACE_DIRECTORIES
        and all(item.get("logicalPath") == f"{expected_root}/{item.get('id')}" for item in directories if isinstance(item, dict))
        and record.get("cancellationRecord") == f"{expected_root}/control/cancellation.json"
        and isinstance(safety, dict)
        and set(safety) == JOB_SAFETY_FLAGS
        and all(value is False for value in safety.values())
    )


def valid_cancellation_record(record: dict[str, Any], job_id: str) -> bool:
    """Accept only unsignaled cancellation state belonging to the prepared job."""

    if (
        not isinstance(record, dict)
        or set(record) != REQUIRED_CANCELLATION_FIELDS
        or record.get("schemaVersion") != "makers-anvil.runtime.job-cancellation.v1"
        or record.get("claimState") != "staged"
    ):
        return False
    state = record.get("state")
    request_id = record.get("requestId")
    requested_at = record.get("requestedAt")
    request_fields_valid = (
        request_id is None and requested_at is None
        if state == "not-requested"
        else isinstance(request_id, str)
        and re.fullmatch(r"cancel-[a-f0-9]{32}", request_id) is not None
        and _valid_timestamp(requested_at)
    )
    return (
        record.get("jobId") == job_id
        and state in {"not-requested", "requested"}
        and request_fields_valid
        and record.get("processSignalSent") is False
        and record.get("processStopped") is False
    )


def valid_intent(value: object) -> bool:
    """Reject private paths or malformed tool data from persisted logical intent."""

    if not isinstance(value, dict) or set(value) != {"source", "output", "tool"}:
        return False
    source = value.get("source")
    output = value.get("output")
    tool = value.get("tool")
    intake_id = source.get("intakeId") if isinstance(source, dict) else None
    bundle_id = output.get("bundleId") if isinstance(output, dict) else None
    logical_output = output.get("logicalDirectory") if isinstance(output, dict) else None
    output_token = logical_output.removeprefix("makers-anvil-data://user/outputs/") if isinstance(logical_output, str) else None
    source_valid = (
        isinstance(source, dict)
        and set(source) == {"intakeId", "logicalReference"}
        and isinstance(intake_id, str)
        and LOGICAL_TOKEN_PATTERN.fullmatch(intake_id) is not None
        and ".." not in intake_id
        and source.get("logicalReference") == f"makers-anvil-intake://records/{intake_id}"
    )
    output_valid = (
        isinstance(output, dict)
        and set(output) == {"bundleId", "logicalDirectory"}
        and isinstance(bundle_id, str)
        and LOGICAL_TOKEN_PATTERN.fullmatch(bundle_id) is not None
        and ".." not in bundle_id
        and isinstance(output_token, str)
        and LOGICAL_TOKEN_PATTERN.fullmatch(output_token) is not None
        and ".." not in output_token
    )
    tool_valid = tool is None or (
        isinstance(tool, dict)
        and set(tool) == {"id", "label", "claimState"}
        and isinstance(tool.get("id"), str)
        and LOGICAL_TOKEN_PATTERN.fullmatch(tool["id"]) is not None
        and ".." not in tool["id"]
        and isinstance(tool.get("label"), str)
        and tool.get("claimState") == "detected"
    )
    return source_valid and output_valid and tool_valid


def valid_id_label(value: object, required_id: str | None = None) -> bool:
    """Validate a minimal identity record and optionally require one exact id."""

    return (
        isinstance(value, dict)
        and set(value) == {"id", "label"}
        and isinstance(value.get("id"), str)
        and LOGICAL_TOKEN_PATTERN.fullmatch(value["id"]) is not None
        and ".." not in value["id"]
        and (required_id is None or value["id"] == required_id)
        and isinstance(value.get("label"), str)
        and bool(value["label"])
    )


def _valid_timestamp(value: object) -> bool:
    """Require a timezone-aware ISO timestamp for every persisted runtime event."""

    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None
