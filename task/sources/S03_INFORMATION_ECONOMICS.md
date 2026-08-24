# Systems model for bounded information economics

Date: 2026-08-24

Status: program-level research frame; not a promoted runtime architecture

## Why this frame is needed

Bounded context is not a stationary storage-allocation problem. The value of a
resident object depends on the current task phase, candidate state, other
resident objects, recent actions, available tools, remaining capacity, and the
actor's next decision. An intervention changes the actor's behavior; that
behavior changes future information demand, residency, cache reuse, and
pressure. Costs and values are therefore path-dependent and partly endogenous.

The program has not demonstrated mathematical chaos, and should not claim it.
It has demonstrated seed sensitivity, failure migration, feedback, changing
bottlenecks, working-set churn, and stage-dependent representation value. The
appropriate working description is an adaptive, non-stationary,
path-dependent system with endogenous feedback.

Systems thinking does not replace narrow causal experiments. It prevents a
locally clean experiment from optimizing the wrong layer or treating a
component's isolated score as a context-independent property.

## Dynamic state

At model decision `t`, record a state vector conceptually containing:

- authoritative task and current candidate/world identity;
- exact resident objects and their sizes/versions;
- resident semantic derivatives and known loss records;
- exact externally available objects and reopen handles;
- recent observations, admitted effects, and unresolved results;
- chronology/control representation;
- prompt occupancy, response reserve, and protected control headroom;
- task phase or operational regime, when mechanically declared;
- calls, latency, cache state, and remaining authorization; and
- observed actor demand, including novel reads, reopens, mutations, and review.

The value of object `o` is conditional:

```text
value(o, t | current state, co-resident set, task regime)
```

not an intrinsic permanent score. An old object may still be part of the active
working set. A newly produced digest may be valuable only after the raw source
leaves residency. A structural outline may be useful during acquisition and
expensive during construction. A missing exact detail may be harmless until a
review or mutation makes it decisive.

## Transition and feedback

Each host or model operation changes the next state:

```text
current bounded state
    -> host representation/maintenance operation
    -> model decision
    -> admitted action or observation
    -> new exact and semantic demand
    -> changed residency, capacity, cache, and task state
```

Important feedback loops already observed include:

- demotion frees capacity, the actor reopens information, and capacity fills;
- history grows, useful exact evidence loses co-residency, and reopening churn
  increases;
- exact reentry removes history, changes orientation, and can create a mutation
  opportunity;
- optional management controls consume prompt space but may not activate before
  the control surface becomes unreachable; and
- semantic compression lowers resident cost while introducing task-dependent
  loss that may or may not cause later exact recovery.

## Information-economic objective

The objective is not minimum resident tokens, maximum eviction, perfect digest
recall, or zero reopening. It is cumulative useful work under bounded resources
and acceptable risk.

A conceptual accounting objective is:

```text
maximize cumulative task progress and artifact quality

subject to:
    hard context, response, and control reserves
    exact custody and version integrity
    bounded calls and retries
    acceptable semantic error and recovery

while accounting for:
    resident token cost
    semantic-derivative production cost
    exact reopen/fault-in cost
    cache invalidation and prefill latency
    maintenance/control cost
    action opportunity cost
    downstream error and repair cost
```

No scalar weights are currently earned. Report the cost vector and behavior
separately rather than inventing one aggregate score. A later decision analysis
may compare Pareto-dominant policies only where outcome quality is commensurate.

The context window is only one throughput constraint. The latest pressure
trajectory makes the broader bottleneck structure explicit:

```text
useful task throughput
= minimum of:
    discovery and acquisition bandwidth
    relationship-formation bandwidth
    relation-to-action binding
    action organization and legal expression
    model-facing exact/semantic residency
    durable work-product externalization
    effect uptake
    feedback discrimination and repair
    review and closure bandwidth
```

Increasing one term moves the active bottleneck. In E36, first-fit relief
removed prompt overflow as the terminal resource; one-read/one-action ingress,
whole-artifact mutation, absent partial-work residue, and the decision horizon
then jointly prevented later functions from becoming observable. This is a
configuration result, not a claim that any one term caused nonconstruction.

