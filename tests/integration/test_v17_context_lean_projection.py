from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.history import HistoricalSnapshot, HistoryInterval
from codexbar.domain.models import (
    Fraction,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.context_history import (
    CONTEXT_CANDIDATE_SQL,
    SqliteContextHistoryRepository,
)
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("window-720m")
OTHER = UsageWindowId("window-other")


def snapshot(observed_at: datetime, remaining: str) -> HistoricalSnapshot:
    usage = UsageSnapshot(
        windows=(
            UsageWindow(
                id=WINDOW,
                label="Dynamic label that Context must not materialize",
                remaining=Fraction(Decimal(remaining)),
                resets_at=observed_at + timedelta(hours=8),
            ),
            UsageWindow(
                id=OTHER,
                label="Unrelated",
                remaining=Fraction(Decimal("0.90")),
                resets_at=observed_at + timedelta(days=1),
            ),
        ),
        observed_at=observed_at,
        source=UsageSource.MOCK,
    )
    return HistoricalSnapshot.from_usage_snapshot(usage)


def test_task_734_lean_projection_reads_only_requested_context_window(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(snapshot(NOW - timedelta(days=2), "0.20"))
    repository.append(snapshot(NOW - timedelta(days=1), "0.40"))
    adapter = SqliteContextHistoryRepository(repository)

    values = adapter.query_candidates(
        WINDOW,
        HistoryInterval(NOW - timedelta(days=3), NOW),
    )

    assert [item.remaining.value for item in values] == [Decimal("0.20"), Decimal("0.40")]
    assert all(item.window_id == WINDOW for item in values)
    assert all(item.resets_at is not None for item in values)


def test_task_731_history_repository_reports_effective_mutations(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    value = snapshot(NOW - timedelta(days=1), "0.40")

    assert repository.append(value) is True
    assert repository.append(value) is False
    assert repository.clear() == 1
    assert repository.clear() == 0


def test_task_734_adapter_does_not_use_rich_query_window_materialization(
    tmp_path,
    monkeypatch,
) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(snapshot(NOW - timedelta(days=1), "0.40"))
    adapter = SqliteContextHistoryRepository(repository)

    def forbidden(*args, **kwargs):
        raise AssertionError("rich History query_window must not be used by Context")

    monkeypatch.setattr(repository, "query_window", forbidden)

    result = adapter.query_candidates(
        WINDOW,
        HistoryInterval(NOW - timedelta(days=2), NOW),
    )

    assert len(result) == 1


def test_task_734_lean_projection_is_equal_to_legacy_window_projection(tmp_path) -> None:
    repository = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repository.append(snapshot(NOW - timedelta(days=2), "0.20"))
    repository.append(snapshot(NOW - timedelta(days=1), "0.40"))
    interval = HistoryInterval(NOW - timedelta(days=3), NOW)
    adapter = SqliteContextHistoryRepository(repository)

    lean = adapter.query_candidates(WINDOW, interval)
    legacy = repository.query_window(WINDOW, interval)

    assert [(item.observed_at, item.remaining, item.resets_at) for item in lean] == [
        (sample.observed_at, sample.observation.remaining, sample.observation.resets_at)
        for sample in legacy
    ]


def test_task_735_sql_is_projection_only_not_context_semantics() -> None:
    normalized = " ".join(CONTEXT_CANDIDATE_SQL.upper().split())

    assert "S.OBSERVED_AT_UTC" in normalized
    assert "W.REMAINING" in normalized
    assert "W.RESETS_AT_UTC" in normalized
    assert "W.LABEL" not in normalized
    assert "S.SOURCE" not in normalized
    for forbidden in (
        "GROUP BY",
        "HAVING",
        "AVG(",
        "COUNT(",
        "MIN(",
        "MAX(",
        "SUM(",
        "LIMIT ",
        "ABS(",
    ):
        assert forbidden not in normalized
