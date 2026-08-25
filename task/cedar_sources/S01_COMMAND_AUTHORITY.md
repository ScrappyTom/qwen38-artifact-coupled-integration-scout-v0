# Cedar Valley command authority and evacuation powers

## Frozen findings

The county incident commander alone issues an evacuation order after receiving the fire-behavior recommendation. The sheriff executes traffic control, public health owns medical continuity, and the shelter branch operates sites; none of those supporting roles can independently declare the whole operation ready.
A voluntary warning may be issued before the statutory trigger. Mandatory orders must identify the exact zone revision and effective time. A vendor, dashboard, or model recommendation is advisory rather than closure authority.
Authority transfers at shift change require an acknowledged incident-action-plan revision. An unacknowledged handoff leaves the outgoing commander responsible and blocks a new readiness declaration.

## Governing relationships

Hazard triggers from S02 and S15 inform the commander but do not replace the legal order. Road controls in S04 become executable only after the sheriff acknowledges the same zone revision.
Candidate checks are current only for the exact plan and roster they evaluated. Any route, shelter, or fleet mutation requires a new readiness reconciliation.

## Operational evidence

| record | time | owner | zone | handoff | plan binding |
|---|---|---|---|---|---|
| AUTH-000 | +0000m | incident-commander | A-North | handoff-due | iap-r2 |
| AUTH-001 | +0015m | fire-behavior-lead | A-River | current | iap-r2 |
| AUTH-002 | +0030m | sheriff | B-East | current | iap-r2 |
| AUTH-003 | +0045m | public-health | B-Center | current | iap-r2 |
| AUTH-004 | +0060m | shelter-branch | C-South | current | iap-r2 |
| AUTH-005 | +0075m | incident-commander | C-Ridge | current | iap-r2 |
| AUTH-006 | +0090m | fire-behavior-lead | A-North | current | iap-r2 |
| AUTH-007 | +0105m | sheriff | A-River | current | iap-r2 |
| AUTH-008 | +0120m | public-health | B-East | current | iap-r2 |
| AUTH-009 | +0135m | shelter-branch | B-Center | handoff-due | iap-r2 |
| AUTH-010 | +0150m | incident-commander | C-South | current | iap-r2 |
| AUTH-011 | +0165m | fire-behavior-lead | C-Ridge | current | iap-r2 |
| AUTH-012 | +0180m | sheriff | A-North | current | iap-r2 |
| AUTH-013 | +0195m | public-health | A-River | current | iap-r2 |
| AUTH-014 | +0210m | shelter-branch | B-East | current | iap-r2 |
| AUTH-015 | +0225m | incident-commander | B-Center | current | iap-r2 |
| AUTH-016 | +0240m | fire-behavior-lead | C-South | current | iap-r3 |
| AUTH-017 | +0255m | sheriff | C-Ridge | current | iap-r3 |
| AUTH-018 | +0270m | public-health | A-North | handoff-due | iap-r3 |
| AUTH-019 | +0285m | shelter-branch | A-River | current | iap-r3 |
| AUTH-020 | +0300m | incident-commander | B-East | current | iap-r3 |
| AUTH-021 | +0315m | fire-behavior-lead | B-Center | current | iap-r3 |
| AUTH-022 | +0330m | sheriff | C-South | current | iap-r3 |
| AUTH-023 | +0345m | public-health | C-Ridge | current | iap-r3 |
| AUTH-024 | +0360m | shelter-branch | A-North | current | iap-r3 |
| AUTH-025 | +0375m | incident-commander | A-River | current | iap-r3 |
| AUTH-026 | +0390m | fire-behavior-lead | B-East | current | iap-r3 |
| AUTH-027 | +0405m | sheriff | B-Center | handoff-due | iap-r3 |
| AUTH-028 | +0420m | public-health | C-South | current | iap-r3 |
| AUTH-029 | +0435m | shelter-branch | C-Ridge | current | iap-r3 |
| AUTH-030 | +0450m | incident-commander | A-North | current | iap-r3 |
| AUTH-031 | +0465m | fire-behavior-lead | A-River | current | iap-r3 |
| AUTH-032 | +0480m | sheriff | B-East | current | iap-r4 |
| AUTH-033 | +0495m | public-health | B-Center | current | iap-r4 |
| AUTH-034 | +0510m | shelter-branch | C-South | current | iap-r4 |
| AUTH-035 | +0525m | incident-commander | C-Ridge | current | iap-r4 |
| AUTH-036 | +0540m | fire-behavior-lead | A-North | handoff-due | iap-r4 |
| AUTH-037 | +0555m | sheriff | A-River | current | iap-r4 |
| AUTH-038 | +0570m | public-health | B-East | current | iap-r4 |
| AUTH-039 | +0585m | shelter-branch | B-Center | current | iap-r4 |
| AUTH-040 | +0600m | incident-commander | C-South | current | iap-r4 |
| AUTH-041 | +0615m | fire-behavior-lead | C-Ridge | current | iap-r4 |
| AUTH-042 | +0630m | sheriff | A-North | current | iap-r4 |
| AUTH-043 | +0645m | public-health | A-River | current | iap-r4 |
| AUTH-044 | +0660m | shelter-branch | B-East | current | iap-r4 |
| AUTH-045 | +0675m | incident-commander | B-Center | handoff-due | iap-r4 |
| AUTH-046 | +0690m | fire-behavior-lead | C-South | current | iap-r4 |
| AUTH-047 | +0705m | sheriff | C-Ridge | current | iap-r4 |

## Decision constraints

The decision must distinguish recommendation, legal order, execution, verification, and closure authority.
No single branch may waive a blocking road, medical, communications, or shelter condition.
