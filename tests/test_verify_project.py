"""Purpose: Prove the canonical project verifier succeeds end to end.

Used by: Developers and CI as the final repository-governance regression.
Inputs: The complete current product checkout.
Outputs: An assertion that every verifier gate returns success.
Side effects: Verifier reads files and uses isolated temporary data only.
Safety: One test cannot bypass a failed schema, purity, or explanation gate.
Failure behavior: Any verifier error fails this test and exposes its output.
Related proof: ``scripts/verify_project.py`` and CI workflow.
"""

from scripts import verify_project


def test_project_verifier_passes() -> None:
    """The same verifier used by developers and CI must return a success code."""

    assert verify_project.main() == 0
