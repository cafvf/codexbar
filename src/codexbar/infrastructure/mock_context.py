from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from codexbar.application.context import ContextHistoryRepository
from codexbar.application.history import HistoryInterval
from codexbar.domain.context import ContextObservation
from codexbar.domain.models import Fraction, UsageWindowId


class MockContextHistoryRepository(ContextHistoryRepository):
    """Deterministic Context fixture for physical UI validation."""

    def query_candidates(
        self,
        window_id: UsageWindowId,
        interval: HistoryInterval,
    ) -> tuple[ContextObservation, ...]:
        values = _VALUES_BY_WINDOW.get(window_id.value, ())
        reset_offset = _RESET_OFFSET_BY_WINDOW.get(window_id.value)
        if reset_offset is None:
            return ()

        observations = []
        for index, value in enumerate(values):
            reset = interval.end - timedelta(days=index + 1) + reset_offset
            observations.append(
                ContextObservation(
                    window_id=window_id,
                    observed_at=reset - reset_offset,
                    remaining=Fraction(Decimal(value)),
                    resets_at=reset,
                )
            )
        return tuple(observations)


_VALUES_BY_WINDOW = {
    # Sparse: observed range only.
    "window_300m": ("0.55", "0.72", "0.80"),
    # Established: current mock Weekly is exactly 0.44. Four equal historical
    # values make tie handling visually unmistakable in the physical smoke.
    "window_10080m": (
        "0.20",
        "0.30",
        "0.40",
        "0.44",
        "0.44",
        "0.44",
        "0.44",
        "0.60",
        "0.70",
        "0.80",
    ),
}

_RESET_OFFSET_BY_WINDOW = {
    "window_300m": timedelta(hours=2),
    "window_10080m": timedelta(days=3),
}
