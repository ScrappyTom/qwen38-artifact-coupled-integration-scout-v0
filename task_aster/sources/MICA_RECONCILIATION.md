# Reconciliation samples, exception rates, and loss estimates

## Frozen findings

The current reconciliation sample covers 2.4 percent of affected transactions, stratified by payment rail and operation. It is not a 2.4-percent loss rate.
Observed unmatched ledger events are 0.14 percent of the sample. The release threshold is below 0.05 percent in two independent samples.
The provisional customer-loss estimate is 310,000 dollars with a 90-percent interval from 240,000 to 430,000 dollars. The interval is not a probability of loss.

## Governing relationships

FORGE requires a MICA sample before settlement-file release. HARBOR uses reconciled state for customer correction, and KELP uses the loss estimate for escalation.
A BRIDGE schema, DUSK replay, or candidate change makes the prior sample stale for affected transactions.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| REC-000 | capture | v3 | 2.4 | percent-sample | superseded |
| REC-001 | refund | v3 | 3.5 | percent-sample | current |
| REC-002 | settlement | v3 | 4.6 | percent-sample | current |
| REC-003 | customer-loss | v3 | 2.8 | percent-sample | current |
| REC-004 | capture | v3 | 3.9 | percent-sample | current |
| REC-005 | refund | v3 | 5.0 | percent-sample | current |
| REC-006 | settlement | v3 | 3.2 | percent-sample | current |
| REC-007 | customer-loss | v3 | 4.3 | percent-sample | current |
| REC-008 | capture | v3 | 2.5 | percent-sample | current |
| REC-009 | refund | v3 | 3.6 | percent-sample | current |
| REC-010 | settlement | v3 | 4.7 | percent-sample | current |
| REC-011 | customer-loss | v3 | 2.9 | percent-sample | current |
| REC-012 | capture | v3 | 4.0 | percent-sample | current |
| REC-013 | refund | v3 | 5.1 | percent-sample | current |
| REC-014 | settlement | v4 | 3.3 | percent-sample | current |
| REC-015 | customer-loss | v4 | 4.4 | percent-sample | current |
| REC-016 | capture | v4 | 2.6 | percent-sample | current |
| REC-017 | refund | v4 | 3.7 | percent-sample | superseded |
| REC-018 | settlement | v4 | 4.8 | percent-sample | current |
| REC-019 | customer-loss | v4 | 3.0 | percent-sample | current |
| REC-020 | capture | v4 | 4.1 | percent-sample | current |
| REC-021 | refund | v4 | 5.2 | percent-sample | current |
| REC-022 | settlement | v4 | 3.4 | percent-sample | current |
| REC-023 | customer-loss | v4 | 4.5 | percent-sample | current |
| REC-024 | capture | v4 | 2.7 | percent-sample | current |
| REC-025 | refund | v4 | 3.8 | percent-sample | current |
| REC-026 | settlement | v4 | 4.9 | percent-sample | current |
| REC-027 | customer-loss | v4 | 3.1 | percent-sample | current |
| REC-028 | capture | v5 | 4.2 | percent-sample | current |
| REC-029 | refund | v5 | 2.4 | percent-sample | current |
| REC-030 | settlement | v5 | 3.5 | percent-sample | current |
| REC-031 | customer-loss | v5 | 4.6 | percent-sample | current |
| REC-032 | capture | v5 | 2.8 | percent-sample | current |
| REC-033 | refund | v5 | 3.9 | percent-sample | current |
| REC-034 | settlement | v5 | 5.0 | percent-sample | superseded |
| REC-035 | customer-loss | v5 | 3.2 | percent-sample | current |
| REC-036 | capture | v5 | 4.3 | percent-sample | current |
| REC-037 | refund | v5 | 2.5 | percent-sample | current |
| REC-038 | settlement | v5 | 3.6 | percent-sample | current |
| REC-039 | customer-loss | v5 | 4.7 | percent-sample | current |
| REC-040 | capture | v5 | 2.9 | percent-sample | current |
| REC-041 | refund | v5 | 4.0 | percent-sample | current |

## Decision constraints

Preserve sampling basis, exception rate, two-sample rule, estimate, interval, and candidate currentness.
State who expands the sample and what observation retires reconciliation blockers.
