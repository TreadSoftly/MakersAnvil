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
    """Purpose: Truth states allowed in product code and user-facing state records.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ClaimState`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: A closed enum prevents optimistic or invented truth labels.
    Example: Construct with ``instance = ClaimState(...)`` using values described by ``__init__``.
    Related proof: ``schemas/claim-state.schema.json`` and verifier schema checks.
    """

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
    """Purpose: Return whether a string is an approved Makers Anvil claim state.

    Inputs: Caller-supplied ``value`` values from the signature.
    Outputs: Returns ``bool``, or raises before returning when validation fails.
    How it works: It returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: A closed enum prevents optimistic or invented truth labels.
    Example: Call ``result = instance.is_claim_state(...)`` with values satisfying the documented inputs.
    Related proof: ``schemas/claim-state.schema.json`` and verifier schema checks.
    """

    return value in ALLOWED_CLAIM_STATES
