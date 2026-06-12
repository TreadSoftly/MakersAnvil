"""Durable workspace status records for Makers Anvil."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]


class WorkspaceStatusService:
    """Read committed status records without depending on reference folders."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or ROOT
        self.status_path = self.root / "state" / "current_status.json"
        self.ledger_path = self.root / "state" / "pass_ledger.json"

    def current_status(self) -> dict[str, Any]:
        return self._read_json(self.status_path)

    def pass_ledger(self) -> dict[str, Any]:
        return self._read_json(self.ledger_path)

    def workspace_status(self) -> dict[str, Any]:
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
        return json.loads(path.read_text(encoding="utf-8"))
