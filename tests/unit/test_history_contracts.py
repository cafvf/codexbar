from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import get_type_hints

import pytest

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryCorruptionError,
    HistoryError,
    HistoryInspection,
    HistoryInterval,
    HistoryReadError,
    HistoryRepository,
    HistorySchemaError,
    HistoryState,
    HistoryWriteError,
)
from codexbar.domain.errors import CodexBarError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def snapshot(*, freshness: Freshness = Freshness.CURRENT) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                "Weekly",
                Fraction(Decimal("0.42")),
                resets_at=T0 + timedelta(days=1),
            ),
        ),
        observed_at=T0,
        source=UsageSource.MOCK,
        freshness=freshness,
        rate_limit_reached_type="weekly",
    )


def test_history_interval_is_half_open() -> None:
    interval = HistoryInterval(T0, T0 + timedelta(hours=1))

    assert interval.contains(T0)
    assert interval.contains(T0 + timedelta(minutes=59))
    assert not interval.contains(T0 + timedelta(hours=1))


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (T0.replace(tzinfo=None), T0 + timedelta(hours=1)),
        (T0, (T0 + timedelta(hours=1)).replace(tzinfo=None)),
        (T0, T0),
        (T0 + timedelta(hours=1), T0),
    ],
)
def test_history_interval_rejects_invalid_boundaries(
    start: datetime,
    end: datetime,
) -> None:
    with pytest.raises(ValueError):
        HistoryInterval(start, end)


def test_historical_snapshot_projects_only_normalized_current_contract() -> None:
    result = HistoricalSnapshot.from_usage_snapshot(snapshot())

    assert result.observed_at == T0
    assert result.source is UsageSource.MOCK
    assert result.rate_limit_reached_type == "weekly"
    assert result.windows == (
        HistoricalWindowObservation(
            window_id=UsageWindowId("weekly"),
            label="Weekly",
            remaining=Fraction(Decimal("0.42")),
            resets_at=T0 + timedelta(days=1),
        ),
    )
    assert not hasattr(result, "freshness")
    assert not hasattr(result, "raw_payload")
    assert not hasattr(result, "credentials")
    assert not hasattr(result, "account_id")


def test_historical_snapshot_rejects_stale_projection() -> None:
    with pytest.raises(ValueError, match="CURRENT"):
        HistoricalSnapshot.from_usage_snapshot(snapshot(freshness=Freshness.STALE))


def test_history_inspection_distinguishes_states_without_filesystem_types() -> None:
    inspection = HistoryInspection(
        path="/home/test/.local/share/codexbar/history.sqlite3",
        state=HistoryState.READY_NON_EMPTY,
        schema_version=1,
        snapshot_count=2,
        oldest_observed_at=T0,
        newest_observed_at=T0 + timedelta(minutes=5),
    )

    assert inspection.state is HistoryState.READY_NON_EMPTY
    assert inspection.snapshot_count == 2
    assert isinstance(inspection.path, str)


def test_history_error_taxonomy_is_under_codexbar_error() -> None:
    assert issubclass(HistoryError, CodexBarError)
    assert issubclass(HistoryReadError, HistoryError)
    assert issubclass(HistoryWriteError, HistoryError)
    assert issubclass(HistorySchemaError, HistoryError)
    assert issubclass(HistoryCorruptionError, HistoryReadError)


def test_history_repository_port_uses_normalized_history_types() -> None:
    hints = get_type_hints(HistoryRepository.append)
    assert hints["snapshot"] is HistoricalSnapshot

    query_hints = get_type_hints(HistoryRepository.query)
    assert query_hints["interval"] is HistoryInterval

    window_hints = get_type_hints(HistoryRepository.query_window)
    assert window_hints["window_id"] is UsageWindowId
    assert window_hints["interval"] is HistoryInterval
