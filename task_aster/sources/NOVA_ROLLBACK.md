# Rollback compatibility, candidate lineage, and recovery gates

## Frozen findings

Candidate R5 changes queue batching and audit fields while retaining schema-12 read compatibility. The rollback estimate is thirty-five minutes if no schema-13-only write has occurred.
After a schema-13-only write, rollback requires a forward repair rather than direct reversion. Candidate identity and write history therefore govern the rollback path.
A check against R4 or pre-mutation R5 remains historical evidence but is stale after any R5 candidate effect until rerun.

## Governing relationships

BRIDGE supplies schema and ledger consistency; IRIS supplies key-set and access currency. Both must bind the same NOVA candidate before rollback or restoration.
ORBIT's exercise used R4 and cannot prove R5 readiness. PRISM independently reviews the current candidate and check set.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| ROLL-000 | candidate-R4 | v3 | 35.0 | minutes | superseded |
| ROLL-001 | candidate-R5 | v3 | 36.1 | minutes | current |
| ROLL-002 | schema-12 | v3 | 37.2 | minutes | current |
| ROLL-003 | schema-13 | v3 | 35.4 | minutes | current |
| ROLL-004 | candidate-R4 | v3 | 36.5 | minutes | current |
| ROLL-005 | candidate-R5 | v3 | 37.6 | minutes | current |
| ROLL-006 | schema-12 | v3 | 35.8 | minutes | current |
| ROLL-007 | schema-13 | v3 | 36.9 | minutes | current |
| ROLL-008 | candidate-R4 | v3 | 35.1 | minutes | current |
| ROLL-009 | candidate-R5 | v3 | 36.2 | minutes | current |
| ROLL-010 | schema-12 | v3 | 37.3 | minutes | current |
| ROLL-011 | schema-13 | v3 | 35.5 | minutes | current |
| ROLL-012 | candidate-R4 | v3 | 36.6 | minutes | current |
| ROLL-013 | candidate-R5 | v3 | 37.7 | minutes | current |
| ROLL-014 | schema-12 | v4 | 35.9 | minutes | current |
| ROLL-015 | schema-13 | v4 | 37.0 | minutes | current |
| ROLL-016 | candidate-R4 | v4 | 35.2 | minutes | current |
| ROLL-017 | candidate-R5 | v4 | 36.3 | minutes | superseded |
| ROLL-018 | schema-12 | v4 | 37.4 | minutes | current |
| ROLL-019 | schema-13 | v4 | 35.6 | minutes | current |
| ROLL-020 | candidate-R4 | v4 | 36.7 | minutes | current |
| ROLL-021 | candidate-R5 | v4 | 37.8 | minutes | current |
| ROLL-022 | schema-12 | v4 | 36.0 | minutes | current |
| ROLL-023 | schema-13 | v4 | 37.1 | minutes | current |
| ROLL-024 | candidate-R4 | v4 | 35.3 | minutes | current |
| ROLL-025 | candidate-R5 | v4 | 36.4 | minutes | current |
| ROLL-026 | schema-12 | v4 | 37.5 | minutes | current |
| ROLL-027 | schema-13 | v4 | 35.7 | minutes | current |
| ROLL-028 | candidate-R4 | v5 | 36.8 | minutes | current |
| ROLL-029 | candidate-R5 | v5 | 35.0 | minutes | current |
| ROLL-030 | schema-12 | v5 | 36.1 | minutes | current |
| ROLL-031 | schema-13 | v5 | 37.2 | minutes | current |
| ROLL-032 | candidate-R4 | v5 | 35.4 | minutes | current |
| ROLL-033 | candidate-R5 | v5 | 36.5 | minutes | current |
| ROLL-034 | schema-12 | v5 | 37.6 | minutes | superseded |
| ROLL-035 | schema-13 | v5 | 35.8 | minutes | current |
| ROLL-036 | candidate-R4 | v5 | 36.9 | minutes | current |
| ROLL-037 | candidate-R5 | v5 | 35.1 | minutes | current |
| ROLL-038 | schema-12 | v5 | 36.2 | minutes | current |
| ROLL-039 | schema-13 | v5 | 37.3 | minutes | current |
| ROLL-040 | candidate-R4 | v5 | 35.5 | minutes | current |
| ROLL-041 | candidate-R5 | v5 | 36.6 | minutes | current |

## Decision constraints

Preserve candidate IDs, schema compatibility, write-history condition, duration, and stale-check rule.
State rollback owner, trigger, exact preconditions, effect uptake, recheck, and abandonment condition.
