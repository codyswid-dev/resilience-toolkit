from datetime import date
from pathlib import Path

import pytest

from controls import check

SAMPLE = Path(__file__).resolve().parents[2] / "sample" / "controls"
AS_OF = date(2026, 11, 15)


def write(tmp_path, controls, requirements, mappings, evidence):
    (tmp_path / "controls.csv").write_text("id,title,owner,frequency,automated\n" + "\n".join(controls) + "\n")
    (tmp_path / "requirements.csv").write_text("framework,requirement_id,title\n" + "\n".join(requirements) + "\n")
    (tmp_path / "mappings.csv").write_text("control_id,framework,requirement_id\n" + "\n".join(mappings) + "\n")
    (tmp_path / "evidence.csv").write_text("control_id,collected_on,result,source,reference\n"
                                           + "\n".join(evidence) + "\n")
    return tmp_path


def categories(result, subject=None):
    return {f.category for f in result.findings if subject is None or f.subject == subject}


@pytest.mark.parametrize("collected,result,expected", [
    ("2026-11-01", "pass", check.CURRENT),     # 14 days into a 100-day window
    ("2026-08-20", "pass", check.DUE_SOON),    # expires 2026-11-28, 13 days out, inside the 25-day threshold
    ("2026-07-01", "pass", check.STALE),       # expired 2026-10-09
    ("2026-11-01", "fail", check.FAILING),     # recent but failed
])
def test_control_status(tmp_path, collected, result, expected):
    d = write(tmp_path, ["c1,Access review,IAM,quarterly,no"], ["SOC 2,CC6.2,Access"],
              ["c1,SOC 2,CC6.2"], [f"c1,{collected},{result},,"])
    assert check.run(d, AS_OF).controls["c1"].status == expected


def test_latest_evidence_wins(tmp_path):
    d = write(tmp_path, ["c1,Restore test,Infra,quarterly,no"], ["SOC 2,A1.3,Recovery"], ["c1,SOC 2,A1.3"],
              ["c1,2026-10-01,fail,,", "c1,2026-11-10,pass,,"])
    assert check.run(d, AS_OF).controls["c1"].status == check.CURRENT


def test_missing_evidence(tmp_path):
    d = write(tmp_path, ["c1,Vendor review,TPRM,annual,no"], ["SOC 2,CC9.2,Vendors"], ["c1,SOC 2,CC9.2"], [])
    r = check.run(d, AS_OF)
    assert r.controls["c1"].status == check.MISSING
    assert "Missing evidence" in categories(r, "c1")
    assert r.requirements[("SOC 2", "CC9.2")].status == check.AT_RISK


def test_requirement_met_by_any_current_control(tmp_path):
    d = write(tmp_path, ["c1,Logging,SecOps,continuous,yes", "c2,Alert review,SecOps,monthly,no"],
              ["NIST 800-53,AU-6,Audit review"], ["c1,NIST 800-53,AU-6", "c2,NIST 800-53,AU-6"],
              ["c1,2026-10-01,pass,,", "c2,2026-11-01,pass,,"])
    r = check.run(d, AS_OF)
    assert r.controls["c1"].status == check.STALE
    assert r.requirements[("NIST 800-53", "AU-6")].status == check.MET


def test_requirement_lapsing_when_only_due_soon_evidence(tmp_path):
    d = write(tmp_path, ["c1,Privileged review,IAM,quarterly,no", "c2,Access review,IAM,quarterly,no"],
              ["SOC 2,CC6.3,Access changes"], ["c1,SOC 2,CC6.3", "c2,SOC 2,CC6.3"],
              ["c1,2026-08-20,pass,,", "c2,2026-06-01,pass,,"])
    r = check.run(d, AS_OF)
    assert r.requirements[("SOC 2", "CC6.3")].status == check.MET
    assert "Requirement lapsing" in categories(r, "SOC 2 CC6.3")


