from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.context import (
    ContextHistoryRepository,
    HistoricalContextReason,
    HistoricalContextService,
    HistoricalContextState,
)
from codexbar.application.history import HistoryInterval, HistoryReadError
from codexbar.domain.context import ContextCoverage, ContextObservation
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("provider-dynamic-a")
OTHER = UsageWindowId("provider-dynamic-b")


class RecordingRepository(ContextHistoryRepository):
    def __init__(
        self,
        observations: tuple[ContextObservation, ...] = (),
        *,
        fail: bool = False,
    ) -> None:
        self.observations = observations
        self.fail = fail
        self.calls: list[tuple[UsageWindowId, HistoryInterval]] = []

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        self.calls.append((window_id, interval))
        if self.fail:
            raise HistoryReadError("history unavailable")
        return self.observations


def snapshot(
    *,
    resets_at: datetime | None = NOW + timedelta(hours=10),
    window_id: UsageWindowId = WINDOW,
) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                window_id,
                "Provider supplied label",
                Fraction(Decimal("0.35")),
                resets_at=resets_at,
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )


def historical_cycle(
    index: int,
    remaining: str,
    *,
    window_id: UsageWindowId = WINDOW,
) -> ContextObservation:
    reset = NOW - timedelta(days=index + 1) + timedelta(hours=10)
    return ContextObservation(
        window_id=window_id,
        observed_at=reset - timedelta(hours=10),
        remaining=Fraction(Decimal(remaining)),
        resets_at=reset,
    )


def test_task_643_current_snapshot_is_reused_and_query_is_exactly_180_days() -> None:
    repository = RecordingRepository()
    current = snapshot()

    result = HistoricalContextService(repository).evaluate(
        current=current,
        window_id=WINDOW,
    )

    assert result.state is HistoricalContextState.UNAVAILABLE
    assert result.reason is HistoricalContextReason.NO_HISTORICAL_OBSERVATIONS
    assert repository.calls == [
        (
            WINDOW,
            HistoryInterval(NOW - timedelta(days=180), NOW),
        )
    ]


def test_task_644_missing_current_window_and_reset_are_explicit() -> None:
    repository = RecordingRepository()
    service = HistoricalContextService(repository)

    missing_window = service.evaluate(current=snapshot(), window_id=OTHER)
    missing_reset = service.evaluate(
        current=snapshot(resets_at=None),
        window_id=WINDOW,
    )

    assert missing_window.state is HistoricalContextState.UNAVAILABLE
    assert missing_window.reason is HistoricalContextReason.CURRENT_WINDOW_MISSING
    assert missing_reset.state is HistoricalContextState.UNAVAILABLE
    assert missing_reset.reason is HistoricalContextReason.CURRENT_RESET_MISSING
    assert repository.calls == []


def test_task_645_history_failure_is_contained_in_context_result() -> None:
    repository = RecordingRepository(fail=True)
    current = snapshot()

    result = HistoricalContextService(repository).evaluate(
        current=current,
        window_id=WINDOW,
    )

    assert result.state is HistoricalContextState.UNAVAILABLE
    assert result.reason is HistoricalContextReason.HISTORY_UNAVAILABLE
    assert result.diagnostic == "history unavailable"
    assert current.windows[0].remaining.value == Decimal("0.35")


def test_task_647_dynamic_window_identity_is_forwarded_without_fixed_labels() -> None:
    dynamic = UsageWindowId("opaque-provider-window-731")
    repository = RecordingRepository()
    service = HistoricalContextService(repository)

    result = service.evaluate(
        current=snapshot(window_id=dynamic),
        window_id=dynamic,
    )

    assert result.window_id == dynamic
    assert repository.calls[0][0] == dynamic


def test_task_644_two_cycles_are_insufficient_and_statistics_are_suppressed() -> None:
    repository = RecordingRepository(
        (
            historical_cycle(0, "0.20"),
            historical_cycle(1, "0.50"),
        )
    )

    result = HistoricalContextService(repository).evaluate(
        current=snapshot(),
        window_id=WINDOW,
    )

    assert result.state is HistoricalContextState.INSUFFICIENT
    assert result.reason is HistoricalContextReason.TOO_FEW_COMPARABLE_CYCLES
    assert result.summary is None


def test_task_644_three_cycles_produce_sufficient_sparse_summary() -> None:
    repository = RecordingRepository(
        (
            historical_cycle(0, "0.20"),
            historical_cycle(1, "0.30"),
            historical_cycle(2, "0.50"),
        )
    )

    result = HistoricalContextService(repository).evaluate(
        current=snapshot(),
        window_id=WINDOW,
    )

    assert result.state is HistoricalContextState.SUFFICIENT
    assert result.reason is None
    assert result.summary is not None
    assert result.summary.coverage is ContextCoverage.SPARSE
    assert result.summary.cycle_count == 3


def test_task_648_multiple_windows_do_not_cross_contaminate_context() -> None:
    repository = RecordingRepository(
        (
            historical_cycle(0, "0.20"),
            historical_cycle(1, "0.30"),
            historical_cycle(2, "0.50"),
            historical_cycle(3, "0.90", window_id=OTHER),
        )
    )

    result = HistoricalContextService(repository).evaluate(
        current=snapshot(),
        window_id=WINDOW,
    )

    assert result.state is HistoricalContextState.SUFFICIENT
    assert result.summary is not None
    assert result.summary.cycle_count == 3
