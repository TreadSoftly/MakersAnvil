from scripts import verify_project


def test_project_verifier_passes() -> None:
    assert verify_project.main() == 0
