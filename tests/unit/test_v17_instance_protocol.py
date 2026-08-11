from __future__ import annotations

import pytest

from codexbar.application.instance_ownership import (
    InstanceCommand,
    InstanceOwnershipDiagnosticState,
    InstanceOwnershipState,
    InstanceReply,
    InstanceResolution,
    encode_instance_command,
    encode_instance_reply,
    parse_instance_command,
    parse_instance_reply,
)
from codexbar.domain.diagnostics import OperationalHealth, SubsystemRole


def test_ping_and_show_details_protocol_round_trip() -> None:
    assert (
        parse_instance_command(encode_instance_command(InstanceCommand.PING))
        is InstanceCommand.PING
    )
    assert (
        parse_instance_command(encode_instance_command(InstanceCommand.SHOW_DETAILS))
        is InstanceCommand.SHOW_DETAILS
    )
    assert parse_instance_reply(encode_instance_reply(InstanceReply.PONG)) is InstanceReply.PONG
    assert parse_instance_reply(encode_instance_reply(InstanceReply.OK)) is InstanceReply.OK


def test_protocol_rejects_unknown_or_non_ascii_commands() -> None:
    with pytest.raises(ValueError, match="unsupported instance command"):
        parse_instance_command(b"QUIT\n")
    with pytest.raises(ValueError, match="ASCII"):
        parse_instance_command("MOSTRAR\N{SNOWMAN}\n".encode())


def test_owner_resolution_requires_owner_binding() -> None:
    diagnostic = InstanceOwnershipDiagnosticState(
        state=InstanceOwnershipState.OWNER,
        endpoint_name="codexbar-test",
        summary="owner",
    )
    with pytest.raises(ValueError, match="owner binding"):
        InstanceResolution(diagnostic=diagnostic)


def test_ambiguous_instance_diagnostic_fails_overall_invariant() -> None:
    diagnostic = InstanceOwnershipDiagnosticState(
        state=InstanceOwnershipState.AMBIGUOUS,
        endpoint_name="codexbar-test",
        summary="ambiguous",
    ).as_subsystem_health()
    assert diagnostic.role is SubsystemRole.INSTANCE_OWNERSHIP
    assert diagnostic.operational_health is OperationalHealth.FAILED
