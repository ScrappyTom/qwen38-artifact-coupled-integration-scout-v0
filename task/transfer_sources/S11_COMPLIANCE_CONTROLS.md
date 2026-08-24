# Security, privacy, retention, and audit controls

## Non-negotiable controls

EU-tagged raw payloads, replay spools, and dead-letter bodies must remain in approved EU storage and processing locations. Encryption in transit or at rest does not permit a residency exception.
Raw payload retention is 30 days. Idempotency keys and non-payload audit metadata are retained for 400 days. Deletion requests must remove payloads while retaining the minimum non-payload proof required for compliance.
Spools use envelope encryption with region-local keys. Break-glass access requires two-person approval, a ticket binding, and a complete audit event. Service accounts are least-privilege and cohort-scoped.

## Control inventory

| control | class | scope | status | owner | evidence set |
|---|---|---|---|---|---|
| C000 | residency | EU | required | owner-0 | review-1 |
| C001 | encryption | US | required | owner-1 | review-1 |
| C002 | access | global-metadata | required | owner-2 | review-1 |
| C003 | retention | EU | required | owner-3 | review-1 |
| C004 | audit | US | required | owner-4 | review-1 |
| C005 | deletion | global-metadata | required | owner-5 | review-1 |
| C006 | residency | EU | required | owner-6 | review-1 |
| C007 | encryption | US | required | owner-7 | review-1 |
| C008 | access | global-metadata | required | owner-0 | review-1 |
| C009 | retention | EU | required | owner-1 | review-1 |
| C010 | audit | US | required | owner-2 | review-1 |
| C011 | deletion | global-metadata | required | owner-3 | review-1 |
| C012 | residency | EU | required | owner-4 | review-1 |
| C013 | encryption | US | required | owner-5 | review-1 |
| C014 | access | global-metadata | required | owner-6 | review-1 |
| C015 | retention | EU | required | owner-7 | review-1 |
| C016 | audit | US | required | owner-0 | review-1 |
| C017 | deletion | global-metadata | required | owner-1 | review-1 |
| C018 | residency | EU | required | owner-2 | review-1 |
| C019 | encryption | US | required | owner-3 | review-1 |
| C020 | access | global-metadata | required | owner-4 | review-1 |
| C021 | retention | EU | required | owner-5 | review-1 |
| C022 | audit | US | required | owner-6 | review-1 |
| C023 | deletion | global-metadata | required | owner-7 | review-1 |
| C024 | residency | EU | required | owner-0 | review-2 |
| C025 | encryption | US | required | owner-1 | review-2 |
| C026 | access | global-metadata | required | owner-2 | review-2 |
| C027 | retention | EU | required | owner-3 | review-2 |
| C028 | audit | US | required | owner-4 | review-2 |
| C029 | deletion | global-metadata | required | owner-5 | review-2 |
| C030 | residency | EU | required | owner-6 | review-2 |
| C031 | encryption | US | required | owner-7 | review-2 |
| C032 | access | global-metadata | required | owner-0 | review-2 |
| C033 | retention | EU | required | owner-1 | review-2 |
| C034 | audit | US | required | owner-2 | review-2 |
| C035 | deletion | global-metadata | required | owner-3 | review-2 |
| C036 | residency | EU | required | owner-4 | review-2 |
| C037 | encryption | US | required | owner-5 | review-2 |
| C038 | access | global-metadata | required | owner-6 | review-2 |
| C039 | retention | EU | required | owner-7 | review-2 |
| C040 | audit | US | required | owner-0 | review-2 |
| C041 | deletion | global-metadata | required | owner-1 | review-2 |
| C042 | residency | EU | required | owner-2 | review-2 |
| C043 | encryption | US | required | owner-3 | review-2 |
| C044 | access | global-metadata | required | owner-4 | review-2 |
| C045 | retention | EU | required | owner-5 | review-2 |
| C046 | audit | US | required | owner-6 | review-2 |
| C047 | deletion | global-metadata | required | owner-7 | review-2 |
| C048 | residency | EU | required | owner-0 | review-3 |
| C049 | encryption | US | required | owner-1 | review-3 |
| C050 | access | global-metadata | required | owner-2 | review-3 |
| C051 | retention | EU | required | owner-3 | review-3 |
| C052 | audit | US | required | owner-4 | review-3 |
| C053 | deletion | global-metadata | required | owner-5 | review-3 |
| C054 | residency | EU | required | owner-6 | review-3 |
| C055 | encryption | US | required | owner-7 | review-3 |
| C056 | access | global-metadata | required | owner-0 | review-3 |
| C057 | retention | EU | required | owner-1 | review-3 |
| C058 | audit | US | required | owner-2 | review-3 |
| C059 | deletion | global-metadata | required | owner-3 | review-3 |
| C060 | residency | EU | required | owner-4 | review-3 |
| C061 | encryption | US | required | owner-5 | review-3 |
| C062 | access | global-metadata | required | owner-6 | review-3 |
| C063 | retention | EU | required | owner-7 | review-3 |
| C064 | audit | US | required | owner-0 | review-3 |
| C065 | deletion | global-metadata | required | owner-1 | review-3 |
| C066 | residency | EU | required | owner-2 | review-3 |
| C067 | encryption | US | required | owner-3 | review-3 |
| C068 | access | global-metadata | required | owner-4 | review-3 |
| C069 | retention | EU | required | owner-5 | review-3 |
| C070 | audit | US | required | owner-6 | review-3 |
| C071 | deletion | global-metadata | required | owner-7 | review-3 |
| C072 | residency | EU | required | owner-0 | review-4 |
| C073 | encryption | US | required | owner-1 | review-4 |
| C074 | access | global-metadata | required | owner-2 | review-4 |
| C075 | retention | EU | required | owner-3 | review-4 |
| C076 | audit | US | required | owner-4 | review-4 |
| C077 | deletion | global-metadata | required | owner-5 | review-4 |
| C078 | residency | EU | required | owner-6 | review-4 |
| C079 | encryption | US | required | owner-7 | review-4 |
| C080 | access | global-metadata | required | owner-0 | review-4 |
| C081 | retention | EU | required | owner-1 | review-4 |
| C082 | audit | US | required | owner-2 | review-4 |
| C083 | deletion | global-metadata | required | owner-3 | review-4 |
| C084 | residency | EU | required | owner-4 | review-4 |
| C085 | encryption | US | required | owner-5 | review-4 |
| C086 | access | global-metadata | required | owner-6 | review-4 |
| C087 | retention | EU | required | owner-7 | review-4 |
| C088 | audit | US | required | owner-0 | review-4 |
| C089 | deletion | global-metadata | required | owner-1 | review-4 |
| C090 | residency | EU | required | owner-2 | review-4 |
| C091 | encryption | US | required | owner-3 | review-4 |
| C092 | access | global-metadata | required | owner-4 | review-4 |
| C093 | retention | EU | required | owner-5 | review-4 |
| C094 | audit | US | required | owner-6 | review-4 |
| C095 | deletion | global-metadata | required | owner-7 | review-4 |
| C096 | residency | EU | required | owner-0 | review-5 |
| C097 | encryption | US | required | owner-1 | review-5 |
| C098 | access | global-metadata | required | owner-2 | review-5 |
| C099 | retention | EU | required | owner-3 | review-5 |
| C100 | audit | US | required | owner-4 | review-5 |
| C101 | deletion | global-metadata | required | owner-5 | review-5 |
| C102 | residency | EU | required | owner-6 | review-5 |
| C103 | encryption | US | required | owner-7 | review-5 |
| C104 | access | global-metadata | required | owner-0 | review-5 |
| C105 | retention | EU | required | owner-1 | review-5 |
| C106 | audit | US | required | owner-2 | review-5 |
| C107 | deletion | global-metadata | required | owner-3 | review-5 |
| C108 | residency | EU | required | owner-4 | review-5 |
| C109 | encryption | US | required | owner-5 | review-5 |
| C110 | access | global-metadata | required | owner-6 | review-5 |
| C111 | retention | EU | required | owner-7 | review-5 |
| C112 | audit | US | required | owner-0 | review-5 |
| C113 | deletion | global-metadata | required | owner-1 | review-5 |
| C114 | residency | EU | required | owner-2 | review-5 |
| C115 | encryption | US | required | owner-3 | review-5 |
| C116 | access | global-metadata | required | owner-4 | review-5 |
| C117 | retention | EU | required | owner-5 | review-5 |
| C118 | audit | US | required | owner-6 | review-5 |
| C119 | deletion | global-metadata | required | owner-7 | review-5 |
| C120 | residency | EU | required | owner-0 | review-6 |
| C121 | encryption | US | required | owner-1 | review-6 |
| C122 | access | global-metadata | required | owner-2 | review-6 |
| C123 | retention | EU | required | owner-3 | review-6 |
| C124 | audit | US | required | owner-4 | review-6 |
| C125 | deletion | global-metadata | required | owner-5 | review-6 |
| C126 | residency | EU | required | owner-6 | review-6 |
| C127 | encryption | US | required | owner-7 | review-6 |
| C128 | access | global-metadata | required | owner-0 | review-6 |
| C129 | retention | EU | required | owner-1 | review-6 |
| C130 | audit | US | required | owner-2 | review-6 |
| C131 | deletion | global-metadata | required | owner-3 | review-6 |
| C132 | residency | EU | required | owner-4 | review-6 |
| C133 | encryption | US | required | owner-5 | review-6 |
| C134 | access | global-metadata | required | owner-6 | review-6 |
| C135 | retention | EU | required | owner-7 | review-6 |
| C136 | audit | US | required | owner-0 | review-6 |
| C137 | deletion | global-metadata | required | owner-1 | review-6 |
| C138 | residency | EU | required | owner-2 | review-6 |
| C139 | encryption | US | required | owner-3 | review-6 |
| C140 | access | global-metadata | required | owner-4 | review-6 |
| C141 | retention | EU | required | owner-5 | review-6 |
| C142 | audit | US | required | owner-6 | review-6 |
| C143 | deletion | global-metadata | required | owner-7 | review-6 |

## Release consequence

Residency, retention, encryption, and access checks are blocking release criteria. The generic fail-anywhere disaster-recovery statement is not authoritative for EU payloads.
