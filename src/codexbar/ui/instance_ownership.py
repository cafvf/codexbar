from __future__ import annotations

import fcntl
import hashlib
import os
import sys
import tempfile
import time
import traceback
from collections.abc import Callable, Mapping
from contextlib import suppress
from pathlib import Path
from typing import cast

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from codexbar.application.instance_ownership import (
    InstanceCommand,
    InstanceOwnershipDiagnosticState,
    InstanceOwnershipError,
    InstanceOwnershipState,
    InstanceReply,
    InstanceResolution,
    encode_instance_command,
    encode_instance_reply,
    parse_instance_command,
    parse_instance_reply,
)

_FAST_COMMAND_TIMEOUT_MS = 90
_BUSY_OWNER_WAIT_MS = 2_000
_BUSY_OWNER_RETRY_MS = 25
_APPLICATION: QApplication | None = None


def instance_endpoint_name(
    environment: Mapping[str, str] | None = None,
    *,
    uid: int | None = None,
) -> str:
    env = os.environ if environment is None else environment
    effective_uid = os.getuid() if uid is None else uid
    session = (
        env.get("WAYLAND_DISPLAY")
        or env.get("DISPLAY")
        or env.get("XDG_SESSION_ID")
        or env.get("DBUS_SESSION_BUS_ADDRESS")
        or "default"
    )
    identity = f"{effective_uid}\0{session}".encode()
    digest = hashlib.blake2s(identity, digest_size=8).hexdigest()
    return f"codexbar-{effective_uid}-{digest}"


def _runtime_directory() -> Path:
    configured = os.environ.get("XDG_RUNTIME_DIR")
    if configured:
        return Path(configured)
    path = Path(tempfile.gettempdir()) / f"codexbar-runtime-{os.getuid()}"
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    with suppress(OSError):
        path.chmod(0o700)
    return path


