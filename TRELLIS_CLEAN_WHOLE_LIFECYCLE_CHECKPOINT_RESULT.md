# Trellis clean whole-lifecycle checkpoint result

Date: 2026-08-30

Frozen apparatus commit:
`fc5acada791bc53dc3562e3f3e2e0b62c1f367a0`

Run ID:
`2026-08-30-trellis-clean-whole-lifecycle-v0`

Disposition: valid sealed checkpoint pause. The first clean prospective live
tranche completed every authorized call, stopped at the mandatory review
boundary, and did not continue automatically.

## Literal result

| Measure | Authorized | Actual |
|---|---:|---:|
| Actor calls | 12 | 12 |
| Maintenance calls | 6 | 6 |
| Provider calls | 18 | 18 |
| Serialized tokens | 400,000 | 205,399 |
| Attempts per call | 1 | 1 |
| Retries | 0 | 0 |

All eighteen provider responses completed normally. There were no failed
calls, rejected actor actions, repeated assistant messages, exact reopens, or
repeat-demand events. The model server was released and the complete run tree
was sealed.

The checkpoint candidate is the exact initial nine-word stub,
`e7a12171c6523e8881fddf7cdcd0cba3e99f97ff7ef1db9770f7295a596db0ba`.
The frozen external evaluator and readiness rule correctly classify it
`not_ready`. This quality judgment describes an acquisition checkpoint, not a
claim that the complete lifecycle has failed.

## Call-by-call actor trajectory

Every actor response was a valid two-range `read_batch`. Qwen followed one
stable depth-first acquisition plan:

| Call | Newly requested exact source ranges | Prompt tokens | Visible scaffold |
|---:|---|---:|---|
| 1 | COUNCIL 1–60; CLIMATE 1–60 | 2,362 | no |
| 2 | COUNCIL 61–94; CLIMATE 61–94 | 5,546 | no |
| 3 | GRID 1–60; WATER 1–60 | 7,608 | no |
| 4 | GRID 61–94; WATER 61–94 | 10,766 | no |
| 5 | CLINIC 1–60; SHELTER 1–60 | 12,833 | no |
| 6 | CLINIC 61–94; SHELTER 61–94 | 16,106 | no |
| 7 | TRANSIT 1–60; COMMS 1–60 | 18,305 | no |
| 8 | TRANSIT 61–94; COMMS 61–94 | 20,166 | yes |
| 9 | SUPPLY 1–60; LABOR 1–60 | 20,091 | yes |
| 10 | SUPPLY 61–94; LABOR 61–94 | 19,732 | yes |
| 11 | LINEAGE 1–60; REVIEW 1–60 | 19,716 | yes |
| 12 | LINEAGE 61–94; REVIEW 61–94 | 19,934 | yes |

The last action acquired `RESULT-012`, but the result remains pending because
there was no thirteenth completed model call. The actor has therefore requested
the entire twelve-source catalog, but the final two source halves have not yet
crossed a model boundary.

This is purposeful pacing, not a loop. The checkpoint occurred exactly between
the final acquisition action and the first possible post-catalog decision.
There is no evidence yet about whether Qwen will construct, reopen, check, or
remain in acquisition after the complete catalog becomes visible.

## Pressure and exact custody

Pressure first activated before call 8. Deterministic first-fit relief then
externalized seven delivered source results:

| Relief event | Exact results externalized | Prompt after relief | Savings |
|---:|---|---:|---:|
| 1 | RESULT-001 | 18,786 | 2,615 |
| 2 | RESULT-002 | 20,726 | 1,490 |
| 3 | RESULT-003 | 20,552 | 2,609 |
| 4 | RESULT-004 | 20,404 | 1,508 |
| 5 | RESULT-005 | 19,074 | 2,710 |
| 6 | RESULT-006, RESULT-007 | 18,578 | 1,604 + 2,532 |

At the checkpoint, `RESULT-001` through `RESULT-007` are delivered and
external, `RESULT-008` through `RESULT-011` are delivered and exact-resident,
and `RESULT-012` is pending exact delivery. Every object remains exactly
custodied and reopenable. No externalized result was demanded again during
this acquisition phase.

