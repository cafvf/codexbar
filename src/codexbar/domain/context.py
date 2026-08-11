from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import StrEnum

from codexbar.domain.models import Fraction, UsageWindowId

_CONTEXT_TOLERANCE_DIVISOR = 20  # alpha = 0.05 exactly
_CONTEXT_TOLERANCE_CAP = timedelta(hours=2)


def _require_aware(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, slots=True, order=True)
class TimeToReset:
    """Non-negative time remaining until an authoritative reset instant."""

    duration: timedelta

    def __post_init__(self) -> None:
        if self.duration < timedelta(0):
            raise ValueError("time to reset must not be negative")

    @classmethod
    def from_instants(cls, *, observed_at: datetime, resets_at: datetime) -> TimeToReset:
        observed_utc = _require_aware(observed_at, "observed_at")
        reset_utc = _require_aware(resets_at, "resets_at")
        return cls(reset_utc - observed_utc)


@dataclass(frozen=True, slots=True)
class CycleIdentity:
    """Authoritative contextual cycle identity."""

    window_id: UsageWindowId
    resets_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resets_at",
            _require_aware(self.resets_at, "resets_at"),
        )


@dataclass(frozen=True, slots=True)
class ContextObservation:
    """One real retained observation eligible for contextual evaluation."""

    window_id: UsageWindowId
    observed_at: datetime
    remaining: Fraction
    resets_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observed_at",
            _require_aware(self.observed_at, "observed_at"),
        )
        if self.resets_at is not None:
            object.__setattr__(
                self,
                "resets_at",
                _require_aware(self.resets_at, "resets_at"),
            )


@dataclass(frozen=True, slots=True)
class ComparableCycleObservation:
    """The single selected real observation contributed by one historical cycle."""

    cycle: CycleIdentity
    observed_at: datetime
    remaining: Fraction
    time_to_reset: TimeToReset

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "observed_at",
            _require_aware(self.observed_at, "observed_at"),
        )


@dataclass(frozen=True, slots=True)
class ContextReferenceSet:
    """Independent-cycle historical references at one current time-to-reset coordinate."""

    current_cycle: CycleIdentity
    current_time_to_reset: TimeToReset
    observations: tuple[ComparableCycleObservation, ...]

    def __post_init__(self) -> None:
        identities = [observation.cycle for observation in self.observations]
        if len(identities) != len(set(identities)):
            raise ValueError("context reference set must contain at most one observation per cycle")
        if self.current_cycle in identities:
            raise ValueError("current cycle must not appear in context reference set")

    @property
    def cycle_count(self) -> int:
        return len(self.observations)


class ContextSelectionState(StrEnum):
    READY = "ready"
    CURRENT_RESET_MISSING = "current_reset_missing"
    CURRENT_RESET_INVALID = "current_reset_invalid"
    NO_HISTORICAL_OBSERVATIONS = "no_historical_observations"
    NO_IDENTIFIABLE_CYCLES = "no_identifiable_cycles"
    NO_COMPARABLE_CYCLES = "no_comparable_cycles"


@dataclass(frozen=True, slots=True)
class ContextReferenceSelection:
    """Explicit result of pure domain reference selection."""

    state: ContextSelectionState
    reference_set: ContextReferenceSet | None = None

    def __post_init__(self) -> None:
        if self.state is ContextSelectionState.READY and self.reference_set is None:
            raise ValueError("ready context selection requires a reference set")
        if self.state is not ContextSelectionState.READY and self.reference_set is not None:
            raise ValueError("non-ready context selection must not contain a reference set")


class ContextCoverage(StrEnum):
    INSUFFICIENT = "insufficient"
    SPARSE = "sparse"
    LIMITED = "limited"
    ESTABLISHED = "established"

    @classmethod
    def from_cycle_count(cls, cycle_count: int) -> ContextCoverage:
        if cycle_count < 0:
            raise ValueError("cycle count must not be negative")
        if cycle_count <= 2:
            return cls.INSUFFICIENT
        if cycle_count <= 4:
            return cls.SPARSE
        if cycle_count <= 9:
            return cls.LIMITED
        return cls.ESTABLISHED


@dataclass(frozen=True, slots=True)
class ContextRank:
    """Factual comparison counts for the current value against historical values."""

    greater_count: int
    equal_count: int
    lower_count: int

    def __post_init__(self) -> None:
        if min(self.greater_count, self.equal_count, self.lower_count) < 0:
            raise ValueError("rank counts must not be negative")

    @property
    def total_count(self) -> int:
        return self.greater_count + self.equal_count + self.lower_count

    @property
    def has_ties(self) -> bool:
        return self.equal_count > 0

    def describe(self) -> str:
        return (
            f"{self.greater_count} historical values greater than current, "
            f"{self.equal_count} equal to current, "
            f"{self.lower_count} lower than current"
        )


