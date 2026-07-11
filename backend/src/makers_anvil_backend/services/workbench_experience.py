"""Purpose: Provide schema-backed help and portable workbench preferences.

Used by: App state, the settings API, and the frontend experience controller.
Inputs: Committed experience policy, guarded preference payloads, and user-data paths.
Outputs: Path-redacted help/preferences contracts for the local workbench.
Side effects: Explicit updates atomically replace one app-owned preference file.
Safety: No source path, personal data, route, tool, output, or software action is stored.
Failure behavior: Invalid policy, payload, guard evidence, or runtime records fail closed.
Related proof: ``tests/test_workbench_experience.py`` and experience schemas.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4

from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.local_request_guard import LocalRequestContext, LocalRequestGuard
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


PREFERENCE_FIELDS = {"density", "motion", "contextHelp"}
SAFETY_FIELDS = {
    "sourcePathStored", "personalDataStored", "arbitraryEventAccepted",
    "routeExecutionEnabled", "toolLaunchEnabled", "outputOpenEnabled", "softwareChangeEnabled",
}


class WorkbenchExperienceError(ValueError):
    """Purpose: Reject invalid workbench policy or preference records explicitly.

    Inputs: A reviewed diagnostic describing one invalid invariant.
    Outputs: A typed ``ValueError`` caught at the API boundary when appropriate.
    How it works: Uses standard exception message storage without normalization.
    Side effects: None.
    Failure behavior: The caller receives no partially accepted setting.
    Safety: Diagnostics describe schema fields, never private runtime locations.
    Example: Unknown density ``wide`` is rejected before any file write.
    Related proof: ``tests/test_workbench_experience.py``.
    """


class WorkbenchExperienceService:
    """Purpose: Own contextual help and three portable presentation preferences.

    Inputs: App root, portable workspace config, shared request guard, and clock.
    Outputs: Current experience contract and atomic preference update response.
    How it works: Validates committed policy, overlays one strict runtime record.
    Side effects: Update creates only ``settings/workbench-preferences.json``.
    Failure behavior: Unknown fields/options and malformed disk records fail closed.
    Safety: Preferences cannot enable maker actions or expose resolved paths.
    Example: User chooses comfortable density and reduced motion from Settings.
    Related proof: ``tests/test_workbench_experience.py``.
    """

    def __init__(
        self,
        root: Path | None = None,
        *,
        workspace_config: WorkspaceConfigService | None = None,
        request_guard: LocalRequestGuard | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        """Purpose: Bind policy, portable storage, guard, and deterministic clock.

        Inputs: Optional application root and injectable focused dependencies.
        Outputs: Initialized service; constructors return ``None``.
        How it works: Resolves source policy only and keeps runtime paths private.
        Side effects: None; the runtime directory is created only during update.
        Failure behavior: Dependency construction errors propagate immediately.
        Safety: The source root selects policy, never the user-data destination.
        Example: Tests inject a temporary ``WorkspaceConfigService``.
        Related proof: Construction and portable-root tests.
        """

        self.root = (root or application_root()).resolve()
        self.workspace_config = workspace_config or WorkspaceConfigService(self.root)
        self.request_guard = request_guard or LocalRequestGuard()
        self.clock = clock or (lambda: datetime.now(UTC))
        self.policy_path = self.root / "config" / "workbench_experience.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load and strictly validate the committed experience policy.

        Inputs: UTF-8 JSON at ``config/workbench_experience.json``.
        Outputs: Validated policy mapping used by all public methods.
        How it works: Checks exact top-level shape, options, help ids, and safety.
        Side effects: Reads one committed file.
        Failure behavior: Malformed or permissive policy raises an explicit error.
        Safety: Every dangerous capability flag must remain exactly false.
        Example: Duplicate help ids or traversal runtime paths are rejected.
        Related proof: Policy mutation tests and JSON schema verification.
        """

        value = json.loads(self.policy_path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or set(value) != {"schemaVersion", "claimState", "preferences", "helpTopics", "activity", "safety"}:
            raise WorkbenchExperienceError("workbench experience policy has an unsupported shape")
        if value["schemaVersion"] != "makers-anvil.config.workbench-experience.v1" or value["claimState"] != "staged":
            raise WorkbenchExperienceError("workbench experience policy identity is invalid")
        preferences = value["preferences"]
        if not isinstance(preferences, dict) or set(preferences) != {"defaults", "densityOptions", "motionOptions", "runtimeFile"}:
            raise WorkbenchExperienceError("workbench preference policy shape is invalid")
        if preferences["densityOptions"] != ["compact", "comfortable"] or preferences["motionOptions"] != ["full", "reduced"]:
            raise WorkbenchExperienceError("workbench preference options are invalid")
        self._validate_preferences(preferences["defaults"], preferences)
        runtime_file = Path(preferences["runtimeFile"])
        if runtime_file.is_absolute() or ".." in runtime_file.parts or runtime_file.as_posix() != "settings/workbench-preferences.json":
            raise WorkbenchExperienceError("workbench preference file must stay in app-owned settings")
        topics = value["helpTopics"]
        if not isinstance(topics, list) or not topics or len({item.get("id") for item in topics if isinstance(item, dict)}) != len(topics):
            raise WorkbenchExperienceError("workbench help topics must be non-empty and unique")
        if not all(isinstance(item, dict) and set(item) == {"id", "title", "summary", "boundary"} and all(isinstance(item[key], str) and item[key] for key in item) for item in topics):
            raise WorkbenchExperienceError("workbench help topics are invalid")
        activity = value["activity"]
        if not isinstance(activity, dict) or set(activity) != {"directory", "recentLimit", "allowedEventTypes"}:
            raise WorkbenchExperienceError("workbench activity policy shape is invalid")
        if activity["directory"] != "logs/activity" or activity["recentLimit"] != 30 or activity["allowedEventTypes"] != ["intake-authorized", "intake-copied", "preferences-updated"]:
            raise WorkbenchExperienceError("workbench activity policy is invalid")
        if not isinstance(value["safety"], dict) or set(value["safety"]) != SAFETY_FIELDS or any(flag is not False for flag in value["safety"].values()):
            raise WorkbenchExperienceError("workbench experience safety flags cannot enable actions")
        return value

    def experience(self) -> dict[str, Any]:
        """Purpose: Return current preferences, help, and honest mutation boundary.

        Inputs: Validated policy plus optional app-owned runtime preference record.
        Outputs: Path-redacted ``makers-anvil.api.workbench-experience.v1`` record.
        How it works: Uses defaults until a strict persisted record exists.
        Side effects: Reads policy and at most one user-data JSON file.
        Failure behavior: Invalid persisted data raises instead of silently guessing.
        Safety: Exposes a logical storage identifier but no resolved filesystem path.
        Example: First run reports compact/full/help-enabled defaults.
        Related proof: Experience API and schema tests.
        """

        policy = self.policy()
        preferences = self._read_preferences(policy)
        return {
            "schemaVersion": "makers-anvil.api.workbench-experience.v1",
            "claimState": "staged",
            "preferences": preferences,
            "options": {"density": policy["preferences"]["densityOptions"], "motion": policy["preferences"]["motionOptions"]},
            "helpTopics": policy["helpTopics"],
            "storage": self.workspace_config.logical_runtime_path(policy["preferences"]["runtimeFile"]),
            "updateAction": {"enabledInApi": True, "endpoint": "/api/workbench/experience", "explicitAuthorizationRequired": True},
            "safety": policy["safety"],
        }

    def update(self, payload: dict[str, Any], context: LocalRequestContext) -> dict[str, Any]:
        """Purpose: Persist one complete explicitly authorized preference selection.

        Inputs: Exact three-field preference object and guarded local request context.
        Outputs: Fresh public experience contract after atomic replacement.
        How it works: Validates guard/options, writes a temporary file, then replaces.
        Side effects: Creates the app-owned settings directory and one JSON record.
        Failure behavior: Validation or I/O failure leaves the prior file unchanged.
        Safety: No partial patch, arbitrary key, HTML, path, or action flag is accepted.
        Example: ``{'density':'compact','motion':'reduced','contextHelp':true}``.
        Related proof: Update, rejection, and atomic persistence tests.
        """

        self.request_guard.validate(context)
        policy = self.policy()
        self._validate_preferences(payload, policy["preferences"])
        target = self.workspace_config.runtime_path(policy["preferences"]["runtimeFile"])
        target.parent.mkdir(parents=True, exist_ok=True)
        record = {"schemaVersion": "makers-anvil.runtime.workbench-preferences.v1", "claimState": "staged", **payload, "updatedUtc": self.clock().astimezone(UTC).isoformat()}
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return self.experience()

    def _read_preferences(self, policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Read one strict runtime record or return committed defaults.

        Inputs: Validated experience policy containing defaults and runtime filename.
        Outputs: Exactly density, motion, and contextHelp values.
        How it works: Checks exact runtime schema/fields before extracting preferences.
        Side effects: Reads one app-owned file when it exists.
        Failure behavior: Corrupt or extra runtime fields raise an explicit error.
        Safety: A manually edited file cannot inject action settings into the API.
        Example: Missing file returns a copy of policy defaults.
        Related proof: Runtime corruption and defaults tests.
        """

        target = self.workspace_config.runtime_path(policy["preferences"]["runtimeFile"])
        if not target.exists():
            return dict(policy["preferences"]["defaults"])
        value = json.loads(target.read_text(encoding="utf-8"))
        expected = {"schemaVersion", "claimState", "density", "motion", "contextHelp", "updatedUtc"}
        if not isinstance(value, dict) or set(value) != expected or value.get("schemaVersion") != "makers-anvil.runtime.workbench-preferences.v1" or value.get("claimState") != "staged" or not isinstance(value.get("updatedUtc"), str):
            raise WorkbenchExperienceError("persisted workbench preferences are invalid")
        result = {key: value[key] for key in PREFERENCE_FIELDS}
        self._validate_preferences(result, policy["preferences"])
        return result

    @staticmethod
    def _validate_preferences(payload: dict[str, Any], policy: dict[str, Any]) -> None:
        """Purpose: Enforce the exact closed workbench preference vocabulary.

        Inputs: Candidate three-field object and validated preference options.
        Outputs: ``None`` only for one complete valid preference set.
        How it works: Checks exact keys, closed string enums, and strict boolean type.
        Side effects: None.
        Failure behavior: Raises ``WorkbenchExperienceError`` before persistence.
        Safety: Extra keys cannot become undeclared settings or actions.
        Example: Integer ``1`` is not accepted as contextHelp ``true``.
        Related proof: Parameterized preference validation tests.
        """

        if not isinstance(payload, dict) or set(payload) != PREFERENCE_FIELDS:
            raise WorkbenchExperienceError("workbench preferences require exactly density, motion, and contextHelp")
        if payload["density"] not in policy["densityOptions"] or payload["motion"] not in policy["motionOptions"] or type(payload["contextHelp"]) is not bool:
            raise WorkbenchExperienceError("workbench preference values are invalid")


__all__ = ["WorkbenchExperienceError", "WorkbenchExperienceService"]
