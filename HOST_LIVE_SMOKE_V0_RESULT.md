# Refactored host live smoke v0 result

Date: 2026-08-28

Freeze commit: `fbc1db052051b23cfb8667780eab0a9939dee11a`

Run ID: `2026-08-28-host-refactor-live-smoke-v0`

Disposition: sealed before provider I/O; zero model calls and zero retries.

## What happened

The authorization and exact selected-asset checks passed. Before starting the
frozen server, the runtime gate found an existing `llama-server` process and
stopped as designed.

Read-only inspection established that PID 12992 was not a leaked process from
this project. It was a live server on port 18084 serving an active Franken Agent
compaction job. GPU telemetry showed about 14.5 GiB in use and only about 1.5
GiB free, so the frozen Qwen3.8 model could not safely coexist with it. The
process was not terminated or altered.

## Custody

The run directory is sealed at:

`qualification_runs/2026-08-28-host-refactor-live-smoke-v0`

The seal SHA-256 is:

`cee41353d20a360aea2dd7ff920eaa2d261eb4cf994c66b370818df3784316dd`

It contains the external authorization receipt, freeze binding, exact runtime
asset verification, failure record, and finalization record. No request was
sent to the model server and no authorized model call was consumed.

## Interpretation

This is neither a host-path failure nor a model result. It is an environmental
resource conflict caught before provider I/O. The exact v0 run ID remains
closed under the frozen no-retry rule.

The same one-call design may be frozen under a v1 run identity after the other
authorized GPU job releases the device. That successor requires its own exact
commit-bound authorization.
