"""Purpose: Report path-redacted presence and metadata version evidence for known maker tools.

Used by: ``AppStateService`` before semantic tool selection and dashboard render.
Inputs: Tool catalog, platform identity, PATH lookup, standard candidates, and metadata reader.
Outputs: Tool/family summaries with detection/version evidence but no resolved path.
Side effects: Filesystem and OS metadata reads only; no process or version command runs.
Safety: Detection cannot launch, install, update, repair, or expose private paths.
Failure behavior: Unknown platforms and missing tools remain not proven.
Related proof: ``tests/test_tool_detection.py`` and tool schemas.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.tool_version import ToolVersionEvidence, read_tool_version


ROOT = application_root()
PLATFORMS = {"windows", "macos", "linux"}
TOOL_SAFETY_FLAGS = {
    "processExecuted",
    "versionCommandExecuted",
    "registryRead",
    "filesystemWritten",
    "toolLaunched",
    "softwareChanged",
}
PathLookup = Callable[[str, str | None], str | None]
GlobLookup = Callable[[Path, str], Iterable[Path]]
VersionLookup = Callable[[Path, str], ToolVersionEvidence | None]
VERSION_EVIDENCE_METHODS = {"windows-version-resource", "macos-bundle-info"}
VERSION_VALUE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+\-]{0,63}$")


class ToolDetectionError(ValueError):
    """Purpose: Raised when tool definitions weaken containment, privacy, or action gates.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ToolDetectionError`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Detection cannot launch, install, update, repair, or expose private paths.
    Example: Construct with ``instance = ToolDetectionError(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_tool_detection.py`` and tool schemas.
    """


class ToolDetectionService:
    """Purpose: Check PATH and narrow standard locations while returning path-redacted evidence.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ToolDetectionService`` exposing the state and operations defined below.
    How it works: It checks conditions, then iterates over bounded records, then handles expected failures explicitly, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
    Safety: Detection cannot launch, install, update, repair, or expose private paths.
    Example: Construct with ``instance = ToolDetectionService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_tool_detection.py`` and tool schemas.
    """

    def __init__(
        self,
        root: Path | None = None,
        platform_name: str | None = None,
        environ: dict[str, str] | None = None,
        path_lookup: PathLookup | None = None,
        glob_lookup: GlobLookup | None = None,
        version_lookup: VersionLookup | None = None,
    ) -> None:
        """Purpose: Capture platform and lookup adapters without executing any detected command.

        Inputs: Caller-supplied root, platform, environment, path/glob adapters, and metadata version adapter.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It checks conditions.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        self.root = root or ROOT
        self.platform_name = self._normalize_platform(platform_name or sys.platform)
        self.environ = dict(os.environ if environ is None else environ)
        self.path_lookup = path_lookup or (lambda command, path: shutil.which(command, path=path))
        self.glob_lookup = glob_lookup or (lambda provider_root, pattern: provider_root.glob(pattern))
        self.version_lookup = version_lookup or read_tool_version
        self.catalog_path = self.root / "config" / "tool_catalog.json"

    def tool_catalog(self) -> dict[str, Any]:
        """Purpose: Load and validate tool definitions, candidate containment, and safety flags.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance.tool_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        catalog = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(catalog, dict):
            raise ToolDetectionError("tool catalog must be a structured record")
        if catalog.get("schemaVersion") != "makers-anvil.config.tool-catalog.v1":
            raise ToolDetectionError("tool catalog schema version is not supported")
        if catalog.get("mode") != "read-only-presence":
            raise ToolDetectionError("tool catalog must remain read-only presence detection")
        safety = catalog.get("safety")
        if not isinstance(safety, dict) or set(safety) != TOOL_SAFETY_FLAGS or any(value is not False for value in safety.values()):
            raise ToolDetectionError("tool catalog cannot execute, write, launch, or change software")

        providers = catalog.get("providers")
        tools = catalog.get("tools")
        if not isinstance(providers, list) or not providers or not all(isinstance(item, dict) for item in providers):
            raise ToolDetectionError("tool catalog requires provider definitions")
        if not isinstance(tools, list) or not tools or not all(isinstance(item, dict) for item in tools):
            raise ToolDetectionError("tool catalog requires tool definitions")
        provider_map = self._validate_providers(providers)
        self._validate_tools(tools, provider_map)
        return catalog

    def detection_catalog(self) -> dict[str, Any]:
        """Purpose: Return path-redacted presence results and keep all tool actions blocked.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance.detection_catalog(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        catalog = self.tool_catalog()
        providers = {provider["id"]: provider for provider in catalog["providers"]}
        tools = [self._detect_tool(tool, providers) for tool in catalog["tools"]]
        detected_count = sum(tool["detection"]["installed"] for tool in tools)
        families = sorted({family for tool in tools for family in tool["families"]})
        family_coverage = []
        for family in families:
            count = sum(tool["detection"]["installed"] and family in tool["families"] for tool in tools)
            family_coverage.append(
                {
                    "id": family,
                    "detectedToolCount": count,
                    "claimState": "detected" if count else "not proven",
                }
            )
        return {
            "schemaVersion": "makers-anvil.api.tool-detection.v1",
            "claimState": "detected" if detected_count else "not proven",
            "mode": catalog["mode"],
            "platform": {
                "id": self.platform_name,
                "claimState": "detected" if self.platform_name in PLATFORMS else "not proven",
            },
            "summary": {
                "toolCount": len(tools),
                "detectedCount": detected_count,
                "notDetectedCount": len(tools) - detected_count,
            },
            "familyCoverage": family_coverage,
            "tools": tools,
            "safety": catalog["safety"],
            "actions": {
                action: {"claimState": "blocked", "enabledInApi": False}
                for action in ("launch", "install", "update", "uninstall", "repair")
            },
        }

    def _detect_tool(
        self,
        tool: dict[str, Any],
        providers: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Purpose: Return one tool result after private metadata proof and path redaction.

        Inputs: Caller-supplied ``tool``, ``providers`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: Detects one private target, reads metadata, then emits only closed public fields.
        Side effects: Reads bounded file metadata through the injected adapter; starts no process.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance._detect_tool(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        match: dict[str, Any] | None = None
        for command in tool["pathCommands"].get(self.platform_name, []):
            resolved = self.path_lookup(command, self.environ.get("PATH"))
            if resolved:
                match = {
                    "method": "path-command",
                    "candidateId": f"path-command:{command}",
                    "executableName": Path(resolved).name,
                    "resolvedPath": Path(resolved),
                }
                break

        if match is None:
            for candidate in tool["candidates"]:
                if candidate["platform"] != self.platform_name:
                    continue
                provider_root = self._provider_root(providers[candidate["provider"]])
                if provider_root is None:
                    continue
                try:
                    matches = sorted(self.glob_lookup(provider_root, candidate["pattern"]), key=lambda path: str(path))
                except OSError:
                    matches = []
                installed = next((path for path in matches if path.is_file()), None)
                if installed is not None:
                    match = {
                        "method": "standard-location",
                        "candidateId": candidate["id"],
                        "executableName": installed.name,
                        "resolvedPath": installed,
                    }
                    break

        installed = match is not None
        version = self._version_evidence(match["resolvedPath"] if match else None)
        return {
            "id": tool["id"],
            "label": tool["label"],
            "publisher": tool["publisher"],
            "families": list(tool["families"]),
            "claimState": "detected" if installed else "not proven",
            "detection": {
                "installed": installed,
                "method": match["method"] if match else "none",
                "candidateId": match["candidateId"] if match else None,
                "executableName": match["executableName"] if match else None,
                "absolutePathExposed": False,
            },
            "version": version,
            "actionsEnabled": False,
        }

    def _version_evidence(self, resolved_path: Path | None) -> dict[str, Any]:
        """Purpose: Convert private OS metadata into one closed path-free version contract.

        Inputs: Privately resolved allowlisted executable path or ``None``.
        Outputs: Proven file/product versions or an explicit not-proven record.
        How it works: Calls the metadata adapter and validates every returned key/value.
        Side effects: The default adapter may read PE or app-bundle metadata only.
        Failure behavior: Missing, unreadable, malformed, or unsupported evidence stays not proven.
        Safety: The public result cannot expose a path, run a command, or imply publisher trust.
        Example: A PE product version yields a proven value with ``commandExecuted: false``.
        Related proof: ``tests/test_tool_detection.py`` and ``tests/test_tool_version.py``.
        """

        not_proven = {
            "claimState": "not proven",
            "value": None,
            "fileVersion": None,
            "productVersion": None,
            "evidenceMethod": "none",
            "commandExecuted": False,
            "absolutePathExposed": False,
        }
        if resolved_path is None:
            return not_proven
        try:
            evidence = self.version_lookup(resolved_path, self.platform_name)
        except (OSError, ValueError):
            return not_proven
        required = {"value", "fileVersion", "productVersion", "evidenceMethod"}
        if not isinstance(evidence, dict) or set(evidence) != required:
            return not_proven
        if evidence.get("evidenceMethod") not in VERSION_EVIDENCE_METHODS:
            return not_proven
        if any(
            not isinstance(evidence.get(field), str) or not VERSION_VALUE.fullmatch(evidence[field])
            for field in ("value", "fileVersion", "productVersion")
        ):
            return not_proven
        return {
            "claimState": "proven",
            **evidence,
            "commandExecuted": False,
            "absolutePathExposed": False,
        }

    def _provider_root(self, provider: dict[str, Any]) -> Path | None:
        """Purpose: Resolve a private provider root for checking without exposing it publicly.

        Inputs: Caller-supplied ``provider`` values from the signature.
        Outputs: Returns ``Path | None``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance._provider_root(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        if provider["platform"] != self.platform_name:
            return None
        raw_root = (
            self.environ.get(provider["environmentVariable"], "")
            if provider["rootKind"] == "environment"
            else provider["fixedRoot"]
        )
        if not raw_root:
            return None
        root = Path(raw_root).expanduser()
        return root if root.is_absolute() else None

    @staticmethod
    def _validate_providers(providers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        """Purpose: Require unique platform providers with exactly one valid root source.

        Inputs: Caller-supplied ``providers`` values from the signature.
        Outputs: Returns ``dict[str, dict[str, Any]]``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance._validate_providers(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        provider_map: dict[str, dict[str, Any]] = {}
        for provider in providers:
            provider_id = provider.get("id")
            platform = provider.get("platform")
            root_kind = provider.get("rootKind")
            if not isinstance(provider_id, str) or not provider_id or provider_id in provider_map:
                raise ToolDetectionError("provider ids must be non-empty and unique")
            if platform not in PLATFORMS or root_kind not in {"environment", "fixed"}:
                raise ToolDetectionError("providers require a supported platform and root kind")
            if root_kind == "environment":
                if not isinstance(provider.get("environmentVariable"), str) or provider.get("fixedRoot") is not None:
                    raise ToolDetectionError("environment providers require only an environment variable")
            else:
                fixed_root = provider.get("fixedRoot")
                root_path = (
                    PureWindowsPath(fixed_root)
                    if isinstance(fixed_root, str) and platform == "windows"
                    else PurePosixPath(fixed_root or "")
                )
                if not isinstance(fixed_root, str) or not root_path.is_absolute() or provider.get("environmentVariable") is not None:
                    raise ToolDetectionError("fixed providers require only an absolute fixed root")
            provider_map[provider_id] = provider
        return provider_map

    @staticmethod
    def _validate_tools(tools: list[dict[str, Any]], providers: dict[str, dict[str, Any]]) -> None:
        """Purpose: Reject ambiguous tools, command paths, and uncontained candidate patterns.

        Inputs: Caller-supplied ``tools``, ``providers`` values from the signature.
        Outputs: Returns ``None``, or raises before returning when validation fails.
        How it works: It checks conditions, then iterates over bounded records.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Raises the explicit errors shown in the body when inputs or invariants are invalid; callers must not treat failure as success.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance._validate_tools(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        tool_ids: set[str] = set()
        candidate_ids: set[str] = set()
        for tool in tools:
            if not all(isinstance(tool.get(field), str) and tool[field] for field in ("id", "label", "publisher")):
                raise ToolDetectionError("tools require ids, labels, and publishers")
            if tool["id"] in tool_ids:
                raise ToolDetectionError("tool ids must be unique")
            families = tool.get("families")
            commands = tool.get("pathCommands")
            candidates = tool.get("candidates")
            if not isinstance(families, list) or not families or len(set(families)) != len(families):
                raise ToolDetectionError("tool families must be non-empty and unique")
            if not isinstance(commands, dict) or set(commands) != PLATFORMS:
                raise ToolDetectionError("tool path commands must define every supported platform")
            for platform_commands in commands.values():
                if not isinstance(platform_commands, list) or any(
                    not isinstance(command, str) or not command or "/" in command or "\\" in command
                    for command in platform_commands
                ):
                    raise ToolDetectionError("PATH candidates must be executable names, not paths")
            if not isinstance(candidates, list) or not all(isinstance(item, dict) for item in candidates):
                raise ToolDetectionError("tool candidates must be structured records")
            for candidate in candidates:
                candidate_id = candidate.get("id")
                provider = providers.get(candidate.get("provider"))
                pattern = candidate.get("pattern")
                if not isinstance(candidate_id, str) or not candidate_id or candidate_id in candidate_ids:
                    raise ToolDetectionError("candidate ids must be non-empty and globally unique")
                if provider is None or candidate.get("platform") != provider["platform"]:
                    raise ToolDetectionError("candidate platform must match a known provider")
                pattern_path = PurePosixPath(pattern) if isinstance(pattern, str) else PurePosixPath("/")
                if pattern_path.is_absolute() or ".." in pattern_path.parts or not pattern_path.parts:
                    raise ToolDetectionError("candidate patterns must stay relative to provider roots")
                candidate_ids.add(candidate_id)
            tool_ids.add(tool["id"])

    @staticmethod
    def _normalize_platform(platform_name: str) -> str:
        """Purpose: Map Python platform names to the catalog's closed platform vocabulary.

        Inputs: Caller-supplied ``platform_name`` values from the signature.
        Outputs: Returns ``str``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Detection cannot launch, install, update, repair, or expose private paths.
        Example: Call ``result = instance._normalize_platform(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_tool_detection.py`` and tool schemas.
        """

        normalized = platform_name.lower()
        if normalized.startswith("win"):
            return "windows"
        if normalized.startswith("darwin") or normalized.startswith("mac"):
            return "macos"
        if normalized.startswith("linux"):
            return "linux"
        return "unknown"
