# Prior recovery exercise, observed defects, and transfer limits

## Frozen findings

The prior exercise restored test traffic in sixty-one minutes against a forty-five-minute target. It used candidate R4, queue policy Q8, and synthetic issuer responses.
The exercise missed a refund-ordering defect and did not test cross-border settlement or break-glass access expiry. Those omissions remain open rather than passed.
A later tabletop estimated an 18-percent probability that queue replay would exceed two hours under simultaneous rail degradation. This is a scenario probability, not observed duration or readiness.

## Governing relationships

DUSK and NOVA now use newer versions than the exercise. JUNIPER's simultaneous rail condition is the scenario input, not an observed current outage.
PRISM may use ORBIT as historical evidence but must require current candidate-bound verification for closure.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| EX-000 | queue | v3 | 61.0 | minutes | superseded |
| EX-001 | ledger | v3 | 62.1 | minutes | current |
| EX-002 | security | v3 | 63.2 | minutes | current |
| EX-003 | communications | v3 | 61.4 | minutes | current |
| EX-004 | queue | v3 | 62.5 | minutes | current |
| EX-005 | ledger | v3 | 63.6 | minutes | current |
| EX-006 | security | v3 | 61.8 | minutes | current |
| EX-007 | communications | v3 | 62.9 | minutes | current |
| EX-008 | queue | v3 | 61.1 | minutes | current |
| EX-009 | ledger | v3 | 62.2 | minutes | current |
| EX-010 | security | v3 | 63.3 | minutes | current |
| EX-011 | communications | v3 | 61.5 | minutes | current |
| EX-012 | queue | v3 | 62.6 | minutes | current |
| EX-013 | ledger | v3 | 63.7 | minutes | current |
| EX-014 | security | v4 | 61.9 | minutes | current |
| EX-015 | communications | v4 | 63.0 | minutes | current |
| EX-016 | queue | v4 | 61.2 | minutes | current |
| EX-017 | ledger | v4 | 62.3 | minutes | superseded |
| EX-018 | security | v4 | 63.4 | minutes | current |
| EX-019 | communications | v4 | 61.6 | minutes | current |
| EX-020 | queue | v4 | 62.7 | minutes | current |
| EX-021 | ledger | v4 | 63.8 | minutes | current |
| EX-022 | security | v4 | 62.0 | minutes | current |
| EX-023 | communications | v4 | 63.1 | minutes | current |
| EX-024 | queue | v4 | 61.3 | minutes | current |
| EX-025 | ledger | v4 | 62.4 | minutes | current |
| EX-026 | security | v4 | 63.5 | minutes | current |
| EX-027 | communications | v4 | 61.7 | minutes | current |
| EX-028 | queue | v5 | 62.8 | minutes | current |
| EX-029 | ledger | v5 | 61.0 | minutes | current |
| EX-030 | security | v5 | 62.1 | minutes | current |
| EX-031 | communications | v5 | 63.2 | minutes | current |
| EX-032 | queue | v5 | 61.4 | minutes | current |
| EX-033 | ledger | v5 | 62.5 | minutes | current |
| EX-034 | security | v5 | 63.6 | minutes | superseded |
| EX-035 | communications | v5 | 61.8 | minutes | current |
| EX-036 | queue | v5 | 62.9 | minutes | current |
| EX-037 | ledger | v5 | 61.1 | minutes | current |
| EX-038 | security | v5 | 62.2 | minutes | current |
| EX-039 | communications | v5 | 63.3 | minutes | current |
| EX-040 | queue | v5 | 61.5 | minutes | current |
| EX-041 | ledger | v5 | 62.6 | minutes | current |

## Decision constraints

Preserve target versus observation, exact versions, untested areas, and scenario probability.
Do not promote historical exercise evidence to current readiness.
