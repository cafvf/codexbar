from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId


class MockUsageProvider:
    def __init__(self, now: datetime | None = None) -> None:
        self._now = now or datetime.now(UTC)

    def get_usage(self) -> UsageSnapshot:
        return UsageSnapshot(
            windows=(
                UsageWindow(
                    id=UsageWindowId("weekly"),
                    label="Weekly",
                    remaining=Fraction(Decimal("0.81")),
                    resets_at=self._now + timedelta(days=3),
                ),
            ),
            observed_at=self._now,
            source=UsageSource.MOCK,
        )
