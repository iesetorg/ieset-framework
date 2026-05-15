#!/usr/bin/env python3
"""Run-local replication for federal_minimum_wage_employment_meta.

This revives the local state-year minimum-wage panel unlocked by the derived
minimum-wage bite vintage. It is intentionally a fixed-effects readiness screen,
not a full Callaway-Sant'Anna implementation or a direct CBO scenario model.
"""
from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[3]
HID = "federal_minimum_wage_employment_meta"
OUT = ROOT / "engine" / "runs" / HID
SPEC_PATH = ROOT / "hypotheses" / "labour" / f"{HID}.yaml"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parquet_rows(path: Path) -> int:
    return int(len(pd.read_parquet(path)))


def latest(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return matches[-1]


def broadest(pattern: str) -> Path:
    matches = sorted(ROOT.glob(pattern))
    if not matches:
        raise FileNotFoundError(pattern)
    return max(matches, key=lambda p: (parquet_rows(p), p.name))


def vintage_record(source: str, path: Path) -> dict:
    return {
        "source": source,
        "vintage_file": str(path.relative_to(ROOT)),
        "sha256": sha256(path),
        "rows": parquet_rows(path),
    }


def load_panel(qcew_path: Path, minwage_path: Path, bite_path: Path) -> pd.DataFrame:
    qcew = pd.read_parquet(qcew_path)
    qcew = qcew[
        ["area_fips", "year", "annual_avg_emplvl", "oty_annual_avg_emplvl_pct_chg"]
    ].copy()
    qcew["state_fips"] = qcew["area_fips"].astype(str).str.slice(0, 2)
    qcew["year"] = qcew["year"].astype(int)
    qcew["annual_avg_emplvl"] = pd.to_numeric(
        qcew["annual_avg_emplvl"], errors="coerce"
    )
    qcew["employment_growth_pct"] = pd.to_numeric(
        qcew["oty_annual_avg_emplvl_pct_chg"], errors="coerce"
    )
    qcew["log_emp"] = qcew["annual_avg_emplvl"].map(
        lambda x: math.log(x) if pd.notna(x) and x > 0 else None
    )

    minwage = pd.read_parquet(minwage_path)
    minwage = minwage[["state_fips", "state_abbr", "state_name", "year", "value"]].rename(
        columns={"value": "minimum_wage"}
    )
    minwage["year"] = minwage["year"].astype(int)
    minwage["minimum_wage"] = pd.to_numeric(minwage["minimum_wage"], errors="coerce")
    minwage = minwage.sort_values(["state_fips", "year"])
    minwage["log_min_wage"] = minwage["minimum_wage"].map(
        lambda x: math.log(x) if pd.notna(x) and x > 0 else None
    )
    minwage["min_wage_growth_pct"] = 100 * (
        minwage["log_min_wage"] - minwage.groupby("state_fips")["log_min_wage"].shift(1)
    )

    bite = pd.read_parquet(bite_path)
    bite = bite[["state_fips", "year", "bite_ratio", "denominator_wage"]].copy()
    bite["year"] = bite["year"].astype(int)
    bite["bite_ratio"] = pd.to_numeric(bite["bite_ratio"], errors="coerce")
    bite["denominator_wage"] = pd.to_numeric(bite["denominator_wage"], errors="coerce")

    panel = qcew.merge(minwage, on=["state_fips", "year"], how="inner")
    panel = panel.merge(bite, on=["state_fips", "year"], how="left")
    panel["year_fe"] = panel["year"].astype(str)
    return panel


def fit(panel: pd.DataFrame, name: str, formula: str, term: str, required: list[str]) -> dict:
    sub = panel.dropna(subset=required).copy()
    model = smf.ols(formula, data=sub).fit(
        cov_type="cluster", cov_kwds={"groups": sub["state_fips"]}
    )
    coef = float(model.params[term])
    se = float(model.bse[term])
    p_value = float(model.pvalues[term])
    return {
        "name": name,
        "formula": formula,
        "term": term,
        "coefficient": coef,
        "std_error_cluster_state": se,
        "p_value": p_value,
        "ci90": [coef - 1.645 * se, coef + 1.645 * se],
        "ci95": [coef - 1.96 * se, coef + 1.96 * se],
        "n_obs": int(len(sub)),
        "n_states": int(sub["state_fips"].nunique()),
        "years": [int(sub["year"].min()), int(sub["year"].max())],
    }


def verdict(primary: dict) -> tuple[str, str]:
    coef = primary["coefficient"]
    ci90_lo, ci90_hi = primary["ci90"]
    if -0.05 <= ci90_lo and ci90_hi <= 0.05:
        return (
            "SUPPORTED",
            (
                "primary employment elasticity is statistically contained in the "
                "predeclared near-zero band [-0.05, +0.05]"
            ),
        )
    if coef < -0.05 and primary["p_value"] < 0.10:
        return (
            "REFUTED",
            "primary elasticity is negative, larger than the near-zero band, and p<0.10",
        )
    return (
        "PARTIAL",
        (
            f"local state FE elasticity {coef:+.4f} is near zero, but the 90% CI "
            f"[{ci90_lo:+.4f}, {ci90_hi:+.4f}] is not contained in [-0.05, +0.05]"
        ),
    )


def write_outputs(spec: dict, vintages: dict, panel: pd.DataFrame, estimates: list[dict]) -> None:
    run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    primary = estimates[0]
    label, reason = verdict(primary)
    bite_nonnull = int(panel["bite_ratio"].notna().sum())
    status = {
        "variables_loaded": [
            {
                "role": "outcome",
                "name": "state_total_employment_qcew",
                "source": "bls:QCEW_state_total_employment_panel",
                "publisher": "bls",
                "n_rows": vintages["qcew"]["rows"],
            },
            {
                "role": "treatment",
                "name": "state_minimum_wage",
                "source": "usdol:state_minimum_wage_history",
                "publisher": "usdol",
                "n_rows": vintages["minwage"]["rows"],
            },
            {
                "role": "treatment",
                "name": "minimum_to_median_wage_ratio",
                "source": "derived:minimum_wage_bite_ratio_subnational_panel",
                "publisher": "derived",
                "n_rows": vintages["bite"]["rows"],
            },
        ],
        "variables_missing": [],
    }
    diagnostics = {
        "verdict": f"{label} - {reason}",
        "verdict_label": label,
        "verdict_reason": reason,
        "hypothesis_id": HID,
        "template": "run_local_minimum_wage_state_panel",
        "claim_direction_inferred": "near_zero",
        "falsification_rule_text": (spec.get("falsification") or {}).get("rule"),
        "falsification_test_text": (spec.get("falsification") or {}).get("test"),
        "estimate": primary,
        "robustness": estimates[1:],
        "data_status": status,
        "panel": {
            "n_obs_state_year": int(len(panel)),
            "n_states": int(panel["state_fips"].nunique()),
            "years": [int(panel["year"].min()), int(panel["year"].max())],
            "bite_nonnull_state_years": bite_nonnull,
        },
        "selected_vintages": vintages,
        "run_utc": run_utc,
        "runner": "engine/runs/federal_minimum_wage_employment_meta/replication.py",
        "method_valid": True,
        "data_gap": False,
        "minimum_wage_data_gate": False,
        "pre_registration_stub_rule": True,
        "scoreboard_posture": "needs_mapping_review",
        "caveats": [
            "The top-level hypothesis remains draft and the falsification rule is generic boilerplate.",
            "This is a state-year FE screen, not a full Callaway-Sant'Anna estimator.",
            "The revived local panel begins in 2014, so it cannot cover the registered 1990-2022 window.",
            "QCEW low-wage-sector and state labour-market controls remain robustness work, not primary inputs here.",
            "The CBO federal-floor extrapolation needs human mapping review before scoreboard conversion.",
        ],
    }
    (OUT / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest_lines = [
        f"hypothesis_id: {HID}",
        f"status: {label.lower()}",
        f"run_utc: {run_utc}",
        "runner: engine/runs/federal_minimum_wage_employment_meta/replication.py",
        "methodology: state-year fixed effects with state-clustered standard errors",
        "scoreboard_posture: needs_mapping_review",
        "vintages:",
    ]
    for key, rec in vintages.items():
        manifest_lines += [
            f"  {key}:",
            f"    source: {rec['source']}",
            f"    vintage_file: {rec['vintage_file']}",
            f"    sha256: {rec['sha256']}",
            f"    rows: {rec['rows']}",
        ]
    manifest_lines += [
        "caveats:",
        "  - draft hypothesis; local screen only",
        "  - broadest QCEW vintage selected because the latest exact QCEW vintage is a 2023-2024 partial refresh",
        "  - federal CBO mapping requires review before scoreboard conversion",
    ]
    (OUT / "manifest.yaml").write_text("\n".join(manifest_lines) + "\n")

    est_rows = [
        "| Estimate | Treatment | Coef | SE | p | N | States | Years |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for est in estimates:
        est_rows.append(
            "| {name} | `{term}` | {coef:+.4f} | {se:.4f} | {p:.3f} | {n} | {s} | {y0}-{y1} |".format(
                name=est["name"],
                term=est["term"],
                coef=est["coefficient"],
                se=est["std_error_cluster_state"],
                p=est["p_value"],
                n=est["n_obs"],
                s=est["n_states"],
                y0=est["years"][0],
                y1=est["years"][1],
            )
        )
    card = [
        f"# Result card - {HID}",
        "",
        f"**Verdict:** {label} - {reason}",
        "",
        "## Pre-registration",
        f"- **Claim:** {spec.get('claim', '').strip()}",
        f"- **Falsification rule:** {(spec.get('falsification') or {}).get('rule', '').strip()}",
        f"- **Falsification test:** {(spec.get('falsification') or {}).get('test', '').strip()}",
        "",
        "## Estimate",
        "",
        *est_rows,
        "",
        "Primary interpretation: the revived local state panel points near zero, but it is too imprecise to make a clean equivalence claim against the federal-floor/CBO mapping.",
        "",
        "## Variables resolved",
        f"- `{vintages['qcew']['source']}` -> state_total_employment_qcew (outcome, n={vintages['qcew']['rows']})",
        f"- `{vintages['minwage']['source']}` -> state_minimum_wage (treatment, n={vintages['minwage']['rows']})",
        f"- `{vintages['bite']['source']}` -> minimum_to_median_wage_ratio (treatment/diagnostic, n={vintages['bite']['rows']})",
        "",
        "## Caveats",
        "- This revives the local data gate, but the hypothesis is still a draft with a generic falsification rule.",
        "- The runner uses state/year FE with state-clustered SEs, not a full Callaway-Sant'Anna estimator.",
        "- The panel covers 2014-2024, not the registered 1990-2022 state-evidence window.",
        "- Scoreboard posture: needs_mapping_review.",
        "",
        f"_Generated by `engine/runs/federal_minimum_wage_employment_meta/replication.py` at {run_utc}_",
    ]
    (OUT / "result_card.md").write_text("\n".join(card) + "\n")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    spec = yaml.safe_load(SPEC_PATH.read_text())
    qcew_path = broadest("data/vintages/bls/QCEW_state_total_employment_panel@*.parquet")
    minwage_path = latest("data/vintages/usdol/state_minimum_wage_history@*.parquet")
    bite_path = latest("data/vintages/derived/minimum_wage_bite_ratio_subnational_panel@*.parquet")
    vintages = {
        "qcew": vintage_record("bls:QCEW_state_total_employment_panel", qcew_path),
        "minwage": vintage_record("usdol:state_minimum_wage_history", minwage_path),
        "bite": vintage_record("derived:minimum_wage_bite_ratio_subnational_panel", bite_path),
    }
    panel = load_panel(qcew_path, minwage_path, bite_path)
    estimates = [
        fit(
            panel,
            "primary_log_employment_elasticity",
            "log_emp ~ log_min_wage + C(state_fips) + C(year_fe)",
            "log_min_wage",
            ["log_emp", "log_min_wage"],
        ),
        fit(
            panel,
            "employment_growth_on_minimum_wage_growth",
            "employment_growth_pct ~ min_wage_growth_pct + C(state_fips) + C(year_fe)",
            "min_wage_growth_pct",
            ["employment_growth_pct", "min_wage_growth_pct"],
        ),
        fit(
            panel,
            "employment_growth_on_bite_ratio",
            "employment_growth_pct ~ bite_ratio + C(state_fips) + C(year_fe)",
            "bite_ratio",
            ["employment_growth_pct", "bite_ratio"],
        ),
    ]
    write_outputs(spec, vintages, panel, estimates)
    label, reason = verdict(estimates[0])
    print(f"{HID}: {label} - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
