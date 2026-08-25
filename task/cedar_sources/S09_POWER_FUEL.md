# Power, fuel, and resupply continuity

## Frozen findings

Civic Arena's generator has sixteen tested hours of fuel, radio repeaters ten, and the county bus reserve fourteen hours at the planned cycle rate. The fuel contract targets delivery within eight hours.
The last regional outage delayed contracted fuel for nineteen hours because the supplier used South Pass. The plan must stage enough local fuel for at least twenty-four hours or diversify the route and supplier.
Traffic signals on generator backup last eight hours. Manual intersection control needs twenty-six trained personnel, but the current roster contains eighteen.

## Governing relationships

Fuel availability constrains shelter viability, radio coverage, bus cycles, and road throughput simultaneously. It cannot be scored once as a generic resource line.
A route closure in S04 can invalidate the fuel contract even if the vendor remains operational.

## Operational evidence

| record | asset | endurance | resupply | dependency | status |
|---|---|---|---|---|---|
| CONT-000 | shelter-generator | 16h | 6h | vendor-dependent | hold |
| CONT-001 | radio-repeater | 10h | 13h | local | tracked |
| CONT-002 | bus-fuel | 14h | 20h | local | tracked |
| CONT-003 | oxygen-cache | 18h | 9h | vendor-dependent | tracked |
| CONT-004 | traffic-signal | 8h | 16h | local | tracked |
| CONT-005 | shelter-generator | 16h | 23h | local | tracked |
| CONT-006 | radio-repeater | 10h | 12h | vendor-dependent | tracked |
| CONT-007 | bus-fuel | 14h | 19h | local | tracked |
| CONT-008 | oxygen-cache | 18h | 8h | local | tracked |
| CONT-009 | traffic-signal | 8h | 15h | vendor-dependent | tracked |
| CONT-010 | shelter-generator | 16h | 22h | local | tracked |
| CONT-011 | radio-repeater | 10h | 11h | local | tracked |
| CONT-012 | bus-fuel | 14h | 18h | vendor-dependent | tracked |
| CONT-013 | oxygen-cache | 18h | 7h | local | tracked |
| CONT-014 | traffic-signal | 8h | 14h | local | hold |
| CONT-015 | shelter-generator | 16h | 21h | vendor-dependent | tracked |
| CONT-016 | radio-repeater | 10h | 10h | local | tracked |
| CONT-017 | bus-fuel | 14h | 17h | local | tracked |
| CONT-018 | oxygen-cache | 18h | 6h | vendor-dependent | tracked |
| CONT-019 | traffic-signal | 8h | 13h | local | tracked |
| CONT-020 | shelter-generator | 16h | 20h | local | tracked |
| CONT-021 | radio-repeater | 10h | 9h | vendor-dependent | tracked |
| CONT-022 | bus-fuel | 14h | 16h | local | tracked |
| CONT-023 | oxygen-cache | 18h | 23h | local | tracked |
| CONT-024 | traffic-signal | 8h | 12h | vendor-dependent | tracked |
| CONT-025 | shelter-generator | 16h | 19h | local | tracked |
| CONT-026 | radio-repeater | 10h | 8h | local | tracked |
| CONT-027 | bus-fuel | 14h | 15h | vendor-dependent | tracked |
| CONT-028 | oxygen-cache | 18h | 22h | local | hold |
| CONT-029 | traffic-signal | 8h | 11h | local | tracked |
| CONT-030 | shelter-generator | 16h | 18h | vendor-dependent | tracked |
| CONT-031 | radio-repeater | 10h | 7h | local | tracked |
| CONT-032 | bus-fuel | 14h | 14h | local | tracked |
| CONT-033 | oxygen-cache | 18h | 21h | vendor-dependent | tracked |
| CONT-034 | traffic-signal | 8h | 10h | local | tracked |
| CONT-035 | shelter-generator | 16h | 17h | local | tracked |
| CONT-036 | radio-repeater | 10h | 6h | vendor-dependent | tracked |
| CONT-037 | bus-fuel | 14h | 13h | local | tracked |
| CONT-038 | oxygen-cache | 18h | 20h | local | tracked |
| CONT-039 | traffic-signal | 8h | 9h | vendor-dependent | tracked |
| CONT-040 | shelter-generator | 16h | 16h | local | tracked |
| CONT-041 | radio-repeater | 10h | 23h | local | tracked |
| CONT-042 | bus-fuel | 14h | 12h | vendor-dependent | hold |
| CONT-043 | oxygen-cache | 18h | 19h | local | tracked |
| CONT-044 | traffic-signal | 8h | 8h | local | tracked |
| CONT-045 | shelter-generator | 16h | 15h | vendor-dependent | tracked |
| CONT-046 | radio-repeater | 10h | 22h | local | tracked |
| CONT-047 | bus-fuel | 14h | 11h | local | tracked |

## Decision constraints

Use observed nineteen-hour delay rather than the eight-hour target as the continuity basis.
Name local staging, alternate supplier/route, consumption checks, and replenishment triggers.
