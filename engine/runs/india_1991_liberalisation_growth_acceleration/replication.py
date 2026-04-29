#!/usr/bin/env python3
"""Replication — India 1991 liberalisation growth acceleration (descriptive)."""
from __future__ import annotations

import hashlib, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")
REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "india_1991_liberalisation_growth_acceleration"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

COUNTRY = "IND"
PRE_WINDOW = (1965, 1990)
POST_WINDOW = (1992, 2019)
PRE_TRIM_WINDOW = (1975, 1990)


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


def annualised(log_series, y0, y1):
    s = log_series[(log_series.index >= y0) & (log_series.index <= y1)].sort_index()
    if len(s) < 2:
        return None
    diffs = s.diff().dropna()
    return float(diffs.mean())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = latest("world_bank_wdi", "NY.GDP.PCAP.KD")
    manifest = {
        "gdp_pc_const_usd": {"publisher": "world_bank_wdi", "series": "NY.GDP.PCAP.KD",
                             "vintage_file": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path)},
    }

    df = load_wdi(path, "gdp_pc_const_usd")
    df = df[df["country"] == COUNTRY].sort_values("year")
    df = df[df["gdp_pc_const_usd"].notna()].copy()
    df["log"] = np.log(df["gdp_pc_const_usd"])
    log = df.set_index("year")["log"]

    pre_ann = annualised(log, *PRE_WINDOW)
    post_ann = annualised(log, *POST_WINDOW)
    pre_trim_ann = annualised(log, *PRE_TRIM_WINDOW)
    accel = post_ann - pre_ann if (pre_ann is not None and post_ann is not None) else None
    accel_trim = post_ann - pre_trim_ann if (pre_trim_ann is not None and post_ann is not None) else None

    pre_cum = (log[PRE_WINDOW[1]] - log[PRE_WINDOW[0]]) if (PRE_WINDOW[1] in log.index and PRE_WINDOW[0] in log.index) else None
    post_cum = (log[POST_WINDOW[1]] - log[POST_WINDOW[0]]) if (POST_WINDOW[1] in log.index and POST_WINDOW[0] in log.index) else None

    primary_pass = accel is not None and accel >= 0.02
    informative_pass = accel_trim is not None and accel_trim >= accel

    if primary_pass:
        verdict = (f"SUPPORTED — post-1991 annualised log-growth {post_ann*100:+.2f}%/yr vs "
                   f"pre-1991 {pre_ann*100:+.2f}%/yr; acceleration {accel*100:+.2f}pp/yr "
                   f"(threshold +2.00pp/yr).")
    else:
        verdict = (f"REFUTED — acceleration {accel*100:+.2f}pp/yr below 2.00pp/yr threshold.")

    diagnostics = {
        "verdict": verdict, "primary_pass": primary_pass, "informative_pass_robustness": informative_pass,
        "pre_window_years": list(PRE_WINDOW),
        "post_window_years": list(POST_WINDOW),
        "pre_trim_window_years": list(PRE_TRIM_WINDOW),
        "pre_annualised_log_growth": pre_ann,
        "post_annualised_log_growth": post_ann,
        "pre_trim_annualised_log_growth": pre_trim_ann,
        "acceleration_log_points_per_year": accel,
        "acceleration_trim_robustness": accel_trim,
        "pre_cumulative_log_growth": pre_cum,
        "post_cumulative_log_growth": post_cum,
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
    }, sort_keys=False))

    pct_pre_cum = (np.exp(pre_cum) - 1) * 100 if pre_cum is not None else None
    pct_post_cum = (np.exp(post_cum) - 1) * 100 if post_cum is not None else None

    lines = [
        "# Result card — India 1991 liberalisation growth acceleration",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Series: WDI `NY.GDP.PCAP.KD` (constant 2015 USD).",
        f"- Pre-reform window 1965-1990 annualised log-growth: {pre_ann*100:+.3f}%/yr "
        f"(cumulative {pre_cum:+.3f} log-points, ~{pct_pre_cum:+.0f}%).",
        f"- Post-reform window 1992-2019 annualised log-growth: {post_ann*100:+.3f}%/yr "
        f"(cumulative {post_cum:+.3f} log-points, ~{pct_post_cum:+.0f}%).",
        f"- **Acceleration: {accel*100:+.3f}pp/yr** (post − pre).",
        f"- Trimmed-pre robustness (1975-1990 vs 1992-2019): {accel_trim*100:+.3f}pp/yr.",
        "",
        "## Threshold applied",
        "",
        "- PRIMARY: `annualised_log_growth(1992-2019) − annualised_log_growth(1965-1990) >= 0.02` (2pp/yr).",
        "- INFORMATIVE: trimmed-pre window (1975-1990) yields a similar or larger acceleration.",
        "",
        "| Component | Threshold | Realised | Pass |",
        "|---|---:|---:|:---:|",
        f"| Annualised acceleration | >= +2.00pp/yr | {accel*100:+.3f}pp/yr | {'yes' if primary_pass else 'no'} |",
        f"| Trimmed-pre robustness | >= primary | {accel_trim*100:+.3f}pp/yr | {'yes' if informative_pass else 'no'} |",
        "",
        "## Interpretation",
        "",
        "This is a within-country structural-break descriptive comparison; results are a pattern match, not "
        "causal identification. The 1991 BoP-crisis liberalisation package is bundled with subsequent "
        "reforms (1990s telecoms, 2000s services-export boom) and global tailwinds (China-driven commodity "
        "supercycle, IT-services offshoring). The descriptive estimator documents the break; it does not "
        "isolate the marginal contribution of 1991-specific instruments.",
        "",
        "## Sources",
        "",
        f"- World Bank WDI `NY.GDP.PCAP.KD` (vintage {Path(manifest['gdp_pc_const_usd']['vintage_file']).name}).",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/india_1991_liberalisation_growth_acceleration.md`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  pre-ann: {pre_ann*100:+.3f}%/yr (1965-1990)")
    print(f"  post-ann: {post_ann*100:+.3f}%/yr (1992-2019)")
    print(f"  acceleration: {accel*100:+.3f}pp/yr (threshold >= 2.00)")
    print(f"  trim robustness: {accel_trim*100:+.3f}pp/yr")


if __name__ == "__main__":
    sys.exit(main())
