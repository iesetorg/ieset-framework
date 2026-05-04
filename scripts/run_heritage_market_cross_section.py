#!/usr/bin/env python3
"""Run Heritage IEF top-vs-bottom market-freedom cross-section screens.

These are exploratory candidate screens, not causal designs. Each run compares
the top quartile of countries on a pre-registered Heritage component against
the bottom quartile on a latest-available WDI outcome.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_panel_fe

RUNS = ROOT / "engine" / "runs"
HYPOTHESES = ROOT / "hypotheses"


def find_spec(hypothesis_id: str) -> Path:
    matches = [
        path
        for path in HYPOTHESES.glob("*/*.yaml")
        if path.stem == hypothesis_id and path.parent.name != "steelman"
    ]
    if not matches:
        raise FileNotFoundError(f"hypothesis spec not found: {hypothesis_id}")
    return matches[0]


def load_spec(hypothesis_id: str) -> dict:
    path = find_spec(hypothesis_id)
    return yaml.safe_load(path.read_text()) or {}


def latest_panel(publisher: str, series: str) -> tuple[pd.DataFrame, Path]:
    path = run_panel_fe.latest_vintage(publisher, series)
    if path is None:
        raise FileNotFoundError(f"no vintage for {publisher}:{series}")
    return pd.read_parquet(path), path


def outcome_panel(source: str) -> tuple[pd.DataFrame, str]:
    loaded = run_panel_fe.load_variable(source)
    if loaded is None:
        raise FileNotFoundError(f"no loadable outcome source: {source}")
    return loaded


def latest_by_country(
    panel: pd.DataFrame,
    *,
    value_col: str = "value",
    max_year: int | None = None,
    min_year: int | None = None,
) -> pd.DataFrame:
    frame = panel.dropna(subset=["country_iso3", "year", value_col]).copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[value_col] = pd.to_numeric(frame[value_col], errors="coerce")
    frame = frame.dropna(subset=["year", value_col])
    if max_year is not None:
        frame = frame[frame["year"] <= max_year]
    if min_year is not None:
        frame = frame[frame["year"] >= min_year]
    if frame.empty:
        return frame
    idx = frame.groupby("country_iso3")["year"].idxmax()
    return frame.loc[idx, ["country_iso3", "year", value_col]].rename(columns={value_col: "value"})


def welch_p_value(a: pd.Series, b: pd.Series) -> float | None:
    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()
    if len(a) < 3 or len(b) < 3:
        return None
    return float(stats.ttest_ind(a, b, equal_var=False, nan_policy="omit").pvalue)


def _safe_slug(value: object) -> str:
    text = str(value or "").strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in text).strip("_")


def add_latest_control(
    merged: pd.DataFrame,
    *,
    source: str,
    name: str,
    max_year: int,
    min_year: int,
) -> pd.DataFrame:
    panel, _ = outcome_panel(source)
    latest = latest_by_country(panel, max_year=max_year, min_year=min_year).rename(
        columns={"value": name, "year": f"{name}_year"}
    )
    return merged.merge(latest, on="country_iso3", how="left")


def controlled_ols(
    frame: pd.DataFrame,
    *,
    y_col: str,
    x_col: str,
    control_cols: list[str],
    categorical_cols: list[str],
) -> dict:
    cols = [y_col, x_col, *control_cols, *categorical_cols]
    df = frame[cols].dropna().copy()
    if len(df) < 12:
        return {"n": int(len(df)), "coef": None, "p_value": None, "control_columns": []}

    work = pd.DataFrame(
        {
            "y": pd.to_numeric(df[y_col], errors="coerce"),
            "market_score": pd.to_numeric(df[x_col], errors="coerce"),
        }
    ).dropna()
    for col in control_cols:
        work[col] = pd.to_numeric(df.loc[work.index, col], errors="coerce")
    work = work.dropna()
    if len(work) < 12:
        return {"n": int(len(work)), "coef": None, "p_value": None, "control_columns": []}

    pieces = [pd.Series(1.0, index=work.index, name="const")]
    market_std = work["market_score"].std()
    if not market_std or np.isnan(market_std):
        return {"n": int(len(work)), "coef": None, "p_value": None, "control_columns": []}
    pieces.append(((work["market_score"] - work["market_score"].mean()) / market_std).rename("market_score_z"))

    used_controls: list[str] = []
    for col in control_cols:
        series = work[col]
        std = series.std()
        if not std or np.isnan(std):
            continue
        pieces.append(((series - series.mean()) / std).rename(col))
        used_controls.append(col)

    for col in categorical_cols:
        cats = df.loc[work.index, col].map(_safe_slug)
        dummies = pd.get_dummies(cats, prefix=col, drop_first=True, dtype=float)
        for dummy_col in dummies.columns:
            pieces.append(dummies[dummy_col])
            used_controls.append(dummy_col)

    design = pd.concat(pieces, axis=1)
    keep = [c for c in design.columns if c == "const" or design[c].std() > 0]
    design = design[keep]
    n, k = design.shape
    if n <= k + 2:
        return {"n": int(n), "coef": None, "p_value": None, "control_columns": used_controls}

    xmat = design.to_numpy(dtype=float)
    yvec = work.loc[design.index, "y"].to_numpy(dtype=float)
    beta, *_ = np.linalg.lstsq(xmat, yvec, rcond=None)
    resid = yvec - xmat @ beta
    rank = np.linalg.matrix_rank(xmat)
    dof = n - rank
    if dof <= 0:
        return {"n": int(n), "coef": None, "p_value": None, "control_columns": used_controls}
    sigma2 = float((resid @ resid) / dof)
    xtx_inv = np.linalg.pinv(xmat.T @ xmat)
    se = np.sqrt(np.diag(xtx_inv) * sigma2)
    market_idx = list(design.columns).index("market_score_z")
    coef = float(beta[market_idx])
    if se[market_idx] <= 0 or np.isnan(se[market_idx]):
        p_value = None
        t_stat = None
    else:
        t_stat = float(coef / se[market_idx])
        p_value = float(2 * stats.t.sf(abs(t_stat), dof))
    return {
        "n": int(n),
        "coef": coef,
        "std_error": None if np.isnan(se[market_idx]) else float(se[market_idx]),
        "t_stat": t_stat,
        "p_value": p_value,
        "degrees_of_freedom": int(dof),
        "control_columns": used_controls,
        "design_columns": list(design.columns),
    }


def run_one(hypothesis_id: str) -> dict:
    spec = load_spec(hypothesis_id)
    threshold = (spec.get("falsification") or {}).get("threshold") or {}
    component = threshold.get("treatment_component") or "overall_score"
    expected_sign = threshold.get("expected_sign") or "+"
    p_max = float(threshold.get("p_value", 0.10))
    quantile = float(threshold.get("tail_quantile", 0.25))
    min_outcome_year = int(threshold.get("min_outcome_year", 2018))
    requested_market_year = threshold.get("market_score_year")
    robustness_design = threshold.get("robustness_design") or "quartile_gap"

    outcome_item = ((spec.get("variables") or {}).get("outcome") or [{}])[0]
    outcome_source = outcome_item.get("source")
    if not outcome_source:
        raise ValueError("missing outcome source")

    heritage, heritage_path = latest_panel("heritage_ief", "ief_panel")
    if component not in heritage.columns:
        raise ValueError(f"component {component!r} not in Heritage panel columns")
    latest_heritage_year = int(pd.to_numeric(heritage["year"], errors="coerce").max())
    market_score_year = int(requested_market_year or latest_heritage_year)
    freedom = latest_by_country(
        heritage[["country_iso3", "year", component]].rename(columns={component: "value"}),
        value_col="value",
        max_year=market_score_year,
    ).rename(columns={"value": "market_score", "year": "market_score_year"})
    heritage_region = (
        heritage.loc[pd.to_numeric(heritage["year"], errors="coerce") == market_score_year, ["country_iso3", "region"]]
        .dropna(subset=["country_iso3"])
        .drop_duplicates("country_iso3")
    )
    freedom = freedom.merge(heritage_region, on="country_iso3", how="left")

    out_panel, outcome_pub = outcome_panel(outcome_source)
    outcome_latest = latest_by_country(
        out_panel,
        max_year=min(2024, int((spec.get("sample") or {}).get("period", [2024, 2026])[-1])),
        min_year=min_outcome_year,
    ).rename(columns={"value": "outcome", "year": "outcome_year"})

    merged = freedom.merge(outcome_latest, on="country_iso3", how="inner").dropna()
    sample_countries = set((spec.get("sample") or {}).get("countries") or [])
    if sample_countries:
        merged = merged[merged["country_iso3"].isin(sample_countries)]

    controls_used: list[str] = []
    categorical_controls: list[str] = []
    ols_result: dict | None = None
    if robustness_design == "ols_income_region":
        merged = add_latest_control(
            merged,
            source=threshold.get("income_control_source", "world_bank_wdi:NY.GDP.PCAP.PP.KD"),
            name="gdp_pc_ppp_control",
            max_year=2024,
            min_year=min_outcome_year,
        )
        merged["log_gdp_pc_ppp_control"] = np.log(pd.to_numeric(merged["gdp_pc_ppp_control"], errors="coerce"))
        controls_used = ["log_gdp_pc_ppp_control"]
        if bool(threshold.get("region_fixed_effects", True)):
            categorical_controls = ["region"]
        ols_result = controlled_ols(
            merged,
            y_col="outcome",
            x_col="market_score",
            control_cols=controls_used,
            categorical_cols=categorical_controls,
        )

    low_cut = float(merged["market_score"].quantile(quantile)) if not merged.empty else float("nan")
    high_cut = float(merged["market_score"].quantile(1 - quantile)) if not merged.empty else float("nan")
    low = merged[merged["market_score"] <= low_cut].copy()
    high = merged[merged["market_score"] >= high_cut].copy()

    mean_high = float(high["outcome"].mean()) if not high.empty else None
    mean_low = float(low["outcome"].mean()) if not low.empty else None
    diff = None if mean_high is None or mean_low is None else mean_high - mean_low
    p_value = welch_p_value(high["outcome"], low["outcome"])
    sign_ok = (diff is not None) and ((diff > 0 and expected_sign == "+") or (diff < 0 and expected_sign == "-"))
    sign_bad = (diff is not None) and ((diff < 0 and expected_sign == "+") or (diff > 0 and expected_sign == "-"))
    decisive = p_value is not None and p_value <= p_max

    if robustness_design == "ols_income_region":
        coef = None if ols_result is None else ols_result.get("coef")
        controlled_p = None if ols_result is None else ols_result.get("p_value")
        controlled_n = 0 if ols_result is None else int(ols_result.get("n") or 0)
        controlled_sign_ok = (coef is not None) and (
            (coef > 0 and expected_sign == "+") or (coef < 0 and expected_sign == "-")
        )
        controlled_sign_bad = (coef is not None) and (
            (coef < 0 and expected_sign == "+") or (coef > 0 and expected_sign == "-")
        )
        controlled_decisive = controlled_p is not None and controlled_p <= p_max
        if controlled_n < 20:
            verdict_label = "INCONCLUSIVE_DATA_PENDING"
            reason = f"insufficient controlled OLS coverage (n={controlled_n})"
        elif controlled_sign_ok and controlled_decisive:
            verdict_label = "SUPPORTED"
            reason = f"controlled market-score coefficient has expected sign {expected_sign} and p={controlled_p:.4g}"
        elif controlled_sign_bad and controlled_decisive:
            verdict_label = "REFUTED"
            reason = f"controlled market-score coefficient has opposite sign and p={controlled_p:.4g}"
        else:
            verdict_label = "PARTIAL"
            p_text = "n/a" if controlled_p is None else f"{controlled_p:.4g}"
            coef_text = "n/a" if coef is None else f"{coef:.4g}"
            reason = f"controlled coefficient not decisive (coef={coef_text}, p={p_text})"
    elif len(high) < 5 or len(low) < 5:
        verdict_label = "INCONCLUSIVE_DATA_PENDING"
        reason = f"insufficient top/bottom quartile coverage (high={len(high)}, low={len(low)})"
    elif sign_ok and decisive:
        verdict_label = "SUPPORTED"
        reason = f"top-vs-bottom gap has expected sign {expected_sign} and Welch p={p_value:.4g}"
    elif sign_bad and decisive:
        verdict_label = "REFUTED"
        reason = f"top-vs-bottom gap has opposite sign and Welch p={p_value:.4g}"
    else:
        verdict_label = "PARTIAL"
        p_text = "n/a" if p_value is None else f"{p_value:.4g}"
        diff_text = "n/a" if diff is None else f"{diff:.4g}"
        reason = f"gap sign/magnitude not decisive (diff={diff_text}, p={p_text})"

    out_dir = RUNS / hypothesis_id
    out_dir.mkdir(parents=True, exist_ok=True)
    chart = merged.sort_values("market_score", ascending=False)
    chart.to_json(out_dir / "chart_data.json", orient="records", indent=2)
    diagnostics = {
        "verdict": f"{verdict_label} — {reason}",
        "verdict_label": verdict_label,
        "verdict_reason": reason,
        "hypothesis_id": hypothesis_id,
        "template": "heritage_market_cross_section",
        "robustness_design": robustness_design,
        "treatment_component": component,
        "expected_sign": expected_sign,
        "tail_quantile": quantile,
        "market_score_year": market_score_year,
        "latest_heritage_release_year": latest_heritage_year,
        "n_merged_countries": int(len(merged)),
        "n_high_market": int(len(high)),
        "n_low_market": int(len(low)),
        "high_cutoff": high_cut,
        "low_cutoff": low_cut,
        "mean_high_market_outcome": mean_high,
        "mean_low_market_outcome": mean_low,
        "difference_high_minus_low": diff,
        "welch_p_value": p_value,
        "controlled_ols": ols_result,
        "controls_used": controls_used,
        "categorical_controls": categorical_controls,
        "outcome_source": outcome_source,
        "outcome_publisher_resolved": outcome_pub,
        "runner": "scripts/run_heritage_market_cross_section.py",
    }
    (out_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

    manifest = {
        "hypothesis_id": hypothesis_id,
        "runner": "scripts/run_heritage_market_cross_section.py",
        "vintages": [
            str(heritage_path.relative_to(ROOT)),
        ],
        "outcome_source": outcome_source,
    }
    (out_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False))

    card = [
        f"# Result card — {hypothesis_id}",
        "",
        f"**Verdict:** {diagnostics['verdict']}",
        "",
        "## Design",
        f"- Heritage component: `{component}` using release year `{market_score_year}`.",
        f"- Design: `{robustness_design}`.",
        f"- Uncontrolled comparison: top `{quantile:.0%}` vs bottom `{quantile:.0%}` of market-score countries.",
        f"- Outcome source: `{outcome_source}` latest available country observation since `{min_outcome_year}`.",
        "",
        "## Estimate",
        f"- High-market mean: `{mean_high}` over `{len(high)}` countries.",
        f"- Low-market mean: `{mean_low}` over `{len(low)}` countries.",
        f"- Difference, high minus low: `{diff}`.",
        f"- Welch p-value: `{p_value}`.",
    ]
    if ols_result is not None:
        card.extend(
            [
                "",
                "## Controlled Robustness",
                f"- Controls: `{controls_used}` plus categorical `{categorical_controls}`.",
                f"- Controlled OLS n: `{ols_result.get('n')}`.",
                f"- Market-score coefficient, standardized score: `{ols_result.get('coef')}`.",
                f"- Controlled p-value: `{ols_result.get('p_value')}`.",
            ]
        )
    card.extend(
        [
            "",
            "## Caveat",
            "This is a candidate cross-sectional screen. It is useful for broad Austrian/ordoliberal market-order triage, but it is not a causal design and should not be scoreboard-promoted without robustness checks.",
        ]
    )
    (out_dir / "result_card.md").write_text("\n".join(card) + "\n")

    replication = (
        "#!/usr/bin/env python3\n"
        "import subprocess, sys\n"
        f"raise SystemExit(subprocess.call([sys.executable, 'scripts/run_heritage_market_cross_section.py', '{hypothesis_id}']))\n"
    )
    (out_dir / "replication.py").write_text(replication)
    return diagnostics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("hypothesis_id", nargs="*")
    parser.add_argument("--from-file", help="newline-delimited hypothesis IDs to run")
    args = parser.parse_args()
    hypothesis_ids = list(args.hypothesis_id)
    if args.from_file:
        hypothesis_ids.extend(
            line.strip()
            for line in Path(args.from_file).read_text().splitlines()
            if line.strip() and not line.strip().startswith("#")
        )
    if not hypothesis_ids:
        parser.error("provide hypothesis IDs or --from-file")
    for hypothesis_id in hypothesis_ids:
        diag = run_one(hypothesis_id)
        print(f"{hypothesis_id}: {diag['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
