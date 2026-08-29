# Trellis E97 verification-lifecycle call-level qualitative review

Date: 2026-08-29

Run:
`2026-08-29-trellis-e97-verification-lifecycle-scout-v0`

This review covers every new actor turn. It separates literal visibility and
state transitions from inferred demand. The sealed requests, responses,
checkpoint, evaluator output, and candidate versions remain authoritative.

## Starting boundary

The imported state contained the exact 904-word five-section candidate, exact
evidence ledger, frozen temporary scaffold, compact receipts for five delivered
applied mutation pairs, and exact pending `RESULT-018`. The donor was frozen
`not_ready` before live behavior. The live tokenizer measured 19,128 tokens,
twelve above the offline projection but within the 20,992-token allowance.

## Call-by-call account

| Absolute call | What was visible | Literal action/output | Durable state change | Qualitative interpretation |
|---:|---|---|---|---|
| 19 | Exact current five-section candidate; evidence ledger; temporary scaffold; compact applied history; exact pending `RESULT-018`; current-effect binding | Normally stopped 378-token `upsert_decision_section` for `Execution, rollback, verification, and closure` | Candidate v007, SHA `8a7a6e…`; exact sixth heading; +241 words; `RESULT-019` pending | Strong local orientation. The pending effect was usable and the actor chose the missing bounded work unit rather than reopening evidence or replacing the whole document. The new section concentrated on lineage, rollback, unresolved review findings, and non-self-authorization. |
| 20 | Updated exact candidate; `RESULT-019` effect; current-effect binding; prior applied history eligible for E97 compaction | Normally stopped seven-token `begin_verification` | Verification phase entered; `RESULT-020` pending; scaffold demoted | The actor recognized construction structure as sufficient to seek feedback. This is a progress transition, not a readiness judgment. No check was run by this action. |
| 21 | Exact current candidate; delivered verification-phase effect; verification frame with `check_binding: null`; demoted scaffold; no declared `run_check` or repair action contract | 4,096-token length stop. Raw text began as undeclared `replace_artifact_section`, embedded the complete document, and repeated the final section heading six times | No candidate change; exact response rejection scheduled | The model attempted repair without current diagnostic evidence and without a declared verification action grammar. Its output shape was economically impossible and semantically degenerative. This is behavior under a malformed interface, not a test of response to a check. |
| 22 | Same candidate and verification frame; call-21 rejection notice; full 18,963-character rejected assistant output still resident | 4,096-token length stop. The first 18,963 characters were byte-identical to call 21, followed by six additional characters | No candidate change; second exact response rejection scheduled | The compact rejection notice did not redirect behavior. The resident failed output and fixed-seed trajectory supported exact recurrence rather than correction. |
| 23 prospective | Same exact world plus both full rejected responses and rejection notices | No provider call; rendered packet 23,811 tokens | Terminal `capacity_blocked` | The terminal resource was rejected-output chronology. E97 had already removed the old applied-action/effect duplication it was designed to remove. |

## Candidate incorporation and loss

The only admitted live artifact change was call 19. It correctly added the
missing heading and carried forward source-bound lineage and review material.
It did not restore the governing relations lost during earlier scaffold
replacement. The independent checkpoint evaluation therefore moved only the
heading/length surface:

- decision words: 904 → 1,145;
- required ordered headings: five of six → six of six;
- distinct decision sources: eight → eight;
- substantive groups T01–T08 met: zero → zero;
- readiness: `not_ready` → `not_ready`.

The two later drafts incorporated no durable information because neither
crossed action admission. Their repeated whole-document content therefore
consumed response and prompt capacity without changing the artifact.

## Demand shifts

The first two turns show a useful demand shift:

```text
pending construction effect
    → fill missing exact section
    → enter verification
```

The next shift was not a valid verification loop:

```text
phase entered, but no check or action contract
    → infer a global repair from current artifact alone
    → truncate
    → receive rejection while failed draft stays resident
    → reproduce the failed draft exactly
```

This distinguishes task demand from interface-induced demand. The actor wanted
to revise the artifact, but the host did not give it the bounded executable
language required for verification and repair.

## System-level findings

1. **E97 was behaviorally enabling at this boundary.** It admitted the first
   call, delivered the pending effect, supported one new exact mutation, and
   allowed phase entry.
2. **Artifact-centered continuity remained useful.** Qwen worked directly on
   the exact current candidate and did not reopen raw sources.
3. **The actor-facing lifecycle was incomplete.** Internal adapter support for
   checks and repairs is not enough; the model must see the exact phase-valid
   action contract.
4. **Rejected outputs need their own residency lifecycle.** Exact custody does
   not require indefinite prompt residency of a response that was rejected and
   caused no world transition.
5. **The repair behavior is not yet a capability verdict.** Qwen never received
   a current check. Its oversized recurrence is a valid local transport/control
   failure under the observed interface, not evidence that it cannot repair
   candidate-bound defects.

## Required next gate

Before another live call, provider-free qualification must render and inspect
the actual request at each lifecycle phase. A scripted action counts as
reachable only when that action is explicitly declared in the actor-visible
request that precedes it. Rejected-response compaction must preserve exact raw
custody, hash, finish reason, candidate binding, and rejection cause while
removing the unadmitted body from ordinary prompt residency.

The sealed v0 checkpoint is terminal and will not be resumed under repaired
code.
