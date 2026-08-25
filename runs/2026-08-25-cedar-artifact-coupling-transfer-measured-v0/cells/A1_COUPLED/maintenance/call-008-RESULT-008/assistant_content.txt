# Evidence Integration Ledger

**R01: Legal Order & Authority**
[S01] establishes the county incident commander as sole issuer of evacuation orders following fire-behavior recommendations [S01]. Supporting roles (sheriff, public health, shelter) execute but cannot declare readiness independently [S01]. Vendors and dashboards are advisory only [S01]. Shift handoffs require acknowledged IAP revisions; unacknowledged handoffs block new readiness declarations [S01].
*   **Disposition:** Bound.
*   **Blockers:** None.

**R02: Hazard Triggers & Zone Sequencing**
[S04] defines physical route constraints: South Pass closes if smoke visibility <150m; North Bridge excludes full-size buses >54°C [S04]. No explicit fire/weather trigger logic is present in [S03], [S04], or [S16].
*   **Disposition:** Partial. Physical limits exist, but conservative fire/weather triggers and forecast binding are missing from allowed sources.
*   **Blockers:** Missing trigger values; no expiry logic defined.

**R03: Population Basis & Assistance Demand**
[S03] specifies Zone A (5,280), B (8,940), C (12,600) residents plus up to 2,100 tourists [S03]. Survey coverage is 91% [S03]. Medical categories (no vehicle, mobility, oxygen, dialysis) overlap and must not be summed as independent people [S03].
*   **Disposition:** Accepted with qualification.
*   **Qualifications:** Must carry uncertainty for unreported households; tourist demand is time-dependent [S03].
*   **Blockers:** Overlap logic must be enforced to avoid double-counting.

**R04: Road Bottlenecks & Route Clearance**
[S04] identifies Mill Junction as the system bottleneck with sustainable throughput of 1,500 vehicles/hour [S04]. North Bridge (1,100 veh/h) and South Pass (850 veh/h) feed into Mill Junction; capacities cannot be added [S04]. Last exercise achieved only 1,180 veh/h due to unmanaged lane merging [S04].
*   **Disposition:** Accepted.
*   **Qualifications:** Do not sum independent road ratings across the shared downstream bottleneck [S04]. Clearance time must use shared junction and exercise throughput until a current field test proves otherwise [S04].
*   **Blockers:** Contraflow requires sheriff closure, 45 minutes setup, and staffed crossover points [S04]. County 12 cannot be fully converted to outbound traffic [S04].

**R05: Fleet Matching & Driver Duty**
No evidence for person/accommodation-level fleet matching, driver duty cycles, or relief capacity is present in [S03], [S04], or [S16]. [S16] lists "complete driver roster" as a blocking readiness item but provides no operational data [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind fleet requirements; no cycle time data available.

**R06: Shelter Capacity & Medical Handoffs**
No evidence for smoke-safe shelter capacity, accessible placements, medical handoffs, filtration, power, or relocation is present in [S03], [S04], or [S16]. [S16] lists "Ridge School filter repair" and "person-level oxygen matching" as blockers but provides no operational data [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot verify shelter suitability or medical continuity.

**R07: Warnings & Community Support**
No evidence for redundant multilingual warning, door-knock timing, radio interoperability, receipt/understanding evidence, or zone revision is present in [S03], [S04], or [S16]. [S16] lists "volunteer-radio identifier test" as a blocker but provides no operational data [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind communication strategy.

**R08: Fuel & Power Continuity**
No evidence for fuel/power continuity, observed delays, local staging, alternate routes/suppliers, or coupled asset effects is present in [S03], [S04], or [S16]. [S16] lists "alternate fuel confirmation" as a blocker but provides no operational data [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind resource contracting.

**R09: Animals & Service Animals**
No evidence for animal handling or service animal separation without delaying human evacuation is present in [S03], [S04], or [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind animal logistics.

**R10: Accountability & Data Privacy**
No evidence for private accountability, public aggregation, self-evacuation tracking, restricted health data handling, reconciliation, retention, or deletion proof is present in [S03], [S04], or [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind data management protocol.

**R11: 48-Hour Execution Sequence**
No evidence for a concrete 48-hour sequence with owners, effects, current checks, repair, recheck, resource/cost authority, and contingencies is present in [S03], [S04], or [S16]. [S16] classifies the package as not ready due to open blockers [S16].
*   **Disposition:** Missing.
*   **Blockers:** Cannot bind execution timeline.

**R12: Verification & Readiness Blockers**
[S16] classifies the package as not ready. Open blockers include North Bridge engineering inspection, complete driver roster, Ridge School filter repair, volunteer-radio identifier test, alternate fuel confirmation, and person-level oxygen matching [S16]. Component dashboards are green but bind to different plan revisions; no current integrated check exists [S16]. Readiness requires every hard blocker resolved, effects incorporated, a current integrated exercise or justified bounded check, and incident-command acceptance [S16]. Submission or a model-authored ledger cannot create that authority [S16].
*   **Disposition:** Not Ready.
*   **Blockers:** All six blockers in [S16] remain open.

**Cross-Source Relationships & Contradictions**
[S03] defines demand; [S04] defines supply constraints; [S01] defines authority; [S16] defines readiness status. No contradictions exist between these sources. However, all four lack evidence for fleet specifics (R05), shelter/medical (R06), communications (R07), resources (R08), animals (R09), data privacy (R10), execution sequence (R11). The integration is incomplete for a full evacuation decision.

**Unresolved Evidence**
*   Specific trigger values for fire/weather (R02) are absent in [S03]/[S04].
*   Fleet matching logic linking [S03] demand to vehicle capacity is absent.
*   Shelter location and capacity data are entirely missing from provided sources.