from datetime import timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from codexbar.domain.models import Fraction, UsageWindowId
from codexbar.domain.quantities import TimeToReset


def _settings_module():
    return import_module("codexbar.domain.settings")


def test_default_settings_are_explicit_and_typed() -> None:
    module = _settings_module()
    settings = module.AppSettings.defaults()

    assert settings.low_remaining_threshold == Fraction(Decimal("0.20"))
    assert settings.refresh_interval_seconds.value == 60
    assert settings.notifications_enabled is True
    assert settings.usage_plan_checkpoints == module.UsagePlanCheckpointPolicy()
    assert settings.plan_breach_notifications_enabled is False


@pytest.mark.parametrize("value", [Decimal("0"), Decimal("1")])
def test_low_threshold_rejects_open_interval_boundaries(value: Decimal) -> None:
    module = _settings_module()

    with pytest.raises(ValueError, match="low"):
        module.AppSettings(
            low_remaining_threshold=Fraction(value),
            refresh_interval_seconds=module.RefreshIntervalSeconds(60),
            notifications_enabled=True,
        )


def test_fraction_rejects_low_threshold_values_outside_fraction_domain() -> None:
    with pytest.raises(ValueError, match="fraction"):
        Fraction(Decimal("-0.01"))


@pytest.mark.parametrize("seconds", [9, 3601, 0, -1])
def test_refresh_interval_rejects_values_outside_supported_domain(seconds: int) -> None:
    module = _settings_module()

    with pytest.raises(ValueError, match="refresh"):
        module.RefreshIntervalSeconds(seconds)


@pytest.mark.parametrize("seconds", [10, 60, 3600])
def test_refresh_interval_accepts_supported_boundaries(seconds: int) -> None:
    module = _settings_module()

    assert module.RefreshIntervalSeconds(seconds).value == seconds


@pytest.mark.parametrize("value", [True, False])
def test_notifications_enabled_accepts_booleans(value: bool) -> None:
    module = _settings_module()
    settings = module.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.20")),
        refresh_interval_seconds=module.RefreshIntervalSeconds(60),
        notifications_enabled=value,
    )

    assert settings.notifications_enabled is value


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_notifications_enabled_rejects_non_booleans(value: object) -> None:
    module = _settings_module()

    with pytest.raises(ValueError, match="notifications"):
        module.AppSettings(
            low_remaining_threshold=Fraction(Decimal("0.20")),
            refresh_interval_seconds=module.RefreshIntervalSeconds(60),
            notifications_enabled=value,
        )


@pytest.mark.parametrize("value", [0, 1, "true", None])
def test_plan_breach_notifications_reject_non_booleans(value: object) -> None:
    module = _settings_module()

    with pytest.raises(ValueError, match="plan_breach"):
        module.AppSettings(
            low_remaining_threshold=Fraction(Decimal("0.20")),
            refresh_interval_seconds=module.RefreshIntervalSeconds(60),
            notifications_enabled=True,
            plan_breach_notifications_enabled=value,
        )


def test_settings_create_usage_policy_from_configured_threshold() -> None:
    module = _settings_module()
    settings = module.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=module.RefreshIntervalSeconds(60),
        notifications_enabled=True,
    )

    assert settings.usage_policy().low_remaining_threshold == Fraction(Decimal("0.15"))


def test_functional_settings_updates_preserve_all_unedited_plan_fields() -> None:
    module = _settings_module()
    weekly = UsageWindowId("opaque-weekly")
    checkpoint_policy = module.UsagePlanCheckpointPolicy(
        (
            module.UsagePlanCheckpoint(
                weekly,
                TimeToReset(timedelta(hours=72)),
                Fraction(Decimal("0.55")),
            ),
        )
    )
    settings = module.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=module.RefreshIntervalSeconds(90),
        notifications_enabled=False,
        usage_plan_checkpoints=checkpoint_policy,
        plan_breach_notifications_enabled=True,
    )

    updated = settings.with_usage_reserve(
        UsageWindowId("opaque-short"),
        Fraction(Decimal("0.10")),
    )

    assert updated.low_remaining_threshold == settings.low_remaining_threshold
    assert updated.refresh_interval_seconds == settings.refresh_interval_seconds
    assert updated.notifications_enabled is settings.notifications_enabled
    assert updated.usage_plan_checkpoints == checkpoint_policy
    assert updated.plan_breach_notifications_enabled is True

    disabled = updated.with_plan_breach_notifications_enabled(False)
    assert disabled.usage_reserves == updated.usage_reserves
    assert disabled.usage_plan_checkpoints == checkpoint_policy
