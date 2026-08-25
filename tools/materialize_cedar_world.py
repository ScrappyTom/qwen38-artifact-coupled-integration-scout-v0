from __future__ import annotations

"""Materialize the deterministic synthetic Cedar Valley evacuation world."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task" / "cedar_sources"


@dataclass(frozen=True)
class SourceSpec:
    filename: str
    title: str
    domain: str
    findings: tuple[str, ...]
    relationships: tuple[str, ...]
    constraints: tuple[str, ...]
    row_factory: Callable[[int], tuple[object, ...]]
    headers: tuple[str, ...]


def table(headers: tuple[str, ...], rows: list[tuple[object, ...]]) -> list[str]:
    output = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    output.extend("| " + " | ".join(str(value) for value in row) + " |" for row in rows)
    return output


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
        *table(spec.headers, [spec.row_factory(index) for index in range(48)]),
        "",
        "## Decision constraints",
        "",
        *spec.constraints,
        "",
    ]
    return "\n".join(lines)


ZONES = ("A-North", "A-River", "B-East", "B-Center", "C-South", "C-Ridge")


def authority_row(index: int) -> tuple[object, ...]:
    owners = ("incident-commander", "fire-behavior-lead", "sheriff", "public-health", "shelter-branch")
    return (f"AUTH-{index:03d}", f"+{index * 15:04d}m", owners[index % len(owners)], ZONES[index % len(ZONES)], "current" if index % 9 else "handoff-due", f"iap-r{2 + index // 16}")


def hazard_row(index: int) -> tuple[object, ...]:
    arrival = max(2.4, 11.8 - index * 0.17)
    confidence = 58 + (index * 7) % 38
    return (f"FIRE-{index:03d}", ZONES[index % len(ZONES)], f"{arrival:.1f}h", f"{18 + (index * 3) % 27}mph", f"{confidence}%", "order" if arrival <= 6 else "prepare")


def population_row(index: int) -> tuple[object, ...]:
    return (f"BLOCK-{index:03d}", ZONES[index % len(ZONES)], 170 + (index * 43) % 390, 9 + (index * 11) % 64, 2 + (index * 5) % 21, 1 + (index * 3) % 12, "survey-2026-r4")


def road_row(index: int) -> tuple[object, ...]:
    routes = ("North-Bridge", "South-Pass", "County-12", "Ridge-Connector", "Mill-Junction")
    capacity = {"North-Bridge": 1100, "South-Pass": 850, "County-12": 620, "Ridge-Connector": 480, "Mill-Junction": 1500}
    route = routes[index % len(routes)]
    observed = int(capacity[route] * (0.68 + (index % 7) * 0.035))
    return (f"ROAD-{index:03d}", route, capacity[route], observed, "shared-junction" if route != "Mill-Junction" else "system-bottleneck", "hold" if index % 13 == 0 else "open")


def fleet_row(index: int) -> tuple[object, ...]:
    kinds = ("standard-bus", "lift-bus", "ambulance", "paratransit", "school-bus")
    kind = kinds[index % len(kinds)]
    available = 1 + index % 4
    seats = {"standard-bus": 44, "lift-bus": 34, "ambulance": 2, "paratransit": 8, "school-bus": 48}[kind]
    return (f"FLEET-{index:03d}", kind, available, seats, f"{1 + index % 5} drivers", f"{35 + (index * 13) % 61}m", "qualified" if index % 8 else "roster-gap")


def shelter_row(index: int) -> tuple[object, ...]:
    sites = ("Civic-Arena", "Expo-Hall", "Ridge-School", "West-College")
    nominal = {"Civic-Arena": 2200, "Expo-Hall": 3000, "Ridge-School": 1200, "West-College": 1800}
    smoke_safe = {"Civic-Arena": 1600, "Expo-Hall": 2100, "Ridge-School": 700, "West-College": 1500}
    accessible = {"Civic-Arena": 48, "Expo-Hall": 64, "Ridge-School": 0, "West-College": 32}
    site = sites[index % len(sites)]
    return (f"SHEL-{index:03d}", site, nominal[site], smoke_safe[site], accessible[site], f"{12 + index % 9}h", "verified" if index % 10 else "filter-test-due")


def care_row(index: int) -> tuple[object, ...]:
    needs = ("oxygen", "dialysis", "refrigerated-medication", "wheelchair", "behavioral-support")
    need = needs[index % len(needs)]
    return (f"CARE-{index:03d}", ZONES[index % len(ZONES)], need, 2 + (index * 7) % 24, f"{20 + (index * 17) % 75}m", "matched" if index % 9 else "transport-unassigned", "health-roster-r5")


def comms_row(index: int) -> tuple[object, ...]:
    channels = ("IPAWS", "cell-SMS", "county-radio", "door-knock", "community-hotline", "social-feed")
    languages = ("English", "Spanish", "Hmong", "ASL-relay")
    channel = channels[index % len(channels)]
    return (f"COMMS-{index:03d}", channel, languages[index % len(languages)], ZONES[index % len(ZONES)], f"{72 + (index * 5) % 29}%", "degraded" if index % 11 == 0 else "available", "message-r7")


def continuity_row(index: int) -> tuple[object, ...]:
    assets = ("shelter-generator", "radio-repeater", "bus-fuel", "oxygen-cache", "traffic-signal")
    asset = assets[index % len(assets)]
    endurance = {"shelter-generator": 16, "radio-repeater": 10, "bus-fuel": 14, "oxygen-cache": 18, "traffic-signal": 8}[asset]
    return (f"CONT-{index:03d}", asset, f"{endurance}h", f"{6 + (index * 7) % 18}h", "local" if index % 3 else "vendor-dependent", "hold" if index % 14 == 0 else "tracked")


def animal_row(index: int) -> tuple[object, ...]:
    category = ("household-pets", "horses", "cattle", "service-animals")[index % 4]
    return (f"ANIMAL-{index:03d}", ZONES[index % len(ZONES)], category, 8 + (index * 19) % 86, 2 + index % 11, f"{30 + (index * 9) % 90}m", "separate-route" if category != "service-animals" else "remain-with-handler")


def air_row(index: int) -> tuple[object, ...]:
    pm = 28 + (index * 17) % 240
    return (f"AIR-{index:03d}", ZONES[index % len(ZONES)], pm, f"{6 + index % 10}h", "MERV-13" if index % 4 else "filter-gap", "relocate" if pm >= 150 else "monitor")


def data_row(index: int) -> tuple[object, ...]:
    record = ("household-status", "medical-accommodation", "transport-assignment", "shelter-checkin", "reunification-contact")[index % 5]
    return (f"DATA-{index:03d}", record, "minimum-necessary", f"{7 + index % 24}d", "restricted" if record == "medical-accommodation" else "operational", "complete" if index % 12 else "deletion-proof-missing")


def exercise_row(index: int) -> tuple[object, ...]:
    defects = ("merge-throughput", "lift-dispatch", "radio-handoff", "family-accountability", "shelter-filter", "fuel-arrival")
    defect = defects[index % len(defects)]
    return (f"EX-{index:03d}", defect, ZONES[index % len(ZONES)], f"{38 + (index * 13) % 119}m", "repaired" if index % 7 in (1, 2, 3) else "open", f"exercise-r{3 + index // 16}")


def cost_row(index: int) -> tuple[object, ...]:
    categories = ("bus-callout", "accessible-cot", "filter-bank", "fuel-staging", "animal-trailer", "translation")
    category = categories[index % len(categories)]
    return (f"COST-{index:03d}", category, 4 + index % 13, f"${1800 + (index * 137) % 8700}", "preapproved" if index % 5 else "incident-authority-required", f"contract-r{4 + index // 20}")


def weather_row(index: int) -> tuple[object, ...]:
    wind = 14 + (index * 5) % 31
    shift = 18 + (index * 11) % 63
    return (f"WX-{index:03d}", f"cycle-{index:02d}", f"{wind}mph", f"{shift}%", f"{4.5 + (index % 12) * 0.45:.1f}h", "conservative-envelope" if shift >= 40 else "base-case")


def readiness_row(index: int) -> tuple[object, ...]:
    blockers = ("bridge-inspection", "driver-roster", "shelter-filter", "radio-interoperability", "fuel-delivery", "oxygen-matching")
    blocker = blockers[index % len(blockers)]
    return (f"READY-{index:03d}", blocker, "blocking" if index % 8 in (0, 1) else "conditional", f"owner-{index % 9:02d}", f"check-r{2 + index // 12}", "current" if index % 10 else "stale-after-change")


SPECS = (
    SourceSpec("S01_COMMAND_AUTHORITY.md", "Cedar Valley command authority and evacuation powers", "authority", (
        "The county incident commander alone issues an evacuation order after receiving the fire-behavior recommendation. The sheriff executes traffic control, public health owns medical continuity, and the shelter branch operates sites; none of those supporting roles can independently declare the whole operation ready.",
        "A voluntary warning may be issued before the statutory trigger. Mandatory orders must identify the exact zone revision and effective time. A vendor, dashboard, or model recommendation is advisory rather than closure authority.",
        "Authority transfers at shift change require an acknowledged incident-action-plan revision. An unacknowledged handoff leaves the outgoing commander responsible and blocks a new readiness declaration.",
    ), (
        "Hazard triggers from S02 and S15 inform the commander but do not replace the legal order. Road controls in S04 become executable only after the sheriff acknowledges the same zone revision.",
        "Candidate checks are current only for the exact plan and roster they evaluated. Any route, shelter, or fleet mutation requires a new readiness reconciliation.",
    ), (
        "The decision must distinguish recommendation, legal order, execution, verification, and closure authority.",
        "No single branch may waive a blocking road, medical, communications, or shelter condition.",
    ), authority_row, ("record", "time", "owner", "zone", "handoff", "plan binding")),
    SourceSpec("S02_FIRE_BEHAVIOR.md", "Fire behavior, trigger thresholds, and uncertainty", "hazard", (
        "Zone A becomes mandatory when the conservative fire-arrival estimate falls below six hours or when spotting crosses Dry Creek. Zone B enters prepare status at nine hours and mandatory status at five hours. Zone C is not ordered from the base forecast alone.",
        "The current median model gives Zone A 7.5 hours, but the conservative ensemble gives 5.8 hours because a wind shift has a 42 percent probability. The governing trigger uses the conservative envelope, not the median.",
        "A forecast update can accelerate an order but cannot silently cancel one already issued. Cancellation requires field confirmation and incident-command approval.",
    ), (
        "Clearance time from S03–S05 must be compared with conservative arrival, including mobilization and accessible-transport delay rather than road travel alone.",
        "Air-quality shelter viability from S11 can remove a nominal destination and thereby alter road demand; hazard and shelter plans are coupled.",
    ), (
        "Use explicit trigger thresholds and show which observation would advance, hold, or expand an order.",
        "Treat forecast uncertainty as a decision input, not a disclaimer that permits delay.",
    ), hazard_row, ("forecast", "zone", "arrival", "wind", "confidence", "disposition")),
    SourceSpec("S03_ZONE_POPULATION.md", "Zone population, vehicle access, and assistance demand", "demand", (
        "Zone A contains 5,280 residents, Zone B 8,940, and Zone C 12,600 at night. Daytime tourism adds up to 2,100 people near A-River and B-Center and is absent from the resident registry.",
        "Across Zones A and B, 620 households report no private vehicle, 184 people require mobility assistance, 73 use continuous oxygen, and 28 have dialysis due within twenty-four hours. These categories overlap and may not be added as independent people.",
        "Household survey coverage is 91 percent. The decision must carry an uncertainty allowance rather than treating unreported households as self-evacuating.",
    ), (
        "Fleet capacity in S05 must be reserved by person and accommodation, not by household count. Medical destinations in S07 constrain which vehicles can serve which riders.",
        "Tourist demand changes with time of day, so clearance estimates must bind to the order time and cannot reuse the overnight denominator.",
    ), (
        "State a demand basis, overlap rule, uncertainty allowance, and priority order.",
        "Do not use total registered households as a substitute for people requiring transport.",
    ), population_row, ("block", "zone", "people", "no vehicle", "mobility", "oxygen", "survey")),
    SourceSpec("S04_ROAD_NETWORK.md", "Road network capacity, shared bottlenecks, and contraflow", "transport", (
        "North Bridge is rated at 1,100 passenger vehicles per hour and South Pass at 850, but both feed Mill Junction, whose measured sustainable throughput is 1,500 vehicles per hour. Their headline capacities therefore cannot be added.",
        "North Bridge excludes full-size buses after deck temperature reaches 54 C until an engineer clears it. South Pass can close under smoke visibility below 150 meters. County 12 is the freight and emergency-access route and cannot be fully converted to outbound traffic.",
        "Contraflow requires a sheriff closure order, forty-five minutes of setup, and staffed crossover points. The last exercise achieved only 1,180 vehicles per hour at Mill Junction because lane merging was unmanaged.",
    ), (
        "Zone sequencing must reserve emergency inbound capacity and align bus routes with bridge restrictions from S05. Forecast and air-quality conditions can invalidate a route after the plan is checked.",
        "Clearance time must use the shared junction and exercise throughput until a current field test proves a higher candidate-bound value.",
    ), (
        "Do not sum independent road ratings across a shared downstream bottleneck.",
        "Name setup effects, route-loss contingencies, and the observation that authorizes each switch.",
    ), road_row, ("record", "route", "rated veh/h", "observed veh/h", "coupling", "status")),
    SourceSpec("S05_TRANSPORT_FLEET.md", "Evacuation fleet, accessible transport, and driver limits", "transport", (
        "Eighteen county buses exist, but only eleven qualified drivers can report within two hours. Four buses are lift-equipped; each carries two occupied wheelchairs and thirty-four seated riders in that configuration.",
        "Twelve school buses become available at 14:30, after student release. They cannot be assumed in an earlier Zone A clearance. Ambulances are reserved for clinical need and are not general mobility vehicles.",
        "Drivers have a twelve-hour duty ceiling. A route plan that uses every driver for outbound movement leaves no legal return, relief, or shelter-transfer capacity.",
    ), (
        "The no-vehicle and accessibility demand in S03 must be matched to actual vehicle/driver pairs. S04 bridge restrictions can remove standard buses from the fastest route.",
        "Fuel endurance and delayed resupply in S09 constrain repeated cycles; nominal seats are not the same as sustained evacuation throughput.",
    ), (
        "Reserve accessible capacity first, state cycle times, and preserve relief-driver capacity.",
        "Do not count unavailable school buses or unstaffed vehicles as operational capacity.",
    ), fleet_row, ("record", "vehicle", "available", "seats", "drivers", "cycle", "status")),
    SourceSpec("S06_SHELTER_CAPACITY.md", "Shelter capacity, smoke filtration, and accessibility", "shelter_care", (
        "The four sites advertise 8,200 nominal spaces, but smoke-safe staffed capacity is 5,900. Civic Arena has 48 accessible cots, Expo Hall 64, Ridge School none, and West College 32.",
        "Expo Hall's primary route crosses the South Pass smoke corridor. Ridge School does not accept pets and lacks backup filtration. Civic Arena's generator has sixteen hours of tested fuel.",
        "A shelter is usable only when staffing, filtration, backup power, sanitation, and route access are current for the same operational period. Nominal floor area is not readiness.",
    ), (
        "Medical accommodation from S07 and animal handling from S10 change effective capacity. Air-quality thresholds in S11 may require relocation after initial opening.",
        "Shelter assignment must be coupled to route and transport plans; independently feasible totals can form an infeasible combined system.",
    ), (
        "Use smoke-safe and accessible capacity, not the 8,200-space headline.",
        "Identify relocation triggers and a destination for every vulnerable cohort.",
    ), shelter_row, ("record", "site", "nominal", "smoke-safe", "accessible", "power", "status")),
    SourceSpec("S07_MEDICAL_ACCESS.md", "Medical continuity and accessibility matching", "shelter_care", (
        "Seventy-three residents use continuous oxygen, twenty-eight have dialysis due within twenty-four hours, and fourteen medications require refrigeration. The lists overlap and contain seven duplicate household records.",
        "Cedar Hospital can accept twenty-two oxygen-dependent evacuees, North Clinic thirty-seven, and verified home oxygen kits cover twenty more. Those capacities total seventy-nine only if transport, power, and patient matching all pass.",
        "A generic shelter cot is not a medical placement. Public health must bind each high-acuity person to transport, destination, power, medication custody, and handoff confirmation.",
    ), (
        "S03 defines uncertain demand, S05 constrains accessible vehicles, S06 constrains destinations, and S09 constrains power/fuel. The medical plan is a joined assignment rather than four independent capacity claims.",
        "Public status messages may not expose health needs; the private roster rules in S12 govern matching and deletion.",
    ), (
        "Require person-level private matching with aggregate public reporting.",
        "Treat any unmatched oxygen, dialysis, or refrigerated-medication case as a blocker.",
    ), care_row, ("record", "zone", "need", "people", "pickup ETA", "match", "roster")),
    SourceSpec("S08_COMMUNICATIONS.md", "Warning channels, language access, and radio interoperability", "communications", (
        "The last exercise disabled 35 percent of cellular towers for eight hours. IPAWS reached 82 percent of enrolled devices, while sirens provided no zone-specific instruction.",
        "Nine percent of households primarily use Hmong and six percent require another language or ASL relay. The current IPAWS template is only English and Spanish. Door-knock teams cover the mobile-home areas but need ninety minutes.",
        "County and volunteer-fire radios share voice but not unit identifiers until the interoperability gateway is configured and tested. A successful county-only radio check is insufficient.",
    ), (
        "Warning lead time must include translation and door-knock completion before the conservative clearance deadline. Communications failure can change the effective population departure curve in S03.",
        "The same zone revision and effective time must appear across IPAWS, radio, hotline, and field teams to avoid contradictory movement.",
    ), (
        "Use redundant channels, explicit language coverage, delivery confirmation, and a radio interoperability check.",
        "Do not treat message transmission as evidence that the intended population received or understood it.",
    ), comms_row, ("record", "channel", "language", "zone", "reach", "status", "message")),
    SourceSpec("S09_POWER_FUEL.md", "Power, fuel, and resupply continuity", "continuity", (
        "Civic Arena's generator has sixteen tested hours of fuel, radio repeaters ten, and the county bus reserve fourteen hours at the planned cycle rate. The fuel contract targets delivery within eight hours.",
        "The last regional outage delayed contracted fuel for nineteen hours because the supplier used South Pass. The plan must stage enough local fuel for at least twenty-four hours or diversify the route and supplier.",
        "Traffic signals on generator backup last eight hours. Manual intersection control needs twenty-six trained personnel, but the current roster contains eighteen.",
    ), (
        "Fuel availability constrains shelter viability, radio coverage, bus cycles, and road throughput simultaneously. It cannot be scored once as a generic resource line.",
        "A route closure in S04 can invalidate the fuel contract even if the vendor remains operational.",
    ), (
        "Use observed nineteen-hour delay rather than the eight-hour target as the continuity basis.",
        "Name local staging, alternate supplier/route, consumption checks, and replenishment triggers.",
    ), continuity_row, ("record", "asset", "endurance", "resupply", "dependency", "status")),
    SourceSpec("S10_ANIMAL_EVACUATION.md", "Household pets, livestock, and service animals", "community", (
        "Survey estimates 1,480 household pets in Zones A and B, while pet-capable shelter space is 600. Fourteen livestock trailers can move 112 large animals per cycle; the registry lists 320 in the threatened area.",
        "Service animals remain with handlers and count against neither pet shelter nor livestock capacity. Separating them is an accessibility failure.",
        "Human evacuation may not be held until every animal is moved. The animal branch needs parallel routes, overflow agreements, and a documented last-safe transport time.",
    ), (
        "Animal trailers compete with buses at Mill Junction and require different shelter destinations. Their schedule must preserve the human clearance assumptions from S03–S05.",
        "Public messaging must distinguish service animals, household pets, and livestock so capacity is not double-counted.",
    ), (
        "Provide a parallel animal plan without delaying human movement.",
        "State overflow capacity, cycles, route conflicts, and the falsifier that stops animal transport.",
    ), animal_row, ("record", "zone", "category", "count", "vehicles", "cycle", "rule")),
    SourceSpec("S11_AIR_QUALITY.md", "Smoke exposure and clean-air shelter thresholds", "hazard", (
        "Outdoor PM2.5 above 150 micrograms per cubic meter triggers relocation of unfiltered shelters. Above 250, field loading requires respiratory protection and shorter staging intervals.",
        "Ridge School failed its last filter inspection. Civic Arena and West College passed with MERV-13 filters; Expo Hall has only eighty percent of required replacement filters on site.",
        "The smoke model can make an otherwise distant shelter unusable before fire arrival. Distance from flame is not a complete shelter-safety criterion.",
    ), (
        "Shelter capacity in S06 must be recalculated under the air-quality forecast, while routes in S04 must remain viable for relocation. Medical cohorts in S07 have lower exposure tolerance.",
        "A filter replacement changes the candidate resource state and requires a current inspection, not reuse of the prior readiness check.",
    ), (
        "Bind shelter use and relocation to explicit PM2.5 and filter-status observations.",
        "Do not declare clean-air capacity from nominal building occupancy.",
    ), air_row, ("record", "zone", "PM2.5", "duration", "filter", "action")),
    SourceSpec("S12_DATA_REUNIFICATION.md", "Evacuee accountability, privacy, and reunification", "data", (
        "The operation needs household status, transport assignment, shelter check-in, and reunification contact. Medical accommodations are restricted and may not appear in the public missing-person feed.",
        "The minimum retention period is seven days after incident closure; operational rosters must be deleted within thirty days unless a legal hold applies. The last exercise retained exported spreadsheets for ninety-two days.",
        "A person may be safe but not at a county shelter. Accountability must accept verified self-evacuation without publishing a destination or health status.",
    ), (
        "Transport and shelter effects should update one private accountability record, but public reporting must use aggregated status. S07 medical matching consumes restricted fields under public-health authority.",
        "A plan mutation to identifiers, export, or retention invalidates the prior privacy check.",
    ), (
        "Specify minimum fields, access roles, reconciliation, deletion proof, and public/private separation.",
        "Do not equate shelter check-in with complete zone accountability.",
    ), data_row, ("record", "data class", "collection", "retention", "access", "status")),
    SourceSpec("S13_EXERCISE_REVIEW.md", "Full-scale exercise defects and repair evidence", "verification", (
        "Exercise Cedar-6 achieved only 1,180 vehicles per hour at Mill Junction, delayed lift-bus dispatch by ninety-six minutes, and accounted for 91 percent of households by the six-hour mark.",
        "County radio voice worked, but volunteer unit identifiers did not cross the gateway. Civic Arena opened, while Ridge School's filter test failed and fuel arrived after seventeen hours.",
        "A corrective-action spreadsheet marks several items closed based on owner attestation. Readiness requires current execution evidence for the exact plan rather than a status label.",
    ), (
        "The observed exercise values override nominal road, fleet, communications, shelter, and fuel targets until a repair is rechecked. One exercise therefore links several evidence domains.",
        "Changing the zone order or fleet roster after a repair makes the old exercise only historical evidence.",
    ), (
        "Carry every material exercise defect into the plan with owner, repair, current recheck, and blocking status.",
        "Do not count owner attestation as operational proof.",
    ), exercise_row, ("record", "defect", "zone", "delay", "status", "exercise binding")),
    SourceSpec("S14_COST_CONTRACTS.md", "Emergency contracts, cost ceilings, and procurement authority", "economics", (
        "The incident commander may authorize up to $750,000 of life-safety expenditure without board approval. The current forty-eight-hour plan is estimated at $612,000 before animal overflow and alternate fuel supply.",
        "The lowest-cost bus vendor cannot provide lift-equipped vehicles. The alternate fuel supplier costs 18 percent more but uses County 12 instead of smoke-prone South Pass.",
        "Cost optimization may not remove a hard accessibility, medical, communications, or continuity control. Costs beyond authority require escalation but do not justify silently declaring an unsafe plan ready.",
    ), (
        "Contract choices alter fleet accessibility and fuel-route resilience. They must appear in the same candidate effects and checks as the operational plan.",
        "Migration-only or incident-only costs need a retirement condition so temporary capacity does not become ungoverned standing spend.",
    ), (
        "State the cost envelope, authority, contingency, and controls that cannot be traded away.",
        "Treat price, capability, route, and activation time as a joint selection.",
    ), cost_row, ("record", "category", "units", "cost", "authority", "contract")),
    SourceSpec("S15_WEATHER_ENSEMBLE.md", "Wind-shift ensemble and forecast update cadence", "hazard", (
        "Forecasts update every ninety minutes. The base case keeps the fire north of Zone B, but 42 percent of current ensemble members shift winds after 16:00 and shorten Zone A arrival below six hours.",
        "A later update can improve the median while widening the worst-case range. The trigger uses the conservative operational envelope until field observations rule out the adverse branch.",
        "Aircraft infrared mapping can lag by two hours under smoke. Absence of a new perimeter is not proof that fire spread stopped.",
    ), (
        "Order timing in S01–S02, road viability in S04, and air quality in S11 all depend on the same forecast revision. Mixing revisions produces an incoherent plan.",
        "The verification packet must name the forecast cycle and expire it at the next update or material field observation.",
    ), (
        "Bind decisions to one forecast cycle and state expiry and adverse-branch actions.",
        "Do not cancel protective actions from a better median alone.",
    ), weather_row, ("record", "cycle", "wind", "shift probability", "arrival", "envelope")),
    SourceSpec("S16_READINESS_REVIEW.md", "Independent evacuation-readiness review", "governance", (
        "The independent review classifies the package as not ready. Open blockers are the North Bridge engineering inspection, complete driver roster, Ridge School filter repair, volunteer-radio identifier test, alternate fuel confirmation, and person-level oxygen matching.",
        "Several component dashboards are green, but they bind to different plan revisions. There is no current integrated check covering the zone order, routes, fleet, shelters, medical roster, communications, fuel, forecast, and accountability design together.",
        "Readiness requires every hard blocker resolved, effects incorporated, a current integrated exercise or justified bounded check, and incident-command acceptance. Submission or a model-authored ledger cannot create that authority.",
    ), (
        "The review is a candidate-bound evaluation of the complete system. Fixing one blocker can change routes, capacity, cost, or timing and make other evidence stale.",
        "Closure must distinguish ready, not ready, and not adjudicated. A strong partial plan should identify its blockers rather than submit as complete.",
    ), (
        "Preserve all six blockers until exact current evidence resolves them.",
        "Require effect uptake, current recheck, and independent readiness authority before closure.",
    ), readiness_row, ("record", "blocker", "severity", "owner", "check", "currency")),
)


SOURCES = {spec.filename: spec for spec in SPECS}


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        (DESTINATION / spec.filename).write_text(document(spec), encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
