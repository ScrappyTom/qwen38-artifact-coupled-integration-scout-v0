from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from reactive_runtime.actions import action_json_schema, parse_action
from reactive_runtime.configuration import artifact_centered_actor_actions
from reactive_runtime.keystone_world import KeystoneWorld
from reactive_runtime.canonical import canonical_json_bytes, sha256_bytes, sha256_file
from reactive_runtime.records import ResultLedger, ResultRecord
from reactive_runtime.world import ActionRejected
from tools.live_common import provider_payload

from host_refactor.capacity import CapacityManager, CountMessages
from host_refactor.checkpoint import CheckpointController
from host_refactor.kernel import HostKernel
from host_refactor.model import (
    DeliveryState,
    ExactStateObject,
    ProjectedHostState,
    RunConfiguration,
    TerminalCode,
    TranscriptEntry,
)
from host_refactor.packet import ModelPacket, PacketComposer
from host_refactor.runner import ActionRejection, DomainOutcome, HostRunner
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
    execution_manifest: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.actor_max_tokens != self.configuration.response_reserve:
            raise ValueError(
                "Trellis provider maximum differs from frozen response reserve"
            )


def trellis_execution_manifest(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    task_root = root / "task_trellis"
    declared = [
        root / "TRELLIS_PRESSURE_SCREEN_CONTRACT.json",
        root / "TRELLIS_MODEL_PROFILE_LOCK.json",
        task_root / "ACTIONS.md",
        task_root / "EVALUATOR.json",
        task_root / "SOURCE_CATALOG.json",
        task_root / "SYSTEM.md",
        task_root / "TASK.md",
        task_root / "TASK_SOURCE_LOCK.json",
        task_root / "VERIFICATION_ACTIONS.md",
        task_root / "WORLD_SPEC.json",
        task_root / "evaluator" / "evaluate.py",
        root / "host_refactor" / "binding.py",
        root / "host_refactor" / "capacity.py",
        root / "host_refactor" / "checkpoint.py",
        root / "host_refactor" / "kernel.py",
        root / "host_refactor" / "model.py",
        root / "host_refactor" / "packet.py",
        root / "host_refactor" / "provider.py",
        root / "host_refactor" / "runner.py",
        root / "host_refactor" / "trellis_adapter.py",
        root / "reactive_runtime" / "actions.py",
        root / "reactive_runtime" / "keystone_world.py",
        root / "reactive_runtime" / "world.py",
        root / "tools" / "live_common.py",
    ]
    files = {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(declared)
    }
    payload = {
        "files": files,
        "payload_builder": "TrellisDomainAdapter.payload:v1",
        "schema": "trellis-host-execution-manifest-v1",
    }
    return {
        **payload,
        "execution_manifest_sha256": sha256_bytes(canonical_json_bytes(payload)),
    }


def trellis_spec(repository_root: Path) -> TrellisRuntimeSpec:
    root = repository_root.resolve()
    execution_manifest = trellis_execution_manifest(root)
    return TrellisRuntimeSpec(
        configuration=RunConfiguration(
            run_id="trellis-host-refactor-v0-not-authorized",
            task_id="trellis-heat-continuity-decision-v0",
            seed=884_219,
            context_window=25_088,
            response_reserve=4_096,
            execution_manifest_sha256=str(
                execution_manifest["execution_manifest_sha256"]
            ),
            accepted_finish_reasons=("stop",),
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
        execution_manifest=execution_manifest,
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

    def current_action_contract_state(self) -> ExactStateObject:
        if self.world.phase != "verification":
            raise ValueError("current action-contract state is verification-only")
        contract = (
            self.spec.paths.task_root / "VERIFICATION_ACTIONS.md"
        ).read_text(encoding="utf-8")
        content = (
            "# Current phase action contract\n\n"
            "PHASE: verification\n\n"
            "This contract supersedes the earlier construction action contract. "
            "Run a current candidate-bound check before repair. Repair only the "
            "failed criteria through bounded section replacement, then run a new "
            "check against the changed candidate before considering submission.\n\n"
            + contract
        )
        return ExactStateObject(
            slot_id="current_action_contract",
            object_id=f"action-contract:{self.spec.configuration.task_id}",
            object_version="verification-v1",
            exact_content=content,
            metadata={
                "phase": "verification",
                "supersedes": "task_trellis/ACTIONS.md",
            },
        )

    def handle(
        self, content: str, *, call_index: int, kernel: HostKernel
    ) -> DomainOutcome:
        try:
            action = parse_action(
                content,
                self.allowed_actions,
                decision_headings=self.world.decision_headings,
            )
        except ValueError as exc:
            return DomainOutcome(
                rejection=ActionRejection(
                    code="invalid_model_output",
                    message=str(exc),
                )
            )
        if action.get("action") == "reopen_exact":
            result_id = str(action["result_id"])
            row = kernel.project().results.get(result_id)
            if row is None or row.delivery_state is not DeliveryState.DELIVERED_EXTERNAL:
                return DomainOutcome(
                    rejection=ActionRejection(
                        code="result_not_reopenable",
                        message=f"result is not delivered-external: {result_id}",
                        attempted_action=action,
                    )
                )
            return DomainOutcome(action=action, reopen_result_id=result_id)
        result_id = f"RESULT-{self.next_result_index:03d}"
        self.next_result_index += 1
        try:
            execution = self.world.execute(
                action,
                result_id=result_id,
                ledger=_legacy_ledger(kernel),
            )
        except ActionRejected as exc:
            return DomainOutcome(
                action=action,
                rejection=ActionRejection(
                    code=exc.code,
                    message=exc.message,
                    attempted_action=action,
                ),
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
        state_updates: list[ExactStateObject] = []
        if not (
            current is not None
            and current.object_version == candidate_state.object_version
            and current.content_sha256 == candidate_state.content_sha256
        ):
            state_updates.append(candidate_state)
        if self.world.phase == "verification":
            action_contract = self.current_action_contract_state()
            current_contract = kernel.project().state_slots.get(
                action_contract.slot_id
            )
            if (
                current_contract is None
                or current_contract.as_dict() != action_contract.as_dict()
            ):
                state_updates.append(action_contract)
        return DomainOutcome(
            result=exact,
            state_updates=tuple(state_updates),
            terminal=terminal,
            action=action,
        )

    def payload(
        self,
        packet: ModelPacket,
        configuration: RunConfiguration,
        state: ProjectedHostState,
    ) -> Mapping[str, Any]:
        external_ids = tuple(
            result_id
            for result_id, row in state.results.items()
            if row.delivery_state is DeliveryState.DELIVERED_EXTERNAL
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
