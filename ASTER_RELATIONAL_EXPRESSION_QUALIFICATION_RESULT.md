# Aster provenance-relational expression qualification result

Date: 2026-08-26

Status: complete, sealed, independently audited; raw semantic material was
locally safe, the frozen exact-line transport gate failed, and no W0/L1
continuation is authorized

Frozen commit:
`8aa9afbec32b5669755760f2d4d7b5c992150e05`

Run ID:
`2026-08-26-aster-relational-expression-qualification-v0`

## Literal outcome

The sole authorized call finished normally. It used 4,428 prompt tokens and
708 completion tokens, for 5,136 serialized tokens. The exact output occupied
707 tokenizer tokens, below the 1,500-token carrier ceiling, and contained four
well-shaped claim blocks: two for ANCHOR and two for BRIDGE. Source IDs,
versions, `RESULT-001` bindings, attribution, authority labels, and claim-count
limits were correct.

The frozen validator admitted none of the four claims. Every
`EVIDENCE_QUOTE` copied one exact sentence from an owner-source line, while the
contract required the complete source line. The relevant source lines contain
multiple sentences. Because each quote was a strict substring rather than a
line-equal match, validation returned:

```text
evidence_quote_not_unique_exact_line
externalized_source_unrepresented:ANCHOR
externalized_source_unrepresented:BRIDGE
```

The last two findings are consequences of the first: quote resolution skipped
all four claims, leaving zero mechanically represented owner sources. No retry,
repair, normalization, or continuation occurred.

## Semantic-safety disposition

Direct comparison of the sealed raw statements with exact ANCHOR and BRIDGE
bytes found no fabricated value or unit, timing conversion, authority
transfer, stale-evidence promotion, relationship reversal, absent-source slot
mutation, readiness assertion, or closure authorization.

The output correctly preserved:

- incident-command isolation and recovery sequencing;
- payment-risk-owner restoration authority after current independent
  verification, with mutation and format checks explicitly non-authorizing;
- 1,800 milliseconds at p95 as observed replication lag; and
- fifteen-second RPO versus forty-five-minute RTO values.

Coverage was narrow. Emergency procurement, accountable closure,
version-acknowledged handoff, candidate-bound verification currentness, and all
governing cross-source relationships were omitted. The two BRIDGE facts also
omitted adjacent qualifications from their multi-sentence lines. The frozen
omission rule treats those as coverage limits rather than contradictions.

Raw semantic material safety therefore passes locally, but the admission-based
gate does not: zero claims entered the register. This distinction does not
repair or regrade the failed qualification.

## What this means

The call is encouraging about bounded, source/version-bound factual expression
and negative for this exact carrier transport. Unlike Meridian E61, the
failure does not expose a corpus-wide category error in the validator. The
instruction explicitly required a complete line, and Qwen instead selected
sentence-level evidence. The line-oriented contract was mechanically
unambiguous, but it was not reliably expressed in this one live call.

The call also did not exercise the main relational affordance: every emitted
claim used `source_reported_fact` with `REFERENTS: NONE`. It therefore cannot
establish that Qwen will express, preserve, or use provenance-local
relationships at the authentic Aster boundary.

The supported disposition is:

```text
bounded grounded factual content       local positive
raw material safety                    local positive
complete-line evidence transport       local negative
mechanically admitted claims           0 / 4
relational expression                  untested in observed output
register persistence / actor utility   untested
whole-system W0/L1 comparison          not authorized
```

## Program routing

The prospectively frozen rule said that failure closes this exact Aster carrier
route at this boundary, with no same-boundary prompt, schema, budget, allowlist,
or retry ladder. That stop rule now applies.

This is not evidence against provenance-local relational persistence in
general. It is evidence that another transport micro-iteration would again
make interface compliance—not system interaction—the immediate research
object. The whole-system L1 arm cannot run on an unqualified carrier, and the
W0/L1 continuation remains closed.

Any future live route must be prospectively distinct and chosen from the
program-level systems question, not presented as a repair or retry of this
call. The reusable mechanical baseline—exact custody, first-fit relief,
reopening, task-native artifact effects, candidate-bound checks, and external
readiness—remains available independently of this failed semantic carrier.

## Costs and custody

- provider/model calls: 1;
- attempts per call: 1;
- retries: 0;
- prompt tokens: 4,428;
- completion tokens: 708;
- serialized tokens: 5,136;
- exact output tokens: 707;
- output SHA-256:
  `2e0c049ffccf2b97b161d9eaf72a77993c59407ac6489c20817a66362ff8a0b6`;
- transport passed: no;
- raw material-safety review passed: yes;
- qualification passed: no;
- runtime released: yes; and
- measured continuation authorized: no.
