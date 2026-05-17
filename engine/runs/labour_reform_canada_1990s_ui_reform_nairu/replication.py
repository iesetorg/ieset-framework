#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
HID = "labour_reform_canada_1990s_ui_reform_nairu"
OUT = ROOT / "engine" / "runs" / HID
TREATED = "CAN"
DONORS = ["USA", "GBR", "AUS", "FRA", "DEU", "NLD"]
EVENT_YEAR = 1990
END_YEAR = 2000
PERIOD = (1985, 2002)


def latest() -> Path:
    files = sorted((ROOT / "data" / "vintages" / "jst").glob("unemp@*.parquet"))
    if not files:
        raise FileNotFoundError("missing jst:unemp")
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


def fit(df: pd.DataFrame) -> dict:
    sub = df[df["country"].isin([TREATED] + DONORS) & df["year"].between(*PERIOD)]
    wide = sub.pivot(index="year", columns="country", values="unemployment_rate")
    pre = wide[wide.index < EVENT_YEAR]
    post = wide[(wide.index >= EVENT_YEAR) & (wide.index <= END_YEAR)]
    available = [d for d in DONORS if d in wide.columns]
    pre_t = pre[TREATED].dropna()
    pre_d = pre[available].dropna(axis=1)
    years = pre_t.index.intersection(pre_d.dropna().index)
    pre_d = pre_d.loc[years].dropna(axis=1)
    names = list(pre_d.columns)
    y = pre_t.loc[years].to_numpy()
    x = pre_d.loc[years].to_numpy()
    w = nnls_weights(x, y)
    common_post = post[TREATED].dropna().index.intersection(post[names].dropna().index)
    gaps = post.loc[common_post, TREATED].to_numpy() - post.loc[common_post, names].to_numpy() @ w
    placebos = []
    for donor in names:
        others = [n for n in names if n != donor]
        if len(others) < 2:
            continue
        w_d = nnls_weights(pre_d.loc[years, others].to_numpy(), pre_d.loc[years, donor].to_numpy())
        cp = post[donor].dropna().index.intersection(post[others].dropna().index)
        if len(cp):
            placebos.append(float(np.mean(post.loc[cp, donor].to_numpy() - post.loc[cp, others].to_numpy() @ w_d)))
    p_value = (1 + sum(abs(pg) >= abs(float(np.mean(gaps))) for pg in placebos)) / (1 + len(placebos))
    return {
        "treated_country": TREATED,
        "event_year": EVENT_YEAR,
        "pre_years": [int(years.min()), int(years.max())],
        "post_years": [int(common_post.min()), int(common_post.max())],
        "donor_weights": {n: float(round(wi, 6)) for n, wi in zip(names, w)},
        "pre_rmse": float(np.sqrt(np.mean((y - x @ w) ** 2))),
        "mean_post_unemployment_gap_pp": float(np.mean(gaps)),
        "end_2000_unemployment_gap_pp": float(gaps[-1]),
        "placebo_p_value": float(p_value),
        "post_gaps": [{"year": int(y_), "gap_pp": float(g)} for y_, g in zip(common_post, gaps)],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    path = latest()
    raw = pd.read_parquet(path)
    df = raw[["country_iso3", "year", "unemp"]].dropna().rename(
        columns={"country_iso3": "country", "unemp": "unemployment_rate"}
    )
    est = fit(df)
    if est["mean_post_unemployment_gap_pp"] <= -1.5 and est["placebo_p_value"] < 0.10:
        verdict, reason = "SUPPORTED", "Canadian unemployment gap clears the -1.5pp synthetic-control gate"
    elif est["mean_post_unemployment_gap_pp"] >= 0 or est["end_2000_unemployment_gap_pp"] >= 0:
        verdict, reason = "REFUTED", "Canadian unemployment is above the synthetic control through 2000"
    else:
        verdict, reason = "PARTIAL", "gap is in the claimed direction but not significant at the registered threshold"
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "synthetic_control_jst_unemployment",
        "estimate": est,
        "data_status": {
            "variables_loaded": [{"source": "jst:unemp", "vintage_file": str(path.relative_to(ROOT)), "sha256": sha256(path)}],
            "variables_missing": ["imf:NAIRU", "province-level frequent-claimant heterogeneity"],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2))
    (OUT / "manifest.yaml").write_text(f"hypothesis_id: {HID}\nsources:\n  jst_unemp: {path.relative_to(ROOT)}\nrun_utc: {run_utc}\n")
    weights = ", ".join(f"{k}={v:.3f}" for k, v in est["donor_weights"].items() if v > 0.001)
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## JST Synthetic-Control Benchmark\n"
        f"- Donor weights: {weights or 'none above 0.001'}.\n"
        f"- Mean 1990-2000 unemployment gap: **{est['mean_post_unemployment_gap_pp']:.2f} pp**.\n"
        f"- End-2000 unemployment gap: **{est['end_2000_unemployment_gap_pp']:.2f} pp**.\n"
        f"- Placebo p-value: **{est['placebo_p_value']:.3f}**.\n\n"
        "The registered regional heterogeneity leg remains unavailable locally, so this is a national unemployment benchmark.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
