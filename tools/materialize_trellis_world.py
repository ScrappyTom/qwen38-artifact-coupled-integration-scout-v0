"""Materialize the fresh synthetic Trellis heat-continuity world."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task_trellis" / "sources"


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
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


def _row(spec: SourceSpec, index: int) -> tuple[str, str, str, str, str, str]:
    asset = spec.assets[index % len(spec.assets)]
    measure = spec.base_measure + ((index * 17) % 29) / 10
    status = "superseded" if index % 23 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"v{3 + index // 13}",
        f"{measure:.1f}",
        spec.unit,
        status,
    )


def document(spec: SourceSpec) -> str:
    lines = [
        f"# {spec.title}", "", "## Frozen findings", "", *spec.findings, "",
        "## Governing relationships", "", *spec.relationships, "",
        "## Operational evidence", "",
        "| record | asset/zone | version | measure | unit | status |",
        "|---|---|---|---:|---|---|",
    ]
    lines.extend(
        "| " + " | ".join(values) + " |"
        for values in (_row(spec, index) for index in range(72))
    )
    lines.extend(["", "## Decision constraints", "", *spec.constraints, ""])
    return "\n".join(lines)


SPECS = (
    SourceSpec(
        "COUNCIL", "COUNCIL_AUTHORITY.md", "Heat emergency authority and public operating states", "authority", "AUT",
        ("incident-command", "health-office", "utility-desk", "public-liaison"), 1.0, "approval",
        (
            "The emergency manager may activate cooling operations and emergency procurement. Only the health commissioner may authorize a citywide heat-health emergency, and only the continuity director may close the incident after current infrastructure, clinical, shelter, transit, staffing, and audit evidence is reconciled.",
            "A successful mechanical check is not health authority or closure authority. Emergency procurement does not waive water-quality, accessibility, labor, privacy, evidence-custody, or independent-review obligations.",
            "A handoff is valid only when the receiver acknowledges the same operating map, facility roster, current demand model, communications release, and candidate version. Version mismatch blocks closure.",
        ),
        (
            "CLIMATE supplies hazard thresholds, GRID and WATER supply infrastructure state, and REVIEW supplies independent findings; none may authorize closure.",
            "LINEAGE binds the current candidate while COUNCIL separates activation, limited operations, expanded operations, and closure.",
        ),
        ("Name who activates, operates, independently verifies, communicates, and closes.", "Treat semantic records and artifact mutations as non-authoritative work products."),
    ),
    SourceSpec(
        "CLIMATE", "CLIMATE_THRESHOLDS.md", "Heat index, WBGT, and geographic trigger evidence", "hazard", "CLI",
        ("north-district", "river-district", "central-core", "hillside"), 39.0, "degrees-C-WBGT",
        (
            "The current central-core wet-bulb globe temperature is 31.4 degrees Celsius. Limited activation begins at 30.0 degrees for two consecutive thirty-minute windows; expanded activation begins at 32.0 degrees, so one 31.4-degree observation is insufficient for expansion.",
            "Forecast probability of exceeding the expanded threshold is 0.62, while the observed station coverage is 84 percent. Probability and measurement coverage must not be exchanged or multiplied.",
            "A sensor relocation, calibration, forecast model, district boundary, or candidate operating-map change makes prior hazard evidence stale for the affected scope.",
        ),
        (
            "SHELTER and TRANSIT staging consume CLIMATE district triggers; COMMS may publish only the operating state authorized by COUNCIL.",
            "LINEAGE records map changes and REVIEW requires current candidate-bound threshold evidence.",
        ),
        ("Preserve observed versus activation values, windows, probability, coverage, and currentness.", "Define falsifiers, district rollback, and evidence that retires a heat stage."),
    ),
    SourceSpec(
        "GRID", "GRID_COOLING_POWER.md", "Cooling power, feeder limits, and backup capacity", "power", "GRD",
        ("feeder-east", "feeder-west", "library-hub", "backup-plant"), 28.0, "megawatts",
        (
            "Installed cooling-service capacity is 31.0 megawatts, while current usable capacity after feeder derating is 24.5 megawatts. Installed and usable capacity must not be added or swapped.",
            "Feeder voltage is 12.6 kilovolts and must remain between 12.2 and 12.9 kilovolts at every critical node for three consecutive fifteen-minute windows. A system average cannot replace every-node compliance.",
            "Backup generation supplies 8.4 megawatts for sixteen hours at emergency cooling load, but only nine hours at full public load. The load regimes and durations remain distinct.",
        ),
        (
            "SHELTER occupancy and CLINIC surge demand depend on GRID; SUPPLY controls fuel duration and WATER depends on powered pumps.",
            "A feeder, transformer, relay, fuel stock, or facility-load change makes earlier power evidence stale.",
        ),
        ("Preserve installed versus usable MW, every-node voltage, windows, load regime, and duration.", "Define staged load, rollback, replenishment, and current verification."),
    ),
    SourceSpec(
        "WATER", "WATER_HYDRATION.md", "Potable water, pressure, and hydration logistics", "water", "WTR",
        ("north-loop", "central-loop", "clinic-tank", "mobile-cache"), 38.0, "psi",
        (
            "Current minimum pressure is 38 psi. Public cooling sites require at least 35 psi at every served node for three consecutive ten-minute windows; one network average is insufficient.",
            "Potable reserve is 1.6 million liters, while forecast consumption is 0.19 million liters per hour at expanded operations. Reserve and hourly flow use different units and must not be added.",
            "A main repair, pump change, tank refill, disinfection event, sampling method, or candidate facility-roster change makes earlier water evidence stale.",
        ),
        (
            "GRID powers pumps, SHELTER and CLINIC consume potable reserve, and SUPPLY controls tanker replenishment.",
            "REVIEW requires current pressure and quality evidence before closure; COUNCIL retains operating authority.",
        ),
        ("Preserve psi, every-node rule, window count, reserve versus flow, and currentness.", "Name conservation stages, alternate supply, quality holds, and release evidence."),
    ),
    SourceSpec(
        "CLINIC", "CLINIC_SURGE.md", "Clinical surge, triage, and ambulance readiness", "healthcare", "CLN",
        ("hospital-a", "hospital-b", "urgent-care", "ambulance-post"), 71.0, "percent-occupied",
        (
            "Current heat-capable bed occupancy is 71 percent. The surge gate is no more than 82 percent for two consecutive reporting windows and at least twelve staffed cooling beds; occupancy alone is insufficient.",
            "Ambulance response is 9.8 minutes at p95 against a twelve-minute ceiling. The p95 observation is not a population average or readiness percentage.",
            "A bed closure, staffing change, triage protocol, ambulance roster, reporting method, or candidate facility change makes prior clinical evidence stale.",
        ),
        (
            "LABOR supplies licensed coverage, GRID and WATER constrain facilities, and TRANSIT supplies accessible transport alternatives.",
            "COUNCIL authorizes public states while REVIEW independently reconciles current clinical blockers.",
        ),
        ("Preserve occupancy, gate, window count, staffed-bed prerequisite, percentile, and currentness.", "Define diversion, rollback, owners, and evidence retiring surge controls."),
    ),
    SourceSpec(
        "SHELTER", "SHELTER_CAPACITY.md", "Cooling-center capacity, accessibility, and intake", "shelter", "SHL",
        ("library-hub", "arena", "school-east", "mobile-center"), 2100.0, "installed-seats",
        (
            "Installed cooling-center capacity is 2,400 seats, while currently staffed accessible capacity is 1,760 seats. Installed and staffed capacity must not be swapped.",
            "Accessible intake sustains 420 people per hour for four hours; forecast arrival is 510 per hour unless TRANSIT staging and COMMS appointment windows reduce peaks.",
            "A facility closure, staffing change, accessibility failure, intake method, demand model, or candidate site roster makes prior shelter evidence stale.",
        ),
        (
            "GRID and WATER constrain usable capacity, LABOR supplies coverage, TRANSIT shapes arrival, and CLIMATE determines district staging.",
            "REVIEW requires current accessibility and capacity evidence; an artifact cannot self-certify a center.",
        ),
        ("Preserve installed versus staffed capacity, throughput, duration, forecast, and accessibility.", "State overflow, alternate sites, owners, and retirement evidence."),
    ),
    SourceSpec(
        "TRANSIT", "TRANSIT_ACCESS.md", "Transit access, vehicle readiness, and route continuity", "transport", "TRN",
        ("route-red", "route-blue", "paratransit", "shuttle-reserve"), 88.0, "percent-available",
        (
            "Twenty-two of twenty-six cooling shuttles passed inspection. Expanded operations require twenty-two available shuttles plus four independently confirmed accessible vehicles; twenty-two shuttles alone are insufficient.",
            "Median route time is 26 minutes and p95 is 44 minutes. Median and p95 serve different planning purposes and must remain distinct.",
            "A vehicle, route, driver roster, accessibility lift, traffic plan, or candidate facility map change makes earlier transit evidence stale.",
        ),
        (
            "SHELTER arrival planning consumes TRANSIT capacity, LABOR supplies drivers, and COMMS publishes only confirmed routes.",
            "CLIMATE changes geographic staging and LINEAGE binds the route map to the current candidate.",
        ),
        ("Preserve fleet counts, accessible prerequisite, median versus p95, and currentness.", "Name alternate routes, rollback, owner, and confirmation evidence."),
    ),
    SourceSpec(
        "COMMS", "COMMS_COVERAGE.md", "Public communication, confirmation, and delivery latency", "communications", "COM",
        ("sms", "radio", "web", "call-center"), 89.0, "percent-delivered",
        (
            "Heat guidance reached 89 percent of subscribed households; eleven percent remains delivery uncertainty, not an eleven-percent reduction in exposed residents.",
            "Public-state delivery is 680 milliseconds at p95 and 1,140 milliseconds at p99. These observations are not response deadlines.",
            "The call center sustains 1,300 contacts per hour for three hours against forecast demand of 1,750 per hour unless multilingual outbound notices reduce repeat calls.",
        ),
        (
            "COUNCIL determines authorized state language; CLIMATE supplies hazard scope and TRANSIT and SHELTER supply confirmed service facts.",
            "A channel, subscriber list, message release, translation, coverage method, or candidate operating state change makes earlier communication evidence stale.",
        ),
        ("Preserve delivered versus uncertain share, latency percentiles, capacity, duration, and forecast.", "State channels, acknowledgment, accessibility, alternates, and evidence that retires manual outreach."),
    ),
    SourceSpec(
        "SUPPLY", "SUPPLY_LOGISTICS.md", "Fuel, water, medical stock, and resupply", "logistics", "SUP",
        ("generator-fuel", "bottled-water", "cooling-packs", "tanker-fleet"), 16.0, "hours-cover",
        (
            "Generator fuel covers sixteen hours at emergency cooling load and nine hours at full public load. The two consumption regimes must remain distinct.",
            "Bottled water covers 2.8 operating days, while cooling packs cover 3.6 clinic-days. Operating days and clinic-days are different inventory measures.",
            "Three potable tankers arrive at 18:20 UTC with uncertainty of plus or minus thirty-five minutes; planned arrival is not deployed capacity.",
        ),
        (
            "GRID backup duration and WATER replenishment depend on SUPPLY; CLINIC and SHELTER consume different stocks.",
            "CLIMATE may alter delivery routes and LABOR must qualify receiving and distribution teams.",
        ),
        ("Preserve load regime, inventory units, arrival time, uncertainty, and qualification.", "Name reorder triggers, alternates, owners, and retirement evidence."),
    ),
    SourceSpec(
        "LABOR", "LABOR_STAFFING.md", "Staff qualification, fatigue, and mutual aid", "staffing", "LAB",
        ("nurses", "drivers", "electricians", "interpreters"), 9.0, "hours-on-duty",
        (
            "Current qualified coverage is fourteen nurses, twenty-two drivers, six electricians, and eight interpreters. Expanded operation requires twelve nurses, twenty-six drivers, six electricians, and ten interpreters simultaneously.",
            "No covered worker may exceed twelve hours on duty and each must receive at least ten consecutive hours off. Twelve on duty and ten off serve different rules.",
            "Mutual aid supplies six drivers and four interpreters at 17:40 UTC with arrival uncertainty of plus or minus fifty minutes; announced support is not confirmed on-duty coverage.",
        ),
        (
            "CLINIC, TRANSIT, GRID, SHELTER, and COMMS consume different qualified roles; aggregate headcount cannot replace role coverage.",
            "COUNCIL retains authority and REVIEW checks current rosters and fatigue records.",
        ),
        ("Preserve simultaneous role counts, on/off hours, arrival, uncertainty, and currentness.", "State alternates, fatigue stops, owners, and evidence retiring mutual aid."),
    ),
    SourceSpec(
        "LINEAGE", "LINEAGE_CONFIGURATION.md", "Operating-map lineage, rollback, and evidence currency", "change_control", "LIN",
        ("facility-map", "load-plan", "route-map", "message-release"), 9.0, "candidate-index",
        (
            "The current continuity candidate is T9 with facility map F6, load plan G4, route map R8, staffing roster L11, and message release C7. Evidence for T8 is historical unless explicitly transferred and rechecked.",
            "Rollback to T8 is mechanically possible only while facility roster F5 and route table R7 remain compatible. Mechanical possibility is not authorization.",
            "Every mutation must record before and after candidate hashes, changed artifacts, affected evidence, check currency, owner, and rollback effect.",
        ),
        (
            "CLIMATE, GRID, WATER, CLINIC, SHELTER, TRANSIT, COMMS, and LABOR observations may become stale after LINEAGE mutations.",
            "REVIEW evaluates current-candidate evidence independently; COUNCIL authorizes operation and closure separately.",
        ),
        ("Keep facility, load, route, roster, release, and candidate versions explicit.", "Require effect uptake, current check, repair, recheck, and rollback evidence."),
    ),
    SourceSpec(
        "REVIEW", "REVIEW_READINESS.md", "Independent readiness review and unresolved blockers", "readiness", "REV",
        ("authority", "infrastructure", "health", "accessibility"), 10.0, "open-findings",
        (
            "The latest independent review found ten open findings: two infrastructure, two water, two clinical, two accessibility, one staffing, and one communication finding. A finding count is not a readiness percentage.",
            "Blocking findings include the third voltage window, third pressure window, accessible-vehicle confirmation, multilingual staffing confirmation, and missing continuity-director acknowledgment.",
            "Readiness requires current candidate-bound evidence for every blocking control, independent residual-risk review, and explicit acceptance by each authorized owner.",
        ),
        (
            "REVIEW consumes evidence from all operating sources but cannot mutate their state, operate facilities, announce readiness, or close the incident.",
            "A task artifact, semantic scaffold, mechanical check, or submission proposal cannot self-authorize operation or closure.",
        ),
        ("List blockers, falsifiers, residual risks, owners, current evidence, and acceptance.", "Keep review separate from execution, public communication, and closure."),
    ),
)

SOURCE_IDS = tuple(spec.source_id for spec in SPECS)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        (DESTINATION / spec.filename).write_text(document(spec), encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
