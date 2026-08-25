# Ordinary actor actions

Return exactly one JSON object and no surrounding prose.

- `{"action":"read_source","source_id":"S01","start_line":1,"end_line":70}`
- `{"action":"read_batch","requests":[{"source_id":"S01","start_line":1,"end_line":70},{"source_id":"S02","start_line":1,"end_line":70}]}`
- `{"action":"reopen_exact","result_id":"RESULT-001"}`
- `{"action":"replace_evidence_ledger","content":"# Evidence Integration Ledger\n..."}`
- `{"action":"upsert_decision_section","heading":"Decision, scope, and authority","body":"..."}`
- `{"action":"replace_decision","content":"# Cedar Valley Evacuation Operations Decision\n..."}`
- `{"action":"run_check"}`
- `{"action":"submit"}`

One source range is at most 120 lines. A batch contains at most two
non-overlapping ranges, 160 total lines, 12,000 exact source bytes, and a 6,500
token model-visible result. The same 6,500-token result cap applies to a single
source read. A section upsert changes one declared level-two section while
preserving the other exact sections. Checks bind to the current composite
candidate hash.
