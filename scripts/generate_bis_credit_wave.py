#!/usr/bin/env python3
"""Generate BIS credit/housing/financial-stress panel run artifacts.

This script is intentionally local to Worker C's BIS wave. It uses only pinned
vintages already present under data/vintages/bis and writes run artifacts for
the requested hypothesis id.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
BIS = ROOT / "data" / "vintages" / "bis"

SPECS = {
    "bis_credit_gap_house_price_reversal_panel": {
        "topic": "housing",
        "title": "BIS credit gap predicts real house-price reversal",
        "outcome": "fwd_real_house_price_growth_12q",
        "treatment": "high_credit_gap",
        "continuous": "credit_gap",
        "formula": (
            "fwd_real_house_price_growth_12q ~ high_credit_gap + credit_gap "
            "+ lag_real_house_price_growth_8q + C(country) + C(year)"
        ),
        "gate": {
            "coef_max": -3.0,
            "p_max": 0.05,
            "mean_diff_max": -3.0,
            "min_countries": 20,
            "min_observations": 600,
        },
        "threshold_text": (
            "High credit-gap episode is BIS WS_CREDIT_GAP CG_DTYPE=C >= 10 "
            "percentage points; outcome is 12-quarter forward real residential "
            "property-price log growth from BIS WS_SPP VALUE=R index."
        ),
    },
    "bis_household_dsr_credit_slowdown_panel": {
        "topic": "monetary",
        "title": "Household debt-service stress predicts credit slowdown",
        "outcome": "fwd_credit_growth_8q",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "formula": (
            "fwd_credit_growth_8q ~ high_household_dsr + household_dsr "
            "+ lag_credit_growth_8q + C(country) + C(year)"
        ),
        "gate": {
            "coef_max": -2.0,
            "p_max": 0.05,
            "mean_diff_max": -2.0,
            "min_countries": 15,
            "min_observations": 500,
        },
        "threshold_text": (
            "High household-DSR stress is BIS WS_DSR DSR_BORROWERS=H above "
            "12 percent and above the country's own predeclared 75th percentile; "
            "outcome is 8-quarter forward change in broad private credit/GDP "
            "from WS_CREDIT_GAP CG_DTYPE=B."
        ),
    },
    "bis_household_dsr_property_slowdown_panel": {
        "topic": "housing",
        "title": "Household debt-service stress predicts property slowdown",
        "outcome": "fwd_real_house_price_growth_8q",
        "treatment": "high_household_dsr",
        "continuous": "household_dsr",
        "formula": (
            "fwd_real_house_price_growth_8q ~ high_household_dsr + household_dsr "
            "+ lag_real_house_price_growth_8q + C(country) + C(year)"
        ),
        "gate": {
            "coef_max": -2.0,
            "p_max": 0.05,
            "mean_diff_max": -2.0,
            "min_countries": 15,
            "min_observations": 400,
        },
        "threshold_text": (
            "High household-DSR stress is BIS WS_DSR DSR_BORROWERS=H above "
            "12 percent and above the country's own predeclared 75th percentile; "
            "outcome is 8-quarter forward real residential property-price log "
            "growth from WS_SPP VALUE=R index."
        ),
    },
    "bis_reer_appreciation_reversal_panel": {
        "topic": "monetary",
        "title": "Real exchange-rate appreciation mean-reverts",
        "outcome": "fwd_reer_growth_8q",
        "treatment": "large_reer_appreciation",
        "continuous": "reer_appreciation_12q",
        "formula": (
            "fwd_reer_growth_8q ~ large_reer_appreciation + reer_appreciation_12q "
            "+ C(country) + C(year)"
        ),
        "gate": {
            "coef_max": -2.0,
            "p_max": 0.05,
            "mean_diff_max": -2.0,
            "min_countries": 25,
            "min_observations": 1200,
        },
        "threshold_text": (
            "Large appreciation is 12-quarter log change in the BIS WS_EER "
            "monthly real broad effective exchange-rate index >= 15 percent; "
            "outcome is 8-quarter forward REER log change."
        ),
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def latest(series: str) -> Path:
    files = sorted(BIS.glob(f"{series}@*.parquet"))
    if not files:
        raise FileNotFoundError(f"Missing BIS vintage for {series}")
    return files[-1]


def qnum(period: str) -> int:
    year, q = str(period).split("-Q")
    return int(year) * 4 + int(q)


def qyear(q: int) -> int:
    return q // 4


def quarterly_index(df: pd.DataFrame, country_col: str, value_col: str = "value") -> pd.DataFrame:
    out = df[[country_col, "period", value_col]].copy()
    out = out.rename(columns={country_col: "country", value_col: "value"})
    out["q"] = out["period"].map(qnum)
    out["year"] = out["q"].map(qyear)
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["country", "q", "value"])


def add_forward_log_growth(df: pd.DataFrame, value_col: str, horizons: list[int], prefix: str) -> pd.DataFrame:
    out = df.sort_values(["country", "q"]).copy()
    for h in horizons:
        future = out.groupby("country")[value_col].shift(-h)
        lagged = out.groupby("country")[value_col].shift(h)
        out[f"fwd_{prefix}_growth_{h}q"] = 100 * (np.log(future) - np.log(out[value_col]))
        out[f"lag_{prefix}_growth_{h}q"] = 100 * (np.log(out[value_col]) - np.log(lagged))
    return out


def build_panel(paths: dict[str, Path]) -> pd.DataFrame:
    credit_raw = pd.read_parquet(paths["WS_CREDIT_GAP"])
    credit_gap = quarterly_index(
        credit_raw[credit_raw["CG_DTYPE"].eq("C")], "BORROWERS_CTY"
    ).rename(columns={"value": "credit_gap"})
    credit_level = quarterly_index(
        credit_raw[credit_raw["CG_DTYPE"].eq("B")], "BORROWERS_CTY"
    ).rename(columns={"value": "credit_gdp"})
    credit_level = credit_level.sort_values(["country", "q"])
    credit_level["fwd_credit_growth_8q"] = (
        credit_level.groupby("country")["credit_gdp"].shift(-8) - credit_level["credit_gdp"]
    )
    credit_level["lag_credit_growth_8q"] = (
        credit_level["credit_gdp"] - credit_level.groupby("country")["credit_gdp"].shift(8)
    )

    spp_raw = pd.read_parquet(paths["WS_SPP"])
    house = quarterly_index(
        spp_raw[spp_raw["VALUE"].eq("R") & spp_raw["UNIT_MEASURE"].eq(628)],
        "REF_AREA",
    ).rename(columns={"value": "real_house_price"})
    house = add_forward_log_growth(house, "real_house_price", [8, 12], "real_house_price")

    dsr_raw = pd.read_parquet(paths["WS_DSR"])
    dsr = quarterly_index(dsr_raw[dsr_raw["DSR_BORROWERS"].eq("H")], "BORROWERS_CTY").rename(
        columns={"value": "household_dsr"}
    )
    pct75 = dsr.groupby("country")["household_dsr"].quantile(0.75).rename("dsr_p75")
    dsr = dsr.merge(pct75, on="country", how="left")
    dsr["high_household_dsr"] = (
        (dsr["household_dsr"] >= 12.0) & (dsr["household_dsr"] >= dsr["dsr_p75"])
    ).astype(int)

    eer_raw = pd.read_parquet(paths["WS_EER"])
    eer_m = eer_raw[
        eer_raw["FREQ"].eq("M")
        & eer_raw["EER_TYPE"].eq("R")
        & eer_raw["EER_BASKET"].eq("B")
    ][["REF_AREA", "period", "value"]].copy()
    eer_m["country"] = eer_m["REF_AREA"]
    eer_m["date"] = pd.to_datetime(eer_m["period"] + "-01", errors="coerce")
    eer_m["q"] = eer_m["date"].dt.year * 4 + ((eer_m["date"].dt.month - 1) // 3 + 1)
    eer = (
        eer_m.dropna(subset=["q", "value"])
        .groupby(["country", "q"], as_index=False)["value"]
        .mean()
        .rename(columns={"value": "reer"})
    )
    eer["year"] = eer["q"].map(qyear)
    eer = add_forward_log_growth(eer, "reer", [8, 12], "reer")
    eer = eer.rename(columns={"lag_reer_growth_12q": "reer_appreciation_12q"})
    eer["large_reer_appreciation"] = (eer["reer_appreciation_12q"] >= 15.0).astype(int)

    panel = credit_gap.merge(credit_level, on=["country", "q", "year"], how="outer")
    panel = panel.merge(
        house[
            [
                "country",
                "q",
                "year",
                "real_house_price",
                "fwd_real_house_price_growth_8q",
                "fwd_real_house_price_growth_12q",
                "lag_real_house_price_growth_8q",
            ]
        ],
        on=["country", "q", "year"],
        how="outer",
    )
    panel = panel.merge(dsr[["country", "q", "year", "household_dsr", "dsr_p75", "high_household_dsr"]], on=["country", "q", "year"], how="outer")
    panel = panel.merge(
        eer[["country", "q", "year", "reer", "reer_appreciation_12q", "fwd_reer_growth_8q", "large_reer_appreciation"]],
        on=["country", "q", "year"],
        how="outer",
    )
    panel["high_credit_gap"] = (panel["credit_gap"] >= 10.0).astype(int)
    return panel


def run_spec(hid: str) -> dict:
    spec = SPECS[hid]
    out_dir = RUNS / hid
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {name: latest(name) for name in ["WS_CREDIT_GAP", "WS_SPP", "WS_DSR", "WS_EER"]}
    panel = build_panel(paths)

    terms = [spec["outcome"], spec["treatment"], spec["continuous"], "country", "year"]
    if "lag_real_house_price_growth_8q" in spec["formula"]:
        terms.append("lag_real_house_price_growth_8q")
    if "lag_credit_growth_8q" in spec["formula"]:
        terms.append("lag_credit_growth_8q")
    model_df = panel[terms].replace([np.inf, -np.inf], np.nan).dropna().copy()
    model_df["year"] = model_df["year"].astype(int)

    n_obs = int(len(model_df))
    n_countries = int(model_df["country"].nunique())
    if n_obs == 0:
        raise RuntimeError(f"{hid}: no usable observations")

    fit = smf.ols(spec["formula"], data=model_df).fit(
        cov_type="cluster", cov_kwds={"groups": model_df["country"]}
    )
    treatment = spec["treatment"]
    coef = float(fit.params[treatment])
    p_value = float(fit.pvalues[treatment])
    se = float(fit.bse[treatment])
    ci_low, ci_high = [float(x) for x in fit.conf_int().loc[treatment].tolist()]

    group = model_df.groupby(treatment)[spec["outcome"]].agg(["mean", "count"]).to_dict("index")
    base_mean = float(group.get(0, {}).get("mean", np.nan))
    high_mean = float(group.get(1, {}).get("mean", np.nan))
    mean_diff = high_mean - base_mean
    high_count = int(group.get(1, {}).get("count", 0))

    gate = spec["gate"]
    enough_data = n_obs >= gate["min_observations"] and n_countries >= gate["min_countries"]
    effect_pass = coef <= gate["coef_max"] and p_value <= gate["p_max"]
    raw_pass = mean_diff <= gate["mean_diff_max"]
    if not enough_data:
        verdict = "inconclusive"
        verdict_detail = "insufficient panel coverage for the predeclared minimum-data gate"
    elif effect_pass and raw_pass:
        verdict = "supported"
        verdict_detail = "regression and raw high-vs-normal contrast both clear the predeclared gates"
    elif effect_pass or raw_pass:
        verdict = "partial"
        verdict_detail = "one of the regression or raw-contrast gates clears, but not both"
    else:
        verdict = "refuted"
        verdict_detail = "neither the regression nor raw-contrast gate clears"

    diagnostics = {
        "hypothesis_id": hid,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "n_observations": n_obs,
        "n_countries": n_countries,
        "treatment": treatment,
        "outcome": spec["outcome"],
        "coefficient": coef,
        "standard_error_cluster_country": se,
        "p_value": p_value,
        "ci95": [ci_low, ci_high],
        "raw_high_minus_normal_mean": mean_diff,
        "normal_mean": base_mean,
        "high_mean": high_mean,
        "high_count": high_count,
        "thresholds": gate,
        "threshold_text": spec["threshold_text"],
        "sample_start_q": int(model_df["year"].min() * 4),
        "sample_end_q": int(model_df["year"].max() * 4 + 4),
    }

    coef_df = pd.DataFrame(
        [
            {
                "hypothesis_id": hid,
                "term": treatment,
                "estimate": coef,
                "std_error": se,
                "p_value": p_value,
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "n_observations": n_obs,
                "n_countries": n_countries,
            },
            {
                "hypothesis_id": hid,
                "term": f"raw_{treatment}_mean_diff",
                "estimate": mean_diff,
                "std_error": np.nan,
                "p_value": np.nan,
                "ci95_low": np.nan,
                "ci95_high": np.nan,
                "n_observations": n_obs,
                "n_countries": n_countries,
            },
        ]
    )
    coef_df.to_parquet(out_dir / "coefficients.parquet", index=False)

    chart_rows = (
        model_df.groupby(["year", treatment], as_index=False)[spec["outcome"]]
        .mean()
        .rename(columns={spec["outcome"]: "mean_outcome"})
        .to_dict("records")
    )
    with (out_dir / "chart_data.json").open("w") as f:
        json.dump({"series": chart_rows}, f, indent=2)
    with (out_dir / "diagnostics.json").open("w") as f:
        json.dump(diagnostics, f, indent=2)

    manifest = {
        "hypothesis_id": hid,
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "runner": "scripts/generate_bis_credit_wave.py",
        "vintages": {
            name: {
                "publisher": "bis",
                "series": name,
                "vintage_file": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
            }
            for name, path in paths.items()
        },
        "formula": spec["formula"],
        "threshold_text": spec["threshold_text"],
    }
    with (out_dir / "manifest.yaml").open("w") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)

    card = f"""# {spec['title']}

