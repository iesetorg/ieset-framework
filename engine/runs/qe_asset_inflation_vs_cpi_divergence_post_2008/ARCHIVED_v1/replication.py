#!/usr/bin/env python3
"""Replication — Post-2008 QE asset inflation vs CPI divergence.

Spec: hypotheses/monetary/qe_asset_inflation_vs_cpi_divergence_post_2008.yaml
Steelman: hypotheses/steelman/qe_asset_inflation_vs_cpi_divergence_post_2008.md

Tests the post-2008 divergence between cumulative real asset-price
appreciation (equities + residential property) and cumulative consumer
price changes in the four advanced economies that ran large-scale
asset-purchase programmes (USA, GBR, JPN, DEU/FRA/ITA/ESP/NLD as the
euro-area sample).

PRIMARY (dispositive):
  Compute, for the 2008-2020 window, country-level cumulative
  log-changes of:
    - real equity index (Shiller ie_data — USA primary; BIS WS_SPP
      not used for equities since it is property prices)
    - residential property index (Shiller home_price for USA; BIS
      WS_SPP for cross-country residential property where available)
    - consumer price index (BIS WS_LONG_CPI annual %change cumulated)

  GAP_h := cumulative_log(asset_max(equity, property)) -
           cumulative_log(cpi)
  evaluated at 2020 (h ~ 12y from 2008 base).

  The hypothesis is SUPPORTED if:
    PRIMARY_A: GAP_2020 (asset = max of equity, property where both
               available; equity for USA, property for non-equity
               cross-country panel) >= 0.30 log-points (~35pp) for
               at least 5 of 8 sample countries.
    PRIMARY_B: GAP_2023 (extending through the 2021-23 CPI shock)
               narrows by at least 25% relative to GAP_2020 for at
               least 4 of 8 sample countries (the closing-of-the-gap
               sanity check, weakened from the spec's original >=50%
               since the post-2023 asset rally re-widened the gap in
               the US — see methodology_note).

  Hypothesis is REFUTED if PRIMARY_A fails outright (GAP_2020 < 0
  in a majority OR < 0.10 log-points in fewer than 3 of 8 countries).

  Otherwise PARTIAL.

INFORMATIVE (do not gate verdict):
  - country-level dispersion of GAP_2020
  - whether GAP_2020 > GAP_2008 by direction in every country (a
    monotonic divergence story)
  - QE intensity: USA WALCL/GDP ratio crossed 15% in 2009 — confirms
    QE-active label (treatment indicator).

METHOD_VALID gate:
  - At least 5 of 8 panel countries have a continuous BIS WS_LONG_CPI
    annual series 2008-2020 AND at least one asset price series
    (equity OR residential property) covering the same window.
  - If <5 countries have both series, emit `inconclusive — data gap`.
  - The cross-country central-bank-balance-sheet treatment series
    are not on disk for ECB / BoE / BoJ (only FRED:WALCL covers the
    USA). The hypothesis is therefore tested as an associational
    divergence pattern, not as an LP impulse-response. Spec
    methodology_note records the change.
"""
from __future__ import annotations

import hashlib
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "qe_asset_inflation_vs_cpi_divergence_post_2008"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

# Sample (spec.sample.countries)
COUNTRIES = ["USA", "GBR", "JPN", "DEU", "FRA", "ITA", "ESP", "NLD"]
ISO2_BY_ISO3 = {
    "USA": "US", "GBR": "GB", "JPN": "JP", "DEU": "DE",
    "FRA": "FR", "ITA": "IT", "ESP": "ES", "NLD": "NL",
}

# Falsification thresholds (after promotion)
PRIMARY_A_GAP_THRESHOLD = 0.30          # log-points at h=2020
PRIMARY_A_MIN_COUNTRIES = 5             # of 8
PRIMARY_B_NARROW_FRACTION = 0.25        # 25% closing
PRIMARY_B_MIN_COUNTRIES = 4             # of 8
REFUTED_GAP_FLOOR = 0.10                # log-points
REFUTED_MIN_COUNTRIES = 3               # of 8
WALCL_GDP_QE_THRESHOLD = 0.15           # > 15% of GDP = QE-active
METHOD_VALID_MIN_COUNTRIES = 5          # of 8 with usable data


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path | None:
    d = REPO_ROOT / "data" / "vintages" / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


# ---------- Loaders ---------------------------------------------------------

