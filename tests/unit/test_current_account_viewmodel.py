from datetime import UTC, datetime
from decimal import Decimal

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import ResetCreditReadResult
from codexbar.domain.settings import AppSettings
from codexbar.ui.current_account_viewmodel import (
    CurrentAccountPresenter,
    ResetCurrentKind,
)

NOW = datetime(2026, 8, 10, 12, tzinfo=UTC)


class Reader:
    def read_account_rate_limits(self):
        return AccountRateLimitsObservation(
            UsageSnapshot(
                (UsageWindow(UsageWindowId("window_300m"), "5 hours", Fraction(Decimal("0.5"))),),
                NOW,
                UsageSource.MOCK,
            ),
            ResetCreditReadResult.unavailable("fixture"),
        )


def test_presenter_uses_captured_observation_without_second_read() -> None:
    source = Reader()
    latest = LatestAccountObservationReader(source)
    latest.read_account_rate_limits()
    presenter = CurrentAccountPresenter(
        latest,
        AppSettings.defaults(),
        lambda: ResetLedgerProjection(),
        clock=lambda: NOW,
    )

    state = presenter.current()

    assert state is not None
    assert state.reset.kind is ResetCurrentKind.UNAVAILABLE
    assert state.usage.windows[0].percent_left == 50
