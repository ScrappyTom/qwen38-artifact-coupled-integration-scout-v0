# Host runtime refactor subproject

Status: active offline refactor; no GPU operation is selected or authorized.

This directory is a contained subproject for replacing duplicated host
lifecycle behavior with one reviewable execution kernel. Historical runners
and sealed experiment outputs remain frozen. New code enters the selected host
path only after provider-free equivalence and regression tests pass.

The refactor is intentionally narrow. It owns exact custody, delivery state,
packet composition, deterministic capacity relief, provider-attempt custody,
and checkpoint/resume. It does not add semantic notes, relevance scoring,
automatic phase inference, loop classification, or model-managed eviction.

## Working order

1. Freeze invariants and architectural decisions.
2. Reconstruct E83 from exact historical custody.
3. Implement one append-only transition kernel.
4. Make packet composition a pure projection of that kernel.
5. Add exact-body deduplication and repeat-demand feedback.
6. Add deterministic first-fit pressure relief without semantic gates.
7. Add sealed checkpoint, review packet, and exact resume.
8. Put one thin configured runner over the shared components.
9. Run provider-free, property, and historical regression tests.
10. Reconcile program documentation before selecting any live experiment.

## Governing files

- `GOVERNANCE.md` defines how this subproject is changed and reviewed.
- `INVARIANTS.md` defines behavior that code and tests must enforce.
- `ARCHITECTURE.md` defines module responsibilities and data flow.
- `DECISIONS.md` records consequential choices and alternatives.
- `WORK_LOG.md` records checkpoints, evidence, and remaining risks.

## Completion gate

This subproject is not complete merely because its new tests pass. Completion
requires all acceptance criteria in `GOVERNANCE.md`, a clean full historical
test run, byte-identical offline/live packet projection from common events,
and documentation of any historical path intentionally left unmigrated.

