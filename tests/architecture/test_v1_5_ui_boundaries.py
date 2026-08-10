from pathlib import Path


def test_application_capture_primitive_has_no_ui_dependency() -> None:
    source = Path("src/codexbar/application/account_presentation.py").read_text()
    assert "codexbar.ui" not in source


def test_presentation_does_not_read_repositories_directly() -> None:
    source = Path("src/codexbar/ui/current_account_viewmodel.py").read_text()
    assert "Sqlite" not in source
    assert "SettingsRepository" not in source
    assert "ResetEventRepository" not in source
