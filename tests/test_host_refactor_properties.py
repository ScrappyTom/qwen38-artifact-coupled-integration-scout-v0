from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from host_refactor.kernel import HostKernel
from host_refactor.model import DeliveryState, ExactResult
from host_refactor.packet import PacketComposer


def exact_result(result_id: str, payload: str, version: str, span: str) -> ExactResult:
    return ExactResult(
        result_id=result_id,
        result_kind="source_observation",
        object_id=span,
        object_version=version,
        exact_content=f"{result_id}\n--- exact result body ---\n{payload}",
        payload_content=payload,
        acquired_call=1,
        candidate_sha256_after="candidate",
        span_key=span,
    )


@settings(max_examples=40)
@given(
    payload=st.text(min_size=1, max_size=80),
    cycles=st.integers(min_value=0, max_value=5),
)
def test_delivery_externalization_reopen_cycles_are_replay_stable(
    payload: str, cycles: int
) -> None:
    result = exact_result("RESULT-001", payload, "v1", "SOURCE-A:1-20")
    kernel = (
        HostKernel()
        .acquire(result)
        .schedule(
            result.result_id,
            call_index=1,
            transcript_entry_id="RESULT-ENTRY-0",
        )
    )
    kernel = kernel.complete_invocation(
        call_index=1,
        included_result_ids=(result.result_id,),
        request_sha256="request-1",
        response_sha256="response-1",
    )
    for index in range(cycles):
        kernel = kernel.externalize(result.result_id, reason="property")
        kernel = kernel.request_reopen(
            result.result_id,
            call_index=index + 2,
            transcript_entry_id=f"RESULT-ENTRY-{index + 1}",
        )
        kernel = kernel.complete_invocation(
            call_index=index + 2,
            included_result_ids=(result.result_id,),
            request_sha256=f"request-{index + 2}",
            response_sha256=f"response-{index + 2}",
        )
    hydrated = HostKernel.from_dict(kernel.as_dict())
    assert hydrated.as_dict() == kernel.as_dict()
    assert (
        hydrated.project().results[result.result_id].delivery_state
        is DeliveryState.DELIVERED_RESIDENT
    )
    contents = [row["content"] for row in PacketComposer().compose(hydrated).messages]
    assert contents.count(result.exact_content) == 1


@settings(max_examples=50)
@given(
    payload=st.text(min_size=1, max_size=80),
    version=st.text(min_size=1, max_size=12),
    span=st.text(min_size=1, max_size=20),
)
def test_result_id_does_not_change_canonical_body_identity(
    payload: str, version: str, span: str
) -> None:
    first = exact_result("RESULT-001", payload, version, span)
    second = exact_result("RESULT-999", payload, version, span)
    assert first.body_identity == second.body_identity
