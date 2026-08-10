from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codexbar.application.redeem import RedeemProcessManager
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.models import UsageWindowId
from codexbar.domain.reset import ResetCreditId
from codexbar.ui.context_panel import HistoricalContextPanel
from codexbar.ui.context_viewmodel import ContextPresenter
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

        labels = {
            window.window_id: window.label
            for window in state.usage.windows
        }
        lines: list[str] = []
        for budget in state.budget.windows:
            label = labels.get(budget.window_id, budget.window_id.value)
            reserve = (
                "Not set"
                if budget.reserve is None
                else f"{_percent(budget.reserve.value)}%"
            )
            status = _budget_status_text(budget.status.value)
            lines.extend(
                (
                    label,
                    f"  Remaining: {_percent(budget.remaining.value)}%",
                    f"  Reserved: {reserve}",
                    f"  Available to use: {_percent(budget.headroom.value)}%",
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
        manager: RedeemProcessManager | None,
        *,
        on_changed: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._manager = manager
        self._on_changed = on_changed
        self._state: CurrentAccountViewState | None = None
        self._active = False

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

    def render_account_state(self, state: CurrentAccountViewState | None) -> None:
        self._state = state
        manager = self._manager
        if state is None or not state.redeem.available or manager is None:
            self._status.setText("Redeem unavailable.")
            self._redeem.setEnabled(False)
            self._retry.setEnabled(False)
            return

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

        self._redeem.setEnabled(
            not self._active
            and not unresolved
            and has_available_credit
        )
        self._retry.setEnabled(not self._active and bool(unresolved))

    def _confirm_redeem(self) -> None:
        manager = self._manager
        if manager is None or self._active:
            return

        state = self._state
        if state is None:
            return

        credit_id: ResetCreditId | None = None
        text = "Redeem one reset credit?"
        if state.reset.credits:
            credit = state.reset.credits[0]
            credit_id = ResetCreditId(credit.credit_id)
            text = (
                f"Redeem reset credit “{credit.title}” "
                f"({credit.expiry_text})?"
            )
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
        self._run(lambda: manager.redeem(credit_id=credit_id))

    def _confirm_retry(self) -> None:
        manager = self._manager
        state = self._state
        if manager is None or self._active or state is None:
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
        self._run(lambda: manager.retry(attempt_id))

    def _run(self, action: Callable[[], object]) -> None:
        self._active = True
        self._redeem.setEnabled(False)
        self._retry.setEnabled(False)
        try:
            result = action()
            attempt = getattr(result, "attempt", None)
            status = getattr(attempt, "status", None)
            self._status.setText(
                f"Redeem result: "
                f"{status.value if status is not None else 'completed'}"
            )
        except Exception as exc:
            self._status.setText(f"Redeem failed: {exc}")
        finally:
            self._active = False
            if self._on_changed is not None:
                self._on_changed()


class CurrentAccountPanel(RichUsagePanel):
    def __init__(
        self,
        presenter: CurrentAccountPresenter,
        redeem_manager: RedeemProcessManager | None,
        *,
        context_presenter: ContextPresenter | None = None,
        on_history: Callable[[UsageWindowId], None] | None = None,
        on_redeem_changed: Callable[[], None] | None = None,
    ) -> None:
        super().__init__(on_history=on_history)
        self._presenter = presenter
        selected_context_presenter = context_presenter or getattr(
            presenter, "context_presenter", None
        )
        self.context_panel = (
            HistoricalContextPanel(selected_context_presenter, self)
            if selected_context_presenter is not None
            else None
        )
        self.reset_panel = ResetCreditsPanel(self)
        self.budget_panel = BudgetPanel(self)
        self.redeem_panel = RedeemPanel(
            redeem_manager,
            on_changed=on_redeem_changed,
            parent=self,
        )
        insert_at = max(0, self._layout.count() - 1)
        if self.context_panel is not None:
            self._layout.insertWidget(insert_at, self.context_panel)
            insert_at += 1
        self._layout.insertWidget(insert_at, self.reset_panel)
        self._layout.insertWidget(insert_at + 1, self.budget_panel)
        self._layout.insertWidget(insert_at + 2, self.redeem_panel)

    def render_state(self, state: TrayViewState) -> None:
        super().render_state(state)
        account = self._presenter.current()
        if self.context_panel is not None:
            self.context_panel.refresh()
        self.reset_panel.render_account_state(account)
        self.budget_panel.render_account_state(account)
        self.redeem_panel.render_account_state(account)

    def current_usage_windows(
        self,
    ) -> tuple[tuple[UsageWindowId, str], ...]:
        account = self._presenter.current()
        if account is None:
            return ()
        return tuple(
            (window.window_id, window.label)
            for window in account.usage.windows
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
