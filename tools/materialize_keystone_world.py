"""Materialize the fresh synthetic Keystone rail-restoration world."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task_keystone" / "sources"


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
    measure = spec.base_measure + ((index * 19) % 31) / 10
    status = "superseded" if index % 19 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"v{4 + index // 11}",
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
        "| record | asset/zone | version | measure | unit | status |",
        "|---|---|---|---:|---|---|",
    ]
    lines.extend(
        "| " + " | ".join(values) + " |"
        for values in (_row(spec, index) for index in range(64))
    )
    lines.extend(["", "## Decision constraints", "", *spec.constraints, ""])
    return "\n".join(lines)


SPECS = (
    SourceSpec(
        "MANDATE", "MANDATE_AUTHORITY.md", "Restoration authority and operating states", "authority", "AUT",
        ("incident-command", "rail-safety", "network-control", "public-liaison"), 1.0, "approval",
        (
            "The incident commander may isolate infrastructure and order emergency stabilization. Only network control may authorize an engineering movement, and only the rail-safety director may authorize passenger service after current track, signal, traction-power, rolling-stock, and crew evidence is reconciled.",
            "A successful automated check is neither an engineering-movement authority nor passenger-service authority. Emergency procurement does not waive inspection, route proving, hours-of-service, hazardous-material, accessibility, or evidence-custody obligations.",
            "A handoff is valid only when the receiving controller acknowledges the same route topology, interlocking build, traction-power map, consist roster, and candidate version. A version mismatch blocks closure.",
        ),
        (
            "TRACK, SIGNAL, POWER, ROLLING, and CREW provide evidence but cannot authorize passenger service; REVIEW provides independent readiness findings but cannot dispatch a train.",
            "LINEAGE binds candidate state while MANDATE separates stabilization, engineering movement, freight movement, passenger service, and closure.",
        ),
        ("Name who may isolate, inspect, verify, dispatch, restore passenger service, and close.", "Treat semantic records and artifact mutations as non-authoritative work products."),
    ),
    SourceSpec(
        "TRACK", "TRACK_GEOMETRY.md", "Track geometry, inspection, and route restrictions", "track", "TRK",
        ("north-main", "river-bridge", "yard-lead", "tunnel-approach"), 3.0, "millimeters",
        (
            "The current north-main alignment deviation is 3.2 millimeters. The passenger-service gate is no more than 4.0 millimeters in two consecutive geometry runs; one 3.2-millimeter run is insufficient.",
            "River-bridge speed is limited to 25 miles per hour until ultrasonic inspection and bearing-temperature evidence are current. Twenty-five is a speed limit, not a probability or inspection count.",
            "A rail replacement, tamping operation, bridge bearing adjustment, sensor calibration, or route-topology change makes earlier geometry evidence stale for the changed candidate.",
        ),
        (
            "SIGNAL route proving consumes TRACK topology, while WEATHER and LOADS constrain speed and axle restrictions.",
            "LINEAGE records every physical mutation; REVIEW requires current candidate-bound evidence for both geometry runs.",
        ),
        ("Preserve observed deviation, gate, run count, speed unit, and candidate currency.", "Bind restrictions to falsifiers, rollback, and evidence that retires them."),
    ),
    SourceSpec(
        "SIGNAL", "SIGNAL_INTERLOCKING.md", "Interlocking, route proving, and crossing logic", "signaling", "SIG",
        ("interlocking-7", "crossing-12", "block-4", "dispatcher-link"), 99.0, "percent-tests",
        (
            "The current interlocking suite passed 99.2 percent of test vectors. The service gate requires 100 percent of safety-critical vectors and two consecutive route-proving trains; 99.2 percent is not a probability of safety.",
            "Crossing 12 warning time is 27 seconds against a minimum of 25 seconds. The observed 27 seconds does not replace the two-train route-proving requirement.",
            "A logic build, route table, crossing controller, axle-counter reset, or dispatcher-link change makes prior signal evidence stale.",
        ),
        (
            "TRACK supplies route topology, CYBER supplies signed build custody, and TELEMETRY supplies current event delivery; none authorizes service alone.",
            "MANDATE assigns movement authority and LINEAGE binds the exact interlocking build to the candidate.",
        ),
        ("Preserve percent versus probability, critical-vector completeness, train count, seconds, and staleness.", "State the fail-safe route and evidence required before removing manual protection."),
    ),
    SourceSpec(
        "POWER", "POWER_TRACTION.md", "Traction power, substations, and emergency supply", "power", "PWR",
        ("substation-east", "substation-west", "feeder-3", "backup-plant"), 31.0, "megawatts",
        (
            "Installed traction capacity is 34.0 megawatts, while current usable capacity after feeder derating is 26.5 megawatts. Installed and usable capacity must not be swapped or added together.",
            "Feeder voltage is 24.7 kilovolts and must remain between 24.0 and 25.2 kilovolts at every monitored node for three consecutive fifteen-minute windows. An average cannot replace every-node compliance.",
            "The backup plant carries 11.8 megawatts for eighteen hours at current fuel stock; it does not carry full passenger peak and eighteen hours is not eighteen days.",
        ),
        (
            "TRACK work windows and ROLLING consist demand depend on POWER; FUEL controls backup duration and TELEMETRY validates node voltage.",
            "A feeder, transformer, relay, fuel stock, or service-load change makes prior power evidence stale.",
        ),
        ("Preserve installed versus usable MW, kV range, every-node rule, duration, and exclusions.", "Define load stages, rollback, replenishment, and current verification."),
    ),
    SourceSpec(
        "ROLLING", "ROLLING_STOCK.md", "Rolling stock, braking, and consist readiness", "rolling_stock", "RST",
        ("emu-14", "emu-18", "rescue-loco", "brake-rig"), 88.0, "percent-available",
        (
            "Fourteen of sixteen electric multiple units passed static inspection. Passenger restoration requires fourteen available units plus one independently verified rescue locomotive; fourteen units alone are insufficient.",
            "Brake-pipe pressure is 72 psi against a required range of 68 to 76 psi. Seventy-two psi is an observation, not a readiness percentage.",
            "A wheelset, brake controller, consist, firmware, inspection method, or rescue-locomotive change makes earlier rolling-stock evidence stale.",
        ),
        (
            "POWER constrains consist demand, TRACK constrains axle and speed limits, and CREW constrains qualified operators.",
            "LINEAGE binds each inspected consist and REVIEW requires current rescue capability before passenger service.",
        ),
        ("Preserve unit count, rescue prerequisite, psi observation/range, and currentness.", "Name quarantine, substitution, retest, rollback, and release evidence."),
    ),
    SourceSpec(
        "CREW", "CREW_QUALIFICATION.md", "Crew qualification, fatigue, and staffing", "crew", "CRW",
        ("engineers", "conductors", "signal-techs", "power-techs"), 9.0, "hours-on-duty",
        (
            "Current qualified coverage is twelve engineers and ten conductors. The first passenger stage requires ten engineers, ten conductors, two signal technicians, and two traction-power technicians on duty simultaneously.",
            "No operating crew member may exceed twelve hours on duty and each must receive at least ten consecutive hours off before the next covered shift. Twelve on duty and ten off serve different rules.",
            "Mutual aid supplies four engineers at 06:15 UTC with arrival uncertainty of plus or minus fifty minutes; announced availability is not confirmed on-duty coverage.",
        ),
        (
            "ROLLING service requires qualified engineers and conductors; SIGNAL and POWER restrictions require their specialist technicians.",
            "COMMS distributes assignments, while MANDATE retains operating authority and REVIEW checks current rosters.",
        ),
        ("Preserve roles, simultaneous counts, on/off-duty hours, start time, and uncertainty.", "State alternates, fatigue stop rules, and evidence that retires mutual-aid dependence."),
    ),
    SourceSpec(
        "WEATHER", "WEATHER_SLOPE.md", "Weather, slope stability, and operating envelopes", "weather", "WTH",
        ("ridge-cut", "river-bridge", "tunnel-east", "north-main"), 14.0, "millimeters-hour",
        (
            "Rainfall at ridge-cut is 14 millimeters per hour. A geotechnical watch begins above 16 mm/h and operations stop above 24 mm/h; watch and stop thresholds must remain distinct.",
            "River crosswind is 42 miles per hour at p95. Passenger service is restricted above 50 mph, while empty-stock movement is restricted above 58 mph.",
            "A slope repair, drainage change, sensor move, forecast model, or operating-consist change makes prior weather-envelope evidence stale.",
        ),
        (
            "TRACK restrictions consume slope and rainfall evidence; ROLLING consist type determines the applicable crosswind gate.",
            "TELEMETRY provides observations but WEATHER owns threshold interpretation and MANDATE owns service decisions.",
        ),
        ("Preserve observed versus watch/stop values, units, percentiles, and consist-specific gates.", "Define alternate monitoring, rollback, and evidence needed to retire watches."),
    ),
    SourceSpec(
        "FUEL", "FUEL_MATERIALS.md", "Fuel, spares, and logistics continuity", "logistics", "FUL",
        ("diesel", "switch-machines", "sand", "bus-bridges"), 18.0, "hours-cover",
        (
            "Backup-plant fuel covers eighteen hours at emergency traction load and eleven hours at full passenger peak. The two consumption regimes must remain distinct.",
            "Replacement switch machines cover 3.5 route-days, while traction sand covers 2.4 operating days. Route-days and operating days are different inventory measures.",
            "Six accessible buses arrive at 07:10 UTC with travel uncertainty of plus or minus forty minutes; planned arrival is not deployed capacity.",
        ),
        (
            "POWER backup duration depends on FUEL, SIGNAL depends on switch machines, and PASSENGER depends on accessible bus bridging.",
            "WEATHER may alter logistics routes and CREW must qualify receiving and installation teams.",
        ),
        ("Preserve load regime, inventory units, arrival time, uncertainty, and qualification.", "Name reorder triggers, alternates, owners, and retirement evidence."),
    ),
    SourceSpec(
        "CYBER", "CYBER_CONTROL.md", "Control access, signing, and audit custody", "cybersecurity", "CYB",
        ("service-account", "logic-signing", "dispatch-api", "audit-store"), 2.0, "hours-access",
        (
            "The exposed dispatch service account was disabled at 11:25 UTC. The interlocking-signing key was not exposed and remains current under key set K12.",
            "Break-glass control access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.",
            "Online controller logs are retained for 210 days and archived investigation evidence for six years; the periods serve different obligations.",
        ),
        (
            "SIGNAL and POWER require CYBER-validated control access; TELEMETRY consumes audit events but cannot authorize access.",
            "Any key-set, role-policy, controller, route-table, or logging mutation makes prior cyber verification stale.",
        ),
        ("Distinguish account disablement, key state, access duration, approval, and retention.", "Name current evidence required before restoring remote dispatch control."),
    ),
    SourceSpec(
        "TELEMETRY", "TELEMETRY_COVERAGE.md", "Monitoring coverage, alarms, and delivery latency", "observability", "TEL",
        ("track-circuits", "voltage", "wind", "brakes"), 93.0, "percent-coverage",
        (
            "Current critical-signal coverage is 93 percent; seven percent remains unobserved. Coverage is not confidence and does not prove uninstrumented assets healthy.",
            "Route-state delivery is 720 milliseconds at p95 and 1,180 milliseconds at p99. These are observations, not response deadlines.",
            "The power warning threshold is 24.2 kilovolts and the operating stop is 23.8 kilovolts. Warning and stop semantics must remain distinct.",
        ),
        (
            "TRACK, SIGNAL, POWER, ROLLING, and WEATHER rely on TELEMETRY observations while retaining their own gates and authorities.",
            "COMMS may report state only where coverage and source currency are adequate.",
        ),
        ("Preserve coverage uncertainty, percentile latency, voltage, purpose, and currentness.", "Define alternate observation routes and evidence for retiring manual watches."),
    ),
    SourceSpec(
        "LOADS", "LOADS_FREIGHT.md", "Freight, hazardous materials, and axle restrictions", "freight", "LOD",
        ("hazmat-71", "grain-22", "intermodal-9", "bridge-axle"), 20.0, "tonnes-axle",
        (
            "River-bridge temporary axle load is limited to 20.5 tonnes. The normal 23.0-tonne rating is suspended and cannot govern the current candidate.",
            "Hazardous-material consist H71 requires a 600-meter separation from passenger platforms and an independent route clearance before movement.",
            "A consist, axle map, bridge inspection, route, cargo classification, or separation-plan change makes earlier freight clearance stale.",
        ),
        (
            "TRACK supplies bridge and route state, SIGNAL supplies route locking, and MANDATE separates freight from passenger authority.",
            "PASSENGER plans must preserve H71 separation and COMMS must not disclose protected cargo details.",
        ),
        ("Preserve current versus suspended load, tonnes, separation distance, and currentness.", "Name quarantine siding, alternate route, owners, and clearance evidence."),
    ),
    SourceSpec(
        "PASSENGER", "PASSENGER_CONTINUITY.md", "Passenger continuity, accessibility, and communication", "passenger", "PSG",
        ("alerts", "stations", "bus-bridge", "call-center"), 86.0, "percent-acknowledged",
        (
            "Service restrictions reached 86 percent of subscribed riders; the missing fourteen percent is communication uncertainty, not a fourteen-percent reduction in affected riders.",
            "The call center sustains 1,600 contacts per hour for three hours. Forecast demand is 2,100 per hour unless multilingual outbound notices reduce repeat contacts.",
            "Public states must distinguish suspended service, engineering movement, freight movement, limited passenger service, full service, and closure.",
        ),
        (
            "MANDATE determines authorized service language; TELEMETRY supplies measured state, FUEL supplies bus capacity, and CYBER constrains sensitive details.",
            "LOADS supplies hazardous-material separation requirements and CREW supplies confirmed staffing.",
        ),
        ("Preserve acknowledgment coverage, state vocabulary, capacity, duration, forecast, and accessibility.", "State owners, channels, timing, acknowledgments, alternates, and retirement evidence."),
    ),
    SourceSpec(
        "LINEAGE", "LINEAGE_CONFIGURATION.md", "Candidate lineage, rollback, and configuration control", "change_control", "LIN",
        ("route-topology", "interlocking-build", "power-map", "consist-roster"), 12.0, "candidate-index",
        (
            "The current restoration candidate is K12 with route topology T8, interlocking build I17, traction-power map P6, consist roster C14, and key set K12. Evidence for K11 is historical unless explicitly transferred and rechecked.",
            "Rollback to K11 is mechanically possible only while route table R5 and controller firmware F21 remain compatible. Mechanical possibility is not authorization.",
            "Every mutation must record before and after candidate hashes, changed artifacts, affected evidence, check currency, owner, and rollback effect.",
        ),
        (
            "TRACK, SIGNAL, POWER, ROLLING, CYBER, TELEMETRY, and LOADS observations can become stale after LINEAGE candidate mutations.",
            "REVIEW evaluates current-candidate evidence independently; MANDATE authorizes movement, service, and closure separately.",
        ),
        ("Keep route, interlocking, power, consist, key, table, and firmware versions explicit.", "Require effect uptake, current check, repair, recheck, and rollback evidence."),
    ),
    SourceSpec(
        "REVIEW", "REVIEW_READINESS.md", "Independent readiness review and blockers", "readiness", "REV",
        ("track", "signal", "power", "operations"), 11.0, "open-findings",
        (
            "The latest independent review found eleven open findings: three track, three signal, two power, two rolling-stock, and one passenger-continuity finding. A finding count is not a readiness percentage.",
            "Blocking findings include the second geometry run, second route-proving train, stale backup-transfer evidence, rescue-locomotive verification, and missing rail-safety acknowledgment.",
            "Readiness requires current candidate-bound evidence for every blocking control, independent residual-risk review, and explicit acceptance by each authorized owner.",
        ),
        (
            "REVIEW consumes evidence from MANDATE, TRACK, SIGNAL, POWER, ROLLING, CREW, WEATHER, CYBER, TELEMETRY, PASSENGER, and LINEAGE but does not mutate their states.",
            "An artifact, semantic register, mechanical check, or submission proposal cannot self-authorize movement, passenger service, or closure.",
        ),
        ("List blockers, falsifiers, residual risks, owners, current evidence, and acceptance.", "Keep review separate from execution, movement authority, public communication, and closure."),
    ),
)


SOURCE_IDS = tuple(spec.source_id for spec in SPECS)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        (DESTINATION / spec.filename).write_text(
            document(spec), encoding="utf-8", newline=""
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
