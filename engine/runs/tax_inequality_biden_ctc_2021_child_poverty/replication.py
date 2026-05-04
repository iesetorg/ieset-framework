#!/usr/bin/env python3
"""Replication - Biden 2021 Child Tax Credit expansion and child poverty.

This run tests the hypothesis' explicit descriptive rule against the Census
Bureau's published Supplemental Poverty Measure (SPM) child-poverty table:

  SUPPORTED if the all-races under-18 SPM poverty rate falls by at least
  3.0 percentage points from 2020 to 2021, and then rises by at least
  2.0 percentage points from 2021 to 2022 after the expanded CTC expires.

The Census table reports 90 percent margins of error. We convert those to
standard errors using 1.645 and require both year-to-year moves to clear a
normal-approximation p<0.10 check.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
HID = "tax_inequality_biden_ctc_2021_child_poverty"
OUT_DIR = REPO_ROOT / "engine" / "runs" / HID
SPEC_PATH = REPO_ROOT / "hypotheses" / "distribution" / f"{HID}.yaml"
SOURCE_URL = "https://www2.census.gov/programs-surveys/demo/tables/p60/283/tableB-2.xlsx"
REPORT_URL = "https://www.census.gov/library/publications/2024/demo/p60-283.html"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from run_panel_fe import latest_vintage  # noqa: E402

sys.path.insert(0, str(REPO_ROOT))
from data.fetchers._base import write_manifest  # noqa: E402
from data.fetchers.us_census import fetch as fetch_us_census  # noqa: E402


def _normal_sf(z: float) -> float:
    return 0.5 * math.erfc(z / math.sqrt(2.0))


def _load_source_frame() -> tuple[pd.DataFrame, Path]:
    path = latest_vintage("us_census", "spm_child_poverty_rate")
    if path is None:
        result = fetch_us_census("spm_child_poverty_rate")
        write_manifest([result])
        path = result.parquet_path
    df = pd.read_parquet(path)
    return df, Path(path)


def _diff_test(df: pd.DataFrame, a: int, b: int, *, direction: str) -> dict:
    by_year = df.set_index("year")
    va = float(by_year.loc[a, "value"])
    vb = float(by_year.loc[b, "value"])
    ma = float(by_year.loc[a, "under18_spm_poverty_rate_moe_90_pctpt"])
    mb = float(by_year.loc[b, "under18_spm_poverty_rate_moe_90_pctpt"])
    if direction == "drop":
        diff = va - vb
        label = f"{a}->{b} drop"
    elif direction == "rebound":
        diff = vb - va
        label = f"{a}->{b} rebound"
    else:
        raise ValueError(direction)
    se = math.sqrt((ma / 1.645) ** 2 + (mb / 1.645) ** 2)
    z = diff / se if se else None
    p_two_sided = 2.0 * _normal_sf(abs(z)) if z is not None else None
    return {
        "label": label,
        "start_year": a,
        "end_year": b,
        "start_rate": va,
        "end_rate": vb,
        "diff_pp": diff,
        "se_diff_pp": se,
        "z": z,
        "p_two_sided_normal_approx": p_two_sided,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC_PATH.read_text())
    df, vintage_path = _load_source_frame()
    df = df[df["country_iso3"].eq("USA")].copy()
    required_years = {2020, 2021, 2022}
    have_years = set(int(y) for y in df["year"].dropna().astype(int))

    if not required_years.issubset(have_years):
        missing = sorted(required_years - have_years)
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        reason = f"missing required Census SPM years: {missing}"
        estimate = {"error": reason}
    else:
        drop = _diff_test(df, 2020, 2021, direction="drop")
        rebound = _diff_test(df, 2021, 2022, direction="rebound")
        drop_supported = drop["diff_pp"] >= 3.0 and (drop["p_two_sided_normal_approx"] or 1.0) < 0.10
        rebound_supported = (
            rebound["diff_pp"] >= 2.0
            and (rebound["p_two_sided_normal_approx"] or 1.0) < 0.10
        )
        if drop_supported and rebound_supported:
            verdict_label = "SUPPORTED"
            reason = (
                f"SPM child poverty fell {drop['diff_pp']:.1f}pp in 2020-2021 "
                f"and rebounded {rebound['diff_pp']:.1f}pp in 2021-2022; both "
                "clear the registered thresholds and p<0.10 MOE check"
            )
        elif drop["diff_pp"] < 1.5 or rebound["diff_pp"] < 1.5:
            verdict_label = "REFUTED"
            reason = (
                f"registered moves too small: drop={drop['diff_pp']:.1f}pp, "
                f"rebound={rebound['diff_pp']:.1f}pp"
            )
        else:
            verdict_label = "PARTIAL"
            reason = (
                f"direction present but one registered threshold/significance gate "
                f"does not clear: drop={drop['diff_pp']:.1f}pp, "
                f"rebound={rebound['diff_pp']:.1f}pp"
            )
        estimate = {
            "shape": "registered_pre_expansion_post_descriptive_check",
            "primary_drop_2020_2021": drop,
            "expiration_rebound_2021_2022": rebound,
            "rates": (
                df[df["year"].isin([2018, 2019, 2020, 2021, 2022, 2023])]
                .sort_values("year")
                [[
                    "year",
                    "value",
                    "under18_spm_poverty_rate_moe_90_pctpt",
                    "all_people_spm_poverty_rate_pct",
                ]]
                .to_dict(orient="records")
            ),
            "method_note": (
                "Census Table B-2 reports 90 percent margins of error. The run "
                "uses a normal approximation for differences in annual published "
                "rates; the CTC effect is partly mechanical because refundable "
                "tax credits enter SPM resources."
            ),
        }

    diagnostics = {
        "verdict": f"{verdict_label} - {reason}",
        "verdict_label": verdict_label,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "event_study",
        "claim_direction_inferred": "-",
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": estimate,
        "data_status": {
            "variables_loaded": [
                {
                    "role": "outcome",
                    "name": "child_poverty_rate",
                    "source": "us_census:spm_child_poverty_rate",
                    "publisher": "us_census",
                    "n_rows": int(len(df)),
                    "vintage": str(vintage_path.relative_to(REPO_ROOT)),
                }
            ],
            "variables_missing": [],
        },
        "source_urls": [SOURCE_URL, REPORT_URL],
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "engine/runs/tax_inequality_biden_ctc_2021_child_poverty/replication.py",
    }
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    rows = estimate.get("rates", []) if isinstance(estimate, dict) else []
    table = "\n".join(
        "| {year} | {value:.1f} | {moe:.1f} | {allp:.1f} |".format(
            year=int(r["year"]),
            value=float(r["value"]),
            moe=float(r["under18_spm_poverty_rate_moe_90_pctpt"]),
            allp=float(r["all_people_spm_poverty_rate_pct"]),
        )
        for r in rows
    )
    card = f"""# Result card - {HID}

**Verdict:** {verdict_label} - {reason}

## Registered Test
- **Rule:** {(spec.get("falsification") or {}).get("rule", "").strip()}
- **Source:** US Census Bureau, P60-283 Table B-2, published child SPM poverty rates.
- **Caveat:** This is a descriptive accounting test. Refundable tax credits enter SPM resources, so the mechanism is partly mechanical rather than a clean randomized causal design.

## Estimate
```json
{json.dumps(estimate, indent=2)}
```

## Key Rates
| year | under-18 SPM poverty rate | 90% MOE | all-people SPM poverty rate |
| --- | ---: | ---: | ---: |
{table}

_Generated by `engine/runs/{HID}/replication.py` at {diagnostics["run_utc"]}._
"""
    (OUT_DIR / "result_card.md").write_text(card)
    print(f"{verdict_label} - {reason}")
    return 0 if verdict_label != "INCONCLUSIVE_DATA_PENDING" else 1


if __name__ == "__main__":
    raise SystemExit(main())
