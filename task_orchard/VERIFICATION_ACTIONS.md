# Orchard bounded verification action contract

Return exactly one JSON action object and no prose.

Allowed actions:

```text
{"action":"patch_decision","edits":[{"old":"exact unique current text","new":"replacement text"}]}
{"action":"run_check"}
{"action":"read_source","source_id":"CHARTER","start_line":1,"end_line":20}
{"action":"read_batch","requests":[{"source_id":"CURRENT","start_line":1,"end_line":20},{"source_id":"ASSAY","start_line":1,"end_line":20}]}
{"action":"reopen_exact","result_id":"RESULT-..."}
{"action":"submit"}
```

Use the candidate-bound expected/observed findings. Repair with bounded exact
edits, observe the effect, and recheck the changed candidate. A passing
mechanical check does not itself authorize release, restart, or closure.
