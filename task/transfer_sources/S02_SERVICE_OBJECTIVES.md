# Northstar service objectives and traffic evidence

## Frozen service objectives

Successful migration requires all of the following simultaneously: monthly ingest availability at least 99.95%; event-loss probability no greater than one per million accepted events; duplicate delivery no greater than 0.02%; and commit-to-visible latency of at most four seconds at the 99.9th percentile.
A second latency guard is tenant-local: every tenant tier must remain at or below eight seconds at p99. Fleet averages and region averages are not acceptable substitutes because they can hide a low-volume cohort regression.
The readiness gate uses the worse of regional and tenant-cohort measurements. A rollout that improves the fleet aggregate while breaching bronze tenants is a failed rollout.

## Observed load

| window | region | tier | events/s | commit-visible p99 s | duplicates | classification |
|---|---|---|---|---|---|---|
| H000 | us-east | gold | 78000 | 3.1 | 0.006% | pass |
| H001 | us-west | gold | 79913 | 3.8 | 0.008% | pass |
| H002 | eu-central | gold | 81826 | 4.5 | 0.010% | pass |
| H003 | us-east | silver | 83739 | 3.6 | 0.012% | pass |
| H004 | us-west | silver | 85652 | 4.3 | 0.014% | pass |
| H005 | eu-central | silver | 87565 | 3.4 | 0.007% | pass |
| H006 | us-east | bronze | 89478 | 10.4 | 0.009% | tail-breach |
| H007 | us-west | bronze | 91391 | 11.2 | 0.011% | tail-breach |
| H008 | eu-central | bronze | 93304 | 12.0 | 0.013% | tail-breach |
| H009 | us-east | gold | 95217 | 4.6 | 0.006% | pass |
| H010 | us-west | gold | 97130 | 3.7 | 0.008% | pass |
| H011 | eu-central | gold | 99043 | 4.4 | 0.010% | pass |
| H012 | us-east | silver | 100956 | 3.5 | 0.012% | pass |
| H013 | us-west | silver | 102869 | 4.2 | 0.014% | pass |
| H014 | eu-central | silver | 104782 | 3.3 | 0.007% | pass |
| H015 | us-east | bronze | 106695 | 9.6 | 0.009% | tail-breach |
| H016 | us-west | bronze | 108608 | 10.4 | 0.011% | tail-breach |
| H017 | eu-central | bronze | 110521 | 11.2 | 0.013% | tail-breach |
| H018 | us-east | gold | 112434 | 4.5 | 0.006% | pass |
| H019 | us-west | gold | 114347 | 3.6 | 0.008% | pass |
| H020 | eu-central | gold | 116260 | 4.3 | 0.010% | pass |
| H021 | us-east | silver | 118173 | 3.4 | 0.012% | pass |
| H022 | us-west | silver | 120086 | 4.1 | 0.014% | pass |
| H023 | eu-central | silver | 121999 | 3.2 | 0.007% | pass |
| H024 | us-east | bronze | 79912 | 12.8 | 0.009% | tail-breach |
| H025 | us-west | bronze | 81825 | 9.6 | 0.011% | tail-breach |
| H026 | eu-central | bronze | 83738 | 10.4 | 0.013% | tail-breach |
| H027 | us-east | gold | 85651 | 4.4 | 0.006% | pass |
| H028 | us-west | gold | 87564 | 3.5 | 0.008% | pass |
| H029 | eu-central | gold | 89477 | 4.2 | 0.010% | pass |
| H030 | us-east | silver | 91390 | 3.3 | 0.012% | pass |
| H031 | us-west | silver | 93303 | 4.0 | 0.014% | pass |
| H032 | eu-central | silver | 95216 | 3.1 | 0.007% | pass |
| H033 | us-east | bronze | 97129 | 12.0 | 0.009% | tail-breach |
| H034 | us-west | bronze | 99042 | 12.8 | 0.011% | tail-breach |
| H035 | eu-central | bronze | 100955 | 9.6 | 0.013% | tail-breach |
| H036 | us-east | gold | 102868 | 4.3 | 0.006% | pass |
| H037 | us-west | gold | 104781 | 3.4 | 0.008% | pass |
| H038 | eu-central | gold | 106694 | 4.1 | 0.010% | pass |
| H039 | us-east | silver | 108607 | 3.2 | 0.012% | pass |
| H040 | us-west | silver | 110520 | 3.9 | 0.014% | pass |
| H041 | eu-central | silver | 112433 | 4.6 | 0.007% | pass |
| H042 | us-east | bronze | 114346 | 11.2 | 0.009% | tail-breach |
| H043 | us-west | bronze | 116259 | 12.0 | 0.011% | tail-breach |
| H044 | eu-central | bronze | 118172 | 12.8 | 0.013% | tail-breach |
| H045 | us-east | gold | 120085 | 4.2 | 0.006% | pass |
| H046 | us-west | gold | 121998 | 3.3 | 0.008% | pass |
| H047 | eu-central | gold | 79911 | 4.0 | 0.010% | pass |
| H048 | us-east | silver | 81824 | 3.1 | 0.012% | pass |
| H049 | us-west | silver | 83737 | 3.8 | 0.014% | pass |
| H050 | eu-central | silver | 85650 | 4.5 | 0.007% | pass |
| H051 | us-east | bronze | 87563 | 10.4 | 0.009% | tail-breach |
| H052 | us-west | bronze | 89476 | 11.2 | 0.011% | tail-breach |
| H053 | eu-central | bronze | 91389 | 12.0 | 0.013% | tail-breach |
| H054 | us-east | gold | 93302 | 4.1 | 0.006% | pass |
| H055 | us-west | gold | 95215 | 3.2 | 0.008% | pass |
| H056 | eu-central | gold | 97128 | 3.9 | 0.010% | pass |
| H057 | us-east | silver | 99041 | 4.6 | 0.012% | pass |
| H058 | us-west | silver | 100954 | 3.7 | 0.014% | pass |
| H059 | eu-central | silver | 102867 | 4.4 | 0.007% | pass |
| H060 | us-east | bronze | 104780 | 9.6 | 0.009% | tail-breach |
| H061 | us-west | bronze | 106693 | 10.4 | 0.011% | tail-breach |
| H062 | eu-central | bronze | 108606 | 11.2 | 0.013% | tail-breach |
| H063 | us-east | gold | 110519 | 4.0 | 0.006% | pass |
| H064 | us-west | gold | 112432 | 3.1 | 0.008% | pass |
| H065 | eu-central | gold | 114345 | 3.8 | 0.010% | pass |
| H066 | us-east | silver | 116258 | 4.5 | 0.012% | pass |
| H067 | us-west | silver | 118171 | 3.6 | 0.014% | pass |
| H068 | eu-central | silver | 120084 | 4.3 | 0.007% | pass |
| H069 | us-east | bronze | 121997 | 12.8 | 0.009% | tail-breach |
| H070 | us-west | bronze | 79910 | 9.6 | 0.011% | tail-breach |
| H071 | eu-central | bronze | 81823 | 10.4 | 0.013% | tail-breach |

## Interpretation constraints

The sample includes repeated bronze tail breaches even while the blended fleet statistic remains below four seconds. Promotion gates must query per-tenant distributions, not only the dashboard headline.
Traffic grows by cohort and time of day. Capacity claims must be bound to the candidate routing revision and tested at the planned dual-write percentage.
