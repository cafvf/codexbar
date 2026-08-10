from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from codexbar.domain.context import (
    ComparableCycleObservation,
    ContextCoverage,
    ContextEmpiricalSummary,
    ContextRank,
    ContextReferenceSet,
    CycleIdentity,
    TimeToReset,
    empirical_median,
    empirical_quantile,
    empirical_rank,
    summarize_context_reference_set,
)
from codexbar.domain.models import Fraction, UsageWindowId

WINDOW = UsageWindowId("dynamic-window")
NOW = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)


def reference_set(values: list[str]) -> ContextReferenceSet:
    observations = []
    for index, value in enumerate(values):
        reset = NOW - timedelta(days=index + 1)
        observations.append(
            ComparableCycleObservation(
                cycle=CycleIdentity(WINDOW, reset),
                observed_at=reset - timedelta(hours=10),
                remaining=Fraction(Decimal(value)),
                time_to_reset=TimeToReset(timedelta(hours=10)),
            )
        )
    return ContextReferenceSet(
        current_cycle=CycleIdentity(WINDOW, NOW + timedelta(hours=10)),
        current_time_to_reset=TimeToReset(timedelta(hours=10)),
        observations=tuple(observations),
    )


@pytest.mark.parametrize(
    ("cycle_count", "expected"),
    [
        (0, ContextCoverage.INSUFFICIENT),
        (2, ContextCoverage.INSUFFICIENT),
        (3, ContextCoverage.SPARSE),
        (4, ContextCoverage.SPARSE),
        (5, ContextCoverage.LIMITED),
        (9, ContextCoverage.LIMITED),
        (10, ContextCoverage.ESTABLISHED),
    ],
)
def test_tv_1609_coverage_boundaries(cycle_count: int, expected: ContextCoverage) -> None:
    assert ContextCoverage.from_cycle_count(cycle_count) is expected


def test_task_630_negative_cycle_count_is_invalid() -> None:
    with pytest.raises(ValueError, match="negative"):
        ContextCoverage.from_cycle_count(-1)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["0.20", "0.40", "0.60"], Decimal("0.40")),
        (["0.20", "0.40", "0.60", "0.80"], Decimal("0.50")),
    ],
)
def test_task_631_decimal_median_odd_and_even(values: list[str], expected: Decimal) -> None:
    assert empirical_median([Decimal(value) for value in values]) == expected


def test_task_631_median_rejects_empty_sequence() -> None:
    with pytest.raises(ValueError, match="at least one"):
        empirical_median([])


def test_tv_1605_median_min_max_rank_and_limited_coverage() -> None:
    refs = reference_set(["0.20", "0.30", "0.40", "0.50", "0.60"])

    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.35")),
        reference_set=refs,
    )

    assert summary.coverage is ContextCoverage.LIMITED
    assert summary.cycle_count == 5
    assert summary.median == Decimal("0.40")
    assert summary.observed_min == Decimal("0.20")
    assert summary.observed_max == Decimal("0.60")
    assert summary.rank == ContextRank(greater_count=3, equal_count=0, lower_count=2)
    assert summary.q25 is None
    assert summary.q75 is None


def test_tv_1606_rank_ties_are_explicit_and_human_readable() -> None:
    rank = empirical_rank(
        current=Decimal("0.30"),
        historical=[
            Decimal("0.20"),
            Decimal("0.30"),
            Decimal("0.30"),
            Decimal("0.50"),
        ],
    )

    assert rank == ContextRank(greater_count=1, equal_count=2, lower_count=1)
    assert rank.total_count == 4
    assert rank.has_ties
    assert rank.describe() == "1 historical values greater, 2 equal, 1 lower"


def test_tv_1607_established_quantiles_use_frozen_decimal_convention() -> None:
    values = [Decimal(index) / Decimal(10) for index in range(1, 11)]
    refs = reference_set([str(value) for value in values])

    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.55")),
        reference_set=refs,
    )

    assert empirical_quantile(values, Decimal("0.25")) == Decimal("0.325")
    assert empirical_quantile(values, Decimal("0.75")) == Decimal("0.775")
    assert summary.coverage is ContextCoverage.ESTABLISHED
    assert summary.median == Decimal("0.55")
    assert summary.q25 == Decimal("0.325")
    assert summary.q75 == Decimal("0.775")
    assert summary.observed_min is None
    assert summary.observed_max is None
    assert summary.rank is not None


def test_task_635_quantile_validates_probability_and_empty_input() -> None:
    with pytest.raises(ValueError, match="between zero and one"):
        empirical_quantile([Decimal("0.5")], Decimal("1.01"))
    with pytest.raises(ValueError, match="at least one"):
        empirical_quantile([], Decimal("0.25"))


def test_task_636_sparse_contract_has_range_and_rank_only() -> None:
    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.35")),
        reference_set=reference_set(["0.20", "0.30", "0.50"]),
    )

    assert summary.coverage is ContextCoverage.SPARSE
    assert summary.observed_min == Decimal("0.20")
    assert summary.observed_max == Decimal("0.50")
    assert summary.rank is not None
    assert summary.median is None
    assert summary.q25 is None
    assert summary.q75 is None


def test_task_637_limited_contract_has_median_range_and_rank() -> None:
    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.45")),
        reference_set=reference_set(["0.10", "0.20", "0.30", "0.40", "0.50"]),
    )

    assert summary.coverage is ContextCoverage.LIMITED
    assert summary.median == Decimal("0.30")
    assert summary.observed_min == Decimal("0.10")
    assert summary.observed_max == Decimal("0.50")
    assert summary.rank is not None
    assert summary.q25 is None
    assert summary.q75 is None


def test_task_638_established_contract_has_middle_50_and_no_observed_range() -> None:
    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.50")),
        reference_set=reference_set(
            ["0.10", "0.20", "0.30", "0.40", "0.50", "0.60", "0.70", "0.80", "0.90", "1.00"]
        ),
    )

    assert summary.coverage is ContextCoverage.ESTABLISHED
    assert summary.median == Decimal("0.55")
    assert summary.q25 == Decimal("0.325")
    assert summary.q75 == Decimal("0.775")
    assert summary.rank is not None
    assert summary.observed_min is None
    assert summary.observed_max is None


@pytest.mark.parametrize("values", [[], ["0.20"], ["0.20", "0.40"]])
def test_task_639_insufficient_suppresses_distribution_and_rank(values: list[str]) -> None:
    summary = summarize_context_reference_set(
        current_remaining=Fraction(Decimal("0.30")),
        reference_set=reference_set(values),
    )

    assert summary.coverage is ContextCoverage.INSUFFICIENT
    assert summary.cycle_count == len(values)
    assert summary.rank is None
    assert summary.observed_min is None
    assert summary.observed_max is None
    assert summary.median is None
    assert summary.q25 is None
    assert summary.q75 is None


def test_task_639_summary_rejects_inconsistent_insufficient_payload() -> None:
    with pytest.raises(ValueError, match="suppress"):
        ContextEmpiricalSummary(
            coverage=ContextCoverage.INSUFFICIENT,
            cycle_count=2,
            median=Decimal("0.30"),
        )
