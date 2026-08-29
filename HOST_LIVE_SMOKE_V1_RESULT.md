# Refactored host live smoke v1 result

Date: 2026-08-28

Freeze commit: `a92577d64612a6a5f7c623e02de89eb527b47017`

Run ID: `2026-08-28-host-refactor-live-smoke-v1`

Disposition: sealed before provider I/O; zero model calls and zero retries.

## What happened

The selected assets, fresh server, model alias/build, 25,088-token context,
66/66 GPU offload, and PID-on-GPU gates passed. The live server counted the
ordinary packet as the expected 21,401 tokens. After deterministic
`RESULT-001` externalization it counted the relieved packet as 18,786 tokens,
one more than the frozen offline projection of 18,785. The exact-equality gate
stopped before completion I/O and released the server cleanly.

## Diagnostic result

Three fresh live server loads—the v1 launch and two separately custodied
tokenizer diagnostics—reproduced 18,786 live tokens. The offline executable
reproduced 18,785. Both paths rendered exactly the same 49,518 prompt bytes
with SHA-256
`fdc87d49f9b66200343f38af6beb5ceeabc6367162124efb97fc875a88bcf695`.
The ordinary packet's bytes and all 21,401 token IDs were identical. The
relieved packet's tokenization began differing at token index 2,580 and later
reconverged; this was not a rendering, source, receipt-selection, or model-file
identity difference.

The runtime manifest already declares live prompt counts to be authoritative.
The correction is therefore not a tolerance. V2 freezes both exact projections:

- offline qualification: 18,785;
- live running-server qualification: 18,786.

Both are far below the 20,992-token prompt limit and select the same sole
first-fit relief result.

## Custody and claim limit

The v1 tree is sealed at
`qualification_runs/2026-08-28-host-refactor-live-smoke-v1` with seal SHA-256
`5dfbc9bc52f3f220602097ff4f4ed5572e45e74f17be6c0e0e91dbfc9d29602f`.
No chat-completion request occurred. V1 is closed; v2 requires a new exact
commit-bound authorization.
