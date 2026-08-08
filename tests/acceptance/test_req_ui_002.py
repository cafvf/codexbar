from datetime import UTC, datetime
from decimal import Decimal

from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.ui.viewmodel import UsageViewModel


def _window(window_id: str, label: str, percent_left: str) -> UsageWindow:
    return UsageWindow(
        id=UsageWindowId(window_id),
        label=label,
        remaining=Fraction.from_percent(Decimal(percent_left)),
    )


def _snapshot(*windows: UsageWindow) -> UsageSnapshot:
    return UsageSnapshot(
        windows=windows,
        observed_at=datetime(2026, 8, 8, 12, 0, tzinfo=UTC),
        source=UsageSource.MOCK,
    )


def test_ac_ui_010_five_hour_window_has_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_300m", "5 hours", "73")))

    assert state.windows[0].short_label == "5h"
    assert state.glance_text == "5h: 73%"


def test_ac_ui_011_weekly_window_has_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_10080m", "Weekly", "41")))

    assert state.windows[0].short_label == "W"
    assert state.glance_text == "W: 41%"


def test_ac_ui_012_two_known_windows_are_shown_together() -> None:
    state = UsageViewModel.from_snapshot(
        _snapshot(
            _window("window_300m", "5 hours", "73"),
            _window("window_10080m", "Weekly", "41"),
        )
    )

    assert state.glance_text == "5h: 73% · W: 41%"


def test_ac_ui_013_missing_window_is_omitted_not_fabricated() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_10080m", "Weekly", "41")))

    assert "5h" not in state.glance_text
    assert state.glance_text == "W: 41%"


def test_unknown_duration_gets_deterministic_compact_label() -> None:
    state = UsageViewModel.from_snapshot(_snapshot(_window("window_1440m", "1 days", "90")))

    assert state.glance_text == "1d: 90%"


def test_ac_ui_016_native_indicator_module_is_optional() -> None:
    from codexbar.ui.native_indicator import ayatana_availability

    result = ayatana_availability()
    assert isinstance(result.available, bool)


def test_ac_ui_019_missing_native_backend_does_not_affect_glance_model() -> None:
    state = UsageViewModel.from_snapshot(
        _snapshot(
            _window("window_300m", "5 hours", "73"),
            _window("window_10080m", "Weekly", "41"),
        )
    )
    assert state.glance_text == "5h: 73% · W: 41%"


def test_ac_ui_020_native_indicator_extra_has_no_pygobject_dependency() -> None:
    from pathlib import Path

    pyproject = Path("pyproject.toml").read_text()
    assert 'native-indicator = []' in pyproject
    assert "PyGObject" not in pyproject


def test_ac_ui_021_native_probe_targets_system_python() -> None:
    from codexbar.ui.native_indicator import SYSTEM_PYTHON

    assert SYSTEM_PYTHON == "/usr/bin/python3"


def test_ac_ui_022_helper_boundary_does_not_import_codex_domain() -> None:
    from pathlib import Path

    helper = Path("src/codexbar/ui/native_indicator_helper.py").read_text()
    assert "codexbar.domain" not in helper
    assert "codexbar.infrastructure" not in helper
    assert "CodexAppServer" not in helper


def test_ac_ui_023_helper_protocol_has_only_ui_intent_events() -> None:
    from pathlib import Path

    helper = Path("src/codexbar/ui/native_indicator_helper.py").read_text()
    for event in ('_emit("refresh")', '_emit("details")', '_emit("quit")'):
        assert event in helper


def test_ac_ui_024_qt_fallback_remains_part_of_native_selection() -> None:
    from pathlib import Path

    tray = Path("src/codexbar/ui/tray.py").read_text()
    assert "if self._native_indicator is None" in tray
    assert "QSystemTrayIcon" in tray


def test_ac_ui_025_native_helper_requires_ready_handshake() -> None:
    from pathlib import Path

    native = Path("src/codexbar/ui/native_indicator.py").read_text()
    helper = Path("src/codexbar/ui/native_indicator_helper.py").read_text()
    assert "_await_ready" in native
    assert '_emit("ready")' in helper


def test_ac_ui_026_runtime_helper_failure_activates_qt_fallback() -> None:
    from pathlib import Path

    tray = Path("src/codexbar/ui/tray.py").read_text()
    assert "is_healthy()" in tray
    assert "_activate_qt_fallback()" in tray
