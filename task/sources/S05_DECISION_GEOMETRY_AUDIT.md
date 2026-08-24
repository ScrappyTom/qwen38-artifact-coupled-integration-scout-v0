# E36 Decision-Geometry Audit

Status: offline, read-only reconstruction

This document reconstructs the decision-level information and action geometry
of the E36 seed-314159 v2 pressure-recovery trajectory. It separates exact
mechanical facts from weaker evidence-availability proxies and semantic
interpretation.

It does not alter or reinterpret the sealed run.

## Exact bindings and evidence base

- Experiment repository: `E:\qwen38-pressure-qualified-lifecycle-scout-v1`
- Audited result commit: `e4dcd58fa554e7e36b99e6cb454803cd099d2044`
- Live v2 freeze commit: `9d14cfc674ca307880621035c8ba20933fdbaf27`
- V2 run:
  `runs/2026-08-23-measured-first-fit-continuation-seed-314159-v2`
- Donor run:
  `runs/2026-08-23-authentic-pressure-screen-seed-271828-v0`

The row-level reconstruction uses the v2 run's:

- `CALL_TRACE.json`
- `RESULT_LEDGER.json`
- `LIFECYCLE_EVENTS.json`
- `FINAL_MESSAGES.json`
- `CELL_RESULT.json`
- per-call `LEDGER_AT_CALL_START.json`
- per-call `VISIBILITY_AT_CALL_START.json`
- per-call `TRANSITION.json`
- per-call `PROMPT_RECEIPT.json`
- per-call `assistant_content.txt`

Task and evidence-obligation mappings come only from:

- `task/TASK.md`
- `task/SOURCE_CATALOG.json`
- `task/EVALUATOR.json`

The donor calls were generated under screen seed `271828`. The separately
authorized continuation starts from that exact model-facing boundary and uses
seed `314159`. Continuation calls 1–18 are absolute calls 5–22.

## Global mechanical facts

- The source catalog and bounded access to `S01` through `S14` remained
  actor-visible throughout. Which bytes the actor requested and received was
  endogenous.
- `reopen_exact` remained available for previously visible, externalized
  exact results.
- The candidate was exact-resident and byte-identical at every decision:
  58 bytes, 9 words, SHA-256
  `b4b7c78af1e8d395a2c4ccfe0150e545c892c9835afc5d26445bda29c468fea3`.
- No mutation, check, submission, candidate effect, or effect-uptake event
  occurred.
- Each receipt retained result and source identity, source path, exact observed
  range, hashes, sizes, and an exact reopen action. Together with the permanent
  catalog, receipts also retained coarse title/role metadata. They contained no
  model-authored conclusion or content-bearing semantic digest.
- The only persisted model outputs were short action objects. No reasoning
  trace or durable model-authored interpretation exists.
- At most three exact source-result bodies were resident together at a
  continuation call start.

Notation in the tables abbreviates split sources: for example, `S03a` means
lines 1–240 and `S03b` means lines 241–312. `R#` in the receipts column is the
number of external-result receipts resident at the call start. Relief occurs
after the listed action, while constructing the next selected packet.

## Donor prefix

| Absolute call | Prompt tokens | Newly visible / exact bodies at start | Literal action | Next-packet consequence |
|---:|---:|---|---|---|
| 1 | 3,832 | none / none | read `S01` lines 1–94 | Exact result fits; next prompt is 5,889 tokens. |
| 2 | 5,889 | `S01` / `S01` | read `S02` lines 1–235 | Exact result fits; next prompt is 14,034 tokens. |
| 3 | 14,034 | `S02` / `S01`, `S02` | attempt `S03` lines 1–312 | Rejected because the 312-line request exceeds the 240-line limit; exact rejection enters call 4. |
| 4 | 14,172 | call-3 rejection / `S01`, `S02` | read `S03a` | Ordinary next prompt is 21,442 tokens, 450 above the 20,992-token allowance. Externalize `RESULT-001` / `S01`; the selected first-fit packet is 19,818 tokens. The later v2 authorization supplies 18 continuation decisions. |

