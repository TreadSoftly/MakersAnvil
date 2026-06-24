"""Detect known maker tools without executing them or exposing install paths."""

from __future__ import annotations

import json
import os
import shutil
import sys
from collections.abc import Callable, Iterable
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
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


class ToolDetectionError(ValueError):
    """Raised when tool definitions weaken containment, privacy, or action gates."""


class ToolDetectionService:
    """Check PATH and narrow standard locations while returning path-redacted evidence."""

    def __init__(
        self,
        root: Path | None = None,
        platform_name: str | None = None,
        environ: dict[str, str] | None = None,
        path_lookup: PathLookup | None = None,
        glob_lookup: GlobLookup | None = None,
    ) -> None:
        """Capture platform and lookup adapters without executing any detected command."""

        self.root = root or ROOT
        self.platform_name = self._normalize_platform(platform_name or sys.platform)
        self.environ = dict(os.environ if environ is None else environ)
        self.path_lookup = path_lookup or (lambda command, path: shutil.which(command, path=path))
        self.glob_lookup = glob_lookup or (lambda provider_root, pattern: provider_root.glob(pattern))
        self.catalog_path = self.root / "config" / "tool_catalog.json"

    def tool_catalog(self) -> dict[str, Any]:
        """Load and validate tool definitions, candidate containment, and safety flags."""

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
        """Return path-redacted presence results and keep all tool actions blocked."""

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
        """Return one tool result without retaining or returning a resolved path."""

        match: dict[str, Any] | None = None
        for command in tool["pathCommands"].get(self.platform_name, []):
            resolved = self.path_lookup(command, self.environ.get("PATH"))
            if resolved:
                match = {
                    "method": "path-command",
                    "candidateId": f"path-command:{command}",
                    "executableName": Path(resolved).name,
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
                    }
                    break

        installed = match is not None
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
            "version": {
                "claimState": "not proven",
                "value": None,
                "commandExecuted": False,
            },
            "actionsEnabled": False,
        }

    def _provider_root(self, provider: dict[str, Any]) -> Path | None:
        """Resolve a private provider root for checking without exposing it publicly."""

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
        """Require unique platform providers with exactly one valid root source."""

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
        """Reject ambiguous tools, command paths, and uncontained candidate patterns."""

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
        """Map Python platform names to the catalog's closed platform vocabulary."""

        normalized = platform_name.lower()
        if normalized.startswith("win"):
            return "windows"
        if normalized.startswith("darwin") or normalized.startswith("mac"):
            return "macos"
        if normalized.startswith("linux"):
            return "linux"
        return "unknown"
