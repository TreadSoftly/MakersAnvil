"""Purpose: Expose the installable Makers Anvil backend package.

Used by: Python importers, the development launcher, and the HTTP server.
Inputs: Package imports only; this module accepts no user or runtime data.
Outputs: The package version and public package identity.
Side effects: None. Importing the package must never start the server.
Safety: Keep package import independent of personal paths and machine state.
Failure behavior: Import errors are allowed to surface instead of being hidden.
Related proof: ``tests/test_api.py`` and ``scripts/verify_project.py``.
"""

__all__ = ["__version__"]

__version__ = "0.1.0"
