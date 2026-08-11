from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from codexbar.application.account import AccountRateLimitsReader, ResetCreditConsumer
from codexbar.application.account_operations import (
    AccountOperationCoordinator,
    CoordinatedAccountRateLimitsReader,
)
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.account_runtime import CapturingAccountRateLimitsReader
from codexbar.application.analytics import HistoricalAnalysisService
from codexbar.application.context import (
    FailedContextHistoryRepository,
    HistoricalContextService,
)
from codexbar.application.history import HistoryError
from codexbar.application.history_runtime import HistoryService
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager
from codexbar.application.reset_ledger import (
    ResetEventRepository,
    ResetLedgerError,
    ResetLedgerReadError,
)
from codexbar.application.reset_ledger_service import ResetLedgerService
from codexbar.application.reset_projection import ResetLedgerProjection
from codexbar.application.settings import GetSettings, SettingsRepository
from codexbar.application.usage_adapter import AccountUsageProvider
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import (
    SqliteHistoryRepository,
    open_history_analytics_repository,
)
from codexbar.infrastructure.mock_context import MockContextHistoryRepository
from codexbar.infrastructure.mock_control import (
    MockAccountRateLimitsReader,
    MockResetCreditConsumer,
)
from codexbar.infrastructure.mock_provider import MockUsageProvider
from codexbar.infrastructure.notifications import NotifySendNotificationAdapter
from codexbar.infrastructure.reset_consumer import CodexResetCreditConsumer
from codexbar.infrastructure.reset_event_paths import reset_ledger_database_path
from codexbar.infrastructure.reset_event_sqlite import SqliteResetEventRepository
from codexbar.infrastructure.settings import JsonSettingsRepository
from codexbar.ui.context_viewmodel import ContextPresenter
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter
from codexbar.ui.history_controller import HistoryController


@dataclass(frozen=True, slots=True)
class HistoryRuntime:
    service: HistoryService | None
    controller: HistoryController
    context_service: HistoricalContextService


@dataclass(frozen=True, slots=True)
class ResetRuntime:
    repository: ResetEventRepository | None
    service: ResetLedgerService | None


@dataclass(slots=True)
class GuiRuntime:
    provider: UsageProvider
    settings_repository: SettingsRepository
    notifier: NotificationPort
    history_controller: HistoryController
    context_service: HistoricalContextService
    context_presenter: ContextPresenter
    operation_coordinator: AccountOperationCoordinator
    presenter: CurrentAccountPresenter
    reset_ledger_service: ResetLedgerService | None = None
    redeem_manager: RedeemProcessManager | None = None

    def close(self) -> None:
        self.history_controller.close()
        self.operation_coordinator.close()


def build_usage_provider(*, mock: bool = False) -> UsageProvider:
    if mock:
        return MockUsageProvider()
    return AccountUsageProvider(CodexAccountRateLimitsReader())


def _build_history_runtime(*, mock: bool) -> HistoryRuntime:
    path = history_database_path()
    try:
        repository = SqliteHistoryRepository(path)
    except HistoryError as exc:
        service = None
        context_service = HistoricalContextService(
            MockContextHistoryRepository()
            if mock
            else FailedContextHistoryRepository(exc)
        )
    else:
        service = HistoryService(repository)
        context_service = HistoricalContextService(
            MockContextHistoryRepository()
            if mock
            else SqliteContextHistoryRepository(repository)
        )

    controller = HistoryController(
        HistoricalAnalysisService(open_history_analytics_repository(path))
    )
    return HistoryRuntime(
        service=service,
        controller=controller,
        context_service=context_service,
    )


def _build_reset_runtime() -> ResetRuntime:
    path = reset_ledger_database_path()
    try:
        repository = SqliteResetEventRepository(path)
    except ResetLedgerError:
        return ResetRuntime(repository=None, service=None)
    return ResetRuntime(
        repository=repository,
        service=ResetLedgerService(repository),
    )


def _unavailable_reset_projection() -> ResetLedgerProjection:
    raise ResetLedgerReadError("reset ledger is unavailable")


def _projection_provider(
    service: ResetLedgerService | None,
) -> Callable[[], ResetLedgerProjection]:
    return service.projection if service is not None else _unavailable_reset_projection


def _account_adapters(
    *,
    mock: bool,
) -> tuple[AccountRateLimitsReader, ResetCreditConsumer]:
    if mock:
        return MockAccountRateLimitsReader(), MockResetCreditConsumer()
    return CodexAccountRateLimitsReader(), CodexResetCreditConsumer()


def build_gui_runtime(*, mock: bool = False) -> GuiRuntime:
    history = _build_history_runtime(mock=mock)
    reset = _build_reset_runtime()
    settings_repository = JsonSettingsRepository()
    settings = GetSettings(settings_repository).execute().settings
    notifier = NotifySendNotificationAdapter()
    coordinator = AccountOperationCoordinator()
    reader, consumer = _account_adapters(mock=mock)

    capturing_reader = CapturingAccountRateLimitsReader(
        reader,
        history.service,
        reset.service,
    )
    latest_reader = LatestAccountObservationReader(capturing_reader)
    coordinated_reader = CoordinatedAccountRateLimitsReader(latest_reader, coordinator)

    redeem_manager = (
        RedeemProcessManager(
            reset.repository,
            consumer,
            latest_reader,
            coordinator,
        )
        if reset.repository is not None
        else None
    )
    presenter = CurrentAccountPresenter(
        latest_reader,
        settings,
        _projection_provider(reset.service),
        redeem_manager=redeem_manager,
    )
    context_presenter = ContextPresenter(latest_reader, history.context_service)

    return GuiRuntime(
        provider=AccountUsageProvider(coordinated_reader),
        settings_repository=settings_repository,
        notifier=notifier,
        history_controller=history.controller,
        context_service=history.context_service,
        context_presenter=context_presenter,
        operation_coordinator=coordinator,
        reset_ledger_service=reset.service,
        presenter=presenter,
        redeem_manager=redeem_manager,
    )
