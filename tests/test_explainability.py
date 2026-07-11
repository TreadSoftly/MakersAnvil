"""Purpose: Prove that source explanations are complete and machine-enforced.

Used by: Developers and CI after every source or documentation change.
Inputs: The tracked repository, source manifest, headers, comments, and guides.
Outputs: Assertions that the explainability checker reports no omissions.
Side effects: Reads repository metadata only.
Safety: Prevents passing builds whose implementation cannot be handed off.
Failure behavior: Missing structured context fails with actionable messages.
Related proof: ``scripts/check_explainability.py`` and explanation standard.
"""

from scripts import check_explainability


def test_every_product_file_has_a_current_manifest_entry() -> None:
    """Purpose: Every tracked or pending product file has exactly one detailed explanation.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents passing builds whose implementation cannot be handed off.
    Example: Run ``python -m pytest tests/test_explainability.py -k test_every_product_file_has_a_current_manifest_entry``.
    Related proof: ``scripts/check_explainability.py`` and explanation standard.
    """

    assert check_explainability.check_manifest_coverage() == []


def test_python_and_frontend_explanation_gates_pass() -> None:
    """Purpose: All Python components and frontend functions retain durable explanations.

    Inputs: No explicit parameters; the test builds its own isolated example state.
    Outputs: No application value; passing assertions prove the named behavior.
    How it works: It executes the focused statements in source order.
    Side effects: May create isolated temporary fixtures supplied by pytest; it must not change real user data.
    Failure behavior: A failed assertion identifies the exact behavior or safety contract that regressed.
    Safety: Prevents passing builds whose implementation cannot be handed off.
    Example: Run ``python -m pytest tests/test_explainability.py -k test_python_and_frontend_explanation_gates_pass``.
    Related proof: ``scripts/check_explainability.py`` and explanation standard.
    """

    assert check_explainability.check_python_docstrings() == []
    assert check_explainability.check_javascript_function_comments() == []
    assert check_explainability.check_frontend_block_comments() == []
    assert check_explainability.check_text_file_headers() == []
    assert check_explainability.check_learning_coverage() == []
