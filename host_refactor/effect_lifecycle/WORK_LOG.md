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
