from decimal import Decimal

import pytest

from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.settings import AppSettings, UsageReserve, UsageReservePolicy


def test_reserve_policy_is_immutable_keyed_by_stable_window_id() -> None:
    weekly = UsageWindowId("window_10080m")
    policy = UsageReservePolicy(
        (UsageReserve(weekly, Fraction(Decimal("0.15"))),)
    )

    assert policy.reserve_for(weekly) == Fraction(Decimal("0.15"))
    assert policy.reserve_for(UsageWindowId("Weekly")) is None


def test_unknown_window_has_no_policy_and_explicit_zero_is_distinct() -> None:
    empty = UsageReservePolicy()
    explicit_zero = empty.with_reserve(
        UsageWindowId("window_300m"),
        Fraction(Decimal("0")),
    )

    assert empty.reserve_for(UsageWindowId("window_300m")) is None
    assert explicit_zero.reserve_for(
        UsageWindowId("window_300m")
    ) == Fraction(Decimal("0"))


def test_duplicate_window_ids_are_rejected() -> None:
    window_id = UsageWindowId("window_300m")
    with pytest.raises(ValueError, match="unique"):
        UsageReservePolicy(
            (
                UsageReserve(window_id, Fraction(Decimal("0.10"))),
                UsageReserve(window_id, Fraction(Decimal("0.20"))),
            )
        )


def test_existing_three_argument_app_settings_constructor_remains_compatible() -> None:
    defaults = AppSettings.defaults()
    settings = AppSettings(
        defaults.low_remaining_threshold,
        defaults.refresh_interval_seconds,
        defaults.notifications_enabled,
    )

    assert settings.usage_reserves == UsageReservePolicy()
