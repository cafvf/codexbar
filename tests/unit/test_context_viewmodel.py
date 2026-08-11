from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.context import ContextHistoryRepository, HistoricalContextService
from codexbar.application.history import HistoryInterval
from codexbar.domain.context import ContextObservation
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import ResetCreditReadResult, ResetCreditReadStatus
from codexbar.ui.context_viewmodel import ContextPresenter, ContextViewKind

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("dynamic-a")


class StaticReader:
    def __init__(self, observation: AccountRateLimitsObservation) -> None:
        self.observation = observation
        self.read_count = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.read_count += 1
        return self.observation


class Repo(ContextHistoryRepository):
    def __init__(self, values: tuple[str, ...]) -> None:
        self.values = values

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        return tuple(
            ContextObservation(
                window_id=window_id,
                observed_at=NOW - timedelta(days=index + 1),
                remaining=Fraction(Decimal(value)),
                resets_at=NOW - timedelta(days=index + 1) + timedelta(hours=10),
            )
            for index, value in enumerate(self.values)
        )


def account_observation() -> AccountRateLimitsObservation:
    usage = UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW,
                "Dynamic label",
                Fraction(Decimal("0.35")),
                resets_at=NOW + timedelta(hours=10),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )
    return AccountRateLimitsObservation(
        usage=usage,
        reset_credits=ResetCreditReadResult(
            status=ResetCreditReadStatus.UNAVAILABLE,
            inventory=None,
            diagnostic="not relevant",
        ),
    )


def presenter(values: tuple[str, ...]) -> tuple[ContextPresenter, StaticReader]:
    source = StaticReader(account_observation())
    latest = LatestAccountObservationReader(source)
    latest.read_account_rate_limits()
    return ContextPresenter(latest, HistoricalContextService(Repo(values))), source


def test_task_650_context_view_state_uses_latest_without_second_upstream_read() -> None:
    context_presenter, source = presenter(("0.20", "0.30", "0.50"))

    state = context_presenter.current()

    assert source.read_count == 1
    assert len(state.windows) == 1
    assert state.windows[0].label == "Dynamic label"
    assert state.windows[0].kind is ContextViewKind.SPARSE
    assert state.windows[0].comparable_cycle_count == 3


def test_task_652_insufficient_state_has_count_and_no_statistics() -> None:
    context_presenter, _ = presenter(("0.20", "0.50"))

    window = context_presenter.current().windows[0]

    assert window.kind is ContextViewKind.INSUFFICIENT
    assert window.comparable_cycle_count == 2
    assert window.median is None
    assert window.range_low is None
    assert window.rank_text is None


def test_task_653_sparse_state_exposes_observed_range() -> None:
    context_presenter, _ = presenter(("0.20", "0.30", "0.50"))

    window = context_presenter.current().windows[0]

    assert window.kind is ContextViewKind.SPARSE
    assert window.range_low == Decimal("0.20")
    assert window.range_high == Decimal("0.50")
    assert window.median is None


def test_task_654_limited_state_exposes_median_range_and_rank() -> None:
    context_presenter, _ = presenter(("0.20", "0.30", "0.40", "0.50", "0.60"))

    window = context_presenter.current().windows[0]

    assert window.kind is ContextViewKind.LIMITED
    assert window.median == Decimal("0.40")
    assert window.range_low == Decimal("0.20")
    assert window.range_high == Decimal("0.60")
    assert window.rank_text == (
        "Historical comparison: 3 historical values greater than current, "
        "0 equal to current, 2 lower than current."
    )


def test_task_655_656_established_state_exposes_middle_50_and_explicit_ties() -> None:
    context_presenter, _ = presenter(
        ("0.10", "0.20", "0.30", "0.35", "0.35", "0.40", "0.50", "0.60", "0.70", "0.80")
    )

    window = context_presenter.current().windows[0]

    assert window.kind is ContextViewKind.ESTABLISHED
    assert window.median == Decimal("0.375")
    assert window.band_low == Decimal("0.3125")
    assert window.band_high == Decimal("0.575")
    assert window.rank_text == (
        "Historical comparison: 5 historical values greater than current, "
        "2 equal to current, 3 lower than current."
    )
