from __future__ import annotations

import time
from threading import Event

from codexbar.application.redeem import RedeemAttempt, RedeemProcessStatus, RedeemResult
from codexbar.application.redeem_execution import (
    RedeemExecutionController,
    RedeemExecutionPhase,
)
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.reset import ResetCreditId


class DelayedManager:
    def __init__(self) -> None:
        self.gate = Event()
        self.calls = 0

    def redeem(self, *, credit_id: ResetCreditId | None = None) -> RedeemResult:
        self.calls += 1
        self.gate.wait(timeout=2.0)
        return RedeemResult(
            RedeemAttempt(
                RedeemAttemptId(f"attempt-{self.calls}"),
                credit_id,
                RedeemProcessStatus.SUCCEEDED,
            )
        )

    def retry(self, attempt_id: RedeemAttemptId) -> RedeemResult:
        self.calls += 1
        self.gate.wait(timeout=2.0)
        return RedeemResult(
            RedeemAttempt(attempt_id, None, RedeemProcessStatus.ALREADY_REDEEMED)
        )


class FailingManager(DelayedManager):
    def redeem(self, *, credit_id: ResetCreditId | None = None) -> RedeemResult:
        raise RuntimeError("delayed fake failure")


def _settle(controller: RedeemExecutionController, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        controller.poll()
        if not controller.busy:
            return
        time.sleep(0.002)
    raise AssertionError("redeem controller did not settle")


def test_task_750_753_duplicate_redeem_start_is_suppressed_while_running() -> None:
    manager = DelayedManager()
    controller = RedeemExecutionController(manager)
    try:
        assert controller.start_redeem(credit_id=ResetCreditId("credit"))
        assert controller.state.phase is RedeemExecutionPhase.RUNNING
        assert not controller.start_redeem(credit_id=ResetCreditId("other"))
        manager.gate.set()
        _settle(controller)
        assert controller.state.phase is RedeemExecutionPhase.RESULT
        assert manager.calls == 1
    finally:
        controller.close()


def test_task_751_error_is_ui_execution_state_not_durable_semantic_rewrite() -> None:
    controller = RedeemExecutionController(FailingManager())
    try:
        assert controller.start_redeem()
        _settle(controller)
        assert controller.state.phase is RedeemExecutionPhase.ERROR
        assert controller.state.error == "delayed fake failure"
    finally:
        controller.close()


def test_task_754_close_suppresses_late_redeem_result() -> None:
    manager = DelayedManager()
    controller = RedeemExecutionController(manager)
    assert controller.start_redeem()
    controller.close()
    manager.gate.set()
    time.sleep(0.01)
    assert controller.state.phase is RedeemExecutionPhase.RUNNING
