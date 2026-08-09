from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from codexbar.application.alerts import AlertEvent
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import Fraction, UsageWindowId, UsageWindowState
from codexbar.infrastructure.notifications import CommandResult, NotifySendNotificationAdapter


def event(state: UsageWindowState, remaining: str) -> AlertEvent:
    return AlertEvent(
        window_id=UsageWindowId("weekly"),
        label="Weekly",
        state=state,
        remaining=Fraction(Decimal(remaining)),
        resets_at=datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("state", "remaining", "summary", "urgency"),
    [
        (UsageWindowState.LOW, "0.15", "CodexBar usage low", "--urgency=normal"),
        (
            UsageWindowState.EXHAUSTED,
            "0",
            "CodexBar usage exhausted",
            "--urgency=critical",
        ),
    ],
)
def test_notify_send_adapter_builds_normalized_command(
    state: UsageWindowState,
    remaining: str,
    summary: str,
    urgency: str,
) -> None:
    commands: list[tuple[str, ...]] = []

    def runner(command):
        commands.append(tuple(command))
        return CommandResult(returncode=0)

    adapter = NotifySendNotificationAdapter(runner)
    adapter.notify(event(state, remaining))

    assert len(commands) == 1
    command = commands[0]
    assert command[0] == "notify-send"
    assert "--app-name=CodexBar" in command
    assert urgency in command
    assert summary in command
    assert any("Weekly" in part for part in command)
    assert any(f"{Fraction(Decimal(remaining)).percent.normalize():f}%" in part for part in command)


def test_notify_send_adapter_normalizes_nonzero_exit() -> None:
    adapter = NotifySendNotificationAdapter(
        lambda _command: CommandResult(returncode=1, stderr="daemon unavailable")
    )

    with pytest.raises(NotificationDeliveryError, match="daemon unavailable"):
        adapter.notify(event(UsageWindowState.LOW, "0.15"))


def test_alert_event_contract_excludes_provider_payload_fields() -> None:
    alert = event(UsageWindowState.LOW, "0.15")
    assert not hasattr(alert, "raw_payload")
    assert not hasattr(alert, "account_id")
    assert not hasattr(alert, "credentials")
