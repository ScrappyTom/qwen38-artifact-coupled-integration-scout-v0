from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from reactive_runtime.actions import action_json_schema, parse_action
from reactive_runtime.configuration import artifact_centered_actor_actions
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.canonical import sha256_bytes
from reactive_runtime.records import ResultLedger, ResultRecord
from tools.live_common import provider_payload

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    DeliveryState,
    ExactStateObject,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import ModelPacket, PacketComposer
from host_refactor.runner import DomainOutcome, HostRunner
from host_refactor.trellis_fixture import historical_result


@dataclass(frozen=True)
class TrellisPaths:
    repository_root: Path
    task_root: Path
    contract_path: Path
    model_lock_path: Path


@dataclass(frozen=True)
class TrellisRuntimeSpec:
    configuration: RunConfiguration
    paths: TrellisPaths
    actor_max_tokens: int = 4_096
    configuration_id: str = "A0_MATRIX_AND_DECISION"


def trellis_spec(repository_root: Path) -> TrellisRuntimeSpec:
    root = repository_root.resolve()
    return TrellisRuntimeSpec(
        configuration=RunConfiguration(
            run_id="trellis-host-refactor-v0-not-authorized",
            task_id="trellis-heat-continuity-decision-v0",
            seed=884_219,
            prompt_limit=20_992,
            response_reserve=4_096,
            tranche_calls=12,
            maximum_calls=60,
            maximum_serialized_tokens=1_800_000,
        ),
        paths=TrellisPaths(
            repository_root=root,
            task_root=root / "task_trellis",
            contract_path=root / "TRELLIS_PRESSURE_SCREEN_CONTRACT.json",
            model_lock_path=root / "TRELLIS_MODEL_PROFILE_LOCK.json",
        ),
    )


def _legacy_ledger(kernel: HostKernel) -> ResultLedger:
    """Compatibility projection for domain reopen execution only.

    Delivery authority remains the new kernel. The legacy ledger is rebuilt
    from it for the historical world adapter and is never written back.
    """

    state = kernel.project()
    ledger = ResultLedger()
    for row in state.results.values():
        result = row.result
        legacy = ResultRecord(
            result_id=result.result_id,
            result_kind=result.result_kind,
            object_id=result.object_id,
            object_version=result.object_version,
            exact_content=result.exact_content,
            acquired_call=result.acquired_call,
            candidate_sha256_after=result.candidate_sha256_after,
            first_model_visible_call=row.first_delivered_call,
            message_index=(
                0 if row.delivery_state is DeliveryState.DELIVERED_RESIDENT else None
            ),
            resident=row.delivery_state is DeliveryState.DELIVERED_RESIDENT,
            relief_eligible=result.relief_eligible,
            evaluated_candidate_sha256=result.evaluated_candidate_sha256,
            raw_result_handle=result.raw_result_handle,
            metadata=dict(result.metadata),
        )
        ledger.add(legacy)
    return ledger


