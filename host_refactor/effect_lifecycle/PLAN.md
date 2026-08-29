# Candidate-effect lifecycle implementation plan

Date: 2026-08-29

## Invariants

1. Pending effects remain exact and cannot be lifecycle-externalized.
2. Provider failure never commits delivery or permits externalization.
3. A delivered effect may leave residency only when its exact mutation chain
   leads to the current candidate hash.
4. Exact effect bytes, event chronology, and reopen capability remain in
   external custody.
5. The model-facing current-effect object is replaceable and says explicitly
   that semantic uptake is not inferred.
6. Old effect bodies are not retained merely because they are marked
   non-relief-eligible for ordinary capacity relief.
7. Current check binding remains candidate-hash based.
8. The exact mutation action may be projected as a compact receipt only with
   the same delivery and lineage proof as its effect; its original bytes remain
   in the append-only event ledger.

## Slices

- add a distinct causal-pair lifecycle event to the host kernel;
- add the bounded effect projection and reconciliation policy;
- add a future-only orchestrator using that policy;
- replay the exact pre-terminal E96 V1 state;
- exercise check, repair, recheck, and closure provider-free;
- document the result and run the complete regression.

## Explicit non-goal

This slice does not make a full-document action fit before its pending effect
has crossed a model call. That one-call transport envelope remains a separate
action-granularity constraint. The lifecycle bounds already-applied history; it
does not retroactively shrink a response that has not yet been delivered.
