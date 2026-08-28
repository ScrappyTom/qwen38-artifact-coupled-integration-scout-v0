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
FINAL REQUEST / EXPOSURE BINDING
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

### `binding.py`

Verifies that the final provider payload contains the exact composed messages
and frozen completion reserve, then binds that payload to the packet,
manifest, pending result bodies, and current exact state exposures. A failed
binding prevents the provider attempt and commits no delivery.

### `runner.py`

A thin coordinator parameterized by immutable configuration, provider, and
domain adapter. It calls shared modules; it does not contain alternate delivery
or relief semantics. Expected response/action rejection is exact nonterminal
evidence; unexpected adapter failure is terminal. Finish-reason eligibility is
checked before any task action can execute.

### `live_path.py`

Runs a bounded tranche, writes per-call custody and timing, verifies the exact
parent checkpoint before resume, and reports provider attempts, completed
invocations, and failed invocations separately.

### `trellis_fixture.py`

Converts frozen E83 custody into common events and supplies provider-free
acceptance fixtures. It is a migration boundary, not a general task policy.

## Historical cut line

The existing `reactive_runtime` and historical `tools/run_*` files remain as
frozen evidence producers. The new path initially lives wholly in this
subproject. Only after acceptance will a future experiment import the thin
runner directly through an immutable task adapter.
