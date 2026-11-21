"""Check a unified control set against framework requirements and the evidence behind it.

Reads four CSV files from one directory:

  controls.csv      one row per control: owner, test frequency, automated or manual
  requirements.csv  the framework requirements in scope (SOC 2, ISO 27001, NIST 800-53, ...)
  mappings.csv      which control satisfies which requirement; one control can map to many
  evidence.csv      one row per piece of test evidence: control, date collected, result

As of a given date, the script:

  1. Marks each control Current, Due soon, Stale, Failing, or Missing evidence, based on
     its latest evidence and how often it must be tested.
  2. Marks each in-scope requirement Met, At risk, or Gap. A requirement is met when at
     least one mapped control has current, passing evidence.
  3. Reports findings, coverage by framework, how far each control is reused across
     frameworks, and an evidence request list grouped by control owner.

The point is the one a unified control library is built for: test a control once and
show which requirements in which frameworks that one test satisfies, and which ones
an auditor will find unsupported.

Standard library only. Run: python -m controls.check sample/controls --as-of 2026-11-15
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

# Longest gap allowed between pieces of evidence, in days, by test frequency.
# Each includes a short grace period. Set these to match your own testing standard.
FREQUENCY_DAYS = {
    "continuous": 7,
    "weekly": 10,
    "monthly": 35,
    "quarterly": 100,
    "semiannual": 190,
    "annual": 380,
}

# Evidence is "due soon" when it expires within this share of its window, capped at 30 days.
DUE_SOON_SHARE = 0.25
DUE_SOON_CAP_DAYS = 30

SEVERITY_ORDER = {"High": 0, "Medium": 1, "Low": 2}

CURRENT, DUE_SOON, STALE, FAILING, MISSING = "Current", "Due soon", "Stale", "Failing", "Missing evidence"
MET, AT_RISK, GAP = "Met", "At risk", "Gap"


@dataclass
class Evidence:
    collected_on: date
    result: str  # pass, fail
    source: str
    reference: str


@dataclass
class Control:
    id: str
    title: str
    owner: str
    frequency: str
    automated: bool
    requirements: list[tuple[str, str]] = field(default_factory=list)  # (framework, requirement_id)
    evidence: list[Evidence] = field(default_factory=list)
    status: str = ""
    expires_on: date | None = None

    @property
    def window_days(self) -> int:
        return FREQUENCY_DAYS[self.frequency]

    @property
    def latest(self) -> Evidence | None:
        return max(self.evidence, key=lambda e: e.collected_on) if self.evidence else None

    @property
    def frameworks(self) -> set[str]:
        return {fw for fw, _ in self.requirements}

    @property
    def satisfies(self) -> bool:
        return self.status in (CURRENT, DUE_SOON)


@dataclass
class Requirement:
    framework: str
    id: str
    title: str
    controls: list[str] = field(default_factory=list)
    status: str = ""

    @property
    def key(self) -> tuple[str, str]:
        return (self.framework, self.id)


@dataclass
class Finding:
    severity: str
    category: str
    subject: str  # control ID, or "framework requirement"
    detail: str


@dataclass
class Result:
    as_of: date
    controls: dict[str, Control]
    requirements: dict[tuple[str, str], Requirement]
    findings: list[Finding]


# ---------------------------------------------------------------- loading


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return [{k: (v or "").strip() for k, v in row.items() if k} for row in csv.DictReader(f)]


def _date(value: str, where: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{where}: expected a date as YYYY-MM-DD, got {value!r}") from None


def load(data_dir: Path) -> tuple[dict[str, Control], dict[tuple[str, str], Requirement], list[Finding]]:
    findings: list[Finding] = []

    controls: dict[str, Control] = {}
    for row in _rows(data_dir / "controls.csv"):
        cid = row["id"]
        if not cid:
            continue
        if cid in controls:
            raise ValueError(f"duplicate control id: {cid}")
        freq = row["frequency"].lower()
        if freq not in FREQUENCY_DAYS:
            raise ValueError(f"{cid}: frequency must be one of {', '.join(FREQUENCY_DAYS)}, got {freq!r}")
        controls[cid] = Control(cid, row["title"], row.get("owner", ""), freq,
                                row.get("automated", "").lower() in ("yes", "y", "true", "1"))

    requirements: dict[tuple[str, str], Requirement] = {}
    for row in _rows(data_dir / "requirements.csv"):
        req = Requirement(row["framework"], row["requirement_id"], row.get("title", ""))
        if req.key in requirements:
            raise ValueError(f"duplicate requirement: {req.framework} {req.id}")
        requirements[req.key] = req

    for row in _rows(data_dir / "mappings.csv"):
        cid, key = row["control_id"], (row["framework"], row["requirement_id"])
        if cid not in controls:
            findings.append(Finding("Medium", "Unknown control ID", cid,
                                    f"Mapping to {key[0]} {key[1]} names {cid}, which is not in the control set."))
            continue
        if key not in requirements:
            findings.append(Finding("Low", "Out-of-scope mapping", cid,
                                    f"{cid} maps to {key[0]} {key[1]}, which is not in the in-scope requirements. "
                                    "Add the requirement to scope or drop the mapping."))
            continue
        if key not in controls[cid].requirements:
            controls[cid].requirements.append(key)
            requirements[key].controls.append(cid)

    for i, row in enumerate(_rows(data_dir / "evidence.csv"), start=2):
        cid = row["control_id"]
        if cid not in controls:
            findings.append(Finding("Medium", "Unknown control ID", cid,
                                    f"evidence.csv line {i} names {cid}, which is not in the control set."))
            continue
        result = row.get("result", "pass").lower() or "pass"
        if result not in ("pass", "fail"):
            raise ValueError(f"evidence.csv line {i}: result must be pass or fail, got {result!r}")
        controls[cid].evidence.append(Evidence(_date(row["collected_on"], f"evidence.csv line {i}"),
                                               result, row.get("source", ""), row.get("reference", "")))
    return controls, requirements, findings


# ---------------------------------------------------------------- analysis


def control_status(ctl: Control, as_of: date) -> tuple[str, date | None]:
    latest = ctl.latest
    if latest is None:
        return MISSING, None
    expires = latest.collected_on + timedelta(days=ctl.window_days)
    if latest.result == "fail":
        return FAILING, expires
    if as_of > expires:
        return STALE, expires
    due_soon = min(DUE_SOON_CAP_DAYS, int(ctl.window_days * DUE_SOON_SHARE))
    if (expires - as_of).days <= due_soon:
        return DUE_SOON, expires
    return CURRENT, expires


def analyze(controls: dict[str, Control], requirements: dict[tuple[str, str], Requirement],
            as_of: date) -> list[Finding]:
    findings: list[Finding] = []

    for ctl in controls.values():
        ctl.status, ctl.expires_on = control_status(ctl, as_of)
        n_req = len(ctl.requirements)
        reach = f"It supports {n_req} requirement{'s' if n_req != 1 else ''} across {len(ctl.frameworks)} framework" \
                f"{'s' if len(ctl.frameworks) != 1 else ''}."
        if ctl.status == MISSING:
            findings.append(Finding("High", "Missing evidence", ctl.id,
                                    f"No test evidence on file for {ctl.id} ({ctl.frequency}). {reach}"))
        elif ctl.status == FAILING:
            findings.append(Finding("High", "Failed test", ctl.id,
                                    f"Latest test on {ctl.latest.collected_on} failed ({ctl.latest.reference or 'no reference'}). "
                                    f"Log an issue with an owner and due date, and retest after remediation. {reach}"))
        elif ctl.status == STALE:
            findings.append(Finding("Medium", "Stale evidence", ctl.id,
                                    f"Latest evidence {ctl.latest.collected_on} expired {ctl.expires_on} "
                                    f"({(as_of - ctl.expires_on).days} days ago) for a {ctl.frequency} control. {reach}"))
        elif ctl.status == DUE_SOON:
            findings.append(Finding("Low", "Evidence due soon", ctl.id,
                                    f"Evidence expires {ctl.expires_on} ({(ctl.expires_on - as_of).days} days)."))
        if not ctl.owner:
            findings.append(Finding("Medium", "No owner", ctl.id,
                                    f"{ctl.id} has no named owner, so nobody is accountable for testing it."))
        if not ctl.requirements:
            findings.append(Finding("Low", "Unmapped control", ctl.id,
                                    f"{ctl.id} maps to no in-scope requirement. Map it, or retire it and stop testing it."))

    for req in requirements.values():
        mapped = [controls[c] for c in req.controls]
        label = f"{req.framework} {req.id}"
        if not mapped:
            req.status = GAP
            findings.append(Finding("High", "Unmapped requirement", label,
                                    f"No control maps to {label} ({req.title}). An auditor testing it will find nothing."))
        elif not any(c.satisfies for c in mapped):
            req.status = AT_RISK
            why = ", ".join(f"{c.id} {c.status.lower()}" for c in mapped)
            findings.append(Finding("High", "Requirement at risk", label,
                                    f"{label} ({req.title}) has mapped controls but none with current passing evidence: {why}."))
        else:
            req.status = MET
            good = [c for c in mapped if c.satisfies]
            if all(c.status == DUE_SOON for c in good):
                first = min(c.expires_on for c in good)
                findings.append(Finding("Medium", "Requirement lapsing", label,
                                        f"{label} ({req.title}) is met only by evidence that expires soon "
                                        f"({', '.join(c.id for c in good)}; first expiry {first}). "
                                        "Without a new test it becomes at risk."))

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.subject))
    return findings


def run(data_dir: Path, as_of: date) -> Result:
    controls, requirements, pre = load(data_dir)
    findings = analyze(controls, requirements, as_of)
    all_findings = sorted(pre + findings, key=lambda f: (SEVERITY_ORDER[f.severity], f.category, f.subject))
    return Result(as_of, controls, requirements, all_findings)


# ---------------------------------------------------------------- output


def coverage(result: Result) -> list[tuple[str, int, int, int, int]]:
    by_fw: dict[str, list[Requirement]] = defaultdict(list)
    for req in result.requirements.values():
        by_fw[req.framework].append(req)
    rows = []
    for fw in sorted(by_fw):
        reqs = by_fw[fw]
        rows.append((fw, len(reqs), sum(r.status == MET for r in reqs),
                     sum(r.status == AT_RISK for r in reqs), sum(r.status == GAP for r in reqs)))
    return rows


def evidence_requests(result: Result) -> dict[str, list[tuple[Control, str]]]:
    """Controls that need new evidence, grouped by owner, each with a due date."""
    by_owner: dict[str, list[tuple[Control, str]]] = defaultdict(list)
    for ctl in result.controls.values():
        if ctl.status == CURRENT or not ctl.requirements:
            continue
        due = "now" if ctl.status in (MISSING, STALE, FAILING) else str(ctl.expires_on)
        by_owner[ctl.owner or "(no owner)"].append((ctl, due))
    for items in by_owner.values():
        items.sort(key=lambda item: (item[1] != "now", item[1], item[0].id))
    return dict(sorted(by_owner.items()))


def render_report(result: Result) -> str:
    ctls, reqs, findings = result.controls, result.requirements, result.findings
    sev = {k: sum(f.severity == k for f in findings) for k in SEVERITY_ORDER}
    met = sum(r.status == MET for r in reqs.values())
    mapped_pairs = sum(len(c.requirements) for c in ctls.values())
    mapped_ctls = [c for c in ctls.values() if c.requirements]
    frameworks = sorted({r.framework for r in reqs.values()})

    out = ["# Control Evidence Report", "", f"As of {result.as_of}.", ""]
    out.append(f"{len(ctls)} controls cover {len(reqs)} in-scope requirements across {len(frameworks)} frameworks "
               f"({', '.join(frameworks)}). {met} of {len(reqs)} requirements are met.")
    if mapped_ctls:
        out.append(f"Each mapped control supports {mapped_pairs / len(mapped_ctls):.1f} requirements on average, "
                   "so one test produces evidence for several frameworks at once.")
    out.append(f"{len(findings)} findings: {sev['High']} high, {sev['Medium']} medium, {sev['Low']} low.")

    out += ["", "## Coverage by framework", "",
            "| Framework | In scope | Met | At risk | Gap | Met % |", "|---|---|---|---|---|---|"]
    for fw, total, n_met, n_risk, n_gap in coverage(result):
        out.append(f"| {fw} | {total} | {n_met} | {n_risk} | {n_gap} | {100 * n_met / total:.0f}% |")

    out += ["", "## Findings", ""]
    if findings:
        out += ["| Severity | Category | Subject | Detail |", "|---|---|---|---|"]
        out += [f"| {f.severity} | {f.category} | {f.subject} | {f.detail} |" for f in findings]
    else:
        out.append("No findings.")

    out += ["", "## Requirements not met", ""]
    unmet = sorted((r for r in reqs.values() if r.status != MET), key=lambda r: (r.status != GAP, r.framework, r.id))
    if unmet:
        out += ["| Framework | Requirement | Title | Status | Mapped controls |", "|---|---|---|---|---|"]
        for r in unmet:
            mapped = ", ".join(f"{c} ({ctls[c].status})" for c in r.controls) or "—"
            out.append(f"| {r.framework} | {r.id} | {r.title} | {r.status} | {mapped} |")
    else:
        out.append("All in-scope requirements are met.")

    out += ["", "## Controls", "",
            "Sorted by reach: the controls at the top support the most requirements, so a lapse there costs the most.", "",
            "| Control | Title | Owner | Frequency | Automated | Frameworks | Requirements | Last evidence | Expires | Status |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for c in sorted(ctls.values(), key=lambda c: (-len(c.requirements), c.id)):
        last = str(c.latest.collected_on) if c.latest else "—"
        out.append(f"| {c.id} | {c.title} | {c.owner or '—'} | {c.frequency} | {'yes' if c.automated else 'no'} | "
                   f"{len(c.frameworks)} | {len(c.requirements)} | {last} | {c.expires_on or '—'} | {c.status} |")

    out += ["", "## Evidence requests by owner", "",
            "What each owner needs to produce, most urgent first. \"now\" means the evidence is missing, stale, or failed.", ""]
    requests = evidence_requests(result)
    if requests:
        for owner, items in requests.items():
            out.append(f"**{owner}**")
            out.append("")
            out += [f"- {c.id} {c.title}: {c.status.lower()}, due {due}" for c, due in items]
            out.append("")
    else:
        out += ["No evidence requests.", ""]
    return "\n".join(out)


def write_status_csv(result: Result, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["framework", "requirement_id", "title", "status", "controls", "satisfying_controls"])
        for r in sorted(result.requirements.values(), key=lambda r: r.key):
            good = [c for c in r.controls if result.controls[c].satisfies]
            w.writerow([r.framework, r.id, r.title, r.status, ";".join(r.controls), ";".join(good)])


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("data_dir", type=Path,
                   help="directory holding controls.csv, requirements.csv, mappings.csv, evidence.csv")
    p.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                   help="date to assess evidence against, YYYY-MM-DD (default: today)")
    p.add_argument("--report", type=Path, help="write the Markdown report here (default: stdout)")
    p.add_argument("--status-csv", type=Path, help="also write per-requirement status as CSV")
    p.add_argument("--fail-on", choices=["high", "medium", "never"], default="never",
                   help="exit 1 if findings at or above this severity exist (for CI use)")
    args = p.parse_args(argv)

    result = run(args.data_dir, args.as_of)
    report = render_report(result)
    if args.report:
        args.report.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.status_csv:
        write_status_csv(result, args.status_csv)

    if args.fail_on != "never":
        threshold = SEVERITY_ORDER["High" if args.fail_on == "high" else "Medium"]
        if any(SEVERITY_ORDER[f.severity] <= threshold for f in result.findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
