# Demand surge and supply-loss forecast revisions

## Frozen findings

The median demand case remains near baseline, but 36 percent of current ensemble members exceed 44,000 bags over seventy-two hours after the neighboring facility outage.
The conservative branch also assumes one component-delivery miss and six hours of river-route closure. It governs reserves until timestamped demand and route observations rule it out.
Forecast revision MF-9 supersedes MF-7. Decisions citing MF-7 are stale even if their arithmetic is otherwise correct.

## Governing relationships

CIPHER demand, EMBER supply timing, FJORD routes, DRIFT output, and KNOLL alternates must be reconciled under the same forecast branch.
A candidate that covers the median case but not the active conservative branch remains blocked.

## Operational evidence

| record | asset/zone | revision | measure | unit | status |
|---|---|---|---:|---|---|
| FCST-000 | baseline | r2 | 36.0 | percent-scenario | hold |
| FCST-001 | surge | r2 | 36.7 | percent-scenario | current |
| FCST-002 | supplier-loss | r2 | 37.4 | percent-scenario | current |
| FCST-003 | route-loss | r2 | 38.1 | percent-scenario | current |
| FCST-004 | baseline | r2 | 38.8 | percent-scenario | current |
| FCST-005 | surge | r2 | 36.4 | percent-scenario | current |
| FCST-006 | supplier-loss | r2 | 37.1 | percent-scenario | current |
| FCST-007 | route-loss | r2 | 37.8 | percent-scenario | current |
| FCST-008 | baseline | r2 | 38.5 | percent-scenario | current |
| FCST-009 | surge | r2 | 36.1 | percent-scenario | current |
| FCST-010 | supplier-loss | r2 | 36.8 | percent-scenario | current |
| FCST-011 | route-loss | r2 | 37.5 | percent-scenario | current |
| FCST-012 | baseline | r2 | 38.2 | percent-scenario | current |
| FCST-013 | surge | r2 | 38.9 | percent-scenario | hold |
| FCST-014 | supplier-loss | r2 | 36.5 | percent-scenario | current |
| FCST-015 | route-loss | r2 | 37.2 | percent-scenario | current |
| FCST-016 | baseline | r3 | 37.9 | percent-scenario | current |
| FCST-017 | surge | r3 | 38.6 | percent-scenario | current |
| FCST-018 | supplier-loss | r3 | 36.2 | percent-scenario | current |
| FCST-019 | route-loss | r3 | 36.9 | percent-scenario | current |
| FCST-020 | baseline | r3 | 37.6 | percent-scenario | current |
| FCST-021 | surge | r3 | 38.3 | percent-scenario | current |
| FCST-022 | supplier-loss | r3 | 39.0 | percent-scenario | current |
| FCST-023 | route-loss | r3 | 36.6 | percent-scenario | current |
| FCST-024 | baseline | r3 | 37.3 | percent-scenario | current |
| FCST-025 | surge | r3 | 38.0 | percent-scenario | current |
| FCST-026 | supplier-loss | r3 | 38.7 | percent-scenario | hold |
| FCST-027 | route-loss | r3 | 36.3 | percent-scenario | current |
| FCST-028 | baseline | r3 | 37.0 | percent-scenario | current |
| FCST-029 | surge | r3 | 37.7 | percent-scenario | current |
| FCST-030 | supplier-loss | r3 | 38.4 | percent-scenario | current |
| FCST-031 | route-loss | r3 | 36.0 | percent-scenario | current |
| FCST-032 | baseline | r4 | 36.7 | percent-scenario | current |
| FCST-033 | surge | r4 | 37.4 | percent-scenario | current |
| FCST-034 | supplier-loss | r4 | 38.1 | percent-scenario | current |
| FCST-035 | route-loss | r4 | 38.8 | percent-scenario | current |
| FCST-036 | baseline | r4 | 36.4 | percent-scenario | current |
| FCST-037 | surge | r4 | 37.1 | percent-scenario | current |
| FCST-038 | supplier-loss | r4 | 37.8 | percent-scenario | current |
| FCST-039 | route-loss | r4 | 38.5 | percent-scenario | hold |
| FCST-040 | baseline | r4 | 36.1 | percent-scenario | current |
| FCST-041 | surge | r4 | 36.8 | percent-scenario | current |
| FCST-042 | supplier-loss | r4 | 37.5 | percent-scenario | current |
| FCST-043 | route-loss | r4 | 38.2 | percent-scenario | current |
| FCST-044 | baseline | r4 | 38.9 | percent-scenario | current |
| FCST-045 | surge | r4 | 36.5 | percent-scenario | current |
| FCST-046 | supplier-loss | r4 | 37.2 | percent-scenario | current |
| FCST-047 | route-loss | r4 | 37.9 | percent-scenario | current |

## Decision constraints

Preserve the 36 percent scenario as probability, not certainty, utilization, or humidity.
Name branch, revision, observation trigger, reserve, and retirement condition.
