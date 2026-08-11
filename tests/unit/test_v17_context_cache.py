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
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.context import ContextObservation
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("window-720m")


class CountingRepo(ContextHistoryRepository):
    def __init__(self) -> None:
        self.query_count = 0

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        self.query_count += 1
        return tuple(
            ContextObservation(
                window_id=window_id,
                observed_at=NOW - timedelta(days=index + 1),
                remaining=Fraction(Decimal(value)),
                resets_at=NOW - timedelta(days=index + 1) + timedelta(hours=8),
            )
            for index, value in enumerate(("0.20", "0.30", "0.50"))
        )


def current() -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                id=WINDOW,
                label="Dynamic",
                remaining=Fraction(Decimal("0.35")),
                resets_at=NOW + timedelta(hours=8),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )


def test_task_733_same_revision_pair_and_window_returns_equal_cached_result() -> None:
    repository = CountingRepo()
    service = HistoricalContextService(repository)
    snapshot = current()

    first = service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(1),
        history_revision=HistoryRevision(2),
    )
    second = service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(1),
        history_revision=HistoryRevision(2),
    )

    assert second == first
    assert repository.query_count == 1
    assert service.cache_stats.hits == 1
    assert service.cache_stats.misses == 1
    assert service.cache_stats.entries == 1


def test_task_733_current_or_history_revision_invalidates_cache() -> None:
    repository = CountingRepo()
    service = HistoricalContextService(repository)
    snapshot = current()

    service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(1),
        history_revision=HistoryRevision(1),
    )
    service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(2),
        history_revision=HistoryRevision(1),
    )
    service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(2),
        history_revision=HistoryRevision(2),
    )

    assert repository.query_count == 3
    assert service.cache_stats.entries == 1


def test_stale_fallback_bypasses_cache_for_same_authoritative_revision() -> None:
    repository = CountingRepo()
    service = HistoricalContextService(repository)
    snapshot = current()
    revision = CurrentRevision(1)
    history_revision = HistoryRevision(1)

    fresh = service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=revision,
        history_revision=history_revision,
    )
    stale = service.evaluate(
        current=snapshot.as_stale(),
        window_id=WINDOW,
        current_revision=revision,
        history_revision=history_revision,
    )

    assert fresh.state is HistoricalContextState.SUFFICIENT
    assert stale.state is HistoricalContextState.UNAVAILABLE
    assert stale.reason is HistoricalContextReason.CURRENT_NOT_CURRENT
    assert repository.query_count == 1


def test_revision_arguments_are_all_or_nothing() -> None:
    service = HistoricalContextService(CountingRepo())

    try:
        service.evaluate(
            current=current(),
            window_id=WINDOW,
            current_revision=CurrentRevision(1),
        )
    except ValueError as exc:
        assert "supplied together" in str(exc)
    else:
        raise AssertionError("partial revision identity must be rejected")


class RecoveringRepo(CountingRepo):
    def __init__(self) -> None:
        super().__init__()
        self.fail = True

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        if self.fail:
            self.query_count += 1
            raise HistoryReadError("temporary read failure")
        return super().query_candidates(window_id, interval)


def test_transient_history_failure_is_not_cached() -> None:
    repository = RecoveringRepo()
    service = HistoricalContextService(repository)
    snapshot = current()

    failed = service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(1),
        history_revision=HistoryRevision(1),
    )
    repository.fail = False
    recovered = service.evaluate(
        current=snapshot,
        window_id=WINDOW,
        current_revision=CurrentRevision(1),
        history_revision=HistoryRevision(1),
    )

    assert failed.reason is HistoricalContextReason.HISTORY_UNAVAILABLE
    assert recovered.state is HistoricalContextState.SUFFICIENT
    assert repository.query_count == 2
