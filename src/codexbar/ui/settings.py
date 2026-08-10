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
from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import (
    AppSettings,
    RefreshIntervalSeconds,
    UsageReserve,
    UsageReservePolicy,
)


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
        self.setMinimumWidth(380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.low_threshold_input = QLineEdit(self)
        self.low_threshold_input.setPlaceholderText("0.20")
        form.addRow("LOW remaining threshold:", self.low_threshold_input)

        self.refresh_interval_input = QLineEdit(self)
        self.refresh_interval_input.setPlaceholderText("60")
        form.addRow("Refresh interval (seconds):", self.refresh_interval_input)

        self.five_hour_reserve_input = QLineEdit(self)
        self.five_hour_reserve_input.setPlaceholderText("empty = no reserve")
        form.addRow("5h reserve:", self.five_hour_reserve_input)

        self.weekly_reserve_input = QLineEdit(self)
        self.weekly_reserve_input.setPlaceholderText("empty = no reserve")
        form.addRow("Weekly reserve:", self.weekly_reserve_input)

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
        self.five_hour_reserve_input.setText(
            _reserve_text(settings, UsageWindowId("window_300m"))
        )
        self.weekly_reserve_input.setText(
            _reserve_text(settings, UsageWindowId("window_10080m"))
        )

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

        reserves = UsageReservePolicy(
            tuple(
                entry
                for entry in (
                    _reserve_entry(
                        UsageWindowId("window_300m"),
                        self.five_hour_reserve_input.text(),
                    ),
                    _reserve_entry(
                        UsageWindowId("window_10080m"),
                        self.weekly_reserve_input.text(),
                    ),
                )
                if entry is not None
            )
        )
        return AppSettings(
            low_remaining_threshold=Fraction(threshold),
            refresh_interval_seconds=RefreshIntervalSeconds(refresh_seconds),
            notifications_enabled=self.notifications_checkbox.isChecked(),
            usage_reserves=reserves,
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


def _reserve_text(settings: AppSettings, window_id: UsageWindowId) -> str:
    reserve = settings.usage_reserves.reserve_for(window_id)
    return "" if reserve is None else str(reserve.value)


def _reserve_entry(window_id: UsageWindowId, text: str) -> UsageReserve | None:
    value = text.strip()
    if not value:
        return None
    try:
        return UsageReserve(window_id, Fraction(Decimal(value)))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid reserve for {window_id.value}") from exc
