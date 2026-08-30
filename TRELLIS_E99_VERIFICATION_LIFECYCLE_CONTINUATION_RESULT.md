# Trellis E99 verification lifecycle continuation — result

Date: 2026-08-30

Frozen apparatus commit:
`97d84493ef72d271410ae590f6ead7e86c2b551a`

Run ID:
`2026-08-30-trellis-e99-verification-lifecycle-continuation-v1`

## Literal result

The authorized continuation completed two actor/provider calls, zero maintenance
calls, and 39,865 additional serialized tokens. Both model responses ended
normally. No retry occurred. The run then stopped before call 27 because the
next exact packet required 21,318 prompt tokens against the 20,992-token
allowance, a 326-token deficit.

The action sequence was:

1. Qwen used the delivered current check to propose a bounded replacement of
   `Authority, scope, and operating states`. The semantic repair was coherent,
   but its expected section hash was stale. The host rejected it without
   changing the candidate and returned the exact current section hash.
2. Qwen repeated the same semantic repair with only the section hash corrected.
   The host admitted it, producing candidate
   `d3a3d3691a254e8d463d98481977070d3e431180541ca5843a23b4c7d880041f`
   and pending effect `RESULT-026`.

`RESULT-026` never crossed a completed model call. No current check of the new
candidate occurred, no submission occurred, and the run is `capacity_blocked`.
The exact run sealed and the model server released.

## Transcript-level qualitative analysis

The behavior remained purposeful rather than recurrent. Qwen read the current
candidate-bound failure report, selected a bounded repair, absorbed an exact
host rejection, and retried with the corrected binding. The second response
preserved the first response's substantive proposal byte for byte. This is a
second clean local example of exact action-feedback uptake.

The proposed text addressed authority, current T9 lineage, historical T8
status, recheck requirements, independent authorized acceptance, rollback
compatibility, open findings, and the prohibition on declaring readiness while
blocking controls remain. It did not attempt premature submission.

The accepted mutation nevertheless made the artifact structurally worse for
two apparatus reasons:

- the donor candidate already contained a heat heading glued to the final
  authority sentence because the prior section replacement had no trailing
  newline;
- `replace_artifact_section` identified sections only from headings beginning
  on their own physical line and did not materialize a safe boundary after the
  replacement.

Consequently, the authority span mechanically included the hidden heat section.
Replacing it deleted that section, and the new replacement then glued the power
heading to its final sentence. The final artifact has only four mechanically
recognized level-two headings. This is not a semantic choice by Qwen to remove
the heat section; it is a host mutation-boundary failure induced by otherwise
valid section-sized work.

## Artifact and evaluator disposition

The frozen external evaluation remains the literal run judgment:

- 871 words;
- 8 cited decision sources;
- exact heading contract failed;
- `T01_authority` passed;
- `T02` through `T08` were reported failing;
- readiness `not_ready`.

The frozen T08 judgment contains a separate evaluator-contract defect. Its
written expected relation is "independent authorized acceptance required," and
the candidate contains that relation, but the regex accepted only the opposite
word order. A prospective evaluator correction accepts both natural orders.
Under that corrected offline diagnostic, T08 passes; T02 through T07 and the
structural/length/source-breadth criteria still fail. This correction does not
turn the run into useful completion.

Relative to the checkpoint candidate, the continuation therefore achieved no
net artifact-quality gain. It demonstrated coherent check-to-repair behavior,
then corrupted the exact artifact through a host boundary defect before a
current recheck could occur.

## Capacity interpretation

The stop was not caused by the authorized economic limits. Ten actor calls and
298,937 serialized tokens remained. The next packet was only 326 prompt tokens
over allowance.

E97 had already compacted delivered applied construction actions and effects,
but the verification packet still carried exact resident bodies for:

- the verification phase effect;
- two candidate-bound checks;
- two section-version rejection receipts;
- the complete current candidate;
- and the newly pending exact candidate effect.

The new effect had to remain exact until delivery. The older check and rejection
objects were not eligible for the construction-era relief policy. The result is
a new, narrow failure migration: applied mutation history was bounded, but one
repair cycle rebuilt enough verification chronology to block delivery of the
next effect.

## Prospective apparatus corrections

After sealing the run, two offline-only corrections were made for future
experiments:

1. section replacement now canonicalizes the blank-line boundary before a
   successor heading and records whether it did so;
2. replacement refuses to operate when the selected bytes already contain a
   glued hidden heading, preventing a malformed legacy artifact from losing a
   successor section;
3. the Trellis T08 evaluator pattern now accepts both "authorized acceptance"
   and "acceptance by an authorized owner."

These changes are prospective. They do not rewrite candidate v009, the frozen
evaluation, or the sealed run.

The prospective changes pass 324 repository tests and targeted Ruff checks.
Targeted Mypy also reports two pre-existing nullable-field errors in
`reactive_runtime/records.py`; neither is in the changed section/evaluator path
and no unrelated typing repair was folded into this result.

## Scientific disposition

Supported locally:

- current check information can drive a semantically targeted repair;
- exact section-hash rejection can be used on the immediately following call;
- Qwen did not loop or close prematurely in this tranche;
- the verification lifecycle can again become capacity-bound after one repair.

Not supported:

- artifact improvement in this continuation;
- current effect uptake after the accepted repair;
- current recheck, additional repair, readiness, or closure;
- semantic redundancy of old verification observations;
- a general verification-history compaction policy.

The sealed continuation is closed. It must not be resumed from its structurally
corrupted candidate. The next work is an offline verification-residency and
mutation-boundary reconciliation, not another GPU continuation or a receipt
format tweak.
