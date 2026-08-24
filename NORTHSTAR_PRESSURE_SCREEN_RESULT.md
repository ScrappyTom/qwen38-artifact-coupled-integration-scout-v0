# Northstar transfer pressure-screen result

Run: `2026-08-24-northstar-transfer-pressure-screen-v0`

Authorized freeze:
`40272d6cc0c5aa2eda7bb5df9394ff02d767829d`

Disposition: **sealed, mechanically valid, scientifically ineligible**.

## Literal result

The actor used two valid batch reads with one attempt per call and zero
retries:

1. `RESULT-001` contained exact S01–S03 and crossed the second actor boundary.
2. `RESULT-002` contained exact S04–S06 and remained pending.

Adding `RESULT-002` to ordinary chronology produced a 25,705-token prompt
against the frozen 20,992-token allowance, an authentic 4,713-token overflow.
The candidate remained exact-initial; no check or submission occurred. A
deterministic positive-savings first-fit step could replace `RESULT-001` and
reduce the same pending-result packet to 14,654 tokens.

The run therefore establishes real pressure and mechanical relief feasibility.
It does **not** establish the frozen scientific fork. The prospective gate
required at least four previously delivered source-observation result objects.
Only one delivered batch result object—covering three sources—existed when the
second batch overflowed. The runner correctly stopped as
`pressure_boundary_ineligible`; the task-selection contract prohibits a retry
or post-hoc relaxation.

## Interaction lesson

The failure arose from the interaction between actor-selected batch ingress,
large exact results, and residency—not from absent world size or an action
transport failure. Batching increased evidence per decision and simultaneously
made pressure arrive before the comparator's meaningful-acquisition gate.
Future transfer qualification must prospectively align its activation unit
with the ingress geometry it permits. It must not count a three-source batch as
one thing for pressure eligibility while relying on batching as the system's
evidence-throughput mechanism.

This does not authorize weakening the current rule after observing the run.
Under `STAGE0_PLAN.md`, a non-diagnostic screen ends this task selection. Any
successor must use a fresh prospective design and new authorization.

## Apparatus finding

The frozen runner omitted `task_source_lock_sha256` from `SCREEN_RESULT.json`
although the frozen qualification auditor required it. The exact task lock is
still present and verified in `FREEZE_BINDING.json`, so this did not cause the
early scientific ineligibility or compromise raw custody. The post-run code
adds the missing field for future screens without modifying the sealed result.
`NORTHSTAR_PRESSURE_SCREEN_DISPOSITION.json` separately verifies the sealed
run's mechanical integrity and preserves this defect explicitly.

## Claim limit

Supported:

- authentic early result-delivery pressure;
- exact two-call behavior and raw custody;
- unchanged candidate and no premature check/closure;
- positive deterministic relief feasibility; and
- an ingress-by-residency activation mismatch in this task design.

Not supported:

- a qualified D0/A1 fork;
- artifact-coupling utility or harm;
- semantic integration quality;
- measured continuation;
- retrying this screen; or
- promoting a revised gate from the observed outcome.