class _OwnershipGuard:
    def __init__(self, endpoint_name: str) -> None:
        digest = hashlib.blake2s(endpoint_name.encode(), digest_size=8).hexdigest()
        self._path = _runtime_directory() / f"codexbar-instance-{digest}.lock"
        self._fd: int | None = None

    def try_acquire(self) -> bool:
        if self._fd is not None:
            return True
        fd = os.open(self._path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            return False
        except OSError:
            os.close(fd)
            raise
        self._fd = fd
        return True

    def close(self) -> None:
        fd = self._fd
        self._fd = None
        if fd is None:
            return
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _ensure_qapplication() -> QApplication:
    global _APPLICATION

    instance = QApplication.instance()
    if isinstance(instance, QApplication):
        _APPLICATION = instance
        return instance
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    _APPLICATION = app
    return app


def send_instance_command(
    endpoint_name: str,
    command: InstanceCommand,
    *,
    timeout_ms: int = _FAST_COMMAND_TIMEOUT_MS,
) -> InstanceReply | None:
    socket = QLocalSocket()
    try:
        socket.connectToServer(endpoint_name)
        if not socket.waitForConnected(timeout_ms):
            return None
        socket.write(encode_instance_command(command))
        if not socket.waitForBytesWritten(timeout_ms):
            return None
        if not socket.waitForReadyRead(timeout_ms):
            return None
        payload = cast(bytes, socket.readLine().data())
        try:
            return parse_instance_reply(payload)
        except ValueError:
            return InstanceReply.ERROR
    finally:
        socket.abort()


class QtLocalInstanceOwner:
    def __init__(self, endpoint_name: str, guard: _OwnershipGuard) -> None:
        self._endpoint_name = endpoint_name
        self._guard = guard
        self._server = QLocalServer()
        self._server.newConnection.connect(self._on_new_connection)
        self._show_details: Callable[[], None] | None = None
        self._pending_show_details = False
        self._clients: set[QLocalSocket] = set()

    @property
    def diagnostic(self) -> InstanceOwnershipDiagnosticState:
        return InstanceOwnershipDiagnosticState(
            state=InstanceOwnershipState.OWNER,
            endpoint_name=self._endpoint_name,
            summary="This process owns the per-session CodexBar GUI endpoint.",
        )

    def listen(self) -> bool:
        return self._server.listen(self._endpoint_name)

    def bind_show_details(self, callback: Callable[[], None]) -> None:
        self._show_details = callback
        if self._pending_show_details:
            self._pending_show_details = False
            callback()

    def _on_new_connection(self) -> None:
        while self._server.hasPendingConnections():
            socket = self._server.nextPendingConnection()
            if socket is None:
                continue
            self._clients.add(socket)
            socket.readyRead.connect(lambda socket=socket: self._read_client(socket))
            socket.disconnected.connect(lambda socket=socket: self._drop_client(socket))
            if socket.canReadLine():
                self._read_client(socket)

    def _read_client(self, socket: QLocalSocket) -> None:
        while socket.canReadLine():
            payload = cast(bytes, socket.readLine().data())
            try:
                command = parse_instance_command(payload)
            except ValueError:
                self._reply(socket, InstanceReply.ERROR)
                continue
            if command is InstanceCommand.PING:
                self._reply(socket, InstanceReply.PONG)
                continue
            if command is InstanceCommand.SHOW_DETAILS:
                callback = self._show_details
                if callback is None:
                    self._pending_show_details = True
                else:
                    try:
                        callback()
                    except Exception:
                        traceback.print_exc()
                        self._reply(socket, InstanceReply.ERROR)
                        continue
                self._reply(socket, InstanceReply.OK)

    @staticmethod
    def _reply(socket: QLocalSocket, reply: InstanceReply) -> None:
        socket.write(encode_instance_reply(reply))
        socket.flush()

    def _drop_client(self, socket: QLocalSocket) -> None:
        self._clients.discard(socket)
        socket.deleteLater()

    def close(self) -> None:
        for socket in tuple(self._clients):
            socket.abort()
            socket.deleteLater()
        self._clients.clear()
        self._server.close()
        self._guard.close()


def _secondary_resolution(endpoint_name: str) -> InstanceResolution:
    return InstanceResolution(
        diagnostic=InstanceOwnershipDiagnosticState(
            state=InstanceOwnershipState.SECONDARY,
            endpoint_name=endpoint_name,
            summary="Existing CodexBar GUI owner accepted SHOW_DETAILS.",
        )
    )


def _ambiguous_error(endpoint_name: str, message: str) -> InstanceOwnershipError:
    diagnostic = InstanceOwnershipDiagnosticState(
        state=InstanceOwnershipState.AMBIGUOUS,
        endpoint_name=endpoint_name,
        summary=message,
    )
    return InstanceOwnershipError(message, diagnostic=diagnostic)


def _signal_existing_owner(endpoint_name: str) -> bool:
    return (
        send_instance_command(endpoint_name, InstanceCommand.SHOW_DETAILS)
        is InstanceReply.OK
    )


def _wait_for_guard_or_owner(endpoint_name: str, guard: _OwnershipGuard) -> bool:
    deadline = time.monotonic() + (_BUSY_OWNER_WAIT_MS / 1000.0)
    while time.monotonic() < deadline:
        if _signal_existing_owner(endpoint_name):
            return False
        if guard.try_acquire():
            return True
        time.sleep(_BUSY_OWNER_RETRY_MS / 1000.0)
    return False


def resolve_gui_instance(*, endpoint_name: str | None = None) -> InstanceResolution:
    _ensure_qapplication()
    endpoint = endpoint_name or instance_endpoint_name()

    if _signal_existing_owner(endpoint):
        return _secondary_resolution(endpoint)

    try:
        guard = _OwnershipGuard(endpoint)
        acquired = _wait_for_guard_or_owner(endpoint, guard)
    except OSError as exc:
        raise _ambiguous_error(
            endpoint,
            "Unable to establish the local GUI ownership guard safely.",
        ) from exc
    if not acquired:
        if _signal_existing_owner(endpoint):
            return _secondary_resolution(endpoint)
        raise _ambiguous_error(
            endpoint,
            "GUI ownership is ambiguous; refusing to start a competing CodexBar runtime.",
        )

    if _signal_existing_owner(endpoint):
        guard.close()
        return _secondary_resolution(endpoint)

    QLocalServer.removeServer(endpoint)
    owner = QtLocalInstanceOwner(endpoint, guard)
    if owner.listen():
        return InstanceResolution(diagnostic=owner.diagnostic, owner=owner)

    if _signal_existing_owner(endpoint):
        owner.close()
        return _secondary_resolution(endpoint)

    owner.close()
    raise _ambiguous_error(
        endpoint,
        "Unable to establish the CodexBar GUI endpoint safely; no second runtime was started.",
    )