**Verdict:** {verdict} — {verdict_detail}.

## Predeclared Test

{spec['threshold_text']}

Decision gates: coefficient on `{treatment}` must be <= {gate['coef_max']} with p <= {gate['p_max']}; raw high-minus-normal mean difference must be <= {gate['mean_diff_max']}; minimum coverage is {gate['min_observations']} observations and {gate['min_countries']} countries.

## Results

- Usable panel: **{n_obs:,} country-quarters**, **{n_countries} countries**.
- Clustered OLS coefficient on `{treatment}`: **{coef:.3f}** (SE {se:.3f}, p={p_value:.4f}, 95% CI [{ci_low:.3f}, {ci_high:.3f}]).
- Raw high-minus-normal outcome mean: **{mean_diff:.3f}** ({high_mean:.3f} vs {base_mean:.3f}); high-stress/high-gap observations: **{high_count:,}**.

## Specification

`{spec['formula']}`

Country fixed effects and calendar-year fixed effects are included. Standard errors are clustered by BIS country code.

## Data

- BIS WS_CREDIT_GAP: credit gap CG_DTYPE=C and broad private credit/GDP CG_DTYPE=B.
- BIS WS_SPP: real residential property-price index, quarterly.
- BIS WS_DSR: household debt-service ratio, quarterly.
- BIS WS_EER: real broad effective exchange-rate index, monthly aggregated to quarterly means.

## Caveats

This is a compact panel screen, not a causal design. The fixed-effects controls remove persistent country differences and common annual shocks, but not time-varying local policy, banking regulation, migration, construction constraints, or terms-of-trade shocks. The test is therefore a falsifiable predictive verdict for the predeclared BIS signal rather than a structural causal estimate.
"""
    (out_dir / "result_card.md").write_text(card)
    return diagnostics


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1] not in SPECS:
        print("Usage: generate_bis_credit_wave.py <hypothesis_id>", file=sys.stderr)
        for hid in SPECS:
            print(f"  {hid}", file=sys.stderr)
        return 2
    diagnostics = run_spec(argv[1])
    print(json.dumps({"hypothesis_id": argv[1], "verdict": diagnostics["verdict"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
