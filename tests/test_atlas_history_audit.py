"""Coverage audits must expose gaps without inventing governments or sovereignty."""
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("audit_atlas_history", ROOT / "scripts/audit_atlas_history.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def registry(*codes):
    return [{"iso3": code, "name": code, "kind": "country_or_territory"} for code in codes]


def movement(mid, start, end, *, country="AAA", scope=None, role=None, policies=()):
    row = {"movement_id": mid, "name": mid, "countries": [country],
           "timeframe": {"start": start, "end": end}, "policies": list(policies)}
    if scope is not None:
        row["scope"] = scope
    if role is not None:
        row["country_drift_role"] = role
    return row


def report(movements, *, units=None, policies=(), as_of=2026, geography=None):
    return AUDIT.build_report(units or registry("AAA", "BBB"), movements, set(policies), geography or {}, [], as_of)


def country(output, code="AAA"):
    return next(row for row in output["countries"] if row["iso3"] == code)


def test_local_supranational_and_context_records_never_fill_primary_national_history():
    result = report([
        movement("local", 1700, 2026, scope="subnational"),
        movement("union", 1750, "ongoing", scope="supranational"),
        movement("context", 1800, 2026, role="context_only"),
        movement("first", 1900, 1902), movement("last", 1905, 1906),
    ])
    row = country(result)
    assert result["slider_floor"] == 1900
    assert row["counts"]["national"] == 3
    assert row["counts"]["subnational"] == row["counts"]["supranational"] == 1
    assert row["national_history"]["first_start_year"] == 1800
    assert row["primary_national_history"]["first_start_year"] == 1900
    assert row["primary_national_history"]["internal_gaps"] == [
        {"from_year": 1903, "through_year": 1904, "years": 2}]
    assert row["national_history"]["internal_gaps"] == []


def test_merged_inclusive_intervals_report_only_true_internal_authored_gaps():
    result = report([movement("later", 1910, "ongoing"), movement("overlap", 1902, 1905),
                     movement("first", 1900, 1903), movement("adjacent", 1906, 1906)])
    history = country(result)["national_history"]
    assert history["merged_intervals"] == [
        {"from_year": 1900, "through_year": 1906}, {"from_year": 1910, "through_year": 2026}]
    assert history["internal_gaps"] == [{"from_year": 1907, "through_year": 1909, "years": 3}]
    assert history["first_start_year"] == 1900
    assert history["last_start_year"] == 1910
    assert history["last_covered_year"] == 2026
    assert [row["movement_id"] for row in history["intervals"]] == ["first", "overlap", "adjacent", "later"]


def test_future_records_do_not_supply_coverage_or_move_slider_floor():
    result = report([movement("future", 2030, 2035)])
    row = country(result)
    assert result["slider_floor"] == 2026
    assert row["counts"]["future_national"] == 1
    assert row["national_history"]["first_start_year"] is None
    assert row["national_history"]["merged_intervals"] == []
    assert row["national_history"]["intervals"][0]["included_by_as_of_year"] is False


def test_policy_reference_counts_require_a_nonempty_fully_resolved_list():
    result = report([movement("empty", 1900, 1901), movement("partial", 1902, 1903, policies=["known", "absent"]),
                     movement("complete", 1904, 1905, policies=["known"])], policies=["known"])
    row = country(result)
    assert row["counts"]["national_with_complete_policy_references"] == 1
    assert row["counts"]["national_with_incomplete_policy_references"] == 2
    assert row["national_history"]["intervals"][1]["missing_policy_ids"] == ["absent"]


def test_factual_policy_events_supply_separate_policy_history_without_creating_movements():
    policies = [
        {"policy_id": "earliest_local", "countries": ["AAA"], "timeframe": {"start": 1700}, "scope": "subnational"},
        {"policy_id": "earliest_union", "countries": ["AAA"], "timeframe": {"start": 1750}, "scope": "supranational"},
        {"policy_id": "factual_event", "countries": ["AAA"], "timeframe": {"start": 1800, "enacted_date": "1810-05-02"}},
        {"policy_id": "coded_policy", "countries": ["AAA"], "timeframe": {"start": 1850}, "axes_moved": [{"axis": "fiscal.tax_income", "direction": "+"}]},
        {"policy_id": "future_policy", "countries": ["AAA"], "timeframe": {"start": 2030}},
    ]
    result = AUDIT.build_report(registry("AAA"), [], {row["policy_id"] for row in policies}, {}, [], 2026, policy_records=policies)
    row = country(result)
    assert row["national_history"]["first_start_year"] is None
    assert row["national_policy_history"]["first_year"] == 1810
    assert row["national_policy_history"]["earliest_policies"][0]["date_basis"] == "enacted_date_year"
    assert row["counts"]["national_policies"] == 2
    assert row["counts"]["national_policies_without_axis_coding"] == 1
    assert row["counts"]["national_policies_with_axis_coding"] == 1
    assert result["summary"]["authored_movement_records"] == 0


def test_registry_preserves_no_history_units_and_separates_historical_identity():
    units = registry("AAA", "BBB") + [{"iso3": "SUN", "name": "Soviet Union", "kind": "historical"}]
    result = report([movement("prior_state", 1922, 1991, country="SUN")], units=units,
                    geography={"AAA": {"feature_names": ["AAA"], "linkage": "iso_numeric"}})
    assert country(result, "AAA")["has_map_geometry"] is True
    assert country(result, "BBB")["has_map_geometry"] is False
    assert country(result, "AAA")["national_history"]["first_start_year"] is None
    assert result["summary"]["country_or_territory"]["without_national_history"] == 2
    assert result["summary"]["historical"]["with_national_history"] == 1
    assert "not automatically attributed" in result["modern_geography_note"]


@pytest.mark.parametrize("start,end", [(True, 2000), (2000, 1999), (1900, "forever"), (0, 1800)])
def test_invalid_dates_fail_loudly(start, end):
    with pytest.raises(ValueError, match="invalid timeframe"):
        report([movement("invalid", start, end)])


def test_duplicates_and_unregistered_country_codes_cannot_silently_disappear():
    with pytest.raises(ValueError, match="Duplicate registry"):
        AUDIT.validate_registry(registry("AAA", "AAA"))
    with pytest.raises(ValueError, match="absent from registry"):
        report([movement("unknown", 1900, 1910, country="ZZZ")])
    with pytest.raises(ValueError, match="Duplicate movement"):
        report([movement("duplicate", 1900, 1910)] * 2)


def test_report_order_is_deterministic_and_no_leading_history_is_invented():
    movements = [movement("late", 1950, 1960), movement("early", 1900, 1910)]
    left = report(movements, units=registry("AAA", "BBB"))
    right = report(list(reversed(movements)), units=registry("BBB", "AAA"))
    assert left == right
    assert country(left)["national_history"]["internal_gaps"][0]["from_year"] == 1911
    assert country(left, "BBB")["national_history"]["internal_gaps"] == []


def test_real_registry_matches_iso_inventory_without_calling_all_units_sovereign():
    rows = AUDIT.validate_registry(json.loads((ROOT / "data/atlas/countries.json").read_text()))
    assert len([row for row in rows if row["kind"] == "country_or_territory"]) == 249
    assert {row["iso3"] for row in rows if row["kind"] == "historical"} == {"CSK", "SUN", "YUG"}
    assert next(row for row in rows if row["iso3"] == "XKX")["kind"] == "disputed"
    geography, unassigned = AUDIT.map_coverage(ROOT, rows)
    assert geography["XKX"]["linkage"] == "supplemental_name_only"
    assert {row["name"] for row in unassigned} == {"N. Cyprus", "Somaliland"}
    assert "SGP" not in geography  # The small-scale map omits a registered, authored country.
