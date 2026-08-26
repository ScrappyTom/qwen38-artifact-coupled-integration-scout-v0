# Action contract

Return exactly one JSON object using one currently allowed action.

```text
{"action":"read_source","source_id":"AURORA","start_line":1,"end_line":64}
{"action":"read_batch","requests":[{"source_id":"AURORA","start_line":1,"end_line":64},{"source_id":"BASTION","start_line":1,"end_line":64}]}
{"action":"reopen_exact","result_id":"RESULT-001"}
{"action":"replace_evidence_ledger","content":"complete compact task-native matrix"}
{"action":"upsert_decision_section","heading":"Authority, scope, and restoration decision","body":"exact section body"}
{"action":"replace_decision","content":"complete exact decision"}
{"action":"run_check"}
{"action":"submit"}
```

One read may contain at most 120 lines. One batch may contain one or two ranges,
at most 160 total lines, 12,000 source bytes, and 6,500 model-visible result
tokens. Same-source ranges may not overlap. Use exact catalog IDs and in-range
line bounds.

Both configurations have the same ordinary action surface. Treatment may
receive separately charged, partially admitted provenance-local records after
exact source bodies are externalized. Those records are incomplete and non-
authoritative. Cross-source synthesis belongs in the exact candidate with all
supporting citations. Checks bind to the exact candidate; any later effect
makes the prior check stale. Submission never self-authorizes readiness.
