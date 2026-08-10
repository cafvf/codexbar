from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.context import HistoricalContextService, HistoricalContextState
from codexbar.application.history import HistoricalSnapshot, HistoricalWindowObservation
from codexbar.domain.context import ContextCoverage
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("opaque-window")


def historical(index: int, remaining: str) -> HistoricalSnapshot:
    reset = NOW - timedelta(days=index + 1) + timedelta(hours=10)
    return HistoricalSnapshot(
        observed_at=reset - timedelta(hours=10),
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=WINDOW,
                label="Any label",
                remaining=Fraction(Decimal(remaining)),
                resets_at=reset,
            ),
        ),
    )


def current() -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW,
                "Current label",
                Fraction(Decimal("0.35")),
                resets_at=NOW + timedelta(hours=10),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )


def test_task_641_648_schema_v1_history_composes_end_to_end(tmp_path) -> None:
    history = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    for index, remaining in enumerate(("0.20", "0.30", "0.40", "0.50", "0.60")):
        history.append(historical(index, remaining))

    service = HistoricalContextService(SqliteContextHistoryRepository(history))
    result = service.evaluate(current=current(), window_id=WINDOW)

    assert result.state is HistoricalContextState.SUFFICIENT
    assert result.summary is not None
    assert result.summary.coverage is ContextCoverage.LIMITED
    assert result.summary.cycle_count == 5
    assert result.summary.median == Decimal("0.40")
