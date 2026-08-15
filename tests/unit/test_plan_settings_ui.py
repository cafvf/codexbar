from __future__ import annotations

import os
from datetime import timedelta
from decimal import Decimal

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QWidget  # noqa: E402

from codexbar.application.settings import SettingsLoadResult, SettingsOrigin  # noqa: E402
from codexbar.domain.models import Fraction, UsageWindowId  # noqa: E402
from codexbar.domain.quantities import TimeToReset  # noqa: E402
from codexbar.domain.settings import (  # noqa: E402
    AppSettings,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)
from codexbar.ui.settings import SettingsActions, SettingsDialog  # noqa: E402


class FakeRepository:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.saved: AppSettings | None = None
        self.resets = 0

    def load(self) -> SettingsLoadResult:
        return SettingsLoadResult(self.settings, SettingsOrigin.PERSISTED, source_schema_version=3)

    def save(self, settings: AppSettings) -> None:
        self.settings = settings
        self.saved = settings

    def reset(self) -> None:
        self.resets += 1
        self.settings = AppSettings.defaults()
        self.saved = None


class CurrentWindowsParent(QWidget):
    def __init__(
        self,
        windows: tuple[tuple[UsageWindowId, str], ...],
    ) -> None:
        super().__init__()
        self._windows = windows

    def current_usage_windows(self) -> tuple[tuple[UsageWindowId, str], ...]:
        return self._windows


def _checkpoint(
    window_id: UsageWindowId,
    seconds: int,
    minimum: str,
) -> UsagePlanCheckpoint:
    return UsagePlanCheckpoint(
        window_id,
        TimeToReset(timedelta(seconds=seconds)),
        Fraction(Decimal(minimum)),
    )


def _settings_with_current_and_absent_policy() -> tuple[
    AppSettings,
    UsageWindowId,
    UsageWindowId,
]:
    current = UsageWindowId("opaque-current")
    absent = UsageWindowId("opaque-absent")
    settings = AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.17")),
        refresh_interval_seconds=AppSettings.defaults().refresh_interval_seconds,
        notifications_enabled=False,
        usage_reserves=UsageReservePolicy(
            (
                UsageReserve(current, Fraction(Decimal("0.20"))),
                UsageReserve(absent, Fraction(Decimal("0.10"))),
            )
        ),
        usage_plan_checkpoints=UsagePlanCheckpointPolicy(
            (
                _checkpoint(current, 259_200, "0.55"),
                _checkpoint(absent, 86_400, "0.35"),
            )
        ),
        plan_breach_notifications_enabled=True,
    )
    return settings, current, absent


def test_plan_editor_loads_only_current_windows_with_typed_checkpoint_rows() -> None:
    app = QApplication.instance() or QApplication([])
    settings, current, absent = _settings_with_current_and_absent_policy()
    repository = FakeRepository(settings)
    parent = CurrentWindowsParent(((current, "Current window"),))
    dialog = SettingsDialog(
        settings,
        SettingsActions(repository, lambda _: None),
        parent,
    )

    assert dialog.plan_notifications_checkbox.isChecked() is True
    assert len(dialog.checkpoint_editors) == 1
    editor = dialog.checkpoint_editors[0]
    assert editor.window_id == current
    assert len(editor.rows) == 1
    assert editor.rows[0].seconds_input.value() == 259_200
    assert editor.rows[0].minimum_input.text() == "0.55"
    assert all(item.window_id != absent for item in dialog.checkpoint_editors)

    dialog.close()
    parent.close()
    app.processEvents()