## Seed-314159 v2 continuation geometry

| Continuation / absolute call | Prompt tokens | Newly visible at call start | Exact bodies resident at start | Receipts | Literal action | Relief and selected next prompt | Decisions left |
|---:|---:|---|---|---:|---|---|---:|
| 1 / 5 | 19,818 | `RESULT-004` / `S03a` | `S02`, `S03a` | 1 | read `S03b` | Externalize `RESULT-002` / `S02`; 15,442 tokens. | 17 |
| 2 / 6 | 15,442 | `RESULT-005` / `S03b` | `S03a`, `S03b` | 2 | read full `S05` | Externalize `RESULT-004` / `S03a`; 15,085 tokens. | 16 |
| 3 / 7 | 15,085 | `RESULT-006` / `S05` | `S03b`, `S05` | 3 | read `S06a` | No relief; 20,172 tokens. | 15 |
| 4 / 8 | 20,172 | `RESULT-007` / `S06a` | `S03b`, `S05`, `S06a` | 3 | read `S06b` | Externalize `RESULT-005` / `S03b` and `RESULT-006` / `S05`; 15,549 tokens. | 14 |
| 5 / 9 | 15,549 | `RESULT-008` / `S06b` | `S06a`, `S06b` | 5 | attempt `S04` lines 1–282 | Rejected because the range exceeds 240 lines; 15,687 tokens. | 13 |
| 6 / 10 | 15,687 | call-9 rejection | `S06a`, `S06b` | 5 | read `S04a` | Externalize `RESULT-007` / `S06a`; 18,183 tokens. | 12 |
| 7 / 11 | 18,183 | `RESULT-010` / `S04a` | `S06b`, `S04a` | 6 | read `S04b` | No relief; 19,574 tokens. | 11 |
| 8 / 12 | 19,574 | `RESULT-011` / `S04b` | `S06b`, `S04a`, `S04b` | 6 | read `S07a` | Externalize `RESULT-008` / `S06b` and `RESULT-010` / `S04a`; 15,034 tokens. | 10 |
| 9 / 13 | 15,034 | `RESULT-012` / `S07a` | `S04b`, `S07a` | 8 | read `S07b` | No relief; 17,533 tokens. | 9 |
| 10 / 14 | 17,533 | `RESULT-013` / `S07b` | `S04b`, `S07a`, `S07b` | 8 | read `S08a` | Externalize `RESULT-011` / `S04b` and `RESULT-012` / `S07a`; 18,472 tokens. | 8 |
| 11 / 15 | 18,472 | `RESULT-014` / `S08a` | `S07b`, `S08a` | 10 | read `S08b` | No relief; 19,887 tokens. | 7 |
| 12 / 16 | 19,887 | `RESULT-015` / `S08b` | `S07b`, `S08a`, `S08b` | 10 | read full `S09` | Externalize `RESULT-013` / `S07b` and `RESULT-014` / `S08a`; 19,301 tokens. | 6 |
| 13 / 17 | 19,301 | `RESULT-016` / `S09` | `S08b`, `S09` | 12 | attempt `S10` lines 1–251 | Rejected because the range exceeds 240 lines; 19,440 tokens. | 5 |
| 14 / 18 | 19,440 | call-17 rejection | `S08b`, `S09` | 12 | read `S10a` | Externalize `RESULT-015` / `S08b` and `RESULT-016` / `S09`; 19,708 tokens. | 4 |
| 15 / 19 | 19,708 | `RESULT-018` / `S10a` | `S10a` | 14 | read `S10b` | No relief; 20,413 tokens. | 3 |
| 16 / 20 | 20,413 | `RESULT-019` / `S10b` | `S10a`, `S10b` | 14 | read `S11a` | Externalize `RESULT-018` / `S10a`; 19,433 tokens. | 2 |
| 17 / 21 | 19,433 | `RESULT-020` / `S11a` | `S10b`, `S11a` | 15 | read `S11b` | No relief; 19,793 tokens. | 1 |
| 18 / 22 | 19,793 | `RESULT-021` / `S11b` | `S10b`, `S11a`, `S11b` | 15 | read `S12a` | Ordinary packet is 24,190 tokens. Externalize `RESULT-019` / `S10b` and `RESULT-020` / `S11a`; selected packet is 16,360 tokens. No call remains. | 0 |

