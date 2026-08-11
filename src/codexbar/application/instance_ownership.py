from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from codexbar.domain.diagnostics import (
    DiagnosticAvailability,
    DiagnosticDetail,
    EvidenceOrigin,
    OperationalHealth,
    SubsystemHealth,
    SubsystemRole,
)
from codexbar.domain.errors import CodexBarError


class InstanceCommand(StrEnum):
    PING = "PING"
    SHOW_DETAILS = "SHOW_DETAILS"


class InstanceReply(StrEnum):
    PONG = "PONG"
    OK = "OK"
    ERROR = "ERROR"


class InstanceOwnershipState(StrEnum):
    OWNER = "owner"
    SECONDARY = "secondary"
    AMBIGUOUS = "ambiguous"


class InstanceOwnershipError(CodexBarError):
    def __init__(self, message: str, *, diagnostic: InstanceOwnershipDiagnosticState) -> None:
        super().__init__(message)
        self.diagnostic = diagnostic


class InstanceOwnerBinding(Protocol):
    @property
    def diagnostic(self) -> InstanceOwnershipDiagnosticState: ...

    def bind_show_details(self, callback: Callable[[], None]) -> None: ...

    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class InstanceOwnershipDiagnosticState:
    state: InstanceOwnershipState
    endpoint_name: str
    summary: str

    def as_subsystem_health(self) -> SubsystemHealth:
        if self.state is InstanceOwnershipState.AMBIGUOUS:
            availability = DiagnosticAvailability.UNAVAILABLE
            health = OperationalHealth.FAILED
        else:
            availability = DiagnosticAvailability.AVAILABLE
            health = OperationalHealth.OK
        return SubsystemHealth(
            name="instance_ownership",
            role=SubsystemRole.INSTANCE_OWNERSHIP,
            availability=availability,
            operational_health=health,
            evidence_origin=EvidenceOrigin.LIVE_RUNTIME,
            summary=self.summary,
            details=(
                DiagnosticDetail("state", self.state.value),
                DiagnosticDetail("endpoint", self.endpoint_name),
            ),
        )


@dataclass(frozen=True, slots=True)
class InstanceResolution:
    diagnostic: InstanceOwnershipDiagnosticState
    owner: InstanceOwnerBinding | None = None

    def __post_init__(self) -> None:
        owns_runtime = self.diagnostic.state is InstanceOwnershipState.OWNER
        if owns_runtime != (self.owner is not None):
            raise ValueError("owner binding must exist exactly for owner resolution")

    @property
    def is_owner(self) -> bool:
        return self.owner is not None


def encode_instance_command(command: InstanceCommand) -> bytes:
    return f"{command.value}\n".encode("ascii")


def parse_instance_command(payload: bytes) -> InstanceCommand:
    try:
        value = payload.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("instance command must be ASCII") from exc
    try:
        return InstanceCommand(value)
    except ValueError as exc:
        raise ValueError(f"unsupported instance command: {value!r}") from exc


def encode_instance_reply(reply: InstanceReply) -> bytes:
    return f"{reply.value}\n".encode("ascii")


def parse_instance_reply(payload: bytes) -> InstanceReply:
    try:
        value = payload.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("instance reply must be ASCII") from exc
    try:
        return InstanceReply(value)
    except ValueError as exc:
        raise ValueError(f"unsupported instance reply: {value!r}") from exc
