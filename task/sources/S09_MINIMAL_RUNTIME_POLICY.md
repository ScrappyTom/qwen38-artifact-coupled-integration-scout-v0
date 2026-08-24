# Minimal runtime policy v0

Date: 2026-08-22
Status: measured v0 policy; scheduled-reentry component retired after scout E35

> Historical policy lock: this document records the policy tested by the v0
> scout. It is not the current incumbent. See
> [REACTIVE_RUNTIME_POLICY_V1.md](REACTIVE_RUNTIME_POLICY_V1.md).

## Scope

This is the smallest model-facing lifecycle policy supported strongly enough to
test as an integrated system. Its reliable part is a **mechanical safety and
operability substrate**, not an end-to-end task-performance architecture.

Evaluation and research custody are deliberately excluded from this runtime
treatment. They are common experimental governance and are specified in
`MANDATORY_EXPERIMENTAL_GOVERNANCE.md`.

## Runtime policy

### 1. Exact external custody and access

Both experimental arms have the same exact external task, source, world,
candidate, event, effect, and history objects and the same access permissions.
Changing model-facing residency never changes authoritative bytes.

### 2. Ordinary chronology while healthy

Within a phase, append ordinary model actions and literal results while the
next valid packet remains feasible. Do not continuously rewrite a prompt that
still satisfies the arm's frozen reserves.

### 3. Host-owned capacity safety

The host renders and tokenizes every prospective request and result delivery
under the frozen template. The model does not own hard-overflow prevention.

Both arms pay the same ordinary response reserve. Treatment additionally pays
the exact, preflighted transition reserve required by its named transition
object. Control is not artificially charged that reserve.

### 4. Deterministic first-fit pressure relief with immediate stop

When a pending exact result would violate treatment's frozen envelope, the
host scans a frozen ordered list of mechanically eligible, previously delivered,
exact-backed result bodies. It replaces one body with its exact reopenable
receipt, rerenders, and stops immediately at the first feasible packet.

This is **minimal under the frozen scan order**. It is not a global
minimum-token or best-subset optimization.

Eligibility requires exact external backing, unchanged object/version binding,
actual prior model-visible delivery, and ordinary exact reopenability. The
pending result cannot be demoted during its own delivery. No semantic relevance
labels or model-selected release amounts are used.

### 5. Actor requests reveal demand

Reads and reopens remain ordinary actions. The host records reopen cost,
repeat reopen, demote-to-reopen interval, re-demotion, novelty, and candidate
progress. A reopen is not automatically a failure.

### 6. Frozen bounded-phase reentry

V0 uses only task-authored phase boundaries declared before inference. It does
not discover phases automatically.

A boundary fires through a prospectively frozen common event: a valid phase
handoff action, completion of a required bounded intermediate artifact, a
frozen phase call ceiling, or an externally scheduled transition.

At that event:

- control appends the common next-phase contract and exogenous phase payload to
  its existing chronology;
- treatment starts a fresh packet with the same common phase contract and
  payload plus only admissible exact current state.

Treatment reentry may include:

1. exact common task and phase inputs declared before any trajectory;
2. exact current candidate/world mechanically derived from admitted effects;
3. a pending observation/effect whose delivery caused the transition;
4. exact objects already delivered to that treatment actor;
5. a predeclared mechanical causal tail; and
6. exact handles to everything else.

It may not introduce an investigator-selected useful source the actor never
acquired, a post-outcome evidence set, or host semantic relevance judgment.

If the frozen result-body relief class cannot preserve treatment's reserves and
no authorized phase transition is available, the endpoint is
`capacity_exhausted_without_authorized_reentry`.

### 7. Hard trajectory budgets

Each task freezes actor-call, transition-call, serialized-token, and wall-clock
ceilings. Budget exhaustion terminates as
`budget_exhausted_with_unresolved_task`; it does not force submission or add a
semantic maintenance pass.

Recurrence is measured but does not trigger a new intervention in v0.

### 8. Excluded mechanisms

V0 contains no default source digest, working note, progress state,
model-managed residency, host relevance scorer, learned policy, semantic
summary, or automatic phase detector.

## Experimental arms

### Control

```text
same exact external custody and access
+ ordinary model-facing chronology
+ same context window and ordinary response reserve
+ common task-authored phase events appended to chronology
+ no result-body pressure relief
+ no chronology-free reentry
+ hard endpoint when the next valid ordinary packet cannot fit
```

### Treatment

```text
same exact external custody and access
+ ordinary chronology while healthy
+ same context window and ordinary response reserve
+ treatment-paid exact transition reserve
+ deterministic first-fit pressure relief under frozen scan order
+ exact reopen on actor demand
+ fresh exact reentry at a frozen task-authored phase boundary
  or declared mechanical relief failure
```

Actor-requested observations and subsequent mutations/effects may diverge after
behavior diverges. Parity means identical accessible world, permissions,
exogenous phase inputs, and evaluation—not identical endogenous trajectories.

## Current claim limit

This policy has earned a fresh-task **whole-method scout**, not architecture
promotion. A positive compound-policy result would justify close transfer and
later ablation. A negative result would route the next study from the first new
exact failure boundary rather than reopen the catalog of old prompt variants.
