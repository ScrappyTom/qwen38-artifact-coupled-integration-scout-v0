# Host code audit and cut line

Date: 2026-08-28

## Baseline

- apparatus branch was clean at
  `324aa72325430fd5353d1591831c93fce33d842f`;
- full baseline: 235 tests passed in 296.71 seconds;
- no GPU or provider call was used.

## Duplicate lifecycle ownership found

The old path has at least 34 direct `mark_model_visible` call sites spanning
live runners, Stage 0 simulations, auditors, fixtures, and tests. Several
measured runners also directly assign `resident` and `message_index` instead of
using even the historical ledger method.

Pressure relief is called from the shared policy, but more than twenty runner,
preflight, Stage 0, audit, and test paths independently decide when and how to
invoke it. That leaves activation, delivery, and feasibility ordering outside
the shared component.

Three task pressure-screen wrappers reconfigure a historical runner through
module globals:

- `run_trellis_pressure_screen.py`;
- `run_keystone_pressure_screen.py`;
- `run_orchard_pressure_screen.py`.

The wrappers change task identity, paths, model lock, seed, budgets, world
class, action surface, and activation thresholds in shared process state.

## Reproduced E83 divergence

`tools/trellis_stage0.py::_pressure_geometry` does this in one iteration:

```text
execute read
append exact result
mark that result model-visible at call+1
count the packet
```

There is no completed call+1 invocation between the last two operations.

The live runner instead does:

```text
start next actor call with prior pending result
complete provider invocation
mark prior pending result visible
execute new action
acquire and append new pending result
```

The sealed Trellis boundary proves the live state:

- calls completed: 7;
- delivered/resident results: RESULT-001 through RESULT-006;
- delivered sources: CLIMATE, CLINIC, COUNCIL, GRID, SHELTER, WATER;
- pending result: RESULT-007;
- pending sources: COMMS, TRANSIT;
- ordinary packet: 21,401 tokens;
- prompt limit: 20,992;
- first positive relief: RESULT-001.

The refactor fixture reconstructs this exact packet from append-only events and
matches `FINAL_MESSAGES.json` byte-for-byte at the canonical message level.

## Selected cut line

Do not refactor every historical task module. The new path owns only:

- immutable configuration;
- delivery and residency events;
- packet projection and manifest;
- exact-body deduplication;
- common capacity relief;
- one-shot provider coordination;
- checkpoint/review/resume;
- one Trellis domain adapter.

Existing world execution remains temporarily behind a compatibility adapter.
The adapter may project a legacy `ResultLedger` for `reopen_exact`, but the
projection is read-only and new delivery authority stays in the event kernel.

## Remaining historical risks outside the cut line

- older measured runners still mutate residency directly;
- task-specific Stage 0 and audit paths still contain divergent simulations;
- old schema names remain in sealed outputs;
- some historical runner failures are terminal while others append a rejection
  and continue;
- not every historical result exposes payload bytes separately from its wrapper.

These are documented rather than mass-migrated. A future experiment must use
the new configured path; a historical experiment remains interpreted through
its sealed runner and audit.

