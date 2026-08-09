from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codexbar.application.settings import (
    GetSettings,
    ResetSettings,
    SaveSettings,
    SettingsRepository,
)
from codexbar.domain.errors import SettingsError
from codexbar.domain.models import Fraction
from codexbar.domain.settings import AppSettings, RefreshIntervalSeconds


@dataclass(frozen=True, slots=True)
class SettingsActions:
    repository: SettingsRepository
    apply: Callable[[AppSettings], None]

    def save(self, settings: AppSettings) -> None:
        SaveSettings(self.repository).execute(settings)
        self.apply(settings)

    def reset(self) -> AppSettings:
        ResetSettings(self.repository).execute()
        settings = GetSettings(self.repository).execute().settings
        self.apply(settings)
        return settings


class SettingsDialog(QDialog):
    def __init__(
        self,
        settings: AppSettings,
        actions: SettingsActions,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._actions = actions
        self.setWindowTitle("CodexBar Settings")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.low_threshold_input = QLineEdit(self)
        self.low_threshold_input.setPlaceholderText("0.20")
        form.addRow("LOW remaining threshold:", self.low_threshold_input)

        self.refresh_interval_input = QLineEdit(self)
        self.refresh_interval_input.setPlaceholderText("60")
        form.addRow("Refresh interval (seconds):", self.refresh_interval_input)

        self.notifications_checkbox = QCheckBox("Enable notifications", self)
        form.addRow("", self.notifications_checkbox)
        layout.addLayout(form)

        self.error_label = QLabel("", self)
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #b00020;")
        layout.addWidget(self.error_label)

        controls = QHBoxLayout()
        self.reset_button = QPushButton("Reset", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.save_button = QPushButton("Save", self)
        controls.addWidget(self.reset_button)
        controls.addStretch(1)
        controls.addWidget(self.cancel_button)
        controls.addWidget(self.save_button)
        layout.addLayout(controls)

        self.reset_button.clicked.connect(self._reset)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save)

        self._set_fields(settings)

    def _set_fields(self, settings: AppSettings) -> None:
        self.low_threshold_input.setText(str(settings.low_remaining_threshold.value))
        self.refresh_interval_input.setText(str(settings.refresh_interval_seconds.value))
        self.notifications_checkbox.setChecked(settings.notifications_enabled)

    def _candidate_settings(self) -> AppSettings:
        threshold_text = self.low_threshold_input.text().strip()
        try:
            threshold = Decimal(threshold_text)
        except InvalidOperation as exc:
            raise ValueError(
                "LOW remaining threshold must be a decimal fraction between 0 and 1"
            ) from exc

        refresh_text = self.refresh_interval_input.text().strip()
        try:
            refresh_seconds = int(refresh_text)
        except ValueError as exc:
            raise ValueError("refresh interval must be an integer number of seconds") from exc

        return AppSettings(
            low_remaining_threshold=Fraction(threshold),
            refresh_interval_seconds=RefreshIntervalSeconds(refresh_seconds),
            notifications_enabled=self.notifications_checkbox.isChecked(),
        )

    def _save(self) -> None:
        try:
            settings = self._candidate_settings()
            self._actions.save(settings)
        except (SettingsError, ValueError) as exc:
            self.error_label.setText(str(exc))
            return

        self.error_label.clear()
        self.accept()

    def _reset(self) -> None:
        try:
            settings = self._actions.reset()
        except SettingsError as exc:
            self.error_label.setText(str(exc))
            return

        self._set_fields(settings)
        self.error_label.clear()
