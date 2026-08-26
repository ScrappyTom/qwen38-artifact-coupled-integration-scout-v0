# Fraud controls, hold thresholds, and manual review capacity

## Frozen findings

The current manual-review rate is 0.8 percent of authorized payments. It is not 0.8 probability, 80 percent, or a duplicate-payment measure.
A risk-score alert begins at 720; an automatic hold begins at 860. The alert and hold thresholds must remain distinct.
Manual review capacity is 9,500 cases per hour for two hours, then 6,200 per hour. Backlog above 18,000 blocks a full traffic ramp.

## Governing relationships

CIRRUS duplicate suppression is independent of GROVE fraud disposition. LATTICE supplies current score-distribution and false-positive telemetry.
HARBOR communications must not call a pending fraud review a declined or settled payment.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| RISK-000 | card | v3 | 0.8 | percent-review-rate | superseded |
| RISK-001 | bank | v3 | 1.9 | percent-review-rate | current |
| RISK-002 | merchant | v3 | 3.0 | percent-review-rate | current |
| RISK-003 | account | v3 | 1.2 | percent-review-rate | current |
| RISK-004 | card | v3 | 2.3 | percent-review-rate | current |
| RISK-005 | bank | v3 | 3.4 | percent-review-rate | current |
| RISK-006 | merchant | v3 | 1.6 | percent-review-rate | current |
| RISK-007 | account | v3 | 2.7 | percent-review-rate | current |
| RISK-008 | card | v3 | 0.9 | percent-review-rate | current |
| RISK-009 | bank | v3 | 2.0 | percent-review-rate | current |
| RISK-010 | merchant | v3 | 3.1 | percent-review-rate | current |
| RISK-011 | account | v3 | 1.3 | percent-review-rate | current |
| RISK-012 | card | v3 | 2.4 | percent-review-rate | current |
| RISK-013 | bank | v3 | 3.5 | percent-review-rate | current |
| RISK-014 | merchant | v4 | 1.7 | percent-review-rate | current |
| RISK-015 | account | v4 | 2.8 | percent-review-rate | current |
| RISK-016 | card | v4 | 1.0 | percent-review-rate | current |
| RISK-017 | bank | v4 | 2.1 | percent-review-rate | superseded |
| RISK-018 | merchant | v4 | 3.2 | percent-review-rate | current |
| RISK-019 | account | v4 | 1.4 | percent-review-rate | current |
| RISK-020 | card | v4 | 2.5 | percent-review-rate | current |
| RISK-021 | bank | v4 | 3.6 | percent-review-rate | current |
| RISK-022 | merchant | v4 | 1.8 | percent-review-rate | current |
| RISK-023 | account | v4 | 2.9 | percent-review-rate | current |
| RISK-024 | card | v4 | 1.1 | percent-review-rate | current |
| RISK-025 | bank | v4 | 2.2 | percent-review-rate | current |
| RISK-026 | merchant | v4 | 3.3 | percent-review-rate | current |
| RISK-027 | account | v4 | 1.5 | percent-review-rate | current |
| RISK-028 | card | v5 | 2.6 | percent-review-rate | current |
| RISK-029 | bank | v5 | 0.8 | percent-review-rate | current |
| RISK-030 | merchant | v5 | 1.9 | percent-review-rate | current |
| RISK-031 | account | v5 | 3.0 | percent-review-rate | current |
| RISK-032 | card | v5 | 1.2 | percent-review-rate | current |
| RISK-033 | bank | v5 | 2.3 | percent-review-rate | current |
| RISK-034 | merchant | v5 | 3.4 | percent-review-rate | superseded |
| RISK-035 | account | v5 | 1.6 | percent-review-rate | current |
| RISK-036 | card | v5 | 2.7 | percent-review-rate | current |
| RISK-037 | bank | v5 | 0.9 | percent-review-rate | current |
| RISK-038 | merchant | v5 | 2.0 | percent-review-rate | current |
| RISK-039 | account | v5 | 3.1 | percent-review-rate | current |
| RISK-040 | card | v5 | 1.3 | percent-review-rate | current |
| RISK-041 | bank | v5 | 2.4 | percent-review-rate | current |

## Decision constraints

Preserve percent, score thresholds, time-varying capacity, backlog gate, and separate control purposes.
Name what evidence can retire a hold without weakening fraud controls.
