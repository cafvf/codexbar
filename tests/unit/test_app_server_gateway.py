from typing import Any

import pytest

from codexbar.domain.errors import (
    UsageAuthenticationError,
    UsageCommandError,
    UsageTimeoutError,
)
from codexbar.infrastructure.app_server import CodexAppServerGateway


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


def test_gateway_performs_handshake_and_arbitrary_request() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {"userAgent": "test"}},
            {"method": "account/updated", "params": {}},
            {"id": 7, "result": {"ok": True}},
        ]
    )
    gateway = CodexAppServerGateway(lambda: transport)

    response = gateway.call(
        "account/example",
        request_id=7,
        params={"value": "opaque"},
    )

    assert response == {"id": 7, "result": {"ok": True}}
    assert [message["method"] for message in transport.sent] == [
        "initialize",
        "initialized",
        "account/example",
    ]
    assert transport.sent[2] == {
        "method": "account/example",
        "id": 7,
        "params": {"value": "opaque"},
    }
    assert transport.closed is True


def test_gateway_omits_params_when_request_has_none() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {}},
            {"id": 1, "result": {"ok": True}},
        ]
    )

    CodexAppServerGateway(lambda: transport).call("account/rateLimits/read")

    assert transport.sent[2] == {
        "method": "account/rateLimits/read",
        "id": 1,
    }


def test_gateway_normalizes_authentication_errors_and_closes() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {}},
            {"id": 1, "error": {"code": -32000, "message": "Login required"}},
        ]
    )

    with pytest.raises(UsageAuthenticationError, match="Login required"):
        CodexAppServerGateway(lambda: transport).call("account/rateLimits/read")

    assert transport.closed is True


def test_gateway_preserves_non_auth_rpc_error_taxonomy() -> None:
    transport = FakeTransport(
        [
            {"id": 0, "result": {}},
            {"id": 1, "error": {"code": -32000, "message": "backend unavailable"}},
        ]
    )

    with pytest.raises(UsageCommandError, match="backend unavailable"):
        CodexAppServerGateway(lambda: transport).call("account/rateLimits/read")

    assert transport.closed is True


def test_gateway_closes_after_receive_failure() -> None:
    transport = FakeTransport([{"id": 0, "result": {}}])

    with pytest.raises(UsageTimeoutError):
        CodexAppServerGateway(lambda: transport).call("account/rateLimits/read")

    assert transport.closed is True
