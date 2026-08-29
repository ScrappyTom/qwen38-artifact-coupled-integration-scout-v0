from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from reactive_runtime.anchored_provenance import (
    DELTA_TOKEN_BUDGET,
    AnchoredProvenanceRegister,
    admit_anchored_delta,
    anchored_delta_messages,
)
from reactive_runtime.canonical import canonical_json_text, sha256_bytes
from reactive_runtime.records import ResultRecord
from tools.live_common import provider_payload

from host_refactor.checkpoint import RuntimeCounters
from host_refactor.kernel import HostKernel
from host_refactor.model import ExactStateObject, TranscriptEntry
from host_refactor.provider import OneShotProvider, ProviderFailure, ProviderSuccess
from host_refactor.runner import HostRunner, RunnerStep
from host_refactor.trellis_adapter import TrellisDomainAdapter, _legacy_ledger


BASELINE_CONFIGURATION = "V0_EXACT_ARTIFACT"
TREATMENT_CONFIGURATION = "V1_TEMPORARY_PROVENANCE_SCAFFOLD"
CONFIGURATIONS = (BASELINE_CONFIGURATION, TREATMENT_CONFIGURATION)
SCAFFOLD_SLOT = "temporary_provenance_scaffold"
VERIFICATION_SLOT = "current_verification_frame"
MAINTENANCE_SEED = 884_220


class MaintenanceFailure(RuntimeError):
    """A charged maintenance attempt could not produce a completed response."""


