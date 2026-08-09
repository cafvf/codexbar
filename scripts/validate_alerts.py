#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from codexbar.application.alerts import AlertEvent, AlertService
from codexbar.application.ports import NotificationPort
from codexbar.domain.errors import NotificationDeliveryError
from codexbar.domain.models import (
    Fraction,
    UsagePolicy,
    UsageSnapshot,
    UsageSource,
    UsageWindow,
    UsageWindowId,
)
from codexbar.infrastructure.notifications import NotifySendNotificationAdapter

DEFAULT_POLICY = UsagePolicy(low_remaining_threshold=Fraction(Decimal("0.20")))
STEP_DELAY_SECONDS = 2.5


class FailingNotifier:
    def notify(self, event: AlertEvent) -> None:
        raise NotificationDeliveryError(
            f"simulated notification failure for {event.window_id.value}"
        )


def make_snapshot(*windows: tuple[str, str, str]) -> UsageSnapshot:
    now = datetime.now(UTC)
    return UsageSnapshot(
        windows=tuple(
            UsageWindow(
                id=UsageWindowId(window_id),
                label=label,
                remaining=Fraction(Decimal(remaining)),
                resets_at=now + timedelta(hours=6),
            )
            for window_id, label, remaining in windows
        ),
        observed_at=now,
        source=UsageSource.MOCK,
    )


def run_sequence(
    title: str,
    steps: list[tuple[str, UsageSnapshot, bool]],
    notifier: NotificationPort,
    *,
    delay_seconds: float = STEP_DELAY_SECONDS,
) -> None:
    print(f"\\n=== {title} ===")
    service = AlertService(notifier)
    for index, (description, snapshot, enabled) in enumerate(steps, start=1):
        print(f"[{index}/{len(steps)}] {description}")
        events = service.process(
            snapshot,
            DEFAULT_POLICY,
            notifications_enabled=enabled,
        )
        states = ", ".join(f"{e.label}:{e.state.value}" for e in events)
        print(f"  transition event(s): {states or 'none'}")
        if index != len(steps):
            time.sleep(delay_seconds)


def scenario_baseline(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "Silent baseline already LOW",
        [("First CURRENT observation already LOW; expect NO notification.",
          make_snapshot(("weekly", "Weekly", "0.10")), True)],
        notifier, delay_seconds=delay,
    )


def scenario_low(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "AVAILABLE -> LOW",
        [
            ("Establish AVAILABLE baseline at 80%; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.80")), True),
            ("Transition to 10%; expect ONE LOW notification for Weekly.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_exhausted(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "LOW -> EXHAUSTED",
        [
            ("Establish LOW baseline at 10%; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
            ("Transition to 0%; expect ONE EXHAUSTED notification for Weekly.",
             make_snapshot(("weekly", "Weekly", "0")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_dedupe(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "LOW deduplication",
        [
            ("Establish AVAILABLE baseline at 80%; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.80")), True),
            ("Transition to LOW at 10%; expect ONE LOW notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
            ("Remain LOW at 9%; expect NO additional notification.",
             make_snapshot(("weekly", "Weekly", "0.09")), True),
            ("Remain LOW at 8%; expect NO additional notification.",
             make_snapshot(("weekly", "Weekly", "0.08")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_rearm(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "Recovery and re-arm",
        [
            ("Establish AVAILABLE baseline at 80%; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.80")), True),
            ("Transition to LOW; expect ONE LOW notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
            ("Recover to AVAILABLE; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.60")), True),
            ("Transition to LOW again; expect ONE NEW LOW notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_disabled(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "Disable / re-enable without replay",
        [
            ("Establish AVAILABLE baseline with notifications disabled.",
             make_snapshot(("weekly", "Weekly", "0.80")), False),
            ("Transition to LOW while disabled; expect NO desktop notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), False),
            ("Re-enable while still LOW; expect NO replay notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
            ("Recover to AVAILABLE; expect NO notification.",
             make_snapshot(("weekly", "Weekly", "0.60")), True),
            ("Transition to LOW after re-enable; expect ONE LOW notification.",
             make_snapshot(("weekly", "Weekly", "0.10")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_restart(notifier: NotificationPort, delay: float) -> None:
    print("\\n=== Restart / new tracker baseline ===")
    first = AlertService(notifier)
    first.process(make_snapshot(("weekly", "Weekly", "0.80")), DEFAULT_POLICY,
                  notifications_enabled=True)
    first.process(make_snapshot(("weekly", "Weekly", "0.10")), DEFAULT_POLICY,
                  notifications_enabled=True)
    print("[1/2] First runtime reached LOW; one LOW notification should have appeared.")
    time.sleep(delay)
    second = AlertService(notifier)
    events = second.process(make_snapshot(("weekly", "Weekly", "0.10")), DEFAULT_POLICY,
                            notifications_enabled=True)
    print("[2/2] New runtime observes already LOW; expect NO notification.")
    print(f"  transition event(s): {len(events)}")


def scenario_multi(notifier: NotificationPort, delay: float) -> None:
    run_sequence(
        "Two windows in one snapshot",
        [
            ("Establish both windows AVAILABLE; expect NO notification.",
             make_snapshot(("five_hour", "5 hours", "0.80"),
                           ("weekly", "Weekly", "0.80")), True),
            ("5 hours -> LOW and Weekly -> EXHAUSTED; expect TWO notifications.",
             make_snapshot(("five_hour", "5 hours", "0.10"),
                           ("weekly", "Weekly", "0")), True),
        ],
        notifier, delay_seconds=delay,
    )


def scenario_failure(delay: float) -> None:
    print("\\n=== Notification failure isolation ===")
    service = AlertService(FailingNotifier())
    service.process(make_snapshot(("weekly", "Weekly", "0.80")), DEFAULT_POLICY,
                    notifications_enabled=True)
    time.sleep(delay)
    events = service.process(make_snapshot(("weekly", "Weekly", "0.10")), DEFAULT_POLICY,
                             notifications_enabled=True)
    print(f"  process survived; transition event count: {len(events)}")
    print("  PASS condition: script reaches this line without exception.")


SCENARIOS: dict[str, Callable[[NotificationPort, float], None]] = {
    "baseline": scenario_baseline,
    "low": scenario_low,
    "exhausted": scenario_exhausted,
    "dedupe": scenario_dedupe,
    "rearm": scenario_rearm,
    "disabled": scenario_disabled,
    "restart": scenario_restart,
    "multi-window": scenario_multi,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Physical desktop-notification validation harness for REQ-ALERT-001."
    )
    parser.add_argument("scenario", choices=tuple(SCENARIOS) + ("failure", "all"))
    parser.add_argument("--delay", type=float, default=STEP_DELAY_SECONDS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.scenario == "failure":
        scenario_failure(args.delay)
        return 0

    notifier = NotifySendNotificationAdapter()
    if args.scenario == "all":
        for name in SCENARIOS:
            SCENARIOS[name](notifier, args.delay)
            time.sleep(args.delay)
        scenario_failure(args.delay)
        return 0

    SCENARIOS[args.scenario](notifier, args.delay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
