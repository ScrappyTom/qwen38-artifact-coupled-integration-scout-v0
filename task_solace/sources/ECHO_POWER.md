# Grid, generator, and fuel continuity

## Frozen findings

The grid feed is rated at 8.2 MW, but the damaged switchgear limits current delivery to 6.5 MW. Rating and currently usable power must not be swapped.
Emergency generation can carry 4.1 MW for thirty-six hours at the current fuel stock. The duration is not thirty-six days and excludes mobile-pump load.
Automatic transfer succeeded in the latest drill, but the observation predates switchgear version SW-9 and is stale for the current candidate.

## Governing relationships

DELTA pump stages and FALCON treatment trains compete for ECHO capacity. KESTREL fuel delivery controls generator duration.
INDIGO telemetry is required to validate voltage and transfer stability; a control-room display alone is insufficient.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| PWR-000 | substation-a | v2 | 6.5 | megawatts | superseded |
| PWR-001 | substation-b | v2 | 7.8 | megawatts | current |
| PWR-002 | generator-1 | v2 | 9.1 | megawatts | current |
| PWR-003 | fuel-yard | v2 | 7.3 | megawatts | current |
| PWR-004 | substation-a | v2 | 8.6 | megawatts | current |
| PWR-005 | substation-b | v2 | 6.8 | megawatts | current |
| PWR-006 | generator-1 | v2 | 8.1 | megawatts | current |
| PWR-007 | fuel-yard | v2 | 9.4 | megawatts | current |
| PWR-008 | substation-a | v2 | 7.6 | megawatts | current |
| PWR-009 | substation-b | v2 | 8.9 | megawatts | current |
| PWR-010 | generator-1 | v2 | 7.1 | megawatts | current |
| PWR-011 | fuel-yard | v2 | 8.4 | megawatts | current |
| PWR-012 | substation-a | v2 | 6.6 | megawatts | current |
| PWR-013 | substation-b | v2 | 7.9 | megawatts | current |
| PWR-014 | generator-1 | v3 | 9.2 | megawatts | current |
| PWR-015 | fuel-yard | v3 | 7.4 | megawatts | current |
| PWR-016 | substation-a | v3 | 8.7 | megawatts | current |
| PWR-017 | substation-b | v3 | 6.9 | megawatts | current |
| PWR-018 | generator-1 | v3 | 8.2 | megawatts | current |
| PWR-019 | fuel-yard | v3 | 9.5 | megawatts | superseded |
| PWR-020 | substation-a | v3 | 7.7 | megawatts | current |
| PWR-021 | substation-b | v3 | 9.0 | megawatts | current |
| PWR-022 | generator-1 | v3 | 7.2 | megawatts | current |
| PWR-023 | fuel-yard | v3 | 8.5 | megawatts | current |
| PWR-024 | substation-a | v3 | 6.7 | megawatts | current |
| PWR-025 | substation-b | v3 | 8.0 | megawatts | current |
| PWR-026 | generator-1 | v3 | 9.3 | megawatts | current |
| PWR-027 | fuel-yard | v3 | 7.5 | megawatts | current |
| PWR-028 | substation-a | v4 | 8.8 | megawatts | current |
| PWR-029 | substation-b | v4 | 7.0 | megawatts | current |
| PWR-030 | generator-1 | v4 | 8.3 | megawatts | current |
| PWR-031 | fuel-yard | v4 | 6.5 | megawatts | current |
| PWR-032 | substation-a | v4 | 7.8 | megawatts | current |
| PWR-033 | substation-b | v4 | 9.1 | megawatts | current |
| PWR-034 | generator-1 | v4 | 7.3 | megawatts | current |
| PWR-035 | fuel-yard | v4 | 8.6 | megawatts | current |
| PWR-036 | substation-a | v4 | 6.8 | megawatts | current |
| PWR-037 | substation-b | v4 | 8.1 | megawatts | current |
| PWR-038 | generator-1 | v4 | 9.4 | megawatts | superseded |
| PWR-039 | fuel-yard | v4 | 7.6 | megawatts | current |
| PWR-040 | substation-a | v4 | 8.9 | megawatts | current |
| PWR-041 | substation-b | v4 | 7.1 | megawatts | current |

## Decision constraints

Separate rated, usable, generated, and reserved power with exact durations.
Name current tests for transfer, load shedding, fuel replenishment, and rollback.
