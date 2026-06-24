"""Purpose: Define the finite truth vocabulary used by APIs and the UI.

Used by: Every service that labels evidence as proven, staged, or blocked.
Inputs: Internal enum construction and serialization requests.
Outputs: Stable string values matching ``claim-state.schema.json``.
Side effects: None.
Safety: A closed enum prevents optimistic or invented truth labels.
Failure behavior: Unknown values raise normal enum conversion errors.
Related proof: ``schemas/claim-state.schema.json`` and verifier schema checks.
"""

from __future__ import annotations

from enum import StrEnum


class ClaimState(StrEnum):
    """Truth states allowed in product code and user-facing state records."""

    PROVEN = "proven"
    DETECTED = "detected"
    STAGED = "staged"
    PREVIEW_ONLY = "preview-only"
    PLANNED = "planned"
    BLOCKED = "blocked"
    FAILED = "failed"
    UNKNOWN = "unknown"
    NOT_PROVEN = "not proven"


ALLOWED_CLAIM_STATES: tuple[str, ...] = tuple(state.value for state in ClaimState)


def is_claim_state(value: str) -> bool:
    """Return whether a string is an approved Makers Anvil claim state."""

    return value in ALLOWED_CLAIM_STATES
