from __future__ import annotations

import io
from unittest.mock import Mock

import pytest

from codexbar.ui import native_indicator
from codexbar.ui.native_indicator_helper import MENU_ACTIONS


def test_helper_indicator_registers_settings_callback(monkeypatch: pytest.MonkeyPatch) -> None:
    stdin = io.StringIO()
    process = Mock(stdin=stdin, stdout=io.StringIO(), stderr=io.StringIO())
    process.poll.return_value = None
    monkeypatch.setattr(native_indicator.subprocess, "Popen", Mock(return_value=process))
    monkeypatch.setattr(
        native_indicator.AyatanaHelperIndicator,
        "_await_ready",
        lambda self, **_: None,
    )
    called: list[str] = []

    indicator = native_indicator.AyatanaHelperIndicator(
        icon_png=b"png",
        on_refresh=lambda: None,
        on_details=lambda: None,
        on_quit=lambda: None,
        on_settings=lambda: called.append("settings"),
    )

    indicator._callbacks["settings"]()
    assert called == ["settings"]

    process.poll.return_value = 0
    indicator.close()


def test_native_helper_menu_contract_includes_settings() -> None:
    assert ("Settings", "settings") in MENU_ACTIONS
    assert MENU_ACTIONS == (
        ("Refresh", "refresh"),
        ("Open details", "details"),
        ("Settings", "settings"),
        ("Quit", "quit"),
    )
