# Solace Evidence and Decision Matrix

| ID | Source | Fact/Constraint | Unit/Status | Dependencies/Conflicts | Unknowns/Currency | Citation |
|---|---|---|---|---|---|---|
| AUR-01 | AURORA | Emergency restoration authority separated from public-health and communication closure authority. | Authority / Current | Binds NEXUS review, JASPER materiality, LUMEN advisory state. | Owner acceptance required for closure; stale if role-policy mutates. | [AURORA] |
| BAS-01 | BASTION | Hydraulic pressure, storage, isolation, residence time, and candidate-bound hydraulics govern zone control. | Pressure/Volume / Current | Isolates zones when triggers met; depends on INDIGO telemetry currency. | Stale if valve map V8 or controller firmware C11 changes. | [BASTION] |
| CIP-01 | CIPHER | Sampling rounds, spacing, detection limits, action thresholds, and staleness define clearance evidence. | Conc/Limit / Current | Must sample each materially different source path per GARNET. | Second-round samples incomplete; stale if source-water blend changes. | [CIPHER] |
| DEL-01 | DELTA | Pump capacity, shared-main limits, staged demand, and cavitation constraints bound flow restoration. | Flow/Head / Current | Competes with FALCON for ECHO capacity; depends on KESTREL staffing. | Stale if pump plan P9 or demand ramp changes. | [DELTA] |
| ECH-01 | ECHO | Grid rated 8.2 MW, usable 6.5 MW; generator 4.1 MW for 36 hours at current fuel. | Power/Duration / Current | Transfer drill stale for switchgear SW-9; KESTREL fuel controls duration. | Usable vs rated power must not swap; stale if switchgear version changes. | [ECHO] |
| FAL-01 | FALCON | Turbidity 0.18 NTU (gate ≤0.30 NTU for 4h); Cl₂ 0.8–2.0 mg/L entry, ≥0.2 mg/L distribution. | NTU/mg/L / Current | Contact time, UV, and source blend changes stale prior verification. | Entry vs distribution thresholds distinct; stale if treatment plan T6 changes. | [FALCON] |
| GAR-01 | GARNET | Ash-plume 34% forecast (not measured) intake impact; VOC non-detect reservoir, 3.1 µg/L river intake. | %/µg/L / Current | Investigation hold active for chemical yard (trench uninspected). | Forecast vs observation distinct; stale if rain event or inspection occurs. | [GARNET] |
| HEL-01 | HELIX | SCADA token revoked 14:10 UTC; controller key current under W4; break-glass expires in 2h with dual approval. | Time/Key / Current | Immutable logging required; retention 90d online, 7y incident. | Remote automation restoration requires named evidence; stale if key-set mutates. | [HELIX] |
| IND-01 | INDIGO | Critical-signal coverage 96%; pressure warning 38 psi, isolation trigger 30 psi; delay p95 700ms, p99 1200ms. | %/Psi/ms / Current | Coverage ≠ confidence; warnings vs actions distinct. | Uninstrumented zones unproven; stale if telemetry config changes. | [INDIGO] |
| JAS-01 | JASPER | Material unauthorized discharge notice within 72h of determination; dechlorination residual >0.019 mg/L at outfall stops discharge. | Hours/mg/L / Current | Permit E-17 governs emergency dechlorination; 7y retention with provenance. | Determination event unknown until AURORA materiality decision. | [JASPER] |
| KES-01 | KESTREL | Diesel 36h emergency load, 22h full pump load; coagulant 4.5d, chlorine 3.2d; 6 operators at 06:00 UTC ±90min. | Hours/Days / Current | Fuel controls ECHO duration; chemicals control FALCON staging. | Inventory ≠ delivery lead time; stale if consumption regime changes. | [KESTREL] |
| LUM-01 | LUMEN | Do-not-drink reached 91% endpoints; call center 3,200/hr for 6h vs forecast 4,100/hr. | %/Contacts / Current | States: do-not-use, do-not-drink, boil-water, restricted, cleared. | Low pressure ≠ contamination; stale if advisory status changes. | [LUMEN] |
| MOS-01 | MOSAIC | Current candidate W7 (H12, P9, T6, W4); rollback to W6 requires V8/C11 compatibility. | Version / Current | Every mutation records before/after hashes, files, effects, checks. | Mechanical possibility ≠ authorization; stale if any component mutates. | [MOSAIC] |
| NEX-01 | NEXUS | 16 open findings (5 hydraulic, 4 treatment, 3 sampling, 2 power, 2 comm); blockers: samples, generator transfer, PHO acknowledgment. | Findings / Current | Independent review separate from execution; no self-authorization. | Residual risk acceptance required; stale if blocking controls change. | [NEXUS] |

## Cross-Source Dependencies & Staleness Triggers

- **Hydraulics**: BASTION isolation depends on INDIGO pressure triggers (30 psi action vs 38 psi warning) and MOSAIC candidate W7 currency.
- **Treatment**: FALCON verification stale if GARNET source blend, BASTION residence time, CIPHER sampling, or DELTA demand ramps change.
- **Power**: ECHO generator duration controlled by KESTREL fuel stock; transfer evidence stale for switchgear SW-9.
- **Security**: HELIX remote automation requires current key-set W4, immutable logging, and AURORA authorization; stale if role-policy mutates.
- **Environmental**: JASPER 72h notice clock starts at AURORA materiality determination, not detection; dechlorination stop threshold 0.019 mg/L.
- **Readiness**: NEXUS blocking findings (samples, generator transfer, PHO acknowledgment) must be resolved with current candidate-bound evidence before independent readiness acceptance.

## Unit & Threshold Preservation Rules

- Psi ≠ kPa; gallons ≠ treated reserve; µg/L ≠ mg/L; reporting limit ≠ action threshold.
- Percentage coverage ≠ confidence; rated power ≠ usable power; nameplate capacity ≠ shared capacity.
- Warning threshold (38 psi) ≠ isolation trigger (30 psi); forecast probability (34%) ≠ measured concentration.
- Mechanical checks ≠ public-health readiness ≠ independent acceptance.

## Candidate Currency & Blockers

- Current candidate: W7 (H12, P9, T6, W4).
- Blocking findings: incomplete second-round samples [CIPHER], stale generator transfer evidence [ECHO], missing PHO acknowledgment [AURORA/NEXUS].
- Investigation hold: chemical yard trench uninspected [GARNET].
- Rollback to W6 mechanically possible only while V8/C11 compatible; not authorized.

## Falsifiers for Important Claims

- If turbidity exceeds 0.30 NTU for 4h, treatment verification falsified [FALCON].
- If Cl₂ residual <0.8 mg/L at entry or <0.2 mg/L in distribution, disinfection claim falsified [FALCON].
- If pressure drops below 30 psi, isolation trigger activated; warning-only claims falsified [INDIGO/BASTION].
- If VOC detected at reservoir (currently non-detect), source-path separation falsified [GARNET].
- If generator transfer fails under SW-9, continuity claim falsified [ECHO].
- If dechlorination residual >0.019 mg/L at outfall, permit compliance falsified [JASPER].