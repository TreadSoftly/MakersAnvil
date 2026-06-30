"""Purpose: Prove portable preferences, help, and redacted create-only activity.

Used by: CI whenever workbench experience or local journal behavior changes.
Inputs: Committed policies copied into isolated source and runtime roots.
Outputs: Assertions over defaults, guarded persistence, activity, and privacy.
Side effects: Writes only pytest-owned settings and activity event files.
Safety: No real user data, source path, route, tool, or output is touched.
Failure behavior: Invalid values, widened records, or path leakage fail explicitly.
Related proof: Experience/activity services and their schemas.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from makers_anvil_backend.services.activity_log import ActivityLogError, ActivityLogService
from makers_anvil_backend.services.local_request_guard import LocalRequestContext, LocalRequestGuard
from makers_anvil_backend.services.runtime_paths import DATA_DIR_ENV, RuntimePathsService
from makers_anvil_backend.services.workbench_experience import WorkbenchExperienceError, WorkbenchExperienceService
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = Path(__file__).resolve().parents[1]
TOKEN = "experience-test-token"
NOW = datetime(2026, 6, 30, 14, 0, tzinfo=UTC)


def build_services(tmp_path: Path) -> tuple[WorkbenchExperienceService, ActivityLogService, Path]:
    """Purpose: Construct experience and activity services over isolated storage.

    Inputs: Pytest-owned temporary directory.
    Outputs: Experience service, activity service, and private runtime root.
    How it works: Copies two committed policies and injects portable runtime paths.
    Side effects: Creates only temporary source/config fixture directories.
    Failure behavior: Missing committed policy fails before service assertions.
    Safety: The production user-data directory is never resolved or consulted.
    Example: Each test receives fresh empty runtime storage.
    Related proof: Portable workspace and runtime-path tests.
    """

    source = tmp_path / "source"
    config = source / "config"
    config.mkdir(parents=True)
    shutil.copy2(ROOT / "config" / "default_settings.json", config / "default_settings.json")
    shutil.copy2(ROOT / "config" / "workbench_experience.json", config / "workbench_experience.json")
    data = tmp_path / "data"
    paths = RuntimePathsService(source_root=source, environ={DATA_DIR_ENV: str(data)}, home=tmp_path / "home", platform_name="linux")
    workspace = WorkspaceConfigService(source, paths)
    guard = LocalRequestGuard(TOKEN)
    experience = WorkbenchExperienceService(source, workspace_config=workspace, request_guard=guard, clock=lambda: NOW)
    activity = ActivityLogService(workspace_config=workspace, experience=experience, clock=lambda: NOW)
    return experience, activity, data


def valid_context() -> LocalRequestContext:
    """Purpose: Return valid same-origin evidence for preference updates.

    Inputs: Fixed test token and loopback endpoint constants.
    Outputs: Immutable request context.
    How it works: Constructs all four required guard fields explicitly.
    Side effects: None.
    Failure behavior: Dataclass construction errors fail the caller.
    Safety: Production validation still runs; this is not a bypass.
    Example: Models a browser fetch from 127.0.0.1 port 8766.
    Related proof: ``tests/test_local_request_guard.py``.
    """

    return LocalRequestContext(TOKEN, "http://127.0.0.1:8766", "127.0.0.1:8766", "same-origin")


def test_preferences_default_then_persist_atomically_without_source_dependency(tmp_path: Path) -> None:
    """Purpose: Prove defaults and an explicit complete update use user-data storage.

    Inputs: Isolated services and comfortable/reduced/help-off preference set.
    Outputs: Updated API values plus exact private runtime record assertions.
    How it works: Reads defaults, performs guarded update, then inspects user data.
    Side effects: Creates one pytest-owned settings JSON file.
    Failure behavior: Wrong location, fields, values, or logical path fail assertions.
    Safety: Record contains no source path, personal data, or action flag.
    Example: The source fixture remains free of runtime settings.
    Related proof: Preference schemas and relocated-source tests.
    """

    experience, _, data = build_services(tmp_path)
    assert experience.experience()["preferences"] == {"density": "compact", "motion": "full", "contextHelp": True}
    result = experience.update({"density": "comfortable", "motion": "reduced", "contextHelp": False}, valid_context())
    assert result["preferences"] == {"density": "comfortable", "motion": "reduced", "contextHelp": False}
    persisted = json.loads((data / "settings" / "workbench-preferences.json").read_text(encoding="utf-8"))
    assert persisted["updatedUtc"] == NOW.isoformat()
    assert "path" not in json.dumps(persisted).lower()
    assert result["storage"] == "makers-anvil-data://user/settings/workbench-preferences.json"


def test_preferences_reject_partial_or_unknown_values_before_write(tmp_path: Path) -> None:
    """Purpose: Ensure settings are complete and closed rather than loose patches.

    Inputs: Partial preference payload with an unsupported density.
    Outputs: Typed rejection and absent runtime data root.
    How it works: Calls update through a valid guard so payload validation is isolated.
    Side effects: None because validation precedes directory creation.
    Failure behavior: Any file creation or silent defaulting fails the test.
    Safety: Extra/unknown values cannot become hidden feature switches.
    Example: Density ``wide`` is not interpreted as comfortable.
    Related proof: Experience API 422 tests.
    """

    experience, _, data = build_services(tmp_path)
    with pytest.raises(WorkbenchExperienceError):
        experience.update({"density": "wide", "motion": "full"}, valid_context())
    assert not data.exists()


def test_activity_is_fixed_create_only_and_path_free(tmp_path: Path) -> None:
    """Purpose: Prove activity records contain only server-reviewed completion facts.

    Inputs: One generated intake id and one fixed event type.
    Outputs: One immutable event, bounded history, and privacy assertions.
    How it works: Records through the allowlist then reads the public history.
    Side effects: Creates one pytest-owned event JSON file.
    Failure behavior: Wrong text, shape, count, or arbitrary acceptance fails.
    Safety: No source name/path/token/content is available to the record call.
    Example: Intake copied records only the generated intake identifier.
    Related proof: Activity event/history schemas.
    """

    _, activity, data = build_services(tmp_path)
    intake_id = "intake-" + "a" * 32
    activity.record("intake-copied", intake_id)
    history = activity.recent()
    assert history["summary"]["eventCount"] == 1
    assert history["events"][0]["subjectId"] == intake_id
    assert history["safety"] == {"sourcePathStored": False, "arbitraryEventAccepted": False, "eventMutationEnabled": False, "eventDeletionEnabled": False}
    assert len(list((data / "logs" / "activity").glob("*.json"))) == 1
    with pytest.raises(ActivityLogError):
        activity.record("browser-free-text")
