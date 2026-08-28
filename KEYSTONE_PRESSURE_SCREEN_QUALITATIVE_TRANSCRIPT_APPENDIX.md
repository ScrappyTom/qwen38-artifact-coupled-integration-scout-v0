# Keystone pressure-screen qualitative transcript appendix

Date: 2026-08-27

Run ID: `2026-08-27-keystone-bounded-causal-pressure-screen-v0`

Frozen run commit: `d13582a9371512ee6d279ade461a88f05096f9f9`

Result commit: `eacafe5e4b46fcb3ffbadd90e9823d16796f6f4e`

## Scope and inference rule

This appendix reconstructs what was model-visible and how the actor's demand
changed. The actor emitted action objects without a reasoning trace. Statements
about why it chose an action are therefore labeled inference rather than fact.

The literal outputs establish action order, exact visibility, result delivery,
candidate state, and token economics. They do not prove that the model retained
or correctly integrated every semantic distinction in the resident sources.

## Initial decision environment

The actor began with:

* the exact task requiring two task artifacts, a 1,400–1,900-word decision,
  eight exact ordered sections, at least ten distinct source IDs, and
  reconciliation of fourteen named evidence domains;
* an exact fourteen-source catalog ordered MANDATE, TRACK, SIGNAL, POWER,
  ROLLING, CREW, WEATHER, FUEL, CYBER, TELEMETRY, LOADS, PASSENGER, LINEAGE,
  REVIEW;
* an empty evidence matrix and ten-word decision placeholder;
* single-source and bounded two-range batch reads;
* exact incremental artifact actions; and
* no semantic scaffold, progress state, pressure notice, or visible call budget.

Every source had 86 lines. One complete source fit the 120-line single-read
limit. Two complete sources did not fit the batch's 160-line aggregate limit.
The actor could batch partial ranges, but it consistently selected complete
single-source reads.

## Call-by-call reconstruction

| Call | Prompt tokens | Newly visible before decision | Action | Durable work change | Qualitative reading |
|---:|---:|---|---|---|---|
| 1 | 2,538 | Task, catalog, empty artifacts | Read complete MANDATE | None | Starts with authority, the first catalog item and the source naming central evidence dependencies. |
| 2 | 4,604 | MANDATE | Read complete TRACK | None | TRACK is the next catalog item and first major MANDATE prerequisite. |
| 3 | 6,758 | MANDATE + TRACK | Read complete SIGNAL | None | SIGNAL consumes TRACK topology and introduces CYBER and TELEMETRY dependencies. |
| 4 | 8,983 | Prior three exact bodies | Read complete POWER | None | POWER is another MANDATE prerequisite and introduces FUEL and TELEMETRY relations. |
| 5 | 11,303 | Prior four exact bodies | Read complete ROLLING | None | ROLLING links power demand, track restrictions, and crew readiness. |
| 6 | 13,583 | Prior five exact bodies | Read complete CREW | None | Completes MANDATE's central evidence list but leaves mandatory domains unread. |
| 7 | 15,799 | Six exact bodies | Read complete WEATHER | None | WEATHER is both next in catalog order and a TRACK/ROLLING dependency. |
| 8 | 18,031 | Seven exact bodies | Read complete FUEL | None | FUEL resolves power duration and logistics but introduces PASSENGER continuity. |
| 9 | 20,179 | Eight exact bodies through FUEL | Read complete CYBER | None | CYBER is next in catalog order and required by SIGNAL; its result cannot enter call 10. |

The first eight source observations crossed later model boundaries. CYBER did
not. Acquisition is not delivery: call 9 demonstrates only that the actor
wanted CYBER, not that it interpreted CYBER's contents.

## Demand topology

The action sequence is semantically coherent, but it is perfectly confounded
with catalog order. The strongest supported statement is catalog-prefix
traversal, not independently optimized semantic priority.

The sources also create forward semantic demand:

```text
MANDATE → TRACK / SIGNAL / POWER / ROLLING / CREW / REVIEW / LINEAGE
TRACK   → WEATHER / LOADS / SIGNAL / REVIEW / LINEAGE
SIGNAL  → CYBER / TELEMETRY / MANDATE / LINEAGE
POWER   → FUEL / TELEMETRY / TRACK / ROLLING
FUEL    → PASSENGER / SIGNAL / POWER / WEATHER / CREW
```

At the boundary, TELEMETRY, LOADS, PASSENGER, LINEAGE, and REVIEW were unseen.
Each maps directly to an explicit task obligation, so continued acquisition was
locally rational. The actor was not shown the 30-call ceiling or impending
prompt pressure and had no model-facing reason to trade another required source
for early partial construction.

## Evidence-to-work conversion failure

The candidate remained exactly the empty evidence matrix and ten-word decision
placeholder. The system accumulated exact evidence but created no durable
semantic or task-work residue. Offering `replace_evidence_ledger` and
`upsert_decision_section` did not itself induce early construction.

The run spent 101,778 prompt tokens and 231 completion tokens: about 441 prompt
tokens per completion token. Each increasingly expensive decision emitted only
another roughly 24-token read action. Prefix caching reduced compute cost but
did not turn interpretation into durable work.

```text
exact source bytes
→ transient model exposure
→ next read action

missing:
interpretation
→ exact evidence relation
→ incremental artifact state
```

## Why offline Stage 0 and live activation diverged

Stage 0 demonstrated a legal paired path using two partial source ranges per
step. That path reached ten qualifying sources at pressure. The live actor
chose complete 86-line single-source reads. Two complete sources exceed the
160-line batch limit, so exact completeness and batch bandwidth were in tension.

```text
offline legal path
partial paired ingress
→ fewer action/result wrappers
→ ten sources at pressure

live actor path
complete single-source ingress
→ more decisions and wrappers
→ first pressure after eight delivered sources
```

Stage 0 proved existence of a permitted path, not likelihood under the live
actor policy. Accessible or legally reachable geometry must not be substituted
for realized actor geometry.

## What first-fit relief would change

The frozen scan selects `RESULT-001`, MANDATE. This is mechanically minimal
under the scan order and restores 344 tokens of headroom. Semantically it would
externalize the foundational authority source before construction starts.

MANDATE remains exactly reopenable, so this is not information destruction.
But it creates the intended system interaction: whether common temporary
provenance-bound residue and exact incremental task work preserve governing
authority distinctions when the raw source leaves residency.

The E79 screen stopped before that operation. It therefore does not measure
semantic persistence, reopen behavior, artifact coupling, or bounded causal
continuity.

## Lifecycle and causal-treatment reachability

At E79 there was no candidate mutation, verification transition, current check,
repair, rejected mutation, or recurrence state. The V0/V1 difference was empty.

The treatment becomes reachable only after construction, current feedback, a
rejected repair, and a later observation acquired in the unchanged-candidate
epoch. The next experiment should treat E79 as immutable common history, make
positive-savings relief common infrastructure, and continue one ordinary
trajectory until that exact causal event exists. Only then should the state be
cloned for V0 and V1, immediately before the next decision that delivers the
pending observation.

This preserves the downstream interaction among artifact, feedback, repair
transport, causal continuity, recheck, readiness, and closure while avoiding
duplicated treatment-inactive acquisition.

## Final qualitative disposition

The actor was syntactically reliable and directionally coherent. It was not
shown to integrate evidence into durable work. First pressure arrived before
the planned evidence gate because the actor selected complete serial ingress
rather than the offline partial-batch path. E79 is therefore a valid systems
result about activation and information throughput, not a test of the bounded-
causal hypothesis.
