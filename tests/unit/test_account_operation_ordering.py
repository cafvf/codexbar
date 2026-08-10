from concurrent.futures import ThreadPoolExecutor
from threading import Event
from time import sleep

from codexbar.application.account_operations import AccountOperationCoordinator


def test_redeem_transaction_holds_single_account_lane_across_refetch() -> None:
    coordinator = AccountOperationCoordinator()
    consume_started = Event()
    allow_finish = Event()
    order = []

    def redeem_transaction():
        def operation():
            order.append("consume")
            consume_started.set()
            allow_finish.wait(timeout=1)
            order.append("refetch")
        coordinator.execute(operation)

    def refresh():
        consume_started.wait(timeout=1)
        coordinator.execute(lambda: order.append("refresh"))

    with ThreadPoolExecutor(max_workers=2) as executor:
        redeem_future = executor.submit(redeem_transaction)
        refresh_future = executor.submit(refresh)
        sleep(0.02)
        assert order == ["consume"]
        allow_finish.set()
        redeem_future.result(timeout=1)
        refresh_future.result(timeout=1)

    assert order == ["consume", "refetch", "refresh"]
