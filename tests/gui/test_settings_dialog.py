import os
from decimal import Decimal

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QDialog  # noqa: E402

from codexbar.application.settings import SettingsLoadResult, SettingsOrigin  # noqa: E402
from codexbar.domain.models import Fraction  # noqa: E402
from codexbar.domain.settings import AppSettings, RefreshIntervalSeconds  # noqa: E402
from codexbar.ui.settings import SettingsActions, SettingsDialog  # noqa: E402


class FakeRepository:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.saved: AppSettings | None = None
        self.resets = 0

    def load(self) -> SettingsLoadResult:
        origin = SettingsOrigin.PERSISTED if self.saved is not None else SettingsOrigin.DEFAULTS
        return SettingsLoadResult(self.settings, origin)

    def save(self, settings: AppSettings) -> None:
        self.settings = settings
        self.saved = settings

    def reset(self) -> None:
        self.resets += 1
        self.settings = AppSettings.defaults()
        self.saved = None


def custom_settings() -> AppSettings:
    return AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.12")),
        refresh_interval_seconds=RefreshIntervalSeconds(180),
        notifications_enabled=False,
    )


def test_ac_settings_020_dialog_opens_with_effective_values() -> None:
    app = QApplication.instance() or QApplication([])
    settings = custom_settings()
    repository = FakeRepository(settings)
    dialog = SettingsDialog(settings, SettingsActions(repository, lambda _: None))

    assert dialog.low_threshold_input.text() == "0.12"
    assert dialog.refresh_interval_input.text() == "180"
    assert dialog.notifications_checkbox.isChecked() is False

    dialog.close()
    app.processEvents()


def test_ac_settings_021_save_persists_and_applies_runtime_settings() -> None:
    app = QApplication.instance() or QApplication([])
    repository = FakeRepository(AppSettings.defaults())
    applied: list[AppSettings] = []
    dialog = SettingsDialog(
        repository.settings,
        SettingsActions(repository, applied.append),
    )
    dialog.show()
    app.processEvents()

    dialog.low_threshold_input.setText("0.15")
    dialog.refresh_interval_input.setText("180")
    dialog.notifications_checkbox.setChecked(False)
    dialog.save_button.click()
    app.processEvents()

    expected = AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=RefreshIntervalSeconds(180),
        notifications_enabled=False,
    )
    assert repository.saved == expected
    assert applied == [expected]
    assert dialog.result() == QDialog.DialogCode.Accepted


def test_ac_settings_022_cancel_does_not_change_settings() -> None:
    app = QApplication.instance() or QApplication([])
    original = custom_settings()
    repository = FakeRepository(original)
    applied: list[AppSettings] = []
    dialog = SettingsDialog(original, SettingsActions(repository, applied.append))
    dialog.show()
    app.processEvents()

    dialog.low_threshold_input.setText("0.33")
    dialog.refresh_interval_input.setText("300")
    dialog.notifications_checkbox.setChecked(True)
    dialog.cancel_button.click()
    app.processEvents()

    assert repository.settings == original
    assert repository.saved is None
    assert applied == []
    assert dialog.result() == QDialog.DialogCode.Rejected


def test_ac_settings_023_reset_uses_shared_reset_use_case_and_applies_defaults() -> None:
    app = QApplication.instance() or QApplication([])
    repository = FakeRepository(custom_settings())
    applied: list[AppSettings] = []
    dialog = SettingsDialog(
        repository.settings,
        SettingsActions(repository, applied.append),
    )
    dialog.show()
    app.processEvents()

    dialog.reset_button.click()
    app.processEvents()

    defaults = AppSettings.defaults()
    assert repository.resets == 1
    assert repository.settings == defaults
    assert applied == [defaults]
    assert dialog.low_threshold_input.text() == "0.20"
    assert dialog.refresh_interval_input.text() == "60"
    assert dialog.notifications_checkbox.isChecked() is True
    assert dialog.isVisible() is True

    dialog.close()
    app.processEvents()


def test_ac_settings_024_validation_error_keeps_dialog_open_without_persisting() -> None:
    app = QApplication.instance() or QApplication([])
    repository = FakeRepository(AppSettings.defaults())
    applied: list[AppSettings] = []
    dialog = SettingsDialog(
        repository.settings,
        SettingsActions(repository, applied.append),
    )
    dialog.show()
    app.processEvents()

    dialog.low_threshold_input.setText("not-a-number")
    dialog.save_button.click()
    app.processEvents()

    assert repository.saved is None
    assert applied == []
    assert dialog.error_label.text()
    assert dialog.isVisible() is True
    assert dialog.result() != QDialog.DialogCode.Accepted

    dialog.close()
    app.processEvents()
