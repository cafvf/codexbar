from __future__ import annotations

import sqlite3
from collections.abc import Callable
from concurrent.futures import Executor, Future
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.context import (
    HistoricalContextReason,
    HistoricalContextService,
    HistoricalContextState,
)
from codexbar.application.history import HistoryInterval, HistorySchemaError
from codexbar.application.reset_ledger import ResetLedgerSchemaError
from codexbar.application.reset_monitor import (
    OpportunityPriority,
    ResetAdvice,
    ResetOpportunityPolicy,
    ResetSituation,
)
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.context import (
    ContextCoverage,
    ContextEmpiricalSummary,
    ContextObservation,
    ContextRank,
)
from codexbar.domain.errors import UsageSchemaError, UsageSourceUnavailableError
from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.domain.reset import (
    ExpiryKnowledge,
    ResetCreditDetail,
    ResetCreditId,
    ResetCreditReadResult,
)
from codexbar.domain.settings import AppSettings
from codexbar.infrastructure.history_sqlite import SqliteHistoryRepository
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
from codexbar.ui.controller import TrayController
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter

NOW = datetime(2026, 8, 10, 20, 0, tzinfo=UTC)
WINDOW = UsageWindowId("window_300m")


def usage(*, freshness: Freshness = Freshness.CURRENT) -> UsageSnapshot:
    return UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW,
                "5 hours",
                Fraction(Decimal("0.44")),
                resets_at=NOW + timedelta(hours=2),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
        freshness=freshness,
    )


def account(*, freshness: Freshness = Freshness.CURRENT) -> AccountRateLimitsObservation:
    return AccountRateLimitsObservation(
        usage=usage(freshness=freshness),
        reset_credits=ResetCreditReadResult.unavailable("fixture"),
    )


class FailOnSecondRead:
    def __init__(self) -> None:
        self.calls = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.calls += 1
        if self.calls == 1:
            return account()
        raise UsageSourceUnavailableError("offline")


def test_latest_account_observation_transitions_whole_composed_state_to_stale() -> None:
    reader = LatestAccountObservationReader(FailOnSecondRead())
    first = reader.read_account_rate_limits()
    assert first.usage.freshness is Freshness.CURRENT

    with pytest.raises(UsageSourceUnavailableError):
        reader.read_account_rate_limits()

    latest = reader.latest
    assert latest is not None
    assert latest.usage.freshness is Freshness.STALE
    assert latest.reset_credits.inventory is None


class SchemaFailOnSecondRead:
    def __init__(self) -> None:
        self.calls = 0

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        self.calls += 1
        if self.calls == 1:
            return account()
        raise UsageSchemaError("unsupported upstream schema")


def test_schema_failure_invalidates_current_derived_state() -> None:
    reader = LatestAccountObservationReader(SchemaFailOnSecondRead())
    reader.read_account_rate_limits()

    with pytest.raises(UsageSchemaError):
        reader.read_account_rate_limits()

    latest = reader.latest
    assert latest is not None
    assert latest.usage.freshness is Freshness.STALE
    assert latest.reset_credits.inventory is None


def test_stale_usage_withholds_budget_and_control_advice() -> None:
    reader = LatestAccountObservationReader(SchemaFailOnSecondRead())
    reader.read_account_rate_limits()
    with pytest.raises(UsageSchemaError):
        reader.read_account_rate_limits()

    presenter = CurrentAccountPresenter(
        reader,
        AppSettings.defaults(),
        lambda: ResetLedgerProjection(),
        clock=lambda: NOW,
    )
    state = presenter.current()

    assert state is not None
    assert state.usage.stale
    assert state.budget.windows == ()
    assert "not current" in state.budget.advice.reason
    assert not state.redeem.available


class MustNotQueryContextHistory:
    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        raise AssertionError("stale Context must not query history")


def test_stale_current_withholds_context_before_history_io() -> None:
    service = HistoricalContextService(MustNotQueryContextHistory())
    result = service.evaluate(current=usage(freshness=Freshness.STALE), window_id=WINDOW)
    assert result.state is HistoricalContextState.UNAVAILABLE
    assert result.reason is HistoricalContextReason.CURRENT_NOT_CURRENT
    assert result.comparable_cycle_count is None


def test_context_summary_rejects_rank_count_mismatch() -> None:
    with pytest.raises(ValueError, match="rank total"):
        ContextEmpiricalSummary(
            coverage=ContextCoverage.LIMITED,
            cycle_count=5,
            rank=ContextRank(1, 1, 1),
            observed_min=Decimal("0.1"),
            observed_max=Decimal("0.9"),
            median=Decimal("0.5"),
        )


def test_expired_credit_is_not_an_upcoming_reset_opportunity() -> None:
    expired = ResetCreditDetail(
        credit_id=ResetCreditId("expired"),
        reset_type="fixture",
        status="available",
        granted_at=NOW - timedelta(days=1),
        expiry=ExpiryKnowledge.expires_at(NOW - timedelta(minutes=1)),
    )
    situation = ResetSituation(account(), (), (expired,), ())
    advice: ResetAdvice = ResetOpportunityPolicy().assess(situation, now=NOW)
    assert advice.priority is OpportunityPriority.NONE


