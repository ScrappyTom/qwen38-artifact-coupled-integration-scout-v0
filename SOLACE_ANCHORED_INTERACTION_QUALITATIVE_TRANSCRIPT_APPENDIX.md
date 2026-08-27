# Solace anchored-interaction qualitative transcript appendix

This appendix examines the sealed run at committed result `353c059b31c94dc5951e727b1a2cfa0bba51b6b8`. It does not alter the sealed run, score, or result claims. `Mechanical fact` is limited to transcript/candidate/register/evaluation evidence. `Direct semantic judgment` is a reading of visible emitted or admitted content; it never turns an unadmitted draft into an artifact. `Inference` is a clearly qualified causal/demand interpretation, with alternatives and confidence. The machine-readable companion is [SOLACE_ANCHORED_INTERACTION_CALL_LEDGER.json](SOLACE_ANCHORED_INTERACTION_CALL_LEDGER.json).

## Reading rules

- **Exact** means source/result material exposed to the actor before a call. **Receipt** means a result handle/reopenable exact result. **Register** means the L1 non-authoritative anchored register; W0 has none. **Artifact** means the candidate ledger/decision version visible before a call.
- `admitted` describes a recorded candidate or register transition, not whether the proposition is true. `unadmitted` means the provider output did not parse/admit and did not change the candidate.
- “Demand” is a description of the next observable task pressure, not a claim about hidden model reasoning. All paths for prompts, messages, output and result records are in the companion ledger.

## Exact-residency and lifecycle order

The rows below are the authoritative pre-call visibility sequence from each sealed `LIFECYCLE.json`; a receipt is not an exact body. The machine-readable form is `visibility_sequence` and `lifecycle_order` in the companion ledger.

| Actor turn | Exact bodies visible before actor call | Receipts visible before actor call | Register / candidate version |
|---|---|---|---|
| W0 A01–A18 | A01: R2–R6; A02: R3–R7; A03: R4–R7; A04: R1,R5–R7; A05: R1,R2,R6,R7; A06: R1–R3,R7; A07: R2–R4; A08: R3–R5; A09: R4–R6; A10: R5–R7; A11: R1,R6,R7; A12: R1,R2,R7; A13: R1–R3; A14: R2–R4; A15: R4,R5; A16: R5,R6; A17: R6,R7; A18: R7. | Every other R1–R7 receipt for that turn. | No register. v000 before A01; v001 after A02 through A18. |
| L1 A01 | R2–R6 | R1 | 6 claims; v000 |
| L1 A02 | R4–R7 | R1–R3 | 13 claims; v000 |
| L1 A03 | R6,R7 | R1–R5 | 20 claims; v001 |
| L1 A04–A07 | R7 | R1–R6 | 20 claims; v002, v003, v004, v005 respectively |
| L1 A08–A09 | none | R1–R7 | 20 claims; v006, v007 respectively |

L1 event order is `R1 → M1 → A1 → R2 → M2 → R3 → M3 → A2 → R4 → M4 → R5 → M5 → A3 → R6 → M6 → A4 → A5 → A6 → A7 → R7 → M7 → A8 → A9 → terminal relief failure`.

## W0 actor turns

