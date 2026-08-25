# Cedar interaction-economics audit

Date: 2026-08-25

Status: offline design evidence; no new model calls and no retroactive admission

Machine-readable receipt: `CEDAR_INTERACTION_ECONOMICS_AUDIT.json`

## Result

E52's shared failure was not merely that a 1,600-token maintenance object was
too difficult to express. The complete synchronous policy spent almost half
of all provider decisions and about twenty-eight percent of serialized tokens
on maintenance, admitted only five of eighteen rewrites in each arm, and made
the independently declared verification tail unreachable.

The exact work path was productive but unsafe. A1 converted more evidence into
a broader artifact, then preserved four material interpretation errors that
entered admitted state through ordinary actor work rather than accepted
maintenance. Its only check preceded two later mutations, and its final effect
never crossed another actor boundary.

This qualifies a system interaction question:

> Can a lower-frequency, mechanically triggered coupled maintenance system or
> a direct actor-authored exact-work system preserve evidence relationships
> while leaving enough bounded opportunity for current verification, repair,
> recheck, and correct closure?

It does not qualify another Cedar continuation or a larger output cap.

## Measured resource split

| arm | actor calls | maintenance calls | provider calls | actor tokens | maintenance tokens | maintenance share of calls | maintenance share of tokens |
|---|---:|---:|---:|---:|---:|---:|---:|
| D0 detached | 19 | 18 | 37 | 371,064 | 144,371 | 48.6% | 28.0% |
| A1 coupled | 19 | 18 | 37 | 368,941 | 141,624 | 48.6% | 27.7% |

Both arms terminated on the maintenance-call ceiling. D0 still had seven
declared actor calls in its current window and A1 had eight. The host therefore
preserved nominal actor opportunity but the policy made it unreachable: the
next positive externalization required another mandatory maintenance call.

## Maintenance acceptance geometry

Both arms accepted exactly maintenance calls 2, 8, 9, 10, and 14. Thirteen of
eighteen outputs were rejected for exceeding the fixed 1,600-token admission
budget; two of those also cited a source outside the exact allowlist.

The externalization gaps were:

```text
start → accepted m02:  one rejected update
m02   → accepted m08:  five rejected updates
m08   → accepted m09:  zero
m09   → accepted m10:  zero
m10   → accepted m14:  three rejected updates
m14   → terminal:      four rejected updates
```

This was not only a late-state carrier problem. The first maintenance call
already exceeded the budget with two allowed sources. Later calls were asked
to rewrite all twelve requirement groups while the allowed source set grew to
thirteen or fourteen. Complete replacement therefore combined three costs:

1. re-expression of already accepted relationships;
2. integration of the newly externalized evidence; and
3. preservation of a growing cross-source state under an unchanged cap.

Rejected prose remains rejected. It was inspected only to determine why the
transport failed and may not be counted as model-visible continuity.

## What accumulated and what did not

The last accepted maintenance state bound eight sources. Evidence from many
later externalizations never entered another accepted maintenance version.
After A1's sole check, the ordinary actor explicitly read S05, S07, and S11;
those domains had appeared in failed maintenance transitions and were not
reliably preserved in the last accepted integration state.

Accepted maintenance did preserve accurate relationships later present in
the exact candidate, including conservative fire-arrival timing, forecast
probability, population overlap, shared road capacity, and readiness blockers.
That establishes availability and plausible temporal influence. It does not
establish unique causal reuse because the actor had also seen exact source
bodies and could independently reconstruct the same facts.

The exact artifact supplied a second accumulation channel. A1 used it to hold
more source coverage and more operational detail than D0. It also held errors
durably. Artifact persistence therefore amplified both valuable and harmful
interpretation.

## Error lineage

The four material A1 contradictions from the independent adjudication did not
originate in an accepted maintenance output:

| contradiction | first admitted location | later persistence |
|---|---|---|
| 5.8 hours became 5.8 km/h | actor decision, call 15 | final decision |
| 42% wind-shift probability became relative humidity | actor decision, call 15 | final decision |
| 91% survey coverage became a 19% uncertainty allowance | actor decision, call 15 | final decision |
| common revision binding became “one revision is permitted” | actor ledger, call 12 | later decision and rejected maintenance prose |

This matters for route selection. A better maintenance carrier alone would not
have prevented these errors. The system also needs candidate-bound feedback
that checks relations, units, probabilities, and version bindings—not merely
headings, terms, citations, or word count.

## Verification and currentness

D0 checked at actor call 13 and mutated at call 14. A1 checked at actor call 14
and mutated at calls 15 and 19. Both final checks were stale. Neither arm
rechecked or submitted. A1's last candidate effect was not delivered into a
later actor decision.

The declared postconstruction budget did not protect a real verification
tail. Maintenance scheduling could consume the control path before that tail
began. A future system must reserve opportunity jointly across provider types,
not merely declare unused actor calls after a construction milestone.

## Capacity-only cadence accounting

The following is mechanical accounting, not a counterfactual behavior claim.

For nineteen positive externalizations:

| policy | separate maintenance calls | provider calls at the observed 19-actor horizon | actor slots still available to the 34-call cap |
|---|---:|---:|---:|
| synchronous measured | 18 | 37 | 15, but unreachable under the maintenance terminal |
| batch every three externalizations, including final flush | 7 | 26 | 15 |
| direct actor work | 0 | 19 | 15, consumed by any actor work actions |

At the full declared actor cap, seven batched maintenance calls would use 41 of
the 52 provider slots, leaving eleven provider slots of headroom. Whether the
batched prompts fit, whether their outputs qualify, and whether either policy
uses the additional decisions well are untested and require prospective Stage
0 qualification.

## Selected successor families

The synchronous Cedar system remains the historical reference. Re-running it
on another task is not required merely for symmetry.

The finite successor candidates are:

### B1 — mechanically batched, artifact-coupled maintenance

- exact evidence externalization remains pressure-triggered;
- a maintenance event fires after a frozen count or byte threshold, never host
  semantic judgment;
- the maintenance pass updates exact, versioned task-native work;
- maintenance effects must cross an actor boundary;
- later checks explicitly bind the candidate version and relation-level
  findings; and
- maintenance cannot consume the protected verification tail.

### W1 — direct actor-authored exact cumulative work

- no separate mandatory maintenance call follows each externalization;
- the ordinary actor can update the same exact task-native work product;
- work actions consume ordinary actor/provider budget;
- exact custody, relief, effect delivery, relation-level checking, repair,
  recheck, and closure remain active; and
- the configuration is not a no-memory or relief-versus-death control.

The comparison is deliberately compound. It asks which complete feedback loop
converts evidence into verified work under a fixed total budget; it does not
claim to isolate a “maintenance main effect.”

## Stage 0 requirements

Before inference, a fresh task/world must establish:

1. realized ingress can reach authentic result-delivery pressure;
2. batched maintenance input and output are feasible under exact tokenizer and
   template accounting;
3. direct work and batched work use the same exact artifact and evaluator;
4. candidate effects and checks expose explicit current/stale bindings;
5. the evaluator detects unit, probability, revision, and cross-source
   relation errors rather than only surface coverage;
6. each arm retains a feasible check→repair→recheck→closure opportunity after
   realistic acquisition and expression failures; and
7. the actor, maintenance, provider, token, and wall ceilings terminate with
   an exact unresolved disposition rather than forced closure.

The Cedar terminal state remains only a design donor. No GPU work is authorized
by this audit.
