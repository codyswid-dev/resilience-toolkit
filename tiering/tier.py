"""Assign recovery tiers to services and check a dependency map for resilience gaps.

Inputs are two CSV files:

  services.csv      one row per service: impact ratings, MTPD, and target RTO/RPO
  dependencies.csv  one row per dependency: service_id depends on depends_on

The script:

  1. Assigns each service a base tier from its impact ratings and MTPD.
  2. Propagates tiers through hard dependencies, so a service that a Tier 1
     service cannot run without is also treated as Tier 1.
  3. Reports findings: RTO inversions, RTO targets that miss the tier standard,
     dependency cycles, concentration risk, missing RPO targets, and unknown IDs.

Standard library only. Run: python -m tiering.tier sample/services.csv sample/dependencies.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Tier standard. A service lands in the first tier whose impact or MTPD
# threshold it meets. max_rto_hours is the longest RTO acceptable for the tier.
TIERS = {
    1: {"min_impact": 5, "max_mtpd_hours": 4, "max_rto_hours": 4},
    2: {"min_impact": 4, "max_mtpd_hours": 24, "max_rto_hours": 24},
    3: {"min_impact": 3, "max_mtpd_hours": 72, "max_rto_hours": 72},
    4: {"min_impact": 1, "max_mtpd_hours": None, "max_rto_hours": 168},
}

IMPACT_FIELDS = ("impact_financial", "impact_customer", "impact_regulatory", "impact_operational")

# A service with this many or more hard dependents is flagged as concentration risk.
CONCENTRATION_THRESHOLD = 4


@dataclass
class Service:
    id: str
    name: str
    owner: str
    impacts: dict[str, int]
    mtpd_hours: float
    rto_hours: float
    rpo_minutes: float | None
    base_tier: int = 0
    tier: int = 0
    tier_reason: str = ""
    hard_deps: list[str] = field(default_factory=list)
    soft_deps: list[str] = field(default_factory=list)
    hard_dependents: list[str] = field(default_factory=list)

    @property
    def max_impact(self) -> int:
        return max(self.impacts.values())


@dataclass
class Finding:
    severity: str  # High, Medium, Low
    category: str
    service_id: str
    detail: str


SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}


# ---------------------------------------------------------------- loading


def _num(value: str, column: str, row_id: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{row_id}: column '{column}' must be a number, got {value!r}") from None


def load_services(path: Path) -> dict[str, Service]:
    services: dict[str, Service] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid = row["id"].strip()
            if not sid:
                continue
            if sid in services:
                raise ValueError(f"duplicate service id: {sid}")
            impacts = {}
            for col in IMPACT_FIELDS:
                score = int(_num(row[col], col, sid))
                if not 1 <= score <= 5:
                    raise ValueError(f"{sid}: {col} must be 1-5, got {score}")
                impacts[col] = score
            rpo_raw = (row.get("target_rpo_minutes") or "").strip()
            services[sid] = Service(
                id=sid,
                name=row["name"].strip(),
                owner=row.get("owner", "").strip(),
                impacts=impacts,
                mtpd_hours=_num(row["mtpd_hours"], "mtpd_hours", sid),
                rto_hours=_num(row["target_rto_hours"], "target_rto_hours", sid),
                rpo_minutes=_num(rpo_raw, "target_rpo_minutes", sid) if rpo_raw else None,
            )
    return services


def load_dependencies(path: Path, services: dict[str, Service]) -> list[Finding]:
    findings: list[Finding] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            src, dst = row["service_id"].strip(), row["depends_on"].strip()
            kind = (row.get("type") or "hard").strip().lower()
            missing = [x for x in (src, dst) if x not in services]
            if missing:
                findings.append(Finding("Medium", "Unknown service ID", src,
                                        f"Dependency {src} -> {dst} references {', '.join(missing)}, "
                                        "which is not in the service inventory."))
                continue
            if kind == "hard":
                services[src].hard_deps.append(dst)
                services[dst].hard_dependents.append(src)
            else:
                services[src].soft_deps.append(dst)
    return findings


# ---------------------------------------------------------------- tiering


def base_tier(svc: Service) -> int:
    for tier, rule in TIERS.items():
        mtpd_limit = rule["max_mtpd_hours"]
        if svc.max_impact >= rule["min_impact"] or (mtpd_limit is not None and svc.mtpd_hours <= mtpd_limit):
            return tier
    return max(TIERS)


def assign_tiers(services: dict[str, Service]) -> None:
    """Base tier per service, then propagate along hard dependencies to a fixed point."""
    for svc in services.values():
        svc.base_tier = svc.tier = base_tier(svc)
        svc.tier_reason = "impact/MTPD"
    changed = True
    while changed:  # terminates: tiers only decrease and are bounded below by 1
        changed = False
        for svc in services.values():
            for dep_id in svc.hard_deps:
                dep = services[dep_id]
                if svc.tier < dep.tier:
                    dep.tier = svc.tier
                    dep.tier_reason = f"inherited from {svc.id}"
                    changed = True


# ---------------------------------------------------------------- analysis


def find_cycles(services: dict[str, Service]) -> list[list[str]]:
    """Strongly connected components with more than one node (Tarjan), over hard dependencies."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []
    counter = [0]

    def visit(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack.add(v)
        for w in services[v].hard_deps:
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                comp.append(w)
                if w == v:
                    break
            if len(comp) > 1 or v in services[v].hard_deps:
                cycles.append(sorted(comp))

    for sid in services:
        if sid not in index:
            visit(sid)
    return cycles


def analyze(services: dict[str, Service]) -> list[Finding]:
    findings: list[Finding] = []
    for svc in services.values():
        for dep_id in svc.hard_deps:
            dep = services[dep_id]
            if dep.rto_hours > svc.rto_hours:
                findings.append(Finding(
                    "High", "RTO inversion", svc.id,
                    f"{svc.id} targets {svc.rto_hours:g}h RTO but hard dependency {dep.id} "
                    f"targets {dep.rto_hours:g}h. {svc.id} cannot recover before {dep.id}."))
        limit = TIERS[svc.tier]["max_rto_hours"]
        if svc.rto_hours > limit:
            findings.append(Finding(
                "High" if svc.tier <= 2 else "Medium", "RTO exceeds tier standard", svc.id,
                f"Tier {svc.tier} ({svc.tier_reason}) allows up to {limit}h RTO; target is {svc.rto_hours:g}h."))
        if svc.rto_hours > svc.mtpd_hours:
            findings.append(Finding(
                "High", "RTO exceeds MTPD", svc.id,
                f"Target RTO {svc.rto_hours:g}h is longer than MTPD {svc.mtpd_hours:g}h."))
        if len(svc.hard_dependents) >= CONCENTRATION_THRESHOLD:
            findings.append(Finding(
                "Medium", "Concentration risk", svc.id,
                f"{len(svc.hard_dependents)} services hard-depend on {svc.id}: "
                f"{', '.join(sorted(svc.hard_dependents))}. Confirm redundancy and include it in DR testing."))
        if svc.rpo_minutes is None and svc.tier <= 2:
            findings.append(Finding(
                "Medium", "Missing RPO", svc.id, f"Tier {svc.tier} service has no RPO target."))
    for cycle in find_cycles(services):
        findings.append(Finding(
            "High", "Dependency cycle", cycle[0],
            f"Hard dependency cycle: {' -> '.join(cycle)}. These services can only be recovered together; "
            "break the cycle or document a manual bootstrap procedure."))
    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.service_id))
    return findings


