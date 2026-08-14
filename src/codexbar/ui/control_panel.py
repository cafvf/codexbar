from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codexbar.application.redeem import RedeemProcessManager, RedeemResult
from codexbar.application.redeem_execution import (
    RedeemExecutionController,
    RedeemExecutionPhase,
)
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.models import UsageWindowId
from codexbar.domain.reset import ResetCreditId
from codexbar.ui.controller import TrayViewState
from codexbar.ui.current_account_viewmodel import (
    CurrentAccountPresenter,
    CurrentAccountViewState,
    ResetCurrentKind,
)
from codexbar.ui.current_panel import RichUsagePanel


class ResetCreditsPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._layout = QVBoxLayout(self)
        self._title = QLabel("Reset credits")
        self._body = QLabel("Data unavailable")
        self._body.setWordWrap(True)
        self._layout.addWidget(self._title)
        self._layout.addWidget(self._body)

    def render_account_state(self, state: CurrentAccountViewState | None) -> None:
        if state is None or state.reset.kind is ResetCurrentKind.UNAVAILABLE:
            self._body.setText("Reset-credit data unavailable.")
            return

        reset = state.reset
        coverage = {
            ResetCurrentKind.COUNT_ONLY: "count only",
            ResetCurrentKind.PARTIAL: "partial details",
            ResetCurrentKind.COMPLETE: "complete details",
        }[reset.kind]
        lines = [f"Available: {reset.available_count} · {coverage}"]
        for credit in reset.credits:
            lines.append(f"{credit.title} · {credit.expiry_text}")
        if reset.kind is ResetCurrentKind.COUNT_ONLY:
            lines.append("Per-credit identity is not available.")
        self._body.setText("\n".join(lines))