## Stock, flow, and complementarity

Do not judge an information object by resident size alone. For each treatment,
separate at least four economic quantities:

- **resident stock cost:** tokens occupied at the current decision boundary;
- **production/acquisition flow cost:** calls, tokens, and latency used to create
  or obtain the object;
- **maintenance/switching flow cost:** rewriting, recomposition, cache loss, and
  control work needed to keep using it; and
- **recovery flow cost:** later exact fault-in, repeated access, repair, or delay
  caused by information that is absent or lossy.

Also record **conversion yield** without treating it as one scalar score:

- exact bytes observed over time;
- distinct relationships or qualifications externally represented;
- relationships or source bindings retained across replacement versions;
- exact partial task-work versions admitted and later reused;
- admitted artifact work;
- current effects taken up;
- evaluator requirements satisfied; and
- decisions spent at each transition.

Large evidence flow with zero artifact flow may be rational while mandatory
evidence is incomplete. It is nevertheless a different operating regime from
cumulative construction and should be visible in the accounting.

For any semantic derivative, decompose resident stock into:

```text
semantic payload
+ identity / provenance / version binding
+ exact-recovery metadata
+ message / role / serialization / template overhead
= actual prompt increment
```

Report `payload_tokens / actual_prompt_increment` as a descriptive
payload/package ratio. Do not call it semantic efficiency or optimize it alone:
non-payload carrier tokens may provide necessary custody, safety, and recovery
value. Causal claims apply to the complete inserted package unless payload,
metadata, role, recency, and serialization are separately varied.

The value of an object may also depend on another resident carrier. Before
calling an omitted fact redundant, bind it to the exact co-resident object that
purportedly supplies the same proposition and verify scope, provenance, version,
and temporal meaning. A current-candidate fact is not automatically equivalent
to a fact about a candidate in an older source study. Complementarity is an
investigator-side audit unless the treatment prospectively changes what the
actor sees.

## Regimes and phase dependence

At minimum, distinguish these operational regimes when they are mechanically
observable or frozen by design:

1. **Navigation/acquisition:** structural addressability and exact fault-in may
   have high value.
2. **Pressure response:** minimum-necessary capacity relief and protected
   control bandwidth dominate.
3. **Construction/effect uptake:** current candidate state, governing evidence,
   and recent effects may dominate old acquisition chronology.
4. **Review/closure:** exact qualifications, check results, candidate identity,
   and unresolved defects may regain value.

Do not infer a phase from vague model behavior. Experiments may freeze a phase
boundary from exact events or compare policies at an authentic pressure state.

## Hard invariants versus economic variables

### Hard disqualification

These protect custody, recoverability, and a usable control plane:

- wrong object, source, candidate, or version binding;
- fabricated exact identity;
- contradiction or material causal reversal presented as source truth;
- semantic derivative presented as authoritative exact state;
- unavailable or invalid exact reopen path;
- violation of context, response, or protected control reserve;
- unbounded representation growth;
- unauthorized call, retry, mutation, or post-outcome treatment change; and
- apparatus/runtime/replay failure.

### Measured loss and cost

These may be harmful, harmless, or useful depending on configuration and time;
record them rather than automatically censoring behavior:

- omitted source detail or count;
- delayed or immediate exact reopen;
- subordinate qualification loss without contradiction;
- digest production cost;
- cache/prefill disruption;
- working-set turnover;
- additional acquisition;
- altered action timing; and
- repair or artifact-quality changes.

An omission becomes a hard failure only when the treatment claims exactness,
creates a contradiction/material reversal, makes recovery impossible, or the
experiment prospectively defines that detail as safety-critical for the tested
operation.

## Experimental consequences

In confirmation, isolate one policy or representation change where possible.
In discovery, a compound arrangement is allowed when it is the simplest
authentic situation that exposes a capability; the supported claim is then
descriptive and applies to the complete arrangement rather than an isolated
mechanism. Both tiers must declare:

