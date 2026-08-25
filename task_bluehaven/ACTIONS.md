# Ordinary actor actions

Return exactly one JSON object and no surrounding prose.

- `{"action":"read_source","source_id":"S01","start_line":1,"end_line":70}`
- `{"action":"read_batch","requests":[{"source_id":"S01","start_line":1,"end_line":70},{"source_id":"S02","start_line":1,"end_line":70}]}`
- `{"action":"reopen_exact","result_id":"RESULT-001"}`
- `{"action":"replace_evidence_ledger","content":"# Evidence Integration Ledger\n..."}`
- `{"action":"upsert_decision_section","heading":"Decision, scope, and authority","body":"..."}`
- `{"action":"replace_decision","content":"# Bluehaven Drinking-Water Restoration Decision\n..."}`
- `{"action":"run_check"}`
- `{"action":"submit"}`

One source range is at most 120 lines. A batch contains at most two
non-overlapping ranges, 160 total lines, 12,000 exact source bytes, and a 6,500
token model-visible result. The same result cap applies to a single read.
Candidate effects invalidate checks of an earlier candidate. A check result
always names the exact candidate it evaluated and whether that result is
current for the presently visible candidate.