def recovery_order(services: dict[str, Service]) -> list[list[str]]:
    """Group services into recovery waves: each wave depends only on earlier waves.

    Services in a dependency cycle are recovered together, in the first wave where all
    of their dependencies outside the cycle are already up.
    """
    cycle_of: dict[str, frozenset[str]] = {}
    for cycle in find_cycles(services):
        for sid in cycle:
            cycle_of[sid] = frozenset(cycle)
    remaining = {sid: set(s.hard_deps) - cycle_of.get(sid, frozenset()) for sid, s in services.items()}
    waves: list[list[str]] = []
    done: set[str] = set()
    while remaining:
        ready = {sid for sid, deps in remaining.items() if deps <= done}
        # A cycle member is ready only when every member of its cycle is ready.
        ready = {sid for sid in ready if cycle_of.get(sid, frozenset({sid})) <= ready | done}
        if not ready:  # defensive; cycles are handled above
            waves.append(sorted(remaining))
            break
        waves.append(sorted(ready, key=lambda sid: (services[sid].tier, sid)))
        done |= ready
        for sid in ready:
            del remaining[sid]
    return waves


# ---------------------------------------------------------------- output


def _node(sid: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in sid)


def mermaid(services: dict[str, Service]) -> str:
    lines = ["```mermaid", "graph LR"]
    for svc in services.values():
        label = svc.name.replace('"', "'")
        lines.append(f'  {_node(svc.id)}["{label}<br/>Tier {svc.tier}"]:::t{svc.tier}')
    for svc in services.values():
        for dep in svc.hard_deps:
            lines.append(f"  {_node(svc.id)} --> {_node(dep)}")
        for dep in svc.soft_deps:
            lines.append(f"  {_node(svc.id)} -.-> {_node(dep)}")
    lines += [
        "  classDef t1 fill:#f8d7da,stroke:#842029",
        "  classDef t2 fill:#fff3cd,stroke:#997404",
        "  classDef t3 fill:#cfe2ff,stroke:#084298",
        "  classDef t4 fill:#e2e3e5,stroke:#41464b",
        "```",
    ]
    return "\n".join(lines)


