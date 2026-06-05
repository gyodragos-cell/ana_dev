from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ErrorPacket:
    code: str
    message: str
    severity: str
    recoverable: bool
    source: str
    details: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "recoverable": self.recoverable,
            "source": self.source,
            "details": dict(self.details),
        }


class ANAError(Exception):
    code = "ANA_ERROR"
    severity = "error"
    recoverable = False

    def __init__(
        self,
        message: str,
        *,
        source: str = "unknown",
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.source = source
        self.details = dict(details or {})

    def packet(self) -> ErrorPacket:
        return ErrorPacket(
            code=self.code,
            message=self.message,
            severity=self.severity,
            recoverable=self.recoverable,
            source=self.source,
            details=self.details,
        )


class RecoverableANAError(ANAError):
    code = "ANA_RECOVERABLE"
    recoverable = True


class FatalANAError(ANAError):
    code = "ANA_FATAL"
    severity = "fatal"
    recoverable = False


class ValidationError(RecoverableANAError):
    code = "VALIDATION_ERROR"


class BoundaryViolation(FatalANAError):
    code = "BOUNDARY_VIOLATION"


class TimeoutFailure(RecoverableANAError):
    code = "TIMEOUT_FAILURE"


class RoutingFailure(RecoverableANAError):
    code = "ROUTING_FAILURE"


class SandboxViolation(FatalANAError):
    code = "SANDBOX_VIOLATION"


def packet_from_exception(exc: Exception, source: str = "unknown") -> ErrorPacket:
    if isinstance(exc, ANAError):
        return exc.packet()
    return ErrorPacket(
        code="UNHANDLED_EXCEPTION",
        message=str(exc),
        severity="fatal",
        recoverable=False,
        source=source,
        details={"type": type(exc).__name__},
    )
