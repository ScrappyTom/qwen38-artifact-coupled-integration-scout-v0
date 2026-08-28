# Refactor work log

## 2026-08-28 — checkpoint 0: baseline and cut line

Completed:

- preserved clean starting commits in the apparatus and program repositories;
- ran the full apparatus regression suite: 235 tests passed;
- mapped 34 direct `mark_model_visible` call sites across runners, Stage 0,
  audits, fixtures, and tests;
- found direct residency/message-index mutation outside `ResultLedger` in
  measured and causal-fork runners;
- confirmed three task wrappers mutate shared runner globals;
- reproduced the exact Trellis mismatch:
  - Stage 0 appends each result and immediately marks it visible;
  - live execution marks the prior pending result visible only after the next
    actor invocation completes;
  - frozen E83 custody contains six delivered source identities and pending
    TRANSIT/COMMS.

Decision:

- create a new contained event-driven host path;
- keep historical runners frozen;
- migrate E83 provider-free first;
- do not begin with a broad rewrite of semantic or task-specific modules.

Risks still open:

- exact mapping from historical wrapped results to canonical payload identity;
- preserving chronological message positions while deduplicating bodies;
- keeping checkpoint files compact without weakening exact custody;
- identifying the smallest future live task adapter after provider-free
  acceptance.

Next slice: implement immutable models and the single delivery-state kernel.

## 2026-08-28 — checkpoint 1: event and delivery kernel

Completed:

- added immutable exact-result, body-identity, transcript-entry, event,
  projected-state, run-configuration, and terminal schemas;
- added the append-only `HostKernel` as the sole authority for acquisition,
  scheduling, completed delivery, externalization, reopen, repeat demand,
  provider failure, and terminal state;
- chose completed invocation as the conservative delivery commit point;
- added event-log serialization and state-hash verification;
- added focused transition tests, including the rule that provider failure
  leaves a scheduled result pending.

Evidence:

- focused kernel and Trellis fixture tests passed;
- E83 reconstructs RESULT-001 through RESULT-006 as delivered-resident and
  RESULT-007 as pending.

Risk found and corrected:

- one result may have multiple historical transcript positions after reopen;
  residency alone does not identify which position owns the current exact
  body. The projection now retains the active transcript entry, so earlier
  positions remain receipts.

Next slice: packet projection, exact-body deduplication, and common pressure
relief.

## 2026-08-28 — checkpoint 2: packet, deduplication, and relief

Completed:

- added pure packet composition with a representation manifest;
- bound canonical body identity to payload hash, object, version, and span;
- added compact repeat-demand feedback for an already resident body;
- preserved same bytes under different versions and partial overlaps as
  distinct bodies;
- added exact receipts and reopen placement behavior;
- added deterministic strictly-positive first-fit relief with no semantic
  activation gate;
- replayed the frozen E83 packet at 21,401 tokens and admitted it by
  externalizing RESULT-001, producing a 18,785-token new-format packet;
- added a direct provider-free replay command.

Evidence:

- 20 focused host-refactor tests pass;
- the refactor packet matches frozen E83 `FINAL_MESSAGES.json` before relief;
- the new receipt is slightly larger than the historical receipt, so relief
  reaches 18,785 rather than 18,663 tokens; both are safely feasible and the
  selected exact body is identical.

Interpretation:

- the token difference is an explicit representation cost, not a behavioral
  difference or an excuse to preserve the older mutation-based path.

Next slice: checkpoint review/resume hardening and thin configured Trellis
adapter.

## 2026-08-28 — checkpoint 3: current state, checkpoint, and thin path

Completed:

- added replaceable exact state slots and migrated the Trellis current
  candidate to that mechanism;
- added a bounded mechanical latest-check binding that labels an exact check
  current or stale against the exact current candidate hash;
- added one-shot provider request/response/failure custody with no retry;
- added twelve-call checkpointing, mechanical review packets, event/state
  hashes, recurrence telemetry, and remaining budgets;
- added exact Trellis domain snapshots covering candidate files, candidate
  version, phase, last check, submission flag, and next result index;
- proved an uninterrupted call 13 and a call 13 resumed from checkpoint produce
  identical event state and next-packet bytes;
- replaced global task-runner mutation with an immutable Trellis spec and
  domain adapter;
- added a thin live-style tranche coordinator that writes per-call custody,
  checkpoint, and review artifacts without owning task or provider policy.

Review correction:

- an earlier checkpoint design sealed only the host event log. That was not
  sufficient for exact continuation because domain candidate files and result
  numbering lived outside the kernel. The checkpoint now includes exact domain
  state and verifies candidate identity on hydration.

Next slice: property tests, full historical regression, and program
reconciliation.

## 2026-08-28 — checkpoint 4: verification and disposition

Completed:

- added randomized delivery/externalization/reopen replay tests;
- added provider-free end-to-end Trellis tests for repeat-read deduplication and
  exact candidate replacement;
- added a static guard against legacy visibility/residency mutation in the
  selected host path;
- added the acceptance matrix and direct E83 replay tool;
- ran formatting, lint, isolated type checking, focused tests, and full
  historical regression.

Verification:

- Ruff: passed;
- mypy with legacy imports skipped: passed for all new host modules;
- focused refactor suite: 31 passed before the final live-style tranche test;
- final full suite: 266 passed in 255.09 seconds;
- no GPU/model/provider call occurred.

Remaining limitations:

- historical runners retain their original duplicated semantics and are frozen
  evidence paths, not migration targets;
- the new path supports one pending exact result per call;
- checkpoints deliberately retain exact event and domain bytes and may be
  large;
- the 12/60 call defaults remain provisional review policy;
- model-server startup, external authorization, and final tree sealing remain
  launcher responsibilities for a future specifically frozen experiment;
- semantic loop judgment remains outside the host.

Disposition:

- the offline host refactor is implementation-complete pending commit and
  program-level reconciliation;
- no GPU operation is selected.
