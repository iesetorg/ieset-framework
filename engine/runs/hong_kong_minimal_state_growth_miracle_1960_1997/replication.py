#!/usr/bin/env python3
"""Replication — Hong Kong minimal-state growth miracle, 1960-1997 (descriptive)."""
from __future__ import annotations

import hashlib, json, sys, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml

warnings.filterwarnings("ignore")
REPO_ROOT = Path(__file__).resolve().parents[3]
RUN_ID = "hong_kong_minimal_state_growth_miracle_1960_1997"
OUT_DIR = REPO_ROOT / "engine" / "runs" / RUN_ID

COUNTRY = "HKG"
COMPARATORS = ["USA", "GBR", "SGP", "KOR", "JPN", "TWN"]
PERIOD = (1960, 1997)


def sha256(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(65536), b""):
            h.update(ch)
    return h.hexdigest()


def latest(pub, prefix):
    d = REPO_ROOT / "data" / "vintages" / pub
    files = sorted(d.glob(f"{prefix}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"{pub}:{prefix}")
    return files[-1]


def load_maddison(path):
    t = pq.read_table(path).to_pandas()
    t = t[(t["country_iso3"].notna()) & (t["country_iso3"].str.len() == 3)]
    out = t[["country_iso3", "year", "gdppc"]].copy()
    out["year"] = out["year"].astype(int)
    out["gdppc"] = pd.to_numeric(out["gdppc"], errors="coerce")
    return out.rename(columns={"country_iso3": "country"})


def annualised(log_series, y0, y1):
    s = log_series[(log_series.index >= y0) & (log_series.index <= y1)].sort_index()
    if len(s) < 2:
        return None
    diffs = s.diff().dropna()
    return float(diffs.mean())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    mpath = latest("maddison", "mpd2020")
    manifest = {
        "gdp_pc_ppp_2011": {"publisher": "maddison", "series": "mpd2020",
                            "vintage_file": str(mpath.relative_to(REPO_ROOT)), "sha256": sha256(mpath)},
    }

    df = load_maddison(mpath)
    keep = [COUNTRY] + COMPARATORS
    df = df[df["country"].isin(keep)]
    df = df[(df["year"] >= PERIOD[0]) & (df["year"] <= PERIOD[1])].copy()
    df = df[df["gdppc"].notna()]
    df["log"] = np.log(df["gdppc"])

    by_country = {}
    for c in keep:
        s = df[df["country"] == c].set_index("year")["log"].sort_index()
        if 1960 in s.index and 1997 in s.index:
            cum = float(s[1997] - s[1960])
            ann = float(annualised(s, 1960, 1997))
            by_country[c] = {
                "log_1960": float(s[1960]),
                "log_1997": float(s[1997]),
                "gdppc_1960": float(np.exp(s[1960])),
                "gdppc_1997": float(np.exp(s[1997])),
                "cumulative_log_growth": cum,
                "annualised_log_growth": ann,
                "annualised_pct": float((np.exp(ann) - 1) * 100),
            }

    hkg = by_country.get(COUNTRY)
    usa = by_country.get("USA")

    # Falsification thresholds (per YAML):
    #   1) HKG GDP-pc must reach >= 80% of USA level by 1997
    #   2) Annual growth must average >= 5% real for 1960-1997
    hkg_share_1997 = (hkg["gdppc_1997"] / usa["gdppc_1997"]) if (hkg and usa) else None
    primary_share_pass = hkg_share_1997 is not None and hkg_share_1997 >= 0.80
    primary_growth_pass = hkg is not None and hkg["annualised_pct"] >= 5.0

    # Donor-pool comparison: HKG vs comparators (cumulative log-growth)
    ranked = sorted(by_country.items(), key=lambda kv: -kv[1]["cumulative_log_growth"])
    comp_means = {
        "comparator_mean_cum_growth": float(np.mean([v["cumulative_log_growth"] for c, v in by_country.items() if c in COMPARATORS])),
        "comparator_mean_ann_pct": float(np.mean([v["annualised_pct"] for c, v in by_country.items() if c in COMPARATORS])),
    }

    if primary_share_pass and primary_growth_pass:
        verdict = (f"SUPPORTED — HKG/USA per-capita ratio 1997 = {hkg_share_1997:.2f} (>=0.80); "
                   f"HKG annualised growth 1960-1997 = {hkg['annualised_pct']:+.2f}%/yr (>=5.0).")
    elif primary_growth_pass and not primary_share_pass:
        verdict = (f"weakened — HKG annualised growth {hkg['annualised_pct']:+.2f}%/yr meets 5.0 threshold "
                   f"but HKG/USA ratio 1997 = {hkg_share_1997:.2f} below 0.80.")
    elif primary_share_pass and not primary_growth_pass:
        verdict = (f"weakened — HKG/USA ratio {hkg_share_1997:.2f} meets 0.80 threshold but annualised "
                   f"growth {hkg['annualised_pct']:+.2f}%/yr below 5.0.")
    else:
        verdict = (f"REFUTED — HKG/USA ratio {hkg_share_1997:.2f} (<0.80) and/or annualised growth "
                   f"{hkg['annualised_pct']:+.2f}%/yr (<5.0).")

    diagnostics = {
        "verdict": verdict,
        "primary_share_pass": primary_share_pass,
        "primary_growth_pass": primary_growth_pass,
        "hkg_gdppc_1960": hkg["gdppc_1960"] if hkg else None,
        "hkg_gdppc_1997": hkg["gdppc_1997"] if hkg else None,
        "usa_gdppc_1997": usa["gdppc_1997"] if usa else None,
        "hkg_to_usa_ratio_1997": hkg_share_1997,
        "hkg_cumulative_log_growth": hkg["cumulative_log_growth"] if hkg else None,
        "hkg_annualised_log_growth": hkg["annualised_log_growth"] if hkg else None,
        "hkg_annualised_pct": hkg["annualised_pct"] if hkg else None,
        "comparator_means": comp_means,
        "ranked": [{"country": c, **v} for c, v in ranked],
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2, default=lambda o: None) + "\n")

    (OUT_DIR / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": RUN_ID,
        "run_utc": pd.Timestamp.now(tz="UTC").isoformat(),
        "estimator": "descriptive",
        "vintages": manifest,
        "notes": ("Maddison MPD2020 GDP per capita (2011 PPP$). The YAML mentions a synthetic-control "
                  "design but the descriptive estimator only computes pre-registered statistics: HKG "
                  "trajectory, HKG/USA convergence ratio, and comparator means."),
    }, sort_keys=False))

    rows = []
    for c, v in ranked:
        rows.append(f"| {c} | {v['gdppc_1960']:>7,.0f} | {v['gdppc_1997']:>7,.0f} | "
                    f"{v['cumulative_log_growth']:+.3f} | {v['annualised_pct']:+.2f}% |")

    lines = [
        "# Result card — Hong Kong minimal-state growth miracle, 1960–1997",
        "",
        f"**Verdict:** {verdict}",
        "",
        "## Headline numbers",
        "",
        f"- Series: Maddison MPD2020 `gdppc` (2011 PPP $).",
        f"- HKG GDP-pc 1960 → 1997: ${hkg['gdppc_1960']:,.0f} → ${hkg['gdppc_1997']:,.0f} "
        f"(cumulative {hkg['cumulative_log_growth']:+.3f} log-points; annualised {hkg['annualised_pct']:+.2f}%/yr).",
        f"- USA GDP-pc 1997: ${usa['gdppc_1997']:,.0f}; HKG/USA ratio 1997 = {hkg_share_1997:.3f}.",
        f"- Comparator pool ({', '.join(COMPARATORS)}) mean cumulative log-growth: "
        f"{comp_means['comparator_mean_cum_growth']:+.3f}; mean annualised: {comp_means['comparator_mean_ann_pct']:+.2f}%/yr.",
        "",
        "## Per-country trajectory 1960 → 1997 (Maddison 2011 PPP $)",
        "",
        "| Country | GDP-pc 1960 | GDP-pc 1997 | cum log-growth | annualised |",
        "|---|---:|---:|---:|---:|",
        *rows,
        "",
        "## Threshold applied",
        "",
        "- PRIMARY: `HKG GDP-pc(1997) / USA GDP-pc(1997) >= 0.80` AND `annualised real growth(HKG, 1960-1997) >= 5.0%/yr`.",
        "",
        "| Component | Threshold | Realised | Pass |",
        "|---|---:|---:|:---:|",
        f"| HKG/USA ratio 1997 | >= 0.80 | {hkg_share_1997:.3f} | {'yes' if primary_share_pass else 'no'} |",
        f"| HKG annualised growth | >= 5.00%/yr | {hkg['annualised_pct']:+.3f}% | {'yes' if primary_growth_pass else 'no'} |",
        "",
        "## Interpretation",
        "",
        "This is a descriptive comparison; results are pattern matches, not causal identification. The "
        "Cowperthwaite-era policy regime is not separable in this estimator from (a) entrepôt geography "
        "at the mouth of the Pearl River Delta, (b) post-war waves of skilled mainland migration, "
        "(c) the regional East Asian manufacturing boom, or (d) British rule-of-law inheritance. "
        "Singapore (SGP) achieved comparable convergence with much heavier state intervention "
        "(HDB, CPF, GLCs), which is why a synthetic-control design is the right next step; the "
        "descriptive run only documents that the trajectory exists.",
        "",
        "## Sources",
        "",
        f"- Maddison Project Database 2020 (vintage {Path(manifest['gdp_pc_ppp_2011']['vintage_file']).name}).",
        "",
        "## Steelman live concerns",
        "",
        "See `hypotheses/steelman/hong_kong_minimal_state_growth_miracle_1960_1997.md`.",
    ]
    (OUT_DIR / "result_card.md").write_text("\n".join(lines) + "\n")

    print(f"verdict: {verdict}")
    print(f"  HKG cum log-growth 1960-1997: {hkg['cumulative_log_growth']:+.3f}")
    print(f"  HKG annualised: {hkg['annualised_pct']:+.3f}%/yr (threshold >=5.00)")
    print(f"  HKG/USA ratio 1997: {hkg_share_1997:.3f} (threshold >=0.80)")


if __name__ == "__main__":
    sys.exit(main())