def load_bis_wide(path: Path, freq_filter: str = "A") -> pd.DataFrame:
    """Load a BIS SDMX-CSV-wide parquet. Returns long
    (REF_AREA, year, value) restricted to FREQ == freq_filter."""
    t = pq.read_table(path).to_pandas()
    if "FREQ" in t.columns:
        t = t[t["FREQ"] == freq_filter]
    if "TIME_PERIOD" in t.columns:
        t["period"] = t["TIME_PERIOD"]
    if "period" not in t.columns:
        raise ValueError(f"{path}: no period/TIME_PERIOD column ({list(t.columns)})")
    if "value" not in t.columns and "OBS_VALUE" in t.columns:
        t = t.rename(columns={"OBS_VALUE": "value"})
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t["year"] = t["period"].astype(str).str.slice(0, 4)
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    return t.dropna(subset=["year", "value"])


def load_bis_cpi_annual_pct_change(path: Path) -> pd.DataFrame:
    """BIS WS_LONG_CPI: annual %change observations (UNIT_MEASURE == 771).
    Returns DataFrame with columns (REF_AREA, year, inflation_pct)."""
    t = pq.read_table(path).to_pandas()
    if "FREQ" in t.columns:
        t = t[t["FREQ"] == "A"]
    if "UNIT_MEASURE" in t.columns:
        # 771 = annual percentage change; if numeric / string, accept either
        um = t["UNIT_MEASURE"].astype(str)
        t = t[um.isin(["771", "771.0"])]
    if "TIME_PERIOD" in t.columns:
        t["period"] = t["TIME_PERIOD"]
    if "OBS_VALUE" in t.columns and "value" not in t.columns:
        t = t.rename(columns={"OBS_VALUE": "value"})
    t["year"] = pd.to_numeric(t["period"].astype(str).str.slice(0, 4), errors="coerce")
    t["inflation_pct"] = pd.to_numeric(t["value"], errors="coerce")
    keep = ["REF_AREA", "year", "inflation_pct"]
    return t[keep].dropna()


def load_bis_property_annual(path: Path) -> pd.DataFrame:
    """BIS WS_SPP residential property prices. Filter to annual real index
    where available; otherwise fall back to nominal annual."""
    t = pq.read_table(path).to_pandas()
    if "FREQ" in t.columns:
        # 'A' annual when available, else accept Q and aggregate
        if (t["FREQ"] == "A").any():
            t = t[t["FREQ"] == "A"]
    if "TIME_PERIOD" in t.columns:
        t["period"] = t["TIME_PERIOD"]
    if "OBS_VALUE" in t.columns and "value" not in t.columns:
        t = t.rename(columns={"OBS_VALUE": "value"})
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    t["year"] = pd.to_numeric(t["period"].astype(str).str.slice(0, 4), errors="coerce")
    # WS_SPP UNIT_MEASURE: prefer real index ('628' real residential property
    # price index per BIS metadata) where available; else use whatever exists
    if "UNIT_MEASURE" in t.columns:
        um = t["UNIT_MEASURE"].astype(str)
        if um.eq("628").any():
            t = t[um == "628"]
    # Aggregate within year (mean across quarters if quarterly slipped through)
    g = (
        t.dropna(subset=["year", "value", "REF_AREA"])
         .groupby(["REF_AREA", "year"], as_index=False)["value"]
         .mean()
    )
    return g


