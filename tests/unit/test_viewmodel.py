from datetime import UTC, datetime
from decimal import Decimal

from codexbar.domain.models import (
    Fraction,
    Freshness,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.ui.viewmodel import UsageViewModel


def test_viewmodel_maps_snapshot_without_source_knowledge() -> None:
    now = datetime.now(UTC)
    snapshot = UsageSnapshot(
        (UsageWindow(UsageWindowId("weekly"), "Weekly", Fraction(Decimal("0.81"))),),
        now,
        UsageSource.CODEX_APP_SERVER,
        Freshness.STALE,
        rate_limit_reached_type="weekly",
    )
    state = UsageViewModel.from_snapshot(snapshot)
    assert state.windows[0].percent_left == 81
    assert state.stale is True
    assert state.rate_limit_reached_type == "weekly"


def test_viewmodel_falls_back_to_semantic_label_for_legacy_ids() -> None:
    now = datetime.now(UTC)
    snapshot = UsageSnapshot(
        (UsageWindow(UsageWindowId("weekly"), "Weekly", Fraction(Decimal("0.62"))),),
        now,
        UsageSource.MOCK,
    )

    state = UsageViewModel.from_snapshot(snapshot)

    assert state.windows[0].short_label == "W"
    assert state.glance_text == "W: 62%"
