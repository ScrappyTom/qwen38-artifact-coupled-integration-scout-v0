# Clean utilities, power, and capacity

## Frozen findings

The water-for-injection loop is at 82 degrees Celsius and requires at least 80 degrees at every return point for three consecutive thirty-minute windows. Average temperature cannot substitute for every-point compliance.
Usable electrical service is 5.4 MW after switchgear derating, while the installed rating is 7.1 MW. Rated and currently usable capacity must not be swapped or added together.
Emergency generation carries 3.2 MW for twenty-eight hours at current fuel stock. The duration is not twenty-eight days and excludes the lyophilizer start transient.

## Governing relationships

CULTURE and STERILE depend on CURRENT clean utilities; SUPPLY fuel controls generator duration and SIGNAL validates return temperatures and transfer stability.
A loop balance, sensor, switchgear, generator, or production-load change makes prior utility evidence stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| UTL-000 | wfi-loop | v3 | 84.0 | percent-load | superseded |
| UTL-001 | clean-steam | v3 | 85.7 | percent-load | current |
| UTL-002 | substation | v3 | 84.5 | percent-load | current |
| UTL-003 | generator | v3 | 86.2 | percent-load | current |
| UTL-004 | wfi-loop | v3 | 85.0 | percent-load | current |
| UTL-005 | clean-steam | v3 | 86.7 | percent-load | current |
| UTL-006 | substation | v3 | 85.5 | percent-load | current |
| UTL-007 | generator | v3 | 84.3 | percent-load | current |
| UTL-008 | wfi-loop | v3 | 86.0 | percent-load | current |
| UTL-009 | clean-steam | v3 | 84.8 | percent-load | current |
| UTL-010 | substation | v3 | 86.5 | percent-load | current |
| UTL-011 | generator | v3 | 85.3 | percent-load | current |
| UTL-012 | wfi-loop | v4 | 84.1 | percent-load | current |
| UTL-013 | clean-steam | v4 | 85.8 | percent-load | current |
| UTL-014 | substation | v4 | 84.6 | percent-load | current |
| UTL-015 | generator | v4 | 86.3 | percent-load | current |
| UTL-016 | wfi-loop | v4 | 85.1 | percent-load | current |
| UTL-017 | clean-steam | v4 | 86.8 | percent-load | superseded |
| UTL-018 | substation | v4 | 85.6 | percent-load | current |
| UTL-019 | generator | v4 | 84.4 | percent-load | current |
| UTL-020 | wfi-loop | v4 | 86.1 | percent-load | current |
| UTL-021 | clean-steam | v4 | 84.9 | percent-load | current |
| UTL-022 | substation | v4 | 86.6 | percent-load | current |
| UTL-023 | generator | v4 | 85.4 | percent-load | current |
| UTL-024 | wfi-loop | v5 | 84.2 | percent-load | current |
| UTL-025 | clean-steam | v5 | 85.9 | percent-load | current |
| UTL-026 | substation | v5 | 84.7 | percent-load | current |
| UTL-027 | generator | v5 | 86.4 | percent-load | current |
| UTL-028 | wfi-loop | v5 | 85.2 | percent-load | current |
| UTL-029 | clean-steam | v5 | 84.0 | percent-load | current |
| UTL-030 | substation | v5 | 85.7 | percent-load | current |
| UTL-031 | generator | v5 | 84.5 | percent-load | current |
| UTL-032 | wfi-loop | v5 | 86.2 | percent-load | current |
| UTL-033 | clean-steam | v5 | 85.0 | percent-load | current |
| UTL-034 | substation | v5 | 86.7 | percent-load | superseded |
| UTL-035 | generator | v5 | 85.5 | percent-load | current |
| UTL-036 | wfi-loop | v6 | 84.3 | percent-load | current |
| UTL-037 | clean-steam | v6 | 86.0 | percent-load | current |
| UTL-038 | substation | v6 | 84.8 | percent-load | current |
| UTL-039 | generator | v6 | 86.5 | percent-load | current |
| UTL-040 | wfi-loop | v6 | 85.3 | percent-load | current |
| UTL-041 | clean-steam | v6 | 84.1 | percent-load | current |

## Decision constraints

Preserve every-point versus average gates, MW meanings, duration, exclusions, and staleness.
Define load stages, rollback, fuel replenishment, and current verification.
