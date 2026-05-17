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
HID = "labour_reform_uk_thatcher_union_law_1980s"
OUT = ROOT / "engine" / "runs" / HID
SPEC = ROOT / "hypotheses" / "labour" / f"{HID}.yaml"
TREATED = "GBR"
DONORS = ["FRA", "DEU", "ITA", "ESP", "NLD", "BEL", "IRL"]
EVENT_YEAR = 1980
END_YEAR = 1990
PERIOD = (1975, 1995)


def latest(pub: str, pattern: str) -> Path:
    files = sorted((ROOT / "data" / "vintages" / pub).glob(pattern))
    if not files:
        raise FileNotFoundError(f"missing {pub}:{pattern}")
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


def synth(panel: pd.DataFrame, value_col: str) -> dict:
    sub = panel[panel["country"].isin([TREATED] + DONORS) & panel["year"].between(*PERIOD)]
    wide = sub.pivot_table(index="year", columns="country", values=value_col, aggfunc="mean")
    pre = wide[wide.index < EVENT_YEAR]
    post = wide[(wide.index >= EVENT_YEAR) & (wide.index <= END_YEAR)]
    available = [donor for donor in DONORS if donor in wide.columns]
    pre_t = pre[TREATED].dropna()
    pre_d = pre[available].dropna(axis=1)
    years = pre_t.index.intersection(pre_d.dropna().index)
    pre_d = pre_d.loc[years].dropna(axis=1)
    donor_names = list(pre_d.columns)
    if len(years) < 2 or len(donor_names) < 2:
        return {"error": f"insufficient coverage (pre_years={len(years)}, donors={len(donor_names)})"}
    y = pre_t.loc[years].to_numpy(dtype=float)
    x = pre_d.loc[years].to_numpy(dtype=float)
    weights = nnls_weights(x, y)
    common = post[TREATED].dropna().index.intersection(post[donor_names].dropna().index)
    actual = post.loc[common, TREATED].to_numpy(dtype=float)
    synthetic = post.loc[common, donor_names].to_numpy(dtype=float) @ weights
    gaps = actual - synthetic
    placebos = []
    for donor in donor_names:
        others = [name for name in donor_names if name != donor]
        if len(others) < 2:
            continue
        w_d = nnls_weights(
            pre_d.loc[years, others].to_numpy(dtype=float),
            pre_d.loc[years, donor].to_numpy(dtype=float),
        )
        cp = post[donor].dropna().index.intersection(post[others].dropna().index)
        if len(cp):
            placebos.append(
                float(
                    np.mean(
                        post.loc[cp, donor].to_numpy(dtype=float)
                        - post.loc[cp, others].to_numpy(dtype=float) @ w_d
                    )
                )
            )
    return {
        "pre_years": [int(years.min()), int(years.max())],
        "post_years": [int(common.min()), int(common.max())],
        "donor_weights": {name: float(round(weight, 6)) for name, weight in zip(donor_names, weights)},
        "pre_rmse": float(np.sqrt(np.mean((y - x @ weights) ** 2))),
        "post_gaps": [
            {"year": int(year), "gap": float(gap)}
            for year, gap in zip(common, gaps)
        ],
        "mean_post_gap": float(np.mean(gaps)),
        "end_1990_gap": float(gaps[-1]),
        "placebo_p_value": (
            (1 + sum(abs(pg) >= abs(float(np.mean(gaps))) for pg in placebos))
            / (1 + len(placebos))
            if placebos
            else None
        ),
        "n_placebos": len(placebos),
    }


def load_union_density(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    tud = df[df["MEASURE"].eq("TUD")][["REF_AREA", "period", "value"]].dropna().copy()
    tud["country"] = tud["REF_AREA"].astype(str)
    tud["year"] = tud["period"].astype(int)
    tud["union_density"] = tud["value"].astype(float)
    return tud[["country", "year", "union_density"]]


def load_unemployment(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    out = df[["country_iso3", "year", "unemp"]].dropna().copy()
    out = out.rename(columns={"country_iso3": "country", "unemp": "unemployment_rate"})
    out["year"] = out["year"].astype(int)
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC.read_text())
    tud_path = latest("oecd", "OECD.ELS.SAE_DSD_TUD_CBC_DF_TUD_1.0@*.parquet")
    unemp_path = latest("jst", "unemp@*.parquet")
    tud_est = synth(load_union_density(tud_path), "union_density")
    unemp_est = synth(load_unemployment(unemp_path), "unemployment_rate")

    if "error" in tud_est and "error" in unemp_est:
        verdict = "INCONCLUSIVE_DATA_PENDING"
        reason = f"proxy benchmarks failed: {tud_est.get('error')}; {unemp_est.get('error')}"
    else:
        verdict = "PARTIAL"
        if "error" not in tud_est and tud_est["end_1990_gap"] >= 0:
            reason = (
                "local union-density proxy is not below synthetic control by 1990; "
                "strike-days and union-wage-premium legs remain unavailable"
            )
        else:
            reason = (
                "proxy benchmarks are directionally informative but primary strike-days "
                "and wage-premium legs remain unavailable"
            )

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    est = {
        "shape": "local_proxy_synthetic_controls",
        "union_density_proxy": tud_est,
        "jst_unemployment_employment_gain_proxy": unemp_est,
        "method_note": (
            "OECD trade-union density is a bargaining-power proxy, not the registered "
            "strike-days or union-wage-premium outcome. JST unemployment is an inverse "
            "employment benchmark."
        ),
    }
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "proxy_synthetic_control",
        "estimate": est,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "proxy_outcome",
                    "name": "trade_union_density",
                    "source": "oecd:OECD.ELS.SAE_DSD_TUD_CBC@DF_TUD",
                    "vintage_file": str(tud_path.relative_to(ROOT)),
                    "sha256": sha256(tud_path),
                },
                {
                    "role": "proxy_outcome",
                    "name": "unemployment_rate",
                    "source": "jst:unemp",
                    "vintage_file": str(unemp_path.relative_to(ROOT)),
                    "sha256": sha256(unemp_path),
                },
            ],
            "variables_missing": [
                "strike_days_lost_per_1000_employees",
                "union_wage_premium",
                "pre-1980 OECD employment-to-population panel for GBR",
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
        f"  oecd_trade_union_density: {tud_path.relative_to(ROOT)}\n"
        f"  jst_unemployment: {unemp_path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    weights = ", ".join(
        f"{k}={v:.3f}"
        for k, v in tud_est.get("donor_weights", {}).items()
        if v > 0.001
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## Local Proxy Synthetic Controls\n"
        f"- Union-density donor weights: {weights or 'none above 0.001'}.\n"
        f"- Union-density mean 1980-1990 gap: **{tud_est.get('mean_post_gap', float('nan')):.2f} pp**.\n"
        f"- Union-density 1990 gap: **{tud_est.get('end_1990_gap', float('nan')):.2f} pp**.\n"
        f"- JST unemployment mean 1980-1990 gap: **{unemp_est.get('mean_post_gap', float('nan')):.2f} pp**.\n\n"
        "Primary strike-days and union-wage-premium data are still absent locally, so this remains a proxy benchmark.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0 if verdict != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
