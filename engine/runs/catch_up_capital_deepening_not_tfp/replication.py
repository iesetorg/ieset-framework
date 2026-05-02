#!/usr/bin/env python3
"""Replication - Catch-up capital deepening versus TFP.

Spec: Developmentalist catch-up episodes generate more early growth through
capital deepening and labor/human-capital accumulation than through sustained
TFP growth.

Design:
  1. Use PWT 10.01 growth accounting variables.
  2. Pre-specify catch-up/developmentalist or transition episodes from the
     hypothesis sample.
  3. Decompose 5-year annualized output-per-worker growth into:
       alpha * capital-per-worker growth
       (1-alpha) * human-capital growth
       TFP growth
     with alpha = 1 - PWT labor share.
  4. Compare the first 15 available episode years against later years.

Falsification:
  SUPPORTED if capital + human-capital channels account for at least 60% of
  positive early catch-up growth and later TFP contribution is lower than early
  TFP contribution. REFUTED if early TFP share is at least 50% and later TFP
  contribution is not lower. Otherwise PARTIAL.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "catch_up_capital_deepening_not_tfp"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

PERIOD = (1960, 2019)
WINDOW = 5
EARLY_YEARS = 15
CAPITAL_HC_SHARE_MIN = 0.60

# Episode starts are intentionally coarse and public-historical rather than
# tuned to fit the PWT panel. They mark major catch-up or reform phases.
EPISODES = {
    "JPN": 1960,
    "KOR": 1962,
    "TWN": 1960,
    "SGP": 1965,
    "MYS": 1971,
    "THA": 1961,
    "IDN": 1967,
    "IND": 1991,
    "CHN": 1978,
    "VNM": 1986,
    "BRA": 1964,
    "MEX": 1960,
    "CHL": 1974,
    "TUR": 1980,
    "POL": 1990,
    "EST": 1992,
    "IRL": 1987,
    "BGD": 1990,
    "ETH": 2000,
    "RWA": 2000,
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def safe_share(numerator: float, denominator: float) -> float | None:
    if not math.isfinite(numerator) or not math.isfinite(denominator) or denominator <= 0:
        return None
    return numerator / denominator


def json_float(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, (int, str, bool)):
        return value
    try:
        value = float(value)
    except (TypeError, ValueError):
        return value
    return value if math.isfinite(value) else None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pwt_path = latest("pwt", "pwt_full")
    manifest = {
        "pwt_full": {
            "publisher": "pwt",
            "series": "pwt_full",
            "vintage_file": str(pwt_path.relative_to(REPO_ROOT)),
            "sha256": sha256(pwt_path),
        },
    }

    raw = pq.read_table(pwt_path).to_pandas()
    cols = ["country_iso3", "country", "year", "rgdpo", "rkna", "emp", "hc", "rtfpna", "labsh"]
    t = raw[cols].dropna().copy()
    t["year"] = t["year"].astype(int)
    t = t[(t["year"] >= PERIOD[0]) & (t["year"] <= PERIOD[1])]
    t = t[t["country_iso3"].isin(EPISODES)]
    t = t[(t["rgdpo"] > 0) & (t["rkna"] > 0) & (t["emp"] > 0) & (t["hc"] > 0) & (t["rtfpna"] > 0)]

    t["episode_start"] = t["country_iso3"].map(EPISODES)
    t = t[t["year"] >= t["episode_start"]]
    t["episode_year"] = t["year"] - t["episode_start"]
    t["phase"] = np.where(t["episode_year"] < EARLY_YEARS, "early", "later")
    t["alpha"] = (1.0 - t["labsh"]).clip(lower=0.20, upper=0.70)
    t["ln_y_worker"] = np.log(t["rgdpo"] / t["emp"])
    t["ln_k_worker"] = np.log(t["rkna"] / t["emp"])
    t["ln_hc"] = np.log(t["hc"])
    t["ln_tfp"] = np.log(t["rtfpna"])

    t = t.sort_values(["country_iso3", "year"])
    for c in ["ln_y_worker", "ln_k_worker", "ln_hc", "ln_tfp", "alpha"]:
        t[f"{c}_t{WINDOW}"] = t.groupby("country_iso3")[c].shift(-WINDOW)

    panel = t.dropna(subset=[f"{c}_t{WINDOW}" for c in ["ln_y_worker", "ln_k_worker", "ln_hc", "ln_tfp", "alpha"]]).copy()
    panel["alpha_avg"] = (panel["alpha"] + panel[f"alpha_t{WINDOW}"]) / 2.0
    panel["output_growth"] = (panel[f"ln_y_worker_t{WINDOW}"] - panel["ln_y_worker"]) / WINDOW
    panel["capital_contribution"] = panel["alpha_avg"] * (panel[f"ln_k_worker_t{WINDOW}"] - panel["ln_k_worker"]) / WINDOW
    panel["human_capital_contribution"] = (1.0 - panel["alpha_avg"]) * (panel[f"ln_hc_t{WINDOW}"] - panel["ln_hc"]) / WINDOW
    panel["tfp_contribution"] = (panel[f"ln_tfp_t{WINDOW}"] - panel["ln_tfp"]) / WINDOW
    panel["residual"] = panel["output_growth"] - (
        panel["capital_contribution"] + panel["human_capital_contribution"] + panel["tfp_contribution"]
    )

    early = panel[(panel["phase"] == "early") & (panel["output_growth"] > 0)].copy()
    later = panel[(panel["phase"] == "later") & (panel["output_growth"] > 0)].copy()

    def phase_metrics(df: pd.DataFrame) -> dict[str, float | int | None]:
        output = float(df["output_growth"].mean()) if len(df) else float("nan")
        capital = float(df["capital_contribution"].mean()) if len(df) else float("nan")
        hc = float(df["human_capital_contribution"].mean()) if len(df) else float("nan")
        tfp = float(df["tfp_contribution"].mean()) if len(df) else float("nan")
        cap_hc_share = safe_share(capital + hc, output)
        tfp_share = safe_share(tfp, output)
        return {
            "n_observations": int(len(df)),
            "n_countries": int(df["country_iso3"].nunique()) if len(df) else 0,
            "mean_output_growth": output,
            "mean_capital_contribution": capital,
            "mean_human_capital_contribution": hc,
            "mean_tfp_contribution": tfp,
            "capital_hc_share_of_growth": cap_hc_share,
            "tfp_share_of_growth": tfp_share,
            "mean_residual": float(df["residual"].mean()) if len(df) else float("nan"),
        }

    early_m = phase_metrics(early)
    later_m = phase_metrics(later)
    early_cap_hc = early_m["capital_hc_share_of_growth"]
    early_tfp = early_m["tfp_share_of_growth"]
    later_tfp_level = later_m["mean_tfp_contribution"]
    early_tfp_level = early_m["mean_tfp_contribution"]

    if early_cap_hc is not None and early_cap_hc >= CAPITAL_HC_SHARE_MIN and later_tfp_level < early_tfp_level:
        verdict = "supported"
        reason = (
            f"Early capital+human-capital share {early_cap_hc*100:.1f}% >= "
            f"{CAPITAL_HC_SHARE_MIN*100:.0f}% and later TFP contribution "
            f"falls from {early_tfp_level*100:.2f}pp/yr to {later_tfp_level*100:.2f}pp/yr."
        )
    elif early_tfp is not None and early_tfp >= 0.50 and later_tfp_level >= early_tfp_level:
        verdict = "refuted"
        reason = (
            f"Early TFP share {early_tfp*100:.1f}% >= 50% and later TFP contribution "
            f"does not fall ({early_tfp_level*100:.2f}pp/yr to {later_tfp_level*100:.2f}pp/yr)."
        )
    else:
        verdict = "partial"
        reason = (
            "The decomposition does not meet the support or refutation threshold: "
            f"early capital+human-capital share is "
            f"{early_cap_hc*100:.1f}% and TFP changes from "
            f"{early_tfp_level*100:.2f}pp/yr to {later_tfp_level*100:.2f}pp/yr."
        )

    by_country = []
    for iso, g in panel.groupby("country_iso3"):
        e = g[(g["phase"] == "early") & (g["output_growth"] > 0)]
        l = g[(g["phase"] == "later") & (g["output_growth"] > 0)]
        if e.empty:
            continue
        em = phase_metrics(e)
        lm = phase_metrics(l)
        by_country.append(
            {
                "country_iso3": iso,
                "country": str(g["country"].iloc[0]),
                "episode_start": int(EPISODES[iso]),
                "early_output_growth": json_float(em["mean_output_growth"]),
                "early_capital_hc_share": json_float(em["capital_hc_share_of_growth"]),
                "early_tfp_contribution": json_float(em["mean_tfp_contribution"]),
                "later_tfp_contribution": json_float(lm["mean_tfp_contribution"]),
                "early_observations": em["n_observations"],
                "later_observations": lm["n_observations"],
            }
        )

    diagnostics = {
        "hypothesis_id": HID,
        "verdict": verdict,
        "reason": reason,
        "metrics": {
            "window_years": WINDOW,
            "early_window_years": EARLY_YEARS,
            "n_panel_observations": int(len(panel)),
            "n_episode_countries": int(panel["country_iso3"].nunique()),
            "early": early_m,
            "later": later_m,
        },
        "threshold": {
            "capital_human_capital_share_min": CAPITAL_HC_SHARE_MIN,
            "later_tfp_must_be_below_early_tfp": True,
        },
        "countries": by_country,
        "vintages": {k: v["vintage_file"] for k, v in manifest.items()},
        "sha256": {k: v["sha256"] for k, v in manifest.items()},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, allow_nan=False) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        f"status: {verdict}\n"
        f"reason: {reason}\n"
        "vintages:\n"
        + "".join(f"  {k}: {v['vintage_file']}\n" for k, v in manifest.items())
    )

    country_rows = "\n".join(
        "| {country_iso3} | {episode_start} | {early_output_growth:+.2%} | {early_capital_hc_share:.1%} | "
        "{early_tfp_contribution:+.2%} | {later_tfp_contribution:+.2%} |".format(
            **{
                **r,
                "later_tfp_contribution": r["later_tfp_contribution"] if r["later_tfp_contribution"] is not None else 0.0,
            }
        )
        for r in by_country
        if r["early_capital_hc_share"] is not None and r["later_tfp_contribution"] is not None
    )

    card = f"""# Result card - {HID}

