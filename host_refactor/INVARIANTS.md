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
  included in a mechanically verified final provider request.
- Provider failure never commits delivery.
- Externalization is legal only after delivery.
- Exact reopen is legal only from delivered-external state and returns the
  object to pending for a later completed invocation.
- Currentness is independent of delivery.
- A delivered candidate effect may move to lifecycle-external state only when
  its exact mutation lineage ends at the exact current candidate.
- That transition may compact the bound assistant mutation action and effect
  together, but preserves both originals in append-only custody.
- Pending candidate effects and their causal actions remain exact-resident.

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
- Applied candidate mutations use compact action/effect receipts only after
  completed delivery and exact candidate-lineage proof.
- Every provider request is bound to the packet hash, manifest hash, exact
  provider-message hash, result exposures, and state-slot exposures.
- Payload transformation may add provider controls but may not drop, reorder,
  or alter the composed model messages.

## Action and response invariants

- A response is eligible for domain action processing only when its exact
  provider finish disposition is allowed by frozen configuration.
- A nonqualified but completed response is preserved exactly, records request
  exposure, emits a nonterminal rejection observation, and executes no action.
- Expected parse or domain rejection is an exact result with candidate binding;
  it does not terminate the trajectory.
- An unexpected adapter or host failure is terminal and distinct from ordinary
  action rejection.
- Reopen capability is derived only from `DELIVERED_EXTERNAL` lifecycle state.
- A reopen changes the original result lifecycle; it does not create a second
  result wrapper for the same exact object.

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
- Configuration binds a complete execution-manifest hash as well as context,
  completion, call, and serialized-token limits.
- A provider attempt may not begin when its frozen maximum request/completion
  cost would exceed the trajectory ceiling.
- Completed request exposures and failed attempted exposures remain distinct.
- Every resumed tranche binds its parent checkpoint hash.
