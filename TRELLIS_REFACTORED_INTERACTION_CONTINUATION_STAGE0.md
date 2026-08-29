# Trellis refactored-host interaction continuation Stage 0

Date: 2026-08-29

Parent result commit:
`0626259773f1411272566caa1b4a00c83e70e606`

Run ID:
`2026-08-29-trellis-refactored-interaction-continuation-v0`

Disposition: provider-free qualified; live continuation not authorized.

## Why continue unchanged

The first live checkpoint was dominated by catalog traversal. Both actors made
the same twelve bounded reads. `RESULT-012`, the final source-pair result, was
acquired only after call 12 and remains pending in both cells. Neither actor has
yet received a decision in which all twelve sources have crossed a completed
model invocation.

The treatment was real but not yet behaviorally discriminating. Six maintenance
calls cost 31,578 serialized tokens and maintained a grounded, bounded register.
The register also revealed a lifecycle weakness: a later chunk from one source
replaced earlier claims from that source, sometimes exchanging governing facts
for low-value tail rows. Changing that rule now would create a different system
and destroy the existing comparison.

The selected continuation therefore resumes the exact sealed checkpoints with
no policy, prompt, action-surface, scaffold, budget, or evaluator change. Its
purpose is to observe the first post-catalog transition:

```text
pending RESULT-012 delivered
→ actor constructs, reopens, reads again, checks, or otherwise reveals demand
→ exact candidate/effect/check state accumulates if admitted
→ mandatory second checkpoint or earlier terminal state
```

## Exact resume qualification

The continuation hydrator verifies the parent checkpoint configuration and
event hash, restores the exact Trellis candidate/world snapshot and interaction
lifecycle, and preserves cumulative provider/token and maintenance budgets.
The parent sealed tree is verified before any live runtime starts.

Provider-free regression resumes both exact live checkpoints. A scripted actor
starting at action 13 delivers `RESULT-012`, mutates the evidence ledger and
decision, enters verification, receives a candidate-bound failed check, applies
a uniquely bound section repair, receives a current passing recheck, and
submits. Both arms reach the common terminal lifecycle; V1 remains within its
six remaining maintenance calls. These are apparatus facts, not Qwen utility.
The three focused continuation tests and the full 295-test repository
regression pass; targeted Ruff and mypy checks are clean.

## Frozen additional limits

- configurations: `V0_EXACT_ARTIFACT`, then
  `V1_TEMPORARY_PROVENANCE_SCAFFOLD`;
- at most 24 additional actor calls;
- at most six additional maintenance calls;
- at most 30 additional provider calls;
- at most 520,028 additional serialized tokens;
- one attempt per call and zero retries;
- fresh model-server process per cell;
- pause at 24 cumulative completed actor calls or an earlier terminal/resource
  disposition;
- external evaluation remains actor-invisible;
- no automatic third tranche.

The limit is additional rather than cumulative accounting. Each underlying
runtime retains its original hard ceiling of 60 actor calls and 450,000
serialized tokens. The authorized delta is the exact remaining aggregate after
the first checkpoint.

## Interpretation limits

This is a whole-configuration continuation. It cannot isolate the semantic
register as the cause of any later difference. It also cannot repair the known
source-slot replacement loss. If the treatment helps, harms, or remains inert,
the result applies to the frozen configuration and lifecycle at this boundary.

No GPU/provider operation is authorized by this document.