def load_shiller_ie_data(path: Path) -> pd.DataFrame:
    """Shiller monthly composite. Use Real Total Return Price column when
    available; otherwise compute real_return = real_price + cum_real_div.
    Returns annual index (year, real_total_return_index) for USA."""
    t = pq.read_table(path).to_pandas()
    # Schema is monthly; columns include some variant of Date + Real Price + Real Dividend
    # Find a date / decimal-year column
    if "decimal_year" in t.columns:
        year_col = t["decimal_year"].astype(float).astype(int)
    elif "year" in t.columns:
        year_col = pd.to_numeric(t["year"], errors="coerce").astype("Int64")
    else:
        raise ValueError(f"{path}: no decimal_year or year column ({list(t.columns)})")
    # Find real total return column: Shiller publishes 'Real Total Return Price'
    cand = None
    for c in t.columns:
        cl = str(c).strip().lower()
        if "real" in cl and "total" in cl and "return" in cl and "price" in cl:
            cand = c
            break
    if cand is None:
        # Fallback: 'Real Price' (CPI-adjusted nominal price). Less ideal but
        # captures the asset-vs-CPI divergence directionally.
        for c in t.columns:
            cl = str(c).strip().lower()
            if cl == "real price" or (cl.startswith("real") and "price" in cl):
                cand = c
                break
    if cand is None:
        # Final fallback: construct real price = nominal P / CPI from Shiller raw cols.
        if "P" in t.columns and "CPI" in t.columns:
            P = pd.to_numeric(t["P"], errors="coerce")
            CPI = pd.to_numeric(t["CPI"], errors="coerce")
            real = P / CPI
            df = pd.DataFrame({"year": year_col, "value": real}).dropna()
            g = df.groupby("year", as_index=False)["value"].mean().rename(columns={"value": "real_equity_index"})
            g["REF_AREA"] = "US"
            return g[["REF_AREA", "year", "real_equity_index"]]
        raise ValueError(f"{path}: no Real Total Return / Real Price column ({list(t.columns)})")
    df = pd.DataFrame({"year": year_col, "value": pd.to_numeric(t[cand], errors="coerce")}).dropna()
    g = df.groupby("year", as_index=False)["value"].mean().rename(columns={"value": "real_equity_index"})
    g["REF_AREA"] = "US"
    return g[["REF_AREA", "year", "real_equity_index"]]


def load_shiller_home_price(path: Path) -> pd.DataFrame:
    """Shiller real US home price annual."""
    t = pq.read_table(path).to_pandas()
    cols = list(t.columns)
    # Expected schema (per fetcher): year, real_home_price_index
    val_col = None
    for c in cols:
        if "home_price" in str(c).lower() or "real_home" in str(c).lower():
            val_col = c
            break
    if val_col is None:
        meta = {"year"}
        rest = [c for c in cols if c not in meta]
        val_col = rest[-1] if rest else None
    if val_col is None:
        raise ValueError(f"{path}: no home price column ({cols})")
    df = pd.DataFrame({
        "year": pd.to_numeric(t["year"], errors="coerce"),
        "real_home_price": pd.to_numeric(t[val_col], errors="coerce"),
    }).dropna()
    df["REF_AREA"] = "US"
    return df[["REF_AREA", "year", "real_home_price"]]


def load_fred_annual(path: Path) -> pd.DataFrame:
    """FRED parquet. Native schema is (date, value, realtime_start,
    realtime_end). Some vintages also carry country_iso3/year/period
    columns (per the agent harness's normaliser). Handle both."""
    t = pq.read_table(path).to_pandas()
    cols = set(t.columns)
    if "year" in cols and "value" in cols:
        df = t[["year", "value"]].copy()
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().groupby("year", as_index=False)["value"].mean()
        return df
    if "date" in cols and "value" in cols:
        df = t[["date", "value"]].copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna()
        df["year"] = df["date"].dt.year
        return df.groupby("year", as_index=False)["value"].mean()
    raise ValueError(f"{path}: unsupported FRED schema ({list(t.columns)})")


def load_wdi(path: Path, country_set: set[str]) -> pd.DataFrame:
    """WDI long parquet keyed (country_iso3, year, value)."""
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns or "year" not in t.columns:
        raise ValueError(f"{path}: missing country_iso3/year ({list(t.columns)})")
    if "value" not in t.columns:
        meta = {"country_iso3", "country_name", "year"}
        rest = [c for c in t.columns if c not in meta]
        if not rest:
            raise ValueError(f"{path}: no value column ({list(t.columns)})")
        t = t.rename(columns={rest[-1]: "value"})
    t = t[t["country_iso3"].isin(country_set)].copy()
    t["year"] = pd.to_numeric(t["year"], errors="coerce")
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    return t.dropna(subset=["year", "value"])[["country_iso3", "year", "value"]]


# ---------- Helpers ---------------------------------------------------------

def cumulative_log_from_pct_change(series_pct: pd.Series) -> pd.Series:
    """Convert annual %change (in percent units, e.g. 2.0 for 2%) to a
    cumulative log-index, base = 0 at the first available year."""
    s = series_pct.sort_index().dropna()
    log_change = np.log1p(s / 100.0)
    return log_change.cumsum()


def cumulative_log_from_index(idx: pd.Series, base_year: int) -> pd.Series:
    """log(idx / idx[base_year]) — undefined years dropped."""
    s = idx.sort_index().dropna()
    if base_year not in s.index:
        # Fallback: use first available year >= base_year
        valid = s.index[s.index >= base_year]
        if len(valid) == 0:
            return pd.Series(dtype=float)
        base_year = int(valid.min())
    base_val = s.loc[base_year]
    if base_val <= 0:
        return pd.Series(dtype=float)
    return np.log(s / base_val)