def test_plan_editor_save_preserves_absent_window_policies_and_unedited_fields() -> None:
    app = QApplication.instance() or QApplication([])
    settings, current, absent = _settings_with_current_and_absent_policy()
    repository = FakeRepository(settings)
    applied: list[AppSettings] = []
    parent = CurrentWindowsParent(((current, "Current window"),))
    dialog = SettingsDialog(
        settings,
        SettingsActions(repository, applied.append),
        parent,
    )
    editor = dialog.checkpoint_editors[0]

    editor.add_button.click()
    app.processEvents()
    assert len(editor.rows) == 2
    editor.rows[1].seconds_input.setValue(86_400)
    editor.rows[1].minimum_input.setText("0.40")
    dialog.plan_notifications_checkbox.setChecked(False)
    dialog.save_button.click()
    app.processEvents()

    saved = repository.saved
    assert saved is not None
    assert saved.low_remaining_threshold == settings.low_remaining_threshold
    assert saved.refresh_interval_seconds == settings.refresh_interval_seconds
    assert saved.notifications_enabled == settings.notifications_enabled
    assert saved.usage_reserves.reserve_for(absent) == Fraction(Decimal("0.10"))
    assert saved.usage_plan_checkpoints.checkpoints_for(absent) == (
        _checkpoint(absent, 86_400, "0.35"),
    )
    assert saved.usage_plan_checkpoints.checkpoints_for(current) == (
        _checkpoint(current, 259_200, "0.55"),
        _checkpoint(current, 86_400, "0.40"),
    )
    assert saved.plan_breach_notifications_enabled is False
    assert applied == [saved]

    parent.close()
    app.processEvents()


def test_plan_editor_remove_deletes_only_current_window_checkpoint_policy() -> None:
    app = QApplication.instance() or QApplication([])
    settings, current, absent = _settings_with_current_and_absent_policy()
    repository = FakeRepository(settings)
    parent = CurrentWindowsParent(((current, "Current window"),))
    dialog = SettingsDialog(
        settings,
        SettingsActions(repository, lambda _: None),
        parent,
    )
    editor = dialog.checkpoint_editors[0]

    editor.rows[0].remove_button.click()
    app.processEvents()
    assert editor.rows == []

    dialog.save_button.click()
    app.processEvents()

    saved = repository.saved
    assert saved is not None
    assert saved.usage_plan_checkpoints.checkpoints_for(current) == ()
    assert saved.usage_plan_checkpoints.checkpoints_for(absent) == (
        _checkpoint(absent, 86_400, "0.35"),
    )

    parent.close()
    app.processEvents()


def test_plan_editor_duplicate_coordinate_validation_keeps_dialog_open() -> None:
    app = QApplication.instance() or QApplication([])
    current = UsageWindowId("opaque-current")
    settings = AppSettings.defaults()
    repository = FakeRepository(settings)
    parent = CurrentWindowsParent(((current, "Current window"),))
    dialog = SettingsDialog(
        settings,
        SettingsActions(repository, lambda _: None),
        parent,
    )
    dialog.show()
    editor = dialog.checkpoint_editors[0]

    for minimum in ("0.55", "0.40"):
        editor.add_button.click()
        row = editor.rows[-1]
        row.seconds_input.setValue(259_200)
        row.minimum_input.setText(minimum)

    dialog.save_button.click()
    app.processEvents()

    assert repository.saved is None
    assert "unique" in dialog.error_label.text()
    assert dialog.isVisible() is True

    dialog.close()
    parent.close()
    app.processEvents()


def test_plan_editor_reset_clears_rows_and_plan_opt_in() -> None:
    app = QApplication.instance() or QApplication([])
    settings, current, _absent = _settings_with_current_and_absent_policy()
    repository = FakeRepository(settings)
    applied: list[AppSettings] = []
    parent = CurrentWindowsParent(((current, "Current window"),))
    dialog = SettingsDialog(
        settings,
        SettingsActions(repository, applied.append),
        parent,
    )

    dialog.reset_button.click()
    app.processEvents()

    assert repository.resets == 1
    assert dialog.plan_notifications_checkbox.isChecked() is False
    assert dialog.checkpoint_editors[0].rows == []
    assert applied == [AppSettings.defaults()]

    dialog.close()
    parent.close()
    app.processEvents()
