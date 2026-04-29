"""Tests for the upgraded multi-metric threshold parser.

Covers the four failing examples from real result_card.md files plus
regression checks for the existing simple-threshold path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_multi_metric_checklist as mm  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic panels — small enough to reason about, large enough to span the
# code paths (peer set with >=3 peers, multiple years, multiple series via
# concat).
# ---------------------------------------------------------------------------

def _gdp_panel() -> pd.DataFrame:
    """Synthetic GDP-pc panel: CUB roughly flat 1960->2023, peers grow ~4x."""
    rows = []
    # CUB: 3000 in 1960, 3500 in 2023 -> ratio ~1.17 (< 1.5)
    rows += [("CUB", 1958, 3500), ("CUB", 1960, 3000), ("CUB", 2023, 3500)]
    # LatAm peers: 2000 -> 8000 (ratio 4.0)
    for code, base in [("DOM", 1500), ("CRI", 2000), ("PAN", 1800),
                       ("MEX", 2500), ("PER", 1700), ("COL", 1900),
                       ("BRA", 2100), ("CHL", 2300), ("ARG", 3500),
                       ("URY", 3000)]:
        rows.append((code, 1960, base))
        rows.append((code, 2023, base * 4.0))
    # 1958 ranks: CUB at 3500 should be top 5 against this universe.
    for code, base in [("DOM", 1500), ("CRI", 2000), ("PAN", 1800),
                       ("MEX", 2500), ("PER", 1700), ("COL", 1900),
                       ("BRA", 2100), ("CHL", 2300), ("ARG", 3700),
                       ("URY", 3200)]:
        rows.append((code, 1958, base))
    # 2023 ranks: CUB at 3500 — peers all > 6000 so CUB should be near bottom
    # universe of 11 (CUB + 10 peers).
    return pd.DataFrame(rows, columns=["country", "year", "value"])


def _hdi_panel() -> pd.DataFrame:
    """Synthetic HDI panel: CUB nearly flat 1990->2022, peers gain >0.10."""
    rows = []
    rows += [("CUB", 1990, 0.760), ("CUB", 2022, 0.770)]  # diff 0.010 (< 0.03)
    for code, b1990, b2022 in [
        ("DOM", 0.62, 0.77),
        ("CRI", 0.65, 0.81),
        ("PAN", 0.66, 0.81),
        ("MEX", 0.65, 0.78),
        ("PER", 0.61, 0.76),
        ("COL", 0.60, 0.76),
        ("BRA", 0.61, 0.76),
        ("CHL", 0.70, 0.85),
        ("ARG", 0.70, 0.84),
        ("URY", 0.69, 0.83),
    ]:
        rows.append((code, 1990, b1990))
        rows.append((code, 2022, b2022))
    return pd.DataFrame(rows, columns=["country", "year", "value"])


# ---------------------------------------------------------------------------
# The four failing examples from real result_card.md
# ---------------------------------------------------------------------------

def test_cuba_metric1_ratio_with_peer_median_and():
    """CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5 AND LatAm peer median 2023/1960 ratio > 3.0"""
    df = _gdp_panel()
    expr = "CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5 AND LatAm peer median 2023/1960 ratio > 3.0"
    res = mm._evaluate_complex_threshold(expr, "CUB", df)
    assert res is not None
    assert res["met"] is True, res


def test_cuba_metric2_rank_top_and_bottom():
    """CUB rank in top 5 (1958) AND CUB rank in bottom 10 out of 20 LatAm (2023)"""
    df = _gdp_panel()
    expr = "CUB rank in top 5 (1958) AND CUB rank in bottom 10 out of 20 LatAm (2023)"
    res = mm._evaluate_complex_threshold(expr, "CUB", df)
    assert res is not None
    # CUB ranked top by value=3500 in 1958 universe; bottom in 2023 vs LatAm
    assert res["met"] is True, res


def test_cuba_metric9_peer_median_diff():
    """CUB HDI 2022 - CUB HDI 1990 < 0.03 AND LatAm peer median HDI 2022 - 1990 > 0.10"""
    df = _hdi_panel()
    expr = "CUB HDI 2022 - CUB HDI 1990 < 0.03 AND LatAm peer median HDI 2022 - 1990 > 0.10"
    res = mm._evaluate_complex_threshold(expr, "CUB", df)
    assert res is not None
    assert res["met"] is True, res


def test_cuba_metric8_event_count_pending():
    """>=2 major monetary-regime changes ... in a 30-year window — must
    return PENDING with an event_count_request diagnostic."""
    df = _gdp_panel()
    expr = ">=2 major monetary-regime changes (redenomination, FX-regime switch, or >100% annualised inflation episode) in a 30-year window"
    res = mm._evaluate_complex_threshold(expr, "CUB", df)
    assert res is not None
    assert res["met"] is None
    assert res["event_count_request"] is not None
    assert "monetary-regime" in res["event_count_request"]


# ---------------------------------------------------------------------------
# Negative-case checks (NOT_MET path)
# ---------------------------------------------------------------------------

def test_negative_cuba_grows_fast():
    """If CUB 2023 GDP is high enough the ratio clause fails -> overall NOT_MET."""
    df = _gdp_panel().copy()
    df.loc[(df["country"] == "CUB") & (df["year"] == 2023), "value"] = 9000
    expr = "CUB 2023 GDP pc / CUB 1960 GDP pc < 1.5 AND LatAm peer median 2023/1960 ratio > 3.0"
    res = mm._evaluate_complex_threshold(expr, "CUB", df)
    assert res is not None
    assert res["met"] is False


# ---------------------------------------------------------------------------
# Regression: legacy simple thresholds still parse via _apply_numeric_threshold
# ---------------------------------------------------------------------------

def test_legacy_simple_threshold_gt():
    """The existing _apply_numeric_threshold path must still work."""
    assert mm._apply_numeric_threshold(80.0, ">60%") is True
    assert mm._apply_numeric_threshold(50.0, ">60%") is False
    assert mm._apply_numeric_threshold(7.0, ">=7") is True
    assert mm._apply_numeric_threshold(6.99, ">=7") is False


def test_legacy_unparseable_returns_none():
    """Nonsense thresholds still return None from the legacy parser."""
    assert mm._apply_numeric_threshold(5.0, "approximately seven") is None


# ---------------------------------------------------------------------------
# Additivity: when complex evaluator can't recognise an expression it must
# return None so the caller falls back.
# ---------------------------------------------------------------------------

def test_unrecognised_expression_returns_none():
    df = _gdp_panel()
    res = mm._evaluate_complex_threshold(">25% cumulative real GDP contraction 1989-1993", "CUB", df)
    # This is a single-clause numeric threshold the legacy path handles.
    # The complex evaluator should return None, signalling fall-through.
    assert res is None


def test_split_logical_basic():
    combinator, clauses = mm._split_logical("A AND B")
    assert combinator == "AND"
    assert clauses == ["A", "B"]
    # AND/OR splits are case-sensitive: lowercase "and"/"or" in natural
    # prose (e.g. "between deep-reform and shallow-reform") must not split.
    combinator, clauses = mm._split_logical("A OR B")
    assert combinator == "OR"
    combinator, clauses = mm._split_logical("between deep and shallow groups")
    assert combinator == "SINGLE"
    combinator, clauses = mm._split_logical("just one clause")
    assert combinator == "SINGLE"


# ---------------------------------------------------------------------------
# Korea / Soviet parser-extension tests (round 2).
# ---------------------------------------------------------------------------

def _korea_gdp_panel() -> pd.DataFrame:
    """ROK >> DPRK GDP-pc panel covering 2020-2023."""
    rows = [
        ("KOR", 2020, 38500), ("KOR", 2021, 39950),
        ("KOR", 2022, 41100), ("KOR", 2023, 41800),
        ("PRK", 2020, 1230), ("PRK", 2021, 1229),
        ("PRK", 2022, 1227), ("PRK", 2023, 1265),
    ]
    return pd.DataFrame(rows, columns=["country", "year", "value"])


def _korea_le_panel() -> pd.DataFrame:
    """Life-expectancy gap for ROK/DPRK 2020-2023."""
    rows = [
        ("KOR", 2020, 83.5), ("KOR", 2021, 83.6),
        ("KOR", 2022, 82.7), ("KOR", 2023, 83.5),
        ("PRK", 2020, 72.4), ("PRK", 2021, 72.6),
        ("PRK", 2022, 72.8), ("PRK", 2023, 73.0),
    ]
    return pd.DataFrame(rows, columns=["country", "year", "value"])


def test_two_country_ratio_rok_dprk_gdp():
    """'>15x ROK/DPRK GDP per capita PPP ratio in 2023' should evaluate MET."""
    df = _korea_gdp_panel()
    expr = ">15x ROK/DPRK GDP per capita PPP ratio in 2023"
    res = mm._evaluate_complex_threshold(expr, "KOR", df)
    assert res is not None
    assert res["met"] is True, res


def test_two_country_ratio_suffix_op():
    """'ROK/DPRK nightlights radiance per unit area >100x' (op-suffix shape)."""
    rows = [("KOR", 2023, 9.9), ("PRK", 2023, 0.06)]
    df = pd.DataFrame(rows, columns=["country", "year", "value"])
    expr = "ROK/DPRK nightlights radiance per unit area >100x"
    res = mm._evaluate_complex_threshold(expr, "KOR", df)
    assert res is not None
    assert res["met"] is True, res


def test_two_country_diff_life_expectancy():
    """'>8 year ROK-minus-DPRK life expectancy gap'."""
    df = _korea_le_panel()
    expr = ">8 year ROK-minus-DPRK life expectancy gap"
    res = mm._evaluate_complex_threshold(expr, "KOR", df)
    assert res is not None
    assert res["met"] is True, res


def test_two_list_peer_set_gap_soviet_metric10():
    """Soviet metric 10: deep-reform vs shallow-reform 2000-relative-to-1989 gap."""
    rows = []
    # Deep reform — recover to ~100% of 1989
    for c, base in [("EST", 18000), ("LVA", 14000), ("POL", 11000), ("CZE", 14000)]:
        rows.append((c, 1989, base))
        rows.append((c, 2000, base * 1.0))   # ~100% of 1989
    # Shallow reform — recover to ~50% of 1989
    for c, base in [("BLR", 11000), ("UKR", 10000), ("UZB", 7000), ("TKM", 6000)]:
        rows.append((c, 1989, base))
        rows.append((c, 2000, base * 0.6))   # ~60% of 1989
    df = pd.DataFrame(rows, columns=["country", "year", "value"])
    expr = (
        ">20 percentage point gap in 2000-GDP-pc-relative-to-1989 between "
        "deep-reform (EST, LVA, POL, CZE) and shallow-reform "
        "(BLR, UKR, UZB, TKM) FSU/CEE republics"
    )
    res = mm._evaluate_complex_threshold(expr, "RUS", df)
    assert res is not None
    assert res["met"] is True, res


def test_two_list_peer_set_negative():
    """Same shape but small gap -> NOT_MET."""
    rows = []
    for c, base in [("EST", 18000), ("LVA", 14000), ("POL", 11000), ("CZE", 14000)]:
        rows.append((c, 1989, base))
        rows.append((c, 2000, base * 1.0))
    for c, base in [("BLR", 11000), ("UKR", 10000), ("UZB", 7000), ("TKM", 6000)]:
        rows.append((c, 1989, base))
        rows.append((c, 2000, base * 0.95))   # only 5pp gap
    df = pd.DataFrame(rows, columns=["country", "year", "value"])
    expr = (
        ">20 percentage point gap in 2000-GDP-pc-relative-to-1989 between "
        "deep-reform (EST, LVA, POL, CZE) and shallow-reform "
        "(BLR, UKR, UZB, TKM) FSU/CEE republics"
    )
    res = mm._evaluate_complex_threshold(expr, "RUS", df)
    assert res is not None
    assert res["met"] is False, res


def test_emigration_word_boundary_no_false_positive_ratio():
    """'emigration' contains the substring 'ratio' but must NOT trigger
    the gap/ratio classifier branch."""
    assert mm._has_word("net-emigration sustained 20 years", "ratio") is False
    assert mm._has_word("a sample emigration record", "gap") is False
    assert mm._has_word("a sample emigration record", "difference") is False
    # Real ratio should still match.
    assert mm._has_word("ROK/DPRK GDP ratio is large", "ratio") is True


def test_event_count_calendar_window_met():
    """Cumulative-count event panel: '>=2 events ... 1989-1998' MET when
    panel max == 3."""
    rows = [
        ("RUS", 1989, 0), ("RUS", 1990, 0), ("RUS", 1991, 1),
        ("RUS", 1992, 1), ("RUS", 1993, 1), ("RUS", 1994, 1),
        ("RUS", 1995, 1), ("RUS", 1996, 1), ("RUS", 1997, 1),
        ("RUS", 1998, 3),
    ]
    df = pd.DataFrame(rows, columns=["country", "year", "value"])
    expr = ">=2 major currency-regime events 1989-1998"
    res = mm._evaluate_complex_threshold(expr, "RUS", df)
    assert res is not None
    assert res["met"] is True, res


def test_event_count_calendar_window_not_met():
    """Same panel but threshold raised to >=5 -> NOT_MET."""
    rows = [
        ("RUS", 1989, 0), ("RUS", 1990, 0), ("RUS", 1991, 1),
        ("RUS", 1992, 1), ("RUS", 1998, 3),
    ]
    df = pd.DataFrame(rows, columns=["country", "year", "value"])
    expr = ">=5 major currency-regime events 1989-1998"
    res = mm._evaluate_complex_threshold(expr, "RUS", df)
    assert res is not None
    assert res["met"] is False, res
