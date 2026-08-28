# Keystone event-triggered continuation qualitative transcript appendix

Date: 2026-08-27

Run ID: `2026-08-27-keystone-event-triggered-causal-continuation-v0`

Frozen run commit: `c443f39fca414303c6f3b4efdfa94ba0b06a37b7`

Sealed result commit: `d53f68b1df0667df39a66880a982e087b3bcdccb`

## Scope and inference rule

This appendix reconstructs the common continuation at the level relevant to
the program's systems question: what exact and semantic information was
visible, what persisted, how demand changed, and whether evidence became
cumulative work.

The actor emitted only action objects and no reasoning trace. Statements about
why an action was selected are therefore labeled as inferences. Exact action
order, prompt residency, register transitions, candidate hashes, call counts,
and token counts are directly established by the sealed traces.

The run never reached the frozen causal trigger. Nothing in this appendix is
evidence for or against `V1_BOUNDED_CAUSAL_CONTINUITY`. It is qualitative
evidence about the common system that was supposed to create the trigger.

## Corrected whole-run frame

The immutable E79 parent contributed nine actor calls and 102,009 serialized
tokens. The continuation added:

* eight actor calls;
* ten semantic-maintenance calls;
* 198,745 serialized tokens; and
* no treatment-dependent decision.

The corrected pre-treatment total is therefore 27 model calls and 300,754
serialized tokens. The historical embedded summary's `empty_trace` activation
snapshot and actor-only call count are derived-reporting defects; the corrected
audit is authoritative.

## State inherited from E79

The actor inherited:

* the exact fourteen-source catalog;
* exact source observations for MANDATE through FUEL that had crossed actor
  boundaries;
* pending CYBER, which the host had acquired but the actor had not yet seen;
* an empty evidence ledger;
* a ten-word decision placeholder;
* exact incremental ledger and decision-section actions;
* exact reopen handles;
* deterministic first-fit relief; and
* a temporary provenance-bound semantic register maintained whenever a source
  result was externalized.

Before the first new actor decision, common infrastructure externalized
MANDATE and TRACK, ran one maintenance call for each, and delivered CYBER. The
actor therefore began the continuation with receipts for MANDATE and TRACK,
seven exact-resident source bodies from SIGNAL through CYBER, and a two-claim
MANDATE register.

## Maintenance behavior

The maintenance pathway was active, fallible, and expensive. It generated 48
candidate claims across ten calls. Eight claims entered the register and forty
were rejected.

| Maintenance call | Externalized result | Source | Prompt + completion | Proposed | Admitted | Register after | Main disposition |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | RESULT-001 | MANDATE | 2,927 + 656 | 4 | 2 | 2 | Two authority facts admitted; two undeclared relationship references rejected |
| 2 | RESULT-002 | TRACK | 3,029 + 687 | 4 | 0 | 2 | Entire source-slot proposal exceeded its budget |
| 3 | RESULT-003 | SIGNAL | 3,102 + 701 | 4 | 0 | 2 | Entire source-slot proposal exceeded its budget |
| 4 | RESULT-004 | POWER | 3,203 + 799 | 4 | 3 | 5 | Three facts admitted; relationship lacked declared referents |
| 5 | RESULT-005 | ROLLING | 3,164 + 743 | 4 | 0 | 5 | Entire source-slot proposal exceeded its budget |
| 6 | RESULT-006 | CREW | 3,094 + 724 | 4 | 0 | 5 | Entire source-slot proposal exceeded its budget |
| 7 | RESULT-007 | WEATHER | 3,107 + 606 | 4 | 0 | 5 | Four evidence anchors were non-unique in the result |
| 8 | RESULT-008 | FUEL | 3,024 + 718 | 4 | 0 | 5 | Entire source-slot proposal exceeded its budget |
| 9 | RESULT-009 | CYBER | 2,967 + 680 | 4 | 0 | 5 | Entire source-slot proposal exceeded its budget |
| 10 | RESULT-010 | TELEMETRY | 3,022 + 755 | 4 | 3 | 8 | Three facts admitted; relationship reference rejected |

The maintenance layer consumed 37,708 serialized tokens and 10 of the 18 new
model-call slots. Its final register contained:

* two MANDATE authority facts;
* three POWER facts covering installed/usable capacity, voltage gates, and
  backup duration; and
