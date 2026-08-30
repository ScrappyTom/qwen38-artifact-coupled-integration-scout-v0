# E104 — Verification-residency reconciliation

Date: 2026-08-30

## Result

E103 did not stop because the current artifact or pending effect was too large
in isolation. It stopped because the prompt carried the latest verification
findings twice:

1. as the complete delivered `RESULT-024` check body; and
2. inside the replaceable `current_verification_frame` state object.

The older delivered `RESULT-021` check body also remained resident although a
newer candidate-bound check had crossed a completed model call.

The historical live call-27 packet was 21,318 tokens against a 20,992-token
allowance, a 326-token deficit. In the exact offline reconstruction,
`RESULT-021` and `RESULT-024` cost approximately 899 and 912 marginal tokens.
The pending `RESULT-026` candidate effect cost approximately 1,264 tokens and
must remain exact.

## Prospective rule

A delivered check may leave full prompt residency only after the current
verification slot binds all of the following:

- exact check result ID;
- exact result SHA-256;
- evaluated candidate SHA-256;
- exact check-projection SHA-256;
- the complete check projection plus mechanical current/stale fields;
- an exact reopen action.

The rule does not infer that the actor understood the check, that the candidate
improved, or that any finding is unimportant. Exact result bytes and chronology
remain in the event ledger. The packet receives a reopenable exact receipt.

Older delivered checks may turn over only when the represented check is at
least as recent and has crossed a completed model invocation. Pending checks
and effects cannot turn over.

## Exact boundary projection

| State | Offline tokens | Interpretation |
|---|---:|---|
| Historical pre-terminal E103 packet | 21,301 | Offline projection; live authority was 21,318 |
| Add exact check/result binding to verification slot | 21,522 | Safety binding has a real carrying cost |
| Turn over delivered `RESULT-021` and `RESULT-024` | 20,548 | 444 tokens offline headroom |

If the observed 17-token live-minus-offline delta repeated, the projected
headroom would be 427 tokens. That is not a live qualification; it is a
conservative provider-free projection.

`RESULT-026` remains `pending_exact_body`. Both check results become
`exact_receipt` and remain exactly reopenable.

## Scope discipline

The audit also measured resident phase effects and action rejections. They were
not compacted. Check turnover alone restores projected feasibility, and it has
the strongest exact-duplication proof. Expanding the rule to resolved
rejections or phase history would add policy surface without a demonstrated
need.

The uncorrupted version-007 candidate bytes still exist, while the next sealed
checkpoint already contains the version-008 glued-heading corruption. Because
there is no sealed checkpoint at version 007, the host did not invent one from
artifact bytes alone. The donor-derived fixture route therefore stopped under
its prospective eligibility rule.

A separate provider-free, non-donor fixture exercised the complete host path
through failed current check, repair, passing recheck, and submission. Its two
delivered checks turned over exactly, the final check passed, and submission
completed. This validates mechanics only; it does not establish live Qwen
orientation, repair quality, or closure utility.

## Disposition

Supported:

- the E103 capacity stop was substantially a verification-state residency
  duplication;
- exact, candidate-bound verification state can replace duplicate resident
  check bodies without losing custody or reopenability;
- this prospective rule restores provider-free feasibility at the exact E103
  boundary;
- a complete provider-free check/repair/recheck/closure lifecycle remains
  operable under the rule.

Not supported:

- that live Qwen remains behaviorally oriented after turnover;
- that Qwen will repair the remaining Trellis defects correctly;
- that the projected live packet count is exact;
- that action rejections or phase effects should also be compacted;
- that E103 may be resumed under its frozen authorization.

No GPU or provider call occurred.
