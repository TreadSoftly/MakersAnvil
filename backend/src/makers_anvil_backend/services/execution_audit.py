"""Purpose: Persist immutable server-authored lifecycle events for contained execution.

Used by: ``ContainedExecutionService`` before and after each execution state change.
Inputs: Generated execution id, closed event type/outcome, and optional generated reference id.
Outputs: Strict event records and a path-redacted ordered audit history.
Side effects: Creates one exclusive JSON file per event under app-owned execution logs.
Safety: No browser text, source path, command, process data, or arbitrary event is accepted.
Failure behavior: Invalid ids/types/outcomes/references and malformed stored events fail closed.
Related proof: ``tests/test_contained_execution.py`` and execution-audit schemas.
"""

from __future__ import annotations

import json
import os
import re
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


EXECUTION_ID_PATTERN = re.compile(r"^execution-[a-f0-9]{32}$")
AUDIT_EVENT_FIELDS = {
    "schemaVersion", "id", "executionId", "sequence", "claimState",
    "timestampUtc", "eventType", "outcome", "summary", "referenceId",
}
EVENT_OUTCOMES = {
    "request-created": {"accepted"},
    "authorization-recorded": {"accepted"},
    "execution-started": {"running"},
    "execution-cancelled": {"cancelled"},
    "execution-completed": {"passed", "failed"},
    "proof-recorded": {"passed", "failed"},
}
EVENT_SUMMARIES = {
    ("request-created", "accepted"): "Contained execution request created.",
    ("authorization-recorded", "accepted"): "Explicit local authorization recorded.",
    ("execution-started", "running"): "Built-in STL preflight started.",
    ("execution-cancelled", "cancelled"): "Cooperative cancellation completed.",
    ("execution-completed", "passed"): "Built-in STL preflight completed successfully.",
    ("execution-completed", "failed"): "Built-in STL preflight completed with a failed result.",
    ("proof-recorded", "passed"): "Passing output proof recorded.",
    ("proof-recorded", "failed"): "Failed output proof recorded.",
}


class ExecutionAuditError(ValueError):
    """Purpose: Reject any execution audit value outside the closed lifecycle contract.

    Inputs: Reviewed diagnostic naming the failed audit invariant.
    Outputs: Typed ``ValueError`` for orchestration and tests.
    How it works: Uses normal exception message storage without coercing values.
    Side effects: None.
    Failure behavior: The caller receives no partially accepted event.
    Safety: Diagnostics describe fields and never expose private filesystem locations.
    Example: Browser-supplied event text is impossible because only event ids are accepted.
    Related proof: Execution audit allowlist and corruption tests.
    """


