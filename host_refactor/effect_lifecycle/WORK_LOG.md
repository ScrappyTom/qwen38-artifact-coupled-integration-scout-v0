# Candidate-effect lifecycle work log

## 2026-08-29 — audit and cut line

E96 stopped with five delivered-resident and one pending candidate-effect
results. Every effect was non-relief-eligible, while `current_candidate`
already contained the cumulative six-mutation result. The next packet was 49
tokens over the prompt allowance and no ordinary relief candidate remained.

Decision: do not make candidate effects generally relief-eligible. Add a
separate lifecycle transition guarded by exact candidate lineage and completed
delivery. Keep pending effects exact, preserve all historical bytes externally,
and expose a replaceable mechanical current-effect projection. Historical E96
execution remains sealed and unchanged.

## 2026-08-29 — first exact replay and causal-pair correction

The first replay showed that the generic source receipt was larger than a
small candidate-effect body. A candidate-effect-specific receipt corrected
that carrier mismatch. The same replay then exposed a larger duplication: each
mutation action could contain substantial artifact text already represented by
the exact current candidate. The guarded transition now projects both the
delivered effect and its exact causal assistant action as compact receipts.
Original bytes remain in the append-only event ledger; effects remain exactly
reopenable.

At the pre-terminal E96 V1 state, the policy externalizes only delivered
`RESULT-013` through `RESULT-017`, leaves pending `RESULT-018` exact, and lowers
the offline next-packet projection from 21,023 to 19,116 tokens. The historical
live report's 21,041 count remains unchanged and is not regraded.

The replay also preserves a real limit: a new complete-document mutation may
itself be too large to coexist with its pending effect for the next call. This
policy bounds applied causal history; it does not solve pre-delivery response
transport or justify global artifact replacement.

The core file changes intentionally alter the Trellis execution-manifest hash.
Accordingly, current-head hydration of the old E94 checkpoint fails closed on
configuration mismatch. Historical exact continuation remains available at
its sealed result commit; the new path does not borrow that old manifest.

## 2026-08-29 — offline qualification complete

Five focused tests pass: published audit reproduction, authentic E96 capacity
recovery, adversarial failure/lineage/action binding, exact reopen/checkpoint
round trip, and a provider-free writable lifecycle through current recheck and
closure. Ruff passes, mypy reports no issues in sixteen host modules, and all
303 repository tests pass in 422.95 seconds. No GPU or provider call occurred.

## 2026-08-30 — verification-residency reconciliation

The exact E103 pre-terminal packet reconstructed at 21,301 offline tokens; the
historical live-authoritative count remains 21,318. The packet duplicated the
latest complete check projection in `RESULT-024` and the replaceable
`current_verification_frame`, while older `RESULT-021` also remained resident.

The new lifecycle requires exact result, evaluated-candidate, result-content,
and check-projection bindings in the verification slot before a delivered
check can become an exact receipt. Applied to E103, it turns over only
`RESULT-021` and `RESULT-024`, leaves pending `RESULT-026` exact, and projects a
20,548-token packet. Reopen remains exact.

The historical donor was not fabricated: version-007 candidate bytes are
uncorrupted, but there is no sealed checkpoint at that state; the next sealed
checkpoint contains the version-008 heading corruption. A separate
provider-free full lifecycle reached passing recheck and submission with the
new turnover policy. Live behavior remains untested. See
`E104_VERIFICATION_RESIDENCY_RECONCILIATION.md`.

Four focused verification-residency tests and the complete 328-test repository
suite pass. Ruff passes. Targeted mypy still reaches two pre-existing errors in
`reactive_runtime/records.py` and additional pre-existing `tools/live_common.py`
errors when the audit tool's full import graph is included; no new core-module
type error was identified. No GPU or provider call occurred.
