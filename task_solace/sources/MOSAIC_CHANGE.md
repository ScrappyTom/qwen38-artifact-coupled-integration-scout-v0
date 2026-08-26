# Candidate lineage, rollback, and configuration control

## Frozen findings

The current recovery candidate is W7 with hydraulic model H12, pump plan P9, treatment plan T6, and key set W4. Evidence for W6 is historical unless explicitly transferred and rechecked.
Rollback to W6 is mechanically possible only while valve map V8 and controller firmware C11 remain compatible. Mechanical possibility is not authorization.
Every mutation must record before and after candidate hashes, changed files, affected evidence, check currency, owner, and rollback effect.

## Governing relationships

BASTION, CIPHER, DELTA, ECHO, FALCON, and HELIX observations can become stale after MOSAIC candidate changes.
NEXUS reviews current-candidate evidence independently; AURORA authorizes execution and closure separately.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| CHG-000 | hydraulic-model | v2 | 7.0 | candidate-index | superseded |
| CHG-001 | pump-plan | v2 | 8.3 | candidate-index | current |
| CHG-002 | treatment-plan | v2 | 9.6 | candidate-index | current |
| CHG-003 | key-set | v2 | 7.8 | candidate-index | current |
| CHG-004 | hydraulic-model | v2 | 9.1 | candidate-index | current |
| CHG-005 | pump-plan | v2 | 7.3 | candidate-index | current |
| CHG-006 | treatment-plan | v2 | 8.6 | candidate-index | current |
| CHG-007 | key-set | v2 | 9.9 | candidate-index | current |
| CHG-008 | hydraulic-model | v2 | 8.1 | candidate-index | current |
| CHG-009 | pump-plan | v2 | 9.4 | candidate-index | current |
| CHG-010 | treatment-plan | v2 | 7.6 | candidate-index | current |
| CHG-011 | key-set | v2 | 8.9 | candidate-index | current |
| CHG-012 | hydraulic-model | v2 | 7.1 | candidate-index | current |
| CHG-013 | pump-plan | v2 | 8.4 | candidate-index | current |
| CHG-014 | treatment-plan | v3 | 9.7 | candidate-index | current |
| CHG-015 | key-set | v3 | 7.9 | candidate-index | current |
| CHG-016 | hydraulic-model | v3 | 9.2 | candidate-index | current |
| CHG-017 | pump-plan | v3 | 7.4 | candidate-index | current |
| CHG-018 | treatment-plan | v3 | 8.7 | candidate-index | current |
| CHG-019 | key-set | v3 | 10.0 | candidate-index | superseded |
| CHG-020 | hydraulic-model | v3 | 8.2 | candidate-index | current |
| CHG-021 | pump-plan | v3 | 9.5 | candidate-index | current |
| CHG-022 | treatment-plan | v3 | 7.7 | candidate-index | current |
| CHG-023 | key-set | v3 | 9.0 | candidate-index | current |
| CHG-024 | hydraulic-model | v3 | 7.2 | candidate-index | current |
| CHG-025 | pump-plan | v3 | 8.5 | candidate-index | current |
| CHG-026 | treatment-plan | v3 | 9.8 | candidate-index | current |
| CHG-027 | key-set | v3 | 8.0 | candidate-index | current |
| CHG-028 | hydraulic-model | v4 | 9.3 | candidate-index | current |
| CHG-029 | pump-plan | v4 | 7.5 | candidate-index | current |
| CHG-030 | treatment-plan | v4 | 8.8 | candidate-index | current |
| CHG-031 | key-set | v4 | 7.0 | candidate-index | current |
| CHG-032 | hydraulic-model | v4 | 8.3 | candidate-index | current |
| CHG-033 | pump-plan | v4 | 9.6 | candidate-index | current |
| CHG-034 | treatment-plan | v4 | 7.8 | candidate-index | current |
| CHG-035 | key-set | v4 | 9.1 | candidate-index | current |
| CHG-036 | hydraulic-model | v4 | 7.3 | candidate-index | current |
| CHG-037 | pump-plan | v4 | 8.6 | candidate-index | current |
| CHG-038 | treatment-plan | v4 | 9.9 | candidate-index | superseded |
| CHG-039 | key-set | v4 | 8.1 | candidate-index | current |
| CHG-040 | hydraulic-model | v4 | 9.4 | candidate-index | current |
| CHG-041 | pump-plan | v4 | 7.6 | candidate-index | current |

## Decision constraints

Keep candidate, model, pump, treatment, key, valve, and firmware versions explicit.
Require effect uptake, current check, repair, recheck, and rollback evidence.
