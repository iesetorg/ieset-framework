#!/usr/bin/env python3
"""Replication — Canadian real disposable income post-2015.

Spec:     hypotheses/labour/canada_real_disposable_income_post_2015.yaml
Steelman: hypotheses/steelman/canada_real_disposable_income_post_2015.md

Per the YAML's data-gate clause: OECD Household Dashboard URN is unverified
and the OECD household disposable income series is not present in our
vintages at run time. The YAML pre-registers that "Until the primary series
is available, runs will use GNI-per-capita proxy only and explicitly label
findings as proxy-based." WDI NY.GNP.PCAP.PP.KD is also not present in
vintages, so we substitute the closest available proxy: WDI GDP per capita
PPP (NY.GDP.PCAP.PP.KD), which is the upper bound of household income
(does not net taxes/transfers/cross-border income flows).

This run is therefore labelled DOUBLE-PROXY: GDP-pc-PPP standing in for
GNI-pc-PPP standing in for OECD household disposable income. The two-spec
rule cannot be evaluated without OECD household disposable income — both
"specs" collapse to one outcome family. Result is recorded as proxy-based
and tentative per the falsification rule.
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
OUT_DIR = REPO_ROOT / "engine" / "runs" / "canada_real_disposable_income_post_2015"

TREATED = "CAN"
DONORS = ["USA", "AUS", "NZL", "GBR", "NOR", "CHE"]
ALL = [TREATED] + DONORS
PERIOD = (2000, 2023)


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


def load_long(path, name):
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def assemble():
    paths = {
        "gdp_pc_ppp":     ("world_bank_wdi", "NY.GDP.PCAP.PP.KD"),
        "gdp_pc_kd":      ("world_bank_wdi", "NY.GDP.PCAP.KD"),
        "population":     ("world_bank_wdi", "SP.POP.TOTL"),
        "trade_openness": ("world_bank_wdi", "NE.TRD.GNFS.ZS"),
        "cpi":            ("world_bank_wdi", "FP.CPI.TOTL.ZG"),
    }
    manifest = {}
    frames = []
    for v, (pub, series) in paths.items():
        p = latest(pub, series)
        manifest[v] = {"publisher": pub, "series": series,
                       "vintage_file": str(p.relative_to(REPO_ROOT)),
                       "sha256": sha256(p)}
        frames.append(load_long(p, v))
    panel = frames[0]
    for f in frames[1:]:
        panel = panel.merge(f, on=["country", "year"], how="outer")
    panel = panel[panel["country"].isin(ALL)]
    panel = panel[(panel["year"] >= PERIOD[0]) & (panel["year"] <= PERIOD[1])]
    panel = panel.sort_values(["country", "year"]).reset_index(drop=True)
    panel["log_gdp_pc_ppp"] = np.log(panel["gdp_pc_ppp"])
    panel["log_gdp_pc_kd"]  = np.log(panel["gdp_pc_kd"])
    panel["log_population"] = np.log(panel["population"])
    panel["canada_post_2015"] = ((panel["country"] == TREATED) & (panel["year"] >= 2015)).astype(int)
    return panel, manifest


def fit(df, outcome, treatments, controls=None):
    controls = controls or []
    cols = ["country", "year", outcome] + treatments + controls
    d = df[cols].dropna().copy().set_index(["country", "year"])
    for c in DONORS[1:]:
        d[f"donor_{c}"] = (d.index.get_level_values("country") == c).astype(float)
    donor_cols = [f"donor_{c}" for c in DONORS[1:]]
    X = d[donor_cols + treatments + controls]
    y = d[outcome]
    res = PanelOLS(y, X, entity_effects=False, time_effects=True,
                   check_rank=False, drop_absorbed=True).fit(
        cov_type="clustered", cluster_entity=True
    )
    out = {"n_obs": int(res.nobs), "r2_within": float(res.rsquared_within), "coefs": {}}
    for t in treatments:
        if t in res.params.index:
            out["coefs"][t] = {
                "estimate": float(res.params[t]),
                "se": float(res.std_errors[t]),
                "ci_lo": float(res.conf_int().loc[t, "lower"]),
                "ci_hi": float(res.conf_int().loc[t, "upper"]),
                "p": float(res.pvalues[t]),
                "t": float(res.tstats[t]),
            }
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel, manifest = assemble()

    # Two pseudo-specs (both proxies; not the true two-spec rule)
    proxy_ppp = fit(panel, "log_gdp_pc_ppp", ["canada_post_2015"],
                    ["log_population", "trade_openness"])
    proxy_kd = fit(panel, "log_gdp_pc_kd", ["canada_post_2015"],
                   ["log_population", "trade_openness"])

    b_ppp = proxy_ppp["coefs"].get("canada_post_2015", {})
    b_kd = proxy_kd["coefs"].get("canada_post_2015", {})

    sign_ppp = b_ppp.get("estimate", 0) < 0
    sig_ppp = b_ppp.get("p", 1.0) < 0.10
    sign_kd = b_kd.get("estimate", 0) < 0
    sig_kd = b_kd.get("p", 1.0) < 0.10

    # Per YAML: supported requires both specs; tentative if one. Both are
    # proxies here, so cap at WEAKENED-tentative even if both are sig.
    if sign_ppp and sig_ppp and sign_kd and sig_kd:
        verdict = (
            f"WEAKENED — both proxy specs (GDP-pc PPP β={b_ppp.get('estimate', 0):+.3f} "
            f"p={b_ppp.get('p', 1):.3f}; GDP-pc constant LCU β={b_kd.get('estimate', 0):+.3f} "
            f"p={b_kd.get('p', 1):.3f}) show negative Canadian post-2015 trajectory, but "
            f"the YAML's true two-spec rule requires OECD household disposable income + "
            f"WDI GNI-per-capita PPP, neither of which is present in the local vintages. "
            f"Both available proxies measure pre-tax-and-transfer aggregate output rather "
            f"than household disposable income. Verdict capped at WEAKENED pending v1.1 "
            f"OECD Household Dashboard fetcher."
        )
    elif sign_ppp and sig_ppp:
        verdict = (
            f"PARTIAL — primary proxy (GDP-pc PPP) negative and significant "
            f"(β={b_ppp.get('estimate', 0):+.3f}, p={b_ppp.get('p', 1):.3f}); "
            f"secondary proxy not significant. True two-spec rule cannot be evaluated."
        )
    else:
        verdict = (
            f"REFUTED-on-proxy — proxies do not show negative post-2015 trajectory. "
            f"Note: proxies measure aggregate output, not household disposable income."
        )

    rows = []
    for label, res in [("proxy_ppp", proxy_ppp), ("proxy_kd", proxy_kd)]:
        for t, c in res.get("coefs", {}).items():
            rows.append({"spec": label, "term": t, **c, "n_obs": res["n_obs"]})
    pd.DataFrame(rows).to_parquet(OUT_DIR / "coefficients.parquet", index=False)

    (OUT_DIR / "diagnostics.json").write_text(json.dumps({
        "verdict": verdict,
        "data_gate_status": "OECD household disposable income unavailable; WDI GNI-pc PPP also unavailable; falling back to GDP-pc PPP + GDP-pc constant LCU",
        "proxy_ppp_twfe": proxy_ppp,
        "proxy_kd_twfe": proxy_kd,
    }, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": "canada_real_disposable_income_post_2015",
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "data_gate": "v1.1 OECD Household Dashboard fetcher pending; current run uses double-proxy",
        "vintages": manifest,
    }, sort_keys=False))

    lines = [
        "# Result card — Canada real disposable income post-2015 (PROXY)",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Data gate",
        "",
        "The YAML's primary outcome is OECD household net disposable income per capita.",
        "That dataflow is not present in the local vintages and the URN was flagged in",
        "the YAML as v1.1 fetcher requirement. The YAML's secondary proxy WDI GNI per",
        "capita PPP (NY.GNP.PCAP.PP.KD) is also not present in vintages. This run",
        "substitutes the closest available proxy — WDI GDP per capita PPP — and a second",
        "proxy WDI GDP per capita constant LCU. Both are aggregate-output proxies that",
        "do NOT net taxes, transfers, or cross-border income flows. Findings are labelled",
        "PROXY and capped at WEAKENED until OECD Household Dashboard ships.",
        "",
        "## Proxy spec 1 — log GDP per capita PPP (constant intl $)",
        "",
        "| Term | Estimate | SE | 95% CI | p | t |",
        "|---|---:|---:|:---:|---:|---:|",
        f"| canada_post_2015 | {b_ppp.get('estimate', float('nan')):+.4f} | {b_ppp.get('se', float('nan')):.4f} | "
        f"[{b_ppp.get('ci_lo', float('nan')):+.3f}, {b_ppp.get('ci_hi', float('nan')):+.3f}] | "
        f"{b_ppp.get('p', float('nan')):.3f} | {b_ppp.get('t', float('nan')):+.2f} |",
        "",
        f"n = {proxy_ppp['n_obs']} country-years.",
        "",
        "## Proxy spec 2 — log GDP per capita (constant LCU)",
        "",
        "| Term | Estimate | SE | 95% CI | p | t |",
        "|---|---:|---:|:---:|---:|---:|",
        f"| canada_post_2015 | {b_kd.get('estimate', float('nan')):+.4f} | {b_kd.get('se', float('nan')):.4f} | "
        f"[{b_kd.get('ci_lo', float('nan')):+.3f}, {b_kd.get('ci_hi', float('nan')):+.3f}] | "
        f"{b_kd.get('p', float('nan')):.3f} | {b_kd.get('t', float('nan')):+.2f} |",
        "",
        f"n = {proxy_kd['n_obs']} country-years.",
        "",
        "## Caveat per YAML pre-registration",
        "",
        "Aggregate-output proxies cannot speak to the transfer-share decomposition channel",
        "(CCB enhancement, CPP enhancement, COVID transfers, $10/day childcare) which the",
        "YAML flags as the most important interpretive guard. If those transfers fully",
        "offset pre-tax wage weakness in household disposable income, the household-stagnation",
        "framing would be inaccurate even if aggregate-output stagnation is real. This",
        "decomposition cannot be performed at v1; flagged for v1.1 OECD Household Dashboard run.",
        "",
        "## Provenance",
        "",
        "Reproduces from vintages in `manifest.yaml`. See `replication.py`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict[:120]}...")
    print(f"  proxy_ppp β={b_ppp.get('estimate', float('nan')):+.4f} p={b_ppp.get('p', float('nan')):.3f}")
    print(f"  proxy_kd  β={b_kd.get('estimate', float('nan')):+.4f} p={b_kd.get('p', float('nan')):.3f}")


if __name__ == "__main__":
    sys.exit(main())
