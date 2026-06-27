"""Purpose: Resolve private app-data locations without exposing personal paths.

Used by: Workspace, intake, job, launcher, API, and relocation behavior.
Inputs: Platform identity, environment variables, and optional absolute override.
Outputs: Private resolved paths plus a separate redacted public location record.
Side effects: None; resolution alone never creates directories.
Safety: Runtime storage cannot depend on the source checkout or current directory.
Failure behavior: Relative or unsafe overrides raise ``ValueError``.
Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[4]
DATA_DIR_ENV = "MAKERS_ANVIL_DATA_DIR"
LOGICAL_DATA_ROOT = "makers-anvil-data://user"


class RuntimePathError(ValueError):
    """Purpose: Raised when a runtime path would depend on an unsafe or ambiguous location.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``RuntimePathError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Runtime storage cannot depend on the source checkout or current directory.
    Example: Construct with ``instance = RuntimePathError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
    """


@dataclass(frozen=True)
class RuntimeLocation:
    """Purpose: Resolved private location plus safe public metadata.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``RuntimeLocation`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Runtime storage cannot depend on the source checkout or current directory.
    Example: Construct with ``instance = RuntimeLocation(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
    """

    root: Path
    provider: str
    label: str
    override_used: bool


class RuntimePathsService:
    """Purpose: Resolve app data independently from the source checkout or working directory.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``RuntimePathsService`` exposing the state and operations defined below.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Runtime storage cannot depend on the source checkout or current directory.
    Example: Construct with ``instance = RuntimePathsService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
    """

    def __init__(
        self,
        source_root: Path | None = None,
        environ: Mapping[str, str] | None = None,
        home: Path | None = None,
        platform_name: str | None = None,
    ) -> None:
        """Purpose: Capture injected platform inputs so path behavior is deterministic and testable.

        Inputs: Caller-supplied ``source_root``, ``environ``, ``home``, ``platform_name`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It checks conditions.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        self.source_root = (source_root or ROOT).resolve()
        self.environ = dict(os.environ if environ is None else environ)
        self.home = (home or Path.home()).resolve()
        self.platform_name = platform_name or sys.platform

    def location(self) -> RuntimeLocation:
        """Purpose: Resolve the private data root from an override or OS convention.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``RuntimeLocation``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Call ``result = instance.location(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        override = self.environ.get(DATA_DIR_ENV)
        if override:
            # Overrides must be absolute so moving the current working
            # directory cannot silently redirect user data.
            root = self._absolute_path(override, DATA_DIR_ENV)
            return RuntimeLocation(root, "environment-override", "Environment override", True)

        # Each default follows the host operating system's per-user data
        # convention. Vendor scoping avoids collisions with unrelated apps.
        if self.platform_name.startswith("win"):
            local_app_data = self.environ.get("LOCALAPPDATA")
            base = self._absolute_path(local_app_data, "LOCALAPPDATA") if local_app_data else self.home / "AppData" / "Local"
            return RuntimeLocation(
                (base / "TreadSoftly" / "MakersAnvil").resolve(),
                "windows-local-app-data",
                "Windows local app data",
                False,
            )

        if self.platform_name == "darwin":
            return RuntimeLocation(
                (self.home / "Library" / "Application Support" / "TreadSoftly" / "MakersAnvil").resolve(),
                "macos-application-support",
                "macOS Application Support",
                False,
            )

        xdg_data_home = self.environ.get("XDG_DATA_HOME")
        if xdg_data_home:
            base = self._absolute_path(xdg_data_home, "XDG_DATA_HOME")
        else:
            base = self.home / ".local" / "share"
        return RuntimeLocation(
            (base / "treadsoftly" / "makers-anvil").resolve(),
            "linux-xdg-data",
            "Linux XDG data",
            False,
        )

    def public_info(self) -> dict[str, object]:
        """Purpose: Return location metadata that deliberately omits the resolved filesystem path.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, object]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Call ``result = instance.public_info(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        location = self.location()
        return {
            "schemaVersion": "makers-anvil.runtime-location.v1",
            "mode": "platform-user-data",
            "provider": location.provider,
            "label": location.label,
            "logicalRoot": LOGICAL_DATA_ROOT,
            "environmentOverride": DATA_DIR_ENV,
            "environmentOverrideUsed": location.override_used,
            "sourceRootDependency": False,
            "absolutePathExposed": False,
        }

    def data_path(self, relative_path: str | Path) -> Path:
        """Purpose: Resolve one contained child path and reject absolute or escaping input.

        Inputs: Caller-supplied ``relative_path`` values from the signature.
        Outputs: Returns ``Path``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Call ``result = instance.data_path(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        candidate = Path(relative_path)
        if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts:
            raise RuntimePathError("runtime data path must be relative and contained")
        root = self.location().root
        target = (root / candidate).resolve()
        if root != target and root not in target.parents:
            raise RuntimePathError("runtime data path escapes the app-owned user-data directory")
        return target

    def logical_path(self, relative_path: str | Path) -> str:
        """Purpose: Return a stable API-safe identifier for a contained runtime child path.

        Inputs: Caller-supplied ``relative_path`` values from the signature.
        Outputs: Returns ``str``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Call ``result = instance.logical_path(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        candidate = Path(relative_path)
        self.data_path(candidate)
        return f"{LOGICAL_DATA_ROOT}/{candidate.as_posix()}"

    def _absolute_path(self, value: str, variable_name: str) -> Path:
        """Purpose: Expand and validate an explicit override before returning its resolved path.

        Inputs: Caller-supplied ``value``, ``variable_name`` values from the signature.
        Outputs: Returns ``Path``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Runtime storage cannot depend on the source checkout or current directory.
        Example: Call ``result = instance._absolute_path(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_runtime_paths.py`` and runtime-location schema.
        """

        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            raise RuntimePathError(f"{variable_name} must be an absolute path")
        return candidate.resolve()
