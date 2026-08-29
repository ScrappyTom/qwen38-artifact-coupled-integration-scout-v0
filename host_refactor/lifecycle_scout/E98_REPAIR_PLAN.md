# E98 Verification-Lifecycle Apparatus Repair

Date: 2026-08-29

## Scope

The sealed live v0 result remains immutable. This repair addresses two exact
apparatus failures exposed by that run and does not reinterpret or retry any
model action:

1. the JSON response schema changed at verification, but the natural-language
   contract remained construction-only;
2. a rejected assistant body remained fully prompt-resident even though it
   produced no admitted action or world transition.

## Ownership rules

The model owns the semantic decision to check, repair, recheck, or stop. The
host owns the phase-valid action language, exact response custody, action
admission, candidate/check bindings, and prompt projection.

At verification entry, the host exposes a replaceable exact
`current_action_contract` state object. It explicitly supersedes the historical
construction contract and explains the candidate-bound sequence:

```text
current check
→ bounded repair of failed criteria
→ changed-candidate effect uptake
→ current recheck
→ submission only if independently ready
```

The response schema and readable contract must both contain every scripted
provider-free action. A hidden grammar is not treated as usable guidance.

## Rejected-response lifecycle

A response with an unaccepted finish reason is never parsed or executed. The
host first records the completed invocation, exact raw assistant transcript,
response rejection, and action disposition. It then projects that assistant
entry as a compact mechanical receipt containing:

- call and transcript identity;
- exact response SHA-256;
- finish reason;
- rejection-result identity;
- exact external history handle;
- explicit `admitted_action: false` and `world_transition_applied: false`.

The append-only event log and provider custody retain the exact raw response.
Only its ordinary model-facing residency changes. No semantic summary, repair,
or retry is introduced.

## Qualification gates

Before a new live route can be frozen:

1. event replay must reject unbound or duplicate response externalization;
2. provider custody must retain the exact raw rejected body;
3. repeated oversized rejected responses must remain prompt-bounded;
4. the exact sealed v0 four-response sequence must leave a feasible next
   packet under the repaired projection;
5. the complete provider-free check/repair/recheck/closure lifecycle must pass;
6. each scripted action must be present in both the response schema and the
   readable phase contract;
7. the full repository suite, lint, freeze manifest, and new authorization
   request must pass.

The repaired route will start again from the original E96 donor boundary. It
will not resume the sealed v0 terminal or inherit its behavior as task state.
No GPU/provider call is authorized by this plan.
