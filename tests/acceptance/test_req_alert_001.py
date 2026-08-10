from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.alerts import AlertService
from codexbar.application.notifications import NotificationMessage
from codexbar.domain.models import (
    Fraction,
    UsagePolicy,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)

OBSERVED_AT = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)


class RecordingNotifier:
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def notify(self, message: NotificationMessage) -> None:
        self.messages.append(message)


def make_snapshot(remaining: str) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal(remaining)),
            ),
        ),
        observed_at=OBSERVED_AT,
        source=UsageSource.MOCK,
    )


def test_req_alert_001_transition_sequence_is_silent_deduplicated_and_rearmed() -> None:
    notifier = RecordingNotifier()
    service = AlertService(notifier)
    policy = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.20")))

    for remaining in ("0.50", "0.15", "0.15", "0.00", "0.50", "0.10"):
        service.process(
            make_snapshot(remaining),
            policy,
            notifications_enabled=True,
        )

    assert [message.summary for message in notifier.messages] == [
        "CodexBar usage low",
        "CodexBar usage exhausted",
        "CodexBar usage low",
    ]


def test_req_alert_001_configured_low_threshold_remains_single_source_of_truth() -> None:
    notifier = RecordingNotifier()
    service = AlertService(notifier)
    strict = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.15")))

    service.process(make_snapshot("0.50"), strict, notifications_enabled=True)
    no_alert = service.process(make_snapshot("0.18"), strict, notifications_enabled=True)
    alert = service.process(make_snapshot("0.15"), strict, notifications_enabled=True)

    assert no_alert == ()
    assert len(alert) == 1
    assert [message.summary for message in notifier.messages] == ["CodexBar usage low"]