- the dynamic state and regime where the change occurs;
- why the object's marginal value or cost may differ there;
- the feedback horizon observed after the change;
- which costs are one-time, resident, recurrent, or switching costs;
- the known semantic-loss vector;
- the exact recovery path;
- immediate and cumulative outcomes; and
- the boundary conditions under which the result might reverse.

Use this marginal-boundary record:

```text
BOUNDARY STATE
MARGINAL INTERVENTION
CO-RESIDENT COMPLEMENTS OR SUBSTITUTES
IMMEDIATE PRICE: resident / production / maintenance / recovery
STATE TRANSITION
FUTURE INFORMATION DEMAND
DOWNSTREAM VALUE AND QUALITY
FAILURE MIGRATION
```

A changed valid action is an observation, not automatically a benefit. A local
utility lead requires useful progress, economically meaningful demand deferral,
or selective recovery with no material quality loss. Merely replacing one
duplicate read with another does not qualify.

Prefer one clean primary decision plus a short predeclared continuation when
feedback is the research question. Do not use an arbitrarily long rollout to
hide an ambiguous first effect, and do not use a one-turn test when the claimed
mechanism is amortization, recovery, or lifecycle stability.

## Provisional function inventory—not a stack

The evidence motivates investigation of these functions, but does not establish
that they should be permanent layers, separate calls, named roles, or one
pipeline:

```text
exact custody and current-world binding
information discovery and selection
relationship and qualification assembly
bounded working-state formation
substantive action and work-product externalization
effect uptake, feedback, repair, and closure
```

The existing mechanical baseline can carry exact candidate/version/effect/check
facts where the host can establish them. Whether semantic continuity is best
carried by ordinary history, selected exact evidence, a model-authored
derivative, partial work product, bounded subtask, fresh reviewer, or another
arrangement remains open. The function labels are an observational lens, not a
fixed four-field prompt or complete context manager.

## Recent systems-frame experiments

S3 tested the sealed 218-token seed-314159 digest without reclassifying its
failed 6/6 gate. The known omissions remained treatment metadata, exact reopen
remained available, and the full production cost was charged.

The source-bound digest package changed the first information-demand event but
did not lower total recovery cost: Qwen3.8 first reopened a paired audit from
the same study, then made the exact historical whole-source reopen one call
later. The package added 720 resident prompt tokens: 218 semantic payload tokens
and 502 carrier/template tokens, a 30.3% payload/package ratio. The two actor
calls consumed 41,036 serialized tokens, and no mutation or candidate change
occurred. Thus package-level behavioral influence and economic value separated
cleanly in this regime. The experiment does not isolate semantic prose from
metadata, role, recency, or serialization.

This result reinforces the non-stationary frame: a representation package can
be accurate enough to affect behavior yet have negative local marginal value
once co-residency, carrier cost, exact recovery, and downstream work are
counted. In this configuration it behaved as an economic complement to exact
evidence rather than a substitute. That describes the observed demand and cost
sequence, not why the actor chose it. The result does not determine the value
of other digests, sources, phases, or longer reuse horizons.

H05 then tested a different economic role: spend bounded resident capacity on a
model-authored control/closure state while exact evidence remains stable. The
byte-identical control reproduced a resident-focus reread. A 169-token state in
a 464-token complete package changed the treated action to immediate admitted
submission. Exact-hash reconciliation later established that the unchanged
candidate was a known strong partial, not a complete artifact.

This is negative local trajectory utility despite strong behavioral influence.
It exchanged 464 resident prompt tokens plus 18,915 serialized production
tokens for premature closure without artifact improvement. The outcome exposes
a false-closure liability that the original coarse post-run review missed.

The package-level causal limit is decisive. Semantic prose, exact bindings,
authority notice, user-message role, recency, and carrier serialization moved
together. The state explicitly framed submission-if-ready as a next progress
event. The experiment therefore cannot distinguish durable semantic continuity
from a recent self-authored closure cue. It failed readiness discrimination at
this defect-bearing boundary and does not establish a useful local control
effect or general progress-state mechanism.

