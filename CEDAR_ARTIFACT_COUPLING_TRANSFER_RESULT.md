# Cedar artifact-coupling transfer result

Run ID: `2026-08-25-cedar-artifact-coupling-transfer-measured-v0`

Authorized freeze:
`f1610d1bf90b5847dbdbe0d981f4b1676abf4279`

Disposition: **local A1 artifact-quality advantage without useful completion**.
The coupled configuration produced substantially broader exact work than the
detached configuration at nearly equal serialized-token cost. Neither
configuration was ready, submitted, or usefully complete. This is a
configuration-level interaction result in one fresh task and one seed; it does
not isolate artifact coupling or promote an architecture.

## Run validity and custody

The frozen runner executed `D0_DETACHED` and then `A1_COUPLED`, as authorized.
It made 38 actor calls and 36 maintenance calls, for 74 provider calls and
1,026,000 serialized tokens. Every provider call used one attempt and zero
retries. Both cells and the aggregate were sealed, both fresh model servers
were released, and the aggregate audit passes.

The post-run audit initially reported three failures. Two came from an obsolete
hard-coded candidate hash inherited from the earlier task. The third assumed
that every positive externalization must have a maintenance call, although the
frozen runtime permits one final result to be externalized immediately before
the maintenance-call ceiling stops the cell. The original failed audit is
preserved in `CEDAR_MEASURED_INTERACTION_AUDIT_V0_FAILURE.json`. The repaired
auditor now derives the boundary hash from the Cedar handoff and accepts a
single ordered terminal unmatched externalization only when the sealed terminal
state and exact budget prove that case. Both cells ended with that same
unmaintained `RESULT-023` and now pass the corrected invariant.

This was an auditor defect, not a runner or model-result repair. No provider
call was repeated and no sealed trajectory byte was changed.

## Literal comparison

| Measure | `D0_DETACHED` | `A1_COUPLED` |
|---|---:|---:|
| Actor calls | 19 | 19 |
| Maintenance calls | 18 | 18 |
| Provider calls | 37 | 37 |
| Serialized tokens | 515,435 | 510,565 |
| Wall time | 1,916.9 s | 1,988.2 s |
| Final prompt tokens | 21,019 | 20,198 |
| Accepted integration updates | 5 | 5 |
| Positive externalizations | 19 | 19 |
| Exact reopens | 0 | 0 |
| Reactive reentries | 1 | 1 |
| Candidate effects | 3 | 8 |
| Candidate effects delivered | 3 | 7 |
| Checks | 1 | 1 |
| Submitted | No | No |
| Terminal state | Maintenance budget exhausted | Maintenance budget exhausted |

Both configurations received the same pressure fork, ingress and maintenance
operations, budgets, tools, and evaluator. Their first nine actor actions were
identical. The first behavioral divergence occurred on actor call 10: A1 read
S14–S15, while D0 read S15–S16. A1 then read S16–S01 and constructed its
ledger on call 12; D0 constructed its ledger on call 11. Both constructed a
decision, ran one candidate-bound check, repaired, and resumed targeted source
acquisition. A1 made a second final decision repair. Neither had budget for a
current recheck and appropriate closure.

The detached arm made 15 batch reads, one ledger replacement, two decision
replacements, and one check. The coupled arm made 11 batch reads, three
single-source reads, one ledger replacement, three decision replacements, and
one check. Thus the treatment did not merely change the location of a note. It
changed the subsequent mix of ingress, exact candidate effects, repair, and
work-product state.

## Candidate-bound outcome

The independent semantic record binds the exact task, protocol, candidate
files, mechanical evaluations, aggregate result, and run seal. It used neutral
candidate labels until the comparative disposition was recorded.

### D0 detached

Candidate `69ac7847bd638abfb4c3ca3429c162abd4af0f684562942528e3059b6f50a28f`
was adjudicated `weak_partial`:

- 0 of 12 semantic criteria met, 9 partial, and 3 not met;
- 952 decision words;
- 9 distinct decision sources and 7 ledger sources;
- five mechanical requirement groups remained blocking;
- R05 fleet/driver operations, R08 fuel continuity, and R09 animal logistics
  were not met;
- no current final actor-visible check and no submission.

The package contained useful fragments but remained sparse and sometimes
incorrect. It collapsed source-defined authority roles, used the 17-hour
exercise fuel arrival instead of the governing 19-hour outage delay, and did
not supply operationally adequate transport, fuel, animal, or closure state.

### A1 coupled

Candidate `35d113e9dfc29e515ffd7e8dad9c52444aef06f4f3a4b353e80adfefc70a2323`
was adjudicated `strong_partial`:

- 1 of 12 semantic criteria met and 11 partial;
- 1,290 decision words;
- 15 distinct decision sources and 12 ledger sources;
- all required source IDs present;
- 16 of 17 mechanical gates passed, with only the 1,500-word minimum failing;
- no current final actor-visible check, no submission, and the final candidate
  effect did not cross another actor decision boundary.

