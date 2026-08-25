# Evidence Integration Ledger

**R01: Legal Order, Recommendation, Execution, Check, and Closure Authority**
[S01] establishes the Incident Commander (IC) as the sole authority for evacuation orders, recommendations, execution, checks, and closure. [S02] confirms IC approval is required for cancellation, which needs field confirmation. Vendors and dashboards are advisory only [S01]. [S16] states that submission or a model-authored ledger cannot create readiness authority [S16].
*   **Disposition:** Bound.
*   **Blockers:** None.

**R02: Hazard Triggers, Forecast Binding, Expiry, and Zone Sequencing**
[S02] defines conservative triggers: Zone A mandatory <6h or spotting across Dry Creek; Zone B mandatory <5h, prepare >9h. [S15] provides the forecast ensemble where 42% of members shift winds after 16:00, shortening Zone A arrival below six hours in the adverse branch [S15]. The governing trigger is the conservative envelope (5.8h for Zone A), not the median (7.5h) [S02][S15]. Forecast updates accelerate orders but cannot silently cancel them [S02]. Expiry occurs at the next update or material field observation [S15].
*   **Disposition:** Bound.
*   **Qualifications:** Use conservative ensemble, not median [S02][S15]. Do not delay a conservative trigger because the median forecast is better [S15].
*   **Blockers:** None.

**R03: Population Basis, Tourists, Overlapping Assistance, Survey Uncertainty, and Clearance Demand**
[S03] lists Zone A (5,280), B (8,940), C (12,600) residents plus up to 2,100 tourists [S03]. Medical categories (no vehicle, mobility, oxygen, dialysis) overlap and must not be summed as independent people [S03]. Survey coverage is 91%; an uncertainty allowance is required for unreported households [S03].
*   **Disposition:** Bound.
*   **Qualifications:** Do not sum overlapping medical categories as separate individuals [S03]. Tourist demand is time-dependent [S03].
*   **Blockers:** None.

**R04: Shared Road Bottlenecks, Observed Exercise Throughput, Contraflow, Emergency Inbound Capacity, and Route-Loss Contingencies**
[S04] identifies Mill Junction as the bottleneck (1,500 veh/h). North Bridge (1,100 veh/h) and South Pass (850 veh/h) feed into it; capacities cannot be added [S04]. Exercise throughput was 1,180 veh/h [S04][S13]. Contraflow requires sheriff closure and 45 minutes setup [S04]. Route-loss contingencies require alternate paths via South Pass if North Bridge fails [S04].
*   **Disposition:** Bound.
*   **Qualifications:** Do not sum roads sharing Mill Junction [S04]. Use exercise throughput until field-tested otherwise [S04][S13].
*   **Blockers:** None.

**R05: Person/Accommodation-Level Fleet Matching, Driver Duty, Cycle Time, Bridge Constraints, and Relief Capacity**
[S03] requires fleet reservation by person/accommodation, not household count [S03]. [S16] lists "complete driver roster" as a blocker but provides no operational data [S16]. [S13] notes lift-bus dispatch delays in exercises [S13]. No evidence for driver duty cycles or relief capacity exists in allowed sources.
*   **Disposition:** Missing.
*   **Blockers:** No fleet matching logic or driver duty data in [S03], [S04], [S16].

**R06: Smoke-Safe Shelter Capacity, Accessible Placements, Medical Handoffs, Filtration, Power, and Relocation**
[S02] notes air-quality shelter viability can remove destinations, altering road demand [S02]. [S16] lists "Ridge School filter repair" and "person-level oxygen matching" as blockers but provides no operational data [S16]. [S13] confirms Ridge School's filter test failed [S13]. No evidence for smoke-safe capacity or medical handoffs exists in allowed sources.
*   **Disposition:** Missing.
*   **Blockers:** Cannot verify shelter suitability or medical continuity [S16][S13].

**R07: Redundant Multilingual Warning, Door-Knock Timing, Radio Interoperability, Receipt/Understanding Evidence, and One Zone Revision**
[S16] lists "volunteer-radio identifier test" as a blocker but provides no operational data [S16]. [S13] notes volunteer unit identifiers did not cross the gateway [S13]. No evidence for multilingual warning, door-knock timing, or receipt/understanding evidence exists in allowed sources.
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind communication strategy [S16][S13].

**R08: Fuel and Power Continuity Using Observed Delay, Local Staging, Alternate Routes/Suppliers, and Coupled Asset Effects**
[S16] lists "alternate fuel confirmation" as a blocker but provides no operational data [S16]. [S13] notes fuel arrived after seventeen hours in the exercise [S13]. No evidence for observed delays, local staging, or coupled asset effects exists in allowed sources.
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind resource contracting [S16][S13].

**R09: Animals and Service Animals Without Delaying Human Evacuation or Double-Counting Routes and Shelter Capacity**
No evidence for animal handling or service animal separation without delaying human evacuation is present in [S03], [S04], or [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind animal logistics.

**R10: Private Accountability, Public Aggregation, Self-Evacuation, Restricted Health Data, Reconciliation, Retention, and Deletion Proof**
No evidence for private accountability, public aggregation, restricted health data handling, reconciliation, retention, or deletion proof is present in [S03], [S04], or [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind data management protocol.

**R11: A Concrete 48-Hour Sequence with Owners, Effects, Current Checks, Repair, Recheck, Resource/Cost Authority, and Contingencies**
No evidence for a concrete 48-hour sequence with owners, effects, current checks, repair, recheck, resource/cost authority, and contingencies is present in [S03], [S04], or [S16]. [S16] classifies the package as not ready due to open blockers [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind execution timeline [S16].

**R12: All Exercise and Independent-Review Blockers, Candidate-Bound Readiness, Uncertainties, and Explicit Falsifiers**
[S16] classifies the package as not ready. Open blockers include North Bridge engineering inspection, complete driver roster, Ridge School filter repair, volunteer-radio identifier test, alternate fuel confirmation, and person-level oxygen matching [S16]. Component dashboards are green but bind to different plan revisions; no current integrated check exists [S16]. Readiness requires every hard blocker resolved, effects incorporated, a current integrated exercise or justified bounded check, and incident-command acceptance [S16]. Submission or a model-authored ledger cannot create that authority [S16].
*   **Disposition:** Not Ready.
*   **Blockers:** All six blockers in [S16] remain open.

**Cross-Source Relationships & Contradictions**
[S03] defines demand; [S04] defines supply constraints; [S01] defines authority; [S16] defines readiness status. No contradictions exist between these sources. However, all four lack evidence for fleet specifics (R05), shelter/medical (R06), communications (R07), resources (R08), animals (R09), data privacy (R10), execution sequence (R11). The integration is incomplete for a full evacuation decision.

**Unresolved Evidence**
*   Specific trigger values for fire/weather (R02) are absent in [S03]/[S04].
*   Fleet matching logic linking [S03] demand to vehicle capacity is absent.
*   Shelter location and capacity data are entirely missing from provided sources.