* three TELEMETRY facts covering observation coverage, delivery latency, and
  warning/stop thresholds.

It retained no admitted relationship claim and represented only three of the
fourteen sources. The register was exact-source/version/anchor bound, but no
independent semantic adjudication of all eight retained paraphrases was part
of this run.

### A consequential carrier interaction

Six sources produced four candidate claims whose combined source-slot payload
exceeded the fixed slot budget. Those calls admitted none of their claims.
By contrast, MANDATE, POWER, and TELEMETRY fell below the effective slot budget
only after one or two relationship claims failed separate admission rules.

The register's contents were therefore not selected solely by semantic value.
They were shaped by an interaction among:

```text
model claim count
+ per-claim carrier size
+ source-slot transaction rule
+ referent/anchor validity
→ which source meaning survived
```

This matters to interpretation. The common system did not provide a broad
fourteen-source semantic working state. It provided a sparse carrier-selected
sample while charging a maintenance call for every externalized result.

## Actor call-by-call reconstruction

Result/source mapping is:

```text
001 MANDATE    002 TRACK      003 SIGNAL     004 POWER
005 ROLLING    006 CREW       007 WEATHER    008 FUEL
009 CYBER      010 TELEMETRY  011 LOADS      012 PASSENGER
013 LINEAGE    014 REVIEW     015 MANDATE    016 TRACK
```

| New actor call | Global actor call | Prompt tokens | Exact-resident source bodies before decision | Semantic register before decision | Action | Work-state effect |
|---:|---:|---:|---|---|---|---|
| 1 | 10 | 19,596 | SIGNAL through CYBER (7) | 2 MANDATE facts | Read complete TELEMETRY | No candidate change |
| 2 | 11 | 19,946 | POWER through TELEMETRY (7) | Same 2 facts | Read complete LOADS | No candidate change |
| 3 | 12 | 19,649 | CREW through LOADS (6) | 2 MANDATE + 3 POWER facts | Read complete PASSENGER | No candidate change |
| 4 | 13 | 20,135 | WEATHER through PASSENGER (6) | Same 5 facts | Read complete LINEAGE | No candidate change |
| 5 | 14 | 20,491 | FUEL through LINEAGE (6) | Same 5 facts | Read complete REVIEW | No candidate change |
| 6 | 15 | 20,880 | CYBER through REVIEW (6) | Same 5 facts | Request complete MANDATE + TRACK in one batch | Rejected: 172 lines exceeded the 160-line cap |
| 7 | 16 | 19,388 | TELEMETRY through REVIEW (5) | Same 5 facts | Reread complete MANDATE | No candidate change |
| 8 | 17 | 20,738 | LOADS through REVIEW + new MANDATE (5) | 2 MANDATE + 3 POWER + 3 TELEMETRY facts | Reread complete TRACK | TRACK result acquired but never delivered to a later decision |

Each actor response was tiny: the eight calls used 160,823 prompt tokens and
214 completion tokens. The system spent roughly 752 actor-prompt tokens per
actor-completion token. This is not merely a model-efficiency curiosity. It
shows that almost all serialized information flowed into choosing another
read, while almost none crossed the output boundary as cumulative task work.

## Exact residency and semantic turnover

Ten positive-savings relief events successively externalized RESULT-001
through RESULT-010. Exact-resident source bodies declined from seven at the
first continuation decision to five at the last. Every externalized body
remained exactly reopenable.

The actor did not use `reopen_exact`. After all fourteen sources had been
observed, it requested MANDATE and TRACK again through `read_source`. This
produced new result identities for exact bytes already held externally.

That behavior is best described as reacquisition through the source surface,
not loss of recoverability. The system had preserved the old exact objects and
advertised their handles. The actor nevertheless expressed demand as fresh
source reads.

## Demand transition

The first five continuation actions completed the exact catalog suffix:

```text
TELEMETRY → LOADS → PASSENGER → LINEAGE → REVIEW
```

Together with the parent trace, that is exact catalog-order traversal through
all fourteen sources. It remains confounded with catalog position and should
not be credited as independently optimized semantic priority.

At call 15, all fourteen source bodies had crossed an actor boundary. The next
request returned to the first two catalog sources, MANDATE and TRACK. The
attempted pair was invalid, after which the actor requested them separately.

