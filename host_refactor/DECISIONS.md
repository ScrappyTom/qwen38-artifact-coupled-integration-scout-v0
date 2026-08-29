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

## D007 — the final provider request is the exposure authority

Decision: the host verifies that the provider-facing message list is byte-for-
byte equivalent to the composed packet. Invocation events bind the packet,
manifest, final messages, exposed results, and exposed state versions.

Reason: a pre-transform pending list cannot prove that a task payload builder
actually sent those bytes.

## D008 — ordinary rejection is evidence, not termination

Decision: adapters translate declared parse/action rejections into exact,
candidate-bound observations that continue through the normal result lifecycle.
Only unexpected adapter or host failure is terminal.

Reason: rejection, no effect, stale binding, and invalid ranges are ordinary
feedback events in the experimental systems and may be causally important.

## D009 — reopen authority stays in the kernel

Decision: task adapters validate a reopen request but the runner applies
`HostKernel.request_reopen()` to the original result. Action availability comes
from projected delivery state, not rendered receipt positions.

Reason: receipts are representations of chronology; they are not lifecycle
authority.

## D010 — exact provenance is host-mechanical

Decision: accepted finish reasons, execution package hashes, request exposure,
resource ceilings, and checkpoint parentage are frozen mechanical bindings.

Reason: these facts can be enforced without semantic judgment and are required
to interpret later model behavior safely.

## D011 — bound applied mutation history as a causal pair

Decision: once a candidate effect has crossed a completed model call and the
exact effect lineage ends at the current candidate, the host may replace both
the old effect body and its bound assistant mutation action with compact
model-facing receipts. Pending effects and their actions remain exact.

Reason: Trellis E96 retained multiple copies of artifact content in the current
candidate, mutation actions, and effect results. Generic pressure relief could
not touch those non-relief-eligible effects, while generic receipts could be
larger than the small effect bodies. The causal-pair transition removes only
mechanically proven redundancy and does not infer model understanding,
readiness, or semantic value.
