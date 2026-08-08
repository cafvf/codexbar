from decimal import Decimal
from importlib import import_module

import pytest

from codexbar.domain.models import Fraction


def _settings_module():
    return import_module("codexbar.domain.settings")


def test_default_settings_are_explicit_and_typed() -> None:
    module = _settings_module()
    settings = module.AppSettings.defaults()

    assert settings.low_remaining_threshold == Fraction(Decimal("0.20"))
    assert settings.refresh_interval_seconds.value == 60
    assert settings.notifications_enabled is True


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


def test_settings_create_usage_policy_from_configured_threshold() -> None:
    module = _settings_module()
    settings = module.AppSettings(
        low_remaining_threshold=Fraction(Decimal("0.15")),
        refresh_interval_seconds=module.RefreshIntervalSeconds(60),
        notifications_enabled=True,
    )

    assert settings.usage_policy().low_remaining_threshold == Fraction(Decimal("0.15"))