def render_report(services: dict[str, Service], findings: list[Finding], pre_findings: list[Finding]) -> str:
    all_findings = sorted(pre_findings + findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.service_id))
    counts = {t: sum(1 for s in services.values() if s.tier == t) for t in TIERS}
    sev = {k: sum(1 for f in all_findings if f.severity == k) for k in SEVERITY_ORDER}
    out = ["# Service Tiering Report", ""]
    out.append(f"{len(services)} services. " + ", ".join(f"Tier {t}: {n}" for t, n in counts.items()) + ".")
    out.append(f"{len(all_findings)} findings: {sev['High']} high, {sev['Medium']} medium, {sev['Low']} low.")
    out += ["", "## Tiers", "",
            "| Service | Name | Owner | Max impact | MTPD (h) | RTO (h) | RPO (min) | Base tier | Final tier | Reason |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for svc in sorted(services.values(), key=lambda s: (s.tier, s.id)):
        rpo = f"{svc.rpo_minutes:g}" if svc.rpo_minutes is not None else "—"
        out.append(f"| {svc.id} | {svc.name} | {svc.owner} | {svc.max_impact} | {svc.mtpd_hours:g} | "
                   f"{svc.rto_hours:g} | {rpo} | {svc.base_tier} | {svc.tier} | {svc.tier_reason} |")
    out += ["", "## Findings", ""]
    if all_findings:
        out += ["| Severity | Category | Service | Detail |", "|---|---|---|---|"]
        for f in all_findings:
            out.append(f"| {f.severity} | {f.category} | {f.service_id} | {f.detail} |")
    else:
        out.append("No findings.")
    out += ["", "## Recovery order", "",
            "Each wave depends only on services in earlier waves. Within a wave, services are listed by tier.", ""]
    cyclic = {sid for c in find_cycles(services) for sid in c}
    for i, wave in enumerate(recovery_order(services), 1):
        out.append(f"{i}. " + ", ".join(
            f"{sid} (T{services[sid].tier}{', cycle' if sid in cyclic else ''})" for sid in wave))
    out += ["", "## Dependency map", "", "Solid arrows are hard dependencies; dotted arrows are soft.", "",
            mermaid(services), ""]
    return "\n".join(out)


def write_tiers_csv(services: dict[str, Service], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "owner", "base_tier", "tier", "tier_reason", "target_rto_hours", "target_rpo_minutes"])
        for svc in sorted(services.values(), key=lambda s: (s.tier, s.id)):
            w.writerow([svc.id, svc.name, svc.owner, svc.base_tier, svc.tier, svc.tier_reason,
                        f"{svc.rto_hours:g}", "" if svc.rpo_minutes is None else f"{svc.rpo_minutes:g}"])


def run(services_csv: Path, deps_csv: Path) -> tuple[dict[str, Service], list[Finding], str]:
    services = load_services(services_csv)
    pre = load_dependencies(deps_csv, services)
    assign_tiers(services)
    findings = analyze(services)
    return services, pre + findings, render_report(services, findings, pre)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("services", type=Path, help="services CSV")
    p.add_argument("dependencies", type=Path, help="dependencies CSV")
    p.add_argument("--report", type=Path, help="write the Markdown report here (default: stdout)")
    p.add_argument("--tiers-csv", type=Path, help="also write final tiers as CSV")
    p.add_argument("--fail-on", choices=["high", "medium", "never"], default="never",
                   help="exit 1 if findings at or above this severity exist (for CI use)")
    args = p.parse_args(argv)

    services, findings, report = run(args.services, args.dependencies)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.tiers_csv:
        write_tiers_csv(services, args.tiers_csv)

    if args.fail_on != "never":
        threshold = SEVERITY_ORDER["High" if args.fail_on == "high" else "Medium"]
        if any(SEVERITY_ORDER[f.severity] <= threshold for f in findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
