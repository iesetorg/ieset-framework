"""
japan_stagnation_wellbeing_outcomes replication.

Tests the degrowth-school claim that Japanese 1990-2020 stagnation
coexisted with stable or improving wellbeing indicators (life expectancy,
unemployment, Gini), refuting the claim that zero-growth necessarily
degrades human outcomes.

Multi-metric checklist:
  - GDP per capita growth (NY.GDP.PCAP.KD.ZG): confirm "stagnation" — JPN
    mean annual growth 1990-2020 should be < 1.5%.
  - Life expectancy at birth (SP.DYN.LE00.IN): JPN 2020 vs 1990 — should
    not degrade by > 10% relative to OECD median.
  - Unemployment rate (SL.UEM.TOTL.ZS): JPN 2020 vs 1990 — should not
    rise by > 10pp relative to OECD median.
  - Gini index (SI.POV.GINI): JPN endpoints — should not rise by > 10pp.

Verdict gate (PRIMARY): JPN mean GDP growth 1990-2020 < 1.5% AND no more
than 1 of 3 wellbeing indicators degrades by > 10% relative to OECD median
over the window.

OECD comparator pool: USA, GBR, DEU, FRA, ITA, ESP, NLD, BEL, AUT, SWE,
NOR, DNK, FIN, CAN, AUS, NZL, KOR.
"""

from __future__ import annotations

import json
import sys
import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
RUN_DIR = Path(__file__).resolve().parent
HID = "japan_stagnation_wellbeing_outcomes"

OECD_COMPARATORS = ["USA", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL",
                    "AUT", "SWE", "NOR", "DNK", "FIN", "CAN", "AUS", "NZL", "KOR"]


def latest(publisher: str, series: str) -> Optional[Path]:
    d = ROOT / "data" / "vintages" / publisher
    if not d.exists():
        return None
    cands = sorted(d.glob(f"{series}@*.parquet"))
    return cands[-1] if cands else None


