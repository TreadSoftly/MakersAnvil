"""Purpose: Group shared Makers Anvil domain vocabulary and truth states.

Used by: Services, API composition, schemas, and tests.
Inputs: Package imports only.
Outputs: A stable namespace for domain contracts.
Side effects: None.
Safety: Domain vocabulary must not depend on UI labels or personal state.
Failure behavior: Invalid imports surface directly.
Related proof: ``tests/test_api.py`` and claim-state schema validation.
"""
