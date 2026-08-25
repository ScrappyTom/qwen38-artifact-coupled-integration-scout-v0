from __future__ import annotations

"""Materialize the deterministic synthetic Bluehaven water-restoration world."""

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task_bluehaven" / "sources"


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
        "| " + " | ".join(values) + " |" for values in (row(spec, i) for i in range(48))
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
        "S01_AUTHORITY.md",
        "Bluehaven emergency drinking-water authority",
        "authority",
        "AUTH",
        ("utility-director", "health-officer", "operations-chief", "mayor"),
        1.0,
        "approval",
        (
            "The public-health officer issues or lifts a boil-water order after the utility laboratory recommendation. The utility director owns operational restoration; neither a vendor nor a dashboard can declare public-health readiness.",
            "The operations chief may isolate mains and dispatch tankers, while the mayor controls emergency expenditure above the utility director's delegated ceiling. These roles are distinct.",
            "A shift handoff is valid only when the receiving officer acknowledges the same incident-plan and water-quality revision. An unacknowledged transfer blocks closure.",
        ),
        (
            "Trigger evidence from S02 and S15 informs the health officer but does not replace the legal order. Restoration effects require a current laboratory and hydraulic check.",
            "Every public notice, field action, and checker must bind the same incident revision and effective time.",
        ),
        (
            "Distinguish recommendation, legal order, operational execution, verification, and closure authority.",
            "Do not treat a model-authored ledger, vendor assertion, or submission as readiness authority.",
        ),
    ),
    SourceSpec(
        "S02_CONTAMINATION.md",
        "Contamination thresholds and conservative response triggers",
        "hazard",
        "WQ",
        ("North-intake", "East-clearwell", "Zone-A", "Zone-B"),
        0.2,
        "mg/L",
        (
            "A mandatory boil-water order begins when treated chlorine residual remains below 0.2 mg/L in two consecutive validated samples or when benzene exceeds 5 micrograms per liter in any confirmed distribution sample.",
            "The median plume forecast stays north of the intake, but 38 percent of current ensemble members reverse after 18:00. The conservative branch governs intake isolation until field samples rule it out.",
            "One clean sample cannot cancel an active order. Lifting requires two compliant rounds, hydraulic stabilization, and public-health approval.",
        ),
        (
            "Demand and alternate-water supply from S03 and S08 must cover the period implied by laboratory turnaround in S09, not only pipe travel time.",
            "River forecast revision in S15, treatment state in S04, and public notice in S10 must remain on one candidate-bound revision.",
        ),
        (
            "Preserve 0.2 mg/L, 5 micrograms per liter, and 38 percent with their exact meanings and units.",
            "State the observations that start, hold, expand, and lift each protective action.",
        ),
    ),
    SourceSpec(
        "S03_DEMAND.md",
        "Service-zone demand, registry coverage, and vulnerable households",
        "demand",
        "DEM",
        ("Zone-A", "Zone-B", "Zone-C", "Zone-D"),
        46.8,
        "thousand-people",
        (
            "Bluehaven serves 46,800 residents: 8,200 in Zone A, 12,600 in B, 15,400 in C, and 10,600 in D. Daytime industrial demand adds 2.4 megaliters per day but is not drinking-water demand.",
            "The emergency minimum is three liters per person per day plus separately calculated clinical and sanitation demand. Vulnerability categories overlap and cannot be summed as independent people.",
            "The customer and meter registry covers 94 percent of occupied premises. The uncovered six percent requires an uncertainty allowance; it is not a six-percent reduction in demand.",
        ),
        (
            "Treatment and distribution capacity in S04-S05 must be compared with time-bound potable demand after losses, not with nominal plant nameplate totals.",
            "Critical facilities in S07 and tanker logistics in S08 need explicit priority allocations outside the household minimum.",
        ),
        (
            "State population basis, overlap rule, registry uncertainty, loss allowance, and time-bound demand.",
            "Do not convert 94 percent coverage into a 94 percent readiness score or six percent into a demand target.",
        ),
    ),
    SourceSpec(
        "S04_TREATMENT.md",
        "Treatment-plant capacity and shared clearwell limits",
        "treatment",
        "PLANT",
        ("Plant-A", "Plant-B", "East-clearwell", "West-clearwell"),
        13.4,
        "ML/day",
        (
            "Plant A is rated at 12 megaliters per day and Plant B at 9, but both discharge through the East clearwell and trunk whose validated sustainable limit is 15 megaliters per day. The ratings cannot be added to claim 21.",
            "The last integrated run sustained 13.4 megaliters per day after filter backwash and distribution losses. A higher figure requires a current candidate-bound test.",
            "Plant B cannot treat the benzene branch without the mobile carbon unit, whose activation and staffing are governed by S12.",
        ),
        (
            "Hydraulic zone pressure in S05 can reduce deliverable potable capacity below treatment output. Generator state in S06 constrains both plants and the shared clearwell pumps.",
            "Alternate-water obligations in S08 are the gap between validated delivered capacity and demand, not the gap from nameplate output.",
        ),
        (
            "Use the shared 15 ML/day bottleneck and observed 13.4 ML/day until a current integrated test proves more.",
            "Bind treatment mode, carbon unit, power, staffing, loss, and hydraulic effects together.",
        ),
    ),
    SourceSpec(
        "S05_DISTRIBUTION.md",
        "Distribution hydraulics, pressure zones, and isolation effects",
        "distribution",
        "HYD",
        ("Zone-A", "Zone-B", "Zone-C", "Zone-D", "East-trunk"),
        27.0,
        "psi",
        (
            "Zones A and B share the East trunk. Closing valve V-17 isolates the suspected plume but lowers Zone B hospital pressure below the 28 psi operational floor unless booster P-4 is running.",
            "Zone C can backfeed B at 3.1 megaliters per day, but only after two cross-connection samples pass. Zone D cannot backfeed without reversing an unprotected industrial connection.",
            "Pressure below 20 psi creates an intrusion risk and independently sustains the boil-water order even if treatment samples are clean.",
        ),
        (
            "The contamination isolation in S02, plant output in S04, hospital demand in S07, and generator state in S06 form one hydraulic decision.",
            "A valve or pump mutation makes any prior pressure and sampling check stale for the new candidate.",
        ),
        (
            "Name valve, pump, pressure, sampling, and backfeed observations for every switch.",
            "Do not assume treatment output reaches customers without a current hydraulic check.",
        ),
    ),
    SourceSpec(
        "S06_POWER.md",
        "Power, generator endurance, and fuel resupply",
        "continuity",
        "PWR",
        ("Plant-A", "Plant-B", "P-4", "lab", "radio"),
        14.0,
        "hours",
        (
            "Plant A has fourteen tested generator hours, Plant B twenty-two, booster P-4 nine, and the utility laboratory twelve at the current load.",
            "The fuel contract targets eight-hour delivery, but the last regional outage produced a seventeen-hour arrival because the primary depot route flooded.",
            "Twenty-four-hour local staging or a verified alternate depot and route is required before relying on repeated treatment and tanker-loading cycles.",
        ),
        (
            "Power loss at P-4 invalidates the Zone B hospital pressure plan in S05-S07. Lab power affects the sample turnaround assumed in S09.",
            "Fuel used by tanker loading and mobile carbon treatment must be included with generator demand rather than budgeted independently.",
        ),
        (
            "Use the observed seventeen-hour delay, not the eight-hour contract target, unless a repair is currently verified.",
            "State consumption, staging, supplier, route, replenishment trigger, and coupled effects.",
        ),
    ),
    SourceSpec(
        "S07_CRITICAL_CUSTOMERS.md",
        "Hospitals, dialysis, care facilities, and accessibility",
        "critical_care",
        "CARE",
        ("Bluehaven-Hospital", "North-Dialysis", "Harbor-Care", "home-oxygen"),
        2.8,
        "ML/day",
        (
            "Bluehaven Hospital requires 0.9 megaliters per day and at least 28 psi; North Dialysis needs 0.18 and a verified low-conductivity supply. Three care facilities require 0.42 combined.",
            "There are 64 registered home dialysis or immune-compromised households, with eleven duplicate entries across programs. Assignments must be person-level and private.",
            "The hospital has six hours of potable storage. A generic tanker is not a clinical supply until hose, disinfection, testing, pressure, and custody pass.",
        ),
        (
            "S05 pressure, S08 tanker specification, S09 sample release, and S13 privacy jointly constrain critical-customer continuity.",
            "Public reporting may aggregate service status but may not reveal individual medical need or delivery address.",
        ),
        (
            "Bind every critical cohort to source, transport, testing, delivery, storage, and handoff.",
            "Treat any unmatched clinical need or sub-28-psi hospital plan as blocking.",
        ),
    ),
    SourceSpec(
        "S08_ALTERNATE_WATER.md",
        "Tanker, bottled-water, loading, and distribution capacity",
        "logistics",
        "ALT",
        ("tanker", "bottle-line", "loading-bay", "distribution-point"),
        5.6,
        "ML/day",
        (
            "The county has eight certified potable tankers totaling 192,000 liters per cycle; only five qualified drivers can report within two hours. A full clean-load-deliver-disinfect cycle averages 4.5 hours.",
            "The bottling contract supplies 110,000 liters per day after a ten-hour activation delay. Two listed tanker vendors carry nonpotable construction tanks and cannot serve drinking water.",
            "Loading Bay 2 shares power and pumps with Plant A. Counting plant output and tanker loading independently double-counts the same constrained asset.",
        ),
        (
            "Household demand in S03, clinical priority in S07, plant/power state in S04/S06, and road access in S12 determine usable alternate-water throughput.",
            "Driver duty and disinfection time require relief capacity; nominal tank volume is not sustained daily delivery.",
        ),
        (
            "Show certified assets, staffed cycles, activation delay, shared loading capacity, priority allocation, and relief.",
            "Do not count nonpotable tanks, unavailable drivers, or gross tank volume as delivered potable supply.",
        ),
    ),
    SourceSpec(
        "S09_LAB.md",
        "Sampling plan, laboratory turnaround, and release authority",
        "verification",
        "LAB",
        ("intake", "clearwell", "Zone-A", "Zone-B", "hospital"),
        6.0,
        "hours",
        (
            "Routine microbiology turnaround is six hours after receipt; benzene confirmation is nine hours. Courier time is additional and currently averages seventy minutes.",
            "A release round requires field blank, duplicate, custody seal, instrument control, and exact sampling-plan revision WQ-R7. Failed quality control voids the round.",
            "Two compliant rounds are required to lift the order; samples collected before a valve, pump, carbon-unit, or source change do not verify the changed candidate.",
        ),
        (
            "The check must bind exact sample locations to the hydraulic state in S05 and current forecast/treatment revision in S02/S15.",
            "Laboratory power and staffing from S06/S11 determine whether nominal turnaround is achievable.",
        ),
        (
            "Track collection, custody, receipt, assay, quality control, candidate version, and release decision.",
            "Do not reuse a clean result across a material candidate mutation.",
        ),
    ),
    SourceSpec(
        "S10_COMMUNICATIONS.md",
        "Public warning, language access, and receipt evidence",
        "communications",
        "COMMS",
        ("SMS", "voice", "door-knock", "web", "radio"),
        82.0,
        "percent-reach",
        (
            "The last outage disabled 31 percent of cellular sites for seven hours. SMS reached 82 percent of enrolled numbers; a web posting alone reached fewer than half of affected households.",
            "Eight percent of households primarily use Vietnamese, five percent Spanish, and three percent require another language or ASL relay. Current templates omit Vietnamese and ASL.",
            "Door-knock teams need two hours for the river mobile-home areas. Message transmission is not proof of receipt or understanding.",
        ),
        (
            "The notice must use the same service-zone and WQ-R7 revision as field isolation and sampling. Contradictory revisions can cause unsafe consumption or unnecessary tanker demand.",
            "Registry gaps in S03 require redundant channels and measured receipt evidence rather than assumed enrollment.",
        ),
        (
            "Specify redundant channels, languages, timing, effective revision, and confirmation evidence.",
            "Do not treat sending, posting, or county-only radio success as population understanding.",
        ),
    ),
    SourceSpec(
        "S11_WORKFORCE.md",
        "Operator, laboratory, driver, and safety staffing",
        "workforce",
        "STAFF",
        ("operator", "lab-tech", "driver", "electrician", "communicator"),
        11.0,
        "qualified-staff",
        (
            "Eighteen utility operators are on roster, but eleven hold the treatment endorsement required for the affected plants. Four of seven laboratory staff can run the benzene method.",
            "Workers have a twelve-hour duty ceiling and need eight hours rest. Using all endorsed operators in the first shift leaves no legal relief for the second operational period.",
            "Confined-space valve entry needs a three-person team and air monitoring; emergency authority does not waive the safety rule.",
        ),
        (
            "S04 treatment modes, S08 tanker cycles, S09 laboratory release, and S12 mutual aid all depend on qualified people by shift rather than headcount.",
            "A schedule mutation changes which capacity claims remain valid and requires a current integrated check.",
        ),
        (
            "State qualification, assignment, shift, duty, relief, mobilization, and safety constraints.",
            "Do not count an unendorsed or resting person as operational capacity.",
        ),
    ),
    SourceSpec(
        "S12_MUTUAL_AID_COST.md",
        "Mutual aid, vendor capability, routes, and cost authority",
        "economics",
        "AID",
        ("carbon-unit", "tanker", "generator", "lab", "crew"),
        640.0,
        "thousand-dollars",
        (
            "The utility director may authorize up to $650,000 of emergency work. The current seventy-two-hour estimate is $572,000 before mobile carbon and alternate fuel.",
            "The low-cost carbon vendor arrives in fourteen hours via the flood-prone depot road. The alternate costs 22 percent more, arrives in eight hours by Ridge Route, and includes qualified operators.",
            "Two low-cost tanker vendors offer nonpotable equipment. Price may not remove drinking-water certification, accessibility, laboratory, power, or continuity controls.",
        ),
        (
            "Vendor selection changes treatment mode, workforce, route, activation time, fuel, and cost together; it must enter one candidate effect and check.",
            "Costs above delegated authority require escalation but do not justify declaring an unsafe plan ready.",
        ),
        (
            "State capability, activation, route, staffing, price, authority, contingency, and retirement condition.",
            "Do not select price independently of technical and timing constraints.",
        ),
    ),
    SourceSpec(
        "S13_ACCOUNTABILITY.md",
        "Customer accountability, privacy, and assistance records",
        "data",
        "DATA",
        ("service-status", "medical-need", "delivery", "complaint", "contact"),
        30.0,
        "days",
        (
            "The operation needs premise service status, notice receipt, alternate-water delivery, and assistance outcome. Medical need and delivery address are restricted fields.",
            "Operational records are retained seven days after order closure and deleted within thirty unless a legal hold applies. The last exercise retained exported spreadsheets for eighty-six days.",
            "A household may obtain safe water independently. Accountability must accept verified self-supply without publishing medical status or location.",
        ),
        (
            "S03 uncertainty, S07 critical delivery, S08 distribution, and S10 warning receipt update one private operational record while public status remains aggregated.",
            "Changing identifiers, export, access, or retention makes the prior privacy check stale.",
        ),
        (
            "Specify minimum fields, role access, reconciliation, retention, deletion proof, and public/private separation.",
            "Do not equate distribution-point attendance with complete household accountability.",
        ),
    ),
    SourceSpec(
        "S14_EXERCISE.md",
        "Full-scale restoration exercise defects",
        "verification",
        "EX",
        ("sample-custody", "hospital-pressure", "tanker", "notice", "handoff"),
        91.0,
        "percent-complete",
        (
            "Exercise Bluewater-4 lost sample custody on two of twelve sites, dropped hospital pressure to 24 psi, and started the first certified tanker cycle ninety-four minutes late.",
            "County SMS worked, but Vietnamese and ASL notices were absent. The shift handoff used different sampling revisions and made three clean results non-current.",
            "The corrective-action tracker marks several items closed from owner attestation. Readiness requires current execution evidence for the exact plan.",
        ),
        (
            "One exercise links sampling, hydraulics, clinical continuity, logistics, communications, and revision binding; repairing one can change the others.",
            "A later candidate mutation makes the old exercise historical unless a bounded current check justifies transfer.",
        ),
        (
            "Carry every material defect with owner, effect, current repair evidence, recheck, and blocking status.",
            "Do not use owner attestation or a green component dashboard as operational proof.",
        ),
    ),
    SourceSpec(
        "S15_RIVER_FORECAST.md",
        "River plume ensemble and common revision cadence",
        "hazard",
        "RIVER",
        ("cycle", "intake", "plume", "rainfall", "current"),
        38.0,
        "percent-reversal",
        (
            "Forecasts update every two hours. The base case keeps the plume north of the intake, but 38 percent of WQ-R7 ensemble members reverse after 18:00 and reach the intake before midnight.",
            "A later median can improve while the adverse range widens. Intake isolation remains governed by the conservative branch until field samples rule it out.",
            "Telemetry can lag ninety minutes during heavy rain. Absence of a new plume position is not evidence that contamination stopped moving.",
        ),
        (
            "S01-S02 orders, S04 treatment, S05 hydraulics, S09 sampling, and S10 notices must all bind revision WQ-R7 until a current successor is explicitly admitted.",
            "Mixing forecast or sampling revisions creates an incoherent restoration decision even when each component is individually green.",
        ),
        (
            "Name WQ-R7, its expiry, adverse branch, and observations that authorize a successor revision.",
            "Do not convert revision binding into permission for an arbitrary number of revisions.",
        ),
    ),
    SourceSpec(
        "S16_READINESS.md",
        "Independent Bluehaven restoration-readiness review",
        "governance",
        "READY",
        ("carbon-unit", "hospital-pressure", "sample-custody", "notice", "fuel", "relief"),
        6.0,
        "blockers",
        (
            "The independent review classifies the package as not ready. Open blockers are mobile-carbon activation, current 28-psi hospital proof, complete sample custody, Vietnamese and ASL notice, alternate fuel confirmation, and endorsed relief staffing.",
            "Several component dashboards are green but bind different candidate and WQ revisions. No current integrated check covers source isolation, treatment, hydraulics, clinical delivery, alternate water, laboratory, communications, power, staffing, and accountability together.",
            "Readiness requires every hard blocker resolved, all effects incorporated, a current candidate-bound check, public-health acceptance, and exact handoff acknowledgment. Submission cannot create that authority.",
        ),
        (
            "The review evaluates a coupled system. Repairing one blocker can change capacity, staffing, route, cost, sampling, or notice currency.",
            "Closure must distinguish ready, not ready, and not adjudicated; a strong partial must preserve its blockers.",
        ),
        (
            "Preserve all six blockers until exact current evidence resolves them.",
            "Require effect uptake, current recheck, independent readiness authority, and acknowledged WQ-R7 binding before closure.",
        ),
    ),
)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        (DESTINATION / spec.filename).write_text(
            document(spec), encoding="utf-8", newline="\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