## Semantic maintenance: safe expression, unstable selection

Six maintenance calls consumed 31,578 serialized tokens. Every call ended
normally and every proposed claim passed the frozen mechanical admission gate.
Twenty claims entered the register across time; the current bounded register
contains ten claims.

The maintenance events were:

| Maintenance | Input results | Claims admitted | Register change |
|---:|---|---:|---|
| 1 | RESULT-001 | 4 | full admission |
| 2 | RESULT-002 | 2 | full admission |
| 3 | RESULT-003 | 4 | full admission |
| 4 | RESULT-004 | 2 | full admission |
| 5 | RESULT-005 | 2 | full admission |
| 6 | RESULT-006, RESULT-007 | 6 | full admission |

The outputs were locally grounded and materially safe. They preserved such
distinctions as limited versus expanded heat thresholds, probability versus
coverage, installed versus usable power, emergency-load versus full-load
duration, node-level water gates, installed versus staffed shelter capacity,
median versus p95 transit time, and communications delivery uncertainty.

The lifecycle nevertheless reproduced the known same-source replacement
problem. Later table-row claims replaced stronger governing claims in the same
source slots:

- COUNCIL authority and closure rules were replaced by a superseded AUT-046
  record;
- CLIMATE activation thresholds were replaced by a superseded 41.8-degree
  record;
- GRID capacity and backup-duration relations were replaced by a 29.8 MW row;
- WATER node gates and reserve/flow were replaced by a 39.8 psi row;
- CLINIC's 71 percent governing observation was replaced by 72.4 percent;
- SHELTER's 2,400 installed versus 1,760 staffed-accessible distinction was
  replaced by a 2,101.4-seat row.

The final register retains useful TRANSIT and COMMS facts, but all ten current
claims are `source_reported_fact` with no relationship referents. It is a safe
but selectively weak construction scaffold.

This is important interaction evidence. The scaffold was visible from call 8
onward, yet it did not interrupt Qwen's coherent plan to finish the exact
catalog. Its immediate effect was neither construction nor disorientation.
Its downstream value and risk remain unmeasured until the pending final result
crosses a model call and task work begins.

## Information economics

The twelve actor calls used 173,165 prompt tokens and 656 completion tokens.
The six maintenance calls used 27,839 prompt tokens and 3,739 completion
tokens. Total serialized usage was 205,399 tokens.

Only 55,390 prompt tokens were reported cached. Actor prefix reuse was strong
through call 7, then fell to zero on calls 8–11 and 164 tokens on call 12 as
relief and replace-in-place scaffold updates changed the prompt. The mechanical
and semantic lifecycle kept every decision feasible, but it paid substantial
prefill and maintenance cost to support tiny acquisition actions.

No artifact progress was purchased within this tranche. That is not yet an
economic verdict because the tranche ends before the first decision that can
use the complete delivered evidence set.

## Qualitative disposition

Supported locally:

- the clean refactored host sustained repeated pressure and six live
  maintenance operations without a retry or lifecycle error;
- Qwen pursued a coherent, non-recurrent twelve-call acquisition plan;
- exact relief did not cause immediate reopen churn;
- anchored semantic expression and admission worked live throughout pressure;
- the active scaffold did not make Qwen prematurely construct or close;
- same-source scaffold replacement again discarded stronger governing facts.

Not yet supported:

- acquisition-to-construction transition;
- scaffold use in exact task work;
- candidate mutation or effect uptake;
- check, repair, current recheck, readiness discrimination, or closure;
- useful completion or architecture promotion.

## Next gate

The highest-value next operation is an unchanged-policy exact-checkpoint
continuation. It should deliver pending `RESULT-012` on the first completed
actor call and observe the first genuine post-catalog decisions. No scaffold
repair, prompt cue, phase reset, or host policy change is justified before that
behavior is observed.

A second tranche should retain the same twelve-call review cadence and stop at
any earlier terminal. The current register's selection losses must remain
visible: the point is to determine whether the complete lifecycle can turn its
actual fallible scaffold and exact artifact surface into construction,
verification, repair, and correct stopping—not to repair the treatment after
seeing its intermediate state.

No continuation occurred under the authorization recorded here.
