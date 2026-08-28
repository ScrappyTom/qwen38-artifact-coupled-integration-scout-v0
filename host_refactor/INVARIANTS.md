# Host invariants

## Exact result lifecycle

Each exact result has exactly one projected lifecycle:

```text
ACQUIRED -> PENDING -> DELIVERED_RESIDENT <-> DELIVERED_EXTERNAL
```

- Acquisition means the host has exact bytes; it says nothing about model
  visibility.
- Pending means the bytes are selected for a particular prospective call.
- Delivery occurs only when a completed model invocation names the result as
  included in its exact request.
- Provider failure never commits delivery.
- Externalization is legal only after delivery.
- Exact reopen is legal only from delivered-external state and returns the
  object to pending for a later completed invocation.
- Currentness is independent of delivery.

## Event and replay invariants

- Events are append-only and ordinal.
- Event identifiers and ordinals are unique.
- Replaying the same canonical event sequence yields the same projected state
  and state hash.
- Invalid transitions fail rather than being repaired or inferred.
- A snapshot contains the full event sequence required to reconstruct state.

## Canonical body identity

An exact body identity binds:

- payload hash;
- object identity;
- object version;
- normalized exact span identity when applicable.

The model-visible wrapper and result identifier do not by themselves define
body identity. This permits a repeated request for the same bound payload to be
recognized even when it receives a new action-result identifier.

Same bytes under a different object/version binding are distinct. Partial
overlap is distinct in v0.

## Packet invariants

- The packet is a pure projection of configuration plus replayed events.
- At most one exact payload with a given canonical body identity is resident.
- Pending and resident copies of the same body cannot both render.
- Delivered-external results render exact receipts, never lost identities.
- A repeated resident demand renders compact `already_resident` feedback and
  does not append the exact payload again.
- Packet manifests explain every exact body, receipt, pending result, and
  mechanical feedback entry.

## Capacity invariants

- Feasibility uses the frozen real tokenizer callback and prompt limit.
- Relief considers only delivered, resident, relief-eligible exact results.
- Pending results are protected.
- Each selected substitution must have strictly positive measured savings.
- Selection follows a frozen deterministic order.
- Relief stops immediately when the complete pending packet is feasible.
- Semantic activation and source coverage never gate ordinary capacity relief.

## Checkpoint invariants

- Checkpoints occur only at frozen call/resource boundaries.
- Pausing does not classify the trajectory as useful, looping, or complete.
- Resume continues the same event lineage and budgets.
- Hydration must reproduce the same state hash and next packet bytes.
- Review packets contain literal/mechanical evidence and full-custody handles,
  not host-authored semantic judgments.

