# Trellis refactored-host interaction continuation result

Date: 2026-08-29

Freeze commit:
`18e17806e906d57943ab9b7461def708084d69b1`

Run ID:
`2026-08-29-trellis-refactored-interaction-continuation-v0`

Disposition: valid sealed whole-system result. V0 reached checkpoint two; V1
made substantial exact artifact progress and then stopped at a real
unrelievable capacity boundary. Neither achieved useful completion.

## Literal result

The continuation stayed within every authorization limit:

| Measure | Authorized additional | Actual additional |
|---|---:|---:|
| Actor calls | 24 | 18 |
| Maintenance calls | 6 | 5 |
| Provider calls | 30 | 23 |
| Serialized tokens | 520,028 | 383,176 |
| Attempts per call | 1 | 1 |
| Retries | 0 | 0 |

V0 used twelve additional actor calls and 238,065 additional serialized tokens.
V1 used six additional actor calls, five maintenance calls, eleven provider
calls, and 145,111 additional serialized tokens. Both runtimes passed their
gates and were released; the complete run tree seal verifies.

The launcher preserved the exact V1 checkpoint and evaluator output, then
raised `RuntimeError` because its success allowlist contained only
`checkpoint_pause` and `completed`, not the host's legitimate
`capacity_blocked` terminal. The resulting `RUN_FAILURE.json` is a wrapper
classification defect after the system stop, not a missing or retried model
call. It is preserved rather than normalized.

## V0: exact availability became full catalog replay

Call 13 delivered the pending final LINEAGE/REVIEW result. Qwen then made the
same twelve source-range requests as calls 1–12, in the same order:

```text
COUNCIL/CLIMATE both halves
→ GRID/WATER both halves
→ CLINIC/SHELTER both halves
→ TRANSIT/COMMS both halves
→ SUPPLY/LABOR both halves
→ LINEAGE/REVIEW both halves
```

These were explicit actor demands, not host duplication. Exact body
deduplication remained active, and old results were reopenable, but Qwen chose
new `read_batch` actions rather than `reopen_exact` or artifact work. V0 reached
the second checkpoint at 24 cumulative actor calls with 21 results external,
two resident, one pending, zero candidate transitions, and the initial
not-ready artifact unchanged.

This establishes a strong local recurrence phenotype:

> Exact custody and knowledge that the complete catalog had been traversed did
> not preserve behavioral consumption across the checkpoint. The actor
> restarted acquisition from the beginning.

## V1: semantic and exact work state changed the action policy

V1 diverged on its first post-catalog decision. After `RESULT-012` crossed the
model boundary, Qwen replaced the exact evidence ledger with a 472-word,
twelve-source requirement matrix. It then made five consecutive admitted
section mutations:

1. Authority, scope, and operating states;
2. Heat triggers and geographic staging;
3. Power, water, and cooling continuity;
4. Clinical, shelter, and accessibility operations;
5. Transit, communications, logistics, and staffing.

The exact candidate changed six times. The decision reached 904 words and cited
eight sources. No raw source was reopened or reread. The sixth required section,
verification, repair, recheck, and closure were not reached.

This is the clearest Trellis interaction signal so far. Under the complete V1
configuration, previously transient evidence became exact cumulative task work.
Under V0, the same post-catalog decision budget became a second acquisition
pass. The result belongs to the whole evolving configuration—anchored semantic
residue, its recent maintenance exposure, the exact evidence ledger,
incremental section actions, exact artifact effects, and different prompt
history—not to the register in isolation.

## The construction carried the scaffold's selection losses

The behavioral benefit did not produce a ready artifact. The actor-invisible
evaluator bound the final candidate hash exactly and found:

- exact ledger heading and all twelve ledger source IDs: pass;
- decision title: pass;
- five of six ordered sections present;
- 904 words against a required 1,200–1,650;
- eight distinct decision sources;
- all eight substantive requirement groups incomplete;
- no prohibited authority, capacity, coverage, duration, labor, or readiness
  reversal;
