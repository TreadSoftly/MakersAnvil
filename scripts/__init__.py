"""Purpose: Make verified local entrypoints importable by the test suite.

Used by: Tests and repository tooling that reuse script functions.
Inputs: Package imports only.
Outputs: A side-effect-free script namespace.
Side effects: None; importing scripts must never run a command.
Safety: Executable behavior stays behind each script's ``main`` guard.
Failure behavior: Import errors surface directly.
Related proof: ``tests/test_verify_project.py``.
"""
