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
HID = "labour_reform_schroeder_agenda_2010_long_run_inequality"
OUT = ROOT / "engine" / "runs" / HID
SPEC = ROOT / "hypotheses" / "labour" / f"{HID}.yaml"
TREATED = "DEU"
DONORS = ["FRA", "NLD", "BEL", "AUT", "ITA", "FIN", "IRL"]
PRE_YEARS = [1995, 2000]
POST_YEARS = [2015, 2016, 2017, 2018]


def latest() -> Path:
    files = sorted((ROOT / "data" / "vintages" / "oecd").glob("DSD_IDD@*.parquet"))
    if not files:
        raise FileNotFoundError("missing oecd:DSD_IDD")
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def nnls_weights(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    try:
        from scipy.optimize import nnls

        raw, _ = nnls(x, y)
    except Exception:
        raw = np.ones(x.shape[1])
    return raw / raw.sum() if raw.sum() > 0 else np.ones(x.shape[1]) / x.shape[1]


def load_lower_tail(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    ratio = df[
        df["MEASURE"].eq("D5_1_INC_DISP")
        & df["AGE"].eq("_T")
        & df["POVERTY_LINE"].eq("_Z")
    ][["REF_AREA", "period", "value"]].dropna()
    ratio = ratio.copy()
    ratio["country"] = ratio["REF_AREA"].astype(str)
    ratio["year"] = ratio["period"].astype(int)
    ratio["bottom_to_median_pct"] = 100.0 / ratio["value"].astype(float)
    return (
        ratio[["country", "year", "bottom_to_median_pct"]]
        .groupby(["country", "year"], as_index=False)
        .mean(numeric_only=True)
    )


def fit(panel: pd.DataFrame) -> dict:
    wide = panel[panel["country"].isin([TREATED] + DONORS)].pivot_table(
        index="year", columns="country", values="bottom_to_median_pct", aggfunc="mean"
    )
    pre = [
        y for y in PRE_YEARS
        if y in wide.index and TREATED in wide.columns and pd.notna(wide.loc[y, TREATED])
    ]
    donor_names = [
        donor
        for donor in DONORS
        if donor in wide.columns
        and all(y in wide.index and pd.notna(wide.loc[y, donor]) for y in pre)
        and all(y in wide.index and pd.notna(wide.loc[y, donor]) for y in POST_YEARS)
    ]
    post = [
        y
        for y in POST_YEARS
        if y in wide.index
        and pd.notna(wide.loc[y, TREATED])
        and all(pd.notna(wide.loc[y, donor]) for donor in donor_names)
    ]
    if len(pre) < 2 or len(donor_names) < 2 or not post:
        return {
            "error": f"insufficient sparse synthetic-control coverage (pre={len(pre)}, donors={len(donor_names)}, post={len(post)})"
        }
    y = wide.loc[pre, TREATED].to_numpy(dtype=float)
    x = wide.loc[pre, donor_names].to_numpy(dtype=float)
    weights = nnls_weights(x, y)
    synth = wide.loc[post, donor_names].to_numpy(dtype=float) @ weights
    actual = wide.loc[post, TREATED].to_numpy(dtype=float)
    gaps = actual - synth
    placebos = []
    for donor in donor_names:
        others = [name for name in donor_names if name != donor]
        if len(others) < 2:
            continue
        w_d = nnls_weights(
            wide.loc[pre, others].to_numpy(dtype=float),
            wide.loc[pre, donor].to_numpy(dtype=float),
        )
        placebo_gap = (
            wide.loc[post, donor].to_numpy(dtype=float)
            - wide.loc[post, others].to_numpy(dtype=float) @ w_d
        )
        placebos.append(float(np.mean(placebo_gap)))
    return {
        "shape": "sparse_oecd_idd_lower_tail_synthetic_control",
        "measure": "bottom_to_median_pct = 100 / OECD D5_1_INC_DISP",
        "treated_country": TREATED,
        "pre_years": pre,
        "post_years": post,
        "donor_weights": {name: float(round(w, 6)) for name, w in zip(donor_names, weights)},
        "pre_rmse_pp": float(np.sqrt(np.mean((y - x @ weights) ** 2))),
        "post_gaps_pp": [
            {
                "year": int(year),
                "actual_bottom_to_median_pct": float(a),
                "synthetic_bottom_to_median_pct": float(s),
                "gap_pp": float(g),
            }
            for year, a, s, g in zip(post, actual, synth, gaps)
        ],
        "gap_2015_pp": float(gaps[0]),
        "mean_2015_2018_gap_pp": float(np.mean(gaps)),
        "placebo_p_value": (
            (1 + sum(abs(pg) >= abs(float(np.mean(gaps))) for pg in placebos))
            / (1 + len(placebos))
            if placebos
            else None
        ),
        "n_placebos": len(placebos),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC.read_text())
    path = latest()
    panel = load_lower_tail(path)
    est = fit(panel)
    if "error" in est:
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", est["error"]
    elif est["gap_2015_pp"] <= -3.0 and est["mean_2015_2018_gap_pp"] <= -3.0:
        verdict = "SUPPORTED"
        reason = "lower-tail disposable-income ratio is at least 3pp below synthetic control"
    elif est["gap_2015_pp"] > -1.0:
        verdict = "REFUTED"
        reason = (
            f"2015 bottom-to-median gap is {est['gap_2015_pp']:+.2f}pp, "
            "not the registered <= -3pp widening"
        )
    else:
        verdict = "PARTIAL"
        reason = "gap is directionally negative but misses the registered -3pp threshold"

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "sparse_synthetic_control_oecd_idd",
        "estimate": est,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "proxy_outcome",
                    "name": "bottom_to_median_disposable_income_ratio",
                    "source": "oecd:DSD_IDD@DF_IDD",
                    "filter": "MEASURE=D5_1_INC_DISP, AGE=_T, POVERTY_LINE=_Z",
                    "vintage_file": str(path.relative_to(ROOT)),
                    "sha256": sha256(path),
                }
            ],
            "variables_missing": [
                "OECD P10/P50 wage ratio",
                "low-pay incidence from the registered wage-distribution source",
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
        f"  oecd_idd_lower_tail_ratio: {path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    weights = ", ".join(
        f"{k}={v:.3f}" for k, v in est.get("donor_weights", {}).items() if v > 0.001
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## Sparse OECD IDD Benchmark\n"
        f"- Donor weights: {weights or 'none above 0.001'}.\n"
        f"- 2015 bottom-to-median disposable-income gap: **{est.get('gap_2015_pp', float('nan')):.2f} pp**.\n"
        f"- Mean 2015-2018 gap: **{est.get('mean_2015_2018_gap_pp', float('nan')):.2f} pp**.\n"
        f"- Placebo p-value: **{est.get('placebo_p_value', float('nan')):.3f}**.\n\n"
        "This is a disposable-income lower-tail proxy. The registered wage P10/P50 source is still not locally wired.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0 if verdict != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
