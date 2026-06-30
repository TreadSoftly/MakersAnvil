"""Purpose: Prove one authorized built-in STL preflight from consent through proof.

Used by: Developers and CI whenever contained execution behavior changes.
Inputs: Real committed policies copied into isolated source/runtime test roots.
Outputs: Assertions over authorization, cancellation, audit, artifacts, hashes, and privacy.
Side effects: Writes only pytest-owned intake and execution data.
Safety: No user source, external command/process/tool, archive, or software is touched.
Failure behavior: Any scope, containment, proof, or cancellation regression fails explicitly.
Related proof: ``services/contained_execution.py`` and execution schemas.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import struct
from datetime import UTC, datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Callable

import pytest

from makers_anvil_backend.services.authorized_intake import AuthorizedIntakeService
from makers_anvil_backend.services.contained_execution import ContainedExecutionError, ContainedExecutionService
from makers_anvil_backend.services.execution_audit import ExecutionAuditService
from makers_anvil_backend.services.intake_catalog import IntakeCatalogService
from makers_anvil_backend.services.local_request_guard import LocalRequestContext, LocalRequestGuard
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "contained-execution-test-token"
BASE_TIME = datetime(2026, 6, 30, 16, 0, tzinfo=UTC)


class AdvancingClock:
    """Purpose: Supply deterministic distinct UTC timestamps across one transaction.

    Inputs: Initial aware UTC datetime.
    Outputs: Callable clock returning one-second increments.
    How it works: Returns current value then advances internal state by one second.
    Side effects: Mutates only its private test timestamp.
    Failure behavior: Invalid initial values remain visible fixture errors.
    Safety: Does not read system time or application/user state.
    Example: Authorization and proof receive ordered reproducible timestamps.
    Related proof: Audit sequence and lifecycle timestamp assertions below.
    """

    def __init__(self, value: datetime = BASE_TIME) -> None:
        """Purpose: Initialize the next deterministic clock value.

        Inputs: Aware datetime used for the first call.
        Outputs: Initialized test clock; constructors return ``None``.
        How it works: Stores the supplied datetime without filesystem work.
        Side effects: Sets private in-memory state only.
        Failure behavior: Naive values are rejected by production services when called.
        Safety: No production clock is replaced outside the isolated service fixture.
        Example: ``AdvancingClock(BASE_TIME)`` starts at 16:00 UTC.
        Related proof: Service UTC validation tests.
        """

        self.value = value

    def __call__(self) -> datetime:
        """Purpose: Return one timestamp and advance the next call by one second.

        Inputs: No caller-supplied values.
        Outputs: Current aware datetime.
        How it works: Saves current value, increments private state, and returns saved value.
        Side effects: Advances private in-memory time.
        Failure behavior: Datetime arithmetic errors propagate.
        Safety: No system or application clock is modified.
        Example: Two calls return 16:00:00 then 16:00:01 UTC.
        Related proof: Ordered audit event tests.
        """

        current = self.value
        self.value += timedelta(seconds=1)
        return current


def request_context(**changes: str) -> LocalRequestContext:
    """Purpose: Build valid same-origin mutation evidence with focused overrides.

    Inputs: Optional field changes for rejection tests.
    Outputs: Immutable local request context.
    How it works: Merges overrides into one known-good loopback baseline.
    Side effects: None.
    Failure behavior: Unknown keys fail through dataclass construction.
    Safety: The real guard still validates every returned field.
    Example: ``request_context(request_token='wrong')`` exercises token rejection.
    Related proof: Shared local request guard tests.
    """

    values = {
        "request_token": TOKEN,
        "origin": "http://127.0.0.1:8766",
        "host": "127.0.0.1:8766",
        "fetch_site": "same-origin",
    }
    values.update(changes)
    return LocalRequestContext(**values)


def binary_stl() -> bytes:
    """Purpose: Return one minimal structurally consistent binary STL fixture.

    Inputs: No caller values.
    Outputs: 134 bytes containing header, one-triangle count, and one triangle record.
    How it works: Packs little-endian count one after an 80-byte header.
    Side effects: None.
    Failure behavior: Struct packing errors fail the test directly.
    Safety: Bytes are synthetic and contain no user or machine data.
    Example: Preflight detects binary-stl with triangleCount one.
    Related proof: Binary format recognition test below.
    """

    return b"Makers Anvil test STL".ljust(80, b"\0") + struct.pack("<I", 1) + (b"\0" * 50)


def build_service(
    tmp_path: Path,
    *,
    content: bytes | None = None,
    chunk_hook: Callable[[str, int], None] | None = None,
) -> tuple[ContainedExecutionService, dict, Path]:
    """Purpose: Build real intake and execution services over isolated portable storage.

    Inputs: Pytest root, optional STL bytes, and optional source-chunk observer.
    Outputs: Execution service, authorized intake record, and private runtime root.
    How it works: Copies policies, injects paths/clock/guard, then performs two-step intake.
    Side effects: Creates only pytest-owned config, intake, and execution fixtures.
    Failure behavior: Unexpected intake rejection fails fixture setup directly.
    Safety: No production user-data root or previous-app dependency is consulted.
    Example: Each test starts with one copied ``fixture.stl`` record.
    Related proof: Intake integration and portable execution assertions.
    """

    source_root = tmp_path / "source"
    config_root = source_root / "config"
    config_root.mkdir(parents=True)
    for name in ("default_settings.json", "intake_policy.json", "contained_execution_policy.json"):
        shutil.copy2(ROOT / "config" / name, config_root / name)
    data_root = tmp_path / "runtime"
    runtime_paths = RuntimePathsService(
        source_root=source_root,
        environ={DATA_DIR_ENV: str(data_root)},
        home=tmp_path / "home",
        platform_name="linux",
    )
    workspace = WorkspaceConfigService(source_root, runtime_paths)
    catalog = IntakeCatalogService(source_root, workspace)
    guard = LocalRequestGuard(TOKEN)
    clock = AdvancingClock()
    intake = AuthorizedIntakeService(catalog, request_guard=guard, clock=clock)
    payload = content if content is not None else binary_stl()
    authorization = intake.authorize(
        {"displayName": "fixture.stl", "sizeBytes": len(payload), "modifiedUtc": "2026-06-30T15:00:00Z"},
        request_context(),
    )["authorization"]
    result = intake.ingest(authorization["id"], BytesIO(payload), len(payload), request_context())
    audit = ExecutionAuditService(workspace_config=workspace, clock=clock)
    service = ContainedExecutionService(
        source_root,
        workspace_config=workspace,
        intake_catalog=catalog,
        request_guard=guard,
        audit=audit,
        clock=clock,
        chunk_hook=chunk_hook,
    )
    return service, result["record"], data_root


def authorization_payload(intake_id: str) -> dict[str, object]:
    """Purpose: Return the exact explicit contained-execution consent object.

    Inputs: Generated authorized intake id.
    Outputs: Four-field browser/API payload.
    How it works: Combines fixed route/operation/accepted values with intake id.
    Side effects: None.
    Failure behavior: Invalid ids are rejected by the service under test.
    Safety: Contains no path, command, tool, output, or arbitrary option.
    Example: Used by each authorization test below.
    Related proof: Execution authorization API schema.
    """

    return {
        "intakeId": intake_id,
        "routeId": "mesh-to-toolpath",
        "operationId": "built-in-stl-preflight",
        "accepted": True,
    }


def test_authorize_and_run_create_real_hashed_partial_route_proof(tmp_path: Path) -> None:
    """Purpose: Prove valid STL consent produces report, log, proof, and complete audit.

    Inputs: One isolated authorized one-triangle binary STL.
    Outputs: Completed proven record and independently verified artifact hashes.
    How it works: Authorizes, runs, reads generated files, and recomputes SHA-256.
    Side effects: Writes only pytest-owned execution files.
    Failure behavior: Missing artifacts, wrong claims, or hash drift fails assertions.
    Safety: Proof explicitly keeps full route and toolpath generation false.
    Example: Five audit events end with ``proof-recorded``.
    Related proof: Runtime execution/report/proof/audit schemas.
    """

    service, intake, data_root = build_service(tmp_path)
    authorized = service.authorize(authorization_payload(intake["id"]), request_context())
    completed = service.run(authorized["record"]["id"], request_context())
    record = completed["record"]
    root = data_root / "executions" / record["id"]
    report_path = root / "outputs" / "stl-preflight-report.json"
    log_path = root / "logs" / "execution.log"
    proof_path = root / "outputs" / "execution-proof.json"

    assert record["claimState"] == "proven"
    assert record["lifecycle"]["state"] == "completed"
    assert record["proof"]["outcome"] == "passed"
    assert record["proof"]["detectedFormat"] == "binary-stl"
    assert record["proof"]["fullRouteCompleted"] is False
    assert record["proof"]["toolpathGenerated"] is False
    assert report_path.is_file() and log_path.is_file() and proof_path.is_file()
    assert record["proof"]["report"]["sha256"] == hashlib.sha256(report_path.read_bytes()).hexdigest()
    assert record["proof"]["executionLog"]["sha256"] == hashlib.sha256(log_path.read_bytes()).hexdigest()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["triangleCount"] == 1
    assert all(report["checks"].values())
    assert [event["eventType"] for event in completed["audit"]["events"]] == [
        "request-created", "authorization-recorded", "execution-started",
        "execution-completed", "proof-recorded",
    ]
    assert str(data_root) not in json.dumps(completed)
    assert all(value is False for value in record["safety"].values())


def test_invalid_stl_finishes_failed_with_honest_proof_not_fake_toolpath(tmp_path: Path) -> None:
    """Purpose: Invalid bytes produce failed proof rather than success or fake G-code.

    Inputs: Authorized ``.stl`` metadata containing non-STL bytes.
    Outputs: Failed terminal record, failed report/proof, and no toolpath artifact.
    How it works: Runs the same real stream/hash path then inspects failed checks.
    Side effects: Writes pytest-owned failed report, log, proof, and audit.
    Failure behavior: Success claims or generated G-code fail assertions.
    Safety: Failure remains contained and opens or launches nothing.
    Example: Detected format is unknown and structureConsistent is false.
    Related proof: Failed-result schema and execution honesty boundaries.
    """

    service, intake, data_root = build_service(tmp_path, content=b"not an stl payload")
    execution = service.authorize(authorization_payload(intake["id"]), request_context())["record"]
    result = service.run(execution["id"], request_context())
    root = data_root / "executions" / execution["id"]

    assert result["claimState"] == "failed"
    assert result["record"]["lifecycle"]["state"] == "failed"
    assert result["record"]["proof"]["outcome"] == "failed"
    assert result["record"]["proof"]["detectedFormat"] == "unknown"
    assert not list(root.rglob("*.gcode"))
    assert result["audit"]["events"][-2]["outcome"] == "failed"


def test_cancel_before_run_is_observed_without_process_signal_or_outputs(tmp_path: Path) -> None:
    """Purpose: Pre-start cancellation reaches terminal state with no process/output claim.

    Inputs: One authorized but not started contained execution.
    Outputs: Cancelled blocked record, observed control state, and cancel audit.
    How it works: Calls cancel before run and inspects private output directory.
    Side effects: Replaces pytest-owned control/record and appends one audit event.
    Failure behavior: Any process signal, proof, or output file fails assertions.
    Safety: Cooperative cancellation is not described as a stopped process.
    Example: Audit contains request, authorization, then cancellation.
    Related proof: Execution cancellation schema and API behavior.
    """

    service, intake, data_root = build_service(tmp_path)
    execution = service.authorize(authorization_payload(intake["id"]), request_context())["record"]
    result = service.cancel(execution["id"], request_context())
    output_root = data_root / "executions" / execution["id"] / "outputs"

    assert result["claimState"] == "blocked"
    assert result["record"]["lifecycle"]["state"] == "cancelled"
    assert result["cancellation"]["state"] == "observed"
    assert result["cancellation"]["processSignalSent"] is False
    assert result["record"]["proof"] is None
    assert list(output_root.iterdir()) == []
    assert result["audit"]["events"][-1]["eventType"] == "execution-cancelled"
    with pytest.raises(ContainedExecutionError, match="terminal"):
        service.run(execution["id"], request_context())


def test_inflight_chunk_hook_requests_cooperative_cancellation(tmp_path: Path) -> None:
    """Purpose: Running execution observes control-file cancellation between chunks.

    Inputs: Large valid-size payload and test hook that invokes cancel after first chunk.
    Outputs: Cancelled execution with start/cancel audits and no report/proof.
    How it works: Hook uses the real guarded cancel method while run owns the slot.
    Side effects: Writes only isolated source/control/audit/state files.
    Failure behavior: Continued output generation or missing observation fails.
    Safety: Test sends no thread/process signal and production has no hook.
    Example: Cancellation is checked immediately after each 1 MiB read.
    Related proof: Cooperative cancellation loop implementation.
    """

    holder: dict[str, object] = {}

    def cancel_after_chunk(execution_id: str, processed: int) -> None:
        """Purpose: Request cancellation once after the first streamed source chunk.

        Inputs: Generated execution id and processed byte count from test hook.
        Outputs: ``None`` after at most one real cancellation request.
        How it works: Uses holder service/context and marks itself called.
        Side effects: Writes isolated cancellation state through production code.
        Failure behavior: Service rejection fails the enclosing run test.
        Safety: Receives no source bytes or private path and sends no process signal.
        Example: First call above zero requests cancellation; later calls do nothing.
        Related proof: In-flight assertion below.
        """

        if processed > 0 and not holder.get("called"):
            holder["called"] = True
            holder["service"].cancel(execution_id, request_context())  # type: ignore[union-attr]

    content = b"solid test\n" + (b"facet normal 0 0 0\n" * 70000) + b"endsolid test\n"
    service, intake, data_root = build_service(tmp_path, content=content, chunk_hook=cancel_after_chunk)
    holder["service"] = service
    execution = service.authorize(authorization_payload(intake["id"]), request_context())["record"]
    result = service.run(execution["id"], request_context())

    assert holder["called"] is True
    assert result["record"]["lifecycle"]["state"] == "cancelled"
    assert result["cancellation"]["state"] == "observed"
    assert [event["eventType"] for event in result["audit"]["events"]][-2:] == ["execution-started", "execution-cancelled"]
    assert list((data_root / "executions" / execution["id"] / "outputs").iterdir()) == []


def test_authorization_rejects_duplicate_scope_and_bad_guard_without_leaking_paths(tmp_path: Path) -> None:
    """Purpose: Guard, scope, uniqueness, and privacy checks precede execution.

    Inputs: One authorized intake plus wrong token, route, and duplicate attempts.
    Outputs: Stable rejections and one path-redacted catalog record only.
    How it works: Calls authorization with focused invalid payloads then valid duplicate.
    Side effects: Creates one isolated execution for the first valid authorization.
    Failure behavior: Acceptance or path leakage fails assertions.
    Safety: Invalid requests never read arbitrary paths or start work.
    Example: Reusing an intake returns conflict instead of a second workspace.
    Related proof: Request guard, scope, and idempotency boundaries.
    """

    service, intake, data_root = build_service(tmp_path)
    payload = authorization_payload(intake["id"])
    with pytest.raises(ValueError):
        service.authorize(payload, request_context(request_token="wrong"))
    with pytest.raises(ContainedExecutionError) as missing_source_error:
        service.authorize({**payload, "intakeId": None}, request_context())
    assert missing_source_error.value.code == "execution_source_rejected"
    wrong_scope = {**payload, "operationId": "slice-now"}
    with pytest.raises(ContainedExecutionError) as scope_error:
        service.authorize(wrong_scope, request_context())
    assert scope_error.value.code == "execution_scope_rejected"
    service.authorize(payload, request_context())
    with pytest.raises(ContainedExecutionError) as duplicate_error:
        service.authorize(payload, request_context())
    assert duplicate_error.value.status == 409
    catalog = service.catalog()
    assert catalog["summary"]["executionCount"] == 1
    assert str(data_root) not in json.dumps(catalog)
    assert catalog["actions"]["openOutput"]["enabledInApi"] is False
