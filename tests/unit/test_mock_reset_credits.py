from codexbar.application.account import ResetConsumeCommand, ResetConsumeOutcome
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.infrastructure.mock_control import (
    MockAccountRateLimitsReader,
    MockResetCreditConsumer,
)


def test_mock_path_has_deterministic_reset_inventory_and_safe_consume() -> None:
    observation = MockAccountRateLimitsReader().read_account_rate_limits()
    consumer = MockResetCreditConsumer()

    assert observation.reset_credits.inventory is not None
    assert observation.reset_credits.inventory.available_count == 2
    assert consumer.consume_reset_credit(
        ResetConsumeCommand(RedeemAttemptId("mock-attempt"))
    ) is ResetConsumeOutcome.RESET
