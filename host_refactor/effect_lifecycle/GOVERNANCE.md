# Candidate-effect lifecycle governance

## Objective

Preserve exact mutation custody and delivery auditability while preventing old
mutation actions and effect bodies from accumulating beside the complete
current candidate.

## Authority boundary

The host may derive only:

- exact before/after candidate hashes;
- the exact assistant action bound to the effect's acquired call;
- whether candidate effects form one exact lineage ending at the current
  candidate;
- acquired, pending, delivered-resident, or delivered-external state;
- exact result hashes, sizes, and reopen handles; and
- whether a completed invocation exposed an effect.

It may not infer that the model understood an effect, that construction is
complete, that a check is sufficient, or that the artifact is ready.

## Change protocol

This subproject is additive. Sealed E96 results and historical runners remain
unchanged. Each implementation slice must update `WORK_LOG.md`, add a
provider-free test, and preserve one-attempt/zero-retry behavior. No provider or
GPU call is allowed during this offline stage.

## Stop rule

Stop after exact E96 replay, adversarial delivery/lineage/action-binding tests,
checkpoint hydration, a provider-free construction-to-verification lifecycle,
and the full repository regression. A live successor requires a new frozen
commit and explicit authorization.
