from __future__ import annotations

import json
import os
import selectors
import shutil
import subprocess
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Protocol, TextIO, cast

from codexbar import __version__
from codexbar.domain.errors import (
    UsageAuthenticationError,
    UsageCommandError,
    UsageSchemaError,
    UsageSourceUnavailableError,
    UsageTimeoutError,
)
from codexbar.domain.models import Fraction, UsageSnapshot, UsageSource, UsageWindow, UsageWindowId

JsonObject = dict[str, Any]


def _is_executable_file(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _nvm_version_key(path: Path) -> tuple[int, ...]:
    raw = path.parent.parent.name.removeprefix("v")
    try:
        return tuple(int(part) for part in raw.split("."))
    except ValueError:
        return (-1,)


def resolve_codex_executable(
    *,
    env: Mapping[str, str] | None = None,
) -> str:
    """Resolve Codex without depending on interactive-shell initialization."""

    values = os.environ if env is None else env

    found = shutil.which("codex", path=values.get("PATH", ""))
    if found is not None:
        return found

    home = Path(values.get("HOME", str(Path.home()))).expanduser()

    local_candidate = home / ".local/bin/codex"
    if _is_executable_file(local_candidate):
        return str(local_candidate)

    nvm_root = Path(values.get("NVM_DIR", str(home / ".nvm"))).expanduser()
    nvm_candidates = [
        candidate
        for candidate in (nvm_root / "versions/node").glob("*/bin/codex")
        if _is_executable_file(candidate)
    ]
    if nvm_candidates:
        selected = max(
            nvm_candidates,
            key=lambda candidate: (_nvm_version_key(candidate), str(candidate)),
        )
        return str(selected)

    npm_global_candidate = home / ".npm-global/bin/codex"
    if _is_executable_file(npm_global_candidate):
        return str(npm_global_candidate)

    return "codex"


class JsonRpcTransport(Protocol):
    def send(self, message: JsonObject) -> None: ...

    def receive(self, timeout_seconds: float) -> JsonObject: ...

    def close(self) -> None: ...


class SubprocessJsonRpcTransport:
    """JSONL transport for the stable `codex app-server --stdio` interface."""

    def __init__(self, executable: str = "codex") -> None:
        resolved_executable = (
            resolve_codex_executable() if executable == "codex" else executable
        )
        process_env = dict(os.environ)
        resolved_path = Path(resolved_executable)
        if resolved_path.is_absolute():
            executable_dir = str(resolved_path.parent)
            current_path = process_env.get("PATH", "")
            path_parts = current_path.split(os.pathsep) if current_path else []
            if executable_dir not in path_parts:
                process_env["PATH"] = os.pathsep.join(
                    [executable_dir, *path_parts]
                )

        try:
            self._process = subprocess.Popen(
                [resolved_executable, "app-server", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                bufsize=1,
                env=process_env,
            )
        except FileNotFoundError as exc:
            raise UsageSourceUnavailableError(
                f"Codex executable not found: {resolved_executable}"
            ) from exc
        except OSError as exc:
            raise UsageSourceUnavailableError(f"Could not start Codex app-server: {exc}") from exc

        if self._process.stdin is None or self._process.stdout is None:
            self.close()
            raise UsageSourceUnavailableError("Codex app-server stdio pipes are unavailable")

        self._stdin = cast(TextIO, self._process.stdin)
        self._stdout = cast(TextIO, self._process.stdout)
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._stdout, selectors.EVENT_READ)

    def send(self, message: JsonObject) -> None:
        if self._process.poll() is not None:
            raise UsageCommandError(self._process_error("Codex app-server exited unexpectedly"))
        try:
            self._stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
            self._stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise UsageCommandError("Could not write to Codex app-server") from exc

    def receive(self, timeout_seconds: float) -> JsonObject:
        if timeout_seconds <= 0:
            raise UsageTimeoutError("Timed out waiting for Codex app-server")

        events = self._selector.select(timeout_seconds)
        if not events:
            if self._process.poll() is not None:
                raise UsageCommandError(self._process_error("Codex app-server exited"))
            raise UsageTimeoutError("Timed out waiting for Codex app-server")

        line = self._stdout.readline()
        if not line:
            raise UsageCommandError(self._process_error("Codex app-server closed stdout"))

        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise UsageSchemaError("Codex app-server emitted invalid JSON") from exc
        if not isinstance(value, dict):
            raise UsageSchemaError("Codex app-server message must be a JSON object")
        return cast(JsonObject, value)

    def close(self) -> None:
        selector = getattr(self, "_selector", None)
        if selector is not None:
            selector.close()
        process = getattr(self, "_process", None)
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)

    def _process_error(self, prefix: str) -> str:
        stderr = self._process.stderr
        detail = (
            stderr.read().strip()
            if stderr is not None and self._process.poll() is not None
            else ""
        )
        return f"{prefix}: {detail}" if detail else prefix


