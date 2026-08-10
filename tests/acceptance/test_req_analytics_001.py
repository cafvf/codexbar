from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from codexbar.application.analytics import (
    AnalysisPeriod,
    HistoricalAnalysisService,
    HistoricalAnalysisState,
)
from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoryInterval,
    HistorySchemaError,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.infrastructure.history_sqlite import (
    SqliteHistoryRepository,
    open_history_analytics_repository,
)

T0 = datetime(2026, 8, 8, 12, 0, tzinfo=UTC)
WEEKLY = UsageWindowId("weekly")
SHORT = UsageWindowId("window_300m")


def historical_snapshot(at: datetime, values: tuple[tuple[UsageWindowId, str, str], ...]):
    return HistoricalSnapshot(
        observed_at=at,
        source=UsageSource.MOCK,
        windows=tuple(
            HistoricalWindowObservation(
                window_id=window_id,
                label=label,
                remaining=Fraction(Decimal(value)),
            )
            for window_id, label, value in values
        ),
    )


def test_half_open_query_and_stable_identity(tmp_path: Path) -> None:
    repo = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repo.append(historical_snapshot(T0, ((WEEKLY, "Weekly old", "0.80"),)))
    repo.append(historical_snapshot(T0 + timedelta(hours=1), ((WEEKLY, "Weekly new", "0.70"),)))
    repo.append(historical_snapshot(T0 + timedelta(hours=2), ((WEEKLY, "Weekly new", "0.60"),)))
    interval = HistoryInterval(T0, T0 + timedelta(hours=2))

    rows = repo.query_window(WEEKLY, interval)

    assert [row.observed_at for row in rows] == [T0, T0 + timedelta(hours=1)]
    assert [row.observation.label for row in rows] == ["Weekly old", "Weekly new"]


def test_distinct_window_discovery_is_schema_v1_query(tmp_path: Path) -> None:
    repo = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repo.append(historical_snapshot(
        T0,
        (
            (WEEKLY, "Same label", "0.80"),
            (SHORT, "Same label", "0.90"),
        ),
    ))

    ids = repo.list_window_ids(HistoryInterval(T0, T0 + timedelta(hours=1)))

    assert ids == (WEEKLY, SHORT)


def test_historical_only_window_is_discoverable(tmp_path: Path) -> None:
    repo = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repo.append(historical_snapshot(T0, ((WEEKLY, "Weekly", "0.80"),)))

    service = HistoricalAnalysisService(repo)
    result = service.discover(
        AnalysisPeriod.HOURS_24,
        end=T0 + timedelta(hours=1),
    )

    assert result.state is HistoricalAnalysisState.READY
    assert result.window_ids == (WEEKLY,)


def test_absent_read_does_not_create_database(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "history.sqlite3"
    repo = open_history_analytics_repository(path)

    result = HistoricalAnalysisService(repo).discover(
        AnalysisPeriod.HOURS_24,
        end=T0,
    )

    assert result.state is HistoricalAnalysisState.EMPTY
    assert not path.exists()
    assert not path.parent.exists()


class UnsupportedRepo:
    def query_window(self, window_id, interval):
        raise HistorySchemaError("unsupported history schema version: 2")

    def list_window_ids(self, interval):
        raise HistorySchemaError("unsupported history schema version: 2")


def test_schema_failure_becomes_unsupported_analysis_state() -> None:
    service = HistoricalAnalysisService(UnsupportedRepo())
    result = service.analyze(WEEKLY, AnalysisPeriod.HOURS_24, end=T0)
    discovery = service.discover(AnalysisPeriod.HOURS_24, end=T0)

    assert result.state is HistoricalAnalysisState.UNSUPPORTED
    assert discovery.state is HistoricalAnalysisState.UNSUPPORTED
    assert "schema" in (result.diagnostic or "")


def test_analytics_contract_has_no_predictive_outputs(tmp_path: Path) -> None:
    repo = SqliteHistoryRepository(tmp_path / "history.sqlite3")
    repo.append(historical_snapshot(T0, ((WEEKLY, "Weekly", "0.80"),)))
    result = HistoricalAnalysisService(repo).analyze(
        WEEKLY,
        AnalysisPeriod.HOURS_24,
        end=T0 + timedelta(hours=1),
    )

    forbidden = ("forecast", "eta", "token", "time_in_low", "time_in_state")
    assert not any(hasattr(result, name) for name in forbidden)
    assert result.summary is not None
    assert not any(hasattr(result.summary, name) for name in forbidden)


def test_open_time_unsupported_schema_is_normalized(tmp_path: Path) -> None:
    import sqlite3

    path = tmp_path / "history.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE history_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO history_meta(key, value) VALUES ('schema_version', '2')"
        )

    repo = open_history_analytics_repository(path)
    result = HistoricalAnalysisService(repo).discover(
        AnalysisPeriod.HOURS_24,
        end=T0,
    )

    assert result.state is HistoricalAnalysisState.UNSUPPORTED


def test_open_time_corruption_is_normalized(tmp_path: Path) -> None:
    path = tmp_path / "history.sqlite3"
    path.write_bytes(b"not a sqlite database")

    repo = open_history_analytics_repository(path)
    result = HistoricalAnalysisService(repo).discover(
        AnalysisPeriod.HOURS_24,
        end=T0,
    )

    assert result.state is HistoricalAnalysisState.UNAVAILABLE
