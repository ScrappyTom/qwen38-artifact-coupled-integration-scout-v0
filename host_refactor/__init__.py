"""Event-driven host runtime refactor.

This package is intentionally isolated from frozen historical runners until
provider-free acceptance is complete.
"""

from host_refactor.kernel import HostKernel, InvalidTransition
from host_refactor.model import (
    CanonicalBodyIdentity,
    DeliveryState,
    ExactResult,
    ExactStateObject,
    HostEvent,
    ProjectedHostState,
    ResultProjection,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)

__all__ = [
    "CanonicalBodyIdentity",
    "DeliveryState",
    "ExactResult",
    "ExactStateObject",
    "HostEvent",
    "HostKernel",
    "InvalidTransition",
    "ProjectedHostState",
    "ResultProjection",
    "RunConfiguration",
    "TerminalCode",
    "TranscriptEntry",
]
