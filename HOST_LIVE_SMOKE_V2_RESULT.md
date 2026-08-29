# Refactored host live smoke v2 result

Date: 2026-08-29

Freeze commit: `3afd9e269abb437512ea961772b43f4a12ea0f30`

Run ID: `2026-08-28-host-refactor-live-smoke-v2`

Disposition: qualified and stopped at the mandatory checkpoint after exactly
one model call, one attempt, and zero retries.

## Mechanical result

The fresh CUDA server passed exact asset identity, model alias/build,
25,088-token context, 66/66 GPU offload, and PID-on-GPU gates. The live prompt
contained 18,786 tokens after deterministic first-fit externalization of
`RESULT-001`, matching the v2 live projection exactly. The request included
pending `RESULT-007`, and the completed invocation made it delivered-resident
on call 8.

Qwen returned one valid action:

```json
{
  "action": "read_batch",
  "requests": [
    {"source_id": "TRANSIT", "start_line": 61, "end_line": 94},
    {"source_id": "COMMS", "start_line": 61, "end_line": 94}
  ]
}
```

The host admitted the action, acquired exact `RESULT-008`, and correctly left
it pending because it has not yet crossed a later completed model invocation.
The candidate stayed at its initial hash. There were no failed invocations,
reopens, repeat demands, repeated assistant messages, or candidate mutations.

The call used 18,786 prompt tokens and 74 completion tokens, for 18,860
serialized tokens. Provider time was 26.98 seconds. The fresh server had no
prefix cache reuse, as expected for this isolated smoke.

The checkpoint, request/response custody, action disposition, mechanical
review, and run seal all verify. The server released cleanly and no
`llama-server` process remained. The run seal SHA-256 is
`2eb130f3ed5d1cea7c399bbf018c7b15e618624b20f31e8eec421ac9cda021d3`.

## Transcript-level interpretation

The visible update was the first half of TRANSIT and COMMS. Qwen immediately
requested the remaining halves of those same two sources. This is coherent
with the depth-first source-pair pacing seen before the pressure boundary. It
is evidence that result delivery, exact prompt reconstruction, action
transport, result acquisition, and checkpointing work together on the live
path. It also confirms that a newly acquired result remains pending rather
than being falsely counted as model-visible.

It is not evidence that the actor can integrate the complete task, avoid later
loops, construct a good artifact, verify it, or close correctly. The smoke was
deliberately too short to answer any of those questions.

## Disposition

The refactored live host path is qualified for this one-call boundary. V2 is
closed under its one-attempt rule. Any continuation from the sealed checkpoint
requires a separately designed freeze and explicit authorization; none is
selected by this result.
