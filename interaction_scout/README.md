# Interaction scout

This subproject composes the refactored mechanical host with one optional
semantic operation and the exact Trellis task lifecycle. It tests a complete
bounded-work configuration; it does not move semantic judgment into the host.

The host remains responsible for exact custody, delivery, packet composition,
capacity, deduplication, currentness, request binding, and checkpoints. The
interaction layer charges and exposes the treatment-only construction
scaffold, records admission failures, and demotes it when verification begins.

The first live comparison pauses after twelve actor calls per configuration.
Codex reviews the literal transcript at that checkpoint; the host records
recurrence and state but never declares that the actor is looping or ready.

See `GOVERNANCE.md`, `WORK_LOG.md`, and the repository-level
`TRELLIS_REFACTORED_INTERACTION_STAGE0.md`.
