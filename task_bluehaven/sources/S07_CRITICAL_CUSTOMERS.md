# Hospitals, dialysis, care facilities, and accessibility

## Frozen findings

Bluehaven Hospital requires 0.9 megaliters per day and at least 28 psi; North Dialysis needs 0.18 and a verified low-conductivity supply. Three care facilities require 0.42 combined.
There are 64 registered home dialysis or immune-compromised households, with eleven duplicate entries across programs. Assignments must be person-level and private.
The hospital has six hours of potable storage. A generic tanker is not a clinical supply until hose, disinfection, testing, pressure, and custody pass.

## Governing relationships

S05 pressure, S08 tanker specification, S09 sample release, and S13 privacy jointly constrain critical-customer continuity.
Public reporting may aggregate service status but may not reveal individual medical need or delivery address.

## Operational evidence

| record | asset/zone | revision | measure | unit | status |
|---|---|---|---:|---|---|
| CARE-000 | Bluehaven-Hospital | r2 | 2.8 | ML/day | hold |
| CARE-001 | North-Dialysis | r2 | 3.5 | ML/day | current |
| CARE-002 | Harbor-Care | r2 | 4.2 | ML/day | current |
| CARE-003 | home-oxygen | r2 | 4.9 | ML/day | current |
| CARE-004 | Bluehaven-Hospital | r2 | 5.6 | ML/day | current |
| CARE-005 | North-Dialysis | r2 | 3.2 | ML/day | current |
| CARE-006 | Harbor-Care | r2 | 3.9 | ML/day | current |
| CARE-007 | home-oxygen | r2 | 4.6 | ML/day | current |
| CARE-008 | Bluehaven-Hospital | r2 | 5.3 | ML/day | current |
| CARE-009 | North-Dialysis | r2 | 2.9 | ML/day | current |
| CARE-010 | Harbor-Care | r2 | 3.6 | ML/day | current |
| CARE-011 | home-oxygen | r2 | 4.3 | ML/day | current |
| CARE-012 | Bluehaven-Hospital | r2 | 5.0 | ML/day | current |
| CARE-013 | North-Dialysis | r2 | 5.7 | ML/day | hold |
| CARE-014 | Harbor-Care | r2 | 3.3 | ML/day | current |
| CARE-015 | home-oxygen | r2 | 4.0 | ML/day | current |
| CARE-016 | Bluehaven-Hospital | r3 | 4.7 | ML/day | current |
| CARE-017 | North-Dialysis | r3 | 5.4 | ML/day | current |
| CARE-018 | Harbor-Care | r3 | 3.0 | ML/day | current |
| CARE-019 | home-oxygen | r3 | 3.7 | ML/day | current |
| CARE-020 | Bluehaven-Hospital | r3 | 4.4 | ML/day | current |
| CARE-021 | North-Dialysis | r3 | 5.1 | ML/day | current |
| CARE-022 | Harbor-Care | r3 | 5.8 | ML/day | current |
| CARE-023 | home-oxygen | r3 | 3.4 | ML/day | current |
| CARE-024 | Bluehaven-Hospital | r3 | 4.1 | ML/day | current |
| CARE-025 | North-Dialysis | r3 | 4.8 | ML/day | current |
| CARE-026 | Harbor-Care | r3 | 5.5 | ML/day | hold |
| CARE-027 | home-oxygen | r3 | 3.1 | ML/day | current |
| CARE-028 | Bluehaven-Hospital | r3 | 3.8 | ML/day | current |
| CARE-029 | North-Dialysis | r3 | 4.5 | ML/day | current |
| CARE-030 | Harbor-Care | r3 | 5.2 | ML/day | current |
| CARE-031 | home-oxygen | r3 | 2.8 | ML/day | current |
| CARE-032 | Bluehaven-Hospital | r4 | 3.5 | ML/day | current |
| CARE-033 | North-Dialysis | r4 | 4.2 | ML/day | current |
| CARE-034 | Harbor-Care | r4 | 4.9 | ML/day | current |
| CARE-035 | home-oxygen | r4 | 5.6 | ML/day | current |
| CARE-036 | Bluehaven-Hospital | r4 | 3.2 | ML/day | current |
| CARE-037 | North-Dialysis | r4 | 3.9 | ML/day | current |
| CARE-038 | Harbor-Care | r4 | 4.6 | ML/day | current |
| CARE-039 | home-oxygen | r4 | 5.3 | ML/day | hold |
| CARE-040 | Bluehaven-Hospital | r4 | 2.9 | ML/day | current |
| CARE-041 | North-Dialysis | r4 | 3.6 | ML/day | current |
| CARE-042 | Harbor-Care | r4 | 4.3 | ML/day | current |
| CARE-043 | home-oxygen | r4 | 5.0 | ML/day | current |
| CARE-044 | Bluehaven-Hospital | r4 | 5.7 | ML/day | current |
| CARE-045 | North-Dialysis | r4 | 3.3 | ML/day | current |
| CARE-046 | Harbor-Care | r4 | 4.0 | ML/day | current |
| CARE-047 | home-oxygen | r4 | 4.7 | ML/day | current |

## Decision constraints

Bind every critical cohort to source, transport, testing, delivery, storage, and handoff.
Treat any unmatched clinical need or sub-28-psi hospital plan as blocking.
