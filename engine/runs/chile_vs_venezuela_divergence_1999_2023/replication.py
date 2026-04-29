#!/usr/bin/env python3
"""Replication — Chile vs Venezuela divergence, 1999-2023 (descriptive)."""
from __future__ import annotations

import hashlib, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")
REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "chile_vs_venezuela_divergence_1999_2023"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

TREATED = "CHL"
COMPARATOR = "VEN"
PERIOD = (1999, 2023)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub, series):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{series}")
    return files[-1]


def load_wdi(path, name):
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "value"]].copy()
    out["year"] = out["year"].astype(int)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.rename(columns={"value": name, "country_iso3": "country"})


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Primary: WDI NY.GDP.PCAP.PP.KD (PPP). VEN missing post-2011 — fall back to WDI NY.GDP.PCAP.KD (constant USD)
    # which has VEN coverage through 2024. Both treated identically; this changes the units (USD vs PPP) but
    # the relative cumulative-growth gap interpretation is preserved (within-country deflators are identical).
    ppp_path = latest("world_bank_wdi", "NY.GDP.PCAP.PP.KD")
    usd_path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")

    manifest = {
        "gdp_pc_ppp": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.PP.KD",
                       "vintage_file": str(ppp_path.relative_to(REPO_ROOT)), "sha256": sha256(ppp_path)},
        "gdp_pc_const_usd": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD",
                             "vintage_file": str(usd_path.relative_to(REPO_ROOT)), "sha256": sha256(usd_path)},
    }

    ppp = load_wdi(ppp_path, "gdp_pc_ppp")
    usd = load_wdi(usd_path, "gdp_pc_const_usd")

    def pull(df, country, value_col):
        s = df[df["country"] == country].set_index("year")[value_col].dropna()
        return s

    chl_ppp = pull(ppp, "CHL", "gdp_pc_ppp")
    ven_ppp = pull(ppp, "VEN", "gdp_pc_ppp")
    chl_usd = pull(usd, "CHL", "gdp_pc_const_usd")
    ven_usd = pull(usd, "VEN", "gdp_pc_const_usd")

    # Choose the working series: PPP if both endpoints present, else fall back to constant USD
    def have(series, y):
        return y in series.index and pd.notna(series[y])

    use_ppp = have(chl_ppp, 1999) and have(chl_ppp, 2023) and have(ven_ppp, 1999) and have(ven_ppp, 2023)
    if use_ppp:
        chl, ven = chl_ppp, ven_ppp
        units = "PPP constant 2021 international $"
        series_id = "NY.GDP.PCAP.PP.KD"
    else:
        chl, ven = chl_usd, ven_usd
        units = "constant 2015 USD"
        series_id = "NY.GDP.PCAP.KD"

    # Compute log series and primary statistics
    log_chl = np.log(chl)
    log_ven = np.log(ven)

    def stat(log_s, y):
        return float(log_s[y]) if y in log_s.index and pd.notna(log_s[y]) else None

    chl_1999 = stat(log_chl, 1999)
    chl_2023 = stat(log_chl, 2023)
    ven_1999 = stat(log_ven, 1999)
    ven_2023 = stat(log_ven, 2023)

    # Endpoint log-gap (Chile minus Venezuela)
    log_gap_1999 = chl_1999 - ven_1999 if (chl_1999 is not None and ven_1999 is not None) else None
    log_gap_2023 = chl_2023 - ven_2023 if (chl_2023 is not None and ven_2023 is not None) else None

    # Cumulative log growth 1999 -> 2023
    chl_cum_growth = chl_2023 - chl_1999 if (chl_2023 is not None and chl_1999 is not None) else None
    ven_cum_growth = ven_2023 - ven_1999 if (ven_2023 is not None and ven_1999 is not None) else None
    growth_gap = chl_cum_growth - ven_cum_growth if (chl_cum_growth is not None and ven_cum_growth is not None) else None

    # Annualised rates
    n_years = 2023 - 1999
    chl_ann = chl_cum_growth / n_years if chl_cum_growth is not None else None
    ven_ann = ven_cum_growth / n_years if ven_cum_growth is not None else None

    # COVID-excluded version: 1999 vs 2019
    chl_2019 = stat(log_chl, 2019)
    ven_2019 = stat(log_ven, 2019)
    chl_cum_pre_covid = chl_2019 - chl_1999 if (chl_2019 is not None and chl_1999 is not None) else None
    ven_cum_pre_covid = ven_2019 - ven_1999 if (ven_2019 is not None and ven_1999 is not None) else None
    growth_gap_pre_covid = (chl_cum_pre_covid - ven_cum_pre_covid
                            if (chl_cum_pre_covid is not None and ven_cum_pre_covid is not None) else None)

    # Falsification thresholds
    primary_endpoint_pass = log_gap_2023 is not None and log_gap_2023 >= 1.20
    primary_growth_pass = growth_gap is not None and growth_gap >= 0.60
    informative_pre_window_small = log_gap_1999 is not None and abs(log_gap_1999) < 0.30

    all_primary_pass = primary_endpoint_pass and primary_growth_pass

    if all_primary_pass:
        verdict = (f"SUPPORTED — 2023 log-gap (CHL−VEN) {log_gap_2023:+.2f} (>=1.20). "
                   f"Cumulative growth gap 1999→2023 {growth_gap:+.2f} log-points (>=0.60). "
                   f"Chile annualised {chl_ann*100:+.2f}%/yr; Venezuela {ven_ann*100:+.2f}%/yr.")
    else:
        verdict = (f"REFUTED — 2023 log-gap {log_gap_2023:+.2f} (threshold 1.20), "
                   f"growth gap {growth_gap:+.2f} (threshold 0.60). Primary thresholds not met.")

    diagnostics = {
        "verdict": verdict,
        "all_primary_pass": all_primary_pass,
        "series_used": series_id, "units": units,
        "chl_log_1999": chl_1999, "chl_log_2023": chl_2023, "chl_log_2019": chl_2019,
        "ven_log_1999": ven_1999, "ven_log_2023": ven_2023, "ven_log_2019": ven_2019,
        "log_gap_1999": log_gap_1999, "log_gap_2023": log_gap_2023,
        "chl_cumulative_log_growth_1999_2023": chl_cum_growth,
        "ven_cumulative_log_growth_1999_2023": ven_cum_growth,
        "growth_gap_log_points": growth_gap,
        "chl_annualised_rate": chl_ann, "ven_annualised_rate": ven_ann,
        "chl_cumulative_pre_covid_1999_2019": chl_cum_pre_covid,
        "ven_cumulative_pre_covid_1999_2019": ven_cum_pre_covid,
        "growth_gap_pre_covid_1999_2019": growth_gap_pre_covid,
        "falsification_components": {
            "endpoint_log_gap_ge_1.20": primary_endpoint_pass,
            "cumulative_growth_gap_ge_0.60": primary_growth_pass,
            "informative_pre_window_gap_lt_0.30": informative_pre_window_small,
        },
    }

    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
        "notes": ("WDI NY.GDP.PCAP.PP.KD has no values for VEN post-2011, so the run falls back to "
                  "NY.GDP.PCAP.KD (constant 2015 USD). Within-country log-growth and the bilateral gap "
                  "are interpretable; only the units shift."),
    }, sort_keys=False))

    # Result card
    pct_chl = (np.exp(chl_cum_growth) - 1) * 100 if chl_cum_growth is not None else None
    pct_ven = (np.exp(ven_cum_growth) - 1) * 100 if ven_cum_growth is not None else None
    rel_gap = (np.exp(growth_gap) - 1) * 100 if growth_gap is not None else None

    lines = [
        "# Result card — Chile vs Venezuela divergence, 1999–2023",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Series used: WDI `{series_id}` ({units}).",
        f"- Chile log GDP-pc 1999 → 2023: {chl_1999:.3f} → {chl_2023:.3f}; cumulative {chl_cum_growth:+.3f} log-points (~{pct_chl:+.0f}%); annualised {chl_ann*100:+.2f}%/yr.",
        f"- Venezuela log GDP-pc 1999 → 2023: {ven_1999:.3f} → {ven_2023:.3f}; cumulative {ven_cum_growth:+.3f} log-points (~{pct_ven:+.0f}%); annualised {ven_ann*100:+.2f}%/yr.",
        f"- Bilateral log-gap (CHL − VEN): 1999 = {log_gap_1999:+.3f}; 2023 = {log_gap_2023:+.3f}.",
        f"- Cumulative growth gap 1999→2023: {growth_gap:+.3f} log-points (~{rel_gap:+.0f}% relative).",
        f"- Pre-COVID robustness (1999→2019): growth gap {growth_gap_pre_covid:+.3f} log-points." if growth_gap_pre_covid is not None else "",
        "",
        "## Threshold applied",
        "",
        "- PRIMARY (dispositive): `log_gdp_pc(CHL, 2023) − log_gdp_pc(VEN, 2023) >= 1.20` AND "
        "`cumulative_log_growth(CHL, 1999-2023) − cumulative_log_growth(VEN, 1999-2023) >= 0.60`.",
        "- INFORMATIVE: `|log_gdp_pc(CHL, 1999) − log_gdp_pc(VEN, 1999)| < 0.30` "
        f"(realised: |{log_gap_1999:+.3f}|; informative pass: {informative_pre_window_small}).",
        "",
        "| Component | Threshold | Realised | Pass |",
        "|---|---:|---:|:---:|",
        f"| Endpoint log-gap 2023 | >= 1.20 | {log_gap_2023:+.3f} | {'yes' if primary_endpoint_pass else 'no'} |",
        f"| Cumulative growth gap | >= 0.60 | {growth_gap:+.3f} | {'yes' if primary_growth_pass else 'no'} |",
        f"| Pre-window gap (informative) | < 0.30 | {abs(log_gap_1999):.3f} | {'yes' if informative_pre_window_small else 'no'} |",
        "",
        "## Interpretation",
        "",
        "This is a descriptive bilateral comparison; results are pattern matches, not causal identification. "
        "We have not constructed a counterfactual Venezuela or controlled for oil prices, terms-of-trade shocks, "
        "or US sanctions. The pre-registered claim is that the magnitude of the divergence is so large that "
        "policy content is the most plausible single explanation, but rigorous causal attribution would require "
        "a synthetic-control or bilateral DiD design. The Chavismo/Maduro programme overlaps with the 2014 oil "
        "price collapse and post-2017 US sanctions, so the gap reflects a bundle of self-inflicted policy and "
        "external shocks, not a clean policy-only experiment.",
        "",
        "## Sources",
        "",
        f"- World Bank WDI `{series_id}` (vintage {Path(manifest['gdp_pc_ppp' if use_ppp else 'gdp_pc_const_usd']['vintage_file']).name}).",
        "- Note: `NY.GDP.PCAP.PP.KD` returns NaN for VEN from 2011 onward in the local WDI vintage; the "
        "fallback to constant-USD preserves within-country log-growth comparability.",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/chile_vs_venezuela_divergence_1999_2023.md`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(l for l in lines if l is not None) + "\n")

    print(f"verdict: {verdict}")
    print(f"  series: {series_id} ({units})")
    print(f"  CHL cum log-growth 1999-2023: {chl_cum_growth:+.3f} ({chl_ann*100:+.2f}%/yr)")
    print(f"  VEN cum log-growth 1999-2023: {ven_cum_growth:+.3f} ({ven_ann*100:+.2f}%/yr)")
    print(f"  bilateral gap 2023: {log_gap_2023:+.3f}; growth gap: {growth_gap:+.3f}")


if __name__ == "__main__":
    sys.exit(main())
