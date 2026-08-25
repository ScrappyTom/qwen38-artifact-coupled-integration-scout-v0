# Bluehaven batched-maintenance expression qualification result

Date: 2026-08-25

Status: complete, sealed, independently audited; qualification failed; frozen
B1 carrier closed; no measured B1/W1 continuation authorized

Frozen commit:
`7051e20b3f46c4100292db5c767482b359362178`

Run ID:
`2026-08-25-bluehaven-batched-maintenance-expression-qualification-v0`

## Literal outcome

Both one-shot provider calls finished normally and stayed below the 2,400-token
admission bound. Their semantic-source dispositions differed:

| Case | Prompt | Completion | Output tokens | Frozen admission |
|---|---:|---:|---:|---|
| Q1 initial S01–S06 batch | 11,238 | 1,058 | 1,057 | rejected |
| Q2 replacement through S12 | 11,436 | 1,274 | 1,273 | accepted |

Q1 cited S07, S08, S09, S10, S11, and S12 despite an exact S01–S06
allowlist. Q2 cited only S01–S12, all allowed, and passed every frozen rule.

The complete run used two model calls and 25,006 serialized tokens. There was
one attempt per call, no retry, no provider/runtime failure, and the GPU/server
was released.

## Why Q1 is a substantive failure

The disallowed references were not only a directory of sources to acquire.
The output attributed task substance to sources absent from the maintenance
packet. Examples include:

- R05 asserted hospital/dialysis and tanker claims under unseen S07/S08;
- R08 asserted multilingual-warning requirements under unseen S10;
- R09 asserted assay and chain-of-custody claims under unseen S09;
- R11 said unseen S11 defined the 72-hour execution sequence even though the
  exact Bluehaven S11 is the workforce source; and
- R12 said unseen S12 supplied independent-review blockers even though exact
  S12 is mutual aid, vendors, routes, and cost authority.

The final two entries reveal a particularly dangerous interaction. The prompt
requires complete entries R01–R12 while supplying only partial exact evidence.
The model appears to have mapped requirement number to same-numbered source and
filled missing sections from task-level cues. That produces fluent,
source-looking state without source custody.

The frozen validator correctly rejected the complete object. Accepting unseen
source IDs merely because some claims resemble the authoritative task would
erase the distinction between task obligations and observed evidence and
would allow incorrect source bindings into exact candidate work.

## What Q2 adds

Q2 shows that the basic Markdown carrier, completion allowance, replacement
operation, and source allowlist are live-expressible once the maintenance
packet covers S01–S12. The gate did not fail because every bounded ledger is
too large or because the runtime cannot emit the format.

It failed at the cold-start interaction:

```text
complete R01–R12 replacement obligation
× partial exact evidence S01–S06
× task-level description of all requirements
× source-like numbering
→ unsupported completion of missing semantic state
```

That is a configuration failure, not a reason to reinterpret Q1 as accepted.

## Disposition

The prospective B1 policy required both initialization and replacement to
qualify. It therefore fails its final pre-measured gate. The B1/W1 comparison
frozen in E53 is ineligible and must not run.

No same-task prompt repair, relaxed source rule, larger token budget, or retry
is selected. A different maintenance trigger—such as waiting for a
prospectively defined evidence-maturity event—would be a new operating policy,
not a repair of B1, and should not be tuned on this observed task/world.

W1 remains conceptually viable but unmeasured. Running it alone would produce
a descriptive trajectory rather than the frozen comparison. The appropriate
next step is program-level systems reconciliation: record partial-evidence
semantic completion as a new interaction hazard, close Bluehaven's measured
fork, and decide whether the next broad scout should compare evidence-mature
semantic transformation with direct exact work on a fresh world.

## Audit

The independent audit verified the exact authorization/freeze identity, screen
handoff, run seal, two provider receipts, prompt recount, output hashes,
recomputed admission decisions, usage arithmetic, and runtime release. It
passes with `qualification_passed: false`; audit validity and treatment success
remain separate.
