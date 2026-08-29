# Refactored host live-smoke qualification

Date: 2026-08-28

Status: offline-qualified; pending a clean frozen commit and separate exact GPU
authorization.

## Purpose

This is the smallest live test that can establish that the refactored host is
connected to the restored frozen model and CUDA runtime correctly. It is not a
behavioral experiment and cannot establish information-management utility.

The test resumes the authentic E83 pressure boundary after seven historical
actor calls. `RESULT-007` (COMMS and TRANSIT) is pending. The ordinary packet is
21,401 tokenizer tokens and cannot fit the 20,992-token prompt allowance. The
frozen first-fit rule externalizes `RESULT-001`, producing an 18,785-token
packet. One live model invocation is then allowed.

## What the one call exercises together

1. Exact restored model identity and tokenizer behavior.
2. Fresh hidden CUDA server startup and runtime gating, with exact verification
   of the named model/server/tokenizer assets and a hash inventory of the loaded
   server bundle.
3. Model alias, build, 25,088-token context, 66/66 GPU offload, and PID-on-GPU
   checks.
4. Exact pressure reproduction and deterministic `RESULT-001` relief.
5. Delivery of the previously pending `RESULT-007` across a completed model
   decision.
6. Exact request binding, raw provider custody, finish-reason admission, and
   ordinary action admission or rejection.
7. Verified parent checkpoint, new checkpoint, mechanical review, runtime
   release, and sealed run tree.

The model may choose any action permitted by the frozen task. A semantically
poor or rejected action does not fail this host qualification. The call
qualifies when the provider completes once, the exact pending result is bound
to and delivered through call 8, the host records the action disposition, and
all custody and shutdown gates pass.

## Frozen limits

- Run ID: `2026-08-28-host-refactor-live-smoke-v0`
- Scope: `host_refactor_live_smoke_v0`
- New model calls: at most 1
- Serialized tokens: at most 30,000
- Attempts per call: 1
- Retries: 0
- Automatic continuation: prohibited

The launcher requires an authorization receipt outside the repository that
binds those values to the eventual clean freeze commit. It refuses a dirty
tree, an existing run directory, mismatched assets, or any failed runtime gate.

## Claim limits

A pass supports only this claim:

> The refactored host can execute one exact, pressure-relieved, result-bearing
> invocation through the frozen live CUDA/model path and leave complete
> custody, checkpoint, review, release, and seal evidence.

It does not show that the model made a useful decision, that the policy improves
task quality, that loops are prevented, or that the refactor is ready for an
unattended long trajectory.

## Successor rule

After a passing smoke, the next step is a separately designed and authorized
bounded live tranche with a human review pause. A failed smoke is repaired at
the exact host/runtime boundary it exposes; it is not retried under this run ID.
