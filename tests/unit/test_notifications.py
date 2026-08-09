from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtDBus import QDBusMessage

from codexbar.application.alerts import AlertEvent
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import Fraction, UsageWindowId, UsageWindowState
from codexbar.infrastructure.notifications import QtDbusNotificationAdapter


class FakeInterface:
    def __init__(self, *, valid: bool = True, reply: QDBusMessage | None = None) -> None:
        self.valid = valid
        self.reply = reply or QDBusMessage()
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def isValid(self) -> bool:
        return self.valid

    def call(self, method: str, *args: object) -> QDBusMessage:
        self.calls.append((method, args))
        return self.reply


def event(state: UsageWindowState, remaining: str) -> AlertEvent:
    return AlertEvent(
        window_id=UsageWindowId("weekly"),
        label="Weekly",
        state=state,
        remaining=Fraction(Decimal(remaining)),
        resets_at=datetime(2026, 8, 9, 12, 0, tzinfo=UTC),
    )


@pytest.mark.parametrize(
    ("state", "remaining", "expected_summary"),
    [
        (UsageWindowState.LOW, "0.15", "CodexBar usage low"),
        (UsageWindowState.EXHAUSTED, "0", "CodexBar usage exhausted"),
    ],
)
def test_qtdbus_adapter_sends_distinguishable_normalized_notifications(
    state: UsageWindowState,
    remaining: str,
    expected_summary: str,
) -> None:
    interface = FakeInterface()
    adapter = QtDbusNotificationAdapter(lambda: interface)

    adapter.notify(event(state, remaining))

    assert len(interface.calls) == 1
    method, args = interface.calls[0]
    assert method == "Notify"
    assert args[0] == "CodexBar"
    assert args[3] == expected_summary
    assert "Weekly" in str(args[4])
    assert f"{Fraction(Decimal(remaining)).percent.normalize():f}%" in str(args[4])


def test_qtdbus_adapter_normalizes_unavailable_service() -> None:
    adapter = QtDbusNotificationAdapter(lambda: FakeInterface(valid=False))

    with pytest.raises(NotificationDeliveryError, match="unavailable"):
        adapter.notify(event(UsageWindowState.LOW, "0.15"))


def test_qtdbus_adapter_normalizes_dbus_error_reply() -> None:
    reply = QDBusMessage.createError("org.example.Failure", "boom")
    adapter = QtDbusNotificationAdapter(lambda: FakeInterface(reply=reply))

    with pytest.raises(NotificationDeliveryError, match="boom"):
        adapter.notify(event(UsageWindowState.LOW, "0.15"))


def test_alert_event_contract_excludes_provider_payload_fields() -> None:
    alert = event(UsageWindowState.LOW, "0.15")

    assert not hasattr(alert, "raw_payload")
    assert not hasattr(alert, "account_id")
    assert not hasattr(alert, "credentials")
