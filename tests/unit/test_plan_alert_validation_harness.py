from __future__ import annotations

import importlib.util
from pathlib import Path

from codexbar.application.notifications import NotificationMessage


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
        self.events: list[NotificationMessage] = []

    def notify(self, message: NotificationMessage) -> None:
        self.events.append(message)


def test_plan_breach_scenario_emits_exactly_one_factual_plan_event() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_plan_breach(notifier, 0)

    assert [message.summary for message in notifier.events] == [
        "CodexBar Plan breach"
    ]


def test_plan_rearm_scenario_emits_again_only_after_recovery() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_plan_rearm(notifier, 0)

    assert len(notifier.events) == 2


def test_plan_disabled_scenario_does_not_replay_suppressed_breach() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_plan_disabled(notifier, 0)

    assert len(notifier.events) == 1


def test_plan_activation_scenario_emits_on_same_cycle_checkpoint_activation() -> None:
    harness = load_harness()
    notifier = RecordingNotifier()

    harness.scenario_plan_activation(notifier, 0)

    assert len(notifier.events) == 1


def test_parser_exposes_plan_scenarios_without_removing_legacy_choices() -> None:
    harness = load_harness()
    parser = harness.build_parser()

    assert parser.parse_args(["low", "--delay", "0"]).scenario == "low"
    assert parser.parse_args(["plan-breach", "--delay", "0"]).scenario == "plan-breach"
    assert parser.parse_args(["plan-activation", "--delay", "0"]).scenario == "plan-activation"
