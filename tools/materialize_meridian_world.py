from __future__ import annotations

"""Materialize the deterministic synthetic Meridian infusion-recovery world."""

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DESTINATION = ROOT / "task_meridian" / "sources"


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    title: str
    domain: str
    prefix: str
    assets: tuple[str, ...]
    base_measure: float
    unit: str
    findings: tuple[str, str, str]
    relationships: tuple[str, str]
    constraints: tuple[str, str]


def row(spec: SourceSpec, index: int) -> tuple[str, str, str, str, str, str]:
    asset = spec.assets[index % len(spec.assets)]
    measure = spec.base_measure + ((index * 7) % 31) / 10
    status = "hold" if index % 13 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"r{2 + index // 16}",
        f"{measure:.1f}",
        spec.unit,
        status,
    )


def document(spec: SourceSpec) -> str:
    lines = [
        f"# {spec.title}",
        "",
        "## Frozen findings",
        "",
        *spec.findings,
        "",
        "## Governing relationships",
        "",
        *spec.relationships,
        "",
        "## Operational evidence",
        "",
        "| record | asset/zone | revision | measure | unit | status |",
        "|---|---|---|---:|---|---|",
    ]
    lines.extend(
        "| " + " | ".join(values) + " |"
        for values in (row(spec, index) for index in range(48))
    )
    lines.extend(
        [
            "",
            "## Decision constraints",
            "",
            *spec.constraints,
            "",
        ]
    )
    return "\n".join(lines)