def test_unmapped_requirement_is_a_gap(tmp_path):
    d = write(tmp_path, ["c1,Access review,IAM,quarterly,no"], ["SOC 2,CC6.2,Access", "SOC 2,CC7.5,Recovery"],
              ["c1,SOC 2,CC6.2"], ["c1,2026-11-01,pass,,"])
    r = check.run(d, AS_OF)
    assert r.requirements[("SOC 2", "CC7.5")].status == check.GAP
    assert "Unmapped requirement" in categories(r, "SOC 2 CC7.5")


def test_one_control_across_frameworks(tmp_path):
    d = write(tmp_path, ["c1,Backups,Infra,continuous,yes"],
              ["SOC 2,A1.2,Backups", "ISO 27001,A.8.13,Backup", "NIST 800-53,CP-9,System backup"],
              ["c1,SOC 2,A1.2", "c1,ISO 27001,A.8.13", "c1,NIST 800-53,CP-9"], ["c1,2026-11-14,pass,,"])
    r = check.run(d, AS_OF)
    assert r.controls["c1"].frameworks == {"SOC 2", "ISO 27001", "NIST 800-53"}
    assert all(req.status == check.MET for req in r.requirements.values())
    assert r.findings == []


def test_data_quality_findings(tmp_path):
    d = write(tmp_path, ["c1,Access review,,quarterly,no", "c2,Clean desk,Facilities,annual,no"],
              ["SOC 2,CC6.2,Access"], ["c1,SOC 2,CC6.2", "c1,PCI DSS,7.2.4", "c9,SOC 2,CC6.2"],
              ["c1,2026-11-01,pass,,", "c2,2026-11-01,pass,,", "c8,2026-11-01,pass,,"])
    r = check.run(d, AS_OF)
    assert "No owner" in categories(r, "c1")
    assert "Out-of-scope mapping" in categories(r, "c1")
    assert "Unmapped control" in categories(r, "c2")
    assert {f.subject for f in r.findings if f.category == "Unknown control ID"} == {"c8", "c9"}


def test_bad_input_raises(tmp_path):
    d = write(tmp_path, ["c1,Access review,IAM,fortnightly,no"], [], [], [])
    with pytest.raises(ValueError, match="frequency"):
        check.run(d, AS_OF)
    d = write(tmp_path, ["c1,Access review,IAM,quarterly,no"], [], [], ["c1,11/01/2026,pass,,"])
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        check.run(d, AS_OF)


def test_evidence_requests_grouped_by_owner(tmp_path):
    d = write(tmp_path, ["c1,Access review,IAM,quarterly,no", "c2,MFA,IAM,continuous,yes",
                         "c3,DR test,Infra,annual,no"],
              ["SOC 2,CC6.1,Logical access", "SOC 2,A1.3,Recovery"],
              ["c1,SOC 2,CC6.1", "c2,SOC 2,CC6.1", "c3,SOC 2,A1.3"],
              ["c1,2026-08-20,pass,,", "c2,2026-11-14,pass,,"])
    reqs = check.evidence_requests(check.run(d, AS_OF))
    assert [(c.id, due) for c, due in reqs["IAM"]] == [("c1", "2026-11-28")]
    assert [(c.id, due) for c, due in reqs["Infra"]] == [("c3", "now")]


def test_fail_on_exit_code(tmp_path):
    d = write(tmp_path, ["c1,Vendor review,TPRM,annual,no"], ["SOC 2,CC9.2,Vendors"], ["c1,SOC 2,CC9.2"], [])
    assert check.main([str(d), "--as-of", "2026-11-15", "--report", str(tmp_path / "r.md"), "--fail-on", "high"]) == 1
    assert check.main([str(d), "--as-of", "2026-11-15", "--report", str(tmp_path / "r.md")]) == 0


def test_sample_runs(tmp_path):
    r = check.run(SAMPLE, AS_OF)
    assert len(r.controls) >= 10
    assert {req.framework for req in r.requirements.values()} == {"SOC 2", "ISO 27001", "NIST 800-53"}
    assert any(req.status == check.GAP for req in r.requirements.values())
    assert check.render_report(r).startswith("# Control Evidence Report")
