# Key rotation, privileged access, and audit evidence

## Frozen findings

The compromised service token was revoked at 12:20 UTC. The signing key was not compromised and remains current under key-set version K7.
Break-glass administrator access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.
The audit log retains online events for ninety days and archived events for seven years; these periods serve different obligations.

## Governing relationships

ANCHOR governs emergency authority and NOVA binds rollback to the current key set. LATTICE consumes IRIS audit events but does not authorize access.
Any key-set, role-policy, or logging mutation makes prior security verification stale.

## Operational evidence

| record | object/region | version | measure | unit | status |
|---|---|---|---:|---|---|
| SEC-000 | signing-key | v3 | 12.0 | hours | superseded |
| SEC-001 | service-token | v3 | 13.1 | hours | current |
| SEC-002 | admin-role | v3 | 14.2 | hours | current |
| SEC-003 | audit-log | v3 | 12.4 | hours | current |
| SEC-004 | signing-key | v3 | 13.5 | hours | current |
| SEC-005 | service-token | v3 | 14.6 | hours | current |
| SEC-006 | admin-role | v3 | 12.8 | hours | current |
| SEC-007 | audit-log | v3 | 13.9 | hours | current |
| SEC-008 | signing-key | v3 | 12.1 | hours | current |
| SEC-009 | service-token | v3 | 13.2 | hours | current |
| SEC-010 | admin-role | v3 | 14.3 | hours | current |
| SEC-011 | audit-log | v3 | 12.5 | hours | current |
| SEC-012 | signing-key | v3 | 13.6 | hours | current |
| SEC-013 | service-token | v3 | 14.7 | hours | current |
| SEC-014 | admin-role | v4 | 12.9 | hours | current |
| SEC-015 | audit-log | v4 | 14.0 | hours | current |
| SEC-016 | signing-key | v4 | 12.2 | hours | current |
| SEC-017 | service-token | v4 | 13.3 | hours | superseded |
| SEC-018 | admin-role | v4 | 14.4 | hours | current |
| SEC-019 | audit-log | v4 | 12.6 | hours | current |
| SEC-020 | signing-key | v4 | 13.7 | hours | current |
| SEC-021 | service-token | v4 | 14.8 | hours | current |
| SEC-022 | admin-role | v4 | 13.0 | hours | current |
| SEC-023 | audit-log | v4 | 14.1 | hours | current |
| SEC-024 | signing-key | v4 | 12.3 | hours | current |
| SEC-025 | service-token | v4 | 13.4 | hours | current |
| SEC-026 | admin-role | v4 | 14.5 | hours | current |
| SEC-027 | audit-log | v4 | 12.7 | hours | current |
| SEC-028 | signing-key | v5 | 13.8 | hours | current |
| SEC-029 | service-token | v5 | 12.0 | hours | current |
| SEC-030 | admin-role | v5 | 13.1 | hours | current |
| SEC-031 | audit-log | v5 | 14.2 | hours | current |
| SEC-032 | signing-key | v5 | 12.4 | hours | current |
| SEC-033 | service-token | v5 | 13.5 | hours | current |
| SEC-034 | admin-role | v5 | 14.6 | hours | superseded |
| SEC-035 | audit-log | v5 | 12.8 | hours | current |
| SEC-036 | signing-key | v5 | 13.9 | hours | current |
| SEC-037 | service-token | v5 | 12.1 | hours | current |
| SEC-038 | admin-role | v5 | 13.2 | hours | current |
| SEC-039 | audit-log | v5 | 14.3 | hours | current |
| SEC-040 | signing-key | v5 | 12.5 | hours | current |
| SEC-041 | service-token | v5 | 13.6 | hours | current |

## Decision constraints

Distinguish token revocation, uncompromised key status, access duration, approvals, and retention periods.
Name the current evidence required before restoring privileged automation.
