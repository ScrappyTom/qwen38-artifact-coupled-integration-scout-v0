# Control access, signing, and audit custody

## Frozen findings

The exposed dispatch service account was disabled at 11:25 UTC. The interlocking-signing key was not exposed and remains current under key set K12.
Break-glass control access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.
Online controller logs are retained for 210 days and archived investigation evidence for six years; the periods serve different obligations.

## Governing relationships

SIGNAL and POWER require CYBER-validated control access; TELEMETRY consumes audit events but cannot authorize access.
Any key-set, role-policy, controller, route-table, or logging mutation makes prior cyber verification stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| CYB-000 | service-account | v4 | 2.0 | hours-access | superseded |
| CYB-001 | logic-signing | v4 | 3.9 | hours-access | current |
| CYB-002 | dispatch-api | v4 | 2.7 | hours-access | current |
| CYB-003 | audit-store | v4 | 4.6 | hours-access | current |
| CYB-004 | service-account | v4 | 3.4 | hours-access | current |
| CYB-005 | logic-signing | v4 | 2.2 | hours-access | current |
| CYB-006 | dispatch-api | v4 | 4.1 | hours-access | current |
| CYB-007 | audit-store | v4 | 2.9 | hours-access | current |
| CYB-008 | service-account | v4 | 4.8 | hours-access | current |
| CYB-009 | logic-signing | v4 | 3.6 | hours-access | current |
| CYB-010 | dispatch-api | v4 | 2.4 | hours-access | current |
| CYB-011 | audit-store | v5 | 4.3 | hours-access | current |
| CYB-012 | service-account | v5 | 3.1 | hours-access | current |
| CYB-013 | logic-signing | v5 | 5.0 | hours-access | current |
| CYB-014 | dispatch-api | v5 | 3.8 | hours-access | current |
| CYB-015 | audit-store | v5 | 2.6 | hours-access | current |
| CYB-016 | service-account | v5 | 4.5 | hours-access | current |
| CYB-017 | logic-signing | v5 | 3.3 | hours-access | current |
| CYB-018 | dispatch-api | v5 | 2.1 | hours-access | current |
| CYB-019 | audit-store | v5 | 4.0 | hours-access | superseded |
| CYB-020 | service-account | v5 | 2.8 | hours-access | current |
| CYB-021 | logic-signing | v5 | 4.7 | hours-access | current |
| CYB-022 | dispatch-api | v6 | 3.5 | hours-access | current |
| CYB-023 | audit-store | v6 | 2.3 | hours-access | current |
| CYB-024 | service-account | v6 | 4.2 | hours-access | current |
| CYB-025 | logic-signing | v6 | 3.0 | hours-access | current |
| CYB-026 | dispatch-api | v6 | 4.9 | hours-access | current |
| CYB-027 | audit-store | v6 | 3.7 | hours-access | current |
| CYB-028 | service-account | v6 | 2.5 | hours-access | current |
| CYB-029 | logic-signing | v6 | 4.4 | hours-access | current |
| CYB-030 | dispatch-api | v6 | 3.2 | hours-access | current |
| CYB-031 | audit-store | v6 | 2.0 | hours-access | current |
| CYB-032 | service-account | v6 | 3.9 | hours-access | current |
| CYB-033 | logic-signing | v7 | 2.7 | hours-access | current |
| CYB-034 | dispatch-api | v7 | 4.6 | hours-access | current |
| CYB-035 | audit-store | v7 | 3.4 | hours-access | current |
| CYB-036 | service-account | v7 | 2.2 | hours-access | current |
| CYB-037 | logic-signing | v7 | 4.1 | hours-access | current |
| CYB-038 | dispatch-api | v7 | 2.9 | hours-access | superseded |
| CYB-039 | audit-store | v7 | 4.8 | hours-access | current |
| CYB-040 | service-account | v7 | 3.6 | hours-access | current |
| CYB-041 | logic-signing | v7 | 2.4 | hours-access | current |
| CYB-042 | dispatch-api | v7 | 4.3 | hours-access | current |
| CYB-043 | audit-store | v7 | 3.1 | hours-access | current |
| CYB-044 | service-account | v8 | 5.0 | hours-access | current |
| CYB-045 | logic-signing | v8 | 3.8 | hours-access | current |
| CYB-046 | dispatch-api | v8 | 2.6 | hours-access | current |
| CYB-047 | audit-store | v8 | 4.5 | hours-access | current |
| CYB-048 | service-account | v8 | 3.3 | hours-access | current |
| CYB-049 | logic-signing | v8 | 2.1 | hours-access | current |
| CYB-050 | dispatch-api | v8 | 4.0 | hours-access | current |
| CYB-051 | audit-store | v8 | 2.8 | hours-access | current |
| CYB-052 | service-account | v8 | 4.7 | hours-access | current |
| CYB-053 | logic-signing | v8 | 3.5 | hours-access | current |
| CYB-054 | dispatch-api | v8 | 2.3 | hours-access | current |
| CYB-055 | audit-store | v9 | 4.2 | hours-access | current |
| CYB-056 | service-account | v9 | 3.0 | hours-access | current |
| CYB-057 | logic-signing | v9 | 4.9 | hours-access | superseded |
| CYB-058 | dispatch-api | v9 | 3.7 | hours-access | current |
| CYB-059 | audit-store | v9 | 2.5 | hours-access | current |
| CYB-060 | service-account | v9 | 4.4 | hours-access | current |
| CYB-061 | logic-signing | v9 | 3.2 | hours-access | current |
| CYB-062 | dispatch-api | v9 | 2.0 | hours-access | current |
| CYB-063 | audit-store | v9 | 3.9 | hours-access | current |

## Decision constraints

Distinguish account disablement, key state, access duration, approval, and retention.
Name current evidence required before restoring remote dispatch control.
