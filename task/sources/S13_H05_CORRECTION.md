# H05 artifact-disposition reconciliation

Date: 2026-08-22

## Finding

The H05 raw behavioral contrast is valid, but its original artifact disposition
was wrong.

The treated actor submitted candidate ID
`38893b4df5afc252a356ff5ab79a1dcda6330b7934a252a67d2759499eb4aac6`,
file SHA-256
`888c142abcad4c3bd9081960bdb18b7402be6415c03b456033ed3c7aed134d39`.
Those exact bytes had already been audited at construction-reentry donor commit
`68a4b0b04c4557dcc459b42822e804f241565757` as a **strong partial** artifact.

The prior frozen table contained 12 substantive requirement groups:

- 10 met;
- apparatus-correction coverage partial; and
- factual precision about the timing of 11 seed-42 reopens partial.

The candidate also satisfied the separate file-scope constraint. It was not a
complete task artifact.

## Corrected H05 interpretation

The literal sequence remains:

```text
byte-identical control
-> resident candidate reread

169-token progress state in 464-token package
-> admitted submit
-> unchanged strong-partial candidate
```

The package was behaviorally active. Its trajectory utility was negative at
this defect-bearing boundary because it induced closure without identifying or
repairing either known partial requirement.

This is the first direct not-ready discrimination result for H05. It is
consistent with a recent self-authored closure cue and does not establish safe
progress reconciliation.

## Error classification

The H05 post-run review checked headline facts at a coarser granularity and did
not reconcile the candidate hash against the existing frozen adjudication. The
error is investigator-side artifact classification. It does not invalidate:

- the three model calls;
- literal actions and results;
- candidate custody;
- tokenizer receipts;
- replay;
- tests; or
- run seals.

The standalone correction is published at commit
`a3422cca49cb882ec252ba84903b856ba3cafc24`.

## Governance rule

Future control/progress utility experiments must freeze an independent
candidate-readiness adjudication before maintenance output or treated actor
behavior is observed. Candidate hashes must be reconciled against every prior
adjudication in the donor lineage. Submission is positive only when that frozen
adjudication says closure is appropriate.
