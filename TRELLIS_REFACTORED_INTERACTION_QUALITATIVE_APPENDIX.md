# Trellis call-by-call qualitative transcript appendix

Date: 2026-08-29

Run ID:
`2026-08-29-trellis-refactored-interaction-tranche-v0`

This appendix describes literal model-visible state and actions. “Likely”
interpretations are investigator inferences from the action sequence, not a
hidden reasoning trace.

## Common calls 1–7

The actor responses were byte-equivalent across V0 and V1 through call 7.
Every call exposed the exact current candidate, which remained the initial
70-byte decision placeholder plus the initial 100-byte evidence ledger.

| Call | Newly visible exact result | Actor action | Information/work transition |
|---:|---|---|---|
| 1 | None | Read COUNCIL/CLIMATE 1–60 | Began at the catalog head. No work artifact changed. |
| 2 | RESULT-001: COUNCIL/CLIMATE 1–60 | Read both 61–94 | Completed the same source pair rather than constructing. |
| 3 | RESULT-002: COUNCIL/CLIMATE 61–94 | Read GRID/WATER 1–60 | Advanced to the next catalog pair. |
| 4 | RESULT-003: GRID/WATER 1–60 | Read both 61–94 | Completed the pair. |
| 5 | RESULT-004: GRID/WATER 61–94 | Read CLINIC/SHELTER 1–60 | Continued breadth acquisition. |
| 6 | RESULT-005: CLINIC/SHELTER 1–60 | Read both 61–94 | Completed the pair. |
| 7 | RESULT-006: CLINIC/SHELTER 61–94 | Read TRANSIT/COMMS 1–60 | Continued the same depth-first pair cadence. |

Prompt size rose from 2,362 tokens on call 1 to 18,305 on call 7. No pressure
relief, semantic maintenance, reopen, mutation, or action rejection occurred.

## Call 8: first authentic divergence

Both calls delivered RESULT-007, the first TRANSIT/COMMS ranges, and both actors
requested TRANSIT/COMMS 61–94.

V0 externalized RESULT-001 and exposed its exact receipt. Exact RESULT-002
through RESULT-007 remained resident. Its actor prompt was 18,786 tokens.

V1 also externalized RESULT-001, then paid one maintenance call over its exact
COUNCIL/CLIMATE contents. Four claims entered the scaffold:

- health-commissioner emergency authority;
- continuity-director closure authority;
- 30.0/32.0 activation thresholds and consecutive-window condition;
- and the 0.62 forecast probability versus 84-percent observed coverage.

The actor saw that new scaffold plus exact RESULT-002 through RESULT-007. Its
prompt was 20,166 tokens. Despite the fresh governing semantic state and the
1,380-token prompt difference, the action category and exact ranges matched V0.

Likely demand interpretation: completing the already-started TRANSIT/COMMS pair
had stronger immediate salience than beginning artifact work.

## Call 9: same-source replacement begins

Both calls delivered RESULT-008 and requested SUPPLY/LABOR 1–60.

V0 retained exact RESULT-002 through RESULT-008 and required no new relief. Its
prompt was 20,864 tokens.

V1 externalized RESULT-002 and ran maintenance on the second COUNCIL/CLIMATE
ranges. The new one-claim source records replaced, rather than supplemented,
the four prior claims. The scaffold now retained only:

- a superseded COUNCIL utility-desk table row; and
- a superseded CLIMATE central-core 41.8-degree table row.

The authority and threshold relationships from call 8 were no longer present.
The actor prompt was 20,091 tokens with the revised scaffold. The actor still
made exactly the V0 acquisition action.

Likely systems interpretation: the treatment relieved pressure partly by
converting exact evidence to semantic residue, but its source-slot replacement
policy converted useful early meaning into less useful late-chunk recency.

## Call 10: paired replacement repeats

Both calls delivered RESULT-009 and requested SUPPLY/LABOR 61–94.

V0 externalized RESULT-002 and RESULT-003 in one relief event. It retained
exact RESULT-004 through RESULT-009. Its prompt was 19,807 tokens.

