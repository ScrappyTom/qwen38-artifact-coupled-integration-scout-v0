# Solace Verification-Frame Action Contract

Return exactly one JSON action object and no prose.

The current candidate and its latest admitted effect are already visible. Begin by checking the current candidate. Use the candidate-bound findings to make bounded repairs, recheck after every candidate change, and submit only when the current check passes and external readiness adjudication remains the only unresolved authority.

Allowed actions:

```json
{"action":"patch_decision","edits":[{"old":"exact unique current text","new":"replacement text"}]}
{"action":"run_check"}
{"action":"read_source","source_id":"AURORA","start_line":1,"end_line":20}
{"action":"read_batch","requests":[{"source_id":"BASTION","start_line":1,"end_line":20},{"source_id":"CIPHER","start_line":1,"end_line":20}]}
{"action":"reopen_exact","result_id":"RESULT-..."}
{"action":"submit"}
```

`patch_decision` is a bounded exact edit operation. It permits 1–24 edits, requires every `old` anchor to occur exactly once in the current decision, limits each old anchor to 2,000 UTF-8 bytes, and limits all replacement text in one action to 12,000 UTF-8 bytes. It does not authorize semantic repair by the host; the actor chooses every edit.

Source reads and exact reopens remain available when the candidate-bound findings require exact evidence. The source catalog gives the valid line bounds.

A successful patch makes every earlier check stale. `run_check` binds its findings to one exact candidate hash. A passed mechanical check does not itself authorize operational recovery or prove independent readiness.
