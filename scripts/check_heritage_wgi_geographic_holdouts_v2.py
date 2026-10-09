#!/usr/bin/env python3
"""Read-only replay of the seven pinned WGI geographic holdouts."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import statsmodels.formula.api as smf

import run_heritage_wgi_geographic_holdouts_v2 as holdouts


def close(actual: float, saved: float) -> bool:
    return math.isclose(actual, saved, rel_tol=1e-9, abs_tol=1e-9)


def check_one(hypothesis_id: str) -> dict[str, object]:
    prereg_commit = holdouts.registration_commit(hypothesis_id)
    _, outcome, treatment, _ = holdouts.COHORT[hypothesis_id]
    _, _, run_rel = holdouts.paths(hypothesis_id)
    run_dir = holdouts.ROOT / run_rel
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text())
    manifest = holdouts.yaml.safe_load((run_dir / "manifest.yaml").read_text())
    gate, panel, sources = holdouts.preflight(hypothesis_id)
    if not gate["passed"]:
        raise ValueError(f"registered coverage gate no longer passes: {hypothesis_id}")
    if diagnostics["preregistration_commit"] != prereg_commit:
        raise ValueError(f"preregistration commit changed: {hypothesis_id}")
    if manifest["vintages"] != sources:
        raise ValueError(f"pinned source custody changed: {hypothesis_id}")
    if diagnostics["preflight"] != gate:
        raise ValueError(f"complete-case panel changed: {hypothesis_id}")
    formula = (
        f"{outcome} ~ {treatment} + "
        "log_gdp_pc_ppp + population_growth + trade_openness_control + "
        "government_consumption_share + C(country_iso3) + C(year)"
    )
    fit = smf.ols(formula, data=panel).fit(
        cov_type="cluster",
        cov_kwds={"groups": panel["country_iso3"], "use_correction": True},
    )
    if np.linalg.matrix_rank(fit.model.exog) < fit.model.exog.shape[1]:
        raise ValueError(f"primary design is rank deficient: {hypothesis_id}")
    estimate = diagnostics["estimate"]
    fresh = {
        "coefficient": float(fit.params[treatment]),
        "std_error": float(fit.bse[treatment]),
        "p_value": float(fit.pvalues[treatment]),
        "ci95": [float(x) for x in fit.conf_int().loc[treatment].tolist()],
        "r_squared": float(fit.rsquared),
    }
    for key in ("coefficient", "std_error", "p_value", "r_squared"):
        if not close(fresh[key], estimate[key]):
            raise ValueError(f"stored {key} did not replay: {hypothesis_id}")
    if not all(close(a, b) for a, b in zip(fresh["ci95"], estimate["ci95"])):
        raise ValueError(f"stored confidence interval did not replay: {hypothesis_id}")
    label, _ = holdouts.classify(fresh["coefficient"], fresh["p_value"])
    if label != diagnostics["verdict"] or label != manifest["status"]:
        raise ValueError(f"stored verdict did not replay: {hypothesis_id}")
    if estimate["n_obs"] != len(panel) or estimate["n_countries"] != panel["country_iso3"].nunique():
        raise ValueError(f"stored sample did not replay: {hypothesis_id}")
    return {"hypothesis_id": hypothesis_id, "verdict": label, "observations": len(panel), "read_only": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("hypothesis_id", choices=[*holdouts.COHORT, "all"])
    args = parser.parse_args()
    ids = list(holdouts.COHORT) if args.hypothesis_id == "all" else [args.hypothesis_id]
    results = [check_one(hypothesis_id) for hypothesis_id in ids]
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
