# Tail-latency and cohort telemetry review

## Finding

The fleet dashboard reported commit-to-visible p99 of 3.8 seconds during the 25% candidate run. Tenant-level analysis found bronze cohorts between 10.4 and 13.7 seconds. Low bronze volume hid the breach in the aggregate.
Promotion requires per-tenant p99, regional p99.9, duplicate rate, loss, reconciliation lag, spool fill, and backpressure. Every metric must be tagged with candidate hash, cohort, region, and schema version.
A dashboard without candidate binding cannot establish current readiness after a deployment or routing change.

## Tenant slice

| tenant | tier | events/s | p99 s | p99.9 s | gate |
|---|---|---|---|---|---|
| tenant-00 | gold | 900 | 2.20 | 3.30 | pass |
| tenant-01 | silver | 1013 | 2.55 | 4.05 | pass |
| tenant-02 | bronze | 1126 | 11.10 | 13.00 | hold |
| tenant-03 | gold | 1239 | 3.25 | 5.55 | pass |
| tenant-04 | silver | 1352 | 3.60 | 6.30 | pass |
| tenant-05 | bronze | 1465 | 3.95 | 5.05 | pass |
| tenant-06 | gold | 1578 | 4.30 | 5.80 | pass |
| tenant-07 | silver | 1691 | 2.20 | 4.10 | pass |
| tenant-08 | bronze | 1804 | 2.55 | 4.85 | pass |
| tenant-09 | gold | 1917 | 2.90 | 5.60 | pass |
| tenant-10 | silver | 2030 | 3.25 | 4.35 | pass |
| tenant-11 | bronze | 2143 | 3.60 | 5.10 | pass |
| tenant-12 | gold | 2256 | 3.95 | 5.85 | pass |
| tenant-13 | silver | 2369 | 4.30 | 6.60 | pass |
| tenant-14 | bronze | 2482 | 10.40 | 13.10 | hold |
| tenant-15 | gold | 2595 | 2.55 | 3.65 | pass |
| tenant-16 | silver | 2708 | 2.90 | 4.40 | pass |
| tenant-17 | bronze | 2821 | 3.25 | 5.15 | pass |
| tenant-18 | gold | 2934 | 3.60 | 5.90 | pass |
| tenant-19 | silver | 3047 | 3.95 | 6.65 | pass |
| tenant-20 | bronze | 3160 | 4.30 | 5.40 | pass |
| tenant-21 | gold | 3273 | 2.20 | 3.70 | pass |
| tenant-22 | silver | 3386 | 2.55 | 4.45 | pass |
| tenant-23 | bronze | 3499 | 2.90 | 5.20 | pass |
| tenant-24 | gold | 3612 | 3.25 | 5.95 | pass |
| tenant-25 | silver | 3725 | 3.60 | 4.70 | pass |
| tenant-26 | bronze | 3838 | 12.15 | 13.65 | hold |
| tenant-27 | gold | 3951 | 4.30 | 6.20 | pass |
| tenant-28 | silver | 4064 | 2.20 | 4.50 | pass |
| tenant-29 | bronze | 4177 | 2.55 | 5.25 | pass |
| tenant-30 | gold | 4290 | 2.90 | 4.00 | pass |
| tenant-31 | silver | 4403 | 3.25 | 4.75 | pass |
| tenant-32 | bronze | 4516 | 3.60 | 5.50 | pass |
| tenant-33 | gold | 4629 | 3.95 | 6.25 | pass |
| tenant-34 | silver | 4742 | 4.30 | 7.00 | pass |
| tenant-35 | bronze | 4855 | 2.20 | 3.30 | pass |
| tenant-36 | gold | 4968 | 2.55 | 4.05 | pass |
| tenant-37 | silver | 5081 | 2.90 | 4.80 | pass |
| tenant-38 | bronze | 5194 | 11.45 | 13.75 | hold |
| tenant-39 | gold | 5307 | 3.60 | 6.30 | pass |
| tenant-40 | silver | 5420 | 3.95 | 5.05 | pass |
| tenant-41 | bronze | 5533 | 4.30 | 5.80 | pass |
| tenant-42 | gold | 5646 | 2.20 | 4.10 | pass |
| tenant-43 | silver | 5759 | 2.55 | 4.85 | pass |
| tenant-44 | bronze | 5872 | 2.90 | 5.60 | pass |
| tenant-45 | gold | 5985 | 3.25 | 4.35 | pass |
| tenant-46 | silver | 6098 | 3.60 | 5.10 | pass |
| tenant-47 | bronze | 6211 | 3.95 | 5.85 | pass |
| tenant-48 | gold | 6324 | 4.30 | 6.60 | pass |
| tenant-49 | silver | 6437 | 2.20 | 4.90 | pass |
| tenant-50 | bronze | 6550 | 10.75 | 11.85 | hold |
| tenant-51 | gold | 6663 | 2.90 | 4.40 | pass |
| tenant-52 | silver | 6776 | 3.25 | 5.15 | pass |
| tenant-53 | bronze | 6889 | 3.60 | 5.90 | pass |
| tenant-54 | gold | 7002 | 3.95 | 6.65 | pass |
| tenant-55 | silver | 7115 | 4.30 | 5.40 | pass |
| tenant-56 | bronze | 7228 | 2.20 | 3.70 | pass |
| tenant-57 | gold | 7341 | 2.55 | 4.45 | pass |
| tenant-58 | silver | 7454 | 2.90 | 5.20 | pass |
| tenant-59 | bronze | 7567 | 3.25 | 5.95 | pass |

## Decision rule

Any tenant above eight seconds p99 holds that cohort even if the fleet aggregate passes. The remedy must be checked against the same tenant slice before release resumes.