@dataclass(frozen=True, slots=True)
class ContextEmpiricalSummary:
    """Coverage-adaptive descriptive summary over independent comparable cycles."""

    coverage: ContextCoverage
    cycle_count: int
    rank: ContextRank | None = None
    observed_min: Decimal | None = None
    observed_max: Decimal | None = None
    median: Decimal | None = None
    q25: Decimal | None = None
    q75: Decimal | None = None

    def __post_init__(self) -> None:
        if self.coverage is not ContextCoverage.from_cycle_count(self.cycle_count):
            raise ValueError("coverage must match cycle count")
        self._validate_statistic_values()
        self._validate_rank_count()
        self._validate_ordering()
        self._validate_coverage_shape()

    def _validate_statistic_values(self) -> None:
        for value in self._statistics():
            if value is not None and (
                not value.is_finite() or not Decimal("0") <= value <= Decimal("1")
            ):
                raise ValueError("context summary statistics must be finite fractions")

    def _validate_rank_count(self) -> None:
        if self.rank is not None and self.rank.total_count != self.cycle_count:
            raise ValueError("rank total must match independent cycle count")

    def _validate_ordering(self) -> None:
        if (
            self.observed_min is not None
            and self.observed_max is not None
            and self.observed_min > self.observed_max
        ):
            raise ValueError("observed context range must be ordered")
        if (
            self.observed_min is not None
            and self.median is not None
            and self.observed_max is not None
            and not self.observed_min <= self.median <= self.observed_max
        ):
            raise ValueError("observed range and median must be ordered")
        if (
            self.q25 is not None
            and self.median is not None
            and self.q75 is not None
            and not self.q25 <= self.median <= self.q75
        ):
            raise ValueError("established quartiles and median must be ordered")

    def _validate_coverage_shape(self) -> None:
        if self.coverage is ContextCoverage.INSUFFICIENT:
            self._validate_insufficient_shape()
        elif self.coverage is ContextCoverage.SPARSE:
            self._validate_sparse_shape()
        elif self.coverage is ContextCoverage.LIMITED:
            self._validate_limited_shape()
        else:
            self._validate_established_shape()

    def _validate_insufficient_shape(self) -> None:
        if self.rank is not None or any(value is not None for value in self._statistics()):
            raise ValueError("insufficient coverage must suppress unsupported statistics")

    def _validate_sparse_shape(self) -> None:
        if self.observed_min is None or self.observed_max is None:
            raise ValueError("sparse coverage requires observed min and max")
        if any(value is not None for value in (self.median, self.q25, self.q75)):
            raise ValueError("sparse coverage must suppress median and quartiles")

    def _validate_limited_shape(self) -> None:
        if any(
            value is None
            for value in (self.rank, self.observed_min, self.observed_max, self.median)
        ):
            raise ValueError("limited coverage requires rank, range and median")
        if self.q25 is not None or self.q75 is not None:
            raise ValueError("limited coverage must suppress quartiles")

    def _validate_established_shape(self) -> None:
        if any(value is None for value in (self.rank, self.median, self.q25, self.q75)):
            raise ValueError("established coverage requires rank, median and quartiles")
        if self.observed_min is not None or self.observed_max is not None:
            raise ValueError("established coverage uses quartile band, not observed range")

    def _statistics(self) -> tuple[Decimal | None, ...]:
        return (
            self.observed_min,
            self.observed_max,
            self.median,
            self.q25,
            self.q75,
        )


def contextual_tolerance(current: TimeToReset) -> timedelta:
    """Return min(0.05*h*, 2 hours) using exact integer scaling."""

    return min(current.duration / _CONTEXT_TOLERANCE_DIVISOR, _CONTEXT_TOLERANCE_CAP)


def select_context_references(
    *,
    current: ContextObservation,
    historical: Iterable[ContextObservation],
) -> ContextReferenceSelection:
    """Select at most one nearest real observation from each eligible historical cycle."""

    if current.resets_at is None:
        return ContextReferenceSelection(ContextSelectionState.CURRENT_RESET_MISSING)

    try:
        current_time = TimeToReset.from_instants(
            observed_at=current.observed_at,
            resets_at=current.resets_at,
        )
    except ValueError:
        return ContextReferenceSelection(ContextSelectionState.CURRENT_RESET_INVALID)

    history = tuple(historical)
    if not history:
        return ContextReferenceSelection(ContextSelectionState.NO_HISTORICAL_OBSERVATIONS)

    current_cycle = CycleIdentity(current.window_id, current.resets_at)
    grouped, identifiable_cycle_seen = _group_historical_cycles(
        current=current,
        current_cycle=current_cycle,
        historical=history,
    )
    if not identifiable_cycle_seen:
        return ContextReferenceSelection(ContextSelectionState.NO_IDENTIFIABLE_CYCLES)
    if not grouped:
        return ContextReferenceSelection(ContextSelectionState.NO_COMPARABLE_CYCLES)

    selected = _select_comparable_cycles(grouped, current_time)
    if not selected:
        return ContextReferenceSelection(ContextSelectionState.NO_COMPARABLE_CYCLES)

    return ContextReferenceSelection(
        state=ContextSelectionState.READY,
        reference_set=ContextReferenceSet(
            current_cycle=current_cycle,
            current_time_to_reset=current_time,
            observations=selected,
        ),
    )


