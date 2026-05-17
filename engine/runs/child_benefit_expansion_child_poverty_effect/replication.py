#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[3]
HID = "child_benefit_expansion_child_poverty_effect"
OUT = ROOT / "engine" / "runs" / HID
SPEC = ROOT / "hypotheses" / "distribution" / f"{HID}.yaml"


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


def normal_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def diff_test(df: pd.DataFrame, start: int, end: int, direction: str) -> dict:
    by_year = df.set_index("year")
    start_rate = float(by_year.loc[start, "value"])
    end_rate = float(by_year.loc[end, "value"])
    start_moe = float(by_year.loc[start, "under18_spm_poverty_rate_moe_90_pctpt"])
    end_moe = float(by_year.loc[end, "under18_spm_poverty_rate_moe_90_pctpt"])
    if direction == "drop":
        diff = start_rate - end_rate
    elif direction == "rebound":
        diff = end_rate - start_rate
    else:
        raise ValueError(direction)
    se = math.sqrt((start_moe / 1.645) ** 2 + (end_moe / 1.645) ** 2)
    z = diff / se if se else None
    return {
        "start_year": start,
        "end_year": end,
        "start_rate": start_rate,
        "end_rate": end_rate,
        "diff_pp": diff,
        "se_diff_pp": se,
        "z": z,
        "p_two_sided_normal_approx": 2.0 * normal_sf(abs(z)) if z is not None else None,
    }


def us_spm_leg(path: Path) -> dict:
    df = pd.read_parquet(path)
    if "country_iso3" in df.columns:
        df = df[df["country_iso3"].eq("USA")]
    df = df.dropna(subset=["year", "value"]).copy()
    df["year"] = df["year"].astype(int)
    required = {2020, 2021, 2022}
    missing = sorted(required - set(df["year"]))
    if missing:
        return {"error": f"missing US SPM years {missing}"}
    drop = diff_test(df, 2020, 2021, "drop")
    rebound = diff_test(df, 2021, 2022, "rebound")
    rates = (
        df[df["year"].between(2018, 2023)]
        .sort_values("year")[
            [
                "year",
                "value",
                "under18_spm_poverty_rate_moe_90_pctpt",
                "all_people_spm_poverty_rate_pct",
            ]
        ]
        .to_dict(orient="records")
    )
    return {
        "source": "us_census:spm_child_poverty_rate",
        "rates": rates,
        "drop_2020_2021": drop,
        "rebound_2021_2022": rebound,
        "drop_gate_pass": bool(
            drop["diff_pp"] >= 3.0 and (drop["p_two_sided_normal_approx"] or 1.0) < 0.10
        ),
        "rebound_gate_pass": bool(
            rebound["diff_pp"] >= 2.0
            and (rebound["p_two_sided_normal_approx"] or 1.0) < 0.10
        ),
    }