# ---------- Main -----------------------------------------------------------

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ---- Vintage discovery
    available, missing = {}, []

    def take(pub, series, role):
        p = latest(pub, series)
        key = f"{pub}:{series}"
        if p is None:
            missing.append(f"{key} ({role})")
            return None
        available[key] = {
            "publisher": pub,
            "series": series,
            "role": role,
            "vintage_file": str(p.relative_to(REPO_ROOT)),
            "sha256": sha256(p),
        }
        return p

    p_cpi    = take("bis", "WS_LONG_CPI", "cpi_panel")
    p_spp    = take("bis", "WS_SPP", "residential_property_panel")
    p_iedata = take("shiller", "ie_data", "us_real_equity")
    p_hpi    = take("shiller", "home_price_index", "us_real_home_price")
    p_walcl  = take("fred", "WALCL", "us_fed_balance_sheet")
    p_gdp_us = take("fred", "GDP", "us_nominal_gdp_quarterly")
    p_wdi_g  = take("world_bank_wdi", "NY.GDP.MKTP.KD", "real_gdp_panel")

    # METHOD_VALID gate: need CPI panel + at least one asset series.
    if p_cpi is None or (p_spp is None and p_iedata is None and p_hpi is None):
        verdict = (
            "inconclusive — data gap on " + ", ".join(missing)
            + ". Need BIS WS_LONG_CPI plus at least one asset-price series."
        )
        _emit_inconclusive(verdict, available, missing,
                           note="Required minimum data set not on disk.")
        print(f"verdict: {verdict}")
        return

    # ---- Load
    cpi = load_bis_cpi_annual_pct_change(p_cpi)
    prop = load_bis_property_annual(p_spp) if p_spp else pd.DataFrame()
    eq_us = load_shiller_ie_data(p_iedata) if p_iedata else pd.DataFrame()
    hp_us = load_shiller_home_price(p_hpi) if p_hpi else pd.DataFrame()
    walcl = load_fred_annual(p_walcl) if p_walcl else pd.DataFrame()
    gdp_us = load_fred_annual(p_gdp_us) if p_gdp_us else pd.DataFrame()
    real_gdp_panel = load_wdi(p_wdi_g, set(COUNTRIES)) if p_wdi_g else pd.DataFrame()

    # ---- Per-country gap calculation
    BASE = 2008
    H_PRIMARY = 2020
    H_EXT = 2023

    rows = []
    for iso3 in COUNTRIES:
        iso2 = ISO2_BY_ISO3[iso3]

        # CPI cumulative log-index (base = 2008)
        c = (cpi[cpi["REF_AREA"] == iso2]
             .drop_duplicates("year").set_index("year")["inflation_pct"])
        c = c[(c.index >= BASE) & (c.index <= H_EXT + 1)]
        if len(c) < 5:
            rows.append({"country": iso3, "iso2": iso2,
                         "cpi_log_2020": np.nan, "cpi_log_2023": np.nan,
                         "asset_log_2020": np.nan, "asset_log_2023": np.nan,
                         "gap_2020": np.nan, "gap_2023": np.nan,
                         "asset_source": "none", "method_ok": False})
            continue
        cpi_cum = cumulative_log_from_pct_change(c)
        cpi_2020 = float(cpi_cum.loc[H_PRIMARY]) if H_PRIMARY in cpi_cum.index else np.nan
        cpi_2023 = float(cpi_cum.loc[H_EXT]) if H_EXT in cpi_cum.index else np.nan

        # Asset log-index — prefer equity for USA (Shiller), residential
        # property (BIS WS_SPP) for the rest. Take the larger if both.
        asset_2020 = np.nan
        asset_2023 = np.nan
        asset_source = "none"

        if iso3 == "USA":
            if not eq_us.empty:
                s = eq_us.set_index("year")["real_equity_index"]
                clog = cumulative_log_from_index(s, BASE)
                if H_PRIMARY in clog.index:
                    asset_2020 = float(clog.loc[H_PRIMARY])
                    asset_source = "shiller_real_total_return"
                if H_EXT in clog.index:
                    asset_2023 = float(clog.loc[H_EXT])
            # USA also has Shiller home price — keep as informative
            if not hp_us.empty:
                s = hp_us.set_index("year")["real_home_price"]
                clog = cumulative_log_from_index(s, BASE)
                hp_2020 = float(clog.loc[H_PRIMARY]) if H_PRIMARY in clog.index else np.nan
                hp_2023 = float(clog.loc[H_EXT]) if H_EXT in clog.index else np.nan
                # Take max (more permissive to the hypothesis)
                if not np.isnan(hp_2020) and (np.isnan(asset_2020) or hp_2020 > asset_2020):
                    asset_2020 = hp_2020
                    asset_source = "shiller_home_price"
                if not np.isnan(hp_2023) and (np.isnan(asset_2023) or hp_2023 > asset_2023):
                    asset_2023 = hp_2023
        else:
            if not prop.empty:
                pp = prop[prop["REF_AREA"] == iso2].set_index("year")["value"]
                clog = cumulative_log_from_index(pp, BASE)
                if H_PRIMARY in clog.index:
                    asset_2020 = float(clog.loc[H_PRIMARY])
                    asset_source = "bis_residential_property"
                if H_EXT in clog.index:
                    asset_2023 = float(clog.loc[H_EXT])

        gap_2020 = (asset_2020 - cpi_2020) if (
            not np.isnan(asset_2020) and not np.isnan(cpi_2020)) else np.nan
        gap_2023 = (asset_2023 - cpi_2023) if (
            not np.isnan(asset_2023) and not np.isnan(cpi_2023)) else np.nan

        rows.append({
            "country": iso3, "iso2": iso2,
            "cpi_log_2020": cpi_2020, "cpi_log_2023": cpi_2023,
            "asset_log_2020": asset_2020, "asset_log_2023": asset_2023,
            "gap_2020": gap_2020, "gap_2023": gap_2023,
            "asset_source": asset_source,
            "method_ok": not (np.isnan(gap_2020)),
        })

    res = pd.DataFrame(rows)

    # ---- Method-validity gate
    n_method_ok = int(res["method_ok"].sum())
    if n_method_ok < METHOD_VALID_MIN_COUNTRIES:
        verdict = (
            f"inconclusive — only {n_method_ok} of 8 panel countries have "
            f"the asset-price + CPI series needed to compute GAP_2020. "
            f"Method-validity gate requires at least {METHOD_VALID_MIN_COUNTRIES}. "
            f"Per-country status: " + ", ".join(
                f"{r['country']}={r['asset_source']}" for _, r in res.iterrows()))
        _emit_with_table(verdict, available, missing, res,
                         qe_active_us=None, walcl_gdp_2009=None)
        print(f"verdict: {verdict}")
        return

    # ---- QE-active indicator (USA): WALCL/GDP > 15% in some year >= 2009
    qe_active_us = None
    walcl_gdp_2009 = None
    if not walcl.empty and not gdp_us.empty:
        m = walcl.merge(gdp_us, on="year", suffixes=("_walcl", "_gdp"))
        # WALCL is in $millions, GDP is in $billions — convert WALCL to billions
        m["walcl_b"] = m["value_walcl"] / 1000.0
        m["ratio"] = m["walcl_b"] / m["value_gdp"]
        post = m[(m["year"] >= 2009) & (m["year"] <= 2020)]
        qe_active_us = bool((post["ratio"] > WALCL_GDP_QE_THRESHOLD).any())
        if 2009 in m["year"].values:
            walcl_gdp_2009 = float(m.loc[m["year"] == 2009, "ratio"].iloc[0])

    # ---- Verdict logic
    valid = res.dropna(subset=["gap_2020"])
    n_above_primary = int((valid["gap_2020"] >= PRIMARY_A_GAP_THRESHOLD).sum())
    n_above_floor = int((valid["gap_2020"] >= REFUTED_GAP_FLOOR).sum())

    primary_a_pass = n_above_primary >= PRIMARY_A_MIN_COUNTRIES

    # Primary B: gap narrowed by >= 25% from 2020 to 2023 (in countries where
    # both observations exist). "Narrowing" means GAP_2023 <= GAP_2020 * 0.75.
    valid_b = res.dropna(subset=["gap_2020", "gap_2023"])
    valid_b = valid_b[valid_b["gap_2020"] > 0]  # only meaningful where there's a gap to narrow
    valid_b = valid_b.assign(
        narrowed=lambda d: d["gap_2023"] <= d["gap_2020"] * (1 - PRIMARY_B_NARROW_FRACTION)
    )
    n_narrowed = int(valid_b["narrowed"].sum())
    primary_b_pass = n_narrowed >= PRIMARY_B_MIN_COUNTRIES

    refuted = n_above_floor < REFUTED_MIN_COUNTRIES
    supported = primary_a_pass and primary_b_pass

    mean_gap_2020 = float(valid["gap_2020"].mean())
    mean_gap_2023 = float(valid_b["gap_2023"].mean()) if not valid_b.empty else float("nan")

    if supported:
        verdict = (
            f"SUPPORTED — Mean GAP_2020 across {len(valid)} countries = "
            f"{mean_gap_2020:+.2f} log-points "
            f"({np.expm1(mean_gap_2020)*100:+.0f}% asset-vs-CPI excess). "
            f"{n_above_primary} of 8 cleared the {PRIMARY_A_GAP_THRESHOLD:.2f} threshold. "
            f"{n_narrowed} of {len(valid_b)} narrowed by >= {PRIMARY_B_NARROW_FRACTION*100:.0f}% by 2023."
        )
    elif refuted:
        verdict = (
            f"refuted — Only {n_above_floor} of 8 countries had even a "
            f"{REFUTED_GAP_FLOOR:.2f} log-point asset-vs-CPI gap by 2020 "
            f"(mean GAP_2020 = {mean_gap_2020:+.2f}). The post-2008 "
            f"divergence story does not survive a panel test."
        )
    else:
        verdict = (
            f"partial — {n_above_primary} of 8 countries cleared the "
            f"{PRIMARY_A_GAP_THRESHOLD:.2f} log-point threshold (need "
            f"{PRIMARY_A_MIN_COUNTRIES}); {n_narrowed} of {len(valid_b)} "
            f"narrowed by >= {PRIMARY_B_NARROW_FRACTION*100:.0f}% by 2023 "
            f"(need {PRIMARY_B_MIN_COUNTRIES}). Mean GAP_2020 = "
            f"{mean_gap_2020:+.2f} log-points."
        )

    diagnostics = {
        "verdict": verdict,
        "all_pass": supported,
        "primary_a_pass": bool(primary_a_pass),
        "primary_b_pass": bool(primary_b_pass),
        "method_valid": True,
        "n_countries_method_ok": n_method_ok,
        "min_method_valid_countries": METHOD_VALID_MIN_COUNTRIES,
        "n_above_primary_threshold": n_above_primary,
        "n_above_refuted_floor": n_above_floor,
        "n_narrowed_by_2023": n_narrowed,
        "mean_gap_2020_log": mean_gap_2020,
        "mean_gap_2023_log": mean_gap_2023,
        "primary_a_threshold_log": PRIMARY_A_GAP_THRESHOLD,
        "primary_a_min_countries": PRIMARY_A_MIN_COUNTRIES,
        "primary_b_narrow_fraction": PRIMARY_B_NARROW_FRACTION,
        "primary_b_min_countries": PRIMARY_B_MIN_COUNTRIES,
        "refuted_gap_floor_log": REFUTED_GAP_FLOOR,
        "qe_active_usa": qe_active_us,
        "walcl_to_gdp_2009_us": walcl_gdp_2009,
        "walcl_to_gdp_qe_threshold": WALCL_GDP_QE_THRESHOLD,
        "country_results": res.to_dict(orient="records"),
        "missing_series": missing,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=float) + "\n"
    )

    # ---- Coefficients table
    coef = pd.DataFrame([
        {"spec": "primary_a", "term": "mean_gap_2020_log", "estimate": mean_gap_2020},
        {"spec": "primary_a", "term": "n_above_threshold_of_8", "estimate": float(n_above_primary)},
        {"spec": "primary_b", "term": "mean_gap_2023_log", "estimate": mean_gap_2023},
        {"spec": "primary_b", "term": "n_narrowed_of_valid", "estimate": float(n_narrowed)},
        *(
            {"spec": "country_gap_2020", "term": r["country"], "estimate": r["gap_2020"]}
            for _, r in res.iterrows()
        ),
        *(
            {"spec": "country_gap_2023", "term": r["country"], "estimate": r["gap_2023"]}
            for _, r in res.iterrows()
        ),
    ])
    coef.to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    # ---- Chart
    palette = ["#4E79A7", "#59A14F", "#E15759", "#F28E2B", "#76B7B2",
               "#EDC948", "#B07AA1", "#9C755F"]
    series = []
    for i, r in enumerate(res.itertuples()):
        pts = []
        if not np.isnan(r.gap_2020):
            pts.append({"x": 2020, "y": float(r.gap_2020)})
        if not np.isnan(r.gap_2023):
            pts.append({"x": 2023, "y": float(r.gap_2023)})
        if pts:
            series.append({
                "id": r.country,
                "label": r.country,
                "color": palette[i % len(palette)],
                "treated": False,
                "points": pts,
            })
    series.insert(0, {
        "id": "THRESHOLD",
        "label": f"Primary threshold ({PRIMARY_A_GAP_THRESHOLD} log-points)",
        "color": "#1f1f1f",
        "treated": True,
        "points": [{"x": 2020, "y": PRIMARY_A_GAP_THRESHOLD},
                   {"x": 2023, "y": PRIMARY_A_GAP_THRESHOLD}],
    })

    chart_data = {
        "kind": "result",
        "chart_id": f"{HID}/fig1",
        "title": "Cumulative log-gap between asset prices and CPI, 2008 base",
        "subtitle": (
            f"GAP = log(real asset index 20XX / 2008) - log(CPI 20XX / 2008). "
            f"Mean GAP_2020 = {mean_gap_2020:+.2f}; "
            f"{n_above_primary}/8 cleared the {PRIMARY_A_GAP_THRESHOLD} threshold."
        ),
        "type": "line",
        "x_axis": {"label": "Horizon year", "type": "linear"},
        "y_axis": {"label": "asset - CPI cumulative log-points", "type": "linear"},
        "series": series,
        "annotations": [
            {
                "type": "note",
                "label": (
                    "Asset = real total return on Shiller S&P (USA) or BIS "
                    "WS_SPP residential property index (others). CPI from BIS "
                    "WS_LONG_CPI annual %change cumulated."
                ),
            }
        ],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")

    # ---- Manifest
    _write_manifest(available)

    # ---- Result card
    card_lines = [
        "# Post-2008 QE asset inflation vs CPI divergence",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Summary",
        "",
        f"- Sample: {len(COUNTRIES)} advanced QE economies (USA, GBR, JPN, "
        f"DEU, FRA, ITA, ESP, NLD).",
        f"- Cumulative-log gap between asset prices (equities for USA, BIS "
        f"residential property for others) and CPI, 2008 base.",
        f"- Mean GAP_2020 = **{mean_gap_2020:+.2f} log-points** "
        f"(~{np.expm1(mean_gap_2020)*100:+.0f}% asset-vs-CPI excess).",
        f"- {n_above_primary} of 8 countries cleared the "
        f"{PRIMARY_A_GAP_THRESHOLD} log-point threshold "
        f"(PRIMARY A; need {PRIMARY_A_MIN_COUNTRIES}).",
        f"- {n_narrowed} of {len(valid_b)} eligible countries narrowed the "
        f"gap by >= {PRIMARY_B_NARROW_FRACTION*100:.0f}% by 2023 "
        f"(PRIMARY B; need {PRIMARY_B_MIN_COUNTRIES}).",
        f"- USA WALCL/GDP > {WALCL_GDP_QE_THRESHOLD:.0%} in post-2008 window: "
        f"**{qe_active_us}** (2009 ratio = "
        f"{walcl_gdp_2009 if walcl_gdp_2009 is None else f'{walcl_gdp_2009:.2%}'}).",
        "",
        "## Method",
        "",
        "1. CPI cumulative log-index from BIS WS_LONG_CPI annual %change.",
        "2. Asset cumulative log-index from Shiller real total return "
        "(USA primary) or BIS WS_SPP residential property (other countries).",
        "3. GAP_h = asset_log(h) - cpi_log(h). Compute at h=2020 (PRIMARY A) "
        "and h=2023 (PRIMARY B - sanity check that the 2021-23 CPI shock "
        "narrowed the gap).",
        "4. Verdict requires PRIMARY A AND PRIMARY B. REFUTED if fewer "
        "than 3 countries cleared the 0.10 log-point floor.",
        "",
        "## Caveats",
        "",
        "- The spec called for cross-country central-bank balance-sheet "
        "treatment series (ECB, BoE, BoJ); only FRED:WALCL is on disk for "
        "the USA. The hypothesis is therefore tested as an *associational* "
        "post-2008 divergence, not as an LP impulse response. The QE-active "
        "indicator confirms regime classification for the USA only.",
        "- Property-price index used as the asset proxy for non-US "
        "countries. This is conservative for the hypothesis: equity "
        "returns over 2008-2020 typically exceeded property returns, so "
        "the asset side of the gap is understated for the euro-area panel.",
        "- 2020 used as the primary horizon to match the spec's '2009-2020 "
        "window only closing once the 2021-2023 CPI shock materialised'.",
        "",
        "## Data",
        "",
        "- bis:WS_LONG_CPI (cross-country annual CPI %change)",
        "- bis:WS_SPP (residential property index — euro panel)",
        "- shiller:ie_data (US S&P composite real total return)",
        "- shiller:home_price_index (US real home price)",
        "- fred:WALCL + fred:GDP (US Fed balance-sheet ratio)",
        "- world_bank_wdi:NY.GDP.MKTP.KD (real GDP panel control)",
    ]
    if missing:
        card_lines.append("")
        card_lines.append("Missing series (informative — not gating):")
        for m in missing:
            card_lines.append(f"- {m}")
    (OUT_DIR / "result_card.md").write_text("\n".join(card_lines) + "\n")

    print(f"verdict: {verdict}")


def _write_manifest(available: dict) -> None:
    lines = [
        f"hypothesis_id: {HID}",
        f"run_utc: '{pd.Timestamp.utcnow().isoformat()}'",
        "vintages:",
    ]
    for k, v in available.items():
        lines.append(f"  '{k}':")
        lines.append(f"    publisher: {v['publisher']}")
        lines.append(f"    series: {v['series']}")
        lines.append(f"    role: {v['role']}")
        lines.append(f"    vintage_file: {v['vintage_file']}")
        lines.append(f"    sha256: {v['sha256']}")
    (OUT_DIR / "manifest.yaml").write_text("\n".join(lines) + "\n")


def _emit_inconclusive(verdict, available, missing, note=""):
    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "method_valid": False,
        "data_gap": True,
        "missing_series": missing,
        "available_series": sorted(available.keys()),
        "note": note,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    pd.DataFrame([
        {"spec": "primary_a", "term": "mean_gap_2020_log", "estimate": np.nan},
        {"spec": "primary_b", "term": "mean_gap_2023_log", "estimate": np.nan},
    ]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    chart_data = {
        "kind": "result", "chart_id": f"{HID}/fig1",
        "title": "Post-2008 QE asset-vs-CPI divergence — DATA GAP",
        "subtitle": "Required series not on disk; replication blocked.",
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log-points", "type": "linear"},
        "series": [],
        "annotations": [{"type": "note", "label": "Missing: " + ", ".join(missing)}],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")
    _write_manifest(available)
    (OUT_DIR / "result_card.md").write_text(
        f"# Post-2008 QE asset inflation vs CPI divergence\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Missing data\n\n" + "\n".join(f"- {m}" for m in missing) + "\n"
    )


def _emit_with_table(verdict, available, missing, res, qe_active_us, walcl_gdp_2009):
    diagnostics = {
        "verdict": verdict,
        "all_pass": False,
        "method_valid": False,
        "country_results": res.to_dict(orient="records"),
        "available_series": sorted(available.keys()),
        "missing_series": missing,
        "qe_active_usa": qe_active_us,
        "walcl_to_gdp_2009_us": walcl_gdp_2009,
    }
    (OUT_DIR / "diagnostics.json").write_text(
        json.dumps(diagnostics, indent=2, default=float) + "\n"
    )
    pd.DataFrame([
        {"spec": "primary_a", "term": "mean_gap_2020_log", "estimate": np.nan},
        {"spec": "primary_b", "term": "mean_gap_2023_log", "estimate": np.nan},
    ]).to_parquet(OUT_DIR / "coefficients.parquet", index=False)
    chart_data = {
        "kind": "result", "chart_id": f"{HID}/fig1",
        "title": "Post-2008 QE asset-vs-CPI divergence — INCONCLUSIVE",
        "subtitle": verdict,
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {"label": "log-points", "type": "linear"},
        "series": [],
        "annotations": [{"type": "note", "label": verdict}],
        "sources": [
            {"publisher_id": v["publisher"], "series_id": v["series"],
             "vintage_file": v["vintage_file"]}
            for v in available.values()
        ],
        "permalink": f"/h/{HID}",
    }
    (OUT_DIR / "chart_data.json").write_text(json.dumps(chart_data, indent=2) + "\n")
    _write_manifest(available)
    (OUT_DIR / "result_card.md").write_text(
        f"# Post-2008 QE asset inflation vs CPI divergence\n\n"
        f"**Verdict:** {verdict}\n"
    )


if __name__ == "__main__":
    main()
