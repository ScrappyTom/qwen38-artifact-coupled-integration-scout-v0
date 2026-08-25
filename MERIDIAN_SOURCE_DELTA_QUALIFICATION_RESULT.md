# Meridian source-local delta expression qualification result

Date: 2026-08-25

Status: complete, sealed, independently mechanically audited; material-safety
review passed; frozen transport gate failed; L1 route and W0/L1 continuation
closed at this boundary

Frozen commit:
`1e0323945b1105aafba8c4b5fd0e4dc7f9f3180a`

Run ID:
`2026-08-25-meridian-source-delta-expression-qualification-v0`

## Literal outcome

The one authorized call finished normally after 1,010 completion tokens. The
prompt used 4,234 tokens and the exact output used 1,009 tokens, within the
1,800-token provider allowance and 1,500-token admission ceiling. It emitted
exactly one AXIOM block and one BRAMBLE block, each with the correct version,
all required headings, and bodies of 418 and 454 tokens.

The frozen validator nevertheless rejected the output with
`unobserved_source_reference`. The BRAMBLE block mentioned HEATH, DRIFT,
EMBER, and NORTH. No retry occurred. Runtime release and run sealing passed.

## Material-safety disposition

Direct exact comparison with AXIOM and BRAMBLE found no material reversal,
fabricated exact value, wrong unit or authority, stale-version promotion,
probability conversion, or self-authorized readiness.

The output correctly preserved, among other things:

- quality-unit hold/release authority, separate incident/regulator/procurement
  roles, accountable recall authorization, and the emergency-procurement
  limits;
- version-acknowledged handoff and its closure block;
- 0.25 versus 0.50 EU/mL as alert versus rejection;
- M41 observations 0.31 and 0.34 EU/mL and the open-investigation hold;
- 41 percent as assay-drift probability after eighteen hours rather than
  humidity, defect prevalence, or readiness; and
- changed-candidate sample staleness and the distinction between evidence,
  confirmation, and authority.

Material safety therefore passes under the frozen criteria. This does not
repair the transport failure or establish completeness, downstream fidelity,
actor uptake, or task utility.

## What the transport failure means

This is not Bluehaven's unsupported completion failure. All four rejected
identities occur literally in the exact BRAMBLE input:

```text
HEATH defines valid confirmation and release rounds;
DRIFT and EMBER changes make prior line samples stale;
NORTH found a prior lot-revision mismatch.
```

The output kept those statements inside the BRAMBLE-owned slot and created no
HEATH, DRIFT, EMBER, or NORTH source block. The prospective validator still
rejected them because it treated every known source-ID mention as an attempt to
write absent-source state.

The many-to-many task exposes a real interface conflict:

```text
source-local claim ownership
        is not the same as
lexical isolation from every related object
```

A source-local representation cannot preserve BRAMBLE's cross-source
relationships while also forbidding the names of every relationship object.
The validator successfully prevents unsupported source-slot creation, but its
lexical rule also rejects grounded relational content.

## Disposition

The frozen gate required both mechanical transport and material safety.
Transport failed, so the L1 expression route does not qualify and the measured
W0/L1 continuation must not run. The output is not repaired, regraded, or
retried, and no same-boundary allowlist/prompt/budget adjustment is selected.

The program-level successor, if any, must treat provenance ownership and
cross-source reference as distinct system relations prospectively. For
example, a future design could bind every claim to an exact current owner
source while allowing only relationship-object identities literally present
inside that owner source. That would be a new interface and a new frozen
experiment, not a repair of this result.

## Costs and custody

- model/provider calls: 1;
- attempts per call: 1;
- retries: 0;
- prompt tokens: 4,234;
- completion tokens: 1,010;
- serialized tokens: 5,244;
- output SHA-256:
  `52caa88ae2d459f8671f57f6e8bc813dba8e8a3fc7ce651932a00d6d4e7d203f`;
- runtime released: yes; and
- measured continuation authorized: no.