Together S3 and H05 show why information economics cannot rank representation
families by behavioral salience. One semantically faithful package increased
exact demand and cost; another bounded package consumed capacity and caused
premature closure. Value depends on the operational regime, co-resident exact
state, induced demand, artifact quality, and whether the resulting action is
actually appropriate.

H05 also adds a measurement invariant: candidate readiness must be adjudicated
independently and hash-bound before a semantic control treatment is scored.
Otherwise a strong action contrast can be mistaken for useful progress.

The subsequent no-GPU consistency audit generalized that invariant. Artifact
identity, task version, rubric/evaluator, and evidence coverage form the
economic accounting key. A lower-cost terminal action is not a benefit when an
unreconciled or coarser disposition has mislabeled the artifact. Corrections
remain in the ledger as explicit supersessions so that attractive historical
claims cannot silently become active again.

The hardened form makes the accounting key exact: candidate/tree and artifact
file hashes, task hash, evaluation-basis hash or explicit unavailability, and
evidence-manifest hash. Within one basis, economic outcome comparison uses the
full score, criterion findings, explicit closure readiness, and blockers—not
only a top-level quality label. It also records semantic provenance: an
inherited judgment and a reconciliation of the same direct review improve
custody but do not constitute independent confirmations.

This implies a third durable external ledger alongside purpose and world
custody:

```text
WORLD LEDGER
exact objects, versions, actions, effects, chronology

PURPOSE LEDGER
authorized task, success contract, operating limits

EVALUATION LEDGER
candidate/task/rubric/evidence-bound judgments,
readiness, blockers, provenance, and supersession
```

The evaluation ledger is governance for investigator claims, not an
automatically resident actor representation and not authoritative world truth.
Its role is to prevent an information intervention from appearing valuable
merely because a stale or coarse artifact judgment labeled its endpoint ready.

## Cross-program routing is part of the economics

The next-route audit exposed another cost category: redundant experimentation.
A proposed submission-readiness reflection and its bounded-phase fallback both
appeared open when only the recent standalone sequence was considered. Pinned
older evidence already contained four complete-audit false-closure studies,
model-authored review, phase-state scout and replication, a three-phase
longitudinal comparison, and reserved exact handoffs.

Those studies do not make every successor ineligible. They change the prior and
the required contrast:

- another readiness message must beat known exact-verification and reviewer-
  uptake/defect-recall boundaries;
- another phase experiment must address automatic boundary choice,
  integration, or a new pressure rather than merely show that fresh reentry can
  work; and
- another reserved maintenance pass must test a new allocation operation, not
  simply prove that the control turn can be reached.

The research system therefore needs a cross-study episode ledger, not only an
experiment index. Value is configuration-dependent, and experiment novelty is
also configuration-dependent. Trigger, regime, owner, resident set, feedback
horizon, and downstream artifact effect determine whether two differently named
studies are actually distinct.

## Cross-study episode result

The first ledger materializes 29 boundary × condition episodes from 12 pinned
Git objects. It confirms a systems hierarchy rather than a global mechanism
ranking:

1. Host mechanical custody and pressure relief are reliable safety operations.
2. Exact recoverability does not imply stable semantic co-residency.
3. Semantic packages can redirect demand or closure policy while having
   negative marginal utility.
4. Fresh-world phase reentry can save tokens in one domain and increase calls,
   cost, or failure in another.
5. Exact verification can buy real repair, but production cost and actor uptake
   remain separate constraints.

The next unresolved allocation question is therefore about ownership and
control-plane reachability: when a pending exact result creates real pressure,
can a dedicated maintenance-only model invocation select a useful exact
working set under a hard budget better than the host's incumbent mechanical
rule? The host must reserve enough capacity for that control operation; the
model may express semantic retention preference but cannot own hard-overflow
safety.

## Allocation-question resolution and program phase

The dedicated study answered that routing question locally. Guaranteed
headroom made the control operation reachable and both managers returned
feasible release sets. They nevertheless removed 6,527 and 6,956 prompt tokens
for deficits of only 394 and 1,045, preserved 0/2 incumbent next decisions, and
caused 2/2 immediate requests for the released source.

The result separates three properties:

```text
control-plane reachability    passed
mechanical feasibility        passed
next-decision workspace value failed locally
```

It also exposes cross-mode instability: the maintenance role's prediction of
future value was contradicted by the ordinary actor one decision later. This
does not prove that every constrained or persistent model-managed cache policy
must fail. It is enough to reject open-ended model-owned eviction as the
current routing default.

The systems ownership split is therefore firmer:

- the host owns exact custody, accounting, response/control reserves,
  prospectively positive-savings relief, reversible receipt substitution, and
  phase/reentry mechanics;
- the actor reveals information demand through ordinary reads and reopens and
  owns task interpretation and work; and
- optional semantic investments require an observed state-specific benefit and
  cannot self-authorize artifact readiness.

## Whole-method scout result: activation is endogenous

The first fresh-task system scout did not exercise its pressure mechanism.
Complete accessible worlds were 44.5K and 59.2K prompt tokens, yet ordinary
actor demand materialized prompts no larger than 9,948 tokens. The intervention
that actually fired was scheduled reentry at fixed call boundaries.

This exposes another information-economics distinction:

```text
available information supply
!= information the actor chooses to acquire
!= resident prompt occupancy
!= authentic pressure on the next result
```

World size is a supply-side property. Policy activation is an endogenous
trajectory property jointly determined by requests, result sizes, chronology,
mutations/effects, protocol failures, and the decision horizon.

Scheduled low-occupancy reentry had negative option value in this configuration:
it solved no pressure, destroyed reusable prefix cache, and sometimes weakened
the binding between a stale check and a newer candidate effect. Reentry should
therefore be priced as a switching operation and triggered only by a pressure
or external authority transition that justifies that price.

The UUID replay incident adds a further representation split. Exact raw event
custody is required, but model-visible diagnostics need not reproduce volatile
transport details. A prospectively frozen projection can retain stable
criterion status, candidate binding, readiness, and a raw handle while exact
UUID/time/path bytes remain external. This is deterministic materialization,
not semantic repair.

## Pressure-qualified streaming result

The later Ceiba scout activated authentic prospective overflow and therefore
separated pressure mechanics from scheduled phase policy. Deterministic
first-fit relief repeatedly kept the trajectory feasible: each 18-call
continuation resolved ten later pressure events through sixteen substitutions
and 80,497 cumulative recovered prompt tokens.

The actor did not enter the earlier reopen-thrashing regime. It made sixteen
novel source reads and two over-range requests, with no reopen, mutation, check,
or submission. Across the visible 18 result records, 322,887 exact result-record
bytes crossed model boundaries; the underlying source slices totaled 312,865
bytes. At most three full source bodies were exact-resident together, and a body
later demoted remained resident for only one to four continuation decisions.
Identity and recovery survived in receipts; no content-bearing model-authored
semantic derivative or partial work product survived with them.

This configuration was physically stable and cognitively underdetermined. The
actor-call budget ended before mandatory S12 and S14 evidence, construction,
effect uptake, verification, and closure could all occur. No reopen during
acquisition does not establish semantic continuity, and no mutation before
evidence completion does not establish acquisition-stopping failure.

The systems result is therefore a throughput decomposition:

```text
useful bounded work is limited jointly by
    information acquisition bandwidth
    model-facing residency
    relationship/integration bandwidth
    decision/action bandwidth
    work-product externalization
    effect uptake
    verification and closure
```

Increasing context operability can move the terminal resource to decisions or
integration without improving the artifact. Receipt-only relief remains a
useful mechanical baseline; it is not the active architecture hypothesis.

## Pressure-active interaction result: interpretation without task-work conversion

E40 made more than one information function live in the same authentic
pressure loop. It crossed one-range versus actor-selected bounded batch ingress
with whole-final-only versus a bounded replacement evidence-integration state.
Across 98 actor and 40 maintenance calls, batching and semantic work both
activated. Every candidate nevertheless remained the initial nine-word stub.

The economic interactions were directional rather than additive:

