# Host locked-asset restoration result

Date: 2026-08-28

## Outcome

The stale locked-tokenizer blocker is resolved. The exact immutable full model
already named by `MODEL_PROFILE_LOCK.json` has been restored to its frozen path
and verified byte-for-byte:

```text
path:
E:\AI_Models\AtomicChat__Qwen3.8-27B-GGUF__ca10ebceb188\Qwen3.8-27B-AD-IQ2_S.gguf

bytes:
11,141,912,032

SHA-256:
d416fa422c9035605c778f60d90a94b288c38b4f9ec2126b58ef938ce8d5f716
```

The historical sparse tokenizer projection was reconstructed from the archived
session record and found to have been created by copying a download while that
download was still in progress, then extending the copy sparsely. Its recorded
hash therefore identifies an accidental transient snapshot, not a deterministic
artifact obtainable from the immutable model revision.

The durable fix is not to weaken identity checks or accept an unrelated Qwen
model. `OfflineTokenizer` now resolves only one of two assets already declared
by the frozen lock:

1. the sparse tokenizer projection, if its exact recorded hash is present; or
2. the immutable full model, if its exact recorded hash is present.

If neither matches, execution stops. No historical lock, sealed result, task
fixture, or expected packet count was changed.

## Verification

| Evidence | Result |
|---|---:|
| Locked asset size and SHA-256 | exact match |
| Asset-resolution tests | 3 passed |
| Direct E83 ordinary packet | 21,401 tokens |
| Deterministic first-fit choice | `RESULT-001` |
| Direct E83 treated packet | 18,785 tokens, feasible |
| Full repository regression | 280 passed in 299.79 s |
| Injected compatible substitute | none |
| GPU/provider calls | 0 |

## Disposition

```text
event-driven core                         accepted
generic live-seam hardening               accepted provider-free
locked tokenizer behavior                 exactly qualified
historical sparse projection dependency   removed
full locked model restored                yes
live GPU/provider behavior                not exercised
```

The refactored host is now ready for a separately selected and authorized live
qualification or experiment. This result itself makes no behavioral or utility
claim.
