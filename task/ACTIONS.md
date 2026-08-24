# Ordinary actor actions

Return exactly one JSON object and no surrounding prose.

- `{"action":"read_source","source_id":"S01","start_line":1,"end_line":120}`
- `{"action":"read_batch","requests":[{"source_id":"S01","start_line":1,"end_line":120},{"source_id":"S02","start_line":1,"end_line":120}]}`
- `{"action":"reopen_exact","result_id":"RESULT-001"}`
- `{"action":"replace_evidence_ledger","content":"# Evidence Integration Ledger\n..."}`
- `{"action":"upsert_decision_section","heading":"Decision and scope","body":"..."}`
- `{"action":"replace_decision","content":"# Northstar Migration Architecture Decision\n..."}`
- `{"action":"run_check"}`
- `{"action":"submit"}`

One source range is at most 240 lines. A batch contains at most three
non-overlapping ranges, 480 total lines, and 40,000 exact source bytes. A
section upsert changes one declared level-two section while preserving the
other exact sections. Checks bind to the current composite candidate hash.
