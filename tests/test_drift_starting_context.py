"""Starting context must not be mistaken for a drift-score offset."""

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_drift_starting_context.py"
SPEC = importlib.util.spec_from_file_location("build_drift_starting_context", SCRIPT)
assert SPEC and SPEC.loader
CONTEXT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CONTEXT)


def test_opening_window_never_uses_future_or_distant_past():
    rows = [(1989, 10.0), (1995, 20.0), (2000, 30.0), (2001, 40.0)]
    assert CONTEXT.select_observation(rows, 2000) == (2000, 30.0, "opening")
    assert CONTEXT.select_observation(rows, 1990) == (1989, 10.0, "opening")
    assert CONTEXT.select_observation(rows, 1994) == (1989, 10.0, "opening")
    assert CONTEXT.select_observation([(1989, 10.0), (2001, 40.0)], 1996) == (2001, 40.0, "later_only")
    assert CONTEXT.select_observation(rows, 1980) == (1989, 10.0, "later_only")
    assert CONTEXT.select_observation([], 2000) is None


def test_fiscal_fallback_and_regulatory_quality_remain_separate():
    drift = {
        "countries": {
            "AAA": {"first_coded_year": 2000},
            "BBB": {"first_coded_year": 1901},
            "CCC": {"first_coded_year": 2000},
        }
    }
    rows = {
        "expense": {"AAA": [(2010, 30.0)], "CCC": [(2010, 30.0)]},
        "consumption": {"AAA": [(1999, 15.0)], "CCC": [(2001, 12.0)]},
        "wgi_regulatory_quality": {"AAA": [(2001, 0.8)], "BBB": [(1996, 1.1)]},
    }
    built = CONTEXT.build_context(drift, rows)
    aaa = built["countries"]["AAA"]
    assert aaa["fiscal"]["metric_id"] == "government_final_consumption_pct_gdp"
    assert aaa["fiscal"]["relation_to_first_coded_year"] == "opening"
    assert aaa["market_institutions"]["metric_id"] == "wgi_regulatory_quality_estimate"
    assert aaa["market_institutions"]["relation_to_first_coded_year"] == "later_only"
    assert aaa["market_institutions"]["value"] == 0.8
    assert "statist_drift" not in aaa
    assert built["countries"]["BBB"]["market_institutions"]["observed_year"] == 1996
    assert built["countries"]["BBB"]["market_institutions"]["relation_to_first_coded_year"] == "later_only"
    assert built["countries"]["CCC"]["fiscal"]["observed_year"] == 2001
    assert built["countries"]["CCC"]["fiscal"]["metric_id"] == "government_final_consumption_pct_gdp"
