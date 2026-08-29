# Trellis bounded candidate causal-history offline result

Date: 2026-08-29

## Outcome

The future-only host lifecycle is implemented and passes its focused offline
qualification. It separates three facts that the prior host had bundled:

- a mutation action/effect exists exactly in external chronology;
- the effect crossed a completed model call;
- the current candidate mechanically contains the effect.

Only after all three are proven may the model-facing historical action/effect
pair become compact receipts.

## Exact E96 replay

The sealed V1 checkpoint contained six candidate effects. `RESULT-013` through
`RESULT-017` were delivered-resident; `RESULT-018` was pending. The exact
before/after hashes form one linear chain ending at the current candidate.

The future lifecycle:

- externalized only `RESULT-013` through `RESULT-017`;
- compacted their five bound assistant mutation actions;
- retained pending `RESULT-018` and its action exactly;
- preserved every exact effect hash;
- exposed `RESULT-018` in a replaceable current-effect slot with
  `semantic_uptake: not_inferred_from_delivery`; and
- reduced the exact offline next packet from 21,023 to 19,116 tokens against a
  20,992-token allowance.

The historical result remains 21,041 live tokens and `capacity_blocked`; this
offline successor does not regrade sealed behavior.

Because the frozen Trellis execution manifest hashes the core host files, the
new head correctly refuses to hydrate the old checkpoint as though it were the
old execution package. Exact historical continuation remains bound to its
recorded result commit. The offline donor audit instead replays the immutable
event prefix without claiming manifest identity, and the new lifecycle is
qualified under the new code and tests.

## What the replay newly exposed

The generic source receipt was larger than these small effect bodies, so an
effect-specific receipt was necessary. More importantly, mutation action text
could duplicate large parts of the exact artifact. Bounding effect bodies alone
was therefore insufficient; the exact causal action and effect must share one
lifecycle.

There is still a distinct one-call transport limit. A newly emitted complete
document and its pending effect must fit at least once before either can be
compacted. The lifecycle makes applied history bounded; it does not make an
oversized new response admissible. Incremental mutations remain the safer
action geometry.

## Provider-free lifecycle

A fresh Trellis fixture exercised exact ledger mutation, full decision
mutation, delivery, lifecycle compaction, verification transition, current
check, targeted repair, current recheck, and submission. All applied candidate
effects ended delivered-external with exact custody preserved. This is
apparatus evidence only; the provider was scripted and no behavioral utility
claim follows.

## Disposition

- exact external custody: preserved;
- pending-effect protection: passed;
- causal action/effect compaction: passed;
- current-effect projection: passed;
- exact reopen and checkpoint replay: passed;
- provider-free writable lifecycle: passed;
- focused lifecycle tests: 5 passed;
- full repository regression: 303 passed in 422.95 seconds;
- Ruff and mypy: passed;
- live actor utility: untested;
- GPU/provider calls: zero.

A live successor would require a separately frozen execution package and new
explicit authorization. It should use incremental mutation affordances and a
review checkpoint, not silently rerun E96 with a complete-document script.
