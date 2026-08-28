from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol

from reactive_runtime.canonical import write_json


@dataclass(frozen=True)
class ProviderSuccess:
    content: str
    finish_reason: str
    usage: Mapping[str, Any]


@dataclass(frozen=True)
class ProviderFailure:
    error_type: str
    error_message: str


ProviderOutcome = ProviderSuccess | ProviderFailure


class Provider(Protocol):
    def complete(self, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


class OneShotProvider:
    """Invoke a provider callback exactly once and never retry."""

    def __init__(
        self,
        complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> None:
        self._complete = complete
        self.attempts = 0

    def invoke(
        self, payload: Mapping[str, Any], *, custody_root: Path | None = None
    ) -> ProviderOutcome:
        if self.attempts != 0:
            raise RuntimeError("one-shot provider adapter cannot be invoked twice")
        self.attempts += 1
        if custody_root is not None:
            write_json(custody_root / "REQUEST.json", dict(payload))
        try:
            value = self._complete(payload)
            if custody_root is not None:
                write_json(custody_root / "RESPONSE.json", dict(value))
            content = value.get("content")
            finish_reason = value.get("finish_reason")
            usage = value.get("usage")
            if not isinstance(content, str):
                raise ValueError("provider response lacks string content")
            if not isinstance(finish_reason, str):
                raise ValueError("provider response lacks finish reason")
            if not isinstance(usage, Mapping):
                raise ValueError("provider response lacks usage")
            outcome: ProviderOutcome = ProviderSuccess(
                content, finish_reason, dict(usage)
            )
        except Exception as exc:
            outcome = ProviderFailure(type(exc).__name__, str(exc))
            if custody_root is not None:
                write_json(
                    custody_root / "FAILURE.json",
                    {
                        "error_message": str(exc),
                        "error_type": type(exc).__name__,
                        "no_retry": True,
                    },
                )
        if custody_root is not None:
            write_json(
                custody_root / "ATTEMPT.json",
                {
                    "attempts": self.attempts,
                    "completed": isinstance(outcome, ProviderSuccess),
                    "no_retry": True,
                    "schema": "bounded-host-provider-attempt-v0",
                },
            )
        return outcome
