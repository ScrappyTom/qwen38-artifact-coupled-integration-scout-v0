# Medical continuity and accessibility matching

## Frozen findings

Seventy-three residents use continuous oxygen, twenty-eight have dialysis due within twenty-four hours, and fourteen medications require refrigeration. The lists overlap and contain seven duplicate household records.
Cedar Hospital can accept twenty-two oxygen-dependent evacuees, North Clinic thirty-seven, and verified home oxygen kits cover twenty more. Those capacities total seventy-nine only if transport, power, and patient matching all pass.
A generic shelter cot is not a medical placement. Public health must bind each high-acuity person to transport, destination, power, medication custody, and handoff confirmation.

## Governing relationships

S03 defines uncertain demand, S05 constrains accessible vehicles, S06 constrains destinations, and S09 constrains power/fuel. The medical plan is a joined assignment rather than four independent capacity claims.
Public status messages may not expose health needs; the private roster rules in S12 govern matching and deletion.

## Operational evidence

| record | zone | need | people | pickup ETA | match | roster |
|---|---|---|---|---|---|---|
| CARE-000 | A-North | oxygen | 2 | 20m | transport-unassigned | health-roster-r5 |
| CARE-001 | A-River | dialysis | 9 | 37m | matched | health-roster-r5 |
| CARE-002 | B-East | refrigerated-medication | 16 | 54m | matched | health-roster-r5 |
| CARE-003 | B-Center | wheelchair | 23 | 71m | matched | health-roster-r5 |
| CARE-004 | C-South | behavioral-support | 6 | 88m | matched | health-roster-r5 |
| CARE-005 | C-Ridge | oxygen | 13 | 30m | matched | health-roster-r5 |
| CARE-006 | A-North | dialysis | 20 | 47m | matched | health-roster-r5 |
| CARE-007 | A-River | refrigerated-medication | 3 | 64m | matched | health-roster-r5 |
| CARE-008 | B-East | wheelchair | 10 | 81m | matched | health-roster-r5 |
| CARE-009 | B-Center | behavioral-support | 17 | 23m | transport-unassigned | health-roster-r5 |
| CARE-010 | C-South | oxygen | 24 | 40m | matched | health-roster-r5 |
| CARE-011 | C-Ridge | dialysis | 7 | 57m | matched | health-roster-r5 |
| CARE-012 | A-North | refrigerated-medication | 14 | 74m | matched | health-roster-r5 |
| CARE-013 | A-River | wheelchair | 21 | 91m | matched | health-roster-r5 |
| CARE-014 | B-East | behavioral-support | 4 | 33m | matched | health-roster-r5 |
| CARE-015 | B-Center | oxygen | 11 | 50m | matched | health-roster-r5 |
| CARE-016 | C-South | dialysis | 18 | 67m | matched | health-roster-r5 |
| CARE-017 | C-Ridge | refrigerated-medication | 25 | 84m | matched | health-roster-r5 |
| CARE-018 | A-North | wheelchair | 8 | 26m | transport-unassigned | health-roster-r5 |
| CARE-019 | A-River | behavioral-support | 15 | 43m | matched | health-roster-r5 |
| CARE-020 | B-East | oxygen | 22 | 60m | matched | health-roster-r5 |
| CARE-021 | B-Center | dialysis | 5 | 77m | matched | health-roster-r5 |
| CARE-022 | C-South | refrigerated-medication | 12 | 94m | matched | health-roster-r5 |
| CARE-023 | C-Ridge | wheelchair | 19 | 36m | matched | health-roster-r5 |
| CARE-024 | A-North | behavioral-support | 2 | 53m | matched | health-roster-r5 |
| CARE-025 | A-River | oxygen | 9 | 70m | matched | health-roster-r5 |
| CARE-026 | B-East | dialysis | 16 | 87m | matched | health-roster-r5 |
| CARE-027 | B-Center | refrigerated-medication | 23 | 29m | transport-unassigned | health-roster-r5 |
| CARE-028 | C-South | wheelchair | 6 | 46m | matched | health-roster-r5 |
| CARE-029 | C-Ridge | behavioral-support | 13 | 63m | matched | health-roster-r5 |
| CARE-030 | A-North | oxygen | 20 | 80m | matched | health-roster-r5 |
| CARE-031 | A-River | dialysis | 3 | 22m | matched | health-roster-r5 |
| CARE-032 | B-East | refrigerated-medication | 10 | 39m | matched | health-roster-r5 |
| CARE-033 | B-Center | wheelchair | 17 | 56m | matched | health-roster-r5 |
| CARE-034 | C-South | behavioral-support | 24 | 73m | matched | health-roster-r5 |
| CARE-035 | C-Ridge | oxygen | 7 | 90m | matched | health-roster-r5 |
| CARE-036 | A-North | dialysis | 14 | 32m | transport-unassigned | health-roster-r5 |
| CARE-037 | A-River | refrigerated-medication | 21 | 49m | matched | health-roster-r5 |
| CARE-038 | B-East | wheelchair | 4 | 66m | matched | health-roster-r5 |
| CARE-039 | B-Center | behavioral-support | 11 | 83m | matched | health-roster-r5 |
| CARE-040 | C-South | oxygen | 18 | 25m | matched | health-roster-r5 |
| CARE-041 | C-Ridge | dialysis | 25 | 42m | matched | health-roster-r5 |
| CARE-042 | A-North | refrigerated-medication | 8 | 59m | matched | health-roster-r5 |
| CARE-043 | A-River | wheelchair | 15 | 76m | matched | health-roster-r5 |
| CARE-044 | B-East | behavioral-support | 22 | 93m | matched | health-roster-r5 |
| CARE-045 | B-Center | oxygen | 5 | 35m | transport-unassigned | health-roster-r5 |
| CARE-046 | C-South | dialysis | 12 | 52m | matched | health-roster-r5 |
| CARE-047 | C-Ridge | refrigerated-medication | 19 | 69m | matched | health-roster-r5 |

## Decision constraints

Require person-level private matching with aggregate public reporting.
Treat any unmatched oxygen, dialysis, or refrigerated-medication case as a blocker.
