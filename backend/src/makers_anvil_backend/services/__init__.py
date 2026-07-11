"""Purpose: Group focused services that own Makers Anvil behavior.

Used by: ``AppStateService``, local scripts, API composition, and tests.
Inputs: Package imports only.
Outputs: A namespace for service modules.
Side effects: None at package import time.
Safety: Each service owns one bounded responsibility and explicit effects.
Failure behavior: Import and policy errors surface to the calling boundary.
Related proof: Focused ``tests/test_*.py`` service suites.
"""