@dataclass(frozen=True)
class InteractionLifecycle:
    configuration_id: str
    register: AnchoredProvenanceRegister = AnchoredProvenanceRegister()
    maintenance_calls: int = 0
    maintenance_serialized_tokens: int = 0
    scaffold_ever_exposed: bool = False
    scaffold_active: bool = False
    phase: str = "construction"
    relief_events: tuple[Mapping[str, Any], ...] = ()
    maintenance_events: tuple[Mapping[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if self.configuration_id not in CONFIGURATIONS:
            raise ValueError(f"unknown interaction configuration: {self.configuration_id}")

    @property
    def treatment(self) -> bool:
        return self.configuration_id == TREATMENT_CONFIGURATION

    def as_dict(self) -> dict[str, Any]:
        return {
            "configuration_id": self.configuration_id,
            "maintenance_calls": self.maintenance_calls,
            "maintenance_events": [dict(row) for row in self.maintenance_events],
            "maintenance_serialized_tokens": self.maintenance_serialized_tokens,
            "phase": self.phase,
            "register": self.register.as_dict(),
            "relief_events": [dict(row) for row in self.relief_events],
            "scaffold_active": self.scaffold_active,
            "scaffold_ever_exposed": self.scaffold_ever_exposed,
            "schema": "trellis-interaction-lifecycle-v0",
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "InteractionLifecycle":
        if value.get("schema") != "trellis-interaction-lifecycle-v0":
            raise ValueError("unsupported interaction lifecycle schema")
        register = value.get("register")
        if not isinstance(register, Mapping):
            raise ValueError("interaction lifecycle lacks register")
        relief = value.get("relief_events", [])
        maintenance = value.get("maintenance_events", [])
        if not isinstance(relief, list) or not isinstance(maintenance, list):
            raise ValueError("interaction lifecycle traces must be lists")
        return cls(
            configuration_id=str(value["configuration_id"]),
            register=AnchoredProvenanceRegister.from_dict(register),
            maintenance_calls=int(value["maintenance_calls"]),
            maintenance_serialized_tokens=int(value["maintenance_serialized_tokens"]),
            scaffold_ever_exposed=bool(value["scaffold_ever_exposed"]),
            scaffold_active=bool(value["scaffold_active"]),
            phase=str(value["phase"]),
            relief_events=tuple(dict(row) for row in relief),
            maintenance_events=tuple(dict(row) for row in maintenance),
        )


@dataclass(frozen=True)
class InteractionStep:
    runner_step: RunnerStep
    lifecycle: InteractionLifecycle


def _catalog(task_root: Path) -> dict[str, dict[str, object]]:
    import json

    value = json.loads((task_root / "SOURCE_CATALOG.json").read_text(encoding="utf-8"))
    return {str(row["source_id"]): dict(row) for row in value["sources"]}


def _visible_state(
    kernel: HostKernel,
    state_object: ExactStateObject,
    *,
    entry_id: str,
) -> HostKernel:
    current = kernel.project().state_slots.get(state_object.slot_id)
    if current is None or current.as_dict() != state_object.as_dict():
        kernel = kernel.set_state_object(state_object)
    if not any(
        entry.state_slot_id == state_object.slot_id
        for entry in kernel.project().transcript
    ):
        kernel = kernel.append_transcript(
            TranscriptEntry(
                entry_id=entry_id,
                role="user",
                content=state_object.exact_content,
                state_slot_id=state_object.slot_id,
                entry_kind="exact_state_slot",
            )
        )
    return kernel


def _scaffold_state(
    adapter: TrellisDomainAdapter,
    lifecycle: InteractionLifecycle,
) -> ExactStateObject:
    return ExactStateObject(
        slot_id=SCAFFOLD_SLOT,
        object_id=f"semantic-scaffold:{adapter.spec.configuration.task_id}",
        object_version=lifecycle.register.sha256,
        exact_content=lifecycle.register.render(),
        metadata={
            "active": True,
            "authority": "non_authoritative_derivative",
            "claim_count": len(lifecycle.register.claims),
            "phase": "construction",
            "readiness_authority": False,
        },
    )


def _demoted_scaffold_state(
    adapter: TrellisDomainAdapter,
    lifecycle: InteractionLifecycle,
) -> ExactStateObject:
    content = canonical_json_text(
        {
            "active": False,
            "exact_external_register_sha256": lifecycle.register.sha256,
            "reason": "construction_scaffold_demoted_at_verification",
            "reopen": "not_actor_exposed_in_v0",
            "schema": "semantic-scaffold-lifecycle-receipt-v0",
        }
    )
    return ExactStateObject(
        slot_id=SCAFFOLD_SLOT,
        object_id=f"semantic-scaffold:{adapter.spec.configuration.task_id}",
        object_version=f"demoted:{lifecycle.register.sha256}",
        exact_content=content,
        metadata={
            "active": False,
            "phase": "verification",
            "register_sha256": lifecycle.register.sha256,
        },
    )


def _verification_state(adapter: TrellisDomainAdapter) -> ExactStateObject:
    binding = adapter.world.current_check_binding()
    content = canonical_json_text(
        {
            "candidate_sha256": adapter.world.candidate_sha256,
            "candidate_version": adapter.world.candidate_version,
            "check_binding": binding,
            "phase": adapter.world.phase,
            "readiness": "not_adjudicated",
            "schema": "trellis-current-verification-frame-v0",
        }
    )
    return ExactStateObject(
        slot_id=VERIFICATION_SLOT,
        object_id=f"verification:{adapter.spec.configuration.task_id}",
        object_version=sha256_bytes(content.encode("utf-8")),
        exact_content=content,
        metadata={
            "candidate_sha256": adapter.world.candidate_sha256,
            "check_currency": None if binding is None else binding.get("currency"),
            "phase": adapter.world.phase,
        },
    )


class InteractionOrchestrator:
    """Adds a fallible construction scaffold around, never inside, host mechanics."""

    def __init__(
        self,
        *,
        host: HostRunner,
        adapter: TrellisDomainAdapter,
        lifecycle: InteractionLifecycle,
        count_messages: Callable[[list[dict[str, str]]], int],
        count_text: Callable[[str], int],
        maintenance_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]] | None,
        maximum_maintenance_calls: int = 18,
    ) -> None:
        self.host = host
        self.adapter = adapter
        self.lifecycle = lifecycle
        self.count_messages = count_messages
        self.count_text = count_text
        self.maintenance_complete = maintenance_complete
        self.maximum_maintenance_calls = maximum_maintenance_calls
        if lifecycle.treatment and maintenance_complete is None:
            raise ValueError("treatment requires a maintenance provider")

    def _maintenance(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        result_ids: Sequence[str],
        custody_root: Path | None,
    ) -> tuple[HostKernel, RuntimeCounters]:
        if not self.lifecycle.treatment:
            return kernel, counters
        ledger = _legacy_ledger(kernel)
        records: list[ResultRecord] = [
            ledger.get(result_id)
            for result_id in result_ids
            if ledger.get(result_id).result_kind == "source_observation"
        ]
        if not records:
            return kernel, counters
        if self.lifecycle.maintenance_calls >= self.maximum_maintenance_calls:
            raise MaintenanceFailure("maintenance_call_budget_exhausted")
        messages = anchored_delta_messages(
            task_text=(self.adapter.spec.paths.task_root / "TASK.md").read_text(
                encoding="utf-8"
            ),
            register=self.lifecycle.register,
            newly_externalized=records,
            source_versions=self.adapter.world.source_versions,
        )
        prompt_tokens = self.count_messages(messages)
        if (
            prompt_tokens + DELTA_TOKEN_BUDGET
            > self.adapter.spec.configuration.context_window
        ):
            raise MaintenanceFailure("maintenance_prompt_infeasible")
        if (
            self.adapter.spec.configuration.maximum_serialized_tokens is not None
            and counters.serialized_tokens + prompt_tokens + DELTA_TOKEN_BUDGET
            > self.adapter.spec.configuration.maximum_serialized_tokens
        ):
            raise MaintenanceFailure("maintenance_token_budget_exhausted")
        provider = OneShotProvider(self.maintenance_complete)  # type: ignore[arg-type]
        outcome = provider.invoke(
            provider_payload(
                messages,
                MAINTENANCE_SEED,
                {"type": "text"},
                max_tokens=DELTA_TOKEN_BUDGET,
            ),
            custody_root=custody_root,
        )
        if isinstance(outcome, ProviderFailure):
            raise MaintenanceFailure(
                f"maintenance_provider_failure:{outcome.error_type}:{outcome.error_message}"
            )
        if not isinstance(outcome, ProviderSuccess):  # pragma: no cover
            raise AssertionError("unknown maintenance provider outcome")
        usage_prompt = outcome.usage.get("prompt_tokens")
        usage_completion = outcome.usage.get("completion_tokens")
        usage_total = outcome.usage.get("total_tokens")
        if usage_prompt != prompt_tokens:
            raise MaintenanceFailure(
                f"maintenance_prompt_usage_mismatch:{usage_prompt}:{prompt_tokens}"
            )
        if (
            not isinstance(usage_completion, int)
            or not 0 <= usage_completion <= DELTA_TOKEN_BUDGET
        ):
            raise MaintenanceFailure("maintenance_completion_usage_invalid")
        if usage_total != usage_prompt + usage_completion:
            raise MaintenanceFailure("maintenance_usage_arithmetic_invalid")
        counters = RuntimeCounters(
            serialized_tokens=counters.serialized_tokens + int(usage_total),
            provider_attempts=counters.provider_attempts + provider.attempts,
        )
        if outcome.finish_reason not in set(
            self.adapter.spec.configuration.accepted_finish_reasons
        ):
            event = {
                "admitted_claim_ids": [],
                "after_sha256": self.lifecycle.register.sha256,
                "before_sha256": self.lifecycle.register.sha256,
                "changed": False,
                "disposition": "finish_reason_reject",
                "finish_reason": outcome.finish_reason,
                "input_result_ids": [record.result_id for record in records],
                "maintenance_call": self.lifecycle.maintenance_calls + 1,
                "output_sha256": sha256_bytes(outcome.content.encode("utf-8")),
                "prompt_tokens": prompt_tokens,
                "rejected_claim_ids": [],
                "total_tokens": usage_total,
            }
            self.lifecycle = replace(
                self.lifecycle,
                maintenance_calls=self.lifecycle.maintenance_calls + 1,
                maintenance_serialized_tokens=(
                    self.lifecycle.maintenance_serialized_tokens + int(usage_total)
                ),
                maintenance_events=(*self.lifecycle.maintenance_events, event),
            )
            return kernel, counters
        admission = admit_anchored_delta(
            outcome.content,
            count_text=self.count_text,
            source_catalog=_catalog(self.adapter.spec.paths.task_root),
            task_root=self.adapter.spec.paths.task_root,
            newly_externalized=records,
            current_source_versions=self.adapter.world.source_versions,
        )
        transition = self.lifecycle.register.apply(
            admission,
            current_source_versions=self.adapter.world.source_versions,
            count_text=self.count_text,
        )
        event = {
            "admitted_claim_ids": list(transition.admitted_claim_ids),
            "after_sha256": transition.after_sha256,
            "before_sha256": transition.before_sha256,
            "changed": transition.changed,
            "disposition": transition.disposition,
            "finish_reason": outcome.finish_reason,
            "input_result_ids": [record.result_id for record in records],
            "maintenance_call": self.lifecycle.maintenance_calls + 1,
            "output_sha256": sha256_bytes(outcome.content.encode("utf-8")),
            "prompt_tokens": prompt_tokens,
            "rejected_claim_ids": list(transition.rejected_claim_ids),
            "total_tokens": usage_total,
        }
        self.lifecycle = replace(
            self.lifecycle,
            register=transition.register,
            maintenance_calls=self.lifecycle.maintenance_calls + 1,
            maintenance_serialized_tokens=(
                self.lifecycle.maintenance_serialized_tokens + int(usage_total)
            ),
            maintenance_events=(*self.lifecycle.maintenance_events, event),
        )
        if transition.changed:
            kernel = _visible_state(
                kernel,
                _scaffold_state(self.adapter, self.lifecycle),
                entry_id="INTERACTION-SEMANTIC-SCAFFOLD",
            )
            self.lifecycle = replace(
                self.lifecycle,
                scaffold_ever_exposed=True,
                scaffold_active=True,
            )
        return kernel, counters

    def prepare(
        self,
        kernel: HostKernel,
        counters: RuntimeCounters,
        *,
        custody_root: Path | None = None,
    ) -> tuple[HostKernel, RuntimeCounters]:
        """Restore feasibility and charge any treatment maintenance before actor I/O."""

        while True:
            state = kernel.project()
            next_call = max((*state.completed_calls, *state.failed_calls), default=0) + 1
            pending = tuple(
                result_id
                for result_id, row in state.results.items()
                if row.pending_call == next_call
            )
            outcome = self.host.capacity.ensure_feasible(
                kernel,
                protected_result_ids=pending,
            )
            event = {
                "audits": [
                    {
                        "before_tokens": row.before_tokens,
                        "prospective_tokens": row.prospective_tokens,
                        "reason": row.reason,
                        "result_id": row.result_id,
                        "savings": row.savings,
                        "selected": row.selected,
                    }
                    for row in outcome.audits
                ],
                "feasible": outcome.feasible,
                "prompt_tokens": outcome.prompt_tokens,
                "relief_event": len(self.lifecycle.relief_events) + 1,
                "selected_result_ids": list(outcome.selected_result_ids),
            }
            kernel = outcome.kernel
            if outcome.selected_result_ids:
                self.lifecycle = replace(
                    self.lifecycle,
                    relief_events=(*self.lifecycle.relief_events, event),
                )
                maintenance_root = None
                if custody_root is not None:
                    maintenance_root = (
                        custody_root
                        / "maintenance"
                        / f"call-{self.lifecycle.maintenance_calls + 1:03d}"
                    )
                kernel, counters = self._maintenance(
                    kernel,
                    counters,
                    outcome.selected_result_ids,
                    maintenance_root,
                )
                continue
            return kernel, counters

    def _sync_phase_state(self, kernel: HostKernel) -> HostKernel:
        if self.adapter.world.phase != "verification":
            return kernel
        if self.lifecycle.phase != "verification":
            self.lifecycle = replace(self.lifecycle, phase="verification")
        if self.lifecycle.treatment and self.lifecycle.scaffold_active:
            kernel = _visible_state(
                kernel,
                _demoted_scaffold_state(self.adapter, self.lifecycle),
                entry_id="INTERACTION-SEMANTIC-SCAFFOLD",
            )
            self.lifecycle = replace(self.lifecycle, scaffold_active=False)
        return _visible_state(
            kernel,
            _verification_state(self.adapter),
            entry_id="INTERACTION-CURRENT-VERIFICATION",
        )

    def step(
        self,
        *,
        kernel: HostKernel,
        counters: RuntimeCounters,
        actor_complete: Callable[[Mapping[str, Any]], Mapping[str, Any]],
        custody_root: Path | None = None,
    ) -> InteractionStep:
        kernel, counters = self.prepare(kernel, counters, custody_root=custody_root)
        actor_root = None if custody_root is None else custody_root / "actor"
        runner_step = self.host.step(
            kernel=kernel,
            counters=counters,
            provider_complete=actor_complete,
            domain=self.adapter,
            provider_custody_root=actor_root,
        )
        synced = self._sync_phase_state(runner_step.kernel)
        if synced is not runner_step.kernel:
            runner_step = replace(runner_step, kernel=synced)
        return InteractionStep(runner_step=runner_step, lifecycle=self.lifecycle)
