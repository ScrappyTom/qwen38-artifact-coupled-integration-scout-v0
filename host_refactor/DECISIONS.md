# Refactor decision log

## D001 — append-only events are authoritative

Decision: new lifecycle state is reconstructed from validated events. Mutable
booleans are projections, not independent authorities.

Reason: E83 showed that separately maintained visibility assumptions diverged
between Stage 0 and live execution.

## D002 — delivery commits on completed invocation

Decision: a result becomes delivered only after a provider/model invocation
completes successfully with that result listed in the exact request manifest.
An attempted or failed invocation does not commit delivery.

Reason: this is conservative, auditable, and matches the project rule that
information counts only after it crosses a completed model decision boundary.
Request custody may separately prove that bytes were sent without upgrading the
behavioral claim.

## D003 — body identity excludes result wrapper identity

Decision: canonical body identity binds payload hash, object, version, and exact
span. Result IDs and wrapper headers remain event identities but do not defeat
deduplication.

Reason: identical actor requests normally receive new result IDs. Treating the
wrapper hash as body identity would duplicate the same exact payload.

## D004 — repeat demand is visible mechanical feedback

Decision: requesting an already resident canonical body emits a compact
`already_resident` control result in chronology. It does not append the body.

Reason: silently ignoring the request hides a real action outcome; duplicating
the bytes wastes capacity. The feedback describes state without advising the
actor.

## D005 — ordinary relief has no semantic activation gate

Decision: pressure relief is common mechanical infrastructure. If a pending
packet does not fit, the host applies deterministic strictly-positive relief
immediately when possible.

Reason: Trellis showed that gating relief on delivered evidence breadth can
prevent delivery of the very pending evidence that would increase breadth.

## D006 — checkpoints pause; they do not judge

Decision: default review boundaries are twelve completed actor calls and sixty
maximum calls, subject to later offline cost review. The host records recurrence
telemetry but does not label loops or force closure.

Reason: pacing is task/model behavior. Codex needs literal transcript evidence
to distinguish coherent slow work from cycling.

