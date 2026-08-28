# Refactor acceptance test matrix

Date: 2026-08-28

| Acceptance claim | Provider-free evidence |
|---|---|
| One delivery transition law | `test_host_refactor_kernel.py`; all selected host modules are statically checked for legacy visibility mutation |
| E83 has six delivered sources and TRANSIT/COMMS pending | `test_host_refactor_trellis_fixture.py` |
| A completed next invocation produces eight delivered sources | `test_host_refactor_trellis_fixture.py` |
| Acquisition, scheduling, and delivery are distinct | kernel transition test and provider-failure test |
| E83 packet parity | refactor packet equals frozen `FINAL_MESSAGES.json` |
| Common relief without semantic gate | E83 21,401-token packet selects RESULT-001 and becomes feasible |
| Exact deduplication | generic and Trellis end-to-end repeat-read tests |
| Reopen without duplicate body | externalize/reopen placement test plus property cycles |
| No partial-overlap or cross-version merging | canonical-body tests |
| Replaceable exact current candidate | state-slot and Trellis mutation tests |
| Check-to-candidate currentness | current then stale packet-projection test |
| One-shot provider behavior and raw custody | provider failure and live-style tranche tests |
| Twelve-call pause and exact call-13 resume | checkpoint/runner tests |
| Exact task-domain resume | Trellis candidate files, phase, check state, result index, and counters round trip |
| Distinct terminal dispositions | provider, invalid action, capacity, call, and token enums; focused runner tests |
| Mechanical review without loop judgment | checkpoint review test asserts `semantic_judgment: null` and literal telemetry |
| Immutable task configuration | Trellis adapter import leaves historical runner globals unchanged |
| Thin selected live-style path | `live_path.py` tranche test writes per-call custody, checkpoint, review, and remains resumable |
| Randomized replay stability | Hypothesis delivery/externalization/reopen cycles and identity properties |
| Historical compatibility | full apparatus regression suite |
| Final request/message binding | adversarial payload-builder test rejects altered messages before provider invocation and delivery |
| Finish-reason admission | truncated response is custodied, rejected nonterminally, and never reaches the domain adapter |
| Ordinary rejection continuity | parse/action rejection becomes an exact scheduled observation and permits another call |
| Native reopen authority | Trellis reopen transitions the original delivered-external result through the kernel |
| Lifecycle-derived reopen catalog | pending and resident results are absent from the provider action schema |
| State exposure binding | provider failure records attempted exact state exposure but no completed exposure event |
| Frozen execution manifest and reserve | configuration mismatch fails hydration; prompt allowance equals context minus reserve |
| Prospective total budget | serialized budget blocks before provider invocation |
| Chained tranche resume | second tranche verifies and binds its exact parent checkpoint |
| Rich mechanical review | request/exposure, custody, usage/timing, action disposition, candidate diff, and recurrence evidence are present |

## Verification commands

```text
python -m ruff check host_refactor tests/test_host_refactor_*.py tools/replay_trellis_host_refactor.py
python -m mypy --follow-imports=skip host_refactor
python -m pytest -q tests -k host_refactor
python -m pytest -q
python tools/replay_trellis_host_refactor.py --repository-root .
```

The direct replay command uses the bundled exact tokenizer and no provider. It
must report six delivered sources, pending COMMS/TRANSIT, 21,401 ordinary
prompt tokens, RESULT-001 relief, and a feasible packet.

## Current qualification receipt

- 11 adversarial hardening tests passed.
- 18 combined checkpoint/live/hardening tests passed.
- Ruff and mypy passed.
- 277 repository tests passed using a tokenizer-compatible local Qwen3.8 GGUF
  injected only into the test process.
- The direct exact replay command is currently blocked because the tokenizer
  projection frozen in `MODEL_PROFILE_LOCK.json` is absent. The compatible run
  is regression evidence, not an exact-lock qualification.
