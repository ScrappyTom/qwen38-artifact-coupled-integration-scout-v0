"""Materialize the fresh synthetic Solace regional-water recovery world."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task_solace" / "sources"


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


def row(spec: SourceSpec, index: int) -> tuple[str, str, str, str, str, str]:
    asset = spec.assets[index % len(spec.assets)]
    measure = spec.base_measure + ((index * 13) % 31) / 10
    status = "superseded" if index % 19 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"v{2 + index // 14}",
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
        for values in (row(spec, index) for index in range(42))
    )
    lines.extend(["", "## Decision constraints", "", *spec.constraints, ""])
    return "\n".join(lines)


SPECS = (
    SourceSpec(
        "AURORA", "AURORA_AUTHORITY.md", "Emergency authority and restoration accountability", "authority", "AUT",
        ("incident-command", "health-officer", "utility-director", "public-information"), 1.0, "approval",
        (
            "The incident commander may isolate zones and order emergency work. Only the county health officer may lift a do-not-drink order, and only after current laboratory and distribution-system verification; a utility repair or green mechanical check is not public-health authorization.",
            "Emergency procurement does not waive operator certification, chain of custody, environmental permits, access control, or fiscal review. Final closure requires the utility director to accept every declared blocker and residual risk.",
            "A handoff is valid only when the receiving lead acknowledges the same hydraulic model, treatment train, sampling plan, pump configuration, and communication version. A version mismatch blocks closure.",
        ),
        (
            "BASTION and CIPHER supply hydraulic and laboratory evidence but cannot lift health restrictions. NEXUS supplies independent readiness findings but does not execute restoration.",
            "MOSAIC owns rollback mechanics; AURORA preserves separation among detection, recommendation, authorization, execution, verification, communication, and closure.",
        ),
        ("Name who may isolate, repair, verify, reopen service, lift advisories, and close.", "Treat semantic records and candidate mutations as non-authoritative work products."),
    ),
    SourceSpec(
        "BASTION", "BASTION_HYDRAULICS.md", "Hydraulic pressure, storage, and zone isolation evidence", "hydraulics", "HYD",
        ("north-zone", "south-zone", "ridge-tank", "valve-grid"), 42.0, "psi",
        (
            "Current minimum distribution pressure is 42 psi in the north zone. The restoration gate is at least 35 psi at every critical node for three consecutive thirty-minute windows; 42 psi must not be converted to 42 kPa or treated as proof of water quality.",
            "Ridge storage contains 5.8 million gallons, while the twelve-hour emergency reserve is 3.2 million gallons. Stored volume and usable treated reserve are different controls.",
            "A valve map, pump curve, demand allocation, or zone-boundary change makes earlier pressure and residence-time checks stale for the changed candidate.",
        ),
        (
            "DELTA pump sequencing depends on BASTION pressure and ECHO power. CIPHER sampling locations must follow the current BASTION flow paths.",
            "MOSAIC rollback is allowed only while the prior valve map remains valid and a current BASTION pressure check passes for the rollback candidate.",
        ),
        ("Preserve psi, gallons, the three-window rule, and candidate currency.", "Distinguish hydraulic service from microbiological and chemical clearance."),
    ),
    SourceSpec(
        "CIPHER", "CIPHER_LAB.md", "Laboratory sampling, detection limits, and clearance evidence", "laboratory", "LAB",
        ("entry-point", "north-grid", "south-grid", "hospital-loop"), 0.0, "positive-samples",
        (
            "The current confirmatory set has zero E. coli positives across forty-eight samples. Clearance requires two complete rounds at least sixteen hours apart; one clean round is insufficient.",
            "The benzene reporting limit is 0.5 micrograms per liter and the action threshold is 5.0 micrograms per liter. The reporting limit is not the action threshold and neither is a percent concentration.",
            "A flow-path, disinfectant-dose, source-water, sampling-plan, or laboratory-method change makes prior samples stale for the changed candidate.",
        ),
        (
            "CIPHER sample placement consumes BASTION flow paths and GARNET contamination hypotheses. HELIX governs chain of custody and laboratory access.",
            "AURORA consumes current CIPHER findings for advisory decisions; CIPHER does not itself authorize public restoration.",
        ),
        ("Preserve rounds, spacing, sample count, detection limit, action threshold, and staleness.", "State what negative result would falsify clearance and trigger renewed isolation."),
    ),
    SourceSpec(
        "DELTA", "DELTA_PUMPS.md", "Pump capacity, sequencing, and cavitation constraints", "pumping", "PMP",
        ("pump-1", "pump-2", "booster-east", "booster-west"), 18.0, "million-gallons-day",
        (
            "The treatment works can supply 18 million gallons per day, but the shared transmission main is capped at 14.5 MGD. Pump nameplate capacities cannot be summed into usable system flow.",
            "The latest inspected configuration sustained 12.8 MGD after fire-flow and hospital reserve. A higher stage requires a current candidate-bound pump and pressure test.",
            "Restoration may advance through 10, 30, 60, and 100 percent demand stages only after two thirty-minute windows meet pressure, turbidity, power, and storage gates.",
        ),
        (
            "BASTION supplies pressure limits, ECHO supplies feeder headroom, and FALCON supplies treatment output. All three constrain DELTA sequencing.",
            "A pump, valve, main allocation, generator, or treatment-train change makes prior capacity evidence stale.",
        ),
        ("Preserve shared capacity, observed flow, stage sequence, windows, and stale conditions.", "Do not infer public-health clearance from hydraulic capacity."),
    ),
    SourceSpec(
        "ECHO", "ECHO_POWER.md", "Grid, generator, and fuel continuity", "power", "PWR",
        ("substation-a", "substation-b", "generator-1", "fuel-yard"), 6.5, "megawatts",
        (
            "The grid feed is rated at 8.2 MW, but the damaged switchgear limits current delivery to 6.5 MW. Rating and currently usable power must not be swapped.",
            "Emergency generation can carry 4.1 MW for thirty-six hours at the current fuel stock. The duration is not thirty-six days and excludes mobile-pump load.",
            "Automatic transfer succeeded in the latest drill, but the observation predates switchgear version SW-9 and is stale for the current candidate.",
        ),
        (
            "DELTA pump stages and FALCON treatment trains compete for ECHO capacity. KESTREL fuel delivery controls generator duration.",
            "INDIGO telemetry is required to validate voltage and transfer stability; a control-room display alone is insufficient.",
        ),
        ("Separate rated, usable, generated, and reserved power with exact durations.", "Name current tests for transfer, load shedding, fuel replenishment, and rollback."),
    ),
    SourceSpec(
        "FALCON", "FALCON_TREATMENT.md", "Treatment barriers, disinfectant, and turbidity controls", "treatment", "TRT",
        ("clarifier", "filter-bank", "chlorine-contact", "uv-train"), 0.18, "ntu",
        (
            "Current combined-filter turbidity is 0.18 NTU. The release gate is at or below 0.30 NTU for four hours; 0.18 NTU is not a chlorine residual.",
            "Free chlorine must remain between 0.8 and 2.0 milligrams per liter at entry points and at least 0.2 mg/L in distribution. Entry and distribution thresholds are different controls.",
            "Filter media, coagulant dose, source-water blend, contact time, or UV configuration changes stale prior treatment verification.",
        ),
        (
            "GARNET source-water findings set FALCON treatment assumptions. BASTION residence time and CIPHER sampling determine whether treated water evidence applies downstream.",
            "DELTA demand ramps cannot outrun FALCON verified capacity or required disinfectant contact time.",
        ),
        ("Preserve NTU, mg/L, locations, duration, and barrier dependencies.", "State pause, rollback, and evidence needed to retire temporary treatment controls."),
    ),
    SourceSpec(
        "GARNET", "GARNET_SOURCE.md", "Source-water contamination hypotheses and watershed controls", "source_water", "SRC",
        ("river-intake", "reservoir", "ash-plume", "chemical-yard"), 3.4, "risk-index",
        (
            "The ash-plume model assigns a 34 percent chance of intake impact during the next rain event. That is a forecast probability, not 34 percent measured contamination.",
            "Observed volatile-organic screening is non-detect at the reservoir and 3.1 micrograms per liter at the river intake. The two locations must not be merged.",
            "The investigation hold remains active for the chemical yard because the containment trench has not been inspected below grade.",
        ),
        (
            "FALCON treatment selection depends on GARNET source hypotheses; CIPHER must sample each materially different source path.",
            "JASPER governs environmental notifications, while AURORA retains restoration and public-health authority separation.",
        ),
        ("Preserve forecast versus observation, percent versus concentration, and location.", "Keep the investigation hold until named inspection and sampling evidence retires it."),
    ),
    SourceSpec(
        "HELIX", "HELIX_SECURITY.md", "Access, control-system integrity, and evidence custody", "security", "SEC",
        ("scada-token", "operator-role", "lab-chain", "audit-log"), 2.0, "hours",
        (
            "The exposed SCADA service token was revoked at 14:10 UTC. The controller signing key was not exposed and remains current under key-set version W4.",
            "Break-glass access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.",
            "Online control logs are retained for ninety days and archived incident evidence for seven years; the periods serve different obligations.",
        ),
        (
            "AURORA governs emergency authority and MOSAIC binds rollback to the current key set. INDIGO consumes HELIX audit events but does not authorize access.",
            "Any key-set, role-policy, controller, or logging mutation makes prior security verification stale.",
        ),
        ("Distinguish token revocation, key status, access duration, approvals, and retention.", "Name current evidence required before restoring remote automation."),
    ),
    SourceSpec(
        "INDIGO", "INDIGO_TELEMETRY.md", "Telemetry coverage, alerts, and observation quality", "observability", "OBS",
        ("pressure", "turbidity", "power", "chlorine"), 96.0, "percent-coverage",
        (
            "Current critical-signal coverage is 96 percent; four percent remains unobserved. Coverage is not confidence and does not prove healthy uninstrumented zones.",
            "The warning threshold for pressure is 38 psi and the isolation trigger is 30 psi. Warning and action thresholds must remain distinct.",
            "Telemetry delay is 700 milliseconds at p95 and 1,200 milliseconds at p99. Both are observations, not control deadlines.",
        ),
        (
            "BASTION, DELTA, ECHO, and FALCON rely on INDIGO observations, but each domain retains its own decision gate.",
            "LUMEN communications may report measured service only where INDIGO coverage and source currency are adequate.",
        ),
        ("Preserve coverage, uncertainty, threshold purpose, percentiles, and units.", "Define alternate observation routes and evidence for retiring manual watches."),
    ),
    SourceSpec(
        "JASPER", "JASPER_ENVIRONMENT.md", "Environmental permits, discharge, and reporting", "environment", "ENV",
        ("river", "wetland", "ash-basin", "dechlorination"), 72.0, "hours",
        (
            "A material unauthorized discharge requires initial notice within seventy-two hours of determination, not seventy-two minutes after detection.",
            "Emergency dechlorination may proceed under permit condition E-17, but residual above 0.019 milligrams per liter at the outfall requires an immediate stop.",
            "Determination evidence, notices, candidate changes, checks, and closure records must be retained for seven years with access provenance.",
        ),
        (
            "GARNET supplies source-impact evidence and FALCON supplies treatment discharge conditions. LUMEN supplies notice delivery records.",
            "AURORA owns materiality determination; a semantic source record cannot make the legal determination.",
        ),
        ("Preserve the determination event, clock, permit, threshold, unit, and custody.", "State unknowns and exact evidence that can change reportability."),
    ),
    SourceSpec(
        "KESTREL", "KESTREL_LOGISTICS.md", "Fuel, chemicals, staffing, and mutual-aid logistics", "logistics", "LOG",
        ("diesel", "chlorine", "operators", "mobile-tankers"), 36.0, "hours-cover",
        (
            "Current diesel stock covers thirty-six hours at emergency load and twenty-two hours at full pump load. The two consumption regimes must remain distinct.",
            "Coagulant stock covers 4.5 days at the current source blend, while chlorine covers 3.2 days. Inventory duration is not delivery lead time.",
            "Mutual aid provides six certified operators beginning at 06:00 UTC; travel uncertainty is plus or minus ninety minutes.",
        ),
        (
            "ECHO generator duration depends on KESTREL fuel; FALCON treatment staging depends on chemical stock; DELTA depends on certified staffing.",
            "LUMEN publishes public tanker locations only after AURORA and HELIX approve safety and access controls.",
        ),
        ("Preserve load regime, stock type, days versus hours, staffing time, and uncertainty.", "Name reorder triggers, alternates, owner, and retirement evidence."),
    ),
    SourceSpec(
        "LUMEN", "LUMEN_PUBLIC.md", "Public warnings, accessibility, and customer continuity", "communications", "COM",
        ("sms", "radio", "clinics", "schools"), 91.0, "percent-delivered",
        (
            "Do-not-drink notices reached 91 percent of registered endpoints; the missing nine percent is communication uncertainty, not a nine-percent reduction in affected population.",
            "Public states must distinguish do-not-use, do-not-drink, boil-water, restricted service, and cleared. Low pressure does not by itself establish contamination.",
            "The call center can sustain 3,200 contacts per hour for six hours. Forecast demand is 4,100 per hour unless alternate-language outreach reduces repeat calls.",
        ),
        (
            "CIPHER and AURORA determine advisory status; INDIGO and BASTION supply service observations. HELIX constrains publication of sensitive infrastructure details.",
            "JASPER supplies mandatory environmental language and KESTREL supplies verified alternate-water locations.",
        ),
        ("Preserve delivery coverage, state vocabulary, capacity, forecast, accessibility, and privacy.", "State owners, channels, timing, acknowledgments, alternates, and retirement evidence."),
    ),
    SourceSpec(
        "MOSAIC", "MOSAIC_CHANGE.md", "Candidate lineage, rollback, and configuration control", "change_control", "CHG",
        ("hydraulic-model", "pump-plan", "treatment-plan", "key-set"), 7.0, "candidate-index",
        (
            "The current recovery candidate is W7 with hydraulic model H12, pump plan P9, treatment plan T6, and key set W4. Evidence for W6 is historical unless explicitly transferred and rechecked.",
            "Rollback to W6 is mechanically possible only while valve map V8 and controller firmware C11 remain compatible. Mechanical possibility is not authorization.",
            "Every mutation must record before and after candidate hashes, changed files, affected evidence, check currency, owner, and rollback effect.",
        ),
        (
            "BASTION, CIPHER, DELTA, ECHO, FALCON, and HELIX observations can become stale after MOSAIC candidate changes.",
            "NEXUS reviews current-candidate evidence independently; AURORA authorizes execution and closure separately.",
        ),
        ("Keep candidate, model, pump, treatment, key, valve, and firmware versions explicit.", "Require effect uptake, current check, repair, recheck, and rollback evidence."),
    ),
    SourceSpec(
        "NEXUS", "NEXUS_READINESS.md", "Independent readiness review, blockers, and falsifiers", "readiness", "RDY",
        ("hydraulic", "quality", "power", "public-health"), 16.0, "open-findings",
        (
            "The latest independent review found sixteen open findings: five hydraulic, four treatment, three sampling, two power, and two communication. A finding count is not a readiness percentage.",
            "Blocking findings include incomplete second-round samples, stale generator transfer evidence, and missing acknowledgment from the public-health duty officer.",
            "Readiness requires current candidate-bound evidence for every blocking control, independent review of residual risk, and explicit acceptance by the authorized owner.",
        ),
        (
            "NEXUS consumes evidence from AURORA, BASTION, CIPHER, ECHO, FALCON, HELIX, INDIGO, LUMEN, and MOSAIC but does not mutate their states.",
            "An artifact, semantic register, mechanical check, or submission proposal cannot self-authorize readiness.",
        ),
        ("List blockers, falsifiers, residual risks, owners, current evidence, and acceptance.", "Keep independent review separate from execution, communication, and closure authority."),
    ),
)

SOURCE_IDS = tuple(spec.source_id for spec in SPECS)


def main() -> int:
    DESTINATION.mkdir(parents=True, exist_ok=True)
    for spec in SPECS:
        path = DESTINATION / spec.filename
        path.write_text(document(spec), encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
