# Idempotency keys, retry windows, and duplicate-payment controls

## Frozen findings

The idempotency retention window is forty-five minutes for API retries and two hours for delayed merchant acknowledgments. Neither window is a transaction timeout.
Keys are unique only within merchant and operation scope. Reusing one key across capture and refund is unsafe even when the amount matches.
The current duplicate-payment observation is 0.08 percent of attempted retries, not 0.08 probability and not an eight-percent customer rate.

## Governing relationships

CIRRUS retry release requires a BRIDGE-consistent ledger position and a DUSK queue policy that preserves the same idempotency key. GROVE fraud holds remain separate from duplicate suppression.
NOVA rollback must retain the dedupe log for the full CIRRUS window or explicitly suspend retries.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| IDEM-000 | api-key | v3 | 45.0 | minutes | superseded |
| IDEM-001 | merchant-key | v3 | 46.1 | minutes | current |
| IDEM-002 | retry-cache | v3 | 47.2 | minutes | current |
| IDEM-003 | dedupe-log | v3 | 45.4 | minutes | current |
| IDEM-004 | api-key | v3 | 46.5 | minutes | current |
| IDEM-005 | merchant-key | v3 | 47.6 | minutes | current |
| IDEM-006 | retry-cache | v3 | 45.8 | minutes | current |
| IDEM-007 | dedupe-log | v3 | 46.9 | minutes | current |
| IDEM-008 | api-key | v3 | 45.1 | minutes | current |
| IDEM-009 | merchant-key | v3 | 46.2 | minutes | current |
| IDEM-010 | retry-cache | v3 | 47.3 | minutes | current |
| IDEM-011 | dedupe-log | v3 | 45.5 | minutes | current |
| IDEM-012 | api-key | v3 | 46.6 | minutes | current |
| IDEM-013 | merchant-key | v3 | 47.7 | minutes | current |
| IDEM-014 | retry-cache | v4 | 45.9 | minutes | current |
| IDEM-015 | dedupe-log | v4 | 47.0 | minutes | current |
| IDEM-016 | api-key | v4 | 45.2 | minutes | current |
| IDEM-017 | merchant-key | v4 | 46.3 | minutes | superseded |
| IDEM-018 | retry-cache | v4 | 47.4 | minutes | current |
| IDEM-019 | dedupe-log | v4 | 45.6 | minutes | current |
| IDEM-020 | api-key | v4 | 46.7 | minutes | current |
| IDEM-021 | merchant-key | v4 | 47.8 | minutes | current |
| IDEM-022 | retry-cache | v4 | 46.0 | minutes | current |
| IDEM-023 | dedupe-log | v4 | 47.1 | minutes | current |
| IDEM-024 | api-key | v4 | 45.3 | minutes | current |
| IDEM-025 | merchant-key | v4 | 46.4 | minutes | current |
| IDEM-026 | retry-cache | v4 | 47.5 | minutes | current |
| IDEM-027 | dedupe-log | v4 | 45.7 | minutes | current |
| IDEM-028 | api-key | v5 | 46.8 | minutes | current |
| IDEM-029 | merchant-key | v5 | 45.0 | minutes | current |
| IDEM-030 | retry-cache | v5 | 46.1 | minutes | current |
| IDEM-031 | dedupe-log | v5 | 47.2 | minutes | current |
| IDEM-032 | api-key | v5 | 45.4 | minutes | current |
| IDEM-033 | merchant-key | v5 | 46.5 | minutes | current |
| IDEM-034 | retry-cache | v5 | 47.6 | minutes | superseded |
| IDEM-035 | dedupe-log | v5 | 45.8 | minutes | current |
| IDEM-036 | api-key | v5 | 46.9 | minutes | current |
| IDEM-037 | merchant-key | v5 | 45.1 | minutes | current |
| IDEM-038 | retry-cache | v5 | 46.2 | minutes | current |
| IDEM-039 | dedupe-log | v5 | 47.3 | minutes | current |
| IDEM-040 | api-key | v5 | 45.5 | minutes | current |
| IDEM-041 | merchant-key | v5 | 46.6 | minutes | current |

## Decision constraints

State the key scope, both retention windows, duplicate observation, and retry retirement evidence.
Do not infer ledger consistency, fraud clearance, or restoration authority from key presence.
