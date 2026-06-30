"""Purpose: Keep a small redacted journal of completed local user actions.

Used by: App-state orchestration after intake and preference operations succeed.
Inputs: Server-selected event type and optional generated intake identifier.
Outputs: A newest-first path-free activity history contract.
Side effects: Creates one immutable JSON event file per completed action.
Safety: Browsers cannot submit arbitrary events, details, paths, or personal data.
Failure behavior: Invalid event types and malformed stored records fail explicitly.
Related proof: ``tests/test_activity_log.py`` and activity schemas.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from makers_anvil_backend.services.workbench_experience import WorkbenchExperienceService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


EVENT_PRESENTATION = {
    "intake-authorized": ("intake", "One file copy was explicitly authorized."),
    "intake-copied": ("intake", "One authorized file was copied into app-owned storage."),
    "preferences-updated": ("settings", "Workbench preferences were updated."),
}
EVENT_FIELDS = {"schemaVersion", "id", "claimState", "timestampUtc", "eventType", "surface", "outcome", "summary", "subjectId"}


class ActivityLogError(ValueError):
    """Purpose: Reject unsupported or corrupted activity records without guessing.

    Inputs: Reviewed diagnostic naming the failed invariant.
    Outputs: Typed ``ValueError`` for service and API tests.
    How it works: Uses standard exception behavior.
    Side effects: None.
    Failure behavior: Callers receive no fabricated history entry.
    Safety: Messages contain no resolved path or user-supplied file metadata.
    Example: An unknown event type raises before a file is created.
    Related proof: ``tests/test_activity_log.py``.
    """


class ActivityLogService:
    """Purpose: Persist only allowlisted server-authored completion events.

    Inputs: Portable workspace config, experience policy, and UTC clock.
    Outputs: Individual immutable event records and bounded recent history.
    How it works: Validates fixed fields, writes create-only JSON, reads newest first.
    Side effects: Creates ``logs/activity`` and one event file per successful call.
    Failure behavior: Collisions, invalid values, and malformed files raise explicitly.
    Safety: No arbitrary event endpoint, source path, token, bytes, or command exists.
    Example: Intake completion records its generated intake id, not its source path.
    Related proof: ``tests/test_activity_log.py``.
    """

    def __init__(
        self,
        *,
        workspace_config: WorkspaceConfigService | None = None,
        experience: WorkbenchExperienceService | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Purpose: Bind portable storage, policy authority, and deterministic time.

        Inputs: Optional focused dependencies for production or tests.
        Outputs: Initialized service; constructors return ``None``.
        How it works: Reuses the experience policy instead of duplicating allowlists.
        Side effects: None until ``record`` is called.
        Failure behavior: Dependency construction failures propagate.
        Safety: Runtime storage remains independent from application source.
        Example: Tests inject a temporary workspace root and fixed clock.
        Related proof: Portable-root and construction tests.
        """

        self.workspace_config = workspace_config or WorkspaceConfigService()
        self.experience = experience or WorkbenchExperienceService(workspace_config=self.workspace_config)
        self.clock = clock or (lambda: datetime.now(UTC))

    def record(self, event_type: str, subject_id: str | None = None) -> dict[str, Any]:
        """Purpose: Create one immutable server-selected activity event.

        Inputs: Allowlisted event type and optional generated intake identifier.
        Outputs: The validated redacted event record written to disk.
        How it works: Maps fixed presentation text and uses exclusive file creation.
        Side effects: Creates the activity directory and exactly one JSON file.
        Failure behavior: Unknown type/subject or collision raises before success.
        Safety: Caller cannot provide summary, surface, path, or arbitrary details.
        Example: ``record('preferences-updated')`` has a null subject id.
        Related proof: Allowlist, privacy, and create-only tests.
        """

        policy = self.experience.policy()["activity"]
        if event_type not in policy["allowedEventTypes"] or event_type not in EVENT_PRESENTATION:
            raise ActivityLogError("activity event type is not allowed")
        if subject_id is not None and (not isinstance(subject_id, str) or not subject_id.startswith("intake-") or len(subject_id) > 80):
            raise ActivityLogError("activity subject id is invalid")
        surface, summary = EVENT_PRESENTATION[event_type]
        event_id = f"activity-{uuid4().hex}"
        event = {
            "schemaVersion": "makers-anvil.runtime.activity-event.v1",
            "id": event_id,
            "claimState": "proven",
            "timestampUtc": self.clock().astimezone(UTC).isoformat(),
            "eventType": event_type,
            "surface": surface,
            "outcome": "completed",
            "summary": summary,
            "subjectId": subject_id,
        }
        self._validate_event(event, policy)
        root = self.workspace_config.runtime_path(policy["directory"])
        root.mkdir(parents=True, exist_ok=True)
        target = root / f"{event['timestampUtc'].replace(':', '-')}_{event_id}.json"
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(event, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return event

    def recent(self) -> dict[str, Any]:
        """Purpose: Return a bounded newest-first history with no filesystem paths.

        Inputs: Validated policy and create-only activity files in user data.
        Outputs: ``makers-anvil.api.activity-history.v1`` contract.
        How it works: Sorts filenames descending, validates, and limits to policy count.
        Side effects: Reads app-owned JSON files only.
        Failure behavior: Any malformed event fails the history instead of being hidden.
        Safety: Response exposes a logical location and reviewed event fields only.
        Example: Empty first run returns count zero and an empty events array.
        Related proof: Ordering, bounds, schema, and privacy tests.
        """

        policy = self.experience.policy()["activity"]
        root = self.workspace_config.runtime_path(policy["directory"])
        paths = sorted(root.glob("*.json"), reverse=True)[: policy["recentLimit"]] if root.exists() else []
        events = []
        for path in paths:
            value = json.loads(path.read_text(encoding="utf-8"))
            self._validate_event(value, policy)
            events.append(value)
        return {
            "schemaVersion": "makers-anvil.api.activity-history.v1",
            "claimState": "proven",
            "mode": "server-authored-create-only",
            "logicalRoot": self.workspace_config.logical_runtime_path(policy["directory"]),
            "summary": {"eventCount": len(events), "recentLimit": policy["recentLimit"]},
            "events": events,
            "safety": {"sourcePathStored": False, "arbitraryEventAccepted": False, "eventMutationEnabled": False, "eventDeletionEnabled": False},
        }

    @staticmethod
    def _validate_event(event: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Enforce the complete closed activity event contract.

        Inputs: Candidate event mapping and validated activity policy.
        Outputs: ``None`` only for an exact server-authored event shape.
        How it works: Checks keys, identity, allowlists, fixed presentation, and subject.
        Side effects: None.
        Failure behavior: Raises ``ActivityLogError`` on the first invalid invariant.
        Safety: Stored files cannot inject alternate summaries or action semantics.
        Example: A settings event must use the fixed settings summary and null subject.
        Related proof: Corrupt-event and arbitrary-detail tests.
        """

        if not isinstance(event, dict) or set(event) != EVENT_FIELDS or event.get("schemaVersion") != "makers-anvil.runtime.activity-event.v1" or event.get("claimState") != "proven":
            raise ActivityLogError("activity event shape is invalid")
        event_type = event.get("eventType")
        if event_type not in policy["allowedEventTypes"] or event_type not in EVENT_PRESENTATION:
            raise ActivityLogError("activity event type is invalid")
        expected_surface, expected_summary = EVENT_PRESENTATION[event_type]
        if event.get("surface") != expected_surface or event.get("summary") != expected_summary or event.get("outcome") != "completed":
            raise ActivityLogError("activity event presentation is invalid")
        if not isinstance(event.get("id"), str) or not event["id"].startswith("activity-") or not isinstance(event.get("timestampUtc"), str):
            raise ActivityLogError("activity event identity is invalid")
        subject = event.get("subjectId")
        if event_type == "preferences-updated" and subject is not None:
            raise ActivityLogError("settings activity cannot have a subject")
        if subject is not None and (not isinstance(subject, str) or not subject.startswith("intake-") or len(subject) > 80):
            raise ActivityLogError("activity event subject is invalid")


__all__ = ["ActivityLogError", "ActivityLogService"]
