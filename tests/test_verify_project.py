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
    """Purpose: The same verifier used by developers and CI must return a success code.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: One test cannot bypass a failed schema, purity, or explanation gate.
    Example: Run ``python -m pytest tests/test_verify_project.py -k test_project_verifier_passes``.
    Related proof: ``scripts/verify_project.py`` and CI workflow.
    """

    assert verify_project.main() == 0