A plausible inference is that the actor was beginning to reassemble
foundational authority and geometry evidence for synthesis. The traces do not
prove this. What they do prove is that completing source coverage did not
produce a construction action, and that the first post-coverage demand was for
old exact evidence rather than the offered incremental artifact surface.

The two MANDATE facts already present in the register did not satiate MANDATE
demand. TRACK had no retained semantic claims because its maintenance update
was rejected. Thus the post-coverage reads are consistent with a sparse
semantic scaffold being insufficient for action-ready integration.

## Evidence-to-work conversion remained the active failure

The actor had all of the following available across the trajectory:

* every exact source at least once;
* exact receipts and reopen actions for externalized sources;
* a bounded provenance register;
* an exact evidence ledger;
* section-level decision updates;
* whole-artifact replacement;
* verification transition and check actions; and
* deterministic capacity relief.

Yet the exact candidate remained byte-identical:

```text
# Keystone Evidence and Decision Matrix

No evidence has yet been integrated.

# Keystone Regional Rail Restoration Decision

Construction has not yet begun.
```

The common configuration preserved STATE and kept evidence ingress alive, but
did not convert observed evidence into durable RELATIONSHIPS or task work. Its
temporary semantic path was too sparse to constitute a broad integrated state,
and its exact artifact path was never used.

The observed pipeline was:

```text
exact source observation
→ pressure relief
→ paid maintenance attempt
→ often zero semantic admission
→ another actor read
→ exact source turnover
```

The missing transition remained:

```text
observed evidence
→ source relationships / requirement binding
→ incremental exact ledger or section
→ current candidate
```

## Call-budget interaction

The frozen common budget was eighteen model calls, not eighteen actor calls.
Ten maintenance invocations left eight actor decisions. This was prospectively
valid and all maintenance cost was correctly charged. It also exposes a real
systems tradeoff:

```text
maintain semantic residue more often
→ fewer actor decisions within a fixed provider-call envelope
```

In this run, the maintenance layer generated substantially more output than
the actor—7,069 versus 214 completion tokens—but admitted only eight persistent
claims and induced no artifact mutation. It cannot be treated as free
background cognition.

## Why the causal experiment did not activate

The trigger correctly required a nontrivial candidate, verification, a current
candidate-bound check, a rejected mutation, an unchanged candidate, and a
later observation. None of the first three prerequisites occurred.

This is a positive result for routing discipline: pressure, source breadth,
reacquisition, or elapsed calls did not falsely activate a causal treatment.
It is simultaneously a negative result for Keystone as a donor: the common
system could not generate the lifecycle state needed to ask the V0/V1 question
within 27 model calls and 300,754 pre-treatment tokens.

The absence of a fork is therefore scientifically meaningful nonactivation,
not missing data and not a reason to lower the trigger.

## System-level conclusions

Supported locally:

* first-fit relief continued to preserve physical operability;
* all fourteen exact sources became model-visible;
* exact custody and reopenability survived repeated turnover;
* fallible maintenance preserved prior accepted state;
* the event trigger did not activate on an ineligible trajectory; and
* source completion alone did not cause construction.

Also observed:

* the semantic carrier admitted 8 of 48 proposed claims and no relationships;
* ten maintenance calls consumed more common call slots than eight actor calls;
* post-coverage demand returned to foundational exact sources;
* one invalid batch request consumed an actor decision;
* the actor used fresh reads rather than exact reopen handles; and
* neither semantic residue nor incremental affordances produced durable work.

Not supported:

* that the actor lacked semantic understanding;
* that more continuation would necessarily produce construction;
* that the register caused or prevented the rereads;
* that V1 causal continuity helps or harms repair;
* that a different register budget or maintenance prompt would fix Keystone;
  or
* that the same world should be continued or retried.

## Final qualitative disposition

Keystone is not merely a causal-treatment no-show. It is a complete example of
a costly pre-treatment information regime in which exact evidence, mechanical
relief, semantic maintenance, and incremental artifact affordances interacted
without producing cumulative work.

The trigger did its job by refusing to convert that upstream failure into a
spurious causal-continuity comparison. Under the frozen rule, the route is
closed. The program should retain the donor as evidence that exact availability
plus sparse paid semantic residue is not sufficient for evidence-to-work
conversion, not tune the threshold or manufacture the missing repair state.
