# Orchard action contract

Return exactly one JSON object using one currently allowed action.

```text
{"action":"read_source","source_id":"CHARTER","start_line":1,"end_line":60}
{"action":"read_batch","requests":[{"source_id":"CHARTER","start_line":1,"end_line":60},{"source_id":"CULTURE","start_line":1,"end_line":60}]}
{"action":"reopen_exact","result_id":"RESULT-001"}
{"action":"replace_evidence_ledger","content":"complete compact task-native matrix"}
{"action":"upsert_decision_section","heading":"Authority, scope, and restart states","body":"exact section body"}
{"action":"patch_decision","edits":[{"old":"exact unique text","new":"replacement text"}]}
{"action":"replace_decision","content":"complete exact decision"}
{"action":"begin_verification"}
{"action":"run_check"}
{"action":"submit"}
```

One read may contain at most 120 lines. One batch may contain one or two ranges,
at most 160 total lines and 12,000 source bytes. Same-source ranges may not
overlap. Use exact catalog IDs and in-range bounds.

`begin_verification` is valid only after the frozen mechanical construction
milestone passes. It changes phase, not candidate bytes, and does not assert
readiness. A successful patch makes every earlier check stale. Submission does
not self-authorize readiness.