class CodexAppServerGateway:
    """Reusable initialized JSON-RPC boundary for one Codex app-server operation."""

    def __init__(
        self,
        transport_factory: Callable[[], JsonRpcTransport] | None = None,
        *,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._transport_factory = transport_factory or SubprocessJsonRpcTransport
        self._timeout_seconds = timeout_seconds

    def call(
        self,
        method: str,
        *,
        request_id: int = 1,
        params: JsonObject | None = None,
    ) -> JsonObject:
        """Open, initialize, execute one request, and always close the transport."""
        transport = self._transport_factory()
        try:
            self._initialize(transport)
            return self._request(
                transport,
                request_id=request_id,
                method=method,
                params=params,
            )
        finally:
            transport.close()

    def _initialize(self, transport: JsonRpcTransport) -> None:
        transport.send(
            {
                "method": "initialize",
                "id": 0,
                "params": {
                    "clientInfo": {
                        "name": "codexbar",
                        "title": "CodexBar",
                        "version": __version__,
                    }
                },
            }
        )
        self._wait_for_id(transport, 0)
        transport.send({"method": "initialized", "params": {}})

    def _request(
        self,
        transport: JsonRpcTransport,
        *,
        request_id: int,
        method: str,
        params: JsonObject | None,
    ) -> JsonObject:
        message: JsonObject = {"method": method, "id": request_id}
        if params is not None:
            message["params"] = params
        transport.send(message)
        return self._wait_for_id(transport, request_id)

    def _wait_for_id(self, transport: JsonRpcTransport, request_id: int) -> JsonObject:
        deadline = time.monotonic() + self._timeout_seconds
        while True:
            message = transport.receive(deadline - time.monotonic())
            if message.get("id") != request_id:
                continue
            error = message.get("error")
            if error is not None:
                self._raise_rpc_error(error)
            return message

    @staticmethod
    def _raise_rpc_error(error: object) -> None:
        message = str(error)
        if isinstance(error, dict):
            message = str(error.get("message", error))
        lowered = message.lower()
        if any(term in lowered for term in ("auth", "login", "credential", "unauthorized")):
            raise UsageAuthenticationError(message)
        raise UsageCommandError(message)


class CodexAppServerProvider:
    """UsageProvider backed by Codex's stable local app-server account API."""

    def __init__(
        self,
        transport_factory: Callable[[], JsonRpcTransport] | None = None,
        *,
        timeout_seconds: float = 5.0,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._gateway = CodexAppServerGateway(
            transport_factory,
            timeout_seconds=timeout_seconds,
        )
        self._clock = clock or (lambda: datetime.now(UTC))

    def get_usage(self) -> UsageSnapshot:
        response = self._gateway.call("account/rateLimits/read")
        observed_at = self._clock()
        if observed_at.tzinfo is None or observed_at.utcoffset() is None:
            raise ValueError("provider clock must return a timezone-aware datetime")
        return parse_rate_limits_response(response, observed_at=observed_at)


def parse_rate_limits_response(message: JsonObject, *, observed_at: datetime) -> UsageSnapshot:
    """Map one supported account/rateLimits/read shape into the canonical model.

    v1.7 source selection is explicit: a structurally usable
    ``rateLimitsByLimitId.codex`` snapshot is preferred; otherwise the supported
    legacy ``rateLimits`` snapshot remains the compatibility fallback. Other
    multi-bucket limit IDs are never merged into Current.
    """
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        raise ValueError("observed_at must be timezone-aware")

    result = _mapping(message.get("result"), "result")
    explicit_codex = _explicit_codex_rate_limits(result)
    legacy_raw = result.get("rateLimits")

    if explicit_codex is not None:
        try:
            return _parse_rate_limit_snapshot(explicit_codex, observed_at=observed_at)
        except UsageSchemaError:
            if legacy_raw is None:
                raise

    if legacy_raw is None:
        raise UsageSchemaError("result.rateLimits is missing")
    legacy = _mapping(legacy_raw, "result.rateLimits")
    return _parse_rate_limit_snapshot(legacy, observed_at=observed_at)


def _explicit_codex_rate_limits(result: JsonObject) -> JsonObject | None:
    buckets_raw = result.get("rateLimitsByLimitId")
    if not isinstance(buckets_raw, dict):
        return None
    buckets = cast(JsonObject, buckets_raw)
    codex_raw = buckets.get("codex")
    if not isinstance(codex_raw, dict):
        return None
    codex = cast(JsonObject, codex_raw)
    if not any(key in codex for key in ("primary", "secondary", "rateLimitReachedType")):
        return None
    return codex


def _parse_rate_limit_snapshot(
    rate_limits: JsonObject,
    *,
    observed_at: datetime,
) -> UsageSnapshot:
    windows: list[UsageWindow] = []
    for slot in ("primary", "secondary"):
        raw = rate_limits.get(slot)
        if raw is None:
            continue
        windows.append(_parse_window(_mapping(raw, f"rateLimits.{slot}")))

    window_ids = [window.id.value for window in windows]
    if len(window_ids) != len(set(window_ids)):
        raise UsageSchemaError(
            "rate limit windows must have unique identities derived from windowDurationMins"
        )

    reached_type_raw = rate_limits.get("rateLimitReachedType")
    reached_type = None if reached_type_raw is None else str(reached_type_raw)
    return UsageSnapshot(
        windows=tuple(windows),
        observed_at=observed_at,
        source=UsageSource.CODEX_APP_SERVER,
        rate_limit_reached_type=reached_type,
    )


def _parse_window(raw: JsonObject) -> UsageWindow:
    used = _decimal(raw.get("usedPercent"), "usedPercent")
    if not Decimal("0") <= used <= Decimal("100"):
        raise UsageSchemaError("usedPercent must be between 0 and 100")

    duration = raw.get("windowDurationMins")
    if isinstance(duration, bool) or not isinstance(duration, int) or duration <= 0:
        raise UsageSchemaError("windowDurationMins must be a positive integer")

    reset_raw = raw.get("resetsAt")
    resets_at: datetime | None
    if reset_raw is None:
        resets_at = None
    elif isinstance(reset_raw, bool) or not isinstance(reset_raw, (int, float)):
        raise UsageSchemaError("resetsAt must be a Unix timestamp or null")
    else:
        try:
            resets_at = datetime.fromtimestamp(reset_raw, tz=UTC)
        except (OverflowError, OSError, ValueError) as exc:
            raise UsageSchemaError("resetsAt is outside the supported datetime range") from exc

    remaining_percent = Decimal("100") - used
    return UsageWindow(
        id=UsageWindowId(f"window_{duration}m"),
        label=_window_label(duration),
        remaining=Fraction.from_percent(remaining_percent),
        resets_at=resets_at,
    )


def _window_label(duration_minutes: int) -> str:
    if duration_minutes == 300:
        return "5 hours"
    if duration_minutes == 10_080:
        return "Weekly"
    if duration_minutes % (24 * 60) == 0:
        days = duration_minutes // (24 * 60)
        return f"{days} days"
    if duration_minutes % 60 == 0:
        hours = duration_minutes // 60
        return f"{hours} hours"
    return f"{duration_minutes} min"


def _mapping(value: object, path: str) -> JsonObject:
    if not isinstance(value, dict):
        raise UsageSchemaError(f"{path} must be an object")
    return cast(JsonObject, value)


def _decimal(value: object, field: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise UsageSchemaError(f"{field} must be numeric")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise UsageSchemaError(f"{field} must be numeric") from exc
    if not number.is_finite():
        raise UsageSchemaError(f"{field} must be finite")
    return number
