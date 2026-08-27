# Keystone bounded verification action contract

Return exactly one JSON action object and no prose.

```text
{"action":"replace_artifact_section","candidate_sha256":"CURRENT","artifact_sha256":"CURRENT","section_heading":"exact heading","expected_section_sha256":"CURRENT","replacement_section":"complete heading and replacement section"}
{"action":"run_check"}
{"action":"read_source","source_id":"TRACK","start_line":1,"end_line":20}
{"action":"read_batch","requests":[{"source_id":"TRACK","start_line":1,"end_line":20},{"source_id":"SIGNAL","start_line":1,"end_line":20}]}
{"action":"reopen_exact","result_id":"RESULT-..."}
{"action":"submit"}
```

The bound repair must name the exact current candidate, exact current decision
artifact, one unique declared section, and the exact section bytes being
replaced. A rejected repair does not change candidate state and remains
unresolved until a candidate effect occurs. After an admitted repair, observe
its effect and recheck the changed candidate. A passing check is not service or
closure authority.