| Turn | Mechanical fact: pre-call visibility and literal action/output | Direct semantic judgment: admitted state, artifact incorporation/loss | Inference: subsequent demand / likely shift (alternatives; confidence) |
|---|---|---|---|
| W0-A01 | Exact R2–R6; receipt R1; no register; artifact v000. MOSAIC/NEXUS had not yet been delivered. Action: `read_batch` MOSAIC/NEXUS. Output: `RESULT-007`. | Observation only; no candidate mutation. It exposes lineage/readiness material, not a decision. | Demand remained evidence-to-decision construction. Could be routine first-fit navigation or deliberate currentness preparation (low). |
| W0-A02 | Exact R3–R7; receipts R1–R2; no register; artifact v000. Action: replace ledger with a fourteen-source matrix. Output `RESULT-008`; v001 manifest records the change. | Admitted ledger incorporates relationships, units, blockers and staleness across all fourteen sources; the decision stays the placeholder. | The unmet demand is decision construction, with ledger refinement as an alternative (high). |
| W0-A03 | Receipt `RESULT-001`; ledger v001; no register. Action/output: reopen exact 001 → `RESULT-009`. | Observation only; AURORA/BASTION were already represented in ledger, no artifact addition. | Start of a repeat fault-in pattern; alternatively a verification reread (medium). |
| W0-A04 | Receipt `RESULT-002`; ledger v001; no register. Reopen 002 → `RESULT-010`. | Observation only; CIPHER/DELTA re-exposed, no artifact addition. | Continued fault-in; alternatively targeted draft preparation (medium). |
| W0-A05 | Receipt `RESULT-003`; ledger v001; no register. Reopen 003 → `RESULT-011`. | Observation only; ECHO/FALCON re-exposed, no artifact addition. | Continued fault-in; alternatively targeted draft preparation (medium). |
| W0-A06 | Receipt `RESULT-004`; ledger v001; no register. Reopen 004 → `RESULT-012`. | Observation only; GARNET/HELIX re-exposed, no artifact addition. | Continued fault-in; alternatively targeted draft preparation (medium). |
| W0-A07 | Receipt `RESULT-005`; ledger v001; no register. Reopen 005 → `RESULT-013`. | Observation only; INDIGO/JASPER re-exposed, no artifact addition. | Continued fault-in; alternatively targeted draft preparation (medium). |
| W0-A08 | Receipt `RESULT-006`; ledger v001; no register. Reopen 006 → `RESULT-014`. | Observation only; KESTREL/LUMEN re-exposed, no artifact addition. | Continued fault-in; alternatively targeted draft preparation (medium). |
| W0-A09 | Receipt `RESULT-007`; ledger v001; no register. Reopen 007 → `RESULT-015`. | Observation only; MOSAIC/NEXUS re-exposed, no artifact addition. | First seven-result pass completed; alternatively preparing a global draft (medium). |
| W0-A10 | Receipt `RESULT-001` again; ledger v001; no register. Reopen 001 → `RESULT-016`. | Second AURORA/BASTION exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A11 | Receipt `RESULT-002` again; ledger v001; no register. Reopen 002 → `RESULT-017`. | Second CIPHER/DELTA exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A12 | Receipt `RESULT-003` again; ledger v001; no register. Reopen 003 → `RESULT-018`. | Second ECHO/FALCON exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A13 | Receipt `RESULT-004` again; ledger v001; no register. Reopen 004 → `RESULT-019`. | Second GARNET/HELIX exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A14 | Receipt `RESULT-005` again; ledger v001; no register. Reopen 005 → `RESULT-020`. | Second INDIGO/JASPER exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A15 | Receipt `RESULT-006` again; ledger v001; no register. Reopen 006 → `RESULT-021`. | Second KESTREL/LUMEN exposure; no candidate effect. | Repetition rather than incremental construction; alternatively ledger verification (high). |
| W0-A16 | Receipt `RESULT-007` again; ledger v001; no register. Reopen 007 → `RESULT-022`. | Second MOSAIC/NEXUS exposure; no candidate effect. | Second exact pass exhausted immediately before drafting; alternatively final verification (high). |
| W0-A17 | Exact R6–R7; receipts R1–R5; ledger v001; decision placeholder; no register. Output begins `replace_decision` with a detailed global decision, but ends at the 4096 completion-token limit and `RESULT.json` records `invalid_json`, no result ID. | **Unadmitted**. The visible draft broadly covers authority, hydraulics, sampling, power/resources, treatment, source, security, telemetry, environment, public continuity and currentness; its text cannot be treated as incorporated or readiness evidence. | Observable shift: exact reopening → complete replacement draft. Alternatives: one-off output overrun or formatting failure without stable construction intent (high for shift; no claim of hidden intent). |
| W0-A18 | Exact R7; receipts R1–R6; pre-call sees W0-A17’s `invalid_json` rejection; same ledger/placeholder/no-register state. Output is another, shorter/differently formatted global `replace_decision`; it again ends at 4096 and is invalid JSON. | **Unadmitted** retry. It retains broad cross-domain content and changes compactness/format after the prior rejection, but changes no candidate bytes. | Observable 17→18 adaptation supports a representation × construction-granularity/action-transport bottleneck. Alternatives: independently sampled similar drafts, or rejection was not causally used (medium). |

## L1 actor turns

