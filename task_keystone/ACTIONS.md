# Keystone construction action contract

Return exactly one JSON action object and no prose.

```text
{"action":"read_source","source_id":"MANDATE","start_line":1,"end_line":60}
{"action":"read_batch","requests":[{"source_id":"MANDATE","start_line":1,"end_line":60},{"source_id":"TRACK","start_line":1,"end_line":60}]}
{"action":"reopen_exact","result_id":"RESULT-001"}
{"action":"replace_evidence_ledger","content":"complete compact task-native matrix"}
{"action":"upsert_decision_section","heading":"Authority, scope, and operating states","body":"exact section body"}
{"action":"patch_decision","edits":[{"old":"exact unique text","new":"replacement text"}]}
{"action":"replace_decision","content":"complete exact decision"}
{"action":"begin_verification"}
```

One read may contain at most 120 lines. A batch may contain one or two ranges,
at most 160 lines and 12,000 exact source bytes. `begin_verification` is valid
only after the frozen mechanical construction milestone. It changes lifecycle
phase, not candidate bytes, and does not assert readiness.
