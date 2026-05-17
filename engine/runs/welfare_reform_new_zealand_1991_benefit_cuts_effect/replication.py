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
HID = "welfare_reform_new_zealand_1991_benefit_cuts_effect"
OUT = ROOT / "engine" / "runs" / HID
SPEC = ROOT / "hypotheses" / "welfare_architecture" / f"{HID}.yaml"
TREATED = "NZL"
DONORS = ["AUS", "IRL", "GBR", "CAN"]


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


def load_child_poverty(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    child = df[
        df["MEASURE"].eq("PR_INC_DISP")
        & df["AGE"].eq("Y_LT18")
        & df["POVERTY_LINE"].eq("PL_50")
    ][["REF_AREA", "period", "value"]].dropna()
    child = child.copy()
    child["country"] = child["REF_AREA"].astype(str)
    child["year"] = child["period"].astype(int)
    child["child_poverty_rate"] = child["value"].astype(float)
    return (
        child[["country", "year", "child_poverty_rate"]]
        .groupby(["country", "year"], as_index=False)
        .mean(numeric_only=True)
    )


def limited_synth_2000(panel: pd.DataFrame) -> dict:
    wide = panel[panel["country"].isin([TREATED] + DONORS)].pivot_table(
        index="year", columns="country", values="child_poverty_rate", aggfunc="mean"
    )
    pre = [1985, 1990]
    post = [2000]
    donor_names = [
        donor
        for donor in DONORS
        if donor in wide.columns
        and all(y in wide.index and pd.notna(wide.loc[y, donor]) for y in pre)
        and all(y in wide.index and pd.notna(wide.loc[y, donor]) for y in post)
    ]
    if len(donor_names) < 2:
        return {"error": f"insufficient donor coverage for 2000 synthetic check ({donor_names})"}
    y = wide.loc[pre, TREATED].to_numpy(dtype=float)
    x = wide.loc[pre, donor_names].to_numpy(dtype=float)
    w = nnls_weights(x, y)
    synth = float(wide.loc[2000, donor_names].to_numpy(dtype=float) @ w)
    actual = float(wide.loc[2000, TREATED])
    return {
        "pre_years": pre,
        "post_year": 2000,
        "donor_weights": {name: float(round(weight, 6)) for name, weight in zip(donor_names, w)},
        "actual_2000": actual,
        "synthetic_2000": synth,
        "gap_2000_pp": actual - synth,
        "pre_rmse_pp": float(np.sqrt(np.mean((y - x @ w) ** 2))),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC.read_text())
    path = latest()
    panel = load_child_poverty(path)
    nz = panel[panel["country"].eq(TREATED)].set_index("year")["child_poverty_rate"].sort_index()
    required = [1985, 1990, 1995, 2000]
    missing = [year for year in required if year not in nz.index]
    if missing:
        est = {"error": f"missing NZL OECD child-poverty years {missing}"}
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", est["error"]
    else:
        delta_1990_1995 = float(nz.loc[1995] - nz.loc[1990])
        delta_1990_2000 = float(nz.loc[2000] - nz.loc[1990])
        synth = limited_synth_2000(panel)
        est = {
            "shape": "oecd_child_poverty_direct_and_limited_synthetic_check",
            "measure": "OECD IDD PR_INC_DISP, AGE=Y_LT18, POVERTY_LINE=PL_50",
            "nz_rates": [
                {"year": int(year), "child_poverty_rate": float(nz.loc[year])}
                for year in required
            ],
            "delta_1990_1995_pp": delta_1990_1995,
            "delta_1990_2000_pp": delta_1990_2000,
            "limited_synthetic_2000": synth,
            "method_note": (
                "The registered five-year horizon is checked directly because the local donor pool "
                "does not have enough 1995 observations for a 1995 synthetic control. A limited "
                "2000 synthetic check is reported where donor coverage permits it."
            ),
        }
        if delta_1990_1995 >= 6.0:
            verdict = "SUPPORTED"
            reason = f"OECD child poverty rises {delta_1990_1995:.1f}pp by 1995"
        elif delta_1990_1995 < 3.0:
            verdict = "REFUTED"
            reason = (
                f"OECD child poverty changes {delta_1990_1995:+.1f}pp by 1995, "
                "well below the registered +6pp rise"
            )
        else:
            verdict = "PARTIAL"
            reason = f"OECD child poverty rises {delta_1990_1995:.1f}pp, below the +6pp gate"

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "oecd_child_poverty_exact_benchmark",
        "estimate": est,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "outcome",
                    "name": "child_poverty_rate_under_50_median",
                    "source": "oecd:DSD_IDD@DF_IDD",
                    "filter": "MEASURE=PR_INC_DISP, AGE=Y_LT18, POVERTY_LINE=PL_50",
                    "vintage_file": str(path.relative_to(ROOT)),
                    "sha256": sha256(path),
                }
            ],
            "variables_missing": [
                "under-65%-median child poverty series",
                "WDI/OECD Gini parallel check with NZL pre-1991 coverage",
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
        f"  oecd_idd_child_poverty: {path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    synth = est.get("limited_synthetic_2000", {}) if isinstance(est, dict) else {}
    synth_line = (
        f"- Limited 2000 synthetic gap: **{synth.get('gap_2000_pp', float('nan')):.2f} pp**.\n"
        if "error" not in synth
        else f"- Limited 2000 synthetic check: {synth.get('error')}.\n"
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## OECD Child-Poverty Benchmark\n"
        f"- NZL 1990 to 1995 change: **{est.get('delta_1990_1995_pp', float('nan')):.2f} pp**.\n"
        f"- NZL 1990 to 2000 change: **{est.get('delta_1990_2000_pp', float('nan')):.2f} pp**.\n"
        f"{synth_line}\n"
        "The exact under-65%-median and Gini parallel legs remain unavailable locally.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0 if verdict != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