def load_wdi(path: Path) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    cols = {c.lower(): c for c in t.columns}
    iso_col = cols.get("country_iso3") or cols.get("iso3") or cols.get("countrycode")
    yr_col = cols.get("year") or cols.get("date")
    val_col = cols.get("value") or [c for c in t.columns if c not in (iso_col, yr_col)][-1]
    df = t[[iso_col, yr_col, val_col]].copy()
    df.columns = ["iso3", "year", "value"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def country_endpoint(df: pd.DataFrame, iso: str, year: int, tol: int = 2) -> Optional[float]:
    sub = df[df["iso3"] == iso]
    candidates = sub[(sub["year"] >= year - tol) & (sub["year"] <= year + tol)]
    if candidates.empty:
        return None
    nearest = candidates.iloc[(candidates["year"] - year).abs().argsort()].iloc[0]
    return float(nearest["value"])


def country_mean(df: pd.DataFrame, iso: str, lo: int, hi: int) -> Optional[float]:
    sub = df[(df["iso3"] == iso) & (df["year"] >= lo) & (df["year"] <= hi)]
    if sub.empty:
        return None
    return float(sub["value"].mean())


def panel_median(df: pd.DataFrame, isos: list, year: int, tol: int = 2) -> Optional[float]:
    vals = [country_endpoint(df, iso, year, tol) for iso in isos]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return float(pd.Series(vals).median())


def main():
    p_growth = latest("world_bank_wdi", "NY.GDP.PCAP.KD.ZG")
    p_le = latest("world_bank_wdi", "SP.DYN.LE00.IN")
    p_unemp = latest("world_bank_wdi", "SL.UEM.TOTL.ZS")
    p_gini = latest("world_bank_wdi", "SI.POV.GINI")

    missing = [n for n, p in (("NY.GDP.PCAP.KD.ZG", p_growth),
                              ("SP.DYN.LE00.IN", p_le),
                              ("SL.UEM.TOTL.ZS", p_unemp),
                              ("SI.POV.GINI", p_gini)) if p is None]

    if missing:
        diag = {
            "verdict": f"inconclusive — data gap on world_bank_wdi:{','.join(missing)}",
            "method_valid": False,
            "missing": missing,
        }
        (RUN_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2))
        print(diag["verdict"])
        return

    growth = load_wdi(p_growth)
    le = load_wdi(p_le)
    unemp = load_wdi(p_unemp)
    gini = load_wdi(p_gini)

    # JPN mean GDP/cap growth 1990-2020 (excluding 2020 COVID year)
    jpn_growth_mean = country_mean(growth[growth["year"] != 2020], "JPN", 1990, 2020)

    # Endpoints for each wellbeing metric
    # Life expectancy
    jpn_le_1990 = country_endpoint(le, "JPN", 1990)
    jpn_le_2020 = country_endpoint(le, "JPN", 2020)
    oecd_le_1990 = panel_median(le, OECD_COMPARATORS, 1990)
    oecd_le_2020 = panel_median(le, OECD_COMPARATORS, 2020)

    # Unemployment
    jpn_unemp_1990 = country_endpoint(unemp, "JPN", 1991)  # series often starts 1991
    jpn_unemp_2020 = country_endpoint(unemp, "JPN", 2020)
    oecd_unemp_1990 = panel_median(unemp, OECD_COMPARATORS, 1991)
    oecd_unemp_2020 = panel_median(unemp, OECD_COMPARATORS, 2020)

    # Gini — endpoints with wider tolerance (sparse series)
    jpn_gini_early = country_endpoint(gini, "JPN", 1995, tol=5)
    jpn_gini_late = country_endpoint(gini, "JPN", 2018, tol=5)

    # Compute deltas (positive = improving for LE, neutral elsewhere)
    le_jpn_delta = (jpn_le_2020 - jpn_le_1990) if (jpn_le_2020 and jpn_le_1990) else None
    le_oecd_delta = (oecd_le_2020 - oecd_le_1990) if (oecd_le_2020 and oecd_le_1990) else None
    le_relative = (le_jpn_delta - le_oecd_delta) if (le_jpn_delta is not None and le_oecd_delta is not None) else None

    unemp_jpn_delta = (jpn_unemp_2020 - jpn_unemp_1990) if (jpn_unemp_2020 and jpn_unemp_1990) else None
    unemp_oecd_delta = (oecd_unemp_2020 - oecd_unemp_1990) if (oecd_unemp_2020 and oecd_unemp_1990) else None
    unemp_relative = (unemp_jpn_delta - unemp_oecd_delta) if (unemp_jpn_delta is not None and unemp_oecd_delta is not None) else None

    gini_jpn_delta = (jpn_gini_late - jpn_gini_early) if (jpn_gini_late and jpn_gini_early) else None

    # Score wellbeing degradations
    # LE degrades if JPN improvement is >10% worse than OECD (i.e. relative < -1y where 1y is ~10% of typical 5-10y improvement).
    # We use absolute thresholds: LE relative-to-OECD difference < -2 years = degraded
    # Unemp degrades if JPN rises by >2pp more than OECD over the window
    # Gini degrades if JPN rises by >5pp
    le_degraded = le_relative is not None and le_relative < -2.0
    unemp_degraded = unemp_relative is not None and unemp_relative > 2.0
    gini_degraded = gini_jpn_delta is not None and gini_jpn_delta > 5.0

    n_degraded = sum([le_degraded, unemp_degraded, gini_degraded])

    stagnation_confirmed = jpn_growth_mean is not None and jpn_growth_mean < 1.5
    primary_pass = stagnation_confirmed and n_degraded <= 1

    def _f(v, fmt=":+.2f"):
        return f"{v:{fmt[1:]}}" if v is not None else "n/a"
    if primary_pass:
        verdict = (f"SUPPORTED — JPN 1990-2020 mean GDP/cap growth = "
                   f"{jpn_growth_mean:.2f}% (<1.5%); {n_degraded} of 3 "
                   f"wellbeing indicators degraded vs OECD median "
                   f"(LE_rel={_f(le_relative)}y; unemp_rel={_f(unemp_relative)}pp; "
                   f"gini_delta={_f(gini_jpn_delta)}pp).")
    elif not stagnation_confirmed:
        verdict = (f"refuted — stagnation premise fails: JPN 1990-2020 "
                   f"mean GDP/cap growth = {jpn_growth_mean:.2f}% (>=1.5%).")
    elif n_degraded >= 2:
        verdict = (f"refuted — 2+ wellbeing indicators degraded vs OECD median "
                   f"(LE_rel={_f(le_relative)}y deg={le_degraded}; "
                   f"unemp_rel={_f(unemp_relative)}pp deg={unemp_degraded}; "
                   f"gini_delta={_f(gini_jpn_delta)}pp deg={gini_degraded}). "
                   f"Stagnation premise held (mean growth {jpn_growth_mean:.2f}%).")
    else:
        verdict = "partial — stagnation confirmed and 1 indicator degraded."

    diagnostics = {
        "verdict": verdict,
        "method_valid": True,
        "primary_pass": primary_pass,
        "stagnation_confirmed": stagnation_confirmed,
        "jpn_mean_gdppc_growth_1990_2020_ex2020": jpn_growth_mean,
        "wellbeing_metrics": {
            "life_expectancy": {
                "jpn_1990": jpn_le_1990, "jpn_2020": jpn_le_2020,
                "oecd_median_1990": oecd_le_1990, "oecd_median_2020": oecd_le_2020,
                "jpn_delta_years": le_jpn_delta,
                "oecd_delta_years": le_oecd_delta,
                "relative_delta_years": le_relative,
                "degraded_threshold": -2.0,
                "degraded": le_degraded,
            },
            "unemployment": {
                "jpn_1991": jpn_unemp_1990, "jpn_2020": jpn_unemp_2020,
                "oecd_median_1991": oecd_unemp_1990, "oecd_median_2020": oecd_unemp_2020,
                "jpn_delta_pp": unemp_jpn_delta,
                "oecd_delta_pp": unemp_oecd_delta,
                "relative_delta_pp": unemp_relative,
                "degraded_threshold_pp": 2.0,
                "degraded": unemp_degraded,
            },
            "gini": {
                "jpn_early": jpn_gini_early, "jpn_late": jpn_gini_late,
                "delta_pp": gini_jpn_delta,
                "degraded_threshold_pp": 5.0,
                "degraded": gini_degraded,
            },
        },
        "n_degraded": int(n_degraded),
    }
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=str))

    chart = {
        "kind": "result",
        "title": "Japan 1990-2020: stagnation vs wellbeing",
        "series": [
            {"name": "JPN mean GDP/cap growth", "value": jpn_growth_mean},
            {"name": "JPN LE delta (years)", "value": le_jpn_delta},
            {"name": "OECD median LE delta", "value": le_oecd_delta},
            {"name": "JPN unemp delta (pp)", "value": unemp_jpn_delta},
            {"name": "JPN Gini delta (pp)", "value": gini_jpn_delta},
        ],
        "annotations": ["PRIMARY: mean growth <1.5% AND <=1 of 3 wellbeing metrics degraded vs OECD median"],
    }
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2, default=str))

    coef = pd.DataFrame([
        {"name": "jpn_mean_gdppc_growth", "value": jpn_growth_mean, "threshold": 1.5},
        {"name": "le_jpn_minus_oecd_delta_y", "value": le_relative, "threshold": -2.0},
        {"name": "unemp_jpn_minus_oecd_delta_pp", "value": unemp_relative, "threshold": 2.0},
        {"name": "gini_jpn_delta_pp", "value": gini_jpn_delta, "threshold": 5.0},
        {"name": "n_wellbeing_degraded", "value": n_degraded, "threshold": 1},
    ])
    coef.to_parquet(RUN_DIR / "coefficients.parquet", index=False)

    def sha256_path(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:16]

    manifest = {
        "hypothesis_id": HID,
        "vintages": [
            {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD.ZG", "path": str(p_growth.relative_to(ROOT)), "sha256_16": sha256_path(p_growth)},
            {"publisher": "world_bank_wdi", "series": "SP.DYN.LE00.IN", "path": str(p_le.relative_to(ROOT)), "sha256_16": sha256_path(p_le)},
            {"publisher": "world_bank_wdi", "series": "SL.UEM.TOTL.ZS", "path": str(p_unemp.relative_to(ROOT)), "sha256_16": sha256_path(p_unemp)},
            {"publisher": "world_bank_wdi", "series": "SI.POV.GINI", "path": str(p_gini.relative_to(ROOT)), "sha256_16": sha256_path(p_gini)},
        ],
    }
    import yaml as _yaml
    (RUN_DIR / "manifest.yaml").write_text(_yaml.safe_dump(manifest, sort_keys=False))

    result = (
        f"# Japan 1990-2020: stagnation vs wellbeing\n\n"
        f"**Verdict:** {verdict}\n\n"
        f"## Method\n\n"
        f"Multi-metric checklist. JPN mean GDP/cap growth 1990-2020 (excl. 2020 COVID) "
        f"vs the 1.5% stagnation threshold; LE/unemployment deltas relative to OECD median; "
        f"Gini delta absolute. Primary supports the degrowth claim if stagnation holds AND "
        f"<=1 of 3 wellbeing metrics degraded.\n\n"
        f"## Numbers\n\n"
        f"- JPN mean GDP/cap growth 1990-2020 (ex 2020): {jpn_growth_mean:.2f}%\n"
        f"- JPN LE 1990→2020: {jpn_le_1990:.1f}→{jpn_le_2020:.1f}y; OECD median: {oecd_le_1990:.1f}→{oecd_le_2020:.1f}y; relative {le_relative:+.2f}y\n"
        f"- JPN unemployment 1991→2020: {jpn_unemp_1990:.2f}→{jpn_unemp_2020:.2f}pp; OECD median {oecd_unemp_1990:.2f}→{oecd_unemp_2020:.2f}pp; relative {unemp_relative:+.2f}pp\n"
        f"- JPN Gini early→late: {jpn_gini_early}→{jpn_gini_late}; delta {gini_jpn_delta if gini_jpn_delta is not None else 'n/a (sparse Gini series)'}\n"
        f"- Wellbeing indicators degraded: {n_degraded} of 3\n\n"
        f"## Caveats\n\n"
        f"- WDI panel does NOT include suicide rates, hikikomori, fertility rates, or hours-worked — "
        f"the indicator basket is the favourable subset of \"wellbeing\".\n"
        f"- Life expectancy improved globally over the window; the OECD-relative test partially "
        f"controls for the secular trend.\n"
        f"- Gini sparse series; endpoints have ±5y tolerance.\n"
    )
    (RUN_DIR / "result_card.md").write_text(result)

    print(verdict)


if __name__ == "__main__":
    main()
