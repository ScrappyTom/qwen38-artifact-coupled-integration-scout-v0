# Artifact-coupled pressure-screen result

## Disposition

The frozen pressure screen qualified an authentic common pre-treatment
boundary.

Under ordinary exact chronology with no relief, maintenance, semantic
sidecar, or reentry, the actor completed eight calls and acquired five exact
source observations. The fifth observation, `RESULT-008`, was obtained by the
host but could not cross another model-decision boundary:

| Measure | Result |
|---|---:|
| Actor calls | 8 |
| Provider attempts | 8 |
| Retries | 0 |
| Serialized tokens | 92,296 |
| Accepted exact results | 5 |
| Rejected actions | 3 |
| Next ordinary prompt | 21,959 tokens |
| Prompt allowance | 20,992 tokens |
| Overflow | 967 tokens |

The candidate remained unchanged at
`eb63671008e22987e37ff1ebc26a8ddb29f92ec55ee1d3d1ad0d7d1d64ae181e`,
and the actor neither checked nor submitted it.

## Literal trajectory

The actor first attempted an oversized three-source batch, then acquired
`S02` and `S03` together. It next acquired `S04` and `S08`, corrected an
out-of-range `S13` request, acquired `S13`, acquired `S09`, corrected an
out-of-range `S10`/`S11` batch, and finally acquired valid ranges from `S10`
and `S11` as `RESULT-008`.

The earlier exact results crossed later model boundaries. `RESULT-008` did
not. It is present as the final user message and in exact external custody,
but its ledger record has no `first_model_visible_call`.

## What this qualifies

This is the common authentic fork required by the interaction design. It
establishes that the fresh task can reach real result-delivery pressure through
ordinary actor-selected evidence ingress. The exact task, candidate, message
history, result ledger, and undelivered pending observation are now frozen for
a matched `D0_DETACHED` versus `A1_COUPLED` continuation.

It does **not** establish that either interaction system is useful. No pressure
relief or semantic maintenance ran, and no measured continuation is authorized
by this result.

## Custody

- Frozen screen commit: `7423d214d5d2a5b77514b0acff43d547743b422e`
- Run ID: `2026-08-24-artifact-coupled-pressure-screen-v0`
- Screen result SHA-256: `3edc4687f6234dd9a8de422568dec4eca60e6989b228fed646a460c2ddba00a8`
- Pressure boundary SHA-256: `311567be65f4c05ef559c93fbb9d96db53f3dd336a795a02bb45ecd7f7912bbe`
- Final messages SHA-256: `feafae2169ed632aa2f6a123d25e6618bd3d50695b0ca93165a2eb74b8ed5543`
- Result ledger SHA-256: `831c2ee21b0262e14c7d79d3255546a6b494bbe92d5734f5d51027a4e89c83d3`
- Run seal SHA-256: `7b2f46a037877b00cbb1089d48146fe13c84dbad799b6ec074c6e57df4c6ef90`
- Independent screen audit SHA-256: `b3243a390af207915d6c111fcb0f72dc0d45f0c76fd03bc89baca592c8cd504b`

The run seal, offline tokenizer reconstruction, provider-attempt receipts,
pending-result non-delivery, unchanged candidate, and runtime release all
passed the independent audit. The server was stopped and the GPU returned to
its pre-run baseline.
