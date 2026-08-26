# External payment rails, observed availability, and fallback

## Frozen findings

Rail A reports 99.7 percent endpoint availability, but successful authorization is 98.9 percent because issuer declines remain separate. Availability is not payment success.
Rail B's contractual restoration target is four hours; the observed restoration in the last event was six hours and twenty minutes. Target and observation must not be swapped.
Fallback routing adds 220 milliseconds p95 and a 0.12-percent fee increment. Both must be included in capacity and cost decisions.

## Governing relationships

EMBER must retain headroom for fallback latency and DUSK replay. FORGE cutoffs constrain whether delayed rail traffic can settle the same day.
KELP reporting may be triggered by customer impact even if contractual rail availability remains above target.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| RAIL-000 | rail-A | v3 | 99.7 | percent-availability | superseded |
| RAIL-001 | rail-B | v3 | 100.8 | percent-availability | current |
| RAIL-002 | card-network | v3 | 101.9 | percent-availability | current |
| RAIL-003 | bank-network | v3 | 100.1 | percent-availability | current |
| RAIL-004 | rail-A | v3 | 101.2 | percent-availability | current |
| RAIL-005 | rail-B | v3 | 102.3 | percent-availability | current |
| RAIL-006 | card-network | v3 | 100.5 | percent-availability | current |
| RAIL-007 | bank-network | v3 | 101.6 | percent-availability | current |
| RAIL-008 | rail-A | v3 | 99.8 | percent-availability | current |
| RAIL-009 | rail-B | v3 | 100.9 | percent-availability | current |
| RAIL-010 | card-network | v3 | 102.0 | percent-availability | current |
| RAIL-011 | bank-network | v3 | 100.2 | percent-availability | current |
| RAIL-012 | rail-A | v3 | 101.3 | percent-availability | current |
| RAIL-013 | rail-B | v3 | 102.4 | percent-availability | current |
| RAIL-014 | card-network | v4 | 100.6 | percent-availability | current |
| RAIL-015 | bank-network | v4 | 101.7 | percent-availability | current |
| RAIL-016 | rail-A | v4 | 99.9 | percent-availability | current |
| RAIL-017 | rail-B | v4 | 101.0 | percent-availability | superseded |
| RAIL-018 | card-network | v4 | 102.1 | percent-availability | current |
| RAIL-019 | bank-network | v4 | 100.3 | percent-availability | current |
| RAIL-020 | rail-A | v4 | 101.4 | percent-availability | current |
| RAIL-021 | rail-B | v4 | 102.5 | percent-availability | current |
| RAIL-022 | card-network | v4 | 100.7 | percent-availability | current |
| RAIL-023 | bank-network | v4 | 101.8 | percent-availability | current |
| RAIL-024 | rail-A | v4 | 100.0 | percent-availability | current |
| RAIL-025 | rail-B | v4 | 101.1 | percent-availability | current |
| RAIL-026 | card-network | v4 | 102.2 | percent-availability | current |
| RAIL-027 | bank-network | v4 | 100.4 | percent-availability | current |
| RAIL-028 | rail-A | v5 | 101.5 | percent-availability | current |
| RAIL-029 | rail-B | v5 | 99.7 | percent-availability | current |
| RAIL-030 | card-network | v5 | 100.8 | percent-availability | current |
| RAIL-031 | bank-network | v5 | 101.9 | percent-availability | current |
| RAIL-032 | rail-A | v5 | 100.1 | percent-availability | current |
| RAIL-033 | rail-B | v5 | 101.2 | percent-availability | current |
| RAIL-034 | card-network | v5 | 102.3 | percent-availability | superseded |
| RAIL-035 | bank-network | v5 | 100.5 | percent-availability | current |
| RAIL-036 | rail-A | v5 | 101.6 | percent-availability | current |
| RAIL-037 | rail-B | v5 | 99.8 | percent-availability | current |
| RAIL-038 | card-network | v5 | 100.9 | percent-availability | current |
| RAIL-039 | bank-network | v5 | 102.0 | percent-availability | current |
| RAIL-040 | rail-A | v5 | 100.2 | percent-availability | current |
| RAIL-041 | rail-B | v5 | 101.3 | percent-availability | current |

## Decision constraints

Preserve availability, success, target, observed duration, latency, and fee units.
State rail-selection owner, fallback gate, rollback, and evidence for normal routing.