## Exact endpoint state

By absolute call 22, the actor had temporally received every byte of `S01`
through `S11`: 18 exact result bodies totaling 322,887 wrapped-result bytes,
of which 312,865 bytes were source slices.

At call 22 the actor saw `S10b` and all of `S11` exactly and requested `S12a`.
The host acquired `RESULT-022`, containing `S12` lines 1–240, and selected it
into a feasible next packet. Because no subsequent model invocation occurred,
that result never crossed a model boundary.

After the final selection:

- 17 prior visible results would be receipts;
- `RESULT-021` / `S11b` would remain exact;
- `RESULT-022` / `S12a` would be exact and pending.

That selected packet is not an observed model state.

The remaining evidence state was:

- `S12` lines 1–240: acquired but model-unseen;
- `S12` lines 241–519: unacquired;
- all of `S13`: unacquired;
- all of `S14`: unacquired.

`S12` and `S14` were specifically required by the task. `S13` was not itself
mandatory once prior-art breadth was otherwise met.

## Artifact obligations versus evidence availability

The artifact disposition is invariant and should not be confused with evidence
exposure. Since the candidate bytes never changed, every call retained the same
state:

- all 16 evaluator criteria `not_met`;
- all required headings absent;
- zero citations;
- 9 words rather than the required 1,800–2,000;
- closure `not_ready`.

No artifact obligation became satisfied merely because a source was read.

The following table is a weaker diagnostic only. “Cumulative” means at least
one source from every evaluator-declared source group had crossed some prior
model boundary. “Exact co-resident” means those source groups had matching
exact ranges resident together at one call. Neither condition proves semantic
adequacy, comprehension, or a correct section.

| Evaluator area | First cumulative proxy | First exact co-resident proxy | Qualification |
|---|---:|---:|---|
| C01 decision scope | 2 | 2 | `S01` alone satisfies the evaluator's broad source group. |
| C02 evidence status | 2 | 2 | `S01` alone satisfies the broad source group. |
| C03 verified strengths | 5 | 5 | `S02` and `S03a` were exact together. |
| C04 capability limits | 7 | 7 | `S05` was exact. |
| C05 prompt/observation pressure | 21 | never | Earlier `S02`/`S06` and later `S11a` were never exact together. |
| C06 structured-output nuance | never | never | Model-visible `S12` or `S14` was absent. |
| C07 model/quantization | never | never | Model-visible `S12` and `S14` were absent. |
| C08 neutrality and safety | 11 | never | `S04` was never exact together with `S03` or `S05`. |
| C09 prior-art boundary | 15 | never | A prior-art source became visible after `S02`/`S03` had become receipts. The three-source section breadth was only cumulative. |
| C10 planner/control simplification | 8 | 8 | `S03b` and `S06a` were exact together. |
| C11 maintainability | 13 | 13 | `S07a` was exact. |
| C12 ordered plan | 13 | never | Four evaluator-listed plan sources had cumulatively appeared, but four were never exact-resident together. |
| C13 measurable gates | 7 | 7 | `S05` was exact. |
| C14 rollback and stop | 7 | 7 | `S05` was exact. |
| C16 non-goals and uncertainty | 7 | 7 | `S05` was exact. |

C15 citation breadth remained impossible at the endpoint despite eleven
distinct model-visible source IDs: required `S12` and `S14` had not crossed a
model boundary.

The central cross-source distinction is therefore:

- exact co-residency supported a few local evaluator source pairings, notably
  C03 at call 5 and C10 at call 8;
