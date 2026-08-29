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

## 2026-08-28 — live hardening checkpoint 0: review and bounded scope

Completed:

- reconciled the external review against `runner.py`, `provider.py`,
  `trellis_adapter.py`, `kernel.py`, `packet.py`, `checkpoint.py`, and
  `live_path.py`;
- confirmed six live seams: final-request binding, nonterminal rejection,
  adapter-native reopen, lifecycle-derived reopen capability, finish-reason
  admission, and state-slot exposure binding;
- confirmed five hardening needs: context/reserve reconciliation, prospective
  serialized budget, execution-manifest binding, richer mechanical review, and
  chained checkpoint/accounting;
- froze `LIVE_HARDENING_PLAN.md` as a ten-case bounded acceptance contract;
- configured future repository-local authorship from the authenticated GitHub
  account without rewriting published commits.

Decision:

- retain the event-driven core and extend its live seams;
- write adversarial provider-free tests before implementation;
- make no GPU/provider call and select no experiment during this pass.

Next slice: add the ten live-hardening acceptance tests and record their
expected initial failures.

## 2026-08-28 — live hardening checkpoint 1: implementation and qualification

Completed:

- bound every final provider request to the exact composed messages, packet
  manifest, pending result bodies, current state-slot exposures, completion
  reserve, and immutable execution manifest;
- prevented delivery or state-exposure commitment when that binding fails;
- preserved unacceptable finish reasons and ordinary parse/action rejections
  as exact nonterminal observations while keeping unexpected adapter failures
  terminal;
- routed Trellis reopen through the original result's native lifecycle and
  derived advertised reopen capability from projected delivery state;
- made context window, response reserve, prompt allowance, accepted finish
  reasons, execution manifest, and prospective serialized budget explicit;
- chained resumed tranches to a verified parent checkpoint and separated
  provider attempts, completed invocations, and failed invocations;
- expanded the mechanical review with request bindings, finish reasons, raw
  custody paths, provider usage and timing, action dispositions, candidate
  transitions, and exact diffs;
- corrected an initially observed replay defect: wall-clock timing remains
  custody/review telemetry and no longer changes the authoritative event log.

Verification:

- adversarial live-hardening tests: 11 passed;
- combined checkpoint/live/hardening tests: 18 passed;
- Ruff: passed;
- mypy over 12 host modules: passed;
- full compatible-tokenizer regression: 277 passed in 307.51 seconds;
- no GPU, model-provider, or external inference call occurred.

Qualification limit:

- the exact tokenizer executable remains present and matches
  `d435fb84f60d6c21dbd2adcb0beb38555f2921894909c98f9236bf0984971b1c`;
- the frozen tokenizer projection expected at
  `E:\AI_Models\AtomicChat__Qwen3.8-27B-GGUF__ca10ebceb188\Qwen3.8-27B-AD-IQ2_S.tokenizer-projection.gguf`
  is absent after the power outage;
- a different local Qwen3.8 GGUF reproduced the E83 count/relief assertion and
  passed the full regression when injected only in-process, but it is not the
  locked asset and cannot substitute for exact qualification.

Disposition:

- code hardening: accepted provider-free;
- compatible-tokenizer regression: passed provisionally;
- exact locked-asset qualification: blocked pending restoration and hash
  verification of the frozen tokenizer projection;
- live GPU/provider readiness: not claimed and not authorized.

## 2026-08-28 — locked asset restoration and exact qualification

Completed:

- recovered the archived construction history for the missing sparse tokenizer
  projection and established that it was a transient snapshot of an in-progress
  download rather than a reproducible immutable repository asset;
- downloaded the full model from the exact repository revision already frozen
  by `MODEL_PROFILE_LOCK.json`;
- verified its exact 11,141,912,032-byte length and SHA-256
  `d416fa422c9035605c778f60d90a94b288c38b4f9ec2126b58ef938ce8d5f716`;
- changed the offline tokenizer resolver to accept only a hash-verified sparse
  projection or, when it is absent, the hash-verified full model from the same
  frozen lock;
- added tests proving projection preference, exact full-model fallback, and
  rejection of present but mismatched assets;
- reproduced the E83 packet geometry exactly: 21,401 ordinary tokens,
  `RESULT-001` relief, 18,785 treated tokens, feasible;
- passed all 280 repository tests in 299.79 seconds without monkeypatching or
  substituting another model.

Disposition:

- exact provider-free host qualification: passed;
- historical projection remains an optional convenience, not a runtime
  dependency;
- live GPU/provider behavior: not exercised by this qualification;
- no behavioral experiment is selected by this result.

## 2026-08-28 — integrated one-call live-smoke Stage 0

Implemented:

- a frozen one-call contract over the authentic E83 pressure boundary;
- a manifest-bound launcher requiring a clean commit and an external receipt
  for one call, 30,000 serialized tokens, one attempt, and zero retries;
