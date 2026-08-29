# Live hardening plan

Date: 2026-08-28

Status: implementation and provider-free qualification complete; exact locked-
asset qualification blocked because the frozen tokenizer projection is absent;
no GPU/provider operation is selected or authorized

## Objective

Extend the qualified offline host core across the final generic-host/live-task
seams without reopening the architecture. The pass succeeds only if the host
can prove what exact request crossed a completed model boundary, preserve
ordinary rejected actions as nonterminal evidence, exercise reopen through the
native lifecycle, enforce frozen response/resource contracts, and produce a
reviewable chained checkpoint.

## Frozen scope

1. Bind the composed packet, packet manifest, final provider messages, exact
   result exposures, and exact state-slot exposures to each attempted request.
2. Commit delivery and state exposure only from a mechanically verified final
   request and a completed provider invocation.
3. Treat parse/action/domain rejections declared by the task adapter as exact,
   nonterminal observations. Unexpected adapter/host failures remain terminal.
4. Route `reopen_exact` through `HostKernel.request_reopen()` on the original
   result. Derive reopen capability from projected lifecycle state.
5. Admit actions only for prospectively accepted provider finish reasons.
6. Bind context window, completion reserve, execution manifest, and prospective
   trajectory budget in immutable configuration.
7. Chain checkpoints and distinguish provider attempts, completed invocations,
   and failed invocations.
8. Expand the twelve-call mechanical review with request/response custody,
   action/rejection disposition, candidate diffs, finish reason, usage/timing,
   and exact exposure records.

## Explicit non-goals

- semantic notes, registers, digests, or progress state;
- relevance or loop classification;
- automatic phase detection;
- a new experiment task or treatment;
- migration or rewriting of sealed historical runners;
- rewriting already-pushed commits to change authorship;
- any live model, GPU, or external provider call.

## Acceptance cases

1. A payload builder that drops or changes packet messages is rejected before
   provider invocation and commits no delivery.
2. `finish_reason=length` is custodied, commits verified request exposure, emits
   a nonterminal response rejection, and executes no domain action.
3. An ordinary domain/action rejection leaves the candidate unchanged, creates
   an exact scheduled rejection observation, and permits a later call.
4. A Trellis reopen moves the original result external to pending to resident,
   emits `REOPEN_REQUESTED`, and renders one exact body.
5. A resident result is never advertised as reopenable merely because an older
   transcript position renders as a receipt.
6. A provider failure after candidate mutation records attempted request
   binding but no completed candidate exposure.
7. Checkpoint hydration fails under a different execution-manifest binding.
8. The effective prompt allowance is mechanically derived from context window
   minus completion reserve, and the total trajectory ceiling is checked before
   a provider attempt.
9. The review packet contains exact exposure, action/rejection, provider,
   candidate-transition, custody, cache/usage, and timing evidence without a
   semantic loop judgment.
10. A second tranche binds and verifies the first checkpoint as its parent and
    reports attempts, completions, and failures separately.

## Stop rule

If satisfying an acceptance case requires semantic judgment, post-hoc repair,
or changes the meaning of a sealed experiment, stop and record a design
blocker. Otherwise finish this bounded pass, run the complete regression suite,
and reconcile program documentation before selecting any live experiment.

## Disposition

All ten code-level acceptance cases are implemented and covered provider-free.
The focused suite, static checks, and a full 277-test regression using a locally
available tokenizer-compatible Qwen3.8 model pass. Exact replay qualification
could not yet be claimed because the frozen tokenizer projection at the path
and hash declared by `MODEL_PROFILE_LOCK.json` was found missing after the
power outage.

The compatible model was injected only inside the test process. No lock,
runtime path, sealed fixture, or historical result was changed. See
`HOST_LIVE_HARDENING_RESULT.md`.

## Subsequent resolution

`HOST_ASSET_RESTORATION_RESULT.md` closes this checkpoint's asset blocker. The
immutable full model already named and hashed by the frozen lock was restored,
the tokenizer resolver gained a hash-verified full-model fallback, the exact
E83 replay passed, and all 280 repository tests passed without substitution.
