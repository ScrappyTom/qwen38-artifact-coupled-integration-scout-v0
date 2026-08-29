# Trellis refactored-host interaction tranche result

Date: 2026-08-29

Freeze commit:
`381e44c9eb3c3c10a793903155c2482f5f8c570f`

Run ID:
`2026-08-29-trellis-refactored-interaction-tranche-v0`

Disposition: valid sealed checkpoint result; no useful completion and no
authorization to continue.

## Literal result

The authorized run completed exactly as bounded:

| Measure | V0 exact artifact | V1 temporary scaffold |
|---|---:|---:|
| Actor calls | 12 | 12 |
| Maintenance calls | 0 | 6 |
| Provider calls | 12 | 18 |
| Serialized tokens | 174,573 | 205,399 |
| Actor prompt tokens | 173,917 | 173,165 |
| Actor completion tokens | 656 | 656 |
| Cached actor prompt tokens | 74,635 | 55,361 |
| Relief events | 4 | 6 |
| Exact result bodies externalized | 5 | 7 |
| Exact reopens | 0 | 0 |
| Admitted maintenance claims | 0 | 20 |
| Final resident scaffold claims | 0 | 10 |
| Candidate changes | 0 | 0 |

Across both cells the aggregate was 24 actor calls, six maintenance calls, 30
provider calls, and 379,972 serialized tokens. One attempt was made per call;
there were no retries or run failures. Both fresh runtimes passed their gates,
stopped at `checkpoint_pause`, were released, and are covered by the aggregate
tree seal.

Both actors made the same twelve accepted actions in the same order: they read
the first and second halves of COUNCIL/CLIMATE, GRID/WATER, CLINIC/SHELTER,
TRANSIT/COMMS, SUPPLY/LABOR, and LINEAGE/REVIEW. `RESULT-001` through
`RESULT-011` crossed later actor invocations. `RESULT-012`, containing the
second LINEAGE/REVIEW ranges, was acquired by call 12 and remained pending.

Neither actor reopened, repeated an exact demand, changed the exact evidence
ledger, changed the decision artifact, checked, repaired, or proposed
submission. Both exact candidates remained the initial placeholder and failed
the actor-invisible checkpoint evaluator.

## What the treatment changed

V1 was mechanically active from actor call 8 onward. Source-result
externalization triggered six charged maintenance calls. All twenty proposed
claims passed per-claim mechanical admission, every maintenance response ended
normally, and no claim was rejected.

The semantic layer nevertheless changed the surrounding information economy:

- it added 31,578 serialized maintenance tokens;
- total V1 cost was 30,826 tokens above V0;
- it reduced actor prefix-cache reuse by 19,274 cached prompt tokens;
- it caused six relief events instead of four;
- and it externalized seven exact source results instead of five.

The last difference is endogenous. The scaffold occupied prompt space, so V1
had to move more exact evidence out of residency even though the actor requested
exactly the same information as V0.

## Register lifecycle finding

The frozen register is source-slot replacing, not within-source cumulative.
When a later range from the same source was externalized, its admitted claims
replaced the earlier claims for that source.

This produced a sharp qualitative pattern:

1. The first COUNCIL/CLIMATE maintenance call captured governing authority and
   activation thresholds. The second-range update replaced all four with two
   low-value tail-table status facts.
2. The first GRID/WATER update captured usable capacity, backup duration,
   all-node pressure, and reserve/consumption. The second-range update replaced
   all four with one current table row per source.
3. The first CLINIC/SHELTER update captured occupancy and staffed accessible
   capacity. The second-range update replaced both with one table row per
   source.
4. The last update also added four useful TRANSIT/COMMS facts concerning
   inspection coverage, route-time distributions, message reach, and call
   capacity.

Twenty claims therefore entered over time, but ten were shed through later
same-source replacement. The final ten-claim register covered eight source
identities while retaining many less decision-relevant late-range rows and
losing several more important early-range distinctions.

This is not a semantic fabrication or admission failure. It is an interaction
between chunk-level ingress cadence and full source-slot replacement.

## Qualitative interpretation

The scaffold was semantically and mechanically active but behaviorally inert
within this first checkpoint. After the configurations diverged, every actor
action still matched literally. The actor's immediate policy was dominated by
finishing each two-range source pair and advancing through the source catalog.

The result does not show that the scaffold is useless. Neither actor had yet
received the final pending result or made its first post-acquisition decision.
The configuration has therefore not reached the point where semantic residue
or exact resident evidence might influence construction timing, construction
granularity, exact reopen demand, or artifact quality.

It does show that the treatment is not free and that its current replacement
semantics can discard high-value source meaning before construction. Any later
benefit must outweigh maintenance cost, lost cache reuse, additional exact
turnover, and semantic replacement loss.

## Supported disposition

Supported locally:

- the refactored host sustained repeated live pressure in two fresh cells;
- pending versus delivered custody, exact relief, action admission,
  checkpointing, sealing, and runtime release remained correct;
- V1 produced and exposed grounded bounded semantic state without blocking
  ordinary work;
- the semantic state changed exact-residency economics;
- and full same-source replacement shed half of all claims admitted over time.

Not supported:

- useful artifact progress;
- a V0/V1 behavioral advantage;
- semantic continuity through construction;
- verification, repair, readiness, or closure;
- or architecture promotion.

The exact run is paused. It must not be modified or continued without a new
frozen continuation and separate authorization.

