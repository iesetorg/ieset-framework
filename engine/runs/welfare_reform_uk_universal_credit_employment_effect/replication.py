#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
HID = "welfare_reform_uk_universal_credit_employment_effect"
OUT = ROOT / "engine" / "runs" / HID
SPEC = ROOT / "hypotheses" / "welfare_architecture" / f"{HID}.yaml"


def latest() -> Path:
    files = sorted((ROOT / "data" / "vintages" / "oecd").glob("DSD_LFS_DF_LFS_INDIC@*.parquet"))
    if not files:
        raise FileNotFoundError("missing oecd:DSD_LFS@DF_LFS_INDIC")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC.read_text())
    path = latest()
    raw = pd.read_parquet(path)
    emp = raw[
        raw["REF_AREA"].eq("GBR")
        & raw["MEASURE"].eq("EMP_RATIO")
        & raw["SEX"].eq("_T")
        & raw["AGE"].eq("Y15T64")
    ][["period", "value"]].dropna()
    emp = emp.copy()
    emp["year"] = emp["period"].astype(int)
    emp["employment_rate"] = emp["value"].astype(float)
    yearly = (
        emp[["year", "employment_rate"]]
        .groupby("year", as_index=False)
        .mean(numeric_only=True)
        .sort_values("year")
    )
    window = yearly[yearly["year"].between(2010, 2019)].copy()
    pre = window[window["year"].between(2010, 2012)]
    post = window[window["year"].between(2013, 2019)]
    if len(pre) < 3 or 2015 not in set(post["year"]):
        est = {"error": f"insufficient national benchmark coverage (pre={len(pre)}, post={len(post)})"}
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", est["error"]
    else:
        x_pre = pre["year"].to_numpy(dtype=float)
        y_pre = pre["employment_rate"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(x_pre, y_pre, 1)
        x_post = post["year"].to_numpy(dtype=float)
        actual = post["employment_rate"].to_numpy(dtype=float)
        counterfactual = slope * x_post + intercept
        gaps = actual - counterfactual
        gap_by_year = {
            int(year): float(gap)
            for year, gap in zip(post["year"].astype(int), gaps)
        }
        est = {
            "shape": "national_oecd_lfs_interrupted_trend_benchmark",
            "country": "GBR",
            "event_year": 2013,
            "pretrend_years": [2010, 2012],
            "post_years": [int(post["year"].min()), int(post["year"].max())],
            "pretrend_slope_pp_per_year": float(slope),
            "post_gaps": [
                {
                    "year": int(year),
                    "actual_employment_rate": float(a),
                    "counterfactual_pretrend": float(cf),
                    "gap_pp": float(g),
                }
                for year, a, cf, g in zip(post["year"], actual, counterfactual, gaps)
            ],
            "gap_24mo_2015_pp": gap_by_year[2015],
            "gap_end_rollout_2017_pp": gap_by_year.get(2017),
            "mean_2013_2019_gap_pp": float(np.mean(gaps)),
            "method_note": (
                "This is a national annual employment-rate benchmark. The registered LAD-level "
                "rollout timing and legacy-benefit-claimant employment panel are not local."
            ),
        }
        if est["gap_24mo_2015_pp"] >= 3.0:
            verdict = "SUPPORTED"
            reason = f"national 24-month employment gap clears +3pp ({est['gap_24mo_2015_pp']:.2f}pp)"
        elif est["gap_24mo_2015_pp"] <= 0.0:
            verdict = "REFUTED"
            reason = f"national 24-month employment gap is not positive ({est['gap_24mo_2015_pp']:.2f}pp)"
        else:
            verdict = "PARTIAL"
            reason = (
                f"national 24-month employment gap is positive but below +3pp "
                f"({est['gap_24mo_2015_pp']:.2f}pp)"
            )

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "national_event_benchmark_oecd_lfs",
        "estimate": est,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "proxy_outcome",
                    "name": "national_working_age_employment_rate",
                    "source": "oecd:DSD_LFS@DF_LFS_INDIC",
                    "filter": "REF_AREA=GBR, MEASURE=EMP_RATIO, SEX=_T, AGE=Y15T64",
                    "vintage_file": str(path.relative_to(ROOT)),
                    "sha256": sha256(path),
                }
            ],
            "variables_missing": [
                "DWP local-authority Universal Credit full-service rollout dates",
                "legacy-benefit-claimant employment outcomes",
                "local-authority unemployment controls",
            ],
        },
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (OUT / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        "sources:\n"
        f"  oecd_lfs_employment_rate: {path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## National Employment Benchmark\n"
        f"- 2015 gap vs 2010-2012 pretrend: **{est.get('gap_24mo_2015_pp', float('nan')):.2f} pp**.\n"
        f"- 2017 gap vs pretrend: **{est.get('gap_end_rollout_2017_pp', float('nan')):.2f} pp**.\n"
        f"- Mean 2013-2019 gap: **{est.get('mean_2013_2019_gap_pp', float('nan')):.2f} pp**.\n\n"
        "This national benchmark is directional only; the registered claimant-by-local-authority design remains unwired.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0 if verdict != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
