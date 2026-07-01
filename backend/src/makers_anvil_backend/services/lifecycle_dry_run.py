"""Purpose: Build path-redacted backup, restore, update, uninstall, and repair previews.

Used by: ``AppStateService`` and read-only lifecycle API routes.
Inputs: Committed lifecycle policy, portable workspace settings, and app-owned metadata.
Outputs: Strict operation plans plus bounded counts and byte totals for app-owned data.
Side effects: Reads directory entries and file metadata only; writes and processes are forbidden.
Safety: No content/name/path exposure, archive access, network, installer, mutation, or deletion.
Failure behavior: Invalid policy, unsafe entries, or inaccessible metadata fails explicitly.
Related proof: ``tests/test_lifecycle_dry_run.py`` and lifecycle JSON schemas.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from makers_anvil_backend import __version__
from makers_anvil_backend.runtime_resources import application_root
from makers_anvil_backend.services.workspace_config import WorkspaceConfigService


ROOT = application_root()
OPERATION_IDS = ("backup", "restore", "update", "uninstall", "repair")
POLICY_FIELDS = {"schemaVersion", "claimState", "mode", "inventory", "operations", "actions", "safety"}
OPERATION_FIELDS = {"id", "label", "summary", "steps", "requiredEvidence", "blockers", "preservation"}
STEP_FIELDS = {"id", "label"}
EXPECTED_ACTIONS = {
    "previewEnabled": True,
    "backupExecutionEnabled": False,
    "restoreExecutionEnabled": False,
    "updateExecutionEnabled": False,
    "uninstallExecutionEnabled": False,
    "repairExecutionEnabled": False,
    "apiMutationEnabled": False,
    "browserMutationEnabled": False,
}
EXPECTED_SAFETY_KEYS = {
    "fileContentRead", "fileNameExposed", "privatePathExposed", "networkAccessEnabled",
    "archiveCreationEnabled", "archiveReadEnabled", "archiveExtractionEnabled", "restoreWriteEnabled",
    "packageDownloadEnabled", "installerExecutionEnabled", "softwareMutationEnabled",
    "userDataDeletionEnabled", "externalProcessEnabled",
}


class LifecycleDryRunError(ValueError):
    """Purpose: Reject lifecycle policy or inventory values outside the read-only contract.

    Inputs: Reviewed diagnostic describing the failed invariant.
    Outputs: Typed value error for API orchestration, verification, and tests.
    How it works: Preserves normal ``ValueError`` semantics without additional state.
    Side effects: None.
    Failure behavior: The caller receives no partial or widened lifecycle plan.
    Safety: Diagnostics name policy concepts and never include private paths or names.
    Example: A true installer flag raises ``LifecycleDryRunError``.
    Related proof: Policy weakening and inaccessible inventory tests.
    """


class LifecycleDryRunService:
    """Purpose: Compose five deterministic lifecycle previews from portable local truth.

    Inputs: Application root and shared portable workspace configuration.
    Outputs: Validated policy response, bounded inventory, and five non-executable plans.
    How it works: Validates closed policy, scans metadata without following links, then joins evidence.
    Side effects: Reads JSON, directory entries, and regular-file size metadata only.
    Failure behavior: Policy, containment, scan, or resource errors raise instead of guessing.
    Safety: Every lifecycle execution effect remains false and every public location is logical.
    Example: Backup preview reports source file count while archive creation stays blocked.
    Related proof: Lifecycle service, API, frontend, and package tests.
    """

    def __init__(
        self,
        root: Path | None = None,
        workspace_config: WorkspaceConfigService | None = None,
    ) -> None:
        """Purpose: Bind read-only bundled policy to one source-independent runtime root.

        Inputs: Optional application root and injected shared workspace service.
        Outputs: Initialized service; constructors return ``None``.
        How it works: Resolves policy location and stores the workspace dependency.
        Side effects: Resolves paths only and creates no runtime directory.
        Failure behavior: Invalid roots or dependencies surface when policy/catalog is read.
        Safety: The current working directory and reference app are never fallback inputs.
        Example: Tests inject temporary source and runtime roots.
        Related proof: Relocation and isolated lifecycle tests.
        """

        self.root = (root or ROOT).resolve()
        self.workspace_config = workspace_config or WorkspaceConfigService(root=self.root)
        self.policy_path = self.root / "config" / "lifecycle_dry_run_policy.json"

    def policy(self) -> dict[str, Any]:
        """Purpose: Load and strictly validate the complete lifecycle dry-run policy.

        Inputs: Committed lifecycle JSON at the application resource root.
        Outputs: Validated closed policy mapping.
        How it works: Checks identities, inventory, operation coverage, steps, actions, and safety.
        Side effects: Reads one bundled JSON file.
        Failure behavior: Missing, malformed, duplicate, weakened, or widened policy raises.
        Safety: Every executable action and side-effect flag is locked to false.
        Example: Exactly five operation ids must match ``OPERATION_IDS`` in order.
        Related proof: Policy contract and negative service tests.
        """

        try:
            value = json.loads(self.policy_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise LifecycleDryRunError("lifecycle dry-run policy is unavailable") from exc
        if not isinstance(value, dict) or set(value) != POLICY_FIELDS:
            raise LifecycleDryRunError("lifecycle dry-run policy shape is invalid")
        if value["schemaVersion"] != "makers-anvil.config.lifecycle-dry-run.v1" or value["claimState"] != "preview-only" or value["mode"] != "read-only-lifecycle-planning":
            raise LifecycleDryRunError("lifecycle dry-run policy identity is invalid")
        self._validate_inventory_policy(value["inventory"])
        self._validate_operations(value["operations"])
        if value["actions"] != EXPECTED_ACTIONS:
            raise LifecycleDryRunError("lifecycle dry-run actions are invalid")
        if not isinstance(value["safety"], dict) or set(value["safety"]) != EXPECTED_SAFETY_KEYS or any(value["safety"].values()):
            raise LifecycleDryRunError("lifecycle dry-run safety effects must remain false")
        return value

    def policy_response(self) -> dict[str, Any]:
        """Purpose: Expose the validated lifecycle scope and logical backup destination.

        Inputs: Valid committed lifecycle policy and workspace directory declarations.
        Outputs: Public policy with path-redacted logical location and disabled API action.
        How it works: Resolves the declared backup id through workspace settings only.
        Side effects: Reads policy and settings; creates nothing.
        Failure behavior: Missing backup declaration raises rather than inventing a target.
        Safety: Response contains no executable endpoint, command, filename, or private path.
        Example: Backup target is ``makers-anvil-data://user/backups``.
        Related proof: Policy API and path-privacy assertions.
        """

        policy = self.policy()
        directories = {item["id"]: item for item in self.workspace_config.settings()["directories"]}
        target_id = policy["inventory"]["backupTargetDirectoryId"]
        if target_id not in directories:
            raise LifecycleDryRunError("lifecycle backup target directory is undeclared")
        return {
            **policy,
            "backupTarget": self.workspace_config.logical_runtime_path(directories[target_id]["relativePath"]),
            "executionAction": {"claimState": "blocked", "enabledInApi": False},
        }

    def catalog(self) -> dict[str, Any]:
        """Purpose: Return five current lifecycle previews over one bounded metadata inventory.

        Inputs: Valid policy, app-owned directory metadata, and bundled core presence.
        Outputs: Path-redacted inventory, operation plans, summaries, actions, and safety.
        How it works: Scans declared source directories then attaches operation-specific evidence.
        Side effects: Reads directory entries, size metadata, and required resource existence only.
        Failure behavior: Unsafe/inaccessible entries are counted and lower inventory truth honestly.
        Safety: File content/names/paths and every lifecycle execution effect stay absent.
        Example: Restore preview can exist while selection, archive read, and writes remain blocked.
        Related proof: Inventory, deterministic-plan, no-write, and API consistency tests.
        """

        policy = self.policy()
        inventory = self._inventory(policy)
        core = self._bundled_core_evidence()
        plans = [self._plan(operation, inventory, core, policy) for operation in policy["operations"]]
        return {
            "schemaVersion": "makers-anvil.api.lifecycle-dry-run-catalog.v1",
            "claimState": "preview-only" if inventory["claimState"] != "failed" else "failed",
            "mode": policy["mode"],
            "summary": {
                "operationCount": len(plans),
                "previewReadyCount": sum(plan["readiness"]["previewReady"] for plan in plans),
                "executionReadyCount": sum(plan["readiness"]["executionReady"] for plan in plans),
                "sourceFileCount": inventory["summary"]["fileCount"],
                "sourceBytes": inventory["summary"]["totalBytes"],
            },
            "inventory": inventory,
            "bundledCore": core,
            "plans": plans,
            "actions": dict(policy["actions"]),
            "safety": dict(policy["safety"]),
        }

    @staticmethod
    def _validate_inventory_policy(value: Any) -> None:
        """Purpose: Lock metadata scanning to reviewed app-owned source and target ids.

        Inputs: Candidate inventory policy mapping.
        Outputs: ``None`` only for exact source, target, exclusion, and limit values.
        How it works: Compares closed field/value sets and validates the positive cap.
        Side effects: None.
        Failure behavior: Any extra, missing, duplicate, or broad value raises.
        Safety: Temporary and backup directories cannot enter their own backup source set.
        Example: Raising ``maxEntries`` without review fails strict equality checks in tests.
        Related proof: Inventory policy weakening tests.
        """

        expected_fields = {"sourceDirectoryIds", "backupTargetDirectoryId", "excludedDirectoryIds", "maxEntries"}
        if not isinstance(value, dict) or set(value) != expected_fields:
            raise LifecycleDryRunError("lifecycle inventory policy shape is invalid")
        if value["sourceDirectoryIds"] != ["settings", "intake", "jobs", "executions", "outputs", "logs"]:
            raise LifecycleDryRunError("lifecycle inventory source scope is invalid")
        if value["backupTargetDirectoryId"] != "backups" or value["excludedDirectoryIds"] != ["tmp", "backups"]:
            raise LifecycleDryRunError("lifecycle inventory target or exclusions are invalid")
        if not isinstance(value["maxEntries"], int) or isinstance(value["maxEntries"], bool) or value["maxEntries"] < 1 or value["maxEntries"] > 10000:
            raise LifecycleDryRunError("lifecycle inventory entry limit is invalid")

    @staticmethod
    def _validate_operations(value: Any) -> None:
        """Purpose: Require complete ordered lifecycle coverage and explanatory plan fields.

        Inputs: Candidate operation list from policy.
        Outputs: ``None`` only for five closed, unique, nonempty operation definitions.
        How it works: Validates ids/order, exact fields, step ids, text lists, and preservation.
        Side effects: None.
        Failure behavior: Duplicate/missing operations, steps, evidence, or blockers raise.
        Safety: Preservation must remain true and data deletion permission false.
        Example: An operation that allows deletion is rejected before inventory access.
        Related proof: Parameterized policy mutation tests.
        """

        if not isinstance(value, list) or [item.get("id") for item in value if isinstance(item, dict)] != list(OPERATION_IDS):
            raise LifecycleDryRunError("lifecycle operation coverage is invalid")
        for operation in value:
            if set(operation) != OPERATION_FIELDS or not all(isinstance(operation[field], str) and operation[field] for field in ("id", "label", "summary")):
                raise LifecycleDryRunError("lifecycle operation shape is invalid")
            steps = operation["steps"]
            if not isinstance(steps, list) or not steps or any(not isinstance(step, dict) or set(step) != STEP_FIELDS or not all(isinstance(step[field], str) and step[field] for field in STEP_FIELDS) for step in steps):
                raise LifecycleDryRunError("lifecycle operation steps are invalid")
            step_ids = [step["id"] for step in steps]
            if len(step_ids) != len(set(step_ids)):
                raise LifecycleDryRunError("lifecycle operation step ids must be unique")
            if any(not isinstance(items, list) or not items or any(not isinstance(item, str) or not item for item in items) for items in (operation["requiredEvidence"], operation["blockers"])):
                raise LifecycleDryRunError("lifecycle evidence or blockers are invalid")
            if operation["preservation"] != {"existingDataPreserved": True, "userDataDeletionAllowed": False}:
                raise LifecycleDryRunError("lifecycle preservation policy is invalid")

    def _inventory(self, policy: dict[str, Any]) -> dict[str, Any]:
        """Purpose: Count app-owned regular files and bytes without exposing names or contents.

        Inputs: Valid source-directory ids and maximum entry count.
        Outputs: Per-directory logical counts plus aggregate metadata and scan health.
        How it works: Uses non-following ``scandir`` recursion and ``stat`` size metadata.
        Side effects: Reads directory entries and file metadata only.
        Failure behavior: Inaccessible/unsupported entries are counted; traversal never follows links.
        Safety: No content opens, filename returns, private path returns, or directory creation occurs.
        Example: Two regular settings files produce count two and their summed byte size.
        Related proof: Empty/populated/capped/symlink/no-write inventory tests.
        """

        settings = self.workspace_config.settings()
        declarations = {item["id"]: item for item in settings["directories"]}
        source_ids = policy["inventory"]["sourceDirectoryIds"]
        if any(source_id not in declarations for source_id in source_ids):
            raise LifecycleDryRunError("lifecycle source directory is undeclared")
        remaining = policy["inventory"]["maxEntries"]
        records: list[dict[str, Any]] = []
        aggregate = {"fileCount": 0, "totalBytes": 0, "symbolicLinkCount": 0, "inaccessibleEntryCount": 0, "unsupportedEntryCount": 0}
        limit_reached = False
        for source_id in source_ids:
            declaration = declarations[source_id]
            path = self.workspace_config.runtime_path(declaration["relativePath"])
            result, remaining, reached = self._scan_directory(path, remaining)
            limit_reached = limit_reached or reached
            for key in aggregate:
                aggregate[key] += result[key]
            records.append({
                "id": source_id,
                "logicalPath": self.workspace_config.logical_runtime_path(declaration["relativePath"]),
                "exists": path.exists(),
                **result,
            })
        aggregate["directoryCount"] = len(records)
        aggregate["existingDirectoryCount"] = sum(record["exists"] for record in records)
        aggregate["scanLimitReached"] = limit_reached
        claim_state = "failed" if limit_reached or aggregate["inaccessibleEntryCount"] else "proven"
        return {
            "schemaVersion": "makers-anvil.api.lifecycle-inventory.v1",
            "claimState": claim_state,
            "contentRead": False,
            "namesExposed": False,
            "pathsExposed": False,
            "summary": aggregate,
            "directories": records,
        }

    @staticmethod
    def _scan_directory(path: Path, remaining: int) -> tuple[dict[str, int], int, bool]:
        """Purpose: Inspect one contained directory tree with a global entry budget.

        Inputs: Private app-owned directory path and remaining positive entry allowance.
        Outputs: Counts/bytes, unused allowance, and whether the cap stopped scanning.
        How it works: Iteratively scans entries, never follows symlinks, and stats files only.
        Side effects: Reads directory entries and metadata only.
        Failure behavior: Permission/I/O errors increment inaccessible count without path leakage.
        Safety: File contents and names never enter the returned mapping.
        Example: A symlink increments its count and is never traversed or stat-followed.
        Related proof: Capped inventory and symlink tests.
        """

        result = {"fileCount": 0, "totalBytes": 0, "symbolicLinkCount": 0, "inaccessibleEntryCount": 0, "unsupportedEntryCount": 0}
        if not path.exists():
            return result, remaining, False
        if path.is_symlink() or not path.is_dir():
            result["unsupportedEntryCount"] += 1
            return result, remaining, False
        stack = [path]
        while stack:
            current = stack.pop()
            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        if remaining == 0:
                            return result, remaining, True
                        remaining -= 1
                        try:
                            if entry.is_symlink():
                                result["symbolicLinkCount"] += 1
                            elif entry.is_dir(follow_symlinks=False):
                                stack.append(Path(entry.path))
                            elif entry.is_file(follow_symlinks=False):
                                result["fileCount"] += 1
                                result["totalBytes"] += entry.stat(follow_symlinks=False).st_size
                            else:
                                result["unsupportedEntryCount"] += 1
                        except OSError:
                            result["inaccessibleEntryCount"] += 1
            except OSError:
                result["inaccessibleEntryCount"] += 1
        return result, remaining, False

    def _bundled_core_evidence(self) -> dict[str, Any]:
        """Purpose: Check existence of the minimum bundled resources needed for repair planning.

        Inputs: Bound application resource root.
        Outputs: Required/available counts and proven-or-failed claim without private paths.
        How it works: Tests four fixed repository-relative files for regular-file presence.
        Side effects: Reads filesystem metadata only.
        Failure behavior: Missing resources lower the claim and remain visible as a count.
        Safety: No resource content, filename list, absolute path, or repair write is exposed.
        Example: A complete source or PyInstaller bundle reports four of four available.
        Related proof: Source and packaged lifecycle API smoke tests.
        """

        required = (
            Path("frontend/public/index.html"),
            Path("config/default_settings.json"),
            Path("state/current_status.json"),
            Path("schemas/app-state.schema.json"),
        )
        available = sum((self.root / relative).is_file() for relative in required)
        return {
            "claimState": "proven" if available == len(required) else "failed",
            "requiredResourceCount": len(required),
            "availableResourceCount": available,
            "contentRead": False,
            "privatePathExposed": False,
        }

    def _plan(
        self,
        operation: dict[str, Any],
        inventory: dict[str, Any],
        core: dict[str, Any],
        policy: dict[str, Any],
    ) -> dict[str, Any]:
        """Purpose: Join one policy operation with current path-redacted evidence.

        Inputs: Valid operation, inventory, bundled core evidence, and safety policy.
        Outputs: Deterministic non-executable plan with operation-specific current facts.
        How it works: Selects a closed evidence shape, marks steps planned, and copies blockers.
        Side effects: None.
        Failure behavior: Unknown operation ids raise rather than receiving generic evidence.
        Safety: Readiness execution is always false and every effect copies false policy flags.
        Example: Update evidence reports current version while release lookup remains false.
        Related proof: Exact five-plan and false-effect tests.
        """

        operation_id = operation["id"]
        if operation_id == "backup":
            evidence = {
                "inventoryObserved": inventory["claimState"] == "proven",
                "sourceFileCount": inventory["summary"]["fileCount"],
                "sourceBytes": inventory["summary"]["totalBytes"],
                "backupManifestCreated": False,
                "archiveCreated": False,
            }
        elif operation_id == "restore":
            evidence = {"backupSelected": False, "manifestVerified": False, "compatibilityVerified": False, "currentDataSnapshotted": False}
        elif operation_id == "update":
            evidence = {"currentVersion": __version__, "releaseMetadataChecked": False, "availableVersion": None, "updateAvailable": "not proven", "signatureVerified": False}
        elif operation_id == "uninstall":
            evidence = {"installerRegistrationChecked": False, "userConfirmationAccepted": False, "userDataDisposition": "preserve", "softwareRemoved": False}
        elif operation_id == "repair":
            evidence = {"bundledCoreClaimState": core["claimState"], "trustedPackageAvailable": False, "signatureVerified": False, "resourcesReplaced": False}
        else:
            raise LifecycleDryRunError("lifecycle operation id is unsupported")
        return {
            "id": f"lifecycle-dry-run-{operation_id}",
            "claimState": "preview-only",
            "operation": {"id": operation_id, "label": operation["label"], "summary": operation["summary"]},
            "currentEvidence": evidence,
            "steps": [{**step, "status": "planned"} for step in operation["steps"]],
            "requiredEvidence": list(operation["requiredEvidence"]),
            "readiness": {"previewReady": True, "executionReady": False, "blockers": list(operation["blockers"])},
            "preservation": dict(operation["preservation"]),
            "effects": dict(policy["safety"]),
            "executionAction": {"claimState": "blocked", "enabledInApi": False},
        }


__all__ = ["LifecycleDryRunError", "LifecycleDryRunService", "OPERATION_IDS"]
