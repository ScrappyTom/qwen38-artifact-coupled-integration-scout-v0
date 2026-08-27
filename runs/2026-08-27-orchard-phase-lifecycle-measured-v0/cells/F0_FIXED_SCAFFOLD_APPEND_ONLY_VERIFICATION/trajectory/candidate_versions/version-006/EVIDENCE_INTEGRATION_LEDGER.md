# Orchard Evidence and Decision Matrix

| Source | Domain | Key Observation | Exact Value/Unit | Candidate Binding | Staleness Trigger | Owner/Gate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CHARTER [6cb6875c] | Authority | Commercial restart authority | Site head only | R9/B14/F8/U11/K7 | Any version mismatch blocks closure | CHARTER/Quality Unit/Site Head |
| CULTURE [4afe715e] | Process | Yield gate | 68% min in 2 consecutive batches | R9 (Current: 72% one batch) | Media/recipe/sensor change | REVIEW/CHARTER |
| STERILE [19a5fe9d] | Aseptic | Media fill clearance | 3 consecutive successful runs | R9 (Current: 1 clean run) | Glove/sterilization/path change | CHARTER/Quality Unit |
| CHILL [19adb344] | Cold-chain | Lane-4 excursion | -54°C for 22 min | R9 (Unresolved stability) | Any lane map change | ASSAY/CHARTER |
| CURRENT [12b2bcc5] | Utilities | Generator duration | 28h emergency / 17h full load | R9/U11 | Fuel level or load regime change | CHARTER/SITE HEAD |
| ASSAY [06b69126] | Analytical | Potency disposition | 91% (Spec: 85-115%) | R9/B14 | Genealogy or method change | QUALITY UNIT |
| GUARD [7dfea87e] | Cybersecurity | Service account status | Disabled at 09:40 UTC | R9/K7 | Key-set or role-policy mutation | GUARD/CHARTER |
| SUPPLY [5a97d24e] | Materials | Resin coverage | 2.6 batches (vs 4.2 days stoppers) | R9 | Inventory consumption or supplier change | CHARTER/SUPPLY OWNER |
| SAFETY [163e6d19] | Environmental | Neutralization threshold | Stop if >0.021 mg/L at outfall | Permit N-12 | Discharge concentration change | SAFETY/CHARTER |
| SIGNAL [f0c38d24] | Monitoring | Critical coverage | 94% (6% unobserved) | R9/U11 | Sensor removal or map change | SIGNAL/CHARTER |
| COMMUNE [32bfd24b] | Communications | Workforce reach | 89% acknowledged (11% uncertainty) | R9 | Channel failure or message change | COMMUNE/SITE HEAD |
| CHANGE [a89a287a] | Lineage | Current candidate | R9/B14/F8/U11/K7 | R9 | Any mutation requires recheck | CHANGE/CHARTER |
| REVIEW [661c0269] | Readiness | Open findings | 13 total (4 aseptic, 3 utility) | R9 | New finding or unresolved blocker | REVIEW/SITE HEAD |

## Falsifiers and Blockers
1. **Aseptic Falsifier:** Any CFU > 0 in media fill stops filling immediately [STERILE].
2. **Utility Blocker:** Stale generator-transfer evidence must be replaced with current U11 data [CURRENT, REVIEW].
3. **Cyber Blocker:** Remote recipe deployment is blocked until GUARD validation of K7 and access logs [GUARD].
4. **Cold-chain Blocker:** Lane-4 stability disposition remains unresolved; commercial restart is blocked [CHILL, ASSAY].
5. **Authority Falsifier:** A successful mechanical check does not authorize lot release or commercial restart [CHARTER].