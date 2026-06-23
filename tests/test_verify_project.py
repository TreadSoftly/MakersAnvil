"""End-to-end example proving the repository verifier remains green."""

from scripts import verify_project


def test_project_verifier_passes() -> None:
    """The same verifier used by developers and CI must return a success code."""

    assert verify_project.main() == 0
