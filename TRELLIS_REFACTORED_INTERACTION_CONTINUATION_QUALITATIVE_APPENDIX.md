# Trellis continuation qualitative transcript appendix

Date: 2026-08-29

Run ID:
`2026-08-29-trellis-refactored-interaction-continuation-v0`

This appendix interprets literal sealed actor and maintenance turns. Alternative
explanations remain explicit. It does not expose hidden model reasoning.

## Starting state

Both arms resumed after twelve identical catalog reads. `RESULT-001` through
`RESULT-011` had crossed completed model calls; `RESULT-012` contained the final
LINEAGE/REVIEW ranges but remained pending. Both exact artifacts were initial
placeholders.

V0 had no semantic state. V1 had a ten-claim grounded register covering eight
sources, but same-source replacement had already removed several important
early facts. V1 had externalized two more exact results than V0 and paid six
maintenance calls.

## V0 calls 13–24

| Call | Newly visible / resident condition | Actor action | Artifact consequence | Qualitative reading |
|---:|---|---|---|---|
| 13 | Pending final LINEAGE/REVIEW result crosses the actor boundary | Read COUNCIL/CLIMATE 1–60 | None | Complete catalog delivery does not trigger construction; demand resets to the first pair. |
| 14 | Reacquired first halves visible | Read COUNCIL/CLIMATE 61–94 | None | Actor completes the familiar pair exactly as in the first pass. |
| 15 | COUNCIL/CLIMATE complete again | Read GRID/WATER 1–60 | None | Catalog-order recurrence continues. |
| 16 | GRID/WATER first halves visible | Read GRID/WATER 61–94 | None | Second pair completion repeats. |
| 17 | GRID/WATER complete again | Read CLINIC/SHELTER 1–60 | None | No use of incremental artifact affordances. |
| 18 | CLINIC/SHELTER first halves visible | Read CLINIC/SHELTER 61–94 | None | The actor remains in acquisition mode. |
| 19 | Six sources reacquired | Read TRANSIT/COMMS 1–60 | None | Exact availability does not act as consumed semantic state. |
| 20 | TRANSIT/COMMS first halves visible | Read TRANSIT/COMMS 61–94 | None | Fourth pair repeats. |
| 21 | Eight sources reacquired | Read SUPPLY/LABOR 1–60 | None | No reopen action; new reads reproduce exact bodies. |
| 22 | SUPPLY/LABOR first halves visible | Read SUPPLY/LABOR 61–94 | None | Fifth pair repeats. |
| 23 | Ten sources reacquired | Read LINEAGE/REVIEW 1–60 | None | Actor reaches final pair a second time. |
| 24 | LINEAGE/REVIEW first halves visible | Read LINEAGE/REVIEW 61–94 | None; new result pending | Entire twelve-action sequence has replayed and checkpoint two fires. |

V0's recurrence is functional and nearly literal. The review reports eight
byte-identical assistant messages across the full history; the remaining
responses are semantically identical range requests with serialization
differences. The actor never selected `reopen_exact`, despite external handles,
and never wrote either artifact.

Alternative explanations include checkpoint-induced orientation loss,
catalog-order prompt salience, or a strategy of refreshing all evidence before
writing. The experiment cannot distinguish them. All imply the same system
fact: exact custody plus receipts did not preserve action-ready consumption.

## V1 maintenance and actor calls

### Before call 13

Delivering `RESULT-012` required externalizing `RESULT-008`. Maintenance call 7
replaced prior TRANSIT/COMMS claims with four later-range route/channel claims.
The actor then saw the complete catalog history, exact current artifact, exact
receipts and remaining resident bodies, and the updated scaffold.

### Actor call 13 — exact evidence ledger

Qwen used `replace_evidence_ledger`, creating a 472-word matrix that named all
twelve sources. This was the first post-catalog action and the first admitted
artifact mutation.

The ledger was broad but scaffold-shaped. It included exact tail-row values and
status labels while omitting many governing cross-source relations. It treated
some current table rows as operational requirements and retained superseded
COUNCIL/CLIMATE rows as warnings rather than reconstructing the task's actual
thresholds.

Likely demand shift: the visible scaffold and exact final evidence made
externalizing accumulated meaning into the task-native ledger more attractive
than rereading. This is an inference from the contrast, not isolated causality.

