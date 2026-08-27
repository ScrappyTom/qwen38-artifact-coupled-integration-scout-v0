# Traction power, substations, and emergency supply

## Frozen findings

Installed traction capacity is 34.0 megawatts, while current usable capacity after feeder derating is 26.5 megawatts. Installed and usable capacity must not be swapped or added together.
Feeder voltage is 24.7 kilovolts and must remain between 24.0 and 25.2 kilovolts at every monitored node for three consecutive fifteen-minute windows. An average cannot replace every-node compliance.
The backup plant carries 11.8 megawatts for eighteen hours at current fuel stock; it does not carry full passenger peak and eighteen hours is not eighteen days.

## Governing relationships

TRACK work windows and ROLLING consist demand depend on POWER; FUEL controls backup duration and TELEMETRY validates node voltage.
A feeder, transformer, relay, fuel stock, or service-load change makes prior power evidence stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| PWR-000 | substation-east | v4 | 31.0 | megawatts | superseded |
| PWR-001 | substation-west | v4 | 32.9 | megawatts | current |
| PWR-002 | feeder-3 | v4 | 31.7 | megawatts | current |
| PWR-003 | backup-plant | v4 | 33.6 | megawatts | current |
| PWR-004 | substation-east | v4 | 32.4 | megawatts | current |
| PWR-005 | substation-west | v4 | 31.2 | megawatts | current |
| PWR-006 | feeder-3 | v4 | 33.1 | megawatts | current |
| PWR-007 | backup-plant | v4 | 31.9 | megawatts | current |
| PWR-008 | substation-east | v4 | 33.8 | megawatts | current |
| PWR-009 | substation-west | v4 | 32.6 | megawatts | current |
| PWR-010 | feeder-3 | v4 | 31.4 | megawatts | current |
| PWR-011 | backup-plant | v5 | 33.3 | megawatts | current |
| PWR-012 | substation-east | v5 | 32.1 | megawatts | current |
| PWR-013 | substation-west | v5 | 34.0 | megawatts | current |
| PWR-014 | feeder-3 | v5 | 32.8 | megawatts | current |
| PWR-015 | backup-plant | v5 | 31.6 | megawatts | current |
| PWR-016 | substation-east | v5 | 33.5 | megawatts | current |
| PWR-017 | substation-west | v5 | 32.3 | megawatts | current |
| PWR-018 | feeder-3 | v5 | 31.1 | megawatts | current |
| PWR-019 | backup-plant | v5 | 33.0 | megawatts | superseded |
| PWR-020 | substation-east | v5 | 31.8 | megawatts | current |
| PWR-021 | substation-west | v5 | 33.7 | megawatts | current |
| PWR-022 | feeder-3 | v6 | 32.5 | megawatts | current |
| PWR-023 | backup-plant | v6 | 31.3 | megawatts | current |
| PWR-024 | substation-east | v6 | 33.2 | megawatts | current |
| PWR-025 | substation-west | v6 | 32.0 | megawatts | current |
| PWR-026 | feeder-3 | v6 | 33.9 | megawatts | current |
| PWR-027 | backup-plant | v6 | 32.7 | megawatts | current |
| PWR-028 | substation-east | v6 | 31.5 | megawatts | current |
| PWR-029 | substation-west | v6 | 33.4 | megawatts | current |
| PWR-030 | feeder-3 | v6 | 32.2 | megawatts | current |
| PWR-031 | backup-plant | v6 | 31.0 | megawatts | current |
| PWR-032 | substation-east | v6 | 32.9 | megawatts | current |
| PWR-033 | substation-west | v7 | 31.7 | megawatts | current |
| PWR-034 | feeder-3 | v7 | 33.6 | megawatts | current |
| PWR-035 | backup-plant | v7 | 32.4 | megawatts | current |
| PWR-036 | substation-east | v7 | 31.2 | megawatts | current |
| PWR-037 | substation-west | v7 | 33.1 | megawatts | current |
| PWR-038 | feeder-3 | v7 | 31.9 | megawatts | superseded |
| PWR-039 | backup-plant | v7 | 33.8 | megawatts | current |
| PWR-040 | substation-east | v7 | 32.6 | megawatts | current |
| PWR-041 | substation-west | v7 | 31.4 | megawatts | current |
| PWR-042 | feeder-3 | v7 | 33.3 | megawatts | current |
| PWR-043 | backup-plant | v7 | 32.1 | megawatts | current |
| PWR-044 | substation-east | v8 | 34.0 | megawatts | current |
| PWR-045 | substation-west | v8 | 32.8 | megawatts | current |
| PWR-046 | feeder-3 | v8 | 31.6 | megawatts | current |
| PWR-047 | backup-plant | v8 | 33.5 | megawatts | current |
| PWR-048 | substation-east | v8 | 32.3 | megawatts | current |
| PWR-049 | substation-west | v8 | 31.1 | megawatts | current |
| PWR-050 | feeder-3 | v8 | 33.0 | megawatts | current |
| PWR-051 | backup-plant | v8 | 31.8 | megawatts | current |
| PWR-052 | substation-east | v8 | 33.7 | megawatts | current |
| PWR-053 | substation-west | v8 | 32.5 | megawatts | current |
| PWR-054 | feeder-3 | v8 | 31.3 | megawatts | current |
| PWR-055 | backup-plant | v9 | 33.2 | megawatts | current |
| PWR-056 | substation-east | v9 | 32.0 | megawatts | current |
| PWR-057 | substation-west | v9 | 33.9 | megawatts | superseded |
| PWR-058 | feeder-3 | v9 | 32.7 | megawatts | current |
| PWR-059 | backup-plant | v9 | 31.5 | megawatts | current |
| PWR-060 | substation-east | v9 | 33.4 | megawatts | current |
| PWR-061 | substation-west | v9 | 32.2 | megawatts | current |
| PWR-062 | feeder-3 | v9 | 31.0 | megawatts | current |
| PWR-063 | backup-plant | v9 | 32.9 | megawatts | current |

## Decision constraints

Preserve installed versus usable MW, kV range, every-node rule, duration, and exclusions.
Define load stages, rollback, replenishment, and current verification.