def _group_historical_cycles(
    *,
    current: ContextObservation,
    current_cycle: CycleIdentity,
    historical: Iterable[ContextObservation],
) -> tuple[dict[CycleIdentity, list[ComparableCycleObservation]], bool]:
    grouped: dict[CycleIdentity, list[ComparableCycleObservation]] = {}
    identifiable_cycle_seen = False

    for observation in historical:
        candidate = _comparable_candidate(current, observation)
        if candidate is None:
            continue
        identifiable_cycle_seen = True
        if candidate.cycle == current_cycle:
            continue
        grouped.setdefault(candidate.cycle, []).append(candidate)

    return grouped, identifiable_cycle_seen


def _comparable_candidate(
    current: ContextObservation,
    observation: ContextObservation,
) -> ComparableCycleObservation | None:
    if observation.window_id != current.window_id:
        return None
    if observation.observed_at > current.observed_at or observation.resets_at is None:
        return None

    try:
        time_to_reset = TimeToReset.from_instants(
            observed_at=observation.observed_at,
            resets_at=observation.resets_at,
        )
    except ValueError:
        return None

    cycle = CycleIdentity(observation.window_id, observation.resets_at)
    return ComparableCycleObservation(
        cycle=cycle,
        observed_at=observation.observed_at,
        remaining=observation.remaining,
        time_to_reset=time_to_reset,
    )


def _select_comparable_cycles(
    grouped: dict[CycleIdentity, list[ComparableCycleObservation]],
    current_time: TimeToReset,
) -> tuple[ComparableCycleObservation, ...]:
    tolerance = contextual_tolerance(current_time)
    selected = []
    for cycle in sorted(grouped, key=lambda identity: identity.resets_at):
        nearest = _nearest_observation(grouped[cycle], current_time)
        mismatch = abs(nearest.time_to_reset.duration - current_time.duration)
        if mismatch <= tolerance:
            selected.append(nearest)
    return tuple(selected)


def empirical_median(values: Sequence[Decimal]) -> Decimal:
    """Return the exact Decimal median of a non-empty sequence."""

    ordered = sorted(values)
    if not ordered:
        raise ValueError("median requires at least one value")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / Decimal(2)


def empirical_quantile(values: Sequence[Decimal], p: Decimal) -> Decimal:
    """Linear interpolation at fractional index (N - 1) * p."""

    if not Decimal(0) <= p <= Decimal(1):
        raise ValueError("quantile probability must be between zero and one")
    ordered = sorted(values)
    if not ordered:
        raise ValueError("quantile requires at least one value")
    if len(ordered) == 1:
        return ordered[0]

    index = Decimal(len(ordered) - 1) * p
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    fraction = index - Decimal(lower_index)
    lower = ordered[lower_index]
    upper = ordered[upper_index]
    return lower + (upper - lower) * fraction


def empirical_rank(*, current: Decimal, historical: Sequence[Decimal]) -> ContextRank:
    """Return strict greater/equal/lower counts, preserving ties explicitly."""

    return ContextRank(
        greater_count=sum(value > current for value in historical),
        equal_count=sum(value == current for value in historical),
        lower_count=sum(value < current for value in historical),
    )


def summarize_context_reference_set(
    *,
    current_remaining: Fraction,
    reference_set: ContextReferenceSet,
) -> ContextEmpiricalSummary:
    """Build the frozen coverage-adaptive descriptive summary."""

    values = tuple(observation.remaining.value for observation in reference_set.observations)
    coverage = ContextCoverage.from_cycle_count(len(values))

    if coverage is ContextCoverage.INSUFFICIENT:
        return ContextEmpiricalSummary(
            coverage=coverage,
            cycle_count=len(values),
        )

    rank = empirical_rank(current=current_remaining.value, historical=values)

    if coverage is ContextCoverage.SPARSE:
        return ContextEmpiricalSummary(
            coverage=coverage,
            cycle_count=len(values),
            rank=rank,
            observed_min=min(values),
            observed_max=max(values),
        )

    median = empirical_median(values)
    if coverage is ContextCoverage.LIMITED:
        return ContextEmpiricalSummary(
            coverage=coverage,
            cycle_count=len(values),
            rank=rank,
            observed_min=min(values),
            observed_max=max(values),
            median=median,
        )

    return ContextEmpiricalSummary(
        coverage=coverage,
        cycle_count=len(values),
        rank=rank,
        median=median,
        q25=empirical_quantile(values, Decimal("0.25")),
        q75=empirical_quantile(values, Decimal("0.75")),
    )


def _nearest_observation(
    observations: Iterable[ComparableCycleObservation],
    current_time: TimeToReset,
) -> ComparableCycleObservation:
    iterator = iter(observations)
    try:
        best = next(iterator)
    except StopIteration as exc:
        raise ValueError("cannot select nearest observation from an empty cycle") from exc

    best_mismatch = abs(best.time_to_reset.duration - current_time.duration)
    for candidate in iterator:
        mismatch = abs(candidate.time_to_reset.duration - current_time.duration)
        if mismatch < best_mismatch or (
            mismatch == best_mismatch and candidate.observed_at > best.observed_at
        ):
            best = candidate
            best_mismatch = mismatch
    return best
