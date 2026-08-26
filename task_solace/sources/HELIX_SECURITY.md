# Access, control-system integrity, and evidence custody

## Frozen findings

The exposed SCADA service token was revoked at 14:10 UTC. The controller signing key was not exposed and remains current under key-set version W4.
Break-glass access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.
Online control logs are retained for ninety days and archived incident evidence for seven years; the periods serve different obligations.

## Governing relationships

AURORA governs emergency authority and MOSAIC binds rollback to the current key set. INDIGO consumes HELIX audit events but does not authorize access.
Any key-set, role-policy, controller, or logging mutation makes prior security verification stale.

## Operational evidence

| record | asset/zone | version | measure | unit | status |
|---|---|---|---:|---|---|
| SEC-000 | scada-token | v2 | 2.0 | hours | superseded |
| SEC-001 | operator-role | v2 | 3.3 | hours | current |
| SEC-002 | lab-chain | v2 | 4.6 | hours | current |
| SEC-003 | audit-log | v2 | 2.8 | hours | current |
| SEC-004 | scada-token | v2 | 4.1 | hours | current |
| SEC-005 | operator-role | v2 | 2.3 | hours | current |
| SEC-006 | lab-chain | v2 | 3.6 | hours | current |
| SEC-007 | audit-log | v2 | 4.9 | hours | current |
| SEC-008 | scada-token | v2 | 3.1 | hours | current |
| SEC-009 | operator-role | v2 | 4.4 | hours | current |
| SEC-010 | lab-chain | v2 | 2.6 | hours | current |
| SEC-011 | audit-log | v2 | 3.9 | hours | current |
| SEC-012 | scada-token | v2 | 2.1 | hours | current |
| SEC-013 | operator-role | v2 | 3.4 | hours | current |
| SEC-014 | lab-chain | v3 | 4.7 | hours | current |
| SEC-015 | audit-log | v3 | 2.9 | hours | current |
| SEC-016 | scada-token | v3 | 4.2 | hours | current |
| SEC-017 | operator-role | v3 | 2.4 | hours | current |
| SEC-018 | lab-chain | v3 | 3.7 | hours | current |
| SEC-019 | audit-log | v3 | 5.0 | hours | superseded |
| SEC-020 | scada-token | v3 | 3.2 | hours | current |
| SEC-021 | operator-role | v3 | 4.5 | hours | current |
| SEC-022 | lab-chain | v3 | 2.7 | hours | current |
| SEC-023 | audit-log | v3 | 4.0 | hours | current |
| SEC-024 | scada-token | v3 | 2.2 | hours | current |
| SEC-025 | operator-role | v3 | 3.5 | hours | current |
| SEC-026 | lab-chain | v3 | 4.8 | hours | current |
| SEC-027 | audit-log | v3 | 3.0 | hours | current |
| SEC-028 | scada-token | v4 | 4.3 | hours | current |
| SEC-029 | operator-role | v4 | 2.5 | hours | current |
| SEC-030 | lab-chain | v4 | 3.8 | hours | current |
| SEC-031 | audit-log | v4 | 2.0 | hours | current |
| SEC-032 | scada-token | v4 | 3.3 | hours | current |
| SEC-033 | operator-role | v4 | 4.6 | hours | current |
| SEC-034 | lab-chain | v4 | 2.8 | hours | current |
| SEC-035 | audit-log | v4 | 4.1 | hours | current |
| SEC-036 | scada-token | v4 | 2.3 | hours | current |
| SEC-037 | operator-role | v4 | 3.6 | hours | current |
| SEC-038 | lab-chain | v4 | 4.9 | hours | superseded |
| SEC-039 | audit-log | v4 | 3.1 | hours | current |
| SEC-040 | scada-token | v4 | 4.4 | hours | current |
| SEC-041 | operator-role | v4 | 2.6 | hours | current |

## Decision constraints

Distinguish token revocation, key status, access duration, approvals, and retention.
Name current evidence required before restoring remote automation.
