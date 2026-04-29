#!/usr/bin/env python3
"""Replication — italian_stagnation_decomposition_1999_2023 (v1).

Spec: hypotheses/growth/italian_stagnation_decomposition_1999_2023.yaml
Steelman: hypotheses/steelman/italian_stagnation_decomposition_1999_2023.md

Decomposition pattern (Nordic-style):
  baseline:  log_gdp_pc_ppp ~ italy_dummy   + year FE   (no country FE,
             which would absorb the time-invariant ITA indicator)
  full:      log_gdp_pc_ppp ~ italy_dummy + REER + debt_gdp + WGI gov_eff
                            + WGI rule_of_law + trade_openness
                            + log_population + urbanisation
                            + year FE

Residual share = |italy_dummy_coef_full| / |italy_dummy_coef_baseline|.
SUPPORTED iff residual_share <= 0.40 (channels absorb the bulk of the gap).

DEVIATIONS:
- Spec listed several constructed series (OECD prime-age LFP, Penn World
  Table TFP, manual political-turnover coding). Not in vintages — substituted
  with WGI gov_eff + rule_of_law + IMF debt + trade openness + urbanisation
  as the closest available channel proxies.
- The synthetic-control sub-spec is not run in v1.
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
HID = "italian_stagnation_decomposition_1999_2023"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

ITALY = "ITA"
PEERS = ["DEU", "FRA", "ESP", "PRT", "GRC"]
ALL_COUNTRIES = sorted([ITALY] + PEERS)
PERIOD = (1999, 2023)
THRESHOLD = 0.40


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(65536), b""):
            h.update(c)
    return h.hexdigest()


def latest(pub: str, ser: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{ser}@*.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{ser}")
    return files[-1]


def load_long(path: Path, var: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    val_col = "value" if "value" in t.columns else [c for c in t.columns
                                                    if c not in ("country_name", "country_iso3", "year", "indicator_id")][0]
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    t = t[["country_iso3", "year", val_col]].copy()
    t["year"] = t["year"].astype(int)
    t[val_col] = pd.to_numeric(t[val_col], errors="coerce")
    return t.rename(columns={val_col: var, "country_iso3": "country"})


def load_reer(path: Path) -> pd.DataFrame:
    """BIS WS_EER → annual mean of monthly real EER, broad basket."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["FREQ"] == "M") & (t["EER_TYPE"] == "R") &
            (t["EER_BASKET"] == "B")].copy()
    if sub.empty:
        # fall back to nominal effective if real isn't tagged as R
        sub = t[(t["FREQ"] == "M") & (t["EER_BASKET"] == "B")].copy()
    sub["year"] = sub["period"].astype(str).str[:4].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["country"] = sub["REF_AREA"]
    iso2_to_iso3 = {"IT": "ITA", "DE": "DEU", "FR": "FRA", "ES": "ESP",
                    "PT": "PRT", "GR": "GRC"}
    sub["country"] = sub["country"].map(iso2_to_iso3).fillna(sub["country"])
    out = (sub.groupby(["country", "year"])["value"].mean().reset_index()
           .rename(columns={"value": "reer"}))
    return out[out["country"].isin(ALL_COUNTRIES)]


def assemble() -> tuple[pd.DataFrame, dict]:
    paths = {
        "gdp_pc_ppp":      ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "trade_openness":  ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "urbanisation":    ("world_bank_wdi", "SP.URB.TOTL.IN.ZS"),
        "population":      ("world_bank_wdi", "SP.POP.TOTL"),
        "debt_gdp":        ("imf", "GGXWDG_NGDP"),
        "gov_eff":         ("wgi", "GOV_WGI_GE.EST"),
        "rule_of_law":     ("wgi", "GOV_WGI_RL.EST"),
    }
    manifest, frames = {}, []
    for var, (pub, ser) in paths.items():
        p = latest(pub, ser)
        manifest[var] = {"publisher": pub, "series": ser,
                         "vintage_file": str(p.relative_to(REPO_ROOT)),
                         "sha256": sha256(p)}
        frames.append(load_long(p, var))

    reer_path = latest("bis", "WS_EER")
    manifest["reer"] = {"publisher": "bis", "series": "WS_EER",
                        "vintage_file": str(reer_path.relative_to(REPO_ROOT)),
                        "sha256": sha256(reer_path)}
    frames.append(load_reer(reer_path))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL_COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_population"] = np.log(panel["population"])
    panel["italy_dummy"] = (panel["country"] == ITALY).astype(int)
    return panel.sort_values(["country", "year"]).reset_index(drop=True), manifest


def fit_baseline(df: pd.DataFrame) -> dict:
    d = df[["country", "year", "log_gdp_pc_ppp", "italy_dummy"]].dropna().copy()
    d = d.set_index(["country", "year"])
    d["const"] = 1.0
    res = PanelOLS(d["log_gdp_pc_ppp"], d[["const", "italy_dummy"]],
                   time_effects=True, check_rank=False, drop_absorbed=True
                   ).fit(cov_type="clustered", cluster_entity=True)
    return {"n_obs": int(res.nobs), "coef": float(res.params["italy_dummy"]),
            "se": float(res.std_errors["italy_dummy"]),
            "p": float(res.pvalues["italy_dummy"])}


