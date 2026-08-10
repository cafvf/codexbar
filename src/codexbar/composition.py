from __future__ import annotations

from dataclasses import dataclass

from codexbar.application.account import AccountRateLimitsReader, ResetCreditConsumer
from codexbar.application.account_operations import (
    AccountOperationCoordinator,
    CoordinatedAccountRateLimitsReader,
)
from codexbar.application.account_presentation import LatestAccountObservationReader
from codexbar.application.account_runtime import CapturingAccountRateLimitsReader
from codexbar.application.analytics import HistoricalAnalysisService
from codexbar.application.context import HistoricalContextService
from codexbar.application.current_account import CurrentAccountController
from codexbar.application.history_runtime import HistoryService
from codexbar.application.ports import NotificationPort, UsageProvider
from codexbar.application.redeem import RedeemProcessManager
from codexbar.application.reset_ledger_service import ResetLedgerService
from codexbar.application.settings import GetSettings, SettingsRepository
from codexbar.application.usage_adapter import AccountUsageProvider
from codexbar.infrastructure.account_reader import CodexAccountRateLimitsReader
from codexbar.infrastructure.context_history import SqliteContextHistoryRepository
from codexbar.infrastructure.history_paths import history_database_path
from codexbar.infrastructure.history_sqlite import (
    SqliteHistoryRepository,
    open_history_analytics_repository,
)
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
from codexbar.ui.current_account_viewmodel import CurrentAccountPresenter
from codexbar.ui.history_controller import HistoryController


@dataclass(slots=True)
class GuiRuntime:
    provider: UsageProvider
    settings_repository: SettingsRepository
    notifier: NotificationPort
    history_controller: HistoryController
    context_service: HistoricalContextService
    account_controller: CurrentAccountController | None = None
    operation_coordinator: AccountOperationCoordinator | None = None
    reset_ledger_service: ResetLedgerService | None = None
    presenter: CurrentAccountPresenter | None = None
    redeem_manager: RedeemProcessManager | None = None

    def close(self) -> None:
        self.history_controller.close()
        if self.operation_coordinator is not None:
            self.operation_coordinator.close()


def build_usage_provider(*, mock: bool = False) -> UsageProvider:
    if mock:
        return MockUsageProvider()
    return AccountUsageProvider(CodexAccountRateLimitsReader())


def build_gui_runtime(*, mock: bool = False) -> GuiRuntime:
    history_path = history_database_path()
    history_repository = SqliteHistoryRepository(history_path)
    history_service = HistoryService(history_repository)
    history_controller = HistoryController(
        HistoricalAnalysisService(open_history_analytics_repository(history_path))
    )
    context_service = HistoricalContextService(
        SqliteContextHistoryRepository(history_repository)
    )
    settings_repository = JsonSettingsRepository()
    settings = GetSettings(settings_repository).execute().settings
    notifier = NotifySendNotificationAdapter()

    reset_repository = SqliteResetEventRepository(reset_ledger_database_path())
    reset_ledger_service = ResetLedgerService(reset_repository)
    coordinator = AccountOperationCoordinator()

    if mock:
        reader: AccountRateLimitsReader = MockAccountRateLimitsReader()
        consumer: ResetCreditConsumer = MockResetCreditConsumer()
    else:
        reader = CodexAccountRateLimitsReader()
        consumer = CodexResetCreditConsumer()

    reader = CapturingAccountRateLimitsReader(
        reader,
        history_service,
        reset_ledger_service,
    )
    latest_reader = LatestAccountObservationReader(reader)
    coordinated_reader = CoordinatedAccountRateLimitsReader(latest_reader, coordinator)
    redeem_manager = RedeemProcessManager(
        reset_repository,
        consumer,
        latest_reader,
        coordinator,
    )
    presenter = CurrentAccountPresenter(
        latest_reader,
        settings,
        reset_ledger_service.projection,
        redeem_manager=redeem_manager,
    )

    return GuiRuntime(
        provider=AccountUsageProvider(coordinated_reader),
        settings_repository=settings_repository,
        notifier=notifier,
        history_controller=history_controller,
        context_service=context_service,
        account_controller=CurrentAccountController(coordinated_reader),
        operation_coordinator=coordinator,
        reset_ledger_service=reset_ledger_service,
        presenter=presenter,
        redeem_manager=redeem_manager,
    )