| Turn | Mechanical fact: pre-call visibility and literal action/output | Direct semantic judgment: admitted state, artifact incorporation/loss | Inference: subsequent demand / likely shift (alternatives; confidence) |
|---|---|---|---|
| L1-A01 | Exact R2–R6; receipt R1; six-claim register; v000. Same `read_batch` MOSAIC/NEXUS action → `RESULT-007`. | Observation only. Its distinct semantic consequence occurs through M1, which was already complete before this call. | Routine navigation or currentness preparation (low). |
| L1-A02 | Exact R4–R7; receipts R1–R3; 13-claim register; v000. Replaces ledger → `RESULT-008`, v001. | Admitted fourteen-source ledger with structured values/distinctions; decision remains placeholder. | Incremental decision construction becomes a plausible next demand; more externalization remains an alternative (medium). |
| L1-A03 | Exact R6,R7; receipts R1–R5; 20-claim register; v001. Upserts `Authority, scope, and restoration decision` → `RESULT-009`, v002. | Admitted authority/currentness/rollback text; no self-authorized readiness claim. | Section-sized construction selected; prompt framing alone is an alternative cause (medium). |
| L1-A04 | Exact R7; receipts R1–R6; 20-claim register; v002. Upserts `Hydraulics, storage, and zone sequencing` → `RESULT-010`, v003. | Admitted pressure/storage/isolation/telemetry and staleness content. | Section-size action lowers transport demand versus W0 global replacement; content-fit alone is an alternative (medium). |
| L1-A05 | Exact R7; receipts R1–R6; 20-claim register; v003. Upserts `Sampling, source water, and treatment barriers` → `RESULT-011`, v004. | Admitted CIPHER/GARNET/treatment relationships and distinctions. | Register/ledger may support local source-linked drafting; direct prompt retention is an alternative (medium). |
| L1-A06 | Exact R7; receipts R1–R6; 20-claim register; v004. Upserts `Power, pumping, logistics, and demand stages` → `RESULT-012`, v005. | Admitted power/fuel/logistics material, including an explicit negation of the 36-days reversal. | Construction continues after register saturation; section self-containment is an alternative (medium). |
| L1-A07 | Exact R7; receipts R1–R6; 20-claim register; v005. Upserts the same power/pumping heading using treatment text → `RESULT-013`, v006. | Treatment text is incorporated, but repeated heading use is a visible structural loss that contributes to final heading-contract failure. | Demand may shift to remaining structure/consolidation; intentional topic merge is an alternative (medium). |
| L1-A08 | No exact bodies; receipts R1–R7; 20-claim register; v006. Upserts that same heading using security/telemetry text → `RESULT-014`, v007. | Security/telemetry is incorporated; declared heading structure remains incomplete. | A global consolidation is plausible; continuing local edits is an alternative (medium). |
| L1-A09 | No exact bodies; receipts R1–R7; 20-claim register; v007. Replaces decision globally → `RESULT-015`, v008. | Admitted 1,934-word/twelve-source strong partial. Direct adjudication records Q02, Q03, Q04 and Q09 partial; Q10 is **met** after reconciliation of the mechanical surface-form miss. The eight-heading contract fails; it is not ready and no check/repair/recheck follows. | Consolidation left no lifecycle budget for verification/repair/recheck; unrelated action selection is an alternative (high). |

## L1 maintenance turns

| Turn | Mechanical fact: pre-call visibility and literal action/output | Direct semantic judgment: register/artifact incorporation or loss | Inference: subsequent demand / likely shift (alternatives; confidence) |
|---|---|---|---|
| L1-M01 | `RESULT-001`; empty register; v000. Trigger: `positive_savings_externalization`; maintenance emits AURORA/BASTION delta. | Six anchored claims fully admitted, register 0→6. They are explicitly non-authoritative derivatives. | Could reduce reopening need for these details; register might not be used (medium). |
| L1-M02 | `RESULT-002`; register 6; v000. Emits CIPHER/DELTA delta. | CIPHER-01..03 admitted, DELTA-01..04 rejected; register 6→9. Pumping facts are selected out despite anchored emitted claims. | Q04 may rely on ledger/exact context; rejection policy or capacity strategy is an alternative (medium). |
| L1-M03 | `RESULT-003`; register 9; v001. Emits ECHO/FALCON delta. | Four claims fully admitted, register 9→13; numerical distinctions persist. | May support Q05/Q06 local drafting; ledger alone could explain it (medium). |
| L1-M04 | `RESULT-004`; register 13; v001. Emits GARNET/HELIX delta. | Seven claims admitted, register 13→20 (final capacity). | Later capacity is exhausted; replacement rather than append remains an alternative (high). |
| L1-M05 | `RESULT-005`; full register; v001. Emits INDIGO/JASPER delta. | Four claims rejected; no register change. Q09/Q10 anchors are emitted but absent from final register; final artifact later preserves Q10's 72-hour/E-17/0.019-mg/L/seven-year substance. | Capacity may raise omission risk; ledger might compensate (medium). |
| L1-M06 | `RESULT-006`; full register; v002. Emits KESTREL/LUMEN delta. | Four claims rejected; no register change. Related resource/public concepts appear later in artifact but not as registered claims. | Paid maintenance supplies no new persistent residue; prompt exposure still could matter (medium). |
| L1-M07 | `RESULT-007`; full register; v006. Emits MOSAIC/NEXUS delta. | Four central Q12 currentness/readiness claims rejected; no register change. Artifact nevertheless uses related material, but no subsequent verification occurs. | Capacity/timing plausibly contributes to lifecycle failure; final audit failure may be independent (medium). |

## Cross-turn qualitative findings

1. The literal contrast is not “W0 never attempted construction.” W0 made two complete-decision attempts after 16 reopens. Both are rejected because the action payload was truncated into invalid JSON, leaving **zero admitted decision mutations**.
2. L1’s observable advantage is cumulative artifact construction through smaller upserts followed by consolidation, not proof that the register alone caused construction. The direct facts support an interaction among representation, action granularity, and transport limits; prompt trajectory and sampling remain alternatives.
3. The L1 register is lossy: it reaches 20 claims after M04; DELTA, INDIGO, JASPER, KESTREL, LUMEN, MOSAIC and NEXUS proposals are then partially/all rejected. Its omissions coexist with adjudicated partial Q04/Q09 and the incomplete lifecycle, but do not establish causation. Q10 is semantically met; its mechanical miss was a surface-form false negative.
4. Neither arm crosses check, repair, recheck, or submission. The sealed final evaluations retain `closure_readiness: not_ready`; no semantic interpretation upgrades that disposition.