The broader artifact was not semantically safe. It converted a 5.8-hour fire
arrival estimate into a 5.8 km/h wind threshold, converted a 42 percent
wind-shift probability into 42 percent relative humidity, and converted 91
percent survey coverage into a 19 percent uncertainty allowance associated
with tourists or Zone C. It also treated a required common revision binding as
a permitted count. These are material source contradictions, not cosmetic
qualification loss.

Therefore A1's stronger breadth and structure do not establish readiness. The
correct primary result remains:

```text
D0 detached  -> weak partial -> not ready -> no useful completion
A1 coupled   -> strong partial -> not ready -> no useful completion
```

## What the interaction tells us

### Exact work can carry useful integration forward

A1 is the first fresh-task transfer signal that routing bounded integration
through exact revisable candidate state can improve the eventual work product
relative to a detached sidecar under the same pressure substrate. Its artifact
covered more sources, more requirements, and more operational detail. After
the check, its actor made targeted reads of S05, S07, and S11 and repaired the
decision again. The work product therefore participated in later acquisition
and repair rather than serving only as an endpoint.

This supports a narrow systems hypothesis: exact artifact state can be a
durable channel for cumulative cognition when evidence bodies rotate out of
residency.

### Coupling does not guarantee correct integration

The same path also preserved or amplified incorrect relationships. Candidate
exactness guarantees custody and revisability, not semantic truth. Because A1
made more candidate changes, it also created more effect-uptake and
current-verification obligations. Seven of eight effects crossed another actor
boundary; the final one did not.

The live interaction is therefore:

```text
semantic maintenance
        +
exact candidate coupling
        -> broader persistent work
        -> different later evidence demand and repair
        -> more candidate effects/currentness obligations
        -> better partial artifact
        -> material source contradictions still remain
```

### The maintenance channel became a shared bottleneck

Only 5 of 18 maintenance calls qualified in each configuration. Thirteen in
each arm exceeded the frozen bounded-expression budget. The rejected outputs
still consumed provider calls, prompt/completion tokens, and wall time but
created no accepted semantic update. Both trajectories stopped when the 18-call
maintenance budget was exhausted, immediately after a nineteenth positive
externalization.

This is not merely a component-format nuisance. Under the frozen interaction,
every externalization synchronously demanded maintenance. A low-yield
maintenance channel therefore limited actor horizon and displaced the clean
check/repair/recheck/closure tail in both arms. The study tested artifact
coupling inside that bottleneck; it did not test a system with reliable or
economical semantic maintenance.

### Mechanical completion and semantic quality separated sharply

A1 passed 16 of 17 mechanical gates and cited every required source, yet had
several source-reversing errors. Broad citation and near-complete structure
were weak proxies for correct cross-source relationships. Future system scouts
must keep candidate-bound semantic adjudication and current verification in the
outcome contract rather than treating requirement coverage as completion.

## Information economics

A1 used 4,870 fewer serialized tokens than D0, a difference below one percent,
but took about 71 seconds longer. Actor prefix-cache reuse was about 20 percent
in both arms, and maintenance reuse was effectively zero. The comparison does
not support a general cost advantage.

The more important economic result is allocation. Thirty-six maintenance calls
were purchased to produce ten accepted updates. At the endpoint both systems
still lacked a current recheck and closure, while A1 additionally had an
undelivered final effect. A viable system must price semantic maintenance not
only by its token count but by the actor decisions and verification bandwidth
it displaces.

## Supported and unsupported claims

Supported locally:

- the Cedar pressure fork and common relief substrate remained operable;
- exact artifact coupling changed downstream system behavior;
- A1 produced materially broader and stronger partial work than D0;
- both configurations could acquire, construct, check, and repair under
  pressure without reopen churn;
- synchronous bounded integration maintenance was low-yield and became the
  terminal resource;
- exact persistent work did not prevent serious semantic integration errors.

Not supported:

- useful completion by either configuration;
- safe readiness or closure;
- a causal claim that artifact coupling alone produced A1's advantage;
- a general semantic-memory or artifact-coupling architecture;
- an economic advantage for A1;
- the claim that a larger actor or maintenance budget would necessarily
  resolve the remaining semantic defects.

## Program routing

Do not extend this exact two-arm run merely by adding calls. Do not tune the
same maintenance prompt on the same trajectory, and do not promote A1 as a
default architecture.

The result does earn a broader interaction question. The next scout should
preserve exact work-product persistence while changing the system-level
maintenance geometry that dominated both arms. A prospective design should
compare viable interaction policies such as:

- synchronous maintenance after every externalization;
- selective or batched maintenance at a mechanically declared evidence/work
  boundary; and
- actor-authored incremental artifact updates without a mandatory separate
  maintenance call for every evicted observation.

The treatment unit must include ingress, maintenance timing, work persistence,
effect uptake, and verification capacity. Success is not a shorter semantic
object. It is a better complete trajectory: source-correct artifact,
current-check/repair uptake, appropriate readiness, and bounded total cost.

Before GPU work, an offline interaction audit should quantify which rejected
maintenance calls contained usable source relationships, how accepted updates
changed the coupled artifact, and how many actor/check decisions each
maintenance policy would preserve under the same total provider budget. That
audit should inform a fresh prospective task or untouched seed, not retroactively
rescore this run.
