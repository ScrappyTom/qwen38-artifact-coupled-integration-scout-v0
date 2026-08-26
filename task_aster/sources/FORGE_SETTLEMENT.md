# Settlement cutoffs, funding, and ledger finality

## Frozen findings

The domestic settlement cutoff is 17:00 UTC and the cross-border cutoff is 15:30 UTC. Missing a cutoff delays finality; it does not erase customer authorization.
The current prefunding requirement is 6.4 million dollars with a 0.9-million contingency. Amounts are cash obligations, not transaction counts.
Settlement files require a BRIDGE-consistent ledger cutoff and a MICA reconciliation sample before release.

## Governing relationships

JUNIPER reports rail availability, KELP governs reportable settlement delay, and HARBOR governs customer-facing pending status.
A BRIDGE schema or cutoff mutation makes FORGE file checks stale until regenerated and reconciled.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| SET-000 | domestic | v3 | 17.0 | hour-utc | superseded |
| SET-001 | cross-border | v3 | 18.1 | hour-utc | current |
| SET-002 | card | v3 | 19.2 | hour-utc | current |
| SET-003 | bank-transfer | v3 | 17.4 | hour-utc | current |
| SET-004 | domestic | v3 | 18.5 | hour-utc | current |
| SET-005 | cross-border | v3 | 19.6 | hour-utc | current |
| SET-006 | card | v3 | 17.8 | hour-utc | current |
| SET-007 | bank-transfer | v3 | 18.9 | hour-utc | current |
| SET-008 | domestic | v3 | 17.1 | hour-utc | current |
| SET-009 | cross-border | v3 | 18.2 | hour-utc | current |
| SET-010 | card | v3 | 19.3 | hour-utc | current |
| SET-011 | bank-transfer | v3 | 17.5 | hour-utc | current |
| SET-012 | domestic | v3 | 18.6 | hour-utc | current |
| SET-013 | cross-border | v3 | 19.7 | hour-utc | current |
| SET-014 | card | v4 | 17.9 | hour-utc | current |
| SET-015 | bank-transfer | v4 | 19.0 | hour-utc | current |
| SET-016 | domestic | v4 | 17.2 | hour-utc | current |
| SET-017 | cross-border | v4 | 18.3 | hour-utc | superseded |
| SET-018 | card | v4 | 19.4 | hour-utc | current |
| SET-019 | bank-transfer | v4 | 17.6 | hour-utc | current |
| SET-020 | domestic | v4 | 18.7 | hour-utc | current |
| SET-021 | cross-border | v4 | 19.8 | hour-utc | current |
| SET-022 | card | v4 | 18.0 | hour-utc | current |
| SET-023 | bank-transfer | v4 | 19.1 | hour-utc | current |
| SET-024 | domestic | v4 | 17.3 | hour-utc | current |
| SET-025 | cross-border | v4 | 18.4 | hour-utc | current |
| SET-026 | card | v4 | 19.5 | hour-utc | current |
| SET-027 | bank-transfer | v4 | 17.7 | hour-utc | current |
| SET-028 | domestic | v5 | 18.8 | hour-utc | current |
| SET-029 | cross-border | v5 | 17.0 | hour-utc | current |
| SET-030 | card | v5 | 18.1 | hour-utc | current |
| SET-031 | bank-transfer | v5 | 19.2 | hour-utc | current |
| SET-032 | domestic | v5 | 17.4 | hour-utc | current |
| SET-033 | cross-border | v5 | 18.5 | hour-utc | current |
| SET-034 | card | v5 | 19.6 | hour-utc | superseded |
| SET-035 | bank-transfer | v5 | 17.8 | hour-utc | current |
| SET-036 | domestic | v5 | 18.9 | hour-utc | current |
| SET-037 | cross-border | v5 | 17.1 | hour-utc | current |
| SET-038 | card | v5 | 18.2 | hour-utc | current |
| SET-039 | bank-transfer | v5 | 19.3 | hour-utc | current |
| SET-040 | domestic | v5 | 17.5 | hour-utc | current |
| SET-041 | cross-border | v5 | 18.6 | hour-utc | current |

## Decision constraints

Separate authorization, capture, ledger posting, settlement-file release, and finality.
State funding owner, cutoff decision, delay contingency, and exact release evidence.
