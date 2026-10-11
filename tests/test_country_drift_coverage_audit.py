"""Small fixtures for coverage boundaries and candidate-only diagnostics."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_country_drift_coverage.py"
SPEC = importlib.util.spec_from_file_location("audit_country_drift_coverage", SCRIPT)
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def movement(mid, start, end, *, country="AAA", scope=None, role=None, policies=()):
    record = {
        "movement_id": mid,
        "countries": [country],
        "timeframe": {"start": start, "end": end},
        "policies": list(policies),
        "axes_summary": [],
        "_source_file": f"movements/{mid}.yaml",
    }
    if scope:
        record["scope"] = scope
    if role:
        record["country_drift_role"] = role
    return record


def policy(pid, year, *, country="AAA", enacted_by=()):
    return {
        "policy_id": pid,
        "title": pid,
        "countries": [country],
        "timeframe": {"start": year},
        "enacted_by": list(enacted_by),
        "status": "candidate",
        "_source_file": f"policies/{pid}.yaml",
    }


def test_plotted_intervals_ignore_context_and_subnational_records():
    movements = [
        movement("early", 1900, 1902),
        movement("state", 1903, 1904, scope="subnational"),
        movement("context", 1900, 1910, role="context_only"),
        movement("late", 1905, 1906),
    ]
    report = AUDIT.report_for(movements, [policy("gap_policy", 1903)], 2026)
    country = report["countries"]["AAA"]
    assert country["authored_movement_count"] == 4
    assert country["plotted_movement_count"] == 2
    assert country["context_only_movement_count"] == 1
    assert country["subnational_movement_count"] == 1
    assert country["internal_gaps"] == [{"from_year": 1903, "through_year": 1904, "years": 2}]
    assert country["missing_current_coverage"] is True
    assert report["candidate_policy_leads"][0]["review_reasons"] == ["internal_uncovered_year"]


def test_policy_leads_do_not_create_movements_and_flag_link_mismatch():
    movements = [movement("prior", 1975, 1983), movement("later", 1991, 1996)]
    policies = [
        policy("mislinked", 1983, enacted_by=["later"]),
        policy("policy_only", 2000, country="BBB"),
    ]
    report = AUDIT.report_for(movements, policies, 2026)
    assert report["summary"]["authored_country_count"] == 1
    assert report["summary"]["policy_only_country_count"] == 1
    assert report["countries"]["BBB"]["plotted_movement_count"] == 0
    assert report["countries"]["BBB"]["missing_current_coverage"] is True
    leads = {(row["country"], row["policy_id"]): row for row in report["candidate_policy_leads"]}
    assert leads[("AAA", "mislinked")]["review_reasons"] == ["enactor_timeframe_mismatch"]
    assert leads[("BBB", "policy_only")]["review_reasons"] == ["no_plotted_movement"]


def test_overlap_requires_shared_policy_and_reports_plotting_status():
    movements = [
        movement("first", 2000, 2005, policies=["p"]),
        movement("second", 2003, 2006, policies=["p"]),
        movement("umbrella", 2000, 2010, role="context_only", policies=["p"]),
        movement("unrelated", 2003, 2006, policies=["q"]),
    ]
    report = AUDIT.report_for(movements, [], 2026)
    shared = report["overlap_shared_policy_candidates"]
    assert len(shared) == 3
    assert sum(row["both_plotted_in_drift"] for row in shared) == 1
    assert all(row["shared_policy_ids"] == ["p"] for row in shared)
    assert report == AUDIT.report_for(movements, [], 2026)


def test_eu_geographic_scope_is_reviewed_without_inferring_membership():
    eu = movement("eu_example", 2018, "ongoing", country="AAA", scope="supranational")
    eu["countries"] = ["AAA", "BBB"]
    report = AUDIT.report_for([eu], [], 2026)
    assert report["summary"]["eu_supranational_geography_review_records"] == 1
    assert report["eu_geographic_scope_review"][0]["declared_countries"] == ["AAA", "BBB"]
    assert "omitted" not in report["eu_geographic_scope_review"][0]
