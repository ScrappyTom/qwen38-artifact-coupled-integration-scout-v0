# Cross-run causal-continuity and repair-transport audit

Date: 2026-08-27

Status: offline audit and provider-free contract qualification complete; zero
new model calls; no GPU operation authorized

Machine records:

* `CROSS_RUN_CAUSAL_CONTINUITY_AUDIT.json`
* `VERIFICATION_CAUSAL_CONTRACT_PREFLIGHT.json`

## Question

Was Orchard's terminal sequence a donor-specific accident, or does the existing
program contain a broader interaction between rejected task actions, bounded
causal continuity, repair transport, and repeated non-progress?

This audit does not ask whether one prompt field improves behavior. It traces
complete action/effect/check histories already produced by four independent
task worlds.

## Scope

The deterministic audit covers 157 sealed actor calls in ten cells:

| World | Cells | Relevant role |
|---|---:|---|
| Architecture decision (E46) | 2 | incremental construction, check, repair, repeated no-effect action |
| Cedar (E52) | 2 | negative/control trajectories without action rejection recurrence |
| Solace construction (E69) | 2 | admitted incremental work versus repeated unadmitted global transport |
| Solace verification (E72) | 2 | admitted patch/check loops and stale final effect |
| Orchard (E76) | 2 | fixed-state capacity failure versus bounded-current recurrence |

These are ten cells but four independent worlds. Same-world arms and stages are
not independent replication.

## Literal cross-run findings

### Architecture-decision D0

The final two actor calls emitted the same exact `upsert_decision_section`
action, with the same heading and byte-identical body. Both were rejected as
`no_effect`; the candidate did not change.

This is an exact rejected-action recurrence in a world independent of Orchard.

The A1 arm is a useful contrast. Its two `no_effect` events were each followed
immediately by a different admitted section update. A rejection does not force a
loop when a viable alternative remains behaviorally accessible.

### Solace W0

After building a fourteen-source evidence ledger and reopening fourteen exact
objects, W0 produced two consecutive full-decision responses that each ended at
the response ceiling and failed JSON admission. The drafts differed, so this is
not byte-identical action recurrence. It is repeated failure at the same
model-to-action transport boundary while the candidate remained unchanged.

The Solace A0/A1 verification cells are positive controls: their bounded patch
and check actions were admitted in alternating sequences. They stopped because
the last effects could not enter current rechecks, not because repair binding
failed.

### Orchard P1

The first `patch_anchor_not_unique` rejection at actor call 16 was followed by a
targeted CHILL read and a different admitted repair at call 18. The rejection
was still recent enough for recovery.

The second non-unique rejection at call 20 remained unresolved. Calls 21–24
then made four byte-identical reads of `CURRENT:1-64`, with no candidate change.
The bounded current-state projection carried the latest observation but did not
retain the still-active repair rejection or an explicit recurrence fact.

### Cedar

Neither Cedar cell contains an action rejection or exact consecutive action
recurrence. Cedar therefore prevents the audit from treating every incomplete
trajectory as a causal-continuity failure.

## Systems conclusion

Three independent worlds exhibit action-transport failure followed by repeated
non-progress at the same functional boundary. Two independent worlds contain
rejected mutation recurrence specifically:

```text
architecture decision
    rejected no-effect section update
    -> exact same rejected update

Orchard
    rejected ambiguous patch
    -> later observation displaces rejection from current projection
    -> four exact reads without mutation
```

This supports a narrow lifecycle law:

> A rejected mutation remains causally active while the candidate is unchanged.
> A later source observation must not mechanically erase that fact.

It does not establish that showing this fact to Qwen changes behavior.

The coupled system boundary is now:

```text
current exact artifact
× exact current check
× mutation transport and admission
× persistence of unresolved rejection
× recurrence inside the unchanged-candidate epoch
× effect uptake and current recheck
× readiness and closure
```

## Bounded mechanical projection

`bounded-verification-causal-frame-v0` is implemented as a host-derived
projection. It contains only exact ledger facts:

* current candidate hash;
* compact current check identity, currency, failing criterion IDs, blocker
  count, and exact result handle;
* latest attempted action and exact outcome;
* latest unresolved rejected action, retained until candidate change;
* latest delivered update;
* latest candidate effect;
* repeated exact-action count inside the current candidate epoch; and
* exact history handle.

It contains no semantic summary, recommended repair, readiness assertion, or
automatic intervention. Across all audited endpoints, the largest rendered
frame is 1,297 tokenizer tokens. At Orchard's terminal P1 state it preserves:

* the call-20 `patch_anchor_not_unique` rejection;
* the four identical CURRENT reads;
* the unchanged candidate;
* the current check identity and exact reopen handle.

## Structurally bound repair

The provider-free contract replaces ambiguous free-form substring patches with
one exact task-artifact section transaction:

```text
replace_artifact_section
candidate_sha256
artifact_sha256
unique section heading
expected exact section SHA-256
complete replacement section
```

The host validates the complete candidate, artifact bytes, unique section, and
section version. It does not choose semantic content.

Against the exact Orchard P1 candidate:

* a valid repair action is 461 tokenizer tokens and is admitted;
* stale candidate binding is rejected without mutation;
* stale section binding is rejected without mutation;
* the admitted effect starts a new candidate epoch and clears the old active
  rejection;
* a provider-free check binds to the new candidate as current; and
* the post-recheck causal frame is 983 tokens.

The fixture deliberately remains `not_ready`. Reachability is not utility.

## Claim disposition

| Claim | Status |
|---|---|
| Action transport and rejection continuity recur across worlds | supported |
| Rejected mutation recurrence occurs beyond Orchard | supported in architecture decision and Orchard |
| An unresolved rejection should survive unrelated observations while candidate is unchanged | supported mechanical lifecycle rule |
| Candidate-/artifact-/section-bound repair is mechanically feasible | provider-free positive |
| The proposed frame is bounded under audited endpoints | provider-free positive, maximum 1,297 tokens |
| The frame improves actor behavior | untested |
| The fields are minimal or sufficient | untested |
| Recurrence should trigger semantic maintenance or closure | unsupported |
| Orchard should be extended or rerun | no |

## Routing

The cross-world gate is satisfied strongly enough to justify a fresh
whole-system Stage 0. The next comparison must not be an Orchard prompt ablation.
It must use a new task/world and keep the complete earned interaction active:

* pressured evidence ingress;
* temporary provenance-bound construction scaffold;
* exact incremental task artifact;
* actor-selected verification transition;
* candidate-bound check;
* uniquely bound section repair;
* bounded current verification state;
* bounded mechanical causal continuity;
* effect uptake, current recheck, readiness, and closure.

No new task has yet qualified, and no GPU run is authorized.
