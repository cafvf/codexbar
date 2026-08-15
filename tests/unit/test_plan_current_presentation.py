from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.plan import PlanCheckpointResolution, PlanCompliance
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.quantities import TimeToReset
from codexbar.domain.reset import ResetCreditReadResult
from codexbar.domain.settings import (
    AppSettings,
    UsagePlanCheckpoint,
    UsagePlanCheckpointPolicy,
)
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter

NOW = datetime(2026, 8, 14, 12, tzinfo=UTC)
WINDOW_ID = UsageWindowId("opaque-weekly")


class Reader:
    def __init__(self, observation: AccountRateLimitsObservation) -> None:
        self.observation = observation
        self.reads = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.reads += 1
        return self.observation


def f(value: str) -> Fraction:
    return Fraction(Decimal(value))


def observation(
    remaining: str,
    *,
    resets_at: datetime | None = None,
    freshness: Freshness = Freshness.CURRENT,
) -> AccountRateLimitsObservation:
    return AccountRateLimitsObservation(
        UsageSnapshot(
            (UsageWindow(WINDOW_ID, "Weekly", f(remaining), resets_at=resets_at),),
            NOW,
            UsageSource.MOCK,
            freshness=freshness,
        ),
        ResetCreditReadResult.unavailable("fixture"),
    )


def plan_settings(*, reserve: str | None = "0.15") -> AppSettings:
    settings = AppSettings.defaults()
    if reserve is not None:
        settings = settings.with_usage_reserve(WINDOW_ID, f(reserve))
    return settings.with_usage_plan_checkpoints(
        UsagePlanCheckpointPolicy(
            (
                UsagePlanCheckpoint(
                    WINDOW_ID,
                    TimeToReset(timedelta(hours=72)),
                    f("0.55"),
                ),
            )
        )
    )


def presenter_for(
    value: AccountRateLimitsObservation,
    settings: AppSettings,
) -> tuple[CurrentAccountPresenter, Reader]:
    source = Reader(value)
    latest = LatestAccountObservationReader(source)
    latest.read_account_rate_limits()
    presenter = CurrentAccountPresenter(
        latest,
        settings,
        lambda: ResetLedgerProjection(),
        clock=lambda: NOW,
    )
    return presenter, source


def test_ac_1818_plan_uses_captured_current_observation_without_second_source_read() -> None:
    presenter, source = presenter_for(
        observation("0.63", resets_at=NOW + timedelta(hours=60)),
        plan_settings(),
    )

    state = presenter.current()
    again = presenter.current()

    assert source.reads == 1
    assert state is not None and again is not None
    assert state.plan == again.plan
    assessment = state.plan.windows[0]
    assert assessment.checkpoint_resolution is PlanCheckpointResolution.ACTIVE
    assert assessment.effective_floor == f("0.55")
    assert assessment.margin is not None
    assert assessment.margin.value == Decimal("0.08")
    assert assessment.compliance is PlanCompliance.ABOVE


def test_task_840_presenter_uses_configured_usage_policy_for_current_classification() -> None:
    settings = AppSettings(
        low_remaining_threshold=f("0.15"),
        refresh_interval_seconds=AppSettings.defaults().refresh_interval_seconds,
        notifications_enabled=True,
    )
    presenter, _ = presenter_for(observation("0.18"), settings)

    state = presenter.current()

    assert state is not None
    assert state.usage.windows[0].state.value == "available"


def test_live_settings_update_reprojects_same_captured_observation_without_source_read() -> None:
    presenter, source = presenter_for(observation("0.40"), AppSettings.defaults())

    before = presenter.current()
    presenter.apply_settings(
        AppSettings.defaults().with_usage_reserve(WINDOW_ID, f("0.50"))
    )
    after = presenter.current()

    assert source.reads == 1
    assert before is not None and after is not None
    assert before.plan.windows[0].effective_floor is None
    assert after.plan.windows[0].effective_floor == f("0.50")
    assert after.plan.windows[0].compliance is PlanCompliance.BELOW


def test_ac_1820_stale_current_withholds_plan_windows_and_current_compliance_claim() -> None:
    presenter, _ = presenter_for(
        observation(
            "0.40",
            resets_at=NOW + timedelta(hours=60),
            freshness=Freshness.STALE,
        ),
        plan_settings(),
    )

    state = presenter.current()

    assert state is not None
    assert state.usage.stale is True
    assert state.plan.available is False
    assert state.plan.windows == ()


def test_ac_1821_checkpoint_policy_does_not_change_budget_headroom_or_advice() -> None:
    base_settings = AppSettings.defaults().with_usage_reserve(WINDOW_ID, f("0.15"))
    presenter, source = presenter_for(
        observation("0.63", resets_at=NOW + timedelta(hours=60)),
        base_settings,
    )

    before = presenter.current()
    presenter.apply_settings(plan_settings(reserve="0.15"))
    after = presenter.current()

    assert source.reads == 1
    assert before is not None and after is not None
    assert before.budget == after.budget
    assert before.plan.windows[0].effective_floor == f("0.15")
    assert after.plan.windows[0].effective_floor == f("0.55")