V1 externalized RESULT-003 and RESULT-004 through two relief/maintenance
events. The first maintenance call added four strong GRID/WATER claims:

- 31.0 MW installed versus 24.5 MW usable cooling capacity;
- 8.4 MW backup duration under two load regimes;
- 35 psi at every node for three consecutive windows;
- and 1.6 million liters reserve versus 0.19 million liters/hour consumption.

The immediately following second-range update replaced those four with two
tail-table facts: backup-plant 29.8 MW and mobile-cache 39.8 psi. Its actor
prompt was 19,732 tokens. The actor again matched V0 exactly.

Likely systems interpretation: maintenance timing was coupled too tightly to
result-body externalization. Because each physical source arrived in two
ranges, the later range could overwrite the semantic value extracted from the
earlier range before the actor had used it in work.

## Call 11: useful claims enter briefly

Both calls delivered RESULT-010 and requested LINEAGE/REVIEW 1–60.

V0 externalized RESULT-004, retained RESULT-005 through RESULT-010, and used a
20,323-token prompt.

V1 externalized RESULT-005. Maintenance added current clinic occupancy and
staffed accessible shelter capacity. The actor saw those claims alongside the
prior six retained source slots and exact RESULT-006 through RESULT-010. Its
prompt was 19,716 tokens. Its next read still matched V0.

Likely demand interpretation: the actor remained committed to completing the
catalog before externalizing task work. The scaffold did not interrupt that
pacing.

## Call 12: final acquisition action and checkpoint

Both calls delivered RESULT-011, the first LINEAGE/REVIEW ranges, and requested
their second ranges. Both then acquired RESULT-012 as pending; neither actor has
seen RESULT-012 yet.

V0 externalized RESULT-005 and finished with exact RESULT-006 through
RESULT-011 resident. Its prompt was 20,611 tokens.

V1 externalized RESULT-006 and RESULT-007. One maintenance call processed both.
It replaced the useful clinic/shelter claims with one later table row each and
added four useful TRANSIT/COMMS claims:

- 22 of 26 shuttles passed inspection;
- median 26-minute versus p95 44-minute route time;
- 89-percent message reach with 11-percent delivery uncertainty;
- and 1,300 contacts/hour capacity versus 1,750/hour demand.

V1 finished with exact RESULT-008 through RESULT-011 resident and a ten-claim
scaffold spanning eight source identities. Its prompt was 19,934 tokens.
Again, the actor action matched V0.

## Checkpoint comparison

### What each actor had temporally observed

Both had received RESULT-001 through RESULT-011. Each had therefore observed
all source material except the pending second halves of LINEAGE and REVIEW.

### What remained exact-resident

- V0: RESULT-006 through RESULT-011.
- V1: RESULT-008 through RESULT-011.

V1 externalized two additional result bodies because its scaffold consumed
model-facing capacity.

### What semantic state remained

- V0: no separate semantic state.
- V1: ten anchored claims across CLIMATE, CLINIC, COMMS, COUNCIL, GRID,
  SHELTER, TRANSIT, and WATER.

The V1 register was exact, provenance-bound, non-authoritative, and mechanically
safe. Its content quality was uneven because ten earlier admitted claims were
replaced by later same-source updates.

### What entered the artifact

Nothing in either configuration. The evidence ledger and decision remained the
exact initial files. No candidate effect existed for later uptake.

### Demand and construction transition

There was no transition to construction. Both actors followed an identical,
orderly acquisition program and used all twelve calls reading six source pairs.
There was also no looping: no reread, reopen, repeated exact action, invalid
action, or repeated assistant message occurred.

The treatment therefore did not solve or worsen actor pacing within this
horizon. It changed the information stock and its cost while leaving expressed
demand unchanged.

### The next unobserved decision boundary

The next completed invocation would deliver RESULT-012. It would be the first
decision at which the actor could know that the catalog's final source pair was
complete. That is the earliest clean boundary for observing whether either
configuration constructs, reopens, continues acquiring, or uses the scaffold.

No such call is part of this sealed tranche.

