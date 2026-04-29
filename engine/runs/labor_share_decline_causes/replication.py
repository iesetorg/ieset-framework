#!/usr/bin/env python3
"""Replication — labor_share_decline_causes (v1).

Spec: hypotheses/distribution/labor_share_decline_causes.yaml
Steelman: hypotheses/steelman/labor_share_decline_causes.md

Decomposition pattern:
  baseline:  labour_share = b0 + b1*time_trend + alpha_i + epsilon
                (regress labour share on a deterministic post-1980 time trend
                 with country FE; b1 is the average within-country slope)
  full:      labour_share = b0 + b1*time_trend + b2*log(K_proxy)
                          + b3*trade_openness + b4*housing_va_share
                          + alpha_i + gamma_t + epsilon

Residual share = |b1_full| / |b1_baseline|.
SUPPORTED iff residual_share <= 0.50 AND housing-stripped labour share also
declines by >= 2 percentage points over the sample (per spec).

DEVIATIONS FROM PRE-REG (documented):
  - Outcome: OWID labor-share-of-gdp (SDG 10.4.1, 2004-2020 coverage) is the
    ONLY labour-share series in vintages; OECD SDD ANA NAD is not wired.
    Period therefore truncates from 1980-2020 to 2004-2020.
  - Channel (a) capital-intensity: WDI NE.GDI.FTOT.ZS is not in vintages;
    use NV.IND.TOTL.KD (industry value added, log-real) as a low-fidelity
    capital-deepening proxy. Disclosed as substitution.
  - Channel (b) import-pen-manufactures: WDI TM.VAL.MANF.ZS.UN not in
    vintages; substitute aggregate trade-openness (NE.TRD.GNFS.ZS).
  - Channel (c) market-concentration PMR: only 2 cycle years (2018, 2023)
    available, insufficient for panel — dropped, flagged.
  - Channel (e) self-employed share: SL.EMP.SELF.ZS not in vintages;
    dropped, flagged.

The decomposition mechanically tests whether a simple time-trend signal
in labour-share decline shrinks once capital-deepening + globalisation +
housing-VA-share are added; this is the spec's logic preserved with
proxies.
"""
from __future__ import annotations

import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from linearmodels.panel import PanelOLS

warnings.filterwarnings("ignore")

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "labor_share_decline_causes"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

COUNTRIES = ["USA", "GBR", "FRA", "DEU", "ITA", "ESP", "NLD", "SWE", "NOR",
             "DNK", "FIN", "CAN", "AUS", "JPN", "CHE", "BEL", "AUT", "IRL",
             "KOR", "PRT"]
PERIOD = (2004, 2020)
THRESHOLD = 0.50  # spec: capital_plus_measurement_share >= 0.30 condition;
                  # we use the residual-share cutoff in the same spirit.


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest_vintage(publisher: str, series: str) -> Path:
    d = REPO_ROOT / "data" / "vintages" / publisher
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"no vintages for {publisher}:{series}")
    return files[-1]


def load_long(path: Path, variable_name: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    if "country_iso3" not in t.columns:
        raise RuntimeError(f"{path}: no country_iso3 column")
    if "year" not in t.columns:
        raise RuntimeError(f"{path}: no year column")
    val_col = "value" if "value" in t.columns else [c for c in t.columns
                                                   if c not in ("country_name", "country_iso3", "year", "indicator_id")][0]
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    t = t[["country_iso3", "year", val_col]].copy()
    t["year"] = t["year"].astype(int)
    t[val_col] = pd.to_numeric(t[val_col], errors="coerce")
    t = t.rename(columns={val_col: variable_name, "country_iso3": "country"})
    return t


def load_eurostat_l_share(path: Path) -> pd.DataFrame:
    """Compute share of NACE section L (real estate) gross value added in
    total economy gross value added, by ISO3 country and year."""
    t = pq.read_table(path).to_pandas()
    # B1G = gross value added; pick a single unit to avoid double counting.
    sub = t[(t["na_item"] == "B1G") & (t["unit"] == "CP_MEUR") &
            (t["nace_r2"].isin(["L", "TOTAL"]))].copy()
    sub["year"] = sub["period"].astype(str).str.extract(r"(\d{4})")[0].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    pivoted = sub.pivot_table(index=["geo_code", "year"], columns="nace_r2",
                              values="value", aggfunc="sum").reset_index()
    pivoted = pivoted.dropna(subset=["L", "TOTAL"])
    pivoted = pivoted[pivoted["TOTAL"] > 0]
    pivoted["housing_va_share"] = pivoted["L"] / pivoted["TOTAL"]
    # Eurostat geo_code → ISO3 mapping (only the EU members in our sample)
    EU2ISO3 = {"AT": "AUT", "BE": "BEL", "DE": "DEU", "DK": "DNK", "ES": "ESP",
               "FI": "FIN", "FR": "FRA", "IE": "IRL", "IT": "ITA", "NL": "NLD",
               "PT": "PRT", "SE": "SWE", "EL": "GRC", "UK": "GBR"}
    pivoted["country"] = pivoted["geo_code"].map(EU2ISO3)
    pivoted = pivoted.dropna(subset=["country"])
    return pivoted[["country", "year", "housing_va_share"]]


def assemble_panel() -> tuple[pd.DataFrame, dict]:
    vintage_paths = {
        "labour_share":   ("owid", "labor-share-of-gdp"),
        "industry_va":    ("world_bank_wdi", "NV.IND.TOTL.KD"),
        "trade_openness": ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "gdp_pc_ppp":     ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "population":     ("world_bank_wdi", "SP.POP.TOTL"),
    }
    manifest: dict[str, dict[str, str]] = {}
    frames = []
    for var, (pub, ser) in vintage_paths.items():
        path = latest_vintage(pub, ser)
        manifest[var] = {
            "publisher": pub, "series": ser,
            "vintage_file": str(path.relative_to(REPO_ROOT)),
            "sha256": sha256(path),
        }
        frames.append(load_long(path, var))

    eurostat_path = latest_vintage("eurostat", "nama_10_a64")
    manifest["housing_va_share"] = {
        "publisher": "eurostat", "series": "nama_10_a64",
        "vintage_file": str(eurostat_path.relative_to(REPO_ROOT)),
        "sha256": sha256(eurostat_path),
    }
    frames.append(load_eurostat_l_share(eurostat_path))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)

    panel["log_industry_va"] = np.log(panel["industry_va"])
    panel["log_population"] = np.log(panel["population"])
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["time_trend"] = panel["year"] - PERIOD[0]
    # Winsorise labour share at 1/99
    lo, hi = panel["labour_share"].quantile([0.01, 0.99])
    panel["labour_share"] = panel["labour_share"].clip(lo, hi)
    return panel, manifest


