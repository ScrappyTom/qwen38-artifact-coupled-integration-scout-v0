# Host runtime refactor result

Date: 2026-08-28

Implementation commit:
`a84f51ce1797cd00574fbc0f1f8d59945e8da2ff`

Disposition: offline host refactor qualified; historical runners remain frozen;
no GPU operation is selected or authorized.

## Outcome

The host refactor is implemented as a governed subproject in `host_refactor/`.
It replaces the selected future path's duplicated visibility/residency logic
with one append-only event kernel and keeps task behavior behind immutable
adapters.

The selected path now provides:

- explicit acquired, pending, delivered-resident, and delivered-external
  states;
- delivery committed only by a completed model invocation;
- pure packet projection from replayed events;
- one canonical exact body per active object/version/span/payload identity;
- compact visible feedback for repeated resident demand;
- exact receipts and reversible reopen;
- deterministic strictly-positive first-fit relief without semantic gates;
- replaceable exact current-candidate state;
- mechanical current/stale binding for the latest delivered check;
- one-shot provider request/response/failure custody;
- twelve-call checkpoint, mechanical review, exact domain-state snapshot, and
  resume;
- an immutable Trellis adapter rather than shared-runner global mutation;
- a thin live-style tranche coordinator whose provider-free test writes exact
  per-call custody and remains resumable.

## E83 correction fixture

Replaying the sealed Trellis boundary through the new kernel reconstructs:

- delivered sources: CLIMATE, CLINIC, COUNCIL, GRID, SHELTER, WATER;
- pending sources: COMMS, TRANSIT;
- ordinary prompt: 21,401 tokenizer tokens;
- prompt limit: 20,992;
- deterministic first positive relief: RESULT-001;
- new-format relieved prompt: 18,785 tokens;
- completed synthetic next invocation: all eight sources delivered.

The pre-relief refactor packet equals the frozen live `FINAL_MESSAGES.json` at
the canonical message level. Stage 0's earlier eight-source prediction is not
reproduced because acquisition and scheduling no longer imply delivery.

## Verification

- Ruff: passed;
- mypy with legacy imports skipped: passed for 11 new host modules;
- focused host-refactor tests: 31 passed;
- complete historical and new suite: 266 passed in 255.09 seconds;
- randomized replay/property tests: passed;
- direct E83 replay: passed;
- GPU/model/provider calls: zero.

## Scope and limitations

The result qualifies host mechanics, not bounded-agent utility.

- Historical experiment runners are unchanged and retain their original
  semantics.
- The selected v0 kernel allows one pending exact result for each actor call.
- Checkpoints preserve exact bytes and may be large; no semantic compaction was
  introduced.
- Twelve calls per tranche and sixty calls maximum remain provisional review
  defaults.
- The host records recurrence but does not label a loop, decide relevance, or
  force closure.
- A future experiment still needs its own frozen task contract, external
  authorization, model-server launcher, budgets, and final sealing.
- Provider capability was exercised only with provider-free callbacks. No GPU
  inference was performed.

## Program consequence

The apparatus is ready to return to experiment design using the new path. A
future run should not import the frozen global-mutating pressure-screen runner.
It should configure the event kernel, task adapter, capacity manager, and
tranche coordinator directly; freeze the launcher around that path; and pause
for transcript review every twelve completed actor calls.

The next scientific design remains interaction-level. Host correctness does
not select a semantic memory, scaffold, or relevance policy.

