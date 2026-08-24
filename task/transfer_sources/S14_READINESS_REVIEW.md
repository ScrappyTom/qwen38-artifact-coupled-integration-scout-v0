# Independent migration readiness review

## Current disposition

The migration is not ready for production promotion. Shadowing may continue, but no tenant cohort may advance beyond 5% until the six blocking evidence groups below are current for the exact candidate.
The review rejects three attractive shortcuts: a 24-hour dedup cache, global failover for EU payloads, and reliance on the four-hour vendor target. It also rejects fleet-average latency as the only performance gate.
Readiness requires a current candidate-bound check after the last routing, schema, deduplication, materializer, capacity, or policy mutation. Submission of a plan is not itself release authorization.

## Open evidence

| item | blocking evidence | status | candidate binding | owner | effect |
|---|---|---|---|---|---|
| A000 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A001 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A002 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A003 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A004 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A005 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A006 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A007 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A008 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A009 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A010 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A011 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A012 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A013 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A014 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A015 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A016 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A017 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A018 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A019 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A020 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A021 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A022 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A023 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A024 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A025 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A026 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A027 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A028 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A029 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A030 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A031 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A032 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A033 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A034 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A035 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A036 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A037 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A038 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A039 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A040 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A041 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A042 | event-key dedup not proven beyond 31h | open | candidate-r4 | owner-0 | blocks-promotion |
| A043 | EU secondary routing not independently tested | open | candidate-r4 | owner-1 | blocks-promotion |
| A044 | us-west shards not installed | evidence-requested | candidate-r4 | owner-2 | blocks-promotion |
| A045 | twelve-hour spool replay not load-tested | open | candidate-r4 | owner-3 | blocks-promotion |
| A046 | schema-v3 materializer bundle lacks current check | open | candidate-r4 | owner-4 | blocks-promotion |
| A047 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r4 | owner-5 | blocks-promotion |
| A048 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A049 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A050 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A051 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A052 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A053 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A054 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A055 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A056 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A057 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A058 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A059 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A060 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A061 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A062 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A063 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A064 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A065 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A066 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A067 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A068 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A069 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A070 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A071 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A072 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A073 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A074 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A075 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A076 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A077 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A078 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A079 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A080 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A081 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A082 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A083 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A084 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A085 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A086 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A087 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A088 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A089 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A090 | event-key dedup not proven beyond 31h | open | candidate-r5 | owner-0 | blocks-promotion |
| A091 | EU secondary routing not independently tested | open | candidate-r5 | owner-1 | blocks-promotion |
| A092 | us-west shards not installed | evidence-requested | candidate-r5 | owner-2 | blocks-promotion |
| A093 | twelve-hour spool replay not load-tested | open | candidate-r5 | owner-3 | blocks-promotion |
| A094 | schema-v3 materializer bundle lacks current check | open | candidate-r5 | owner-4 | blocks-promotion |
| A095 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r5 | owner-5 | blocks-promotion |
| A096 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A097 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A098 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A099 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A100 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A101 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A102 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A103 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A104 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A105 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A106 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A107 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A108 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A109 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A110 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A111 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A112 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A113 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A114 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A115 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A116 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A117 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A118 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A119 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A120 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A121 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A122 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A123 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A124 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A125 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A126 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A127 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A128 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A129 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A130 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A131 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A132 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A133 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A134 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A135 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A136 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A137 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |
| A138 | event-key dedup not proven beyond 31h | open | candidate-r6 | owner-0 | blocks-promotion |
| A139 | EU secondary routing not independently tested | open | candidate-r6 | owner-1 | blocks-promotion |
| A140 | us-west shards not installed | evidence-requested | candidate-r6 | owner-2 | blocks-promotion |
| A141 | twelve-hour spool replay not load-tested | open | candidate-r6 | owner-3 | blocks-promotion |
| A142 | schema-v3 materializer bundle lacks current check | open | candidate-r6 | owner-4 | blocks-promotion |
| A143 | per-tenant latency gate absent from release automation | evidence-requested | candidate-r6 | owner-5 | blocks-promotion |

## Expected decision

A credible ninety-day plan should sequence prerequisites before traffic, preserve a safe pre-v3 rollback envelope, define the post-v3 forward-fix boundary, assign owners, and state falsifiers that would stop or reverse the chosen route.