```text
batch ingress
    raised evidence per admitted actor decision
    and raised exact-result size and reentry demand

bounded semantic work
    externalized genuine cross-source interpretation
    and incurred 339,354 serialized maintenance tokens
    and lost earlier citation breadth under replacement

whole-final artifact surface
    left construction as one large indivisible action

joint outcome
    evidence flow > 0
    semantic flow > 0
    exact task-artifact flow = 0
```

This refines the stock/flow model. A semantic derivative can have high
production and resident value at one decision yet low **retention yield** over
successive rewrites. A provenance allowlist can grow while the derivative's
substantive relationships contract. Metadata stock and semantic stock must
therefore be accounted separately.

It also distinguishes **semantic externalization** from **work-product
externalization**. The E40 object was lossy and non-authoritative. It did not
create exact partial charter sections, admitted candidate effects, or a
version-current feedback target. The information economy paid to interpret
evidence but did not create a transaction through which that interpretation
could become cumulative, checkable work.

The strongest diagnostic cell exposed all 14 sources and carried a 550-word
semantic record, then acquired exact reopens instead of mutating. This does not
show that interpretation was absent. It shows that evidence breadth, semantic
state, artifact action granularity, and feedback must be analyzed as a coupled
conversion pipeline.

The run also tightened the mechanical accounting law. One tiny I1 exact body
became a receipt that cost 79 more prompt tokens. Custody alone does not make an
object economically demotable. Relief eligibility must be determined from the
prospectively rendered packet and require strictly positive savings.

The next interaction question is consequently not another sidecar format or
batch cap. It is whether semantic integration has positive downstream value
when bound to an exact, incrementally revisable task artifact with source and
requirement provenance, current effects, and partial feedback—while ingress,
pressure, recovery, repair, readiness, and closure remain live. That is a
complete-system question about conversion and feedback, not a component score.

## Low-pressure reconnaissance correction

E37 then sampled multiple tasks while every prompt remained far below the
pressure ceiling. It exposed action-expression failures and two
strong-partial/false-closure paths, but pressure relief, semantic persistence,
and incremental work did not co-activate. Those observations describe a useful
low-pressure reference regime. They do not adjudicate the system interaction
that motivated the research-phase shift.

This distinction is essential:

```text
heterogeneous component outcomes
!=
evidence about interaction among information functions
```

An interaction result requires multiple viable configurations in which the
relevant functions operate in the same feedback loop and are followed through
induced demand, artifact state, effects, feedback, and closure. The program
must not convert each observed boundary into its own successor queue.

## Research-allocation economics

Experiments consume option value as well as tokens. Repeatedly refining one
boundary can produce excellent local knowledge while leaving the task/world and
functional coverage too narrow to choose an architecture. Apparatus investment
also has switching cost: every new schema, role, state object, router, or
promotion ladder makes later lateral exploration more expensive and encourages
the program to defend the representation it already built.

The allocation policy is now:

- use small interaction scouts to compare viable whole configurations in
  materially different operating regimes;
- code multiple capability boundaries inside each trajectory rather than
  assigning one experiment to every label;
- require at least two co-active information functions and a shared downstream
  outcome before calling a study an interaction probe;
- preserve exact validity controls while keeping solution-specific apparatus
  minimal;
- treat a valid negative as information and move laterally unless the question
  was obscured by a validity-dominating apparatus defect;
- require a consequential functional endpoint to recur in at least two
  independent worlds before expensive optimization or architecture promotion;
- do not count seeds or packet variants from one donor as independent
  recurrence; and
- stop for owner review when evidence changes the conceptual map rather than
  automatically manufacturing a successor.

A cheap controlled contrast may still be a discovery probe before recurrence.
Its claim remains local. One or two calls are appropriate only for immediate
effects; demand, effect uptake, repair, amortization, and lifecycle claims need
the shortest horizon that can actually expose them.

`STRUCTURED_EXPLORATION_ROADMAP.md` and
`SYSTEM_INTERACTION_EXPLORATION.md` govern the active phase. The intended
product is evidence about substitution, complementarity, interference, and
failure migration among bounded-work configurations—not a polished context
runtime or a ranking of isolated components.
