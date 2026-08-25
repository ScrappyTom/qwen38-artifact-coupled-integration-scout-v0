# Action contract

Return exactly one JSON object using one currently allowed action.

```text
{"action":"read_source","source_id":"AXIOM","start_line":1,"end_line":70}
{"action":"read_batch","requests":[{"source_id":"AXIOM","start_line":1,"end_line":70},{"source_id":"BRAMBLE","start_line":1,"end_line":70}]}
{"action":"reopen_exact","result_id":"RESULT-001"}
{"action":"upsert_evidence_slot","source_id":"AXIOM","source_version":"<exact catalog sha256>","content":"source-local bounded work"}
{"action":"upsert_decision_section","heading":"Decision, scope, and authority","body":"exact section body"}
{"action":"replace_decision","content":"complete exact decision"}
{"action":"run_check"}
{"action":"submit"}
```

One read may contain at most 120 lines. One batch may contain one or two ranges,
at most 160 total lines, 12,000 source bytes, and 6,500 model-visible result
tokens. Same-source ranges may not overlap. Use exact catalog IDs and in-range
line bounds.

`upsert_evidence_slot` is available only in the direct-work configuration. It
replaces one exact source/version slot and cannot edit any other source slot.
The local-delta configuration receives mechanically merged source-local work
through its separately costed maintenance channel.

Checks bind to the exact candidate version. Any later candidate effect makes
the prior check stale. Submission never self-authorizes readiness.
