"""Synthetic checks for the guarded ALMP employment calibration."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


RUNNER = Path(__file__).resolve().parents[1] / "scripts/run_oecd_almp_low_education_employment_2026.py"
SPEC = importlib.util.spec_from_file_location("almp_employment_runner", RUNNER)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def test_categorical_event_boundaries_are_symmetric() -> None:
    assert module.event_indicators(0.05) == (1, 0)
    assert module.event_indicators(-0.05) == (0, 1)
    assert module.event_indicators(0.049999) == (0, 0)
    assert module.event_indicators(-0.049999) == (0, 0)
    with pytest.raises(ValueError):
        module.event_indicators(float("nan"))


def test_preflight_requests_only_outcome_key_columns(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    class FakeParquet:
        metadata = type("Metadata", (), {"num_rows": 1184864})()
        schema = type("Schema", (), {"names": module.OUTCOME_KEY_COLUMNS + ["value"]})()

    calls = []

    def read_keys(path: Path, *, columns: list[str]) -> pd.DataFrame:
        calls.append(columns)
        assert columns == module.OUTCOME_KEY_COLUMNS
        return pd.DataFrame({"freq": ["A", "A"], "citizen": ["TOTAL", "TOTAL"],
                             "isced11": ["ED0-2", "ED0-2"], "sex": ["T", "T"],
                             "age": ["Y25-64", "Y25-64"], "unit": ["PC", "PC"],
                             "geo_code": ["AT", "AT"], "period": [2005, 2006]})

    monkeypatch.setattr(module.pq, "ParquetFile", lambda path: FakeParquet())
    monkeypatch.setattr(module.pd, "read_parquet", read_keys)
    assert module.selected_keys(tmp_path) == {("AUT", 2005), ("AUT", 2006)}
    assert calls == [module.OUTCOME_KEY_COLUMNS]


def synthetic_panel(sign: int) -> tuple[pd.DataFrame, dict[str, int]]:
    rows = []
    for country_number in range(30):
        for year in range(2005, 2019):
            category = (country_number + 3 * year) % 5
            increase, decrease = int(category == 0), int(category == 1)
            baseline = (55 + country_number * 0.25 + (year - 2005) * 0.1
                        + 0.13 * math.sin(country_number * 0.43 + year * 0.32))
            log_gdp = (9.2 + country_number * 0.03 + (year - 2005) * 0.006
                       + 0.018 * math.cos(country_number * 0.36 - year * 0.29))
            noise = 0.08 * math.sin(country_number * 1.7 + year * 0.9)
            rows.append({"country_iso3": f"C{country_number:02d}", "year": year,
                         "increase": increase, "decrease": decrease,
                         "baseline_rate": baseline, "log_gdp_pc": log_gdp,
                         "y": sign * (0.72 * increase - 0.18 * decrease) + noise})
    panel = pd.DataFrame(rows)
    gate = {"valid_rows": len(panel), "valid_countries": panel.country_iso3.nunique(),
            "increase_rows": int(panel.increase.sum()),
            "increase_countries": panel.loc[panel.increase.eq(1), "country_iso3"].nunique(),
            "decrease_rows": int(panel.decrease.sum()),
            "decrease_countries": panel.loc[panel.decrease.eq(1), "country_iso3"].nunique()}
    return panel, gate


@pytest.mark.parametrize("sign,expected", [(1, "SUPPORTED"), (-1, "REFUTED")])
def test_synthetic_primary_contrast_uses_both_events(sign: int, expected: str) -> None:
    panel, gate = synthetic_panel(sign)
    result = module.estimate(panel, gate)
    assert result["verdict"] == expected
    primary = result["primary"]
    assert primary is not None
    assert sign * primary["contrast_increase_minus_decrease_pp"] >= module.SESOI
    assert primary["p_value_two_sided"] <= module.P_MAX


def test_insufficient_complete_events_are_inconclusive() -> None:
    panel, gate = synthetic_panel(1)
    gate["decrease_rows"] = 49
    result = module.estimate(panel, gate)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["primary"] is None
