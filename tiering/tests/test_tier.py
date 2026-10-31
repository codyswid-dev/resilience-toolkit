from pathlib import Path

import pytest

from tiering import tier

SAMPLE = Path(__file__).resolve().parents[2] / "sample"
SERVICE_HEADER = ("id,name,owner,business_function,impact_financial,impact_customer,"
                  "impact_regulatory,impact_operational,mtpd_hours,target_rto_hours,target_rpo_minutes\n")


def write(tmp_path, services, deps):
    s = tmp_path / "services.csv"
    d = tmp_path / "deps.csv"
    s.write_text(SERVICE_HEADER + "\n".join(services) + "\n")
    d.write_text("service_id,depends_on,type\n" + "\n".join(deps) + "\n")
    return s, d


def svc(sid, impact=2, mtpd=168, rto=72, rpo="60"):
    return f"{sid},{sid},team,fn,{impact},{impact},1,{impact},{mtpd},{rto},{rpo}"


def categories(findings, service_id=None):
    return {f.category for f in findings if service_id is None or f.service_id == service_id}


def test_base_tier_from_impact_and_mtpd(tmp_path):
    s, d = write(tmp_path, [svc("a", impact=5, rto=1), svc("b", impact=2, mtpd=4, rto=1),
                            svc("c", impact=3, rto=48), svc("d", impact=1, rto=72)], [])
    services, _, _ = tier.run(s, d)
    assert {k: v.tier for k, v in services.items()} == {"a": 1, "b": 1, "c": 3, "d": 4}


def test_tier_propagates_through_hard_dependencies_only(tmp_path):
    s, d = write(tmp_path, [svc("app", impact=5, rto=1), svc("db", rto=1), svc("cache", rto=1),
                            svc("analytics", rto=1)],
                 ["app,db,hard", "db,cache,hard", "app,analytics,soft"])
    services, _, _ = tier.run(s, d)
    assert services["db"].tier == 1
    assert services["cache"].tier == 1  # transitive
    assert services["cache"].tier_reason == "inherited from db"
    assert services["analytics"].tier == 4  # soft dependency does not inherit


def test_rto_inversion_flagged(tmp_path):
    s, d = write(tmp_path, [svc("app", rto=2), svc("db", rto=8)], ["app,db,hard"])
    _, findings, _ = tier.run(s, d)
    assert "RTO inversion" in categories(findings, "app")


def test_soft_dependency_rto_not_flagged(tmp_path):
    s, d = write(tmp_path, [svc("app", rto=2), svc("db", rto=8)], ["app,db,soft"])
    _, findings, _ = tier.run(s, d)
    assert "RTO inversion" not in categories(findings)


def test_cycle_detected_and_recovered_together(tmp_path):
    s, d = write(tmp_path, [svc("a"), svc("b"), svc("c"), svc("root")],
                 ["a,b,hard", "b,a,hard", "c,a,hard", "a,root,hard"])
    services, findings, _ = tier.run(s, d)
    assert tier.find_cycles(services) == [["a", "b"]]
    assert "Dependency cycle" in categories(findings)
    assert tier.recovery_order(services) == [["root"], ["a", "b"], ["c"]]


def test_concentration_risk(tmp_path):
    n = tier.CONCENTRATION_THRESHOLD
    users = [svc(f"u{i}") for i in range(n)]
    s, d = write(tmp_path, users + [svc("shared")], [f"u{i},shared,hard" for i in range(n)])
    _, findings, _ = tier.run(s, d)
    assert "Concentration risk" in categories(findings, "shared")


def test_rto_beyond_tier_standard_and_mtpd(tmp_path):
    s, d = write(tmp_path, [svc("a", impact=5, mtpd=4, rto=8)], [])
    _, findings, _ = tier.run(s, d)
    assert {"RTO exceeds tier standard", "RTO exceeds MTPD"} <= categories(findings, "a")


def test_missing_rpo_only_for_tier_1_and_2(tmp_path):
    s, d = write(tmp_path, [svc("crit", impact=5, rto=1, rpo=""), svc("low", rpo="")], [])
    _, findings, _ = tier.run(s, d)
    assert "Missing RPO" in categories(findings, "crit")
    assert "Missing RPO" not in categories(findings, "low")


def test_unknown_dependency_reported(tmp_path):
    s, d = write(tmp_path, [svc("a")], ["a,ghost,hard"])
    _, findings, _ = tier.run(s, d)
    assert "Unknown service ID" in categories(findings, "a")


def test_invalid_impact_rejected(tmp_path):
    s, d = write(tmp_path, [svc("a", impact=7)], [])
    with pytest.raises(ValueError, match="1-5"):
        tier.run(s, d)


def test_duplicate_id_rejected(tmp_path):
    s, d = write(tmp_path, [svc("a"), svc("a")], [])
    with pytest.raises(ValueError, match="duplicate"):
        tier.run(s, d)


def test_sample_runs_and_shows_expected_gaps():
    services, findings, report = tier.run(SAMPLE / "services.csv", SAMPLE / "dependencies.csv")
    assert services["catalog"].base_tier == 2 and services["catalog"].tier == 1
    cats = categories(findings)
    assert {"RTO inversion", "Dependency cycle", "Concentration risk", "Missing RPO"} <= cats
    assert "```mermaid" in report


def test_fail_on_exit_code(tmp_path):
    s, d = write(tmp_path, [svc("app", rto=2), svc("db", rto=8)], ["app,db,hard"])
    out = tmp_path / "r.md"
    assert tier.main([str(s), str(d), "--report", str(out), "--fail-on", "high"]) == 1
    assert tier.main([str(s), str(d), "--report", str(out)]) == 0
