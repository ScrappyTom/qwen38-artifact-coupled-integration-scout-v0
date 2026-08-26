# Action contract

Return exactly one JSON object using one currently allowed action.

```text
{"action":"read_source","source_id":"ANCHOR","start_line":1,"end_line":64}
{"action":"read_batch","requests":[{"source_id":"ANCHOR","start_line":1,"end_line":64},{"source_id":"BRIDGE","start_line":1,"end_line":64}]}
{"action":"reopen_exact","result_id":"RESULT-001"}
{"action":"replace_evidence_ledger","content":"complete compact task-native matrix"}
{"action":"upsert_decision_section","heading":"Authority, scope, and recovery decision","body":"exact section body"}
{"action":"replace_decision","content":"complete exact decision"}
{"action":"run_check"}
{"action":"submit"}
```

One read may contain at most 120 lines. One batch may contain one or two ranges,
at most 160 total lines, 12,000 source bytes, and 6,500 model-visible result
tokens. Same-source ranges may not overlap. Use exact catalog IDs and in-range
line bounds.

Both configurations have the same ordinary action surface. The treatment may
receive separately charged provenance-local source reports after exact source
bodies are externalized, but those reports are not source truth, task work,
verification, or readiness authority. Cross-source synthesis belongs in the
exact candidate and must cite all supporting sources.

Checks bind to the exact candidate version. Any later candidate effect makes
the prior check stale. Submission never self-authorizes readiness.