class ExecutionAuditService:
    """Purpose: Own create-only ordered audit evidence for one execution directory.

    Inputs: Portable workspace service, UTC clock, execution id, and closed event values.
    Outputs: Immutable events plus bounded ordered public history.
    How it works: Counts validated existing events and exclusively creates the next file.
    Side effects: Creates only ``executions/<id>/logs/audit/*.json`` event files.
    Failure behavior: Collisions, malformed history, or invalid values raise explicitly.
    Safety: Events contain fixed summaries and generated identifiers, never user content.
    Example: Successful preflight has request, authorization, start, complete, and proof events.
    Related proof: ``tests/test_contained_execution.py`` and audit schemas.
    """

    def __init__(
        self,
        *,
        workspace_config: WorkspaceConfigService,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Purpose: Bind portable execution storage and an injectable aware UTC clock.

        Inputs: Shared workspace configuration and optional deterministic test clock.
        Outputs: Initialized service with an in-process append lock.
        How it works: Stores dependencies and creates no runtime directory yet.
        Side effects: Allocates one thread lock only.
        Failure behavior: Dependency construction errors propagate directly.
        Safety: Runtime storage remains independent from source and current directory.
        Example: Tests inject a temporary workspace plus a fixed UTC lambda.
        Related proof: Portable-root execution audit tests.
        """

        self.workspace_config = workspace_config
        self.clock = clock or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()

    def append(
        self,
        execution_id: str,
        event_type: str,
        outcome: str,
        reference_id: str | None = None,
    ) -> dict[str, Any]:
        """Purpose: Exclusively create the next fixed lifecycle event.

        Inputs: Generated execution id, closed event/outcome pair, optional generated reference.
        Outputs: The complete validated event written to app-owned storage.
        How it works: Validates existing history, assigns sequence, and fsyncs one new file.
        Side effects: Creates the audit directory and exactly one immutable JSON file.
        Failure behavior: Unknown values or write failures raise without claiming an event.
        Safety: Summary text is selected internally and no arbitrary detail field exists.
        Example: ``append(id, 'execution-started', 'running')`` creates sequence three.
        Related proof: Ordering, immutability, and arbitrary-event rejection tests.
        """

        self._validate_inputs(execution_id, event_type, outcome, reference_id)
        with self._lock:
            existing = self._read_events(execution_id)
            sequence = len(existing) + 1
            event_id = f"execution-audit-{uuid4().hex}"
            event = {
                "schemaVersion": "makers-anvil.runtime.execution-audit-event.v1",
                "id": event_id,
                "executionId": execution_id,
                "sequence": sequence,
                "claimState": "proven",
                "timestampUtc": self._utc_now().isoformat(),
                "eventType": event_type,
                "outcome": outcome,
                "summary": EVENT_SUMMARIES[(event_type, outcome)],
                "referenceId": reference_id,
            }
            self._validate_event(event, execution_id)
            root = self._audit_root(execution_id)
            root.mkdir(parents=True, exist_ok=True)
            target = root / f"{sequence:04d}-{event_id}.json"
            descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump(event, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            return event

    def history(self, execution_id: str) -> dict[str, Any]:
        """Purpose: Return complete ordered audit evidence without private paths.

        Inputs: Generated execution id.
        Outputs: Public history with event count, logical root, and strict events.
        How it works: Reads files by sequence filename and validates contiguous ordering.
        Side effects: Reads app-owned event JSON only.
        Failure behavior: Missing directories return empty history; malformed events raise.
        Safety: Resolved audit root and filesystem filenames are never returned.
        Example: A completed execution exposes five reviewed lifecycle facts.
        Related proof: Audit history schema, empty state, and sequence-gap tests.
        """

        events = self._read_events(execution_id)
        return {
            "schemaVersion": "makers-anvil.api.execution-audit-history.v1",
            "claimState": "proven",
            "executionId": execution_id,
            "appendOnly": True,
            "logicalRoot": f"makers-anvil-data://user/executions/{execution_id}/logs/audit",
            "summary": {"eventCount": len(events)},
            "events": events,
            "safety": {
                "arbitraryEventAccepted": False,
                "eventMutationEnabled": False,
                "eventDeletionEnabled": False,
                "privatePathExposed": False,
            },
        }

    def _read_events(self, execution_id: str) -> list[dict[str, Any]]:
        """Purpose: Decode and validate every create-only event in sequence order.

        Inputs: Generated execution id.
        Outputs: Ordered list with contiguous sequence numbers.
        How it works: Sorts fixed JSON filenames and validates each decoded mapping.
        Side effects: Reads app-owned audit files only.
        Failure behavior: Invalid JSON, file names, event fields, or gaps raise.
        Safety: Symbolic-link directories and files are rejected before reads.
        Example: Files ``0001-*`` and ``0002-*`` become events one and two.
        Related proof: Corrupt-history and symlink rejection tests.
        """

        self._validate_execution_id(execution_id)
        root = self._audit_root(execution_id)
        if not root.exists():
            return []
        if root.is_symlink() or not root.is_dir():
            raise ExecutionAuditError("execution audit root is not a regular directory")
        events: list[dict[str, Any]] = []
        for expected_sequence, path in enumerate(sorted(root.glob("*.json")), start=1):
            if path.is_symlink() or not path.is_file():
                raise ExecutionAuditError("execution audit event is not a regular file")
            try:
                event = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ExecutionAuditError("execution audit event is unreadable") from exc
            self._validate_event(event, execution_id)
            if event["sequence"] != expected_sequence or not path.name.startswith(f"{expected_sequence:04d}-"):
                raise ExecutionAuditError("execution audit sequence is not contiguous")
            events.append(event)
        return events

    def _audit_root(self, execution_id: str) -> Path:
        """Purpose: Resolve one contained private audit directory from a generated id.

        Inputs: Valid execution id.
        Outputs: Path below app-owned ``executions/<id>/logs/audit``.
        How it works: Validates the id before joining fixed path components.
        Side effects: None; the path need not exist.
        Failure behavior: Invalid ids raise before path construction.
        Safety: No browser-supplied separator or traversal token can enter the path.
        Example: ``execution-<32 hex>`` maps to its private audit directory.
        Related proof: Traversal-id tests.
        """

        self._validate_execution_id(execution_id)
        return self.workspace_config.runtime_path(Path("executions") / execution_id / "logs" / "audit")

    @staticmethod
    def _validate_inputs(execution_id: str, event_type: str, outcome: str, reference_id: str | None) -> None:
        """Purpose: Validate the small closed input vocabulary before file access.

        Inputs: Execution id, event type, outcome, and optional generated reference.
        Outputs: ``None`` only when the combination is allowed.
        How it works: Checks regex, event/outcome mapping, and reference token format.
        Side effects: None.
        Failure behavior: Raises ``ExecutionAuditError`` on first invalid value.
        Safety: There is no free-text summary or details input.
        Example: Proof may reference ``execution-proof``; request-created uses null.
        Related proof: Parameterized audit input tests.
        """

        ExecutionAuditService._validate_execution_id(execution_id)
        if event_type not in EVENT_OUTCOMES or outcome not in EVENT_OUTCOMES[event_type]:
            raise ExecutionAuditError("execution audit event type and outcome are invalid")
        if reference_id is not None and (not isinstance(reference_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", reference_id)):
            raise ExecutionAuditError("execution audit reference id is invalid")

    @staticmethod
    def _validate_event(event: dict[str, Any], execution_id: str) -> None:
        """Purpose: Enforce every field in a decoded execution audit event.

        Inputs: Candidate event mapping and expected execution id.
        Outputs: ``None`` for one exact fixed-summary event.
        How it works: Checks field set, ids, sequence, timestamp, mapping, and reference.
        Side effects: None.
        Failure behavior: Raises ``ExecutionAuditError`` instead of exposing corruption.
        Safety: A modified local file cannot inject arbitrary history text.
        Example: A passed proof event must use the fixed passing proof summary.
        Related proof: Stored-event corruption tests and schema validation.
        """

        if not isinstance(event, dict) or set(event) != AUDIT_EVENT_FIELDS:
            raise ExecutionAuditError("execution audit event shape is invalid")
        if event.get("schemaVersion") != "makers-anvil.runtime.execution-audit-event.v1" or event.get("claimState") != "proven":
            raise ExecutionAuditError("execution audit event identity is invalid")
        if event.get("executionId") != execution_id or not isinstance(event.get("sequence"), int) or isinstance(event.get("sequence"), bool) or event["sequence"] < 1:
            raise ExecutionAuditError("execution audit event owner or sequence is invalid")
        if not isinstance(event.get("id"), str) or not re.fullmatch(r"execution-audit-[a-f0-9]{32}", event["id"]):
            raise ExecutionAuditError("execution audit event id is invalid")
        if not isinstance(event.get("timestampUtc"), str):
            raise ExecutionAuditError("execution audit timestamp is invalid")
        event_type = event.get("eventType")
        outcome = event.get("outcome")
        ExecutionAuditService._validate_inputs(execution_id, event_type, outcome, event.get("referenceId"))
        if event.get("summary") != EVENT_SUMMARIES[(event_type, outcome)]:
            raise ExecutionAuditError("execution audit summary is invalid")

    @staticmethod
    def _validate_execution_id(execution_id: str) -> None:
        """Purpose: Reject traversal and arbitrary execution identifiers.

        Inputs: Candidate execution id.
        Outputs: ``None`` only for ``execution-<32 lowercase hex>``.
        How it works: Applies one anchored regular expression.
        Side effects: None.
        Failure behavior: Raises ``ExecutionAuditError`` before filesystem access.
        Safety: Separators, dots, globs, and user filenames cannot become paths.
        Example: ``../outside`` is rejected.
        Related proof: Traversal-id tests.
        """

        if not isinstance(execution_id, str) or not EXECUTION_ID_PATTERN.fullmatch(execution_id):
            raise ExecutionAuditError("execution id is invalid")

    def _utc_now(self) -> datetime:
        """Purpose: Normalize the injected clock to aware UTC.

        Inputs: Constructor-provided clock callable.
        Outputs: Timezone-aware UTC datetime.
        How it works: Calls once, rejects naive values, and converts to UTC.
        Side effects: Reads current time only.
        Failure behavior: Invalid clocks raise ``ExecutionAuditError``.
        Safety: Ordered evidence never depends on local timezone guessing.
        Example: Tests inject one deterministic UTC timestamp.
        Related proof: Deterministic audit timestamp tests.
        """

        value = self.clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ExecutionAuditError("execution audit clock is invalid")
        return value.astimezone(UTC)


__all__ = ["EXECUTION_ID_PATTERN", "ExecutionAuditError", "ExecutionAuditService"]
