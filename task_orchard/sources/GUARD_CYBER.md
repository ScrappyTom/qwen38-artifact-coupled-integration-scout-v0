# Control-system access, integrity, and evidence custody

## Frozen findings

The exposed service account was disabled at 09:40 UTC. The recipe-signing key was not exposed and remains current under key-set K7.
Break-glass access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.
Online controller logs are retained for 180 days and archived investigation evidence for seven years; the periods serve different obligations.

## Governing relationships

STERILE and CULTURE require GUARD-validated controller access; SIGNAL consumes audit events but does not authorize access.
Any key-set, role-policy, controller, recipe, or logging mutation makes prior cyber verification stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| CYB-000 | service-account | v3 | 2.0 | hours | superseded |
| CYB-001 | recipe-signing | v3 | 3.7 | hours | current |
| CYB-002 | historian | v3 | 2.5 | hours | current |
| CYB-003 | audit-store | v3 | 4.2 | hours | current |
| CYB-004 | service-account | v3 | 3.0 | hours | current |
| CYB-005 | recipe-signing | v3 | 4.7 | hours | current |
| CYB-006 | historian | v3 | 3.5 | hours | current |
| CYB-007 | audit-store | v3 | 2.3 | hours | current |
| CYB-008 | service-account | v3 | 4.0 | hours | current |
| CYB-009 | recipe-signing | v3 | 2.8 | hours | current |
| CYB-010 | historian | v3 | 4.5 | hours | current |
| CYB-011 | audit-store | v3 | 3.3 | hours | current |
| CYB-012 | service-account | v4 | 2.1 | hours | current |
| CYB-013 | recipe-signing | v4 | 3.8 | hours | current |
| CYB-014 | historian | v4 | 2.6 | hours | current |
| CYB-015 | audit-store | v4 | 4.3 | hours | current |
| CYB-016 | service-account | v4 | 3.1 | hours | current |
| CYB-017 | recipe-signing | v4 | 4.8 | hours | superseded |
| CYB-018 | historian | v4 | 3.6 | hours | current |
| CYB-019 | audit-store | v4 | 2.4 | hours | current |
| CYB-020 | service-account | v4 | 4.1 | hours | current |
| CYB-021 | recipe-signing | v4 | 2.9 | hours | current |
| CYB-022 | historian | v4 | 4.6 | hours | current |
| CYB-023 | audit-store | v4 | 3.4 | hours | current |
| CYB-024 | service-account | v5 | 2.2 | hours | current |
| CYB-025 | recipe-signing | v5 | 3.9 | hours | current |
| CYB-026 | historian | v5 | 2.7 | hours | current |
| CYB-027 | audit-store | v5 | 4.4 | hours | current |
| CYB-028 | service-account | v5 | 3.2 | hours | current |
| CYB-029 | recipe-signing | v5 | 2.0 | hours | current |
| CYB-030 | historian | v5 | 3.7 | hours | current |
| CYB-031 | audit-store | v5 | 2.5 | hours | current |
| CYB-032 | service-account | v5 | 4.2 | hours | current |
| CYB-033 | recipe-signing | v5 | 3.0 | hours | current |
| CYB-034 | historian | v5 | 4.7 | hours | superseded |
| CYB-035 | audit-store | v5 | 3.5 | hours | current |
| CYB-036 | service-account | v6 | 2.3 | hours | current |
| CYB-037 | recipe-signing | v6 | 4.0 | hours | current |
| CYB-038 | historian | v6 | 2.8 | hours | current |
| CYB-039 | audit-store | v6 | 4.5 | hours | current |
| CYB-040 | service-account | v6 | 3.3 | hours | current |
| CYB-041 | recipe-signing | v6 | 2.1 | hours | current |

## Decision constraints

Distinguish account disablement, key status, access duration, approval, and retention.
Name current evidence required before restoring remote recipe deployment.
