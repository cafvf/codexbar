from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.budget import BudgetRuntime, BudgetStatus
from codexbar.domain.models import (
    Fraction,
    UsageWindow,
    UsageWindowId,
    UsageWindowState,
)
from codexbar.domain.settings import AppSettings


def test_runtime_reserve_change_applies_without_restart_or_usage_state_change() -> None:
    window = UsageWindow(
        UsageWindowId("window_300m"),
        "5 hours",
        Fraction(Decimal("0.18")),
        datetime(2026, 8, 11, tzinfo=UTC),
    )
    settings = AppSettings.defaults()
    runtime = BudgetRuntime(settings)

    before_state = window.state(settings.usage_policy())
    before = runtime.assess(window)

    updated = settings.with_usage_reserve(
        window.id,
        Fraction(Decimal("0.20")),
    )
    runtime.apply_settings(updated)
    after = runtime.assess(window)
    after_state = window.state(updated.usage_policy())

    assert before.status is BudgetStatus.NO_POLICY
    assert after.status is BudgetStatus.BELOW_RESERVE
    assert before_state is UsageWindowState.LOW
    assert after_state is UsageWindowState.LOW
