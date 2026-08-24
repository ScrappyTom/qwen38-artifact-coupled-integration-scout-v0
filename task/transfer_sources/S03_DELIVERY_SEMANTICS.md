# Delivery, acknowledgement, and idempotency contract

## Identity and acknowledgement

The only authoritative idempotency key is producer_id:event_id. A transport batch ID identifies a shipment and may be reused after a producer restart; it is not an event identity and must never drive deduplication.
The gateway may acknowledge an event only after the authoritative path has committed it to two availability zones and persisted the idempotency key. A socket write, broker receipt, or batch acceptance is not a commit acknowledgement.
StreamCore consumers are at-least-once. Exactly-once delivery is not promised. The system objective is idempotent observable effects with auditable duplicate bounds.

## Retention conflict

The original StreamCore proposal set the deduplication horizon to 24 hours. Producer incident evidence contains legitimate retries 31 hours after acknowledgement. The migration decision must raise the minimum deduplication horizon to 48 hours or supply an equally explicit mechanism that covers those retries.
A producer epoch can change only through the authenticated reset workflow. An unannounced producer restart does not authorize erasing prior idempotency state.

## Replay examples

| record | producer | event | condition | delay | 24h cache result |
|---|---|---|---|---|---|
| P000 | producer-00 | event-00000 | accepted | 0h | hit |
| P001 | producer-01 | event-00001 | retry-before-ack | 17h | hit |
| P002 | producer-02 | event-00002 | retry-after-ack | 34h | miss |
| P003 | producer-03 | event-00003 | late-replay | 5h | hit |
| P004 | producer-04 | event-00004 | producer-reset | 22h | miss |
| P005 | producer-05 | event-00005 | accepted | 39h | miss |
| P006 | producer-06 | event-00006 | retry-before-ack | 10h | hit |
| P007 | producer-07 | event-00007 | retry-after-ack | 27h | miss |
| P008 | producer-08 | event-00008 | late-replay | 44h | miss |
| P009 | producer-09 | event-00009 | producer-reset | 15h | miss |
| P010 | producer-10 | event-00010 | accepted | 32h | miss |
| P011 | producer-11 | event-00011 | retry-before-ack | 3h | hit |
| P012 | producer-00 | event-00012 | retry-after-ack | 20h | hit |
| P013 | producer-01 | event-00013 | late-replay | 37h | miss |
| P014 | producer-02 | event-00014 | producer-reset | 8h | miss |
| P015 | producer-03 | event-00015 | accepted | 25h | miss |
| P016 | producer-04 | event-00016 | retry-before-ack | 42h | miss |
| P017 | producer-05 | event-00017 | retry-after-ack | 13h | hit |
| P018 | producer-06 | event-00018 | late-replay | 30h | miss |
| P019 | producer-07 | event-00019 | producer-reset | 1h | miss |
| P020 | producer-08 | event-00020 | accepted | 18h | hit |
| P021 | producer-09 | event-00021 | retry-before-ack | 35h | miss |
| P022 | producer-10 | event-00022 | retry-after-ack | 6h | hit |
| P023 | producer-11 | event-00023 | late-replay | 23h | hit |
| P024 | producer-00 | event-00024 | producer-reset | 40h | miss |
| P025 | producer-01 | event-00025 | accepted | 11h | hit |
| P026 | producer-02 | event-00026 | retry-before-ack | 28h | miss |
| P027 | producer-03 | event-00027 | retry-after-ack | 45h | miss |
| P028 | producer-04 | event-00028 | late-replay | 16h | hit |
| P029 | producer-05 | event-00029 | producer-reset | 33h | miss |
| P030 | producer-06 | event-00030 | accepted | 4h | hit |
| P031 | producer-07 | event-00031 | retry-before-ack | 21h | hit |
| P032 | producer-08 | event-00032 | retry-after-ack | 38h | miss |
| P033 | producer-09 | event-00033 | late-replay | 9h | hit |
| P034 | producer-10 | event-00034 | producer-reset | 26h | miss |
| P035 | producer-11 | event-00035 | accepted | 43h | miss |
| P036 | producer-00 | event-00036 | retry-before-ack | 14h | hit |
| P037 | producer-01 | event-00037 | retry-after-ack | 31h | miss |
| P038 | producer-02 | event-00038 | late-replay | 2h | hit |
| P039 | producer-03 | event-00039 | producer-reset | 19h | miss |
| P040 | producer-04 | event-00040 | accepted | 36h | miss |
| P041 | producer-05 | event-00041 | retry-before-ack | 7h | hit |
| P042 | producer-06 | event-00042 | retry-after-ack | 24h | hit |
| P043 | producer-07 | event-00043 | late-replay | 41h | miss |
| P044 | producer-08 | event-00044 | producer-reset | 12h | miss |
| P045 | producer-09 | event-00045 | accepted | 29h | miss |
| P046 | producer-10 | event-00046 | retry-before-ack | 0h | hit |
| P047 | producer-11 | event-00047 | retry-after-ack | 17h | hit |
| P048 | producer-00 | event-00048 | late-replay | 34h | miss |
| P049 | producer-01 | event-00049 | producer-reset | 5h | miss |
| P050 | producer-02 | event-00050 | accepted | 22h | hit |
| P051 | producer-03 | event-00051 | retry-before-ack | 39h | miss |
| P052 | producer-04 | event-00052 | retry-after-ack | 10h | hit |
| P053 | producer-05 | event-00053 | late-replay | 27h | miss |
| P054 | producer-06 | event-00054 | producer-reset | 44h | miss |
| P055 | producer-07 | event-00055 | accepted | 15h | hit |
| P056 | producer-08 | event-00056 | retry-before-ack | 32h | miss |
| P057 | producer-09 | event-00057 | retry-after-ack | 3h | hit |
| P058 | producer-10 | event-00058 | late-replay | 20h | hit |
| P059 | producer-11 | event-00059 | producer-reset | 37h | miss |
| P060 | producer-00 | event-00060 | accepted | 8h | hit |
| P061 | producer-01 | event-00061 | retry-before-ack | 25h | miss |
| P062 | producer-02 | event-00062 | retry-after-ack | 42h | miss |
| P063 | producer-03 | event-00063 | late-replay | 13h | hit |
| P064 | producer-04 | event-00064 | producer-reset | 30h | miss |
| P065 | producer-05 | event-00065 | accepted | 1h | hit |
| P066 | producer-06 | event-00066 | retry-before-ack | 18h | hit |
| P067 | producer-07 | event-00067 | retry-after-ack | 35h | miss |
| P068 | producer-08 | event-00068 | late-replay | 6h | hit |
| P069 | producer-09 | event-00069 | producer-reset | 23h | miss |
| P070 | producer-10 | event-00070 | accepted | 40h | miss |
| P071 | producer-11 | event-00071 | retry-before-ack | 11h | hit |
| P072 | producer-00 | event-00072 | retry-after-ack | 28h | miss |
| P073 | producer-01 | event-00073 | late-replay | 45h | miss |
| P074 | producer-02 | event-00074 | producer-reset | 16h | miss |
| P075 | producer-03 | event-00075 | accepted | 33h | miss |
| P076 | producer-04 | event-00076 | retry-before-ack | 4h | hit |
| P077 | producer-05 | event-00077 | retry-after-ack | 21h | hit |
| P078 | producer-06 | event-00078 | late-replay | 38h | miss |
| P079 | producer-07 | event-00079 | producer-reset | 9h | miss |
| P080 | producer-08 | event-00080 | accepted | 26h | miss |
| P081 | producer-09 | event-00081 | retry-before-ack | 43h | miss |
| P082 | producer-10 | event-00082 | retry-after-ack | 14h | hit |
| P083 | producer-11 | event-00083 | late-replay | 31h | miss |
| P084 | producer-00 | event-00084 | producer-reset | 2h | miss |
| P085 | producer-01 | event-00085 | accepted | 19h | hit |
| P086 | producer-02 | event-00086 | retry-before-ack | 36h | miss |
| P087 | producer-03 | event-00087 | retry-after-ack | 7h | hit |
| P088 | producer-04 | event-00088 | late-replay | 24h | hit |
| P089 | producer-05 | event-00089 | producer-reset | 41h | miss |
| P090 | producer-06 | event-00090 | accepted | 12h | hit |
| P091 | producer-07 | event-00091 | retry-before-ack | 29h | miss |
| P092 | producer-08 | event-00092 | retry-after-ack | 0h | hit |
| P093 | producer-09 | event-00093 | late-replay | 17h | hit |
| P094 | producer-10 | event-00094 | producer-reset | 34h | miss |
| P095 | producer-11 | event-00095 | accepted | 5h | hit |
| P096 | producer-00 | event-00096 | retry-before-ack | 22h | hit |
| P097 | producer-01 | event-00097 | retry-after-ack | 39h | miss |
| P098 | producer-02 | event-00098 | late-replay | 10h | hit |
| P099 | producer-03 | event-00099 | producer-reset | 27h | miss |
| P100 | producer-04 | event-00100 | accepted | 44h | miss |
| P101 | producer-05 | event-00101 | retry-before-ack | 15h | hit |
| P102 | producer-06 | event-00102 | retry-after-ack | 32h | miss |
| P103 | producer-07 | event-00103 | late-replay | 3h | hit |
| P104 | producer-08 | event-00104 | producer-reset | 20h | miss |
| P105 | producer-09 | event-00105 | accepted | 37h | miss |
| P106 | producer-10 | event-00106 | retry-before-ack | 8h | hit |
| P107 | producer-11 | event-00107 | retry-after-ack | 25h | miss |
| P108 | producer-00 | event-00108 | late-replay | 42h | miss |
| P109 | producer-01 | event-00109 | producer-reset | 13h | miss |
| P110 | producer-02 | event-00110 | accepted | 30h | miss |
| P111 | producer-03 | event-00111 | retry-before-ack | 1h | hit |
| P112 | producer-04 | event-00112 | retry-after-ack | 18h | hit |
| P113 | producer-05 | event-00113 | late-replay | 35h | miss |
| P114 | producer-06 | event-00114 | producer-reset | 6h | miss |
| P115 | producer-07 | event-00115 | accepted | 23h | hit |
| P116 | producer-08 | event-00116 | retry-before-ack | 40h | miss |
| P117 | producer-09 | event-00117 | retry-after-ack | 11h | hit |
| P118 | producer-10 | event-00118 | late-replay | 28h | miss |
| P119 | producer-11 | event-00119 | producer-reset | 45h | miss |
| P120 | producer-00 | event-00120 | accepted | 16h | hit |
| P121 | producer-01 | event-00121 | retry-before-ack | 33h | miss |
| P122 | producer-02 | event-00122 | retry-after-ack | 4h | hit |
| P123 | producer-03 | event-00123 | late-replay | 21h | hit |
| P124 | producer-04 | event-00124 | producer-reset | 38h | miss |
| P125 | producer-05 | event-00125 | accepted | 9h | hit |
| P126 | producer-06 | event-00126 | retry-before-ack | 26h | miss |
| P127 | producer-07 | event-00127 | retry-after-ack | 43h | miss |
| P128 | producer-08 | event-00128 | late-replay | 14h | hit |
| P129 | producer-09 | event-00129 | producer-reset | 31h | miss |
| P130 | producer-10 | event-00130 | accepted | 2h | hit |
| P131 | producer-11 | event-00131 | retry-before-ack | 19h | hit |
| P132 | producer-00 | event-00132 | retry-after-ack | 36h | miss |
| P133 | producer-01 | event-00133 | late-replay | 7h | hit |
| P134 | producer-02 | event-00134 | producer-reset | 24h | miss |
| P135 | producer-03 | event-00135 | accepted | 41h | miss |
| P136 | producer-04 | event-00136 | retry-before-ack | 12h | hit |
| P137 | producer-05 | event-00137 | retry-after-ack | 29h | miss |
| P138 | producer-06 | event-00138 | late-replay | 0h | hit |
| P139 | producer-07 | event-00139 | producer-reset | 17h | miss |
| P140 | producer-08 | event-00140 | accepted | 34h | miss |
| P141 | producer-09 | event-00141 | retry-before-ack | 5h | hit |
| P142 | producer-10 | event-00142 | retry-after-ack | 22h | hit |
| P143 | producer-11 | event-00143 | late-replay | 39h | miss |
| P144 | producer-00 | event-00144 | producer-reset | 10h | miss |
| P145 | producer-01 | event-00145 | accepted | 27h | miss |
| P146 | producer-02 | event-00146 | retry-before-ack | 44h | miss |
| P147 | producer-03 | event-00147 | retry-after-ack | 15h | hit |
| P148 | producer-04 | event-00148 | late-replay | 32h | miss |
| P149 | producer-05 | event-00149 | producer-reset | 3h | miss |
| P150 | producer-06 | event-00150 | accepted | 20h | hit |
| P151 | producer-07 | event-00151 | retry-before-ack | 37h | miss |
| P152 | producer-08 | event-00152 | retry-after-ack | 8h | hit |
| P153 | producer-09 | event-00153 | late-replay | 25h | miss |
| P154 | producer-10 | event-00154 | producer-reset | 42h | miss |
| P155 | producer-11 | event-00155 | accepted | 13h | hit |
| P156 | producer-00 | event-00156 | retry-before-ack | 30h | miss |
| P157 | producer-01 | event-00157 | retry-after-ack | 1h | hit |
| P158 | producer-02 | event-00158 | late-replay | 18h | hit |
| P159 | producer-03 | event-00159 | producer-reset | 35h | miss |
| P160 | producer-04 | event-00160 | accepted | 6h | hit |
| P161 | producer-05 | event-00161 | retry-before-ack | 23h | hit |
| P162 | producer-06 | event-00162 | retry-after-ack | 40h | miss |
| P163 | producer-07 | event-00163 | late-replay | 11h | hit |
| P164 | producer-08 | event-00164 | producer-reset | 28h | miss |
| P165 | producer-09 | event-00165 | accepted | 45h | miss |
| P166 | producer-10 | event-00166 | retry-before-ack | 16h | hit |
| P167 | producer-11 | event-00167 | retry-after-ack | 33h | miss |
| P168 | producer-00 | event-00168 | late-replay | 4h | hit |
| P169 | producer-01 | event-00169 | producer-reset | 21h | miss |
| P170 | producer-02 | event-00170 | accepted | 38h | miss |
| P171 | producer-03 | event-00171 | retry-before-ack | 9h | hit |
| P172 | producer-04 | event-00172 | retry-after-ack | 26h | miss |
| P173 | producer-05 | event-00173 | late-replay | 43h | miss |
| P174 | producer-06 | event-00174 | producer-reset | 14h | miss |
| P175 | producer-07 | event-00175 | accepted | 31h | miss |
| P176 | producer-08 | event-00176 | retry-before-ack | 2h | hit |
| P177 | producer-09 | event-00177 | retry-after-ack | 19h | hit |
| P178 | producer-10 | event-00178 | late-replay | 36h | miss |
| P179 | producer-11 | event-00179 | producer-reset | 7h | miss |

## Required tests

Tests must cover retries before and after acknowledgement, a 31-hour replay, producer restart with reused batch ID, duplicate delivery across a regional handoff, and expiry at the selected horizon.
