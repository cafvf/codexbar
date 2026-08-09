from __future__ import annotations

import importlib.util
from pathlib import Path

from codexbar.application.alerts import AlertEvent


def load_harness():
    path = Path("scripts/validate_alerts.py")
    spec = importlib.util.spec_from_file_location("validate_alerts", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RecordingNotifier:
    def __init__(self) -> None:
        self.events: list[AlertEvent] = []

    def notify(self, event: AlertEvent) -> None:
        self.events.append(event)


def test_validation_harness_low_scenario_emits_exactly_one_low_event() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_low(notifier, 0)

    assert len(notifier.events) == 1
    assert notifier.events[0].state.value == "low"


def test_validation_harness_dedupe_scenario_does_not_repeat_low() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_dedupe(notifier, 0)

    assert len(notifier.events) == 1


def test_validation_harness_disabled_scenario_does_not_replay_suppressed_transition() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_disabled(notifier, 0)

    assert len(notifier.events) == 1


def test_validation_harness_multi_window_scenario_emits_two_distinct_events() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_multi(notifier, 0)

    assert [event.window_id.value for event in notifier.events] == [
        "five_hour",
        "weekly",
    ]


def test_validation_harness_parser_lists_expected_scenarios() -> None:
    harness = load_harness()
    parser = harness.build_parser()

    args = parser.parse_args(["low", "--delay", "0"])

    assert args.scenario == "low"
    assert args.delay == 0
