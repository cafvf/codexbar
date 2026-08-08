from datetime import datetime, timezone
from decimal import Decimal

import pytest

from codexbar.domain.models import Fraction, UsagePolicy, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId


def test_fraction_from_percent_and_percent_are_inverse() -> None:
    fraction = Fraction.from_percent(Decimal("12.5"))
    assert fraction.value == Decimal("0.125")
    assert fraction.percent == Decimal("12.500")


def test_snapshot_rejects_duplicate_window_ids() -> None:
    now = datetime.now(timezone.utc)
    window = UsageWindow(UsageWindowId("same"), "Window", Fraction(Decimal("0.5")))
    with pytest.raises(ValueError, match="unique"):
        UsageSnapshot((window, window), now, UsageSource.MOCK)


def test_low_threshold_is_explicit_policy() -> None:
    window = UsageWindow(UsageWindowId("w"), "Window", Fraction(Decimal("0.15")))
    strict = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.10")))
    assert window.state().value == "low"
    assert window.state(strict).value == "available"