class BudgetPanel(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Control / budget"))
        self._body = QLabel("No budget state yet.")
        self._body.setWordWrap(True)
        layout.addWidget(self._body)

    def render_account_state(self, state: CurrentAccountViewState | None) -> None:
        if state is None:
            self._body.setText("No budget state yet.")
            return
        if state.usage.stale:
            self._body.setText(
                "Control / budget unavailable while current usage is stale."
            )
            return

        labels = {window.window_id: window.label for window in state.usage.windows}
        lines: list[str] = []
        for budget in state.budget.windows:
            label = labels.get(budget.window_id, budget.window_id.value)
            status = _budget_status_text(budget.status.value)
            if budget.reserve is None:
                lines.extend(
                    (
                        label,
                        f"  Remaining: {_percent(budget.remaining.value)}%",
                        "  Reserve policy: Not configured",
                        "  Available above reserve: Not applicable",
                        f"  Status: {status}",
                        "  Configure a reserve in Settings to calculate reserve headroom.",
                        "",
                    )
                )
                continue

            headroom = (
                "Not applicable"
                if budget.headroom is None
                else f"{_percent(budget.headroom.value)}%"
            )
            lines.extend(
                (
                    label,
                    f"  Remaining: {_percent(budget.remaining.value)}%",
                    f"  Reserve: {_percent(budget.reserve.value)}%",
                    f"  Available above reserve: {headroom}",
                    f"  Status: {status}",
                    "",
                )
            )
        lines.extend(
            (
                "Reset recommendation",
                f"  {state.budget.advice.priority.value}: "
                f"{state.budget.advice.reason}",
            )
        )
        self._body.setText("\n".join(lines))


class RedeemPanel(QFrame):
    def __init__(
        self,
        manager: RedeemProcessManager | None = None,
        *,
        controller: RedeemExecutionController | None = None,
        on_changed: Callable[[RedeemResult], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._controller = (
            controller
            if controller is not None
            else RedeemExecutionController(manager)
            if manager is not None
            else None
        )
        self._on_changed = on_changed
        self._state: CurrentAccountViewState | None = None
        self._seen_result_generation = 0

        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reset action"))
        self._status = QLabel("Redeem unavailable.")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)
        self._redeem = QPushButton("Redeem reset credit")
        self._retry = QPushButton("Retry unresolved attempt")
        layout.addWidget(self._redeem)
        layout.addWidget(self._retry)
        self._redeem.clicked.connect(self._confirm_redeem)
        self._retry.clicked.connect(self._confirm_retry)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(25)
        self._poll_timer.timeout.connect(self._poll_execution)

    def render_account_state(self, state: CurrentAccountViewState | None) -> None:
        self._state = state
        controller = self._controller
        if state is None or not state.redeem.available or controller is None:
            self._status.setText("Redeem unavailable.")
            self._redeem.setEnabled(False)
            self._retry.setEnabled(False)
            return

        execution = controller.state
        if execution.phase is RedeemExecutionPhase.RUNNING:
            self._status.setText("Redeem operation in progress…")
        elif execution.phase is RedeemExecutionPhase.ERROR:
            self._status.setText(f"Redeem failed: {execution.error or 'unknown error'}")
        elif execution.phase is RedeemExecutionPhase.RESULT and execution.result is not None:
            self._status.setText(
                f"Redeem result: {execution.result.attempt.status.value}"
            )
        else:
            unresolved = state.redeem.unresolved
            has_available_credit = (
                state.reset.available_count is not None
                and state.reset.available_count > 0
            )
            if unresolved:
                self._status.setText(
                    f"Unresolved attempt: {unresolved[0].attempt_id.value} "
                    f"({unresolved[0].status.value})."
                )
            elif has_available_credit:
                self._status.setText("Reset credit available for manual redemption.")
            else:
                self._status.setText("No reset credits available.")

        unresolved = state.redeem.unresolved
        has_available_credit = (
            state.reset.available_count is not None and state.reset.available_count > 0
        )
        self._redeem.setEnabled(
            not controller.busy and not unresolved and has_available_credit
        )
        self._retry.setEnabled(not controller.busy and bool(unresolved))

    def _confirm_redeem(self) -> None:
        controller = self._controller
        state = self._state
        if controller is None or controller.busy or state is None:
            return

        credit_id: ResetCreditId | None = None
        text = "Redeem one reset credit?"
        if state.reset.credits:
            credit = state.reset.credits[0]
            credit_id = ResetCreditId(credit.credit_id)
            text = f"Redeem reset credit “{credit.title}” ({credit.expiry_text})?"
        elif state.reset.available_count:
            text = (
                "Redeem one reset credit? Per-credit details are unavailable; "
                "the backend will choose the credit."
            )

        answer = QMessageBox.question(
            self,
            "Confirm reset redemption",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer is not QMessageBox.StandardButton.Yes:
            return
        if controller.start_redeem(credit_id=credit_id):
            self._poll_timer.start()
            self.render_account_state(state)

    def _confirm_retry(self) -> None:
        controller = self._controller
        state = self._state
        if controller is None or controller.busy or state is None:
            return
        unresolved = state.redeem.unresolved
        if not unresolved:
            return

        attempt_id: RedeemAttemptId = unresolved[0].attempt_id
        answer = QMessageBox.question(
            self,
            "Retry unresolved redemption",
            f"Retry attempt {attempt_id.value} using the same idempotency key?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer is not QMessageBox.StandardButton.Yes:
            return
        if controller.start_retry(attempt_id):
            self._poll_timer.start()
            self.render_account_state(state)

    def _poll_execution(self) -> None:
        controller = self._controller
        if controller is None:
            self._poll_timer.stop()
            return
        execution = controller.poll()
        self.render_account_state(self._state)
        if (
            execution.phase is RedeemExecutionPhase.RESULT
            and execution.result is not None
            and execution.generation > self._seen_result_generation
        ):
            self._seen_result_generation = execution.generation
            if self._on_changed is not None:
                self._on_changed(execution.result)
        if not controller.busy:
            self._poll_timer.stop()


class CurrentAccountPanel(RichUsagePanel):
    def __init__(
        self,
        presenter: CurrentAccountPresenter,
        redeem_manager: RedeemProcessManager | None,
        *,
        redeem_controller: RedeemExecutionController | None = None,
        on_history: Callable[[UsageWindowId], None] | None = None,
        on_redeem_changed: Callable[[RedeemResult], None] | None = None,
    ) -> None:
        super().__init__(on_history=on_history)
        self._presenter = presenter
        self.reset_panel = ResetCreditsPanel(self)
        self.budget_panel = BudgetPanel(self)
        self.redeem_panel = RedeemPanel(
            redeem_manager,
            controller=redeem_controller,
            on_changed=on_redeem_changed,
            parent=self,
        )
        insert_at = max(0, self._layout.count() - 1)
        self._layout.insertWidget(insert_at, self.reset_panel)
        self._layout.insertWidget(insert_at + 1, self.budget_panel)
        self._layout.insertWidget(insert_at + 2, self.redeem_panel)

    def render_state(self, state: TrayViewState) -> None:
        super().render_state(state)
        account = self._presenter.current()
        self.reset_panel.render_account_state(account)
        self.budget_panel.render_account_state(account)
        self.redeem_panel.render_account_state(account)

    def current_usage_windows(self) -> tuple[tuple[UsageWindowId, str], ...]:
        account = self._presenter.current()
        if account is None:
            return ()
        return tuple(
            (window.window_id, window.label) for window in account.usage.windows
        )


def _budget_status_text(value: str) -> str:
    return {
        "no_policy": "No reserve policy",
        "above_reserve": "Within budget",
        "at_reserve": "At reserve",
        "below_reserve": "Below reserve",
    }.get(value, value.replace("_", " ").title())


def _percent(value: Decimal) -> str:
    return format((value * Decimal("100")).normalize(), "f")