### Before actor call 14

The ledger effect became pending. To fit the next decision, the host
externalized `RESULT-009` and `RESULT-010`. Maintenance calls 8 and 9 first
added strong SUPPLY/LABOR facts, then replaced them with later-range rows. The
actor saw the ledger effect, exact current artifact, and the revised scaffold.

### Actor call 14 — authority section

Qwen added “Authority, scope, and operating states” (about 230 body words). It
correctly preserved T9's F6/G4/R8/L11/C7 lineage, distinguished mechanical
possibility from authority, kept REVIEW separate from COUNCIL authorization,
and refused self-authorized readiness. It also used later REVIEW details to
list blocking findings.

This was the strongest section because the newest exact LINEAGE/REVIEW result
and related semantic state were salient. The effect was admitted exactly.

### Actor call 15 — heat section

With no new maintenance event, Qwen added “Heat triggers and geographic
staging” (about 169 words). It centered the superseded 41.8-degree row and
general currentness rules. It omitted the required 31.4 observation, 30.0
two-window limited gate, 32.0 expanded gate, and the 0.62-versus-84-percent
distinction.

The section is safe in the sense that it does not promote superseded evidence,
but it is not sufficient task work. The earlier CLIMATE replacement loss is now
visible inside the durable artifact.

### Before actor call 16

Fitting the newest effect externalized `RESULT-011` and `RESULT-012`.
Maintenance calls 10 and 11 first added six useful LINEAGE/REVIEW claims and
then replaced them with two later status claims. At this point every source
observation was external; the model-facing system depended on the scaffold,
ledger, artifact, receipts, and candidate effects.

### Actor call 16 — power/water section

Qwen added “Power, water, and cooling continuity” (about 173 words). It used
29.8 MW and 39.8 psi tail records and REVIEW blockers, while explicitly warning
that reserve figures do not prove usable flow. It omitted all required central
numbers and duration/window relations.

This is a mixed semantic outcome: relational caution survived, but the wrong
evidence rows dominated because the source-slot scaffold had discarded the
governing rows.

### Actor call 17 — clinical/shelter section

Qwen added “Clinical, shelter, and accessibility operations” (about 169 words).
It used 72.4-percent hospital occupancy and 2,101.4 installed seats from later
rows. It maintained installed-versus-usable caution and linked open clinical
and accessibility findings, but omitted the required 71/82-percent window,
twelve staffed beds, and 2,400/1,760-seat distinction.

### Actor call 18 — transit/comms section

Qwen added “Transit, communications, logistics, and staffing” (about 154
words). This fifth section completed the domains represented by the remaining
register. It still omitted the task's required vehicle counts, median/p95
travel times, delivery uncertainty, and p95/p99 communication latency.

The fifth mutation produced pending `RESULT-018`.

### Attempted call 19 — no provider call

The next packet projected to 21,041 tokens. All twelve source results were
already external. Five candidate-effect bodies remained delivered-resident and
the sixth was pending; all six were non-relief-eligible. The complete current
candidate also remained resident. No strictly positive eligible substitution
existed, so the host stopped before provider I/O.

The sixth required section, verification transition, check, repair, recheck,
and closure never occurred.

## Cross-arm qualitative synthesis

The second tranche exposes two different continuity failures:

```text
V0
exact history + receipts + no semantic scaffold
→ complete acquisition replay
→ no work

V1
semantic scaffold + exact ledger + incremental artifact
→ immediate cumulative work
→ scaffold-selection losses enter artifact
→ append-only candidate effects exhaust capacity
```

This is a positive interaction signal and a negative completion result. V1
solved the acquisition-to-construction transition locally but moved the
bottleneck twice: first to semantic fidelity, then to effect-lifecycle capacity.

The exact artifact clearly functioned as external cognition. After raw sources
were gone, Qwen continued adding sections without reopening them. But exact
artifact persistence alone did not guarantee correct relationship recovery;
the content it accumulated reflected the quality of the semantic/evidence
state available at construction time.

The most important next design implication is host-mechanical, not a new prompt:
the runtime needs a bounded exact way to expose the latest candidate mutation
and its uptake/currentness while moving older effect bodies to external custody.
That design must preserve auditability and pending delivery without keeping
every effect next to the full current candidate.
