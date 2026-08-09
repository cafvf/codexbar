from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.history import HistoryInterval, RecordHistorySnapshot
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

T0 = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def usage_snapshot(
    observed_at: datetime,
    *,
    freshness: Freshness = Freshness.CURRENT,
    weekly: str = "0.42",
    short: str = "0.75",
    weekly_label: str = "Weekly",
) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                UsageWindowId("weekly"),
                weekly_label,
                Fraction(Decimal(weekly)),
                resets_at=observed_at + timedelta(days=1),
            ),
            UsageWindow(
                UsageWindowId("five_hour"),
                "5 hours",
                Fraction(Decimal(short)),
            ),
        ),
        observed_at=observed_at,
        source=UsageSource.MOCK,
        freshness=freshness,
        rate_limit_reached_type="weekly",
    )


def test_ac_history_001_002_006_current_snapshot_round_trips_atomically(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    repository = SqliteHistoryRepository(path)
    capture = RecordHistorySnapshot(repository)
    source = usage_snapshot(T0)

    assert capture.execute(source)

    result = repository.query(HistoryInterval(T0, T0 + timedelta(seconds=1)))
    assert len(result) == 1
    stored = result[0]
    assert stored.observed_at == T0
    assert stored.source is UsageSource.MOCK
    assert stored.rate_limit_reached_type == "weekly"
    assert len(stored.windows) == 2
    weekly = next(window for window in stored.windows if window.window_id.value == "weekly")
    assert weekly.remaining == Fraction(Decimal("0.42"))
    assert weekly.resets_at == T0 + timedelta(days=1)


def test_ac_history_003_stale_snapshot_is_not_written(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    capture = RecordHistorySnapshot(repository)

    assert not capture.execute(usage_snapshot(T0, freshness=Freshness.STALE))
    assert repository.query(HistoryInterval(T0, T0 + timedelta(seconds=1))) == ()


def test_ac_history_007_equal_values_at_distinct_times_are_distinct(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    capture = RecordHistorySnapshot(repository)

    capture.execute(usage_snapshot(T0))
    capture.execute(usage_snapshot(T0 + timedelta(minutes=1)))

    result = repository.query(HistoryInterval(T0, T0 + timedelta(minutes=2)))
    assert [item.observed_at for item in result] == [T0, T0 + timedelta(minutes=1)]


def test_same_logical_snapshot_append_is_idempotent(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    capture = RecordHistorySnapshot(repository)
    source = usage_snapshot(T0)

    capture.execute(source)
    capture.execute(source)

    assert len(repository.query(HistoryInterval(T0, T0 + timedelta(seconds=1)))) == 1


def test_ac_history_008_010_history_survives_repository_restart_without_insert(tmp_path) -> None:
    path = tmp_path / "history.sqlite3"
    first = SqliteHistoryRepository(path)
    RecordHistorySnapshot(first).execute(usage_snapshot(T0))

    reopened = SqliteHistoryRepository(path)

    result = reopened.query(HistoryInterval(T0, T0 + timedelta(seconds=1)))
    assert len(result) == 1


def test_ac_history_011_012_013_query_is_ordered_and_half_open(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    capture = RecordHistorySnapshot(repository)
    capture.execute(usage_snapshot(T0 + timedelta(minutes=2)))
    capture.execute(usage_snapshot(T0))
    capture.execute(usage_snapshot(T0 + timedelta(minutes=1)))

    result = repository.query(
        HistoryInterval(T0, T0 + timedelta(minutes=2))
    )

    assert [item.observed_at for item in result] == [
        T0,
        T0 + timedelta(minutes=1),
    ]


def test_ac_history_014_015_window_query_uses_stable_id_and_preserves_labels(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    capture = RecordHistorySnapshot(repository)
    capture.execute(usage_snapshot(T0, weekly_label="Weekly old label"))
    capture.execute(
        usage_snapshot(
            T0 + timedelta(minutes=1),
            weekly_label="Weekly renamed",
        )
    )

    result = repository.query_window(
        UsageWindowId("weekly"),
        HistoryInterval(T0, T0 + timedelta(minutes=2)),
    )

    assert [sample.observed_at for sample in result] == [
        T0,
        T0 + timedelta(minutes=1),
    ]
    assert [sample.observation.label for sample in result] == [
        "Weekly old label",
        "Weekly renamed",
    ]
    assert all(sample.observation.window_id == UsageWindowId("weekly") for sample in result)


def test_ac_history_016_empty_interval_result_is_empty(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")

    assert repository.query(HistoryInterval(T0, T0 + timedelta(minutes=1))) == ()
    assert repository.query_window(
        UsageWindowId("weekly"),
        HistoryInterval(T0, T0 + timedelta(minutes=1)),
    ) == ()
