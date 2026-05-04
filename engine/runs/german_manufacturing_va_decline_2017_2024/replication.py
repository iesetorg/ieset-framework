#!/usr/bin/env python3
"""Replication — german_manufacturing_va_decline_2017_2024 (v1).

Spec: hypotheses/growth/german_manufacturing_va_decline_2017_2024.yaml
Steelman: hypotheses/steelman/german_manufacturing_va_decline_2017_2024.md

Descriptive structural-decomposition analysis (SDA).

Step 1: Document the manufacturing-VA-share trajectory for DEU vs peer
        pool (FRA, ITA, NLD, SWE) using Eurostat nama_10r_3gva (NACE C
        share of TOTAL, B1G basis, current-price). Test pre-registered
        2017-2024 share-change >= -2pp threshold.

Step 2: TWFE panel-FE decomposition (DEU + peers, 2010-2023):
        baseline: log(manuf_va_share) = α_i + γ_t + β·deu_post_2017
        full:     ... + λ_1·log(REER) + λ_2·log_unit_labour_cost
                  + λ_3·trade_openness
        residual_share = |β_full| / |β_baseline|.

Step 3: Channel-share attribution (via β attenuation when each channel
        added sequentially) — illustrative not causally identified.

DEVIATIONS from spec:
- Eurostat NRG_PC_205 industrial electricity price not in vintages;
  energy-cost channel proxied indirectly via REER (BIS WS_EER) +
  log unit labour cost (Eurostat nama_10_lp_ulc NULC_HW index).
- OECD STAN manufacturing hours not in vintages; manufacturing
  employment-share channel skipped.
- OECD TiVA China import penetration channel not in vintages;
  channel skipped (flagged in deviations).
- External-demand channel not constructed (would require
  trade-weighted destination GDP from OECD or Comtrade).
- Sample period clipped to 2010-2023 (Eurostat REER + ULC data
  bounds); 2024 final values incomplete.
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
HID = "german_manufacturing_va_decline_2017_2024"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID

TREATED = "DEU"
PEERS = ["FRA", "ITA", "NLD", "SWE", "ESP", "BEL", "AUT"]
ALL_COUNTRIES = [TREATED] + PEERS
PERIOD = (2010, 2023)
THRESHOLD_PP = -2.0  # spec: at-least 2pp decline 2017→2024 (we use 2017→latest)

EU2ISO3 = {"DE": "DEU", "FR": "FRA", "IT": "ITA", "NL": "NLD", "SE": "SWE",
           "ES": "ESP", "BE": "BEL", "AT": "AUT", "PT": "PRT"}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(pub: str, ser: str) -> Path:
    files = sorted((REPO_ROOT / "data" / "vintages" / pub).glob(f"{ser}@*.parquet"),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{ser}")
    return files[-1]


def load_long_wdi(path: Path, var: str) -> pd.DataFrame:
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": var, "country_iso3": "country"})


def load_eurostat_manuf_share(path: Path) -> pd.DataFrame:
    """Manufacturing (NACE C) gross value-added share of total economy GVA."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["unit"] == "CP_MEUR") & (t["nace_r2"].isin(["C", "TOTAL"]))].copy()
    if "na_item" in sub.columns:
        sub = sub[sub["na_item"] == "B1G"].copy()
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    pivot = sub.pivot_table(index=["geo_code", "year"], columns="nace_r2",
                            values="value", aggfunc="sum").reset_index()
    pivot = pivot.dropna(subset=["C", "TOTAL"])
    pivot = pivot[pivot["TOTAL"] > 0]
    pivot["manuf_va_share"] = pivot["C"] / pivot["TOTAL"]
    pivot["country"] = pivot["geo_code"].map(EU2ISO3)
    pivot = pivot.dropna(subset=["country"])
    return pivot[["country", "year", "manuf_va_share"]]


def load_eurostat_manuf_lci(path: Path) -> pd.DataFrame:
    """Unit-labour-cost proxy, preferring manufacturing LCI when available."""
    t = pq.read_table(path).to_pandas()
    if {"nace_r2", "lcstruct"}.issubset(t.columns):
        sub = t[(t["nace_r2"] == "C") & (t["lcstruct"] == "D11") &
                (t["unit"] == "I20")].copy()
    else:
        # On-disk Eurostat vintage is the national-accounts ULC dataset, not
        # the labour-cost-index-by-NACE dataset used in the first draft.
        sub = t[(t["na_item"] == "NULC_HW") & (t["unit"] == "I20")].copy()
    sub["year"] = sub["period"].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    sub["country"] = sub["geo_code"].map(EU2ISO3)
    sub = sub.dropna(subset=["country"])
    return sub.groupby(["country", "year"], as_index=False)["value"].mean().rename(
        columns={"value": "manuf_wage_cost_idx"})


