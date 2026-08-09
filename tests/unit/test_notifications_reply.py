from __future__ import annotations

import subprocess

import pytest

from codexbar.domain.errors import NotificationDeliveryError
from codexbar.infrastructure import notifications


def test_default_runner_normalizes_missing_notify_send(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("notify-send")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(NotificationDeliveryError, match="libnotify-bin"):
        notifications._default_runner(["notify-send", "title"])


def test_default_runner_normalizes_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="notify-send", timeout=5)

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(NotificationDeliveryError, match="timed out"):
        notifications._default_runner(["notify-send", "title"])
