# Provenance-local relational claim contract

Date: 2026-08-25

Status: offline historical-fixture audit passed; live expression and
whole-system utility remain unqualified; no provider call is authorized

## Why this contract exists

E61 produced bounded AXIOM and BRAMBLE semantic work that passed every frozen
material-safety criterion. The carrier rejected it because BRAMBLE's exact
relationships named DRIFT, EMBER, HEATH, and NORTH. E62 then found that every
Meridian source names at least one other source, across 66 directed lexical
reference edges.

The old rule treated these as equivalent:

```text
mention source X
create or mutate X-owned semantic state
attest to X's authoritative current state
```

They are different capabilities. Locality must constrain semantic authority
and mutation scope without erasing relationships described by exact evidence.

## Minimal distinctions

Every prospective claim separates five properties.

1. **Record kind and mutation slot.** A source-reported claim may update only
   one admitted exact source/version slot. A genuinely derived claim belongs
   in task-native derived work rather than an arbitrary source slot.
2. **Evidence basis.** Each claim binds one or more exact source/version spans.
   The host validates source custody, line range, and exact span hash.
3. **Referents.** A source-reported relationship may name another known object
   when that identity occurs in the bound owner-source evidence. The referent
   acquires no mutation or attestation authority.
4. **Assertion mode and attribution.** The first scout distinguishes
   `source_reported_fact`, `source_reported_relationship`, and
   `derived_cross_source`. Source-reported modes use one owner source. Derived
   mode requires a multi-source support set and a separate derived-work record.
5. **Currentness.** Historical validity and active currency are separate. A
   source-version change retains the old claim in lineage but makes it stale
   and inactive.

All records are non-authoritative derivatives. They may not authorize
submission, release, recall, or closure.

## Mechanical versus semantic validation

The host can validate:

- exact slot identity and version;
- whether that source/version was admitted to the operation;
- exact evidence-span existence and hash;
- declared referents and whether relationship referents occur in the bound
  owner evidence;
- multi-source support for a derived-work claim;
- source-version currentness;
- mutation namespace; and
- token and control-authority limits in any later carrier.

The host cannot infer from those facts whether a predicate was paraphrased
correctly. The audit deliberately includes two mechanically valid claims that
remain semantic failures:

- Meridian changes are said to keep samples current rather than make them
  stale; and
- Cedar's 5.8-hour arrival and 42-percent wind-shift probability are converted
  into 5.8 km/h and relative humidity.

Exact provenance therefore improves custody and adjudicability. It does not
establish semantic truth.

## Historical-fixture audit

The ten-case audit covers the required design boundaries:

| Case | Mechanical result | Semantic disposition |
|---|---|---|
| AXIOM owner-local fact | allowed | pass |
| E61 BRAMBLE relationships naming four other sources | allowed in the BRAMBLE slot | pass under the frozen E61 safety review |
| BRAMBLE evidence used to mutate a DRIFT slot | rejected | absent-slot mutation |
| declared absent-source authoritative state | rejected | unsupported authority |
| reversed BRAMBLE staleness predicate | allowed mechanically | semantic failure |
| BRAMBLE + DRIFT synthesis in derived task work | allowed | pass for the frozen example |
| the same synthesis stored under BRAMBLE | rejected | wrong record kind |
| prior AXIOM version after a version successor | historically valid, inactive | stale |
| Bluehaven S07 state without S07 input | rejected | unsupported completion |
| Cedar unit/probability reversal with exact S02 provenance | allowed mechanically | semantic failure |

All source files, spans, historical outputs, candidate bytes, and prior
adjudication records are hash-bound. The audit makes no model call and does not
regrade any prior experiment.

## What this rules out

Do not:

- re-admit or retry E61;
- add its four rejected names to a special allowlist;
- treat any of Meridian's 66 lexical edges as automatically true claims;
- allow one source slot to own a genuinely multi-source synthesis;
- infer semantic correctness from exact span and referent checks;
- adopt the audit's Python/JSON representation as a required live transport;
  or
- build a universal claim graph before a complete trajectory demonstrates
  value.

The audit record is an apparatus specification, not the model-facing format.
A later expression gate may use bounded plain text with mechanically parsed
bindings if that is simpler and more reliable.

## Economic obligations of a future system

A live provenance-local policy must account for more than admission:

- total source-slot stock and wrapper cost;
- duplicated relationship edges across slots;
- retained conflicts between source reports;
- version replacement and stale-lineage cost;
- separately stored derived task work;
- semantic-provider calls and latency;
- exact reopening induced or avoided;
- actor-visible carrier cost; and
- downstream artifact, verification, repair, and closure quality.

At sixteen sources and the historical 650-token ceiling, source-slot payload
alone could approach 10,400 tokens before provenance and carrier overhead.
This is a ceiling, not a proposed target. The system must earn that cost by
improving cumulative exact work.

## Next experimental route

The current E61 boundary remains closed. The next route, if selected, is a new
prospective whole-system scout on a fresh eligible trajectory:

```text
W0_DIRECT_EXACT_WORK
    actor converts exact evidence into task-native work

L1_PROVENANCE_LOCAL_RELATIONAL
    separately charged bounded source reports
    + explicit relation referents
    + derived multi-source task work
    + the same exact artifact and feedback loop
```

Before a measured comparison, L1 receives at most one new expression
qualification. That gate must test the chosen live carrier, claim ownership,
referents, evidence bindings, derived-record separation, token bounds, and
material safety together. It is not another E61 prompt repair.

The full comparison must retain authentic ingress and pressure, reversible
relief, actor uptake, exact candidate effects, current verification,
repair/recheck opportunity, independent readiness, and total economic cost.
Admission rates are not a primary outcome.

No live task, expression gate, provider call, or GPU run is selected or
authorized by this contract.
