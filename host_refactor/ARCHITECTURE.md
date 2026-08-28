# Refactor architecture

## Data flow

```text
IMMUTABLE RUN CONFIGURATION
             |
             v
APPEND-ONLY EVENT / CUSTODY LOG
             |
             v
PURE DELIVERY-STATE PROJECTION
             |
             v
PURE PACKET COMPOSER + MANIFEST
             |
             v
DETERMINISTIC CAPACITY PLANNER
             |
             v
ONE-SHOT PROVIDER ADAPTER
             |
             v
DOMAIN ACTION ADAPTER
             |
             v
CHECKPOINT / REVIEW / RESUME
```

## Modules

### `model.py`

Immutable schemas for exact results, canonical body identity, transcript
entries, events, projected result state, packets, provider outcomes, terminal
states, and frozen run configuration.

### `kernel.py`

The only implementation of result lifecycle transitions. It appends validated
events and replays them into projected state. It does not render prompts or
call providers.

### `packet.py`

Purely renders transcript entries against projected delivery/residency state,
deduplicates canonical exact bodies, and returns both messages and a mechanical
manifest.

### `capacity.py`

Measures complete packets and plans deterministic strictly-positive first-fit
externalization. It contains no source-count, phase, or semantic relevance
logic.

### `checkpoint.py`

Serializes event history, budgets, configuration binding, and mechanical review
telemetry. Hydration verifies hashes before returning a resumable kernel.

### `provider.py`

Wraps exactly one provider attempt and returns a completed or failed outcome.
It never retries and never owns lifecycle transitions.

### `runner.py`

A thin coordinator parameterized by immutable configuration, provider, and
domain adapter. It calls shared modules; it does not contain alternate delivery
or relief semantics.

### `trellis_fixture.py`

Converts frozen E83 custody into common events and supplies provider-free
acceptance fixtures. It is a migration boundary, not a general task policy.

## Historical cut line

The existing `reactive_runtime` and historical `tools/run_*` files remain as
frozen evidence producers. The new path initially lives wholly in this
subproject. Only after acceptance will a future experiment import the thin
runner directly through an immutable task adapter.