- exact selected-asset verification and the existing CUDA/model runtime gate;
- verified historical parent checkpoint creation before the resumed call;
- exact preflight for 21,401 ordinary tokens, `RESULT-001` first-fit relief,
  18,785 treated tokens, and pending `RESULT-007`;
- raw HTTP and host-provider custody, request/result binding checks, checkpoint,
  mechanical review, runtime release, and final tree seal;
- provider-free tests for the manifest and the entire one-call host transition.

Offline defects caught and repaired before freeze:

- a resumed historical kernel initially lacked the parent checkpoint required
  by the hardened tranche interface;
- the launcher initially queried a review-only invocation structure instead of
  the authoritative event log;
- the raw response check initially named the wrong custody file.

Disposition:

- Stage 0 implementation and focused offline qualification: passed;
- live model behavior: not yet measured;
- next permissible operation after full regression and freeze: the separately
  authorized one-call smoke in `LIVE_SMOKE_PLAN.md`.

Verification:

- selected model/server/tokenizer assets passed exact hash verification and the
  CUDA server bundle received a complete file-hash inventory;
- direct E83 replay passed with the frozen 21,401 / 18,785 token geometry;
- 44 refactored-host tests passed;
- Ruff passed over the selected host/tests/tools path;
- mypy passed over all 13 host modules;
- all 282 repository tests passed in 329.53 seconds;
- GPU/provider calls remained zero.

## 2026-08-28 — live smoke v0 environmental stop

Observed:

- authorization and selected-asset verification passed;
- the fresh-runtime gate found pre-existing `llama-server` PID 12992 and
  stopped before starting this project's server;
- inspection showed that the process served an active Franken Agent job on
  port 18084 and occupied nearly all available VRAM;
- the process was not terminated;
- provider attempts and model calls were both zero;
- the v0 run was sealed and remains closed under its no-retry rule.

Disposition:

- no host or model claim follows from v0;
- preserve the exact failure as `HOST_LIVE_SMOKE_V0_RESULT.md`;
- freeze the unchanged one-call design under v1 and wait for the other GPU job
  to release the device before seeking new exact authorization.

## 2026-08-28 — live smoke v1 tokenizer-projection stop

Observed:

- selected assets and all live server gates passed, including the frozen model
  alias/build, 25,088-token context, 66/66 GPU offload, and PID-on-GPU check;
- the running server reproduced the ordinary packet at exactly 21,401 tokens;
- after deterministic `RESULT-001` relief, it counted 18,786 tokens rather than
  the frozen 18,785-token offline projection;
- the exact-equality gate stopped before completion I/O, released the server,
  sealed the run, and consumed zero provider attempts and zero model calls.

Diagnosis:

- two additional fresh live-server loads reproduced the 18,786 count;
- offline and live paths rendered the same 49,518 bytes with SHA-256
  `fdc87d49f9b66200343f38af6beb5ceeabc6367162126b58efb97fc875a88bcf695`;
- the ordinary packet produced identical token IDs on both paths;
- relieved tokenization first diverged at token index 2,580 and later
  reconverged, so this is a stable tokenizer-engine projection difference, not
  altered messages, model identity, relief selection, or an added BOS token.

Disposition:

- v1 is closed and preserved in `HOST_LIVE_SMOKE_V1_RESULT.md`;
- do not add a tolerance or weaken exact gating;
- v2 freezes 18,785 offline and 18,786 live as distinct exact projections over
  the same frozen prompt bytes;
- a new commit-bound authorization is required before any completion call.

## 2026-08-29 — live smoke v2 qualified checkpoint

Observed:

- all frozen asset and live runtime gates passed;
- exact first-fit `RESULT-001` relief produced the frozen 18,786-token live
  request and preserved the 4,096-token response reserve;
- completed call 8 delivered pending `RESULT-007`;
- Qwen returned a valid batch read for TRANSIT 61–94 and COMMS 61–94;
- the host admitted the action, acquired `RESULT-008`, and left it pending for
  a later invocation rather than falsely marking it delivered;
- one provider attempt completed with 18,786 prompt and 74 completion tokens;
- the candidate remained unchanged and no reopen, repeat demand, failed call,
  or repeated response occurred;
- checkpoint, mechanical review, exact custody, run seal, and runtime release
  verify; the seal SHA-256 is
  `2eb130f3ed5d1cea7c399bbf018c7b15e618624b20f31e8eec421ac9cda021d3`.

Disposition:

- the one-call refactored live host path is qualified at this boundary;
- the action is coherent with the actor's prior depth-first pair pacing, but
  does not establish task integration, artifact quality, loop avoidance, or
  closure behavior;
- v2 is closed after its sole authorized attempt;
- no continuation is selected or authorized by this apparatus result.