- several other relationships became available only in the weaker sense that
  their sources had appeared at different earlier decisions and were later
  represented mainly by receipts.

## First possible partial-work points

These are opportunities in the mechanical action/evidence geometry, not claims
that the actor should have acted or that the evidence was semantically
sufficient.

1. **Absolute call 2 — earliest technically source-grounded update.** `S01`
   was fully exact-resident and could support a document skeleton plus
   provisional scope or evidence-status material. It could not support a
   remotely complete charter.
2. **Absolute call 5 — first exact cross-source partial-section opportunity.**
   `S02` and `S03a` were exact together and matched the evaluator's two-group
   evidence proxy for “What to keep.”
3. **Absolute call 8 — strongest early thematic checkpoint.** `S03b`, `S05`,
   and `S06a` were exact together. They could potentially support bounded
   planner, capability, root-cause, or runtime material and met the C10 source
   proxy.
4. **Absolute call 13 — first broad cumulative checkpoint.** Four
   evaluator-listed plan sources had appeared, and cumulative source exposure
   covered broad prerequisites for scope, evidence status, strengths, limits,
   runtime, neutrality, maintainability, gates, rollback, and uncertainty.
   Only `S04b` and `S07a` were exact at that moment; earlier substance had no
   durable model-authored residue.
5. **Absolute calls 15 and 21 — later relationship checkpoints.** At call 15,
   prior-art versus Ceiba material was cumulatively available. At call 21,
   benchmark material made the prompt/observation relation cumulatively
   available. The relevant sides of either relation were never all exact
   together.
6. **No complete-work checkpoint occurred.** `S12` and `S14` remained absent
   from model-visible evidence. At the endpoint, the shortest optimistic path
   still required at least receiving `S12` and requesting `S14`, receiving
   `S14` and mutating, and receiving the effect before closure. Checking or
   repair would require additional decisions.

## Partial-work action-surface qualification

`replace_charter` was available at every actor call. Its live schema and
executor mechanically accepted any changed, nonempty whole-file content up to
250,000 UTF-8 bytes; evaluator completeness was not a mutation precondition.

However, the actor instruction said that `content` must contain the complete
Markdown document, “not a patch or excerpt.” There was no section-patch,
evidence-matrix, note, or intermediate-artifact action. Partial work therefore
could be externalized only by replacing the entire candidate with an incomplete
draft. This was mechanically possible but ergonomically and linguistically
discouraged. The audit does not claim the actor should have selected it.

## Fact and inference boundary

The following are mechanical facts:

- literal actions and rejection receipts;
- exact prompt-token counts;
- result acquisition and visibility;
- exact-resident and external-receipt status;
- pressure substitutions and selected next packets;
- candidate identity and lack of effects;
- remaining call budget;
- final evaluator disposition.

The following are explicitly weaker inferences or proxies:

- that a source set “could support” a section;
- that a call was a construction opportunity;
- that evaluator source-group availability implies semantic sufficiency;
- that cumulative exposure preserved usable understanding;
- that lack of a reopen implies durable continuity.

No reasoning trace exists. This audit therefore cannot establish forgetting,
successful digestion, intent to defer construction, or that any acquisition
was unnecessary.

The absence of a reopen during acquisition does not establish semantic
continuity. Demand for earlier material could arise only after synthesis began.

The result also does not establish a deadlock or predict whether another fixed
number of calls would succeed. Mandatory evidence remained incomplete and the
actor was traversing novel source ranges.

The two executed seed variants share one donor state. Their identical literal
trajectories are local seed consistency, not independent-world replication.

Finally, the measured outcome belongs to the whole configuration:

- one bounded read per action;
- one action per response;
- receipt-only persistence for old exact content;
- no durable semantic or work-product residue;
- whole-file-only mutation;
- an 18-call continuation ceiling.

This audit cannot identify any one of those elements as the sole cause of the
observed acquisition-only horizon.
