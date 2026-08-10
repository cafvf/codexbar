from __future__ import annotations

from collections.abc import Callable
from threading import Lock
from typing import TypeVar

from codexbar.application.account import AccountRateLimitsObservation, AccountRateLimitsReader

T = TypeVar("T")


class AccountOperationClosedError(RuntimeError):
    """Raised when an account operation is submitted after coordinator shutdown."""


class AccountOperationCoordinator:
    """Single in-process lane shared by account reads and later account mutations."""

    def __init__(self) -> None:
        self._operation_lock = Lock()
        self._state_lock = Lock()
        self._closed = False

    @property
    def closed(self) -> bool:
        with self._state_lock:
            return self._closed

    def execute(self, operation: Callable[[], T]) -> T:
        with self._state_lock:
            if self._closed:
                raise AccountOperationClosedError("account operation coordinator is closed")

        with self._operation_lock:
            with self._state_lock:
                if self._closed:
                    raise AccountOperationClosedError("account operation coordinator is closed")
            return operation()

    def close(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True

        # Wait for an already-running operation to leave the lane.
        with self._operation_lock:
            pass


class CoordinatedAccountRateLimitsReader:
    """Serialize account reads without changing their synchronous port contract."""

    def __init__(
        self,
        reader: AccountRateLimitsReader,
        coordinator: AccountOperationCoordinator,
    ) -> None:
        self._reader = reader
        self._coordinator = coordinator

    def read_account_rate_limits(self) -> AccountRateLimitsObservation:
        return self._coordinator.execute(self._reader.read_account_rate_limits)