def fit_full(df: pd.DataFrame) -> dict:
    cols = ["country", "year", "log_gdp_pc_ppp", "italy_dummy", "reer",
            "debt_gdp", "gov_eff", "rule_of_law", "trade_openness",
            "log_population", "urbanisation"]
    d = df[cols].dropna().copy()
    d = d.set_index(["country", "year"])
    d["const"] = 1.0
    X = d[["const", "italy_dummy", "reer", "debt_gdp", "gov_eff",
           "rule_of_law", "trade_openness", "log_population", "urbanisation"]]
    res = PanelOLS(d["log_gdp_pc_ppp"], X, time_effects=True,
                   check_rank=False, drop_absorbed=True
                   ).fit(cov_type="clustered", cluster_entity=True)
    out = {"n_obs": int(res.nobs),
           "coef": float(res.params["italy_dummy"]) if "italy_dummy" in res.params.index else float("nan"),
           "se": float(res.std_errors["italy_dummy"]) if "italy_dummy" in res.std_errors.index else float("nan"),
           "p": float(res.pvalues["italy_dummy"]) if "italy_dummy" in res.pvalues.index else float("nan"),
           "channels": {}}
    for ch in ["reer", "debt_gdp", "gov_eff", "rule_of_law", "trade_openness",
               "log_population", "urbanisation"]:
        if ch in res.params.index:
            out["channels"][ch] = {"coef": float(res.params[ch]),
                                   "se": float(res.std_errors[ch]),
                                   "p": float(res.pvalues[ch])}
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    base = fit_baseline(panel)
    full = fit_full(panel)
    rs = abs(full["coef"]) / abs(base["coef"]) if abs(base["coef"]) > 1e-12 else float("nan")

    if np.isnan(rs):
        verdict = "indeterminate"
    elif rs <= THRESHOLD:
        verdict = "supported"
    else:
        verdict = f"weakened — residual_share {rs:.3f} > threshold {THRESHOLD:.2f}"

    # Italian stagnation stylised fact check
    ita = panel[panel["country"] == ITALY].set_index("year")["log_gdp_pc_ppp"].dropna()
    ita_2023 = float(ita.loc[ita.index.max()]) if len(ita) else float("nan")
    ita_1999 = float(ita.loc[ita.index.min()]) if len(ita) else float("nan")
    ita_log_change = ita_2023 - ita_1999

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID, "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "deviations": [
            "Spec channels prime_age_lfp, PWT TFP, political_turnover coding "
            "not in vintages; substituted WGI gov_eff + rule_of_law as "
            "institutional/political proxies and IMF debt + REER + trade "
            "openness as macroeconomic channels.",
            "Synthetic-control sub-spec not run.",
        ]
    }, sort_keys=False))

    rows = [{"spec": "baseline", "term": "italy_dummy", "estimate": base["coef"],
             "se": base["se"], "p": base["p"], "n_obs": base["n_obs"]},
            {"spec": "full", "term": "italy_dummy", "estimate": full["coef"],
             "se": full["se"], "p": full["p"], "n_obs": full["n_obs"]}]
    for ch, v in full["channels"].items():
        rows.append({"spec": "full", "term": ch, "estimate": v["coef"],
                     "se": v["se"], "p": v["p"], "n_obs": full["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diag = {
        "sample": {"countries": ALL_COUNTRIES, "period": PERIOD,
                   "n_obs_panel": int(len(panel))},
        "baseline_italy_coef": base["coef"], "full_italy_coef": full["coef"],
        "residual_share": rs, "threshold": THRESHOLD,
        "italy_log_gdp_pc_ppp_1999": ita_1999,
        "italy_log_gdp_pc_ppp_2023": ita_2023,
        "italy_cumulative_log_change": ita_log_change,
        "verdict": verdict,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2,
                                                         default=lambda o: None) + "\n")

    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"Pre-registered residual-share threshold: {THRESHOLD:.2f} on the "
        "Italy-vs-peer log-GDP-pc-PPP gap.",
        "",
        "## Coefficient summary",
        "",
        "| Spec | Term | Estimate | SE | n_obs |",
        "|---|---|---:|---:|---:|",
        f"| baseline | italy_dummy | {base['coef']:+.4f} | {base['se']:.4f} | {base['n_obs']} |",
        f"| full | italy_dummy | {full['coef']:+.4f} | {full['se']:.4f} | {full['n_obs']} |",
        "",
        f"Residual share: **{rs:.3f}**  (threshold {THRESHOLD:.2f})",
        "",
        f"Italian log-GDP-pc-PPP cumulative change 1999-2023: {ita_log_change:+.3f} "
        f"(≈{(np.exp(ita_log_change)-1)*100:+.1f}%); spec stagnation stylised "
        f"fact requires |change| < 0.10.",
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
        "- WGI gov_eff + rule_of_law substitute for the spec's PMR/political-",
        "  turnover/judicial-slowness channels.",
        "- BIS REER (broad basket, real if available) is the euro-entry-",
        "  overvaluation proxy.",
        "- WDI urbanisation + log-population are demographic-style controls; ",
        "  spec's old-age dependency / prime-age LFP not in vintages.",
        "- Synthetic-control sub-spec deferred.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  baseline_coef={base['coef']:+.4f}  full_coef={full['coef']:+.4f}  "
          f"residual_share={rs:.3f}  threshold={THRESHOLD:.2f}")
    print(f"artifacts: {OUT_DIR}")
    return 0 if (not np.isnan(rs) and rs <= THRESHOLD) else 1


if __name__ == "__main__":
    sys.exit(main())
