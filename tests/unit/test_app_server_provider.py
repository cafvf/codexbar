from datetime import UTC, datetime
from typing import Any

import pytest

from codexbar.domain.errors import UsageAuthenticationError, UsageTimeoutError
from codexbar.infrastructure.app_server import CodexAppServerProvider


class FakeTransport:
    def __init__(self, incoming: list[dict[str, Any]]) -> None:
        self.incoming = list(incoming)
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    def send(self, message: dict[str, Any]) -> None:
        self.sent.append(message)

    def receive(self, timeout_seconds: float) -> dict[str, Any]:
        if not self.incoming:
            raise UsageTimeoutError("timeout")
        return self.incoming.pop(0)

    def close(self) -> None:
        self.closed = True


def test_provider_performs_required_handshake_and_rate_limit_read() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {"userAgent": "test"}},
            {"method": "account/updated", "params": {}},
            {
                "id": 1,
                "result": {
                    "rateLimits": {
                        "primary": {"usedPercent": 10, "windowDurationMins": 300},
                        "secondary": None,
                        "rateLimitReachedType": None,
                    }
                },
            },
        ]
    )
    now = datetime(2026, 8, 8, tzinfo=UTC)
    provider = CodexAppServerProvider(lambda: transport, clock=lambda: now)

    snapshot = provider.get_usage()

    assert [message["method"] for message in transport.sent] == [
        "initialize",
        "initialized",
        "account/rateLimits/read",
    ]
    assert snapshot.windows[0].remaining.percent == 90
    assert transport.closed is True


def test_rpc_auth_error_is_normalized() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {}},
            {"id": 1, "error": {"code": -32000, "message": "Login required"}},
        ]
    )
    provider = CodexAppServerProvider(lambda: transport)
    with pytest.raises(UsageAuthenticationError):
        provider.get_usage()
    assert transport.closed is True
