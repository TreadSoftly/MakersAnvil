"""Purpose: Read committed current-pass and pass-ledger product truth.

Used by: ``AppStateService`` and workspace status API routes.
Inputs: Repository ``state/current_status.json`` and ``state/pass_ledger.json``.
Outputs: Parsed status and historical pass dictionaries.
Side effects: None; committed truth files are read only.
Safety: Runtime observations do not overwrite durable build claims.
Failure behavior: Missing or malformed truth files raise explicit errors.
Related proof: ``tests/test_api.py`` and status schema validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


from makers_anvil_backend.runtime_resources import application_root


ROOT = application_root()


class WorkspaceStatusService:
    """Purpose: Read committed status records without depending on reference folders.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``WorkspaceStatusService`` exposing the state and operations defined below.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Runtime observations do not overwrite durable build claims.
    Example: Construct with ``instance = WorkspaceStatusService(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_api.py`` and status schema validation.
    """

    def __init__(self, root: Path | None = None) -> None:
        """Purpose: Bind the committed current-status and pass-ledger source files.

        Inputs: Caller-supplied ``root`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime observations do not overwrite durable build claims.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_api.py`` and status schema validation.
        """

        self.root = root or ROOT
        self.status_path = self.root / "state" / "current_status.json"
        self.ledger_path = self.root / "state" / "pass_ledger.json"

    def current_status(self) -> dict[str, Any]:
        """Purpose: Load the committed machine-readable current status record.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime observations do not overwrite durable build claims.
        Example: Call ``result = instance.current_status(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and status schema validation.
        """

        return self._read_json(self.status_path)

    def pass_ledger(self) -> dict[str, Any]:
        """Purpose: Load the committed ordered pass ledger.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime observations do not overwrite durable build claims.
        Example: Call ``result = instance.pass_ledger(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and status schema validation.
        """

        return self._read_json(self.ledger_path)

    def workspace_status(self) -> dict[str, Any]:
        """Purpose: Combine current status and ledger summary for the read-only API.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime observations do not overwrite durable build claims.
        Example: Call ``result = instance.workspace_status(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and status schema validation.
        """

        current = self.current_status()
        ledger = self.pass_ledger()
        return {
            "schemaVersion": "makers-anvil.api.workspace-status.v1",
            "claimState": current["claimState"],
            "product": current["product"],
            "currentPass": current["currentPass"],
            "trackPercentages": current["trackPercentages"],
            "sourceTruth": current["sourceTruth"],
            "referencePolicy": current["referencePolicy"],
            "passLedgerSummary": {
                "path": "state/pass_ledger.json",
                "passCount": len(ledger.get("passes", [])),
                "latestPassId": ledger.get("passes", [{}])[-1].get("id", "unknown"),
            },
            "nextPass": current["nextPass"],
        }

    def _read_json(self, path: Path) -> dict[str, Any]:
        """Purpose: Parse one trusted repository state file without mutating durable truth.

        Inputs: Caller-supplied ``path`` values from the signature.
        Outputs: Returns ``dict[str, Any]``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Runtime observations do not overwrite durable build claims.
        Example: Call ``result = instance._read_json(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and status schema validation.
        """

        return json.loads(path.read_text(encoding="utf-8"))