def load_bis_reer(path: Path) -> pd.DataFrame:
    """BIS REER, broad basket, real if available; annual mean of monthly."""
    t = pq.read_table(path).to_pandas()
    sub = t[(t["FREQ"] == "M") & (t["EER_TYPE"] == "R") &
            (t["EER_BASKET"] == "B")].copy()
    if sub.empty:
        sub = t[(t["FREQ"] == "M") & (t["EER_BASKET"] == "B")].copy()
    sub["year"] = sub["period"].astype(str).str[:4].astype(int)
    sub["value"] = pd.to_numeric(sub["value"], errors="coerce")
    iso2_to_iso3 = {"DE": "DEU", "FR": "FRA", "IT": "ITA", "NL": "NLD",
                    "SE": "SWE", "ES": "ESP", "BE": "BEL", "AT": "AUT"}
    sub["country"] = sub["REF_AREA"].map(iso2_to_iso3).fillna(sub["REF_AREA"])
    out = (sub.groupby(["country", "year"])["value"].mean().reset_index()
           .rename(columns={"value": "reer"}))
    return out[out["country"].isin(ALL_COUNTRIES)]


def assemble() -> tuple[pd.DataFrame, dict]:
    manifest, frames = {}, []

    p = latest("eurostat", "nama_10r_3gva")
    manifest["manuf_va_share"] = {"publisher": "eurostat", "series": "nama_10r_3gva",
                                  "vintage_file": str(p.relative_to(REPO_ROOT)),
                                  "sha256": sha256(p)}
    frames.append(load_eurostat_manuf_share(p))

    p = latest("eurostat", "nama_10_lp_ulc")
    manifest["manuf_wage_cost_idx"] = {"publisher": "eurostat", "series": "nama_10_lp_ulc",
                                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                                       "sha256": sha256(p)}
    frames.append(load_eurostat_manuf_lci(p))

    p = latest("bis", "WS_EER")
    manifest["reer"] = {"publisher": "bis", "series": "WS_EER",
                        "vintage_file": str(p.relative_to(REPO_ROOT)),
                        "sha256": sha256(p)}
    frames.append(load_bis_reer(p))

    p = latest("world_bank_wdi", "NE.TRD.GNFS.ZS")
    manifest["trade_openness"] = {"publisher": "world_bank_wdi", "series": "NE.TRD.GNFS.ZS",
                                  "vintage_file": str(p.relative_to(REPO_ROOT)),
                                  "sha256": sha256(p)}
    frames.append(load_long_wdi(p, "trade_openness"))

    p = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    manifest["gdp_pc_ppp"] = {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.PP.KD",
                              "vintage_file": str(p.relative_to(REPO_ROOT)),
                              "sha256": sha256(p)}
    frames.append(load_long_wdi(p, "gdp_pc_ppp"))

    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL_COUNTRIES)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel["log_manuf_va_share"] = np.log(panel["manuf_va_share"])
    panel["log_reer"] = np.log(panel["reer"])
    panel["log_wage_cost"] = np.log(panel["manuf_wage_cost_idx"])
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["deu_post_2017"] = ((panel["country"] == TREATED) &
                              (panel["year"] >= 2017)).astype(int)
    return panel.sort_values(["country", "year"]).reset_index(drop=True), manifest


