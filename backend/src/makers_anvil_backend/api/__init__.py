"""Purpose: Mark the package that owns Makers Anvil's HTTP-style API facade.

Used by: The loopback server and backend composition tests.
Inputs: Package imports only.
Outputs: A namespace for API boundary components.
Side effects: None.
Safety: Business rules remain in services and mutation remains blocked here.
Failure behavior: Import failures surface to the caller.
Related proof: ``tests/test_api.py``.
"""