**Verdict:** {verdict} - {reason}

## Design

PWT panel {PERIOD[0]}-{PERIOD[1]}. For each pre-specified catch-up episode,
5-year annualized output-per-worker growth is decomposed into capital deepening,
human capital, and TFP contributions. The first {EARLY_YEARS} available episode
years are compared with later episode years.

## Threshold

SUPPORTED if capital + human-capital channels explain at least
{CAPITAL_HC_SHARE_MIN:.0%} of positive early catch-up growth and the later TFP
contribution is below the early TFP contribution. REFUTED if early TFP explains
at least 50% and later TFP contribution does not fall. Otherwise PARTIAL.

## Aggregate Metrics

| Metric | Early window | Later window |
|---|---:|---:|
| Observations | {early_m['n_observations']} | {later_m['n_observations']} |
| Countries | {early_m['n_countries']} | {later_m['n_countries']} |
| Output-per-worker growth | {early_m['mean_output_growth']:+.2%}/yr | {later_m['mean_output_growth']:+.2%}/yr |
| Capital contribution | {early_m['mean_capital_contribution']:+.2%}/yr | {later_m['mean_capital_contribution']:+.2%}/yr |
| Human-capital contribution | {early_m['mean_human_capital_contribution']:+.2%}/yr | {later_m['mean_human_capital_contribution']:+.2%}/yr |
| TFP contribution | {early_m['mean_tfp_contribution']:+.2%}/yr | {later_m['mean_tfp_contribution']:+.2%}/yr |
| Capital + human-capital share | {early_m['capital_hc_share_of_growth']:.1%} | {later_m['capital_hc_share_of_growth']:.1%} |
| TFP share | {early_m['tfp_share_of_growth']:.1%} | {later_m['tfp_share_of_growth']:.1%} |

## Country Summary

| ISO3 | Start | Early output growth | Early K+HC share | Early TFP | Later TFP |
|---|---:|---:|---:|---:|---:|
{country_rows}

## Limitations

- Episode starts are coarse historical markers, not machine-coded treatment dates.
- PWT TFP is only available for years with the full national accounts inputs.
- Negative-growth windows are excluded from the share calculation to avoid unstable
  contribution shares; diagnostics retain observation counts.
- This is a growth-accounting decomposition, not a causal estimate of industrial
  policy.

## Next Robustness Checks

- Re-run with 10-year windows.
- Use all below-40%-of-US catch-up observations, not only named episodes.
- Add WGI/Fraser/Heritage market-institution splits once those datasets are loaded.
"""
    (OUT_DIR / "result_card.md").write_text(card)

    print(f"verdict: {verdict} - {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