def fit(df: pd.DataFrame, outcome: str, regressors: list[str]) -> dict:
    cols = ["country", "year", outcome] + regressors
    d = df[cols].dropna().copy().set_index(["country", "year"])
    X = d[regressors]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=True, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True)
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in regressors:
        if t in res.params.index:
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    # Step 1: descriptive — DEU manuf VA share trajectory
    deu = panel[panel["country"] == TREATED][["year", "manuf_va_share"]].dropna()
    deu = deu.set_index("year")
    share_2017 = float(deu.loc[2017, "manuf_va_share"]) if 2017 in deu.index else float("nan")
    last_year = int(deu.index.max())
    share_last = float(deu.loc[last_year, "manuf_va_share"])
    pp_change = (share_last - share_2017) * 100.0  # in percentage-points

    # Step 2: TWFE baseline (DEU-post-2017 indicator only, with FE)
    baseline = fit(panel, "log_manuf_va_share", ["deu_post_2017"])
    full = fit(panel, "log_manuf_va_share",
               ["deu_post_2017", "log_reer", "log_wage_cost", "trade_openness"])

    b_base = baseline["coefs"].get("deu_post_2017", {})
    b_full = full["coefs"].get("deu_post_2017", {})
    base_coef = b_base.get("estimate", float("nan"))
    full_coef = b_full.get("estimate", float("nan"))

    if abs(base_coef) > 1e-9:
        residual_share = abs(full_coef) / abs(base_coef)
    else:
        residual_share = float("nan")

    # Falsification rule:
    #   (a) DEU manuf share change 2017→latest <= -2pp
    #   (b) channels absorb >= 40% (residual_share <= 0.60)
    #   (c) no single channel >60% of explained change — assess by
    #       single-channel attenuation
    decline_ok = pp_change <= THRESHOLD_PP
    channels_ok = (not np.isnan(residual_share)) and residual_share <= 0.60

    # Single-channel test: which channel has the biggest attenuation?
    chan_names = ["log_reer", "log_wage_cost", "trade_openness"]
    chan_attn = {}
    for ch in chan_names:
        m = fit(panel, "log_manuf_va_share", ["deu_post_2017", ch])
        c = m["coefs"].get("deu_post_2017", {}).get("estimate", float("nan"))
        chan_attn[ch] = {"deu_post_coef": c,
                         "attenuation": (base_coef - c) if not np.isnan(c) else float("nan")}
    total_attn = base_coef - full_coef if not np.isnan(full_coef) else float("nan")
    if abs(total_attn) > 1e-9:
        for ch in chan_names:
            chan_attn[ch]["share_of_total_attenuation"] = chan_attn[ch]["attenuation"] / total_attn
    monocausal = any(abs(chan_attn[ch].get("share_of_total_attenuation", 0)) > 0.60
                     for ch in chan_names if not np.isnan(chan_attn[ch].get("share_of_total_attenuation", float("nan"))))

    all_pass = decline_ok and channels_ok and not monocausal

    if all_pass:
        verdict = (f"supported — DEU manuf-VA share fell {pp_change:+.2f}pp 2017→{last_year}; "
                   f"channels (REER+ULC+trade) absorb {(1 - residual_share)*100:.0f}% of TWFE "
                   f"DEU-post-2017 effect; no single channel >60% of attenuation")
    elif not decline_ok:
        verdict = f"refuted — DEU manuf-VA share change {pp_change:+.2f}pp does not meet -2pp threshold (2017→{last_year})"
    elif not channels_ok:
        verdict = (f"weakened — decline of {pp_change:+.2f}pp confirmed but residual share "
                   f"{residual_share:.2f} > 0.60 (channels miss most of the variation)")
    else:
        verdict = (f"weakened — decline confirmed and channels absorb material share, but a "
                   f"single channel exceeds 60% of explained attenuation (monocausal)")

    rows = [
        {"spec": "baseline", "term": "deu_post_2017", "estimate": base_coef,
         "se": b_base.get("se", float("nan")), "p": b_base.get("p", float("nan")),
         "n_obs": baseline["n_obs"]},
        {"spec": "full", "term": "deu_post_2017", "estimate": full_coef,
         "se": b_full.get("se", float("nan")), "p": b_full.get("p", float("nan")),
         "n_obs": full["n_obs"]},
    ]
    for ch, v in full["coefs"].items():
        if ch == "deu_post_2017":
            continue
        rows.append({"spec": "full", "term": ch, "estimate": v["estimate"],
                     "se": v["se"], "p": v["p"], "n_obs": full["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    diag = {
        "verdict": verdict, "all_pass": all_pass,
        "deu_manuf_va_share_2017": share_2017,
        f"deu_manuf_va_share_{last_year}": share_last,
        "deu_manuf_va_share_change_pp": pp_change,
        "threshold_pp": THRESHOLD_PP,
        "twfe_baseline_deu_post_2017": b_base,
        "twfe_full_deu_post_2017": b_full,
        "residual_share": residual_share,
        "channel_single_attenuation": chan_attn,
        "monocausal_flag": monocausal,
        "sample": {"countries": ALL_COUNTRIES, "period": PERIOD,
                   "n_obs_panel": int(len(panel))},
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diag, indent=2,
                                                         default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": HID, "run_utc": pd.Timestamp.utcnow().isoformat(),
        "vintages": manifest,
        "deviations": [
            "Outcome: Eurostat nama_10r_3gva NACE-C share of TOTAL GVA (current price) replaces WDI NV.IND.MANF.CD in the bespoke decomposition.",
            "Energy-cost channel: NRG_PC_205 industrial electricity price not in vintages; proxied via BIS REER + Eurostat nama_10_lp_ulc national-accounts ULC index (NULC_HW, 2020=100).",
            "Chinese import-penetration channel: OECD TiVA not in vintages; channel skipped.",
            "External-demand channel: trade-weighted destination GDP not constructed; channel skipped.",
            "Period clipped to 2010-2023 for balanced peer coverage in the decomposition; 2024 not yet final for all peers.",
        ],
    }, sort_keys=False))

    lines = [
        f"# Result card — {HID}",
        "",
        f"**Verdict:** {verdict}",
        "",
        f"**DEU manufacturing VA share (NACE C / TOTAL):** "
        f"{share_2017*100:.2f}% (2017) → {share_last*100:.2f}% ({last_year}). "
        f"Change: **{pp_change:+.2f} pp** "
        f"(spec threshold: ≤ {THRESHOLD_PP:.1f} pp).",
        "",
        "## TWFE decomposition (country + year FE, DEU + EU peers)",
        "",
        "| Spec | β(deu_post_2017) | SE | p | n_obs |",
        "|---|---:|---:|---:|---:|",
        f"| baseline (DEU-post-2017 only) | {base_coef:+.4f} | {b_base.get('se', float('nan')):.4f} | {b_base.get('p', float('nan')):.3f} | {baseline['n_obs']} |",
        f"| full (+ REER + log wage cost + trade openness) | {full_coef:+.4f} | {b_full.get('se', float('nan')):.4f} | {b_full.get('p', float('nan')):.3f} | {full['n_obs']} |",
        "",
        f"Residual share (|full / baseline|): **{residual_share:.3f}**",
        f"Channels absorb: **{(1 - residual_share)*100:.0f}%** of the DEU-post-2017 log-manuf-share effect.",
        "",
        "## Single-channel attenuation shares",
        "",
        "| Channel | β(deu_post_2017) when added alone | share of total attenuation |",
        "|---|---:|---:|",
    ]
    for ch in chan_names:
        c = chan_attn[ch]
        lines.append(f"| {ch} | {c['deu_post_coef']:+.4f} | "
                     f"{c.get('share_of_total_attenuation', float('nan')):+.2f} |")
    lines += [
        "",
        f"Monocausal flag (any channel > 60% of attenuation): **{monocausal}**.",
        "",
        f"Sample N: {baseline['n_obs']} country-year observations, "
        f"DEU + {', '.join(PEERS)}, {PERIOD[0]}-{PERIOD[1]}.",
        "",
        "## Deviations from pre-registration",
        "",
        "- Eurostat nama_10r_3gva (NACE-C share of TOTAL GVA, current price) supplies the manufacturing-share trajectory.",
        "- Energy-cost channel: NRG_PC_205 not in vintages; substituted via BIS REER (broad basket) and Eurostat nama_10_lp_ulc national-accounts ULC index. The substitution captures cost-competitiveness but NOT the energy-specific Energiewende+gas-shock pathway directly.",
        "- China import-penetration channel and external-demand channel both skipped (TiVA + trade-weighted destination GDP not in vintages).",
        "- Period clipped to 2010-2023; final 2024 numbers will require re-run when data refreshes.",
        "",
        "## Steelman live concerns",
        "",
        "See [hypotheses/steelman/german_manufacturing_va_decline_2017_2024.md]"
        "(../../../hypotheses/steelman/german_manufacturing_va_decline_2017_2024.md) "
        "for the secular-deindustrialisation framing, the COVID-recovery composition "
        "argument, and the auto-sector-restructuring critique.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  DEU manuf share 2017→{last_year}: {share_2017*100:.2f}% → {share_last*100:.2f}% ({pp_change:+.2f}pp)")
    print(f"  TWFE β baseline: {base_coef:+.4f}  full: {full_coef:+.4f}")
    print(f"  residual_share: {residual_share:.3f}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
