from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Protocol, cast

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
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
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.settings import (
    AppSettings,
    RefreshIntervalSeconds,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
    UsageReserve,
    UsageReservePolicy,
)


class CurrentWindowSource(Protocol):
    def current_usage_windows(self) -> tuple[tuple[UsageWindowId, str], ...]: ...


@dataclass(frozen=True, slots=True)
class ReserveField:
    window_id: UsageWindowId
    label: str
    input: QLineEdit


@dataclass(frozen=True, slots=True)
class CheckpointField:
    window_id: UsageWindowId
    container: QWidget
    seconds_input: QSpinBox
    minimum_input: QLineEdit
    remove_button: QPushButton


@dataclass(slots=True)
class CheckpointEditor:
    window_id: UsageWindowId
    label: str
    rows_layout: QVBoxLayout
    add_button: QPushButton
    rows: list[CheckpointField]


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
        self._reserve_fields: tuple[ReserveField, ...] = ()
        self._checkpoint_editors: tuple[CheckpointEditor, ...] = ()
        self.setWindowTitle("CodexBar Settings")
        self.setMinimumWidth(620)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.low_threshold_input = QLineEdit(self)
        self.low_threshold_input.setPlaceholderText("0.20")
        form.addRow("LOW remaining threshold:", self.low_threshold_input)

        self.refresh_interval_input = QLineEdit(self)
        self.refresh_interval_input.setPlaceholderText("60")
        form.addRow("Refresh interval (seconds):", self.refresh_interval_input)

        current_windows = _current_windows(parent)
        reserve_fields = []
        for window_id, label in current_windows:
            line_edit = QLineEdit(self)
            line_edit.setPlaceholderText("empty = no reserve")
            reserve_fields.append(ReserveField(window_id, label, line_edit))
            form.addRow(f"{label} reserve:", line_edit)
        self._reserve_fields = tuple(reserve_fields)

        if not self._reserve_fields:
            form.addRow(
                "Usage reserves:",
                QLabel("No current usage windows available to configure.", self),
            )

        self.notifications_checkbox = QCheckBox("Enable notifications", self)
        form.addRow("", self.notifications_checkbox)

        self.plan_notifications_checkbox = QCheckBox(
            "Enable Plan breach notifications",
            self,
        )
        form.addRow("", self.plan_notifications_checkbox)
        layout.addLayout(form)

        checkpoint_editors: list[CheckpointEditor] = []
        if current_windows:
            layout.addWidget(QLabel("Plan checkpoints", self))
            for window_id, label in current_windows:
                group = QGroupBox(label, self)
                group_layout = QVBoxLayout(group)
                rows_layout = QVBoxLayout()
                group_layout.addLayout(rows_layout)
                add_button = QPushButton("Add checkpoint", group)
                group_layout.addWidget(add_button)
                editor = CheckpointEditor(
                    window_id=window_id,
                    label=label,
                    rows_layout=rows_layout,
                    add_button=add_button,
                    rows=[],
                )
                checkpoint_editors.append(editor)

                def add_checkpoint(
                    _checked: bool = False,
                    current_editor: CheckpointEditor = editor,
                ) -> None:
                    self._add_checkpoint_row(current_editor)

                add_button.clicked.connect(add_checkpoint)
                layout.addWidget(group)
        else:
            layout.addWidget(
                QLabel(
                    "Plan checkpoints: no current usage windows available to configure.",
                    self,
                )
            )
        self._checkpoint_editors = tuple(checkpoint_editors)

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

    @property
    def reserve_fields(self) -> tuple[ReserveField, ...]:
        return self._reserve_fields

    @property
    def checkpoint_editors(self) -> tuple[CheckpointEditor, ...]:
        return self._checkpoint_editors

    def _set_fields(self, settings: AppSettings) -> None:
        self.low_threshold_input.setText(str(settings.low_remaining_threshold.value))
        self.refresh_interval_input.setText(str(settings.refresh_interval_seconds.value))
        self.notifications_checkbox.setChecked(settings.notifications_enabled)
        self.plan_notifications_checkbox.setChecked(
            settings.plan_breach_notifications_enabled
        )
        for field in self._reserve_fields:
            field.input.setText(_reserve_text(settings, field.window_id))
        for editor in self._checkpoint_editors:
            self._clear_checkpoint_rows(editor)
            for checkpoint in settings.usage_plan_checkpoints.checkpoints_for(
                editor.window_id
            ):
                self._add_checkpoint_row(editor, checkpoint)

    def _add_checkpoint_row(
        self,
        editor: CheckpointEditor,
        checkpoint: UsagePlanCheckpoint | None = None,
    ) -> None:
        container = QWidget(self)
        row_layout = QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)

        seconds_input = QSpinBox(container)
        seconds_input.setRange(0, 2_147_483_647)
        seconds_input.setSuffix(" s")
        seconds_input.setToolTip("Factual time remaining until reset, in whole seconds.")

        minimum_input = QLineEdit(container)
        minimum_input.setPlaceholderText("minimum remaining, e.g. 0.55")

        remove_button = QPushButton("Remove", container)

        row_layout.addWidget(QLabel("Time to reset:", container))
        row_layout.addWidget(seconds_input)
        row_layout.addWidget(QLabel("Minimum remaining:", container))
        row_layout.addWidget(minimum_input)
        row_layout.addWidget(remove_button)

        row = CheckpointField(
            window_id=editor.window_id,
            container=container,
            seconds_input=seconds_input,
            minimum_input=minimum_input,
            remove_button=remove_button,
        )
        editor.rows.append(row)
        editor.rows_layout.addWidget(container)

        if checkpoint is not None:
            seconds_input.setValue(_time_to_reset_seconds(checkpoint.time_to_reset))
            minimum_input.setText(str(checkpoint.minimum_remaining.value))

        def remove_checkpoint(
            _checked: bool = False,
            current_editor: CheckpointEditor = editor,
            current_row: CheckpointField = row,
        ) -> None:
            self._remove_checkpoint_row(current_editor, current_row)

        remove_button.clicked.connect(remove_checkpoint)

    def _remove_checkpoint_row(
        self,
        editor: CheckpointEditor,
        row: CheckpointField,
    ) -> None:
        if row not in editor.rows:
            return
        editor.rows.remove(row)
        editor.rows_layout.removeWidget(row.container)
        row.container.hide()
        row.container.deleteLater()

    def _clear_checkpoint_rows(self, editor: CheckpointEditor) -> None:
        for row in tuple(editor.rows):
            self._remove_checkpoint_row(editor, row)

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
            raise ValueError(
                "refresh interval must be an integer number of seconds"
            ) from exc

        existing = GetSettings(self._actions.repository).execute().settings
        current_ids = {
            field.window_id.value
            for field in self._reserve_fields
        }

        reserves = [
            entry
            for entry in existing.usage_reserves.entries
            if entry.window_id.value not in current_ids
        ]
        reserves.extend(
            entry
            for field in self._reserve_fields
            if (
                entry := _reserve_entry(
                    field.window_id,
                    field.input.text(),
                )
            )
            is not None
        )

        checkpoint_ids = {
            editor.window_id.value
            for editor in self._checkpoint_editors
        }
        checkpoints = [
            entry
            for entry in existing.usage_plan_checkpoints.entries
            if entry.window_id.value not in checkpoint_ids
        ]
        for editor in self._checkpoint_editors:
            checkpoints.extend(_checkpoint_entries(editor))

        return replace(
            existing,
            low_remaining_threshold=Fraction(threshold),
            refresh_interval_seconds=RefreshIntervalSeconds(refresh_seconds),
            notifications_enabled=self.notifications_checkbox.isChecked(),
            usage_reserves=UsageReservePolicy(
                tuple(
                    sorted(
                        reserves,
                        key=lambda item: item.window_id.value,
                    )
                )
            ),
            usage_plan_checkpoints=UsagePlanCheckpointPolicy(
                tuple(checkpoints)
            ),
            plan_breach_notifications_enabled=(
                self.plan_notifications_checkbox.isChecked()
            ),
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


def _current_windows(
    parent: QWidget | None,
) -> tuple[tuple[UsageWindowId, str], ...]:
    provider = getattr(parent, "current_usage_windows", None)
    if not callable(provider):
        return ()
    source = cast(CurrentWindowSource, parent)
    return source.current_usage_windows()


def _reserve_text(settings: AppSettings, window_id: UsageWindowId) -> str:
    reserve = settings.usage_reserves.reserve_for(window_id)
    return "" if reserve is None else str(reserve.value)


def _reserve_entry(
    window_id: UsageWindowId,
    text: str,
) -> UsageReserve | None:
    value = text.strip()
    if not value:
        return None
    try:
        return UsageReserve(window_id, Fraction(Decimal(value)))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid reserve for {window_id.value}") from exc


def _checkpoint_entries(
    editor: CheckpointEditor,
) -> tuple[UsagePlanCheckpoint, ...]:
    entries: list[UsagePlanCheckpoint] = []
    for row in editor.rows:
        value = row.minimum_input.text().strip()
        if not value:
            raise ValueError(
                f"minimum remaining is required for {editor.window_id.value}"
            )
        try:
            minimum = Fraction(Decimal(value))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(
                f"invalid minimum remaining for {editor.window_id.value}"
            ) from exc
        entries.append(
            UsagePlanCheckpoint(
                window_id=editor.window_id,
                time_to_reset=TimeToReset(
                    timedelta(seconds=row.seconds_input.value())
                ),
                minimum_remaining=minimum,
            )
        )
    return tuple(entries)


def _time_to_reset_seconds(value: TimeToReset) -> int:
    duration = value.duration
    return duration.days * 86_400 + duration.seconds
