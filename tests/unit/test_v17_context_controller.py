from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from threading import Event

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.application.revisions import CurrentRevision, HistoryRevision
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId
from codexbar.domain.reset import ResetCreditReadResult
from codexbar.ui.context_controller import ContextController, ContextControllerPhase
from codexbar.ui.context_viewmodel import (
    ContextPresentationRequest,
    ContextViewKind,
    ContextViewState,
    ContextWindowViewState,
)

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=UTC)
WINDOW = UsageWindowId("dynamic")


def _observation() -> AccountRateLimitsObservation:
    return AccountRateLimitsObservation(
        usage=UsageSnapshot(
            windows=(
                UsageWindow(
                    WINDOW,
                    "Dynamic",
                    Fraction(Decimal("0.40")),
                    resets_at=NOW + timedelta(hours=5),
                ),
            ),
            observed_at=NOW,
            source=UsageSource.MOCK,
        ),
        reset_credits=ResetCreditReadResult.unavailable("not relevant"),
    )


class FakeContextSource:
    def __init__(self) -> None:
        self.current_revision = CurrentRevision(1)
        self.history_revision = HistoryRevision(1)
        self.gate = Event()
        self.block = False
        self.fail_once = False

    def capture_request(self) -> ContextPresentationRequest:
        return ContextPresentationRequest(
            _observation(),
            self.current_revision,
            self.history_revision,
        )

    def current_identity(self) -> tuple[CurrentRevision, HistoryRevision]:
        return self.current_revision, self.history_revision

    def evaluate_request(self, request: ContextPresentationRequest) -> ContextViewState:
        if self.block:
            self.gate.wait(timeout=2.0)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("obsolete failure")
        return ContextViewState(
            (
                ContextWindowViewState(
                    window_id=WINDOW,
                    label=f"h{request.history_revision.value}",
                    kind=ContextViewKind.UNAVAILABLE,
                    comparable_cycle_count=0,
                    status_text="test",
                ),
            )
        )


def _settle(controller: ContextController, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        controller.poll()
        if not controller.busy and controller.state.phase is not ContextControllerPhase.LOADING:
            return
        time.sleep(0.002)
    raise AssertionError("Context controller did not settle")


def test_task_740_741_context_work_runs_through_async_controller() -> None:
    source = FakeContextSource()
    controller = ContextController(source)
    try:
        assert controller.start()
        assert controller.state.phase is ContextControllerPhase.LOADING
        _settle(controller)
        assert controller.state.phase is ContextControllerPhase.READY
        assert controller.state.view.windows[0].label == "h1"
    finally:
        controller.close()


def test_task_742_obsolete_revision_result_is_rejected_and_recomputed() -> None:
    source = FakeContextSource()
    source.block = True
    controller = ContextController(source)
    try:
        assert controller.start()
        source.history_revision = HistoryRevision(2)
        source.gate.set()
        _settle(controller)
        assert controller.state.phase is ContextControllerPhase.READY
        assert controller.state.view.windows[0].label == "h2"
    finally:
        controller.close()


def test_task_742_obsolete_error_is_rejected_and_recomputed() -> None:
    source = FakeContextSource()
    source.block = True
    source.fail_once = True
    controller = ContextController(source)
    try:
        assert controller.start()
        source.history_revision = HistoryRevision(3)
        source.gate.set()
        _settle(controller)
        assert controller.state.phase is ContextControllerPhase.READY
        assert controller.state.view.windows[0].label == "h3"
    finally:
        controller.close()


def test_task_746_close_suppresses_late_context_adoption() -> None:
    source = FakeContextSource()
    source.block = True
    controller = ContextController(source)
    assert controller.start()
    controller.close()
    source.gate.set()
    time.sleep(0.01)
    assert controller.state.phase is not ContextControllerPhase.READY
