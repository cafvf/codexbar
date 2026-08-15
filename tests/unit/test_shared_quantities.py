from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.analytics import FractionDelta as AnalyticsFractionDelta
from codexbar.domain.context import TimeToReset as ContextTimeToReset
from codexbar.domain.quantities import FractionDelta, TimeToReset


def test_historical_quantity_imports_reexport_the_neutral_owner() -> None:
    assert AnalyticsFractionDelta is FractionDelta
    assert ContextTimeToReset is TimeToReset


def test_neutral_quantities_preserve_existing_value_semantics() -> None:
    observed = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    reset = observed + timedelta(hours=2)

    assert TimeToReset.from_instants(
        observed_at=observed,
        resets_at=reset,
    ).duration == timedelta(hours=2)
    assert FractionDelta(Decimal("-0.125")).value == Decimal("-0.125")