SPECS = (
    SourceSpec(
        "AXIOM_AUTHORITY.md",
        "Emergency manufacturing, recall, and release authority",
        "authority",
        "AUTH",
        ("quality-unit", "incident-commander", "regulator", "procurement"),
        1.0,
        "approval",
        (
            "The independent quality unit places or releases a lot hold. The incident commander coordinates recovery, the regulator receives mandatory notice, and procurement executes an approved supplier choice; none may substitute for the quality release decision.",
            "A field recall begins on quality-unit recommendation and accountable-executive authorization. Emergency purchasing authority does not waive validated process, sterility, labeling, or traceability controls.",
            "A shift handoff is valid only when the receiving owner acknowledges the same recovery-candidate, affected-lot, and assay-plan versions. An unacknowledged handoff blocks closure.",
        ),
        (
            "Hazard evidence from BRAMBLE and HEATH informs the hold or release but does not itself create legal authority. Every manufacturing, allocation, and checker effect must bind one candidate version.",
            "A supplier or model-authored evidence slot is advisory work, never recall or release authority.",
        ),
        (
            "Separate detection, recommendation, authorization, execution, verification, and closure.",
            "Name the accountable owner and exact evidence needed to retire each hold.",
        ),
    ),
    SourceSpec(
        "BRAMBLE_CONTAMINATION.md",
        "Endotoxin, particulate, and assay-drift thresholds",
        "quality_hazard",
        "QUAL",
        ("lot-M41", "line-A", "line-B", "water-loop"),
        0.25,
        "EU/mL",
        (
            "The alert threshold is 0.25 endotoxin units per milliliter and the rejection limit is 0.50 EU/mL. Values and units must not be converted into hours, percent, or temperature.",
            "Two validated M41 samples measured 0.31 and 0.34 EU/mL. The lot remains held while the water-loop investigation is open even though neither value reaches the rejection limit.",
            "Current stability modeling assigns a 41 percent probability of assay drift after eighteen hours. That probability is not humidity, defect prevalence, or a readiness score.",
        ),
        (
            "HEATH defines valid confirmation and release rounds; DRIFT and EMBER changes make prior line samples stale for the changed candidate.",
            "NORTH found that particulate inspection and endotoxin sampling were previously reported under mismatched lot revisions.",
        ),
        (
            "Preserve 0.25 EU/mL, 0.50 EU/mL, both observed results, and 41 percent with their exact meanings.",
            "State what starts, holds, expands, and retires the lot and line controls.",
        ),
    ),
    SourceSpec(
        "CIPHER_DEMAND.md",
        "Hospital demand, registry coverage, and overlapping critical cohorts",
        "demand",
        "DEM",
        ("adult-ICU", "pediatric", "dialysis", "home-infusion"),
        93.0,
        "percent-covered",
        (
            "The seventy-two-hour planning demand is 38,400 infusion bags: 18,200 adult acute-care, 7,600 pediatric, 6,900 dialysis, and 5,700 home-infusion allocations.",
            "The registry covers 93 percent of recurring patients. The uncovered seven percent requires an uncertainty allowance; it is not a seven-percent demand reduction.",
            "Pediatric, dialysis, immune-compromised, and home-infusion categories overlap. They cannot be added as independent people or independent bag demand without person-level reconciliation.",
        ),
        (
            "GLINT sets clinical prioritization while FJORD and MARCH constrain verified delivery and acknowledgment. Supply must be compared with time-bound usable output after losses.",
            "A facility may hold local stock, but that stock counts only after lot, expiry, storage, and custody are verified through LOOM.",
        ),
        (
            "State time horizon, population basis, overlap rule, registry uncertainty, and shortage allocation.",
            "Do not translate coverage into readiness or subtract uncovered demand.",
        ),
    ),
    SourceSpec(
        "DRIFT_CAPACITY.md",
        "Fill-line output and shared sterilizer constraint",
        "manufacturing",
        "CAP",
        ("line-A", "line-B", "sterilizer-3", "inspection-cell"),
        16.2,
        "thousand-bags/day",
        (
            "Line A is nominally rated for 14,000 bags per day and Line B for 11,000, but both depend on Sterilizer 3, whose validated sustainable limit is 18,000 bags per day. The line ratings cannot be summed to claim 25,000.",
            "The last integrated run produced 16,200 released bags per day after inspection loss and changeover. Higher output requires a current candidate-bound line, sterilizer, inspection, and laboratory check.",
            "Line B cannot use alternate caps without EMBER dimensional qualification and a new container-closure integrity sample plan.",
        ),
        (
            "IRIS power and JASPER staffing may reduce usable capacity below validated output. KNOLL alternate production shares the same inspection-cell contractor.",
            "Any line, sterilizer cycle, component, or shift mutation makes prior throughput and release evidence stale.",
        ),
        (
            "Use the shared 18,000 limit and observed 16,200 output until current testing proves more.",
            "Bind equipment, component, inspection loss, staffing, power, and release effects.",
        ),
    ),
    SourceSpec(
        "EMBER_COMPONENTS.md",
        "Container components, supplier yield, and observed delivery",
        "components",
        "COMP",
        ("cap-17", "bag-film", "port-set", "label-stock"),
        88.0,
        "percent-yield",
        (
            "The incumbent cap supplier targets an eight-hour emergency delivery, but its last three regional disruptions arrived after nineteen, seventeen, and twenty-one hours. Nineteen hours is the frozen planning observation.",
            "Incoming cap inspection yielded 88 percent usable units. That yield is not a twelve-percent reduction in patient demand and cannot be multiplied into an unvalidated line rating.",
            "The alternate cap has the same catalog diameter but a different compression profile. Dimensional acceptance alone does not establish container-closure integrity.",
        ),
        (
            "DRIFT establishes shared production capacity; HEATH defines the candidate-bound integrity and sterility evidence after a component change.",
            "KNOLL price and lead-time alternatives must retain qualification, inspection, line-change, and traceability effects.",
        ),
        (
            "Distinguish target lead time from observed arrival and component yield from demand.",
            "Do not release alternate components on catalog equivalence alone.",
        ),
    ),
    SourceSpec(
        "FJORD_DISTRIBUTION.md",
        "Cold-chain distribution, routes, and custody",
        "distribution",
        "COLD",
        ("north-route", "river-route", "cross-dock", "hospital-dock"),
        5.1,
        "degrees-C",
        (
            "Released bags must remain between 2 and 8 degrees Celsius. A single value of 2.8 degrees is not a valid replacement for that range.",
            "The river route shortens travel by forty minutes but has a six-hour bridge-closure risk. The north route is ninety minutes longer and has current generator-backed cross-dock capacity.",
            "A temperature excursion starts a hold at the affected pallet and lot level. Delivery completion requires logger review, custody handoff, and facility acknowledgment.",
        ),
        (
            "CIPHER allocation, GLINT clinical priority, IRIS backup power, LOOM lot identity, and MARCH acknowledgment form one delivery claim.",
            "Changing route, cross-dock, pallet, logger, or receiving facility makes prior distribution verification inapplicable to the changed movement.",
        ),
        (
            "State temperature range, route, delay, power, custody, excursion response, and acknowledgment.",
            "Do not equate dispatch, arrival, or one logger reading with usable clinical delivery.",
        ),
    ),
    SourceSpec(
        "GLINT_CLINICAL.md",
        "Clinical allocation, substitution, and protected cohorts",
        "clinical",
        "CARE",
        ("adult-ICU", "pediatric-ICU", "dialysis", "oncology"),
        6.4,
        "thousand-bags/day",
        (
            "Pediatric ICU and neonatal use cannot substitute the concentrated alternative without pharmacy review. Adult routine hydration can use two approved alternatives when renal status is documented.",
            "Dialysis demand is 2,300 bags over seventy-two hours, including 420 patients also represented in the home-infusion registry. The overlap must be reconciled once.",
            "Clinical priority is life-sustaining use, time-critical antimicrobial delivery, then nondeferrable procedures. First request and contract price are not clinical priority rules.",
        ),
        (
            "CIPHER establishes total demand, FJORD delivery usability, MARCH acknowledgment, and LOOM protected patient/lot traceability.",
            "A substitution changes dose, pharmacy review, labeling, and monitoring obligations and requires a current check.",
        ),
        (
            "Preserve cohort overlap, substitution restrictions, review, and monitoring.",
            "Treat any unmatched life-sustaining allocation or unreviewed pediatric substitution as blocking.",
        ),
    ),
    SourceSpec(
        "HEATH_LAB.md",
        "Sampling, assay validity, and lot release evidence",
        "verification",
        "LAB",
        ("endotoxin", "sterility", "particulate", "closure-integrity"),
        11.0,
        "hours",
        (
            "Validated rapid sterility screening takes eleven hours after incubation begins; endotoxin confirmation takes three hours after sample receipt. Courier and queue time are additional.",
            "A release set requires blanks, positive and negative controls, duplicate sampling, custody seals, instrument status, and exact plan revision MR-4. Failed control voids the set.",
            "Samples collected before a line, sterilizer cycle, cap, water-loop, or supplier change do not verify the changed candidate. Two compliant release sets are required after the root-cause correction.",
        ),
        (
            "BRAMBLE defines hazard thresholds; DRIFT and EMBER define candidate-changing production inputs; AXIOM owns formal release.",
            "IRIS power and JASPER staffing determine whether nominal turnaround is achievable.",
        ),
        (
            "Track sample, custody, receipt, controls, assay, plan, candidate, and release decision.",
            "Do not reuse clean results across material candidate mutations.",
        ),
    ),
    SourceSpec(
        "IRIS_CONTINUITY.md",
        "Power, clean utilities, and fuel continuity",
        "continuity",
        "PWR",
        ("line-A", "line-B", "sterilizer-3", "cold-store"),
        13.0,
        "hours",
        (
            "The current tested endurance is thirteen hours for Sterilizer 3, twenty-one for the cold store, and nine for the laboratory air handler at present load.",
            "The fuel agreement targets seven-hour delivery, but the last regional outage produced a sixteen-hour arrival after the depot lost pumping power.",
            "Twenty-four-hour staging or a verified alternate depot and route is required before relying on repeated sterilizer, laboratory, and cold-store cycles.",
        ),
        (
            "DRIFT production, HEATH assay time, FJORD cold-chain custody, and JASPER shifts share continuity resources.",
            "Fuel used by alternate production or mobile generation must be included with facility demand rather than budgeted independently.",
        ),
        (
            "Use the observed sixteen-hour delay rather than the seven-hour target unless a current repair is verified.",
            "State load, endurance, staging, supplier, route, replenishment trigger, and coupled effect.",
        ),
    ),
    SourceSpec(
        "JASPER_WORKFORCE.md",
        "Qualified staffing, shifts, and safety controls",
        "workforce",
        "STAFF",
        ("aseptic-operator", "quality-analyst", "mechanic", "driver"),
        12.0,
        "qualified-staff",
        (
            "Twenty-two operators are on roster, but twelve hold the aseptic endorsement for the affected lines. Five of nine analysts can run the rapid sterility method.",
            "Workers have a twelve-hour duty ceiling and require ten hours rest. Assigning all endorsed operators to the first shift leaves no lawful relief for the second production period.",
            "Sterilizer entry needs lockout, confined-space controls, and a three-person qualified team. Emergency authority does not waive the safety rule.",
        ),
        (
            "DRIFT line modes, HEATH release, FJORD distribution, and KNOLL alternate production depend on qualified people by shift rather than roster headcount.",
            "A schedule mutation changes which capacity and turnaround claims remain current.",
        ),
        (
            "State endorsement, assignment, shift, duty, rest, relief, mobilization, and safety.",
            "Do not count an unendorsed or resting person as available capacity.",
        ),
    ),
    SourceSpec(
        "KNOLL_ALTERNATES.md",
        "Alternate manufacturer capability, timing, and cost authority",
        "economics",
        "ALT",
        ("partner-east", "partner-west", "airfreight", "mobile-inspection"),
        740.0,
        "thousand-dollars",
        (
            "The incident executive may authorize up to 780,000 dollars. The current seventy-two-hour recovery estimate is 712,000 before alternate-cap qualification and airfreight.",
            "Partner East is 24 percent more expensive but can start in ten hours with an approved formulation and qualified operators. Partner West quotes six hours but lacks current closure-integrity method transfer.",
            "The mobile inspection contractor is shared with DRIFT's local lines. Counting its throughput in both facilities double-counts the same constrained team.",
        ),
        (
            "Alternative selection changes formulation, component, inspection, release site, freight, cold chain, workforce, and cost together.",
            "Costs above authority require escalation but do not justify declaring an unverified option ready.",
        ),
        (
            "State capability, qualification, activation, staffing, shared inspection, cost, authority, and retirement condition.",
            "Do not select price or quoted speed independently of validation and current evidence.",
        ),
    ),
    SourceSpec(
        "LOOM_TRACEABILITY.md",
        "Lot genealogy, patient linkage, privacy, and retention",
        "traceability",
        "DATA",
        ("lot", "pallet", "facility", "patient-support"),
        30.0,
        "days",
        (
            "The operation requires component lot, fill lot, sterilizer cycle, assay set, pallet, logger, receiving facility, and disposition. Patient-support data are restricted.",
            "Operational linkage is retained fourteen days after recall closure and deleted within thirty unless a legal hold applies. The last exercise retained exported patient files for ninety-two days.",
            "A facility may use verified local stock. Reconciliation must accept that stock without exposing patient identity or protected clinical need.",
        ),
        (
            "EMBER components, DRIFT production, HEATH release, FJORD movement, GLINT allocation, and MARCH receipt update one exact lot chain.",
            "Changing identifiers, export, access, or retention makes the prior privacy and traceability check stale.",
        ),
        (
            "Specify minimum fields, role access, reconciliation, retention, deletion proof, and public/private separation.",
            "Do not equate a shipping record with complete lot-to-use accountability.",
        ),
    ),
    SourceSpec(
        "MARCH_COMMUNICATIONS.md",
        "Facility notification, acknowledgment, and escalation",
        "communications",
        "COMMS",
        ("safety-alert", "pharmacy-call", "portal", "courier"),
        84.0,
        "percent-acknowledged",
        (
            "The prior safety alert reached 84 percent of enrolled pharmacy contacts within two hours. Transmission is not evidence of acknowledgment or implementation.",
            "Seven rural facilities lack continuous portal access and require voice plus courier confirmation. Two pediatric centers require direct pharmacy review before substitution.",
            "Messages must identify affected lots, effective time, replacement candidate, handling, and escalation. A generic shortage notice is insufficient for recall execution.",
        ),
        (
            "AXIOM authority, GLINT clinical rules, FJORD delivery, and LOOM lot identity must share one effective candidate and lot revision.",
            "Unacknowledged critical facilities remain a closure blocker even when a message was sent.",
        ),
        (
            "Specify channel, audience, timing, effective revision, acknowledgment, and escalation.",
            "Do not convert 84 percent acknowledgment into complete reach or readiness.",
        ),
    ),
    SourceSpec(
        "NORTH_EXERCISE.md",
        "Frozen recovery exercise defects and corrective evidence",
        "exercise",
        "EX",
        ("lot-board", "sample-plan", "cross-dock", "handoff"),
        4.0,
        "material-defects",
        (
            "The exercise found four material defects: lot and assay revisions diverged, the shared inspection contractor was double-booked, two rural facilities were marked notified without acknowledgment, and a clean pre-change sample was reused after a component change.",
            "The initial candidate did not change during the exercise. No current full verification ran, and the exercise did not establish operational readiness.",
            "Corrective evidence requires one candidate-bound lot chain, current post-change assays, confirmed inspection allocation, and facility acknowledgment.",
        ),
        (
            "The defects test AXIOM handoff, DRIFT/KNOLL capacity, HEATH currency, MARCH acknowledgment, and LOOM traceability together.",
            "A checklist pass that omits any of the four defects is nondiscriminating and cannot support closure.",
        ),
        (
            "Carry every defect into exact work, verification, repair, and readiness adjudication.",
            "Do not summarize the exercise as generally successful or treat no candidate change as a current check.",
        ),
    ),
    SourceSpec(
        "ONYX_FORECAST.md",
        "Demand surge and supply-loss forecast revisions",
        "forecast",
        "FCST",
        ("baseline", "surge", "supplier-loss", "route-loss"),
        36.0,
        "percent-scenario",
        (
            "The median demand case remains near baseline, but 36 percent of current ensemble members exceed 44,000 bags over seventy-two hours after the neighboring facility outage.",
            "The conservative branch also assumes one component-delivery miss and six hours of river-route closure. It governs reserves until timestamped demand and route observations rule it out.",
            "Forecast revision MF-9 supersedes MF-7. Decisions citing MF-7 are stale even if their arithmetic is otherwise correct.",
        ),
        (
            "CIPHER demand, EMBER supply timing, FJORD routes, DRIFT output, and KNOLL alternates must be reconciled under the same forecast branch.",
            "A candidate that covers the median case but not the active conservative branch remains blocked.",
        ),
        (
            "Preserve the 36 percent scenario as probability, not certainty, utilization, or humidity.",
            "Name branch, revision, observation trigger, reserve, and retirement condition.",
        ),
    ),
    SourceSpec(
        "PIVOT_READINESS.md",
        "Independent readiness, falsification, and closure rules",
        "readiness",
        "READY",
        ("quality", "supply", "clinical", "communications", "governance"),
        12.0,
        "gates",
        (
            "Readiness requires twelve independent gates: authority, hazard disposition, demand, validated output, qualified components, usable distribution, clinical allocation, workforce and utilities, traceability, execution contingencies, current verification, and unresolved-blocker disposition.",
            "A green mechanical format check, a model-authored source slot, a candidate mutation, or submission proposal is not independent readiness adjudication.",
            "Any current lot hold, unmatched critical allocation, stale post-change assay, unavailable qualified shift, unacknowledged critical facility, or authority gap blocks ready status.",
        ),
        (
            "NORTH supplies discriminating defects; AXIOM defines authority; HEATH and LOOM bind verification to the exact candidate and lot chain.",
            "The final review must identify evidence that would falsify each capacity, safety, delivery, and closure claim.",
        ),
        (
            "Separate mechanical completeness, semantic quality, current verification, and closure authority.",
            "Do not let a progress state, evidence register, or ordinary actor self-authorize readiness.",
        ),
    ),
)


SOURCE_IDS = (
    "AXIOM",
    "BRAMBLE",
    "CIPHER",
    "DRIFT",
    "EMBER",
    "FJORD",
    "GLINT",
    "HEATH",
    "IRIS",
    "JASPER",
    "KNOLL",
    "LOOM",
    "MARCH",
    "NORTH",
    "ONYX",
    "PIVOT",
)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for source_id, spec in zip(SOURCE_IDS, SPECS, strict=True):
        (DESTINATION / spec.filename).write_text(
            document(spec), encoding="utf-8", newline="\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
