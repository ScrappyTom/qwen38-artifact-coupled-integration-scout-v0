# Trellis E97 verification-lifecycle scout — Stage 0

Date: 2026-08-29

## Outcome

The donor-derived live scout is implemented and qualified offline. No GPU or live model call was made.

This is the first frozen route that combines the currently earned lifecycle in one post-construction system:

```text
sealed E96 treatment state
        ↓ explicit verified migration
E97 applied action/effect compaction
        ↓
exact pending effect + exact current candidate
        ↓
finish incremental construction
        ↓
candidate-bound compact check
        ↓
bounded section repair(s)
        ↓
current recheck
        ↓
submission proposal or explicit incomplete state
```

It is descriptive and donor-derived. A positive result will require fresh-world transfer.

## Exact donor and migration

The frozen donor is the E96 V1 checkpoint:

- checkpoint SHA-256: `1be26e7d366f4c6f14c1f5975cb70c317768b0702fd36a53b1cc1f224546b955`;
- candidate SHA-256: `d133a537f9aef2b3635359316743f39196095c0be3dc6a4b5c86444cdc8a52d9`;
- inherited provider attempts: 29;
- inherited serialized tokens: 350,510;
- frozen terminal: `capacity_blocked`.

The old checkpoint cannot be directly resumed under the E97 execution manifest. The new migration therefore:

1. verifies the checkpoint's self-hash, configuration, domain state, candidate, counters, and sealed parent run;
2. imports the exact event prefix before the terminal event;
3. preserves the excluded terminal event and its hash in a migration receipt;
4. applies E97 without changing source, candidate, or semantic content;
5. creates a new checkpoint under the new manifest whose parent is the exact donor checkpoint.

This is not a historical replay claim. The old run remains sealed and unchanged.

## Frozen readiness

Before any future model behavior, the exact donor candidate is frozen as `not_ready`:

- 904 words against 1,200–1,650;
- the sixth required section is absent;
- decision citations cover eight rather than ten sources;
- each of T01 through T08 has at least one missing required relationship.

The exact criterion set is in `TRELLIS_E97_DONOR_READINESS_ADJUDICATION.json`. It is evaluator governance, not actor-visible advice.

## Mechanical activation

E97 externalizes only delivered `RESULT-013` through `RESULT-017` and their bound mutation actions. Pending `RESULT-018` and its action remain exact. The offline next packet is 19,116 tokens against a 20,992-token prompt allowance.

The first future completed request must include `RESULT-018` and exact exposures of:

- `current_candidate`;
- `current_candidate_effect`;
- the existing temporary provenance scaffold.

Packet fit is an apparatus gate, not a success outcome.

## Bounded verification projection

Provider-free qualification exposed a duplicate-state problem: the generic check result and the current-verification slot each carried the evaluator's verbose blocking strings. After one admitted repair, that duplicated diagnostic prevented the action/effect pair from entering another call.

The frozen scout now uses the intended bounded verification layer:

- raw evaluator stdout and stderr remain exact in external custody;
- the actor-visible projection is bound to the evaluated candidate;
- it contains failed criterion IDs, short descriptions, frozen expectations, readiness status, and a raw-result handle;
- it excludes volatile data and does no semantic repair;
- after a candidate change the same projection is explicitly stale rather than silently current.

This is a representation of exact evaluator findings, not a progress note or model-authored readiness state.

## Provider-free lifecycle result

The scripted qualification crossed one exact checkpoint/resume boundary and completed in eleven additional actor calls with zero maintenance calls:

1. deliver pending effect and add the missing sixth section;
2. enter verification;
3. run a current failing check;
4. repair six exact bound sections incrementally;
5. run a current passing recheck;
6. submit only after that recheck.

The initial check was negative, the repair changed the candidate, the final evaluator passed, and the terminal disposition was `completed`. The fixture proves reachability and transport only; it says nothing about what Qwen will choose.

The qualification also preserved a real limitation. A repair action and its pending effect must fit together once. E97 can compact an applied pair only after its effect has crossed a later completed call. The scout therefore keeps section-sized repair affordances and does not raise the response limit or permit hidden host repairs.

## Live stop rules

- one model configuration;
- at most 18 additional actor calls;
- at most one additional maintenance call;
- at most 19 additional provider calls;
- at most 450,000 additional serialized tokens;
- one attempt per call and zero retries;
- mandatory pause after at most six additional actor calls;
- no automatic continuation;
- live server tokenization is operationally authoritative for the exact frozen packet and must remain within 20,992 tokens.

The first live tranche will stop at the first six-call checkpoint or any earlier terminal state. Continuation requires transcript review and separate authorization.

## Interpretation rule

A positive result would show that the integrated donor configuration can use E97-created space to cross effect uptake into verification and repair. It would not isolate the scaffold, prove general architecture value, or count as transfer.

A negative result will be interpreted from its first new qualitative failure boundary: orientation after compaction, evaluator use, repair transport, currentness, recurrence, or closure judgment. It will not automatically trigger receipt or prompt tuning.
