"""Generic panel runs must not turn distinct source measures into one mean."""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_panel_fe import normalise_panel


def test_ilo_sex_age_rows_require_an_explicit_slice():
    rows = pd.DataFrame(
        {
            "country_iso3": ["USA", "USA"],
            "year": [2022, 2022],
            "sex": ["SEX_T", "SEX_T"],
            "classif1": ["AGE_YTHADULT_Y15-24", "AGE_YTHADULT_YGE25"],
            "value": [12.0, 4.0],
        }
    )
    assert normalise_panel(rows, "ilostat", series="UNE_2EAP_SEX_AGE_RT_A") is None
    selected = normalise_panel(rows.iloc[:1], "ilostat", series="UNE_2EAP_SEX_AGE_RT_A")
    assert selected is not None
    assert selected["value"].tolist() == [12.0]


def test_oecd_mean_and_median_minimum_wage_ratios_cannot_be_blended():
    rows = pd.DataFrame(
        {
            "REF_AREA": ["USA", "USA"],
            "period": [2022, 2022],
            "AGGREGATION_OPERATION": ["MEAN", "MEDIAN"],
            "value": [35.0, 45.0],
        }
    )
    assert normalise_panel(rows, "oecd", series="MWUSD") is None
    selected = normalise_panel(rows.iloc[1:], "oecd", series="MWUSD")
    assert selected is not None
    assert selected["value"].tolist() == [45.0]
