# Queue backlog, replay order, and drain constraints

## Frozen findings

The durable queue contains 3.6 million pending messages. The observed safe drain rate is 1,200 messages per second while live ingress is capped at 400 per second; the rate is not messages per minute.
Refund and reversal events must preserve account order. Webhooks may be delayed, but capture acknowledgments cannot pass an unresolved ledger write.
The restore gate is backlog below 200,000 plus a current fifteen-minute zero-ordering-error observation. Backlog alone is not sufficient.

## Governing relationships

CIRRUS supplies retry identity; BRIDGE supplies ledger position; EMBER supplies capacity headroom. All three constrain DUSK replay sequencing.
LATTICE alerts on rate and ordering, while ORBIT documents an earlier exercise that used an obsolete queue-policy version.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| QUE-000 | capture | v3 | 1200.0 | messages-per-second | superseded |
| QUE-001 | refund | v3 | 1201.1 | messages-per-second | current |
| QUE-002 | webhook | v3 | 1202.2 | messages-per-second | current |
| QUE-003 | settlement | v3 | 1200.4 | messages-per-second | current |
| QUE-004 | capture | v3 | 1201.5 | messages-per-second | current |
| QUE-005 | refund | v3 | 1202.6 | messages-per-second | current |
| QUE-006 | webhook | v3 | 1200.8 | messages-per-second | current |
| QUE-007 | settlement | v3 | 1201.9 | messages-per-second | current |
| QUE-008 | capture | v3 | 1200.1 | messages-per-second | current |
| QUE-009 | refund | v3 | 1201.2 | messages-per-second | current |
| QUE-010 | webhook | v3 | 1202.3 | messages-per-second | current |
| QUE-011 | settlement | v3 | 1200.5 | messages-per-second | current |
| QUE-012 | capture | v3 | 1201.6 | messages-per-second | current |
| QUE-013 | refund | v3 | 1202.7 | messages-per-second | current |
| QUE-014 | webhook | v4 | 1200.9 | messages-per-second | current |
| QUE-015 | settlement | v4 | 1202.0 | messages-per-second | current |
| QUE-016 | capture | v4 | 1200.2 | messages-per-second | current |
| QUE-017 | refund | v4 | 1201.3 | messages-per-second | superseded |
| QUE-018 | webhook | v4 | 1202.4 | messages-per-second | current |
| QUE-019 | settlement | v4 | 1200.6 | messages-per-second | current |
| QUE-020 | capture | v4 | 1201.7 | messages-per-second | current |
| QUE-021 | refund | v4 | 1202.8 | messages-per-second | current |
| QUE-022 | webhook | v4 | 1201.0 | messages-per-second | current |
| QUE-023 | settlement | v4 | 1202.1 | messages-per-second | current |
| QUE-024 | capture | v4 | 1200.3 | messages-per-second | current |
| QUE-025 | refund | v4 | 1201.4 | messages-per-second | current |
| QUE-026 | webhook | v4 | 1202.5 | messages-per-second | current |
| QUE-027 | settlement | v4 | 1200.7 | messages-per-second | current |
| QUE-028 | capture | v5 | 1201.8 | messages-per-second | current |
| QUE-029 | refund | v5 | 1200.0 | messages-per-second | current |
| QUE-030 | webhook | v5 | 1201.1 | messages-per-second | current |
| QUE-031 | settlement | v5 | 1202.2 | messages-per-second | current |
| QUE-032 | capture | v5 | 1200.4 | messages-per-second | current |
| QUE-033 | refund | v5 | 1201.5 | messages-per-second | current |
| QUE-034 | webhook | v5 | 1202.6 | messages-per-second | superseded |
| QUE-035 | settlement | v5 | 1200.8 | messages-per-second | current |
| QUE-036 | capture | v5 | 1201.9 | messages-per-second | current |
| QUE-037 | refund | v5 | 1200.1 | messages-per-second | current |
| QUE-038 | webhook | v5 | 1201.2 | messages-per-second | current |
| QUE-039 | settlement | v5 | 1202.3 | messages-per-second | current |
| QUE-040 | capture | v5 | 1200.5 | messages-per-second | current |
| QUE-041 | refund | v5 | 1201.6 | messages-per-second | current |

## Decision constraints

Calculate drain opportunity using both drain and live-ingress rates and preserve event ordering.
Name the current evidence that starts, pauses, resumes, and retires replay controls.