class DeferredExecutor(Executor):
    def __init__(self) -> None:
        self.future: Future[UsageSnapshot] = Future()

    def submit(
        self,
        fn: Callable[..., Any],
        /,
        *args: Any,
        **kwargs: Any,
    ) -> Future[Any]:
        return self.future

    def shutdown(
        self,
        wait: bool = True,
        *,
        cancel_futures: bool = False,
    ) -> None:
        return None


class FakeRefreshCoordinator:
    def __init__(self) -> None:
        self.accepted: UsageSnapshot | None = None

    def refresh(self) -> UsageSnapshot:
        raise AssertionError("deferred executor must not execute refresh inline")

    def accept_snapshot(self, snapshot: UsageSnapshot) -> UsageSnapshot:
        self.accepted = snapshot
        return snapshot


def test_post_command_snapshot_invalidates_older_inflight_refresh_result() -> None:
    executor = DeferredExecutor()
    coordinator = FakeRefreshCoordinator()
    controller = TrayController(coordinator, executor=executor)

    assert controller.start_refresh()
    adopted = UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW,
                "5 hours",
                Fraction(Decimal("0.20")),
                resets_at=NOW + timedelta(hours=2),
            ),
        ),
        observed_at=NOW + timedelta(seconds=1),
        source=UsageSource.MOCK,
    )
    controller.adopt_snapshot(adopted)

    older = UsageSnapshot(
        windows=(
            UsageWindow(
                WINDOW,
                "5 hours",
                Fraction(Decimal("0.80")),
                resets_at=NOW + timedelta(hours=2),
            ),
        ),
        observed_at=NOW,
        source=UsageSource.MOCK,
    )
    executor.future.set_result(older)
    state = controller.poll()

    assert state.usage is not None
    assert state.usage.windows[0].percent_left == 20
    assert coordinator.accepted is adopted


def _history_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE history_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE snapshots (
            id INTEGER PRIMARY KEY,
            observed_at_utc TEXT NOT NULL,
            source TEXT NOT NULL,
            rate_limit_reached_type TEXT,
            observation_key TEXT NOT NULL UNIQUE
        );
        CREATE TABLE window_observations (
            snapshot_id INTEGER NOT NULL,
            window_id TEXT NOT NULL,
            label TEXT NOT NULL,
            remaining TEXT NOT NULL,
            resets_at_utc TEXT,
            PRIMARY KEY (snapshot_id, window_id),
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id) ON DELETE CASCADE
        );
        CREATE INDEX idx_snapshots_observed_at ON snapshots(observed_at_utc, id);
        CREATE INDEX idx_windows_window_id_snapshot
            ON window_observations(window_id, snapshot_id);
        INSERT INTO history_meta(key, value)
            VALUES ('schema_version', '1');
        """
    )


def _reset_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE reset_ledger_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE reset_events (
            sequence INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            event_type TEXT NOT NULL,
            occurred_at_utc TEXT NOT NULL,
            provenance TEXT NOT NULL,
            payload_version INTEGER NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE INDEX idx_reset_events_occurred_at
            ON reset_events(occurred_at_utc, sequence);
        INSERT INTO reset_ledger_meta(key, value)
            VALUES ('schema_version', '1');
        """
    )


def test_repositories_accept_the_expected_operational_schema(
    tmp_path: Path,
) -> None:
    history = tmp_path / "history.sqlite3"
    with sqlite3.connect(history) as connection:
        _history_schema(connection)
    SqliteHistoryRepository(history)

    reset = tmp_path / "reset.sqlite3"
    with sqlite3.connect(reset) as connection:
        _reset_schema(connection)
    SqliteResetEventRepository(reset)


def test_history_repository_rejects_missing_operational_index(
    tmp_path: Path,
) -> None:
    history = tmp_path / "history.sqlite3"
    with sqlite3.connect(history) as connection:
        _history_schema(connection)
        connection.execute("DROP INDEX idx_windows_window_id_snapshot")

    with pytest.raises(
        HistorySchemaError,
        match="idx_windows_window_id_snapshot",
    ):
        SqliteHistoryRepository(history)


def test_reset_repository_rejects_missing_event_uniqueness(
    tmp_path: Path,
) -> None:
    reset = tmp_path / "reset.sqlite3"
    with sqlite3.connect(reset) as connection:
        connection.execute(
            "CREATE TABLE reset_ledger_meta "
            "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO reset_ledger_meta(key, value) VALUES (?, ?)",
            ("schema_version", "1"),
        )
        connection.execute(
            "CREATE TABLE reset_events ("
            "sequence INTEGER PRIMARY KEY AUTOINCREMENT,"
            "event_id TEXT NOT NULL,"
            "event_type TEXT NOT NULL,"
            "occurred_at_utc TEXT NOT NULL,"
            "provenance TEXT NOT NULL,"
            "payload_version INTEGER NOT NULL,"
            "payload_json TEXT NOT NULL"
            ")"
        )
        connection.execute(
            "CREATE INDEX idx_reset_events_occurred_at "
            "ON reset_events(occurred_at_utc, sequence)"
        )

    with pytest.raises(
        ResetLedgerSchemaError,
        match="event-id uniqueness",
    ):
        SqliteResetEventRepository(reset)
