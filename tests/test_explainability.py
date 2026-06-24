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
    """Every tracked or pending product file has exactly one detailed explanation."""

    assert check_explainability.check_manifest_coverage() == []


def test_python_and_frontend_explanation_gates_pass() -> None:
    """All Python components and frontend functions retain durable explanations."""

    assert check_explainability.check_python_docstrings() == []
    assert check_explainability.check_javascript_function_comments() == []
    assert check_explainability.check_text_file_headers() == []