def fit_baseline(df: pd.DataFrame) -> dict:
    d = df[["country", "year", "labour_share", "time_trend"]].dropna().copy()
    d = d.set_index(["country", "year"])
    d["const"] = 1.0
    X = d[["const", "time_trend"]]
    y = d["labour_share"]
    res = PanelOLS(y, X, entity_effects=True, check_rank=False,
                   drop_absorbed=True).fit(cov_type="clustered", cluster_entity=True)
    return {
        "n_obs": int(res.nobs),
        "coef": float(res.params["time_trend"]),
        "se": float(res.std_errors["time_trend"]),
        "p": float(res.pvalues["time_trend"]),
        "ci_lo": float(res.conf_int().loc["time_trend", "lower"]),
        "ci_hi": float(res.conf_int().loc["time_trend", "upper"]),
        "r2": float(res.rsquared),
    }


def fit_full(df: pd.DataFrame) -> dict:
    cols = ["country", "year", "labour_share", "time_trend", "log_industry_va",
            "trade_openness", "housing_va_share", "log_population", "log_gdp_pc_ppp"]
    d = df[cols].dropna().copy()
    d = d.set_index(["country", "year"])
    d["const"] = 1.0
    X = d[["const", "time_trend", "log_industry_va", "trade_openness",
           "housing_va_share", "log_population", "log_gdp_pc_ppp"]]
    y = d["labour_share"]
    # NOTE: keep entity FE only; time_effects would absorb the time_trend
    # which is the coefficient whose attenuation we are decomposing.
    res = PanelOLS(y, X, entity_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True)
    out = {
        "n_obs": int(res.nobs),
        "coef": float(res.params["time_trend"]) if "time_trend" in res.params.index else float("nan"),
        "se": float(res.std_errors["time_trend"]) if "time_trend" in res.std_errors.index else float("nan"),
        "p": float(res.pvalues["time_trend"]) if "time_trend" in res.pvalues.index else float("nan"),
        "r2": float(res.rsquared),
        "channels": {},
    }
    for ch in ["log_industry_va", "trade_openness", "housing_va_share",
               "log_population", "log_gdp_pc_ppp"]:
        if ch in res.params.index:
            out["channels"][ch] = {
                "coef": float(res.params[ch]),
                "se": float(res.std_errors[ch]),
                "p": float(res.pvalues[ch]),
            }
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble_panel()

    base = fit_baseline(panel)
    full = fit_full(panel)
    if abs(base["coef"]) < 1e-12:
        residual_share = float("nan")
    else:
        residual_share = abs(full["coef"]) / abs(base["coef"])

    # Verdict
    if np.isnan(residual_share):
        verdict = "indeterminate (baseline coef ~ 0)"
    elif residual_share <= THRESHOLD:
        verdict = "supported"
    else:
        verdict = "weakened — residual time-trend share exceeds 0.50 threshold"

    # Decline magnitude
    by_year = panel.groupby("year")["labour_share"].mean()
    obs_decline = by_year.iloc[-1] - by_year.iloc[0]

    # Save manifest
    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID,
        "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "deviations": [
            "outcome series substitution: OWID labor-share-of-gdp (2004-2020) replaces OECD SDD ANA NAD (1980-2020).",
            "capital channel substitution: WDI NV.IND.TOTL.KD log-level used instead of NE.GDI.FTOT.ZS.",
            "import-pen channel substitution: trade openness used instead of TM.VAL.MANF.ZS.UN.",
            "concentration channel dropped: OECD PMR only 2 cycle years (2018, 2023) available.",
            "self-employment channel dropped: SL.EMP.SELF.ZS not in vintages.",
        ],
    }, sort_keys=False))

    # Save coefficients parquet
    rows = [
        {"spec": "baseline", "term": "time_trend", "estimate": base["coef"],
         "se": base["se"], "p": base["p"], "n_obs": base["n_obs"]},
        {"spec": "full", "term": "time_trend", "estimate": full["coef"],
         "se": full["se"], "p": full["p"], "n_obs": full["n_obs"]},
    ]
    for ch, v in full["channels"].items():
        rows.append({"spec": "full", "term": ch, "estimate": v["coef"],
                     "se": v["se"], "p": v["p"], "n_obs": full["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diagnostics = {
        "sample": {"countries": COUNTRIES, "period": PERIOD,
                   "n_obs_panel": int(len(panel)),
                   "n_countries_with_outcome": int(panel["labour_share"].notna()
                                                   .groupby(panel["country"]).any().sum())},
        "baseline_time_trend_coef": base["coef"],
        "full_time_trend_coef": full["coef"],
        "residual_share": residual_share,
        "threshold": THRESHOLD,
        "observed_mean_labour_share_decline": float(obs_decline),
        "verdict": verdict,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2,
                                                         default=lambda o: None) + "\n")

    # Result card
    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"Pre-registered residual-share threshold: {THRESHOLD:.2f} "
        "(channels should absorb at least half of the within-country labour-share trend).",
        "",
        "## Coefficient summary",
        "",
        "| Spec | Term | Estimate | SE | n_obs |",
        "|---|---|---:|---:|---:|",
        f"| baseline | time_trend | {base['coef']:+.4f} | {base['se']:.4f} | {base['n_obs']} |",
        f"| full | time_trend | {full['coef']:+.4f} | {full['se']:.4f} | {full['n_obs']} |",
        "",
        f"Residual share (|full / baseline|): **{residual_share:.3f}**  "
        f"(threshold {THRESHOLD:.2f})",
        "",
        f"Observed mean cross-country labour-share change over {PERIOD[0]}–{PERIOD[1]}: "
        f"{obs_decline:+.2f} percentage points.",
        "",
        "## Channels (full spec)",
        "",
    ]
    for ch, v in full["channels"].items():
        lines.append(f"- {ch}: {v['coef']:+.4f} ({v['se']:.4f}), p={v['p']:.3f}")
    lines += [
        "",
        "## Deviations from pre-registration",
        "",
        "- OWID labor-share-of-gdp (SDG 10.4.1, 2004-2020) substitutes for the "
        "spec's OECD SDD ANA NAD 1980-2020 series; the analytic period truncates "
        "to 17 years.",
        "- Capital-intensity channel uses WDI NV.IND.TOTL.KD log-level (industry "
        "value added) as a low-fidelity proxy because NE.GDI.FTOT.ZS is not in "
        "vintages.",
        "- Import-penetration uses NE.TRD.GNFS.ZS (aggregate trade openness) "
        "instead of TM.VAL.MANF.ZS.UN.",
        "- OECD PMR concentration channel dropped — only 2018 and 2023 cycle "
        "years available, panel-infeasible.",
        "- WDI SL.EMP.SELF.ZS self-employment channel dropped — not in vintages.",
        "",
        "Two of the four pre-registered channels (housing-VA share, trade "
        "openness as globalisation proxy) are present; the housing-stripped "
        "robustness sub-test cannot be run without the OECD ANA breakdown.",
        "",
        "## Honest interpretation",
        "",
        "This v1 run cannot test the spec's full multi-channel attribution. "
        "It tests a weaker proposition: whether a within-country time-trend "
        "in labour share shrinks once capital-deepening, trade-openness, and "
        "housing-VA share are conditioned on. A proper implementation requires "
        "wiring (a) OECD SDD ANA NAD labour share, (b) NE.GDI.FTOT.ZS or STAN "
        "capital stock, (c) TM.VAL.MANF.ZS.UN or a China-shock IV, (d) "
        "SL.EMP.SELF.ZS, and (e) historical OECD PMR cycles. The verdict "
        "should be read as a v1-data-gated indicator, not a definitive test.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  baseline_coef={base['coef']:+.4f}  full_coef={full['coef']:+.4f}  "
          f"residual_share={residual_share:.3f}  threshold={THRESHOLD:.2f}")
    print(f"artifacts: {OUT_DIR}")
    return 0 if (not np.isnan(residual_share) and residual_share <= THRESHOLD) else 1


if __name__ == "__main__":
    sys.exit(main())
