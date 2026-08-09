from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.history import (
    HistoricalSnapshot,
    HistoricalWindowObservation,
    HistoricalWindowSample,
)
from codexbar.domain.models import Fraction, UsageSource, UsageWindowId
from codexbar.infrastructure.history_sqlite import (
    _format_timestamp,
    _observation_key,
    _parse_timestamp,
)

T0 = datetime(2026, 8, 9, 12, 0, 1, 123456, tzinfo=UTC)


def historical_snapshot(observed_at: datetime = T0) -> HistoricalSnapshot:
    return HistoricalSnapshot(
        observed_at=observed_at,
        source=UsageSource.MOCK,
        windows=(
            HistoricalWindowObservation(
                window_id=UsageWindowId("weekly"),
                label="Weekly",
                remaining=Fraction(Decimal("0.4200")),
                resets_at=observed_at + timedelta(days=1),
            ),
        ),
        rate_limit_reached_type="weekly",
    )


def test_timestamp_round_trip_is_canonical_utc() -> None:
    encoded = _format_timestamp(T0)
    decoded = _parse_timestamp(encoded)

    assert encoded == "2026-08-09T12:00:01.123456+00:00"
    assert decoded == T0


def test_observation_key_is_deterministic_and_time_sensitive() -> None:
    first = _observation_key(historical_snapshot())
    repeated = _observation_key(historical_snapshot())
    later = _observation_key(historical_snapshot(T0 + timedelta(seconds=1)))

    assert first == repeated
    assert first != later


def test_window_sample_preserves_temporal_context() -> None:
    observation = HistoricalWindowObservation(
        window_id=UsageWindowId("weekly"),
        label="Weekly",
        remaining=Fraction(Decimal("0.42")),
    )
    sample = HistoricalWindowSample(
        observed_at=T0,
        source=UsageSource.MOCK,
        observation=observation,
    )

    assert sample.observed_at == T0
    assert sample.observation is observation