def uk_oecd_leg(path: Path) -> dict:
    df = pd.read_parquet(path)
    uk = df[
        df["REF_AREA"].eq("GBR")
        & df["MEASURE"].eq("PR_INC_DISP")
        & df["AGE"].eq("Y_LT18")
        & df["POVERTY_LINE"].eq("PL_50")
    ][["period", "value"]].dropna()
    if uk.empty:
        return {"error": "missing UK OECD child poverty series"}
    yearly = uk.groupby("period", as_index=False)["value"].mean()
    yearly["period"] = yearly["period"].astype(int)
    pre = yearly[yearly["period"].between(2011, 2013)]
    post = yearly[yearly["period"].between(2014, 2019)]
    if len(pre) < 2 or len(post) < 3:
        return {"error": f"insufficient UK sign-check years (pre={len(pre)}, post={len(post)})"}
    pre_mean = float(pre["value"].mean())
    post_mean = float(post["value"].mean())
    delta = post_mean - pre_mean
    return {
        "source": "oecd:DSD_IDD@DF_IDD",
        "measure_filter": {
            "REF_AREA": "GBR",
            "MEASURE": "PR_INC_DISP",
            "AGE": "Y_LT18",
            "POVERTY_LINE": "PL_50",
        },
        "pre_2011_2013_mean": pre_mean,
        "post_2014_2019_mean": post_mean,
        "post_minus_pre_pp": delta,
        "sign_gate_pass": bool(delta >= 1.0),
        "yearly_rates": yearly[yearly["period"].between(2009, 2019)].to_dict(orient="records"),
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC.read_text())
    spm_path = latest("us_census", "spm_child_poverty_rate@*.parquet")
    idd_path = latest("oecd", "DSD_IDD@*.parquet")
    us = us_spm_leg(spm_path)
    uk = uk_oecd_leg(idd_path)

    if "error" in us:
        verdict, reason = "INCONCLUSIVE_DATA_PENDING", us["error"]
    else:
        us_ok = us["drop_gate_pass"] and us["rebound_gate_pass"]
        uk_ok = "error" not in uk and uk["sign_gate_pass"]
        if us_ok and uk_ok:
            verdict = "SUPPORTED"
            reason = (
                f"US SPM child poverty fell {us['drop_2020_2021']['diff_pp']:.1f}pp "
                f"and rebounded {us['rebound_2021_2022']['diff_pp']:.1f}pp; "
                f"UK child poverty rose {uk['post_minus_pre_pp']:.1f}pp after the 2013 tightening"
            )
        elif us_ok or uk_ok:
            verdict = "PARTIAL"
            reason = "one country leg clears the exact descriptive gate"
        elif us["drop_2020_2021"]["diff_pp"] < 1.5 and us["rebound_2021_2022"]["diff_pp"] < 1.5:
            verdict = "REFUTED"
            reason = "US SPM drop and rebound are both below the minimum refutation floor"
        else:
            verdict = "PARTIAL"
            reason = "directional movement is present but exact gates do not jointly clear"

    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    estimate = {
        "shape": "exact_child_benefit_descriptive_benchmark",
        "us_spm_leg": us,
        "uk_oecd_child_poverty_leg": uk,
        "method_note": (
            "US Census SPM is an annual accounting benchmark for the ARP CTC expansion. "
            "The UK OECD IDD leg is a sign check around the 2013 child-benefit means-test "
            "tightening, not a claimant-level causal design."
        ),
    }
    diag = {
        "verdict": f"{verdict} - {reason}",
        "verdict_label": verdict,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "exact_child_benefit_descriptive",
        "claim_direction_inferred": "-",
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "estimate": estimate,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "outcome",
                    "name": "us_spm_child_poverty_rate",
                    "source": "us_census:spm_child_poverty_rate",
                    "vintage_file": str(spm_path.relative_to(ROOT)),
                    "sha256": sha256(spm_path),
                },
                {
                    "role": "outcome",
                    "name": "uk_oecd_child_poverty_rate",
                    "source": "oecd:DSD_IDD@DF_IDD",
                    "vintage_file": str(idd_path.relative_to(ROOT)),
                    "sha256": sha256(idd_path),
                },
            ],
            "variables_missing": ["harmonised CPS/FRS microdata for the original staggered-DiD design"],
        },
        "run_utc": run_utc,
        "runner": f"engine/runs/{HID}/replication.py",
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diag, indent=2) + "\n")
    (OUT / "manifest.yaml").write_text(
        f"hypothesis_id: {HID}\n"
        "sources:\n"
        f"  us_spm_child_poverty_rate: {spm_path.relative_to(ROOT)}\n"
        f"  oecd_idd_child_poverty: {idd_path.relative_to(ROOT)}\n"
        f"run_utc: {run_utc}\n"
    )
    uk_line = (
        f"- UK OECD PL50 under-18 poverty: {uk['pre_2011_2013_mean']:.1f}% "
        f"(2011-2013) to {uk['post_2014_2019_mean']:.1f}% (2014-2019), "
        f"delta {uk['post_minus_pre_pp']:.1f} pp.\n"
        if "error" not in uk
        else f"- UK OECD sign check: {uk['error']}.\n"
    )
    (OUT / "result_card.md").write_text(
        f"# Result card - {HID}\n\n"
        f"**Verdict:** {verdict} - {reason}\n\n"
        "## Exact Benchmark\n"
        f"- US SPM child poverty drop, 2020-2021: {us.get('drop_2020_2021', {}).get('diff_pp', float('nan')):.1f} pp.\n"
        f"- US SPM child poverty rebound, 2021-2022: {us.get('rebound_2021_2022', {}).get('diff_pp', float('nan')):.1f} pp.\n"
        f"{uk_line}"
        "\nThe UK leg is a sign check around the 2013 means-test tightening; the original microdata DiD remains unwired locally.\n\n"
        f"_Generated by `engine/runs/{HID}/replication.py` at {run_utc}_\n"
    )
    print(json.dumps({"hypothesis_id": HID, "verdict": verdict, "reason": reason}, indent=2))
    return 0 if verdict != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
