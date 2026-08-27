# Solace Evidence and Decision Matrix

| ID | Domain | Source | Fact/Observation | Unit/Value | Status | Dependencies | Conflicts/Unknowns | Candidate Currency | Citations |
|---|---|---|---|---|---|---|---|---|---|
| E-01 | Authority | AURORA | County health officer lifts do-not-drink only after current lab/distribution verification | n/a | Active | CIPHER, BASTION | Utility repair ≠ public-health authorization | W7 | [AURORA] |
| E-02 | Authority | AURORA | Final closure requires utility director acceptance of all blockers/risks | n/a | Active | NEXUS | Residual risk must be explicit | W7 | [AURORA] |
| E-03 | Hydraulic | BASTION | Min distribution pressure north zone | 42 psi | Current | DELTA, ECHO | Warning 38 psi vs Isolation 30 psi distinct | W7/H12 | [BASTION] |
| E-04 | Hydraulic | BASTION | Ridge storage volume / 12-hr emergency reserve | 5.8M gal / 3.2M gal | Current | DELTA | Gallons vs treated reserve distinct | W7/H12 | [BASTION] |
| E-05 | Sampling | CIPHER | Clearance requires two complete rounds ≥16 hours apart | n/a | Active | BASTION, GARNET | One clean round insufficient | W7 | [CIPHER] |
| E-06 | Sampling | CIPHER | Benzene reporting limit / action threshold | 0.5 µg/L / 5.0 µg/L | Current | GARNET | Reporting limit ≠ action threshold; µg/L not mg/L | W7 | [CIPHER] |
| E-07 | Pump | DELTA | Pump sequencing depends on BASTION pressure and ECHO power | n/a | Active | BASTION, ECHO | Cavitation constraints apply | W7/P9 | [DELTA] |
| E-08 | Power | ECHO | Emergency generation capacity/duration | 4.1 MW / 36 hrs | Current | KESTREL | Excludes mobile-pump load; not 36 days | W7 | [ECHO] |
| E-09 | Power | ECHO | Grid feed rated vs usable power | 8.2 MW rated / 6.5 MW usable | Current | DELTA | Damaged switchgear limits delivery | W7 | [ECHO] |
| E-10 | Treatment | FALCON | Free chlorine entry vs distribution thresholds | 0.8–2.0 mg/L entry / ≥0.2 mg/L dist | Current | INDIGO | Entry and distribution controls distinct; mg/L not µg/L | W7/T6 | [FALCON] |
| E-11 | Treatment | FALCON | Combined-filter turbidity current vs release gate | 0.18 NTU / ≤0.30 NTU (4 hrs) | Current | INDIGO | 0.18 NTU is not chlorine residual | W7/T6 | [FALCON] |
| E-12 | Source | GARNET | Ash-plume intake impact probability next rain | 34% forecast | Active | CIPHER, FALCON | Forecast probability ≠ measured contamination; reservoir vs river intake distinct | W7 | [GARNET] |
| E-13 | Source | GARNET | Chemical yard investigation hold active | n/a | Active | CIPHER | Containment trench not inspected below grade | W7 | [GARNET] |
| E-14 | Access | HELIX | SCADA token revoked; controller key current (W4) | n/a | Current | INDIGO, MOSAIC | Break-glass expires 2 hrs + dual approval; emergency ≠ continuing auth | W7/W4 | [HELIX] |
| E-15 | Telemetry | INDIGO | Critical-signal coverage | 96% covered / 4% unobserved | Current | BASTION, DELTA, ECHO, FALCON | Coverage ≠ confidence; uninstrumented zones not proven healthy | W7 | [INDIGO] |
| E-16 | Telemetry | INDIGO | Pressure warning vs isolation trigger | 38 psi warn / 30 psi isolate | Current | BASTION | Warning and action thresholds must remain distinct | W7 | [INDIGO] |
| E-17 | Environmental | JASPER | Unauthorized discharge notice clock | 72 hours from determination | Active | GARNET, FALCON, LUMEN | Determination event ≠ detection time; AURORA owns materiality | W7 | [JASPER] |
| E-18 | Environmental | JASPER | Emergency dechlorination residual limit | ≤0.019 mg/L at outfall | Current | FALCON | Immediate stop required if exceeded; permit E-17 | W7 | [JASPER] |
| E-19 | Logistics | KESTREL | Diesel stock coverage emergency vs full pump load | 36 hrs / 22 hrs | Current | ECHO, DELTA | Load regimes distinct; not days | W7 | [KESTREL] |
| E-20 | Logistics | KESTREL | Coagulant/chlorine stock duration | 4.5 days / 3.2 days | Current | FALCON | Inventory duration ≠ delivery lead time | W7 | [KESTREL] |
| E-21 | Public | LUMEN | Do-not-drink notice delivery coverage | 91% registered endpoints | Current | CIPHER, AURORA | Missing 9% is comm uncertainty, not pop reduction | W7 | [LUMEN] |
| E-22 | Public | LUMEN | Call center capacity vs forecast demand | 3,200/hr (6 hrs) / 4,100/hr forecast | Current | KESTREL | Alternate-language outreach may reduce repeats | W7 | [LUMEN] |
| E-23 | Change | MOSAIC | Current recovery candidate | W7 (H12, P9, T6, W4) | Current | ALL | W6 evidence historical unless transferred/rechecked | W7 | [MOSAIC] |
| E-24 | Change | MOSAIC | Rollback to W6 mechanical possibility | Valve map V8 + firmware C11 compatible | Active | BASTION, CIPHER, DELTA, ECHO, FALCON, HELIX | Mechanical possibility ≠ authorization | W7→W6 | [MOSAIC] |
| E-25 | Readiness | NEXUS | Open findings count | 16 (5 hyd, 4 treat, 3 samp, 2 pow, 2 comm) | Current | ALL | Finding count ≠ readiness percentage | W7 | [NEXUS] |
| E-26 | Readiness | NEXUS | Blocking findings | Incomplete 2nd-round samples; stale gen transfer evidence; missing PH duty officer ack | Active | CIPHER, ECHO, AURORA | Independent review required; no self-authorization | W7 | [NEXUS] |

