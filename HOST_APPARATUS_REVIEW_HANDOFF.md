# Host apparatus review handoff

Date: 2026-08-28

Status: review-only return point; do not run GPU experiments from the current
runner family

## Immediate diagnosis

The Trellis live result is valid. Its failed Stage 0 prediction exposes a code-
organization problem: provider-free geometry and live execution simulate
result visibility in different code paths. The offline path marked the current
result visible immediately; the live runner marked the previous pending result
visible only when starting a later actor call.

The repository also contains task wrappers that reconfigure historical shared
runners by overwriting module globals. This reduced duplication initially, but
now couples task identity, action surfaces, world classes, contracts, schemas,
and lifecycle logic through mutable process state. The direct-file launch of
the Trellis wrapper also initially failed because its import path depended on
module invocation; no provider call occurred, but it is another sign that the
entrypoint boundary is fragile.

## Current code smells to review

Start with, but do not assume the list is exhaustive:

- `tools/run_solace_pressure_screen.py`: provider lifecycle, prompt assembly,
  visibility, pressure detection, activation, custody, action execution,
  finalization, and sealing in one orchestration path.
- `tools/run_trellis_pressure_screen.py` and similar wrappers: mutation of the
  shared runner's globals to select task, world, contract, and actions.
- `tools/trellis_stage0.py` and other Stage 0 scripts: independent simulations
  of delivery and packet growth rather than calls into the live transition
  kernel.
- `reactive_runtime/records.py`: visibility and residency representation.
- `reactive_runtime/policy.py`: relief selection and message mutation.
- `reactive_runtime/activation.py`: coverage derived from ledger state plus a
  separate pending result.
- task-specific audit modules: repeated replay and expected-result logic.
- reused historical schema labels such as `solace` and `cedar` in later task
  outputs.

The goal of review is not to rename everything. It is to find which duplicated
or mutable boundaries can change experiment meaning.

## Target module boundaries

### 1. Immutable run configuration

A frozen value object should contain task paths, model profile, seed, budgets,
action surface, world adapter, prompt limit, and checkpoint schedule. Runners
receive it as an argument. Imports must not mutate another module's globals.

### 2. Exact event and custody store

Append-only events own exact request, response, action, observation, effect,
candidate, check, and submission identities. Materialized state is derived by
replay.

### 3. Delivery state machine

One transition implementation owns:

```text
ACQUIRED → PENDING → DELIVERED_RESIDENT ↔ DELIVERED_EXTERNAL
```

Delivery occurs only when a completed model invocation includes the result.
Candidate/check currentness remains a separate dimension.

### 4. Packet composer

Given immutable run configuration plus replayed state, produce the complete
model-facing messages. It must enforce one resident copy per canonical exact
body and emit a manifest explaining every included body and handle.

### 5. Capacity manager

Given a rendered pending packet, use the real tokenizer and deterministic
strictly-positive first-fit substitutions until it fits or report an exact
mechanical blocker. It may not consult source-count activation or relevance.

### 6. Provider adapter

One attempt, exact custody, no retry, with an explicit completed/failed outcome.
It should not own task policy or ledger transitions.

### 7. Checkpoint controller

Stop cleanly after a configured tranche, produce a review packet, seal the
snapshot, and resume only from that exact state under new authorization.

## Deduplication behavior to test

- identical source/result body already resident;
- identical object already pending;
- exact reopen of an external object;
- repeated request after reopen;
- same bytes under incompatible object/version binding;
- distinct partially overlapping source ranges;
- receipt substitution whose rendered form has non-positive savings;
- candidate/check observations whose bytes resemble older but stale objects.

Only identical canonical bodies are deduplicated in the first version. Do not
silently merge partially overlapping ranges.

## Checkpoint review packet

The host-generated packet should contain:

- exact event interval and state hashes;
- per-call action, result, prompt/completion usage, and candidate hash;
- new/repeated/resident/external/pending/reopened object identities;
- relief choices and exact token savings;
- artifact diffs and check currency;
- recurrence telemetry without a host judgment of `looping`;
- remaining budgets and resumable snapshot handle;
- links to full raw call custody.

Codex supplies the qualitative interpretation after the pause. The host does
not automatically terminate for unchanged candidates or repeated reads.

## Provider-free acceptance fixtures

At minimum:

1. replay E83 and recover six delivered sources with TRANSIT/COMMS pending;
2. deliver the pending result in a synthetic completed next invocation and
   recover eight delivered sources afterward;
3. request a resident exact body twice and show one body plus compact repeat
   feedback;
4. externalize and reopen the same body without duplication;
5. prove offline and live-mode packet construction is byte-identical from the
   same events;
6. stop at call 12, seal, hydrate, and render the same call-13 packet as an
   uninterrupted provider-free run;
7. fail safely when no positive-savings relief exists;
8. preserve stale check binding across unrelated observations;
9. keep one-attempt/no-retry semantics through provider failure; and
10. run historical regression without changing sealed results.

## Review decisions still open

These are implementation review questions, not reasons to resume GPU work:

- whether delivery is committed at completed provider response or needs an
  intermediate `included_in_request` audit event;
- the exact canonical identity for source spans versus wrapped result bodies;
- whether compact `already_resident` feedback is a result object or a control
  event visible to the next actor call;
- how review-tranche continuation IDs bind to one parent trajectory;
- whether the provisional 12-call tranche and 60-call maximum remain suitable
  after offline cost simulation.

## Non-goals

Do not add notes, digests, scaffold policies, semantic relevance, model-managed
eviction, phase inference, loop classification, or multi-agent control during
this refactor. Do not migrate every historical runner before one thin path and
the E83 replay pass.

## Completion condition

The apparatus is ready for new experiment planning only when the acceptance
criteria in the bounded-context program repository's
`HOST_RUNTIME_REFACTOR_HANDOFF.md` are met and an independent code review finds
no second implementation of delivery semantics in the selected live path.

No GPU operation is selected or authorized.
