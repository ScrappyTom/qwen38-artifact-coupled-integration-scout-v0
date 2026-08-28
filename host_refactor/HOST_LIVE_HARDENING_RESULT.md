# Host live-hardening result

Date: 2026-08-28

## Outcome

The bounded hardening pass succeeded at the code and provider-free apparatus
level. The refactored host now closes the live seams identified in external
review:

- final provider payloads cannot silently diverge from composed packets;
- delivery and current-state exposure are committed only from the verified
  request that reached a completed invocation;
- truncated responses and expected task/action rejections remain exact,
  nonterminal evidence;
- native reopen operates on the original externally delivered result;
- reopen capability comes from lifecycle state, not transcript receipts;
- context, completion reserve, prompt allowance, execution manifest, accepted
  finish reasons, and total trajectory budget are mechanically frozen;
- tranche resume verifies and chains its exact parent checkpoint;
- review output distinguishes attempts, completions, failures, candidate
  changes, action disposition, exposure, raw custody, usage, and timing.

The pass also found and corrected a subtle deterministic-replay issue. Provider
wall-clock duration had initially entered the authoritative invocation event,
causing uninterrupted and checkpoint-resumed histories to differ. Timing is
now retained as custody/review telemetry rather than authoritative task state.

## Verification

| Evidence | Result |
|---|---:|
| New adversarial hardening tests | 11 passed |
| Combined checkpoint/live/hardening tests | 18 passed |
| Ruff | passed |
| mypy (`--follow-imports=skip host_refactor`) | passed, 12 modules |
| Full repository regression with compatible tokenizer | 277 passed in 307.51 s |
| GPU/provider calls | 0 |

The compatible full regression used the unchanged tokenizer executable and a
locally available Qwen3.8 GGUF injected only by an in-process test monkeypatch.
No tracked lock, path, source, sealed fixture, or historical result changed.
The same compatible asset also reproduced the frozen E83 token-count/relief
assertion locally.

## Exact qualification blocker

The frozen tokenizer projection declared by `MODEL_PROFILE_LOCK.json` is
missing after the power outage:

```text
path:
E:\AI_Models\AtomicChat__Qwen3.8-27B-GGUF__ca10ebceb188\Qwen3.8-27B-AD-IQ2_S.tokenizer-projection.gguf

expected SHA-256:
7047272e809b62b5c68b6427a349cba78b2f45109de04350d48f0338db68eef3
```

The locked `llama-tokenize.exe` remains present and matches:

```text
d435fb84f60d6c21dbd2adcb0beb38555f2921894909c98f9236bf0984971b1c
```

A different 13,146,393,504-byte Qwen3.8 GGUF is available locally and appears
tokenizer-compatible, but its different identity cannot satisfy the frozen
asset contract. The host therefore must not be described as exactly
live-qualified yet.

## Disposition

```text
event-driven core                         accepted offline
generic live-seam hardening               accepted provider-free
historical regression                     passed with compatible tokenizer
exact frozen-tokenizer qualification      blocked
live GPU/provider readiness               not claimed
```

The next eligible operation is restoration of the exact tokenizer projection,
hash verification, then provider-free rerun of the direct E83 replay and the
full suite. Restoring that asset does not authorize a GPU or provider run.