- closure readiness: `not_ready`.

The qualitative failure follows the register lifecycle observed at checkpoint
one. Later source chunks had replaced governing facts with tail-table records.
The ledger and sections then emphasized exact but poorly selected values such
as superseded 41.8-degree climate evidence, 29.8 MW, 39.8 psi, 72.4 percent
occupancy, 2,101.4 seats, and later route/channel rows. They omitted the task's
critical relations: 31.4 versus 30.0 for two windows and 32.0 expanded; 31.0
installed versus 24.5 usable MW; 38 versus 35 psi at every node; 71 versus 82
percent occupancy plus twelve beds; 2,400 versus 1,760 seats; transit counts and
latencies; supply-duration and labor-rest distinctions; and current T9 versus
historical T8 recheck requirements.

The semantic scaffold therefore had both positive and negative downstream
effects:

```text
grounded bounded residue
→ early exact ledger and section construction
→ no catalog replay

same-source replacement loss
→ available residue overweights later table rows
→ exact artifact capitalizes incomplete requirement relations
```

This repeats the broader cross-world warning: coupling semantic state into exact
task work can turn interpretation into durable progress, but it can also turn
semantic selection error into durable artifact error.

## The new terminal bottleneck: append-only candidate effects

V1 did not stop because its ordinary source bodies were still too large. By the
terminal boundary, all twelve source results were external. It stopped because
each admitted artifact mutation produced an exact candidate-effect result that
was marked non-relief-eligible while the complete current candidate was also
resident in a replaceable state slot.

At call 19 the model-facing state contained:

- five delivered-resident candidate effects, `RESULT-013` through
  `RESULT-017`;
- pending candidate effect `RESULT-018`;
- the current exact candidate containing all six mutations;
- the active fourteen-claim semantic scaffold;
- ordinary action chronology and exact receipts.

The next packet required 21,041 prompt tokens against the 20,992-token prompt
allowance. No strictly positive eligible result remained, so the host stopped
before provider I/O. Five effect bodies remained resident and the sixth remained
pending.

This is failure migration:

```text
semantic scaffold resolves acquisition recurrence
→ exact incremental construction succeeds
→ each construction effect accumulates append-only
→ effect chronology duplicates information represented by current candidate
→ verification becomes unreachable
```

The host was correct under the frozen policy. The policy's non-relief-eligible
candidate-effect lifecycle is now the active systems defect.

## Economic interpretation

Cumulatively, V0 used 412,638 serialized tokens over 24 actor calls and produced
no artifact progress. V1 used 350,510 tokens over 18 actor plus eleven
maintenance calls and produced a substantial but incomplete artifact. V1 was
62,128 tokens cheaper at its earlier terminal boundary while producing more
work.

That difference is descriptive, not a clean efficiency estimate. The arms
ended in different states, V1 had six fewer actor calls, and neither completed.
The supported economic conclusion is narrower: under the frozen action and
context geometry, V1 converted fewer total serialized tokens into much more
admitted work, but its semantic losses and effect-residency costs prevented
useful completion.

## Supported disposition

Supported locally:

- V0 exhibits complete post-catalog reacquisition recurrence;
- V1 changes immediately from acquisition to admitted cumulative construction;
- the full V1 configuration has strong behavioral and artifact-production
  leverage;
- source-slot semantic replacement losses propagate into exact task work;
- exact artifact state can carry cumulative cognition without raw source
  reopen;
- append-only, non-relief-eligible candidate effects can make verification
  unreachable even while a current exact candidate is present;
- the refactored host stopped safely and preserved exact custody.

Not supported:

- useful completion;
- semantic scaffold fidelity sufficient for the full task;
- verification, repair, current recheck, or correct closure;
- isolated register causality;
- architecture promotion.

The exact route is closed at this terminal boundary. A future experiment should
not add more calls to this checkpoint. The next design question is how to make
candidate-effect uptake exact and auditable without retaining every mutation
effect body alongside the full current artifact.
