from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from time import sleep

import pytest

from codexbar.application.account_operations import (
    AccountOperationClosedError,
    AccountOperationCoordinator,
)


def test_account_operations_are_serialized() -> None:
    coordinator = AccountOperationCoordinator()
    state_lock = Lock()
    active = 0
    max_active = 0

    def operation(value: int) -> int:
        nonlocal active, max_active
        with state_lock:
            active += 1
            max_active = max(max_active, active)
        sleep(0.02)
        with state_lock:
            active -= 1
        return value

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda value: coordinator.execute(lambda: operation(value)),
                range(4),
            )
        )

    assert results == [0, 1, 2, 3]
    assert max_active == 1


def test_close_waits_for_running_operation_and_rejects_new_work() -> None:
    coordinator = AccountOperationCoordinator()
    entered = Event()
    release = Event()

    def operation() -> str:
        entered.set()
        release.wait(timeout=1)
        return "done"

    with ThreadPoolExecutor(max_workers=2) as executor:
        running = executor.submit(coordinator.execute, operation)
        assert entered.wait(timeout=1)
        closing = executor.submit(coordinator.close)
        sleep(0.02)
        assert not closing.done()
        release.set()
        assert running.result(timeout=1) == "done"
        closing.result(timeout=1)

    with pytest.raises(AccountOperationClosedError):
        coordinator.execute(lambda: None)


def test_close_is_idempotent() -> None:
    coordinator = AccountOperationCoordinator()

    coordinator.close()
    coordinator.close()

    assert coordinator.closed is True
