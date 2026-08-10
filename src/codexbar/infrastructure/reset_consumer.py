from __future__ import annotations

from codexbar.application.account import (
    ResetConsumeCommand,
    ResetConsumeOutcome,
    ResetCreditConsumer,
)
from codexbar.domain.errors import UsageSchemaError
from codexbar.infrastructure.app_server import CodexAppServerGateway


class CodexResetCreditConsumer(ResetCreditConsumer):
    """Typed adapter for account/rateLimitResetCredit/consume."""

    def __init__(self, gateway: CodexAppServerGateway | None = None) -> None:
        self._gateway = gateway or CodexAppServerGateway()

    def consume_reset_credit(self, command: ResetConsumeCommand) -> ResetConsumeOutcome:
        params: dict[str, object] = {
            "idempotencyKey": command.attempt_id.value,
        }
        if command.credit_id is not None:
            params["creditId"] = command.credit_id.value

        response = self._gateway.call(
            "account/rateLimitResetCredit/consume",
            params=params,
        )
        result = response.get("result")
        if not isinstance(result, dict):
            raise UsageSchemaError("reset consume result must be an object")
        outcome = result.get("outcome")
        if not isinstance(outcome, str):
            raise UsageSchemaError("reset consume outcome must be a string")
        try:
            return ResetConsumeOutcome(outcome)
        except ValueError as exc:
            raise UsageSchemaError(
                f"unsupported reset consume outcome: {outcome!r}"
            ) from exc
