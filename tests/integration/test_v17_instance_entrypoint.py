from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

import pytest

import codexbar.__main__ as cli
from codexbar.application.instance_ownership import (
    InstanceOwnershipDiagnosticState,
    InstanceOwnershipState,
    InstanceResolution,
)


@dataclass
class _FakeOwner:
    closed: bool = False

    @property
    def diagnostic(self) -> InstanceOwnershipDiagnosticState:
        return InstanceOwnershipDiagnosticState(
            state=InstanceOwnershipState.OWNER,
            endpoint_name="test",
            summary="owner",
        )

    def bind_show_details(self, callback: object) -> None:
        del callback

    def close(self) -> None:
        self.closed = True


def test_second_gui_launch_exits_before_runtime_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secondary = InstanceResolution(
        diagnostic=InstanceOwnershipDiagnosticState(
            state=InstanceOwnershipState.SECONDARY,
            endpoint_name="test",
            summary="secondary",
        )
    )
    import codexbar.ui.launcher as launcher

    monkeypatch.setattr(launcher, "resolve_gui_instance", lambda: secondary)
    monkeypatch.setattr(
        cli,
        "build_gui_runtime",
        lambda **_: (_ for _ in ()).throw(AssertionError("runtime must not be built")),
    )

    assert cli.main(["--gui", "--mock"]) == 0


def test_owner_guard_closes_when_runtime_construction_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from codexbar.domain.errors import CodexBarError

    owner = _FakeOwner()
    resolution = InstanceResolution(diagnostic=owner.diagnostic, owner=owner)
    import codexbar.ui.launcher as launcher

    monkeypatch.setattr(launcher, "resolve_gui_instance", lambda: resolution)

    def fail_runtime(**_: object) -> object:
        raise CodexBarError("construction failed")

    monkeypatch.setattr(cli, "build_gui_runtime", fail_runtime)
    assert cli.main(["--gui", "--mock"]) == 2
    assert owner.closed


def test_owner_runtime_lifecycle_closes_runtime_and_guard(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner = _FakeOwner()
    resolution = InstanceResolution(diagnostic=owner.diagnostic, owner=owner)
    import codexbar.ui.launcher as launcher

    runtime = SimpleNamespace(
        provider=object(),
        settings_repository=object(),
        notifier=object(),
        history_controller=object(),
        presenter=object(),
        redeem_manager=None,
        context_presenter=object(),
        closed=False,
    )

    def close_runtime() -> None:
        runtime.closed = True

    runtime.close = close_runtime
    monkeypatch.setattr(launcher, "resolve_gui_instance", lambda: resolution)
    monkeypatch.setattr(cli, "build_gui_runtime", lambda **_: runtime)

    def fake_run_tray(provider: object, **kwargs: object) -> int:
        assert provider is runtime.provider
        assert kwargs["instance_owner"] is owner
        return 17

    monkeypatch.setattr(launcher, "run_tray", fake_run_tray)
    assert cli.main(["--gui", "--mock"]) == 17
    assert runtime.closed
    assert owner.closed
