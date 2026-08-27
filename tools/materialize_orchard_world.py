"""Materialize the fresh synthetic Orchard biologics-restart world."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "task_orchard" / "sources"


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
    measure = spec.base_measure + ((index * 17) % 29) / 10
    status = "superseded" if index % 17 == 0 else "current"
    return (
        f"{spec.prefix}-{index:03d}",
        asset,
        f"v{3 + index // 12}",
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
        "CHARTER", "CHARTER_AUTHORITY.md", "Restart authority and accountable disposition", "authority", "AUT",
        ("incident-lead", "quality-unit", "site-head", "regulatory-liaison"), 1.0, "approval",
        (
            "The incident lead may isolate equipment and order emergency stabilization. Only the independent quality unit may release a manufactured lot, and only the site head may authorize commercial restart after current quality, aseptic, utility, and cyber evidence is reconciled.",
            "Emergency procurement does not waive validated methods, operator qualification, chain of custody, environmental permits, data-integrity controls, or deviation review. A successful mechanical check is not lot release or commercial restart authority.",
            "A handoff is valid only when the receiving lead acknowledges the same batch genealogy, fill-line configuration, cold-chain map, utility state, and control-system version. A version mismatch blocks closure.",
        ),
        (
            "ASSAY and STERILE provide release evidence but cannot authorize release; REVIEW provides independent readiness findings but cannot execute restart.",
            "CHANGE binds candidate lineage while CHARTER preserves separation among stabilization, execution, verification, release, restart authorization, and closure.",
        ),
        ("Name who may isolate, repair, verify, release a lot, restart operations, and close.", "Treat semantic records and candidate mutations as non-authoritative work products."),
    ),
    SourceSpec(
        "CULTURE", "CULTURE_PROCESS.md", "Bioreactor state, yield, and hold-time evidence", "process", "BIO",
        ("reactor-a", "reactor-b", "harvest-tank", "transfer-loop"), 72.0, "percent-yield",
        (
            "The current engineering batch achieved 72 percent yield. The restart gate is at least 68 percent yield in two consecutive engineering batches; one 72 percent batch is insufficient.",
            "Harvest hold time is limited to six hours at 2 to 8 degrees Celsius. Six hours is not the downstream twelve-hour formulated-bulk limit.",
            "A media lot, inoculum, control recipe, reactor sensor, transfer path, or hold vessel change makes earlier process evidence stale for the changed candidate.",
        ),
        (
            "ASSAY disposition consumes CULTURE genealogy and results; CURRENT utilities and SIGNAL observations constrain whether CULTURE evidence remains applicable.",
            "CHANGE records every recipe and equipment mutation; REVIEW requires current candidate-bound evidence for both consecutive batches.",
        ),
        ("Preserve yield, consecutive-batch count, temperature, hold time, and candidate currency.", "Distinguish process performance from lot release and commercial restart."),
    ),
    SourceSpec(
        "STERILE", "STERILE_ASEPTIC.md", "Aseptic processing and contamination-control evidence", "aseptic", "ASP",
        ("filling-line", "isolator", "transfer-port", "environmental-zone"), 0.0, "cfu",
        (
            "The latest media fill found zero contaminated units across 9,600 filled units. Clearance requires three consecutive successful media fills; one clean run is insufficient.",
            "The action limit is 1 CFU per cubic meter in Grade A active air, while the alert limit is 3 CFU per plate in the adjacent Grade B settle test. The locations, units, and limit types must not be interchanged.",
            "A glove, transfer port, sterilization cycle, filling path, viable-air method, or environmental-monitoring plan change makes earlier aseptic evidence stale.",
        ),
        (
            "CULTURE provides batch genealogy, ASSAY consumes sterility evidence, and GUARD constrains validated access to the filling controller.",
            "CHARTER assigns release authority; STERILE findings alone cannot authorize lot release or restart.",
        ),
        ("Preserve units, locations, alert/action meaning, fill count, run count, and staleness.", "State the falsifier that stops filling and reopens investigation."),
    ),
    SourceSpec(
        "CHILL", "CHILL_COLD_CHAIN.md", "Cold-chain mapping, excursion, and disposition", "cold_chain", "CLD",
        ("freezer-1", "freezer-2", "shipping-lane", "staging-room"), -70.0, "degrees-celsius",
        (
            "Frozen drug substance is stored at minus 70 degrees Celsius with an allowed range of minus 80 to minus 60 degrees Celsius. Minus 20 degrees is not an acceptable frozen-drug-substance set point.",
            "The observed lane-4 excursion was minus 54 degrees Celsius for twenty-two minutes. Disposition requires product-specific stability review; duration alone neither releases nor rejects the material.",
            "A probe, logger, pallet map, shipping lane, freezer controller, or packaging configuration change makes prior mapping evidence stale.",
        ),
        (
            "ASSAY owns product disposition evidence, SUPPLY owns lane and packaging availability, and SIGNAL owns current alarm delivery evidence.",
            "CHANGE binds the evaluated packaging and controller versions; CHARTER retains release authority separation.",
        ),
        ("Preserve signs, ranges, duration, lane, product-specific review, and currentness.", "Name quarantine, alternate storage, remapping, and evidence needed to retire temporary controls."),
    ),
    SourceSpec(
        "CURRENT", "CURRENT_UTILITIES.md", "Clean utilities, power, and capacity", "utilities", "UTL",
        ("wfi-loop", "clean-steam", "substation", "generator"), 84.0, "percent-load",
        (
            "The water-for-injection loop is at 82 degrees Celsius and requires at least 80 degrees at every return point for three consecutive thirty-minute windows. Average temperature cannot substitute for every-point compliance.",
            "Usable electrical service is 5.4 MW after switchgear derating, while the installed rating is 7.1 MW. Rated and currently usable capacity must not be swapped or added together.",
            "Emergency generation carries 3.2 MW for twenty-eight hours at current fuel stock. The duration is not twenty-eight days and excludes the lyophilizer start transient.",
        ),
        (
            "CULTURE and STERILE depend on CURRENT clean utilities; SUPPLY fuel controls generator duration and SIGNAL validates return temperatures and transfer stability.",
            "A loop balance, sensor, switchgear, generator, or production-load change makes prior utility evidence stale.",
        ),
        ("Preserve every-point versus average gates, MW meanings, duration, exclusions, and staleness.", "Define load stages, rollback, fuel replenishment, and current verification."),
    ),
    SourceSpec(
        "ASSAY", "ASSAY_QUALITY.md", "Analytical results, specification, and lot disposition", "quality", "QLT",
        ("potency", "sterility", "endotoxin", "identity"), 91.0, "percent-potency",
        (
            "Current potency is 91 percent of reference with an approved specification of 85 to 115 percent. Ninety-one percent is an observation, not a probability of passing.",
            "Endotoxin is 0.18 EU per milliliter against a limit of not more than 0.25 EU/mL. A legacy 0.50 EU/mL method is superseded and cannot govern current release.",
            "Method, reference standard, sample plan, batch genealogy, cold-chain disposition, or candidate change makes prior analytical disposition stale.",
        ),
        (
            "CULTURE and STERILE supply genealogy and contamination controls; CHILL supplies excursion evidence. CHARTER assigns independent release authority.",
            "REVIEW may identify blockers but neither REVIEW nor a passing automated check releases a lot.",
        ),
        ("Preserve observation versus probability, specification range, EU/mL limits, and supersession.", "Bind every release recommendation to exact methods, samples, genealogy, and current candidate."),
    ),
    SourceSpec(
        "GUARD", "GUARD_CYBER.md", "Control-system access, integrity, and evidence custody", "cybersecurity", "CYB",
        ("service-account", "recipe-signing", "historian", "audit-store"), 2.0, "hours",
        (
            "The exposed service account was disabled at 09:40 UTC. The recipe-signing key was not exposed and remains current under key-set K7.",
            "Break-glass access expires after two hours and requires dual approval plus immutable session logging. Emergency access is not continuing authorization.",
            "Online controller logs are retained for 180 days and archived investigation evidence for seven years; the periods serve different obligations.",
        ),
        (
            "STERILE and CULTURE require GUARD-validated controller access; SIGNAL consumes audit events but does not authorize access.",
            "Any key-set, role-policy, controller, recipe, or logging mutation makes prior cyber verification stale.",
        ),
        ("Distinguish account disablement, key status, access duration, approval, and retention.", "Name current evidence required before restoring remote recipe deployment."),
    ),
    SourceSpec(
        "SUPPLY", "SUPPLY_MATERIALS.md", "Materials, fuel, staffing, and supplier continuity", "supply", "SUP",
        ("resin", "stoppers", "diesel", "operators"), 31.0, "hours-cover",
        (
            "Current diesel stock covers twenty-eight hours at emergency load and seventeen hours at full production load. The two consumption regimes must remain distinct.",
            "Sterile stopper stock covers 4.2 production days, while chromatography resin covers 2.6 batches. Days and batches are different inventory measures.",
            "Mutual aid provides five qualified operators beginning at 05:30 UTC with travel uncertainty of plus or minus seventy-five minutes.",
        ),
        (
            "CURRENT generator duration depends on SUPPLY fuel; STERILE depends on stoppers; CULTURE depends on resin and qualified staffing.",
            "CHILL shipping alternatives require approved packaging and current lane qualification before use.",
        ),
        ("Preserve load regime, units, staffing time, uncertainty, and supplier qualification.", "Name reorder triggers, alternates, owners, and retirement evidence."),
    ),
    SourceSpec(
        "SAFETY", "SAFETY_ENVIRONMENT.md", "Worker safety, emissions, waste, and notification", "safety_environment", "ENV",
        ("solvent-room", "waste-tank", "exhaust", "neutralization"), 24.0, "hours",
        (
            "A material unauthorized solvent release requires initial notice within twenty-four hours of determination, not twenty-four minutes after detection.",
            "Temporary neutralization may proceed under permit condition N-12, but discharge above 0.021 milligrams per liter at the outfall requires an immediate stop.",
            "Determination evidence, notices, candidate changes, checks, and closure records must be retained for seven years with access provenance.",
        ),
        (
            "SIGNAL supplies alarm evidence and CURRENT supplies utility state. CHARTER owns materiality determination; a semantic record cannot make the legal determination.",
            "COMMUNE supplies notice-delivery records and GUARD protects sensitive facility details.",
        ),
        ("Preserve determination event, clock, permit, threshold, unit, and custody.", "State unknowns and exact evidence that can change reportability."),
    ),
    SourceSpec(
        "SIGNAL", "SIGNAL_OBSERVABILITY.md", "Monitoring coverage, alerts, and latency", "observability", "OBS",
        ("temperature", "pressure", "viable-air", "power"), 94.0, "percent-coverage",
        (
            "Current critical-signal coverage is 94 percent; six percent remains unobserved. Coverage is not confidence and does not prove healthy uninstrumented assets.",
            "The clean-utility warning threshold is 81 degrees Celsius and the production stop is 79 degrees. Warning and stop thresholds must remain distinct.",
            "Alarm delivery is 640 milliseconds at p95 and 1,050 milliseconds at p99. Both are observations, not response deadlines.",
        ),
        (
            "CURRENT, STERILE, CHILL, and GUARD rely on SIGNAL observations, but each domain retains its own gate and authority.",
            "COMMUNE may report operational state only where SIGNAL coverage and source currency are adequate.",
        ),
        ("Preserve coverage uncertainty, threshold purpose, percentiles, units, and currentness.", "Define alternate observation routes and evidence for retiring manual watches."),
    ),
    SourceSpec(
        "COMMUNE", "COMMUNE_COMMUNICATIONS.md", "Workforce, regulator, and customer communications", "communications", "COM",
        ("sms", "regulator-portal", "hotline", "shift-briefing"), 89.0, "percent-acknowledged",
        (
            "Restart restrictions reached 89 percent of affected personnel; the missing eleven percent is communication uncertainty, not an eleven-percent reduction in affected staff.",
            "Public states must distinguish investigation, quarantine, engineering restart, lot release, commercial restart, and closure. Engineering restart does not imply lot release.",
            "The hotline sustains 1,800 contacts per hour for four hours. Forecast demand is 2,400 per hour unless multilingual outbound messages reduce repeat contacts.",
        ),
        (
            "CHARTER and ASSAY determine authorized release language; SIGNAL supplies measured operational state and GUARD constrains sensitive details.",
            "SAFETY supplies mandatory environmental language and SUPPLY supplies verified alternate-shift arrangements.",
        ),
        ("Preserve acknowledgment coverage, state vocabulary, capacity, forecast, accessibility, and privacy.", "State owners, channels, timing, acknowledgments, alternates, and retirement evidence."),
    ),
    SourceSpec(
        "CHANGE", "CHANGE_LINEAGE.md", "Candidate lineage, rollback, and configuration control", "change_control", "CHG",
        ("batch-genealogy", "fill-line", "utility-map", "key-set"), 9.0, "candidate-index",
        (
            "The current restart candidate is R9 with batch genealogy B14, fill-line configuration F8, utility map U11, and key set K7. Evidence for R8 is historical unless explicitly transferred and rechecked.",
            "Rollback to R8 is mechanically possible only while recipe V6 and controller firmware C13 remain compatible. Mechanical possibility is not authorization.",
            "Every mutation must record before and after candidate hashes, changed files, affected evidence, check currency, owner, and rollback effect.",
        ),
        (
            "CULTURE, STERILE, CHILL, CURRENT, ASSAY, GUARD, and SIGNAL observations can become stale after CHANGE candidate mutations.",
            "REVIEW evaluates current-candidate evidence independently; CHARTER authorizes execution, release, restart, and closure separately.",
        ),
        ("Keep candidate, genealogy, line, utility, key, recipe, and firmware versions explicit.", "Require effect uptake, current check, repair, recheck, and rollback evidence."),
    ),
    SourceSpec(
        "REVIEW", "REVIEW_READINESS.md", "Independent readiness review, blockers, and falsifiers", "readiness", "RDY",
        ("process", "aseptic", "quality", "cyber"), 13.0, "open-findings",
        (
            "The latest independent review found thirteen open findings: four aseptic, three utility, three quality, two cyber, and one communication. A finding count is not a readiness percentage.",
            "Blocking findings include two missing media fills, stale generator-transfer evidence, unresolved lane-4 stability disposition, and missing quality-unit acknowledgment.",
            "Readiness requires current candidate-bound evidence for every blocking control, independent residual-risk review, and explicit acceptance by each authorized owner.",
        ),
        (
            "REVIEW consumes evidence from CHARTER, CULTURE, STERILE, CHILL, CURRENT, ASSAY, GUARD, SIGNAL, COMMUNE, and CHANGE but does not mutate their states.",
            "An artifact, semantic register, mechanical check, or submission proposal cannot self-authorize release, restart, or closure.",
        ),
        ("List blockers, falsifiers, residual risks, owners, current evidence, and acceptance.", "Keep review separate from execution, release, communications, and closure authority."),
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