## Cross-Source Dependencies
- CIPHER sampling consumes BASTION flow paths and GARNET hypotheses [CIPHER, BASTION, GARNET].
- DELTA pump sequencing depends on BASTION pressure and ECHO power [DELTA, BASTION, ECHO].
- FALCON treatment selection depends on GARNET source hypotheses [FALCON, GARNET].
- INDIGO telemetry supports BASTION, DELTA, ECHO, FALCON but each retains own decision gate [INDIGO, BASTION, DELTA, ECHO, FALCON].
- HELIX audit events consumed by INDIGO; HELIX does not authorize access [HELIX, INDIGO].
- JASPER environmental notices depend on GARNET source impact and FALCON discharge conditions [JASPER, GARNET, FALCON].
- KESTREL fuel supports ECHO generator duration; KESTREL chemicals support FALCON staging [KESTREL, ECHO, FALCON].
- LUMEN communications depend on CIPHER/AURORA advisory status and INDIGO/BASTION service observations [LUMEN, CIPHER, AURORA, INDIGO, BASTION].
- MOSAIC candidate changes make BASTION, CIPHER, DELTA, ECHO, FALCON, HELIX evidence stale [MOSAIC, BASTION, CIPHER, DELTA, ECHO, FALCON, HELIX].
- NEXUS consumes all sources for independent review but does not mutate states [NEXUS, ALL].

## Conflicts and Unknowns
- GARNET ash-plume 34% is forecast, not observed contamination; reservoir (non-detect) vs river intake (3.1 µg/L) must not be merged [GARNET].
- Chemical yard investigation hold active; trench inspection below grade pending [GARNET].
- INDIGO 4% unobserved coverage does not prove healthy uninstrumented zones [INDIGO].
- HELIX break-glass access expired; remote automation restoration requires named evidence [HELIX].
- NEXUS blocking findings: second-round samples incomplete, generator transfer evidence stale, PH duty officer acknowledgment missing [NEXUS].

## Candidate Currency
Current candidate W7 (H12, P9, T6, W4) [MOSAIC]. Any mutation to hydraulic model, pump plan, treatment plan, key set, valve map, or firmware makes prior evidence stale and requires recheck [MOSAIC]. Rollback to W6 mechanically possible only with V8/C11 compatibility but not authorized [MOSAIC].

## Falsifiers for Important Claims
- If CIPHER second-round samples show benzene ≥5.0 µg/L at any location, clearance claim falsified [CIPHER].
- If ECHO generator transfer evidence remains stale after recheck, 36-hr duration claim falsified [ECHO].
- If AURORA public-health duty officer does not acknowledge, closure claim falsified [AURORA].
- If FALCON turbidity exceeds 0.30 NTU for >4 hrs, release gate claim falsified [FALCON].
- If INDIGO coverage drops below 96% or unobserved zones show adverse conditions, telemetry adequacy claim falsified [INDIGO].