# Trellis bounded candidate causal-history Stage 0

Date: 2026-08-29

## Question

Can the refactored host keep exact mutation custody while preventing already
applied mutation actions and effect bodies from competing indefinitely with the
complete exact current candidate?

## Prospective ownership rule

The host may compact an applied mutation's action/effect pair only after:

1. the effect has crossed a completed model invocation;
2. its exact before/after chain leads to the exact current candidate;
3. the causal assistant entry is the response from the effect's acquired call;
4. its exact action hash is preserved in the lifecycle event; and
5. its exact effect bytes remain in external custody and reopenable.

The newest pending effect and its action remain exact. The bounded current
effect object states delivery and lineage facts and explicitly says semantic
uptake is not inferred.

## Frozen offline donor

Use the sealed E96 V1 checkpoint immediately before its terminal
`capacity_blocked` event. Do not alter or regrade the historical run. Replay
the preceding 143 events, apply the future-only lifecycle, and compare the next
offline packet under the exact locked tokenizer.

## Required gates

- exact donor replay;
- pending/provider-failure protection;
- wrong-current-hash and broken-lineage rejection;
- causal-action hash tamper rejection;
- exact effect reopen;
- checkpoint/event/packet round trip;
- provider-free mutation, effect delivery, verification, repair, recheck, and
  closure on a fresh Trellis fixture;
- Ruff, mypy, focused tests, and full historical regression.

No GPU/provider call is authorized or required.

## Claim limits

Passing Stage 0 proves a host lifecycle is mechanically reachable and bounded.
It does not prove that Qwen understands an effect, that it will choose an
admissible action size, or that a live trajectory will verify and close.
