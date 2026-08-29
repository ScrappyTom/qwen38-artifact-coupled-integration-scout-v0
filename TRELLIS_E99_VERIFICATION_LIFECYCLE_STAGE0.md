# Trellis E99 repaired verification-lifecycle scout — Stage 0

Date: 2026-08-29

## Outcome

The repaired donor-derived route is fully qualified offline. No GPU, live
tokenizer, or live model call was used.

It starts from the original sealed E96 donor boundary, not from the sealed E98
failure. The experimental lifecycle is unchanged except for two prospective
apparatus repairs demanded by E98:

```text
construction action contract
        ↓ actor chooses begin_verification
exact verification action contract becomes current
        ↓
run current candidate-bound check
        ↓
bounded repair → effect uptake → current recheck → closure decision

unaccepted provider response
        ↓ no action/world transition admitted
exact raw response retained in custody and event history
        +
compact hash-bound receipt remains model-facing
```

## Interface repair

At verification entry, the host adds a replaceable exact
`current_action_contract` slot. It explicitly supersedes the construction
contract and explains `run_check`, bound section repair, changed-candidate
effect uptake, recheck, and submission discipline. The JSON response schema
continues to enforce phase-valid syntax.

The provider-free actor fixture now refuses each scripted action unless the
action appears in both:

1. the request's response schema;
2. the natural-language action contract visible in the request messages.

This closes the seam that the original Stage 0 bypassed.

## Rejected-response repair

Responses with unaccepted finish reasons remain exact in provider custody and
the append-only event log. Because they produce no admitted action or world
transition, the projected assistant transcript entry becomes a bounded receipt
containing the exact response hash, finish reason, rejection-result ID, and
history handle. The host does not parse, summarize, repair, or retry the body.

The exact sealed E98 responses from calls 19–22 were replayed against the
repaired host. The two 4,096-token rejected bodies produced two compact
receipts, neither raw body remained model-facing, and the prospective next
packet measured 16,335 tokens against the 20,992-token limit. Under the old
projection it measured 23,811 and stopped.

## Complete provider-free lifecycle

The prospective route also repeated the full intended lifecycle:

- exact original donor migration at 19,116 offline prompt tokens;
- pending `RESULT-018` delivery;
- missing-section construction;
- verification transition;
- current failing check;
- six candidate-bound section repairs;
- current passing recheck;
- submission proposal;
- exact checkpoint/resume;
- terminal `completed`.

It used eleven actor calls, zero maintenance calls, and 214,965 additional
serialized tokens. The fixture proves mechanical reachability and transport,
not Qwen utility. The independent task evaluation passed its frozen substantive
criteria; its generic readiness field remains `not_adjudicated`, so live
readiness is never inferred from fixture completion alone.

## Live contract

- run ID: `2026-08-29-trellis-e99-verification-lifecycle-scout-v1`;
- configuration: `V1_E97_REPAIRED_DONOR_DERIVED_LIFECYCLE`;
- at most 18 additional actor calls;
- at most one additional maintenance call;
- at most 19 additional provider calls;
- at most 450,000 additional serialized tokens;
- one attempt per call;
- zero retries;
- mandatory review after at most six additional actor calls;
- no automatic continuation.

The first live tranche ends at the six-call review or any earlier terminal.
The sealed E98 run is never resumed. No GPU/provider call is authorized by this
Stage 0 result.

## Interpretation

A positive result would show that the repaired integrated system can cross the
post-construction boundary into real check use, repair, recheck, and an
appropriate closure decision. It would remain donor-derived and require
fresh-world transfer.

A negative result must be classified at the first new systems boundary. It
does not automatically reopen interface, receipt, scaffold, or prompt tuning.
