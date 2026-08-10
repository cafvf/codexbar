from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from codexbar.application.account import AccountRateLimitsObservation
from codexbar.infrastructure.account_rate_limits import parse_account_rate_limits_response
from codexbar.infrastructure.app_server import CodexAppServerGateway


class CodexAccountRateLimitsReader:
    """Composed account reader backed by one Codex app-server request."""

    def __init__(
        self,
        gateway: CodexAppServerGateway | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._gateway = gateway or CodexAppServerGateway()
        self._clock = clock or (lambda: datetime.now(UTC))

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        response = self._gateway.call("account/rateLimits/read")
        observed_at = self._clock()
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("account reader clock must return a timezone-aware datetime")
        return parse_account_rate_limits_response(response, observed_at=observed_at)
