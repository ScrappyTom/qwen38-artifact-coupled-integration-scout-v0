# Trellis E97 verification-lifecycle scout result

Date: 2026-08-29

Frozen apparatus commit:
`520d8237e42e313fb014ad146aefb4c51feb8a3e`

Run:
`2026-08-29-trellis-e97-verification-lifecycle-scout-v0`

## Outcome

The run stopped safely after four live actor calls, before the mandatory six-
call review point, because the next request required 23,811 prompt tokens
against the 20,992-token allowance. The runtime released cleanly and the run
seal verifies.

This is not a clean negative for the intended verification lifecycle. The live
trajectory exposed an actor-facing apparatus omission that the provider-free
fixture had not tested: after `begin_verification`, the request still contained
only the construction action contract. It declared no `run_check`, bounded
repair, recheck, or submit action.

## What crossed successfully

E97 did create a real opportunity. The first live packet fit at 19,128 tokens,
delivered pending `RESULT-018`, and exposed the exact current candidate and
effect state. Qwen remained oriented and added the missing sixth decision
section through a bounded `upsert_decision_section` action. The resulting
effect crossed the next call, and Qwen then selected `begin_verification`.

The candidate changed from 904 to 1,145 words and gained the exact sixth
heading. It remained `not_ready`: only eight decision sources were cited, all
eight substantive relation groups still failed, and no current check, repair,
recheck, or submission occurred.

## Where the route failed

Call 21 received the exact verification-phase effect and a current verification
frame with `check_binding: null`. It did not receive a declared verification
action surface. Qwen improvised an undeclared `replace_artifact_section`
response containing the entire document rather than a bounded section. The
generation repeated the final heading six times and exhausted all 4,096
completion tokens, so the host rejected it without mutation.

Call 22 received a compact rejection notice, but the complete 18,963-character
rejected assistant output also remained in chronology. Qwen reproduced all
18,963 prior characters byte-for-byte and continued for six more characters
before again exhausting 4,096 tokens. That second output was also rejected.

The prospective call-23 packet then measured 23,811 tokens. No source or old
applied-effect body could solve this because the new burden was two full,
unadmitted assistant responses plus their rejection observations. The host
stopped before provider I/O.

## Accounting

- actor/provider calls: 4;
- maintenance calls: 0;
- prompt tokens: 74,069;
- completion tokens: 8,577;
- additional serialized tokens: 82,646;
- cumulative provider calls including the donor: 33;
- cumulative serialized tokens including the donor: 433,156;
- attempts per call: 1;
- retries: 0.

## Interpretation

The experiment produced two useful findings.

First, E97's bounded applied-history mechanism worked live far enough to carry
the pending effect into a coherent new construction action and then enter the
verification phase. That is a narrow local positive for lifecycle reachability,
not completion utility.

Second, the next failure is jointly an interface and chronology-lifecycle
failure:

```text
verification phase entered
        +
no actor-visible verification action contract
        ↓
model improvises oversized undeclared repair
        +
full rejected output remains resident beside rejection receipt
        ↓
exact recurrence on the next call
        ↓
capacity blocked before any current check
```

The model's two oversized responses are real behavior, but they cannot support
a conclusion about using candidate-bound verification feedback because no such
feedback was generated or exposed. Provider-free Stage 0 overclaimed interface
reachability by invoking verification and repair actions directly rather than
rendering the exact messages a live actor would receive.

## Disposition

The sealed v0 route is closed as **live apparatus-censored with narrow local
effect-uptake and phase-entry positives**. It must not be resumed under changed
code.

A repaired v1 requires:

1. an explicit actor-visible verification contract after phase entry;
2. provider-free assertions that every scripted action is actually declared in
   the corresponding actor request;
3. exact external custody but compact model-facing representation of rejected
   assistant bodies after rejection, because they caused no world transition;
4. a new run ID, clean frozen commit, and separate GPU authorization.

No successor GPU run is authorized.
