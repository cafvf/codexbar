import pytest

from codexbar.application.account import ResetConsumeCommand, ResetConsumeOutcome
from codexbar.application.reset_events import RedeemAttemptId
from codexbar.domain.errors import UsageSchemaError
from codexbar.domain.reset import ResetCreditId
from codexbar.infrastructure.reset_consumer import CodexResetCreditConsumer


class Gateway:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def call(self, method, *, request_id=1, params=None):
        self.calls.append((method, params))
        return self.response


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("reset", ResetConsumeOutcome.RESET),
        ("alreadyRedeemed", ResetConsumeOutcome.ALREADY_REDEEMED),
        ("nothingToReset", ResetConsumeOutcome.NOTHING_TO_RESET),
        ("noCredit", ResetConsumeOutcome.NO_CREDIT),
    ],
)
def test_consumer_maps_all_documented_outcomes(raw, expected) -> None:
    gateway = Gateway({"id": 1, "result": {"outcome": raw}})
    consumer = CodexResetCreditConsumer(gateway)

    outcome = consumer.consume_reset_credit(
        ResetConsumeCommand(
            RedeemAttemptId("attempt-1"),
            ResetCreditId("credit-1"),
        )
    )

    assert outcome is expected
    assert gateway.calls == [
        (
            "account/rateLimitResetCredit/consume",
            {"idempotencyKey": "attempt-1", "creditId": "credit-1"},
        )
    ]


def test_consumer_omits_optional_credit_id() -> None:
    gateway = Gateway({"result": {"outcome": "reset"}})

    CodexResetCreditConsumer(gateway).consume_reset_credit(
        ResetConsumeCommand(RedeemAttemptId("attempt-1"))
    )

    assert gateway.calls[0][1] == {"idempotencyKey": "attempt-1"}


def test_consumer_rejects_future_unknown_outcome() -> None:
    gateway = Gateway({"result": {"outcome": "future"}})

    with pytest.raises(UsageSchemaError):
        CodexResetCreditConsumer(gateway).consume_reset_credit(
            ResetConsumeCommand(RedeemAttemptId("attempt-1"))
        )
