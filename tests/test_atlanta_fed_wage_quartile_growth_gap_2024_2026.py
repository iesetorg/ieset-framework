"""Synthetic contract checks; never open Atlanta wage values."""

import pytest

from scripts.run_atlanta_fed_wage_quartile_growth_gap_2024_2026 import (
    MONTHS, YEARS, classify, hac_mean_test,
)


def test_fixed_roster_and_missing_shutdown_month():
    assert len(MONTHS) == 32
    assert MONTHS[0] == "2024-01"
    assert MONTHS[-1] == "2026-09"
    assert "2025-10" not in MONTHS
    assert [sum(month.startswith(str(year)) for month in MONTHS) for year in YEARS] == [12, 11, 9]


def test_mirrored_thresholds_and_year_sign_guard():
    positive = {str(year): 0.7 for year in YEARS}
    negative = {str(year): -0.7 for year in YEARS}
    support = {"support_one_sided_p": 0.02, "refute_one_sided_p": 0.98}
    refute = {"support_one_sided_p": 0.98, "refute_one_sided_p": 0.02}
    assert classify(support, positive)[0] == "SUPPORTED"
    assert classify(refute, negative)[0] == "REFUTED"
    assert classify(support, {"2024": 0.7, "2025": -0.1, "2026": 0.7})[0] == "PARTIAL"
    assert classify(refute, {"2024": -0.7, "2025": 0.1, "2026": -0.7})[0] == "PARTIAL"
    assert classify({"support_one_sided_p": 0.026, "refute_one_sided_p": 0.98}, positive)[0] == "PARTIAL"


def test_hac_contract_rejects_short_or_degenerate_series():
    with pytest.raises(ValueError, match="exactly 32"):
        hac_mean_test([0.0] * 31)
    with pytest.raises(ValueError, match="variance"):
        hac_mean_test([1.0] * 32)
    result = hac_mean_test([0.6 + 0.1 * ((i % 4) - 1.5) for i in range(32)])
    assert result["hac_lags"] == 12
    assert result["t_df"] == 31
    assert result["hac_se_pp"] > 0
    assert 0 <= result["support_one_sided_p"] <= 1
    assert 0 <= result["refute_one_sided_p"] <= 1
