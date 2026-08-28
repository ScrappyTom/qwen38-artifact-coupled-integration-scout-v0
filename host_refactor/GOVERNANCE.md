# Refactor governance

## Objective

Make the host mechanically exact, modular, and auditable so future experiment
results can be attributed to the tested system rather than divergent host
implementations.

## Authority boundaries

The host may decide only mechanical facts: exact identity, delivery,
residency, capacity, currentness, resource limits, and whether an operation is
valid under a frozen contract. It may not decide relevance, task sufficiency,
looping, readiness, or what the model should do next.

The model chooses reads, reopens, construction, checks, repairs, and proposed
closure. Codex performs qualitative review only at explicit checkpoints.

## Change protocol

Every implementation slice must:

1. name the invariant it enforces;
2. add or strengthen a provider-free test;
3. avoid modifying sealed historical result directories;
4. avoid GPU/provider calls;
5. record its disposition in `WORK_LOG.md`;
6. update `DECISIONS.md` when a real design fork is resolved;
7. pass the focused test set before the next slice begins.

Historical runners remain frozen references. Migration means building a new
configured path, not silently rewriting the runner that produced an existing
result.

## Checkpoint cadence

A written checkpoint is required after each of these milestones:

- audit and cut line;
- event/delivery kernel;
- packet projection and deduplication;
- pressure relief;
- checkpoint/resume;
- thin-runner integration;
- full regression and documentation reconciliation.

Each checkpoint records completed work, tests run, unresolved risks, and the
next bounded slice. If a test exposes a change in experiment meaning, work
stops for explicit design review rather than repairing around the failure.

## Acceptance criteria

1. One delivery transition kernel is used by the new offline fixture, replay,
   packet composer, and thin runner.
2. E83 replay reconstructs six delivered sources and pending TRANSIT/COMMS.
3. Completing the next synthetic invocation reconstructs eight delivered
   sources.
4. Delivery is not inferred from acquisition, scheduling, or prompt assembly.
5. No new task wrapper mutates globals in another runner module.
6. Identical canonical exact bodies cannot coexist in one active packet.
7. A repeated resident request emits compact, auditable feedback without
   duplicating bytes.
8. An external exact object can be reopened once without duplication.
9. Partially overlapping spans are not silently merged.
10. Deterministic strictly-positive first-fit relief is available regardless
    of semantic activation gates and stops immediately at feasibility.
11. No-positive-savings and no-eligible-relief cases stop with an exact
    capacity blocker.
12. A run can pause after twelve completed actor calls, seal state, hydrate it,
    and render the identical next packet.
13. Provider failure, unexpected domain failure, request-binding failure,
    capacity blocker, checkpoint pause, and budget exhaustion have distinct
    terminal codes; expected parse/action rejection remains nonterminal.
14. Provider attempts are one-shot; the host performs no retry.
15. The selected offline and live-style adapters render byte-identical packets
    from the same event log.
16. Existing historical tests remain green.

## Live-hardening acceptance extension

The offline core criteria above remain satisfied but do not by themselves
qualify a general live experiment host. Before the next GPU authorization, the
selected path must also satisfy every case in `LIVE_HARDENING_PLAN.md`:

- final-request-to-delivery and state-exposure binding;
- nonterminal exact action rejection;
- native kernel reopen through the task adapter;
- frozen finish-reason admission;
- mechanically reconciled context/completion and prospective token budgets;
- execution-manifest-bound checkpoint hydration;
- chained checkpoints and attempt/completion/failure accounting;
- investigator-ready mechanical review evidence.

This is one bounded hardening pass. It may not grow into another semantic,
experiment-design, or historical-runner migration project.

## Explicit non-goals

- semantic notes, digests, or scaffolds;
- relevance ranking;
- model-managed residency;
- automatic loop detection;
- automatic phase discovery;
- learned policies;
- multi-agent control;
- migration of every historical runner;
- a universal product memory abstraction.
