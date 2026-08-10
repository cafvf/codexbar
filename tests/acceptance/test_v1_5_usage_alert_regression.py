from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.alerts import AlertService
from codexbar.domain.models import (
    Fraction,
    UsagePolicy,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)


class Notifier:
    def __init__(self):
        self.messages = []

    def notify(self, message):
        self.messages.append(message)


def snapshot(value: str):
    return UsageSnapshot(
        (
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal(value)),
            ),
        ),
        datetime(2026, 8, 10, tzinfo=UTC),
        UsageSource.MOCK,
    )


def test_usage_alert_transition_semantics_survive_notification_generalization() -> None:
    notifier = Notifier()
    service = AlertService(notifier)
    policy = UsagePolicy(Fraction(Decimal("0.20")))

    service.process(snapshot("0.50"), policy, notifications_enabled=True)
    service.process(snapshot("0.10"), policy, notifications_enabled=True)

    assert len(notifier.messages) == 1
    assert notifier.messages[0].summary == "CodexBar usage low"