class TrellisDomainAdapter:
    """Task-specific actions around the shared host kernel."""

    def __init__(
        self,
        *,
        spec: TrellisRuntimeSpec,
        trajectory_root: Path,
        count_text: Callable[[str], int] | None = None,
    ) -> None:
        self.spec = spec
        self.world = KeystoneWorld(
            spec.paths.task_root,
            trajectory_root,
            count_text=count_text,
        )
        self.next_result_index = 1

    @property
    def allowed_actions(self) -> tuple[str, ...]:
        return artifact_centered_actor_actions(
            self.spec.configuration_id,
            phase=self.world.phase,
        )

    def current_candidate_state(self) -> ExactStateObject:
        return ExactStateObject(
            slot_id="current_candidate",
            object_id=f"candidate:{self.spec.configuration.task_id}",
            object_version=self.world.candidate_version,
            exact_content="# Exact current candidate\n" + self.world.candidate_packet(),
            metadata={
                "candidate_sha256": self.world.candidate_sha256,
                "candidate_version": self.world.candidate_version,
                "files": self.world.candidate_manifest,
            },
        )

    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        action = parse_action(
            content,
            self.allowed_actions,
            decision_headings=self.world.decision_headings,
        )
        result_id = f"RESULT-{self.next_result_index:03d}"
        self.next_result_index += 1
        execution = self.world.execute(
            action,
            result_id=result_id,
            ledger=_legacy_ledger(kernel),
        )
        legacy = self.world.make_result_record(
            execution,
            result_id=result_id,
            acquired_call=call_index,
        )
        exact = historical_result(legacy.as_dict(include_exact_content=True))
        terminal = TerminalCode.COMPLETED if action.get("action") == "submit" else None
        current = kernel.project().state_slots.get("current_candidate")
        candidate_state = self.current_candidate_state()
        state_updates = (
            ()
            if current is not None
            and current.object_version == candidate_state.object_version
            and current.content_sha256 == candidate_state.content_sha256
            else (candidate_state,)
        )
        return DomainOutcome(
            result=exact,
            state_updates=state_updates,
            terminal=terminal,
        )

    def payload(
        self, packet: ModelPacket, configuration: RunConfiguration
    ) -> Mapping[str, Any]:
        state = packet.manifest_dict()
        del state  # The manifest remains in host custody, not provider payload.
        external_ids = tuple(
            row.result_id
            for row in packet.manifest
            if row.representation == "exact_receipt" and row.result_id is not None
        )
        schema = action_json_schema(
            self.allowed_actions,
            source_ids=self.world.sources,
            reopen_result_ids=external_ids,
            decision_headings=self.world.decision_headings,
            schema_name="trellis_host_refactor_actor_action_v0",
        )
        return provider_payload(
            packet.message_list(),
            configuration.seed,
            schema,
            max_tokens=self.spec.actor_max_tokens,
        )

    def snapshot(self) -> dict[str, Any]:
        candidate_files = {}
        for name in self.world.candidate_files:
            content = (self.world.candidate_root / name).read_text(encoding="utf-8")
            candidate_files[name] = {
                "content": content,
                "sha256": sha256_bytes(content.encode("utf-8")),
            }
        return {
            "candidate_files": candidate_files,
            "candidate_sha256": self.world.candidate_sha256,
            "candidate_version": self.world.candidate_version,
            "last_check_projection": self.world.last_check_projection,
            "next_result_index": self.next_result_index,
            "phase": self.world.phase,
            "schema": "trellis-domain-checkpoint-v0",
            "submitted": self.world.submitted,
            "version_index": self.world.version_index,
        }

    @classmethod
    def from_snapshot(
        cls,
        *,
        spec: TrellisRuntimeSpec,
        trajectory_root: Path,
        snapshot: Mapping[str, Any],
        count_text: Callable[[str], int] | None = None,
    ) -> "TrellisDomainAdapter":
        if snapshot.get("schema") != "trellis-domain-checkpoint-v0":
            raise ValueError("unsupported Trellis domain checkpoint schema")
        adapter = cls(
            spec=spec,
            trajectory_root=trajectory_root,
            count_text=count_text,
        )
        candidate_files = snapshot.get("candidate_files")
        if not isinstance(candidate_files, Mapping):
            raise ValueError("Trellis checkpoint lacks candidate files")
        for name in adapter.world.candidate_files:
            row = candidate_files.get(name)
            if not isinstance(row, Mapping):
                raise ValueError(f"Trellis checkpoint lacks candidate file: {name}")
            content = row.get("content")
            if not isinstance(content, str):
                raise ValueError(f"Trellis checkpoint candidate is not text: {name}")
            if sha256_bytes(content.encode("utf-8")) != row.get("sha256"):
                raise ValueError(f"Trellis checkpoint candidate hash mismatch: {name}")
            (adapter.world.candidate_root / name).write_text(
                content,
                encoding="utf-8",
                newline="",
            )
        adapter.world.version_index = int(snapshot["version_index"])
        adapter.world.phase = str(snapshot["phase"])
        adapter.world.submitted = bool(snapshot["submitted"])
        last_check = snapshot.get("last_check_projection")
        if last_check is not None and not isinstance(last_check, Mapping):
            raise ValueError("Trellis checkpoint check projection must be an object")
        adapter.world.last_check_projection = (
            None if last_check is None else dict(last_check)
        )
        adapter.next_result_index = int(snapshot["next_result_index"])
        if adapter.world.candidate_sha256 != snapshot.get("candidate_sha256"):
            raise ValueError("Trellis checkpoint candidate identity mismatch")
        if adapter.world.candidate_version != snapshot.get("candidate_version"):
            raise ValueError("Trellis checkpoint candidate version mismatch")
        return adapter


def initial_trellis_kernel(adapter: TrellisDomainAdapter) -> HostKernel:
    task = adapter.spec.paths.task_root
    messages = (
        ("system", (task / "SYSTEM.md").read_text(encoding="utf-8")),
        ("user", (task / "TASK.md").read_text(encoding="utf-8")),
        (
            "user",
            (task / "ACTIONS.md").read_text(encoding="utf-8")
            + "\n\n# Common pre-fork action notice\n"
            + "No semantic-maintenance output is present during pressure screening. "
            + "Both future configurations share this ordinary action surface and exact task work.\n\n"
            + "# Exact source catalog\n"
            + adapter.world.source_catalog_for_actor(),
        ),
    )
    kernel = HostKernel()
    for index, (role, content) in enumerate(messages):
        kernel = kernel.append_transcript(
            TranscriptEntry(
                entry_id=f"TRELLIS-BASE-{index:03d}",
                role=role,
                content=content,
            )
        )
    candidate = adapter.current_candidate_state()
    kernel = kernel.set_state_object(candidate)
    kernel = kernel.append_transcript(
        TranscriptEntry(
            entry_id="TRELLIS-BASE-003",
            role="user",
            content=candidate.exact_content,
            state_slot_id="current_candidate",
            entry_kind="exact_state_slot",
        )
    )
    return kernel


def build_trellis_host(
    *,
    repository_root: Path,
    trajectory_root: Path,
    count_messages: CountMessages,
    count_text: Callable[[str], int] | None = None,
) -> tuple[HostRunner, TrellisDomainAdapter, HostKernel]:
    spec = trellis_spec(repository_root)
    adapter = TrellisDomainAdapter(
        spec=spec,
        trajectory_root=trajectory_root,
        count_text=count_text,
    )
    composer = PacketComposer()
    host = HostRunner(
        configuration=spec.configuration,
        composer=composer,
        capacity=CapacityManager(
            composer=composer,
            count_messages=count_messages,
            prompt_limit=spec.configuration.prompt_limit,
        ),
        checkpoint=CheckpointController(spec.configuration),
        payload_builder=adapter.payload,
    )
    return host, adapter, initial_trellis_kernel(adapter)
