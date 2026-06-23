"""Executable examples for durable code and file explanation governance."""

from scripts import check_explainability


def test_every_product_file_has_a_current_manifest_entry() -> None:
    """Every tracked or pending product file has exactly one detailed explanation."""

    assert check_explainability.check_manifest_coverage() == []


def test_python_and_frontend_explanation_gates_pass() -> None:
    """Python docstrings and non-visible frontend purpose comments remain complete."""

    assert check_explainability.check_python_docstrings() == []
    assert check_explainability.check_text_file_headers() == []
