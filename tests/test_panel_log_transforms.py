"""Growth labels must use exact within-country calendar lags."""

import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_panel_fe import transform, transform_panel_values


def test_annual_log_change_uses_prior_calendar_year_in_same_country():
    frame = pd.DataFrame(
        [
            ("BBB", 2001, 40.0),
            ("AAA", 2002, 30.0),
            ("AAA", 2000, 10.0),
            ("BBB", 2000, 20.0),
            ("AAA", 2001, 15.0),
        ],
        columns=["country_iso3", "year", "value"],
    )

    result = transform_panel_values(frame, "value", "annual_log_change")
    values = result.set_index(["country_iso3", "year"])["value"]

    assert math.isnan(values.loc["AAA", 2000])
    assert values.loc["AAA", 2001] == pytest.approx(math.log(15 / 10))
    assert values.loc["AAA", 2002] == pytest.approx(math.log(30 / 15))
    assert math.isnan(values.loc["BBB", 2000])
    assert values.loc["BBB", 2001] == pytest.approx(math.log(40 / 20))


def test_five_year_log_difference_requires_exact_year_not_previous_row():
    frame = pd.DataFrame(
        [
            ("AAA", 2000, 10.0),
            ("AAA", 2004, 15.0),
            ("AAA", 2005, 20.0),
            ("AAA", 2010, 80.0),
            ("BBB", 2005, 50.0),
        ],
        columns=["country_iso3", "year", "value"],
    )

    result = transform_panel_values(frame, "value", "log_diff_5y")
    values = result.set_index(["country_iso3", "year"])["value"]

    assert math.isnan(values.loc["AAA", 2004])
    assert values.loc["AAA", 2005] == pytest.approx(math.log(20 / 10))
    assert values.loc["AAA", 2010] == pytest.approx(math.log(80 / 20))
    assert math.isnan(values.loc["BBB", 2005])


def test_log_growth_without_country_year_keys_fails_closed():
    with pytest.raises(ValueError, match="country-year keys are required"):
        transform(pd.Series([10.0, 20.0]), "annual_log_change")
