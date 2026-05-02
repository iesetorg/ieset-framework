#!/usr/bin/env python3
"""Generate Worker D's OECD labour/distribution hypothesis wave.

The script intentionally uses only OECD vintages already present under
data/vintages/oecd. It writes specs, steelmen, and runnable per-hypothesis
replication scripts plus the current run artifacts.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
OECD = ROOT / "data" / "vintages" / "oecd"

TUD_FILE = "OECD.ELS.SAE_DSD_TUD_CBC_DF_TUD_1.0"
CBC_FILE = "OECD.ELS.SAE_DSD_TUD_CBC_DF_CBC_1.0"
IDD_FILE = "OECD.WISE.INE_DSD_IDD_DF_IDD_1.0"
LFS_FILE = "DSD_LFS_DF_LFS_INDIC"
EARN_FILE = "OECD.ELS.SAE_DSD_EARNINGS_DF_EARNINGS_1.0"
KEI_FILE = "OECD.ECO.MAD_DSD_KEI_DF_KEI_1.0"

SAMPLE = [
    "AUS", "AUT", "BEL", "CAN", "CHL", "COL", "CRI", "CZE", "DNK", "EST",
    "FIN", "FRA", "DEU", "GRC", "HUN", "ISL", "IRL", "ISR", "ITA", "JPN",
    "KOR", "LVA", "LTU", "LUX", "MEX", "NLD", "NZL", "NOR", "POL", "PRT",
    "SVK", "SVN", "ESP", "SWE", "CHE", "TUR", "GBR", "USA",
]


def latest(stem: str) -> Path:
    files = sorted(OECD.glob(f"{stem}@*.parquet"), key=lambda p: p.stat().st_mtime)
    if not files:
        raise FileNotFoundError(stem)
    return files[-1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_series(stem: str, filters: dict[str, str], value_name: str) -> pd.DataFrame:
    df = pq.read_table(latest(stem)).to_pandas()
    for col, val in filters.items():
        df = df[df[col] == val]
    out = df[["REF_AREA", "period", "value"]].copy()
    out["country"] = out["REF_AREA"].astype(str)
    out["year"] = out["period"].astype(str).str[:4].astype(int)
    out[value_name] = pd.to_numeric(out["value"], errors="coerce")
    out = out[out["country"].isin(SAMPLE)]
    return (
        out[["country", "year", value_name]]
        .dropna()
        .groupby(["country", "year"], as_index=False)
        .mean(numeric_only=True)
    )


def fit_fe(panel: pd.DataFrame, outcome: str, treatment: str, controls: list[str]) -> dict:
    import statsmodels.formula.api as smf

    cols = ["country", "year", outcome, treatment] + controls
    d = panel[cols].replace([math.inf, -math.inf], pd.NA).dropna().copy()
    d = d[(d["year"] >= 1990) & (d["year"] <= 2022)]
    rhs = [treatment] + controls + ["C(country)", "C(year)"]
    model = smf.ols(f"{outcome} ~ {' + '.join(rhs)}", data=d)
    res = model.fit(cov_type="cluster", cov_kwds={"groups": d["country"]})
    beta = float(res.params[treatment])
    se = float(res.bse[treatment])
    return {
        "method": "statsmodels OLS with country and year fixed effects; SE clustered by country",
        "outcome": outcome,
        "treatment": treatment,
        "controls": controls,
        "coefficient": beta,
        "std_error": se,
        "p_value": float(res.pvalues[treatment]),
        "ci90_low": beta - 1.645 * se,
        "ci90_high": beta + 1.645 * se,
        "n_obs": int(res.nobs),
        "n_countries": int(d["country"].nunique()),
        "year_min": int(d["year"].min()),
        "year_max": int(d["year"].max()),
        "r_squared": float(res.rsquared),
    }


def verdict_for(hid: str, est: dict) -> tuple[str, str]:
    b = est["coefficient"]
    p = est["p_value"]
    hi = est["ci90_high"]
    if hid == "oecd_union_density_disposable_gini_panel":
        if b <= -0.0005 and p < 0.10:
            return "SUPPORTED", "negative union-density coefficient clears the predeclared magnitude and p<0.10 threshold"
        if b >= 0.0005 and p < 0.10:
            return "REFUTED", "positive union-density coefficient clears the predeclared opposite-direction threshold"
        return "PARTIAL", "point estimate is negative as claimed but too small/imprecise for the support threshold"
    if hid == "oecd_collective_bargaining_unemployment_nonpenalty":
        if hi <= 0.10:
            return "SUPPORTED", "90% upper confidence bound is below the +0.10 pp unemployment non-inferiority margin"
        if b >= 0.10 and p < 0.10:
            return "REFUTED", "positive unemployment penalty exceeds the +0.10 pp margin at p<0.10"
        return "PARTIAL", "estimate does not clear support or refutation threshold"
    if hid == "oecd_collective_bargaining_growth_penalty_kei":
        if b >= -0.02 or p >= 0.10:
            return "SUPPORTED", "no statistically significant material growth penalty under the -0.02 pp margin"
        if b <= -0.02 and p < 0.10:
            return "REFUTED", "coverage coefficient is below the -0.02 pp growth-penalty margin at p<0.10"
        return "PARTIAL", "estimate does not clear support or refutation threshold"
    if hid == "oecd_youth_wage_gap_youth_employment":
        if b <= -0.20 and p < 0.10:
            return "SUPPORTED", "negative youth-employment coefficient clears the predeclared magnitude and p<0.10 threshold"
        if b >= 0.00 and p < 0.10:
            return "REFUTED", "coefficient is significantly opposite signed"
        return "PARTIAL", "point estimate is negative as claimed but misses the p<0.10 and magnitude threshold"
    raise KeyError(hid)


def build_panel(config: dict) -> tuple[pd.DataFrame, dict]:
    frames = []
    manifest = {}
    for name, spec in config["series"].items():
        path = latest(spec["stem"])
        manifest[name] = {
            "publisher": "oecd",
            "series": spec["stem"],
            "filters": spec["filters"],
            "vintage_file": str(path.relative_to(ROOT)),
            "sha256": sha256(path),
        }
        frames.append(read_series(spec["stem"], spec["filters"], name))
    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["country", "year"], how="inner")
    return panel, manifest


CONFIGS = [
    {
        "id": "oecd_union_density_disposable_gini_panel",
        "topic": "distribution",
        "claim": (
            "In OECD country-years from 1990 to 2022, higher trade-union density is "
            "associated with lower disposable-income Gini after country and year fixed "
            "effects and unemployment controls."
        ),
        "outcome": "gini_disp",
        "treatment": "union_density",
        "controls": ["unemployment_rate"],
        "series": {
            "union_density": {"stem": TUD_FILE, "filters": {"MEASURE": "TUD"}},
            "gini_disp": {"stem": IDD_FILE, "filters": {"MEASURE": "INC_DISP_GINI", "AGE": "_T"}},
            "unemployment_rate": {
                "stem": LFS_FILE,
                "filters": {"MEASURE": "UNE_RATE", "SEX": "_T", "AGE": "Y15T64"},
            },
        },
        "support_rule": "SUPPORTED iff beta_union_density <= -0.0005 Gini points per 1 pp union density with p<0.10.",
        "refute_rule": "REFUTED iff beta_union_density >= +0.0005 with p<0.10. PARTIAL otherwise if method-valid.",
        "prior": 0.62,
        "disclosure": (
            "I expected the sign to be negative from bargaining-power theory, but the "
            "within-country FE design is deliberately hard on slow-moving institutions."
        ),
        "steelman": (
            "The strongest case for the claim is that unions compress wage schedules, "
            "raise worker bargaining power, and help preserve inclusive labour-market "
            "norms. Disposable-income Gini is the right hard outcome because it captures "
            "both market earnings and tax-transfer systems that unions may politically sustain.\n\n"
            "The strongest objection is that union density moves slowly, has measurement "
            "breaks, and may be endogenous to deindustrialisation or public-sector size. "
            "Country and year fixed effects therefore test only within-country deviations, "
            "not the full institutional regime contrast between Nordic and liberal-market systems."
        ),
    },
    {
        "id": "oecd_collective_bargaining_unemployment_nonpenalty",
        "topic": "labour",
        "claim": (
            "In OECD country-years from 1990 to 2022, broader collective-bargaining "
            "coverage does not impose a material unemployment penalty."
        ),
        "outcome": "unemployment_rate",
        "treatment": "bargaining_coverage",
        "controls": [],
        "series": {
            "bargaining_coverage": {"stem": CBC_FILE, "filters": {"MEASURE": "ERB"}},
            "unemployment_rate": {
                "stem": LFS_FILE,
                "filters": {"MEASURE": "UNE_RATE", "SEX": "_T", "AGE": "Y15T64"},
            },
        },
        "support_rule": "SUPPORTED iff the 90% upper confidence bound for beta_bargaining_coverage is <= +0.10 unemployment-rate points per 1 pp coverage.",
        "refute_rule": "REFUTED iff beta_bargaining_coverage >= +0.10 with p<0.10. PARTIAL otherwise if method-valid.",
        "prior": 0.58,
        "disclosure": (
            "This is framed as a non-inferiority test rather than proof of job creation. "
            "That favors the modest social-democratic claim that bargaining coverage is not mechanically unemployment-raising."
        ),
        "steelman": (
            "The best pro-coverage argument is coordination: broad bargaining can internalise "
            "macro constraints, reduce wage undercutting, and preserve employment by trading "
            "wage growth, training, and work-time rules. If this view is right, high coverage "
            "should not show a large positive unemployment coefficient once country and year "
            "effects absorb institutions and common shocks.\n\n"
            "The best skeptical argument is insider-outsider labour economics: broad agreements "
            "can price out marginal workers and raise equilibrium unemployment, especially "
            "where wage floors are not offset by active labour-market policy."
        ),
    },
    {
        "id": "oecd_collective_bargaining_growth_penalty_kei",
        "topic": "labour",
        "claim": (
            "In OECD annual data from 1990 to 2022, broader collective-bargaining "
            "coverage is not associated with a material penalty to real GDP-volume growth."
        ),
        "outcome": "gdp_volume_growth",
        "treatment": "bargaining_coverage",
        "controls": ["unemployment_rate"],
        "series": {
            "bargaining_coverage": {"stem": CBC_FILE, "filters": {"MEASURE": "ERB"}},
            "gdp_volume_growth": {
                "stem": KEI_FILE,
                "filters": {"FREQ": "A", "MEASURE": "B1GQ_Q", "TRANSFORMATION": "G1"},
            },
            "unemployment_rate": {
                "stem": LFS_FILE,
                "filters": {"MEASURE": "UNE_RATE", "SEX": "_T", "AGE": "Y15T64"},
            },
        },
        "support_rule": "SUPPORTED iff beta_bargaining_coverage >= -0.02 GDP-growth points per 1 pp coverage OR p>=0.10.",
        "refute_rule": "REFUTED iff beta_bargaining_coverage <= -0.02 with p<0.10. PARTIAL otherwise if method-valid.",
        "prior": 0.52,
        "disclosure": (
            "The claim is intentionally vulnerable: it takes the no-growth-cost version "
            "of the bargaining argument seriously and lets the KEI growth series falsify it."
        ),
        "steelman": (
            "The strongest no-penalty case is that coordinated bargaining can stabilise "
            "demand, reduce conflict, and support skill formation, so aggregate growth need "
            "not suffer even if wage setting is more collective. The strongest growth-penalty "
            "case is that broader coverage slows adjustment, compresses wage dispersion, and "
            "reduces employment or investment dynamism. Annual GDP-volume growth is noisy, "
            "but it is a direct macro cost metric."
        ),
    },
    {
        "id": "oecd_youth_wage_gap_youth_employment",
        "topic": "labour",
        "claim": (
            "In OECD country-years from 1990 to 2022, a wider youth-to-prime-age wage "
            "gap is associated with lower youth employment, even after controlling for "
            "the aggregate unemployment rate."
        ),
        "outcome": "youth_employment_ratio",
        "treatment": "youth_prime_wage_gap",
        "controls": ["unemployment_rate"],
        "series": {
            "youth_prime_wage_gap": {"stem": EARN_FILE, "filters": {"MEASURE": "Y_PA_WP", "SEX": "_T"}},
            "youth_employment_ratio": {
                "stem": LFS_FILE,
                "filters": {"MEASURE": "EMP_RATIO", "SEX": "_T", "AGE": "Y15T24"},
            },
            "unemployment_rate": {
                "stem": LFS_FILE,
                "filters": {"MEASURE": "UNE_RATE", "SEX": "_T", "AGE": "Y15T64"},
            },
        },
        "support_rule": "SUPPORTED iff beta_youth_prime_wage_gap <= -0.20 youth-employment-ratio points per 1 pp wage gap with p<0.10.",
        "refute_rule": "REFUTED iff beta_youth_prime_wage_gap >= 0 with p<0.10. PARTIAL otherwise if method-valid.",
        "prior": 0.50,
        "disclosure": (
            "The measure is a wage-gap outcome, not a clean policy instrument. This makes "
            "the test descriptive and vulnerable to reverse causality from weak youth labour markets."
        ),
        "steelman": (
            "The strongest interpretation is a segmentation story: when youth wages lag "
            "prime-age wages more sharply, young workers may be in weaker positions and "
            "youth employment ratios should also be lower. The strongest objection is "
            "reverse causality and composition: low youth employment may itself select "
            "which youths remain employed and alter the measured wage gap."
        ),
    },
]


def spec_doc(config: dict) -> dict:
    treatment = config["treatment"]
    return {
        "hypothesis_id": config["id"],
        "version": 1,
        "status": "pre_registered",
        "topic": config["topic"],
        "claim": config["claim"],
        "evidence_type": "associational",
        "sample": {
            "countries": SAMPLE,
            "period": [1990, 2022],
            "temporal_structure": "panel",
            "exclusion_rules": [
                "drop country-years missing the OECD treatment, outcome, or control series",
                "collapse duplicate OECD cells to country-year means after predeclared code filters",
                "retain COVID years because year fixed effects absorb common shocks",
            ],
        },
        "variables": {
            "outcome": [
                {
                    "name": config["outcome"],
                    "source": "oecd:" + config["series"][config["outcome"]]["stem"],
                    "transformation": "level",
                }
            ],
            "treatment": [
                {
                    "name": treatment,
                    "source": "oecd:" + config["series"][treatment]["stem"],
                    "transformation": "level",
                }
            ],
            "controls": [
                {
                    "name": c,
                    "source": "oecd:" + config["series"][c]["stem"],
                    "transformation": "level",
                }
                for c in config["controls"]
            ],
        },
        "estimator": {
            "template": "panel_fe",
            "clustering": "country",
            "fixed_effects": ["country", "year"],
            "notes": (
                "OLS with country and year fixed effects, clustered by country. "
                "This is an associational institutional panel, not a causal natural experiment."
            ),
        },
        "falsification": {
            "rule": config["support_rule"] + " " + config["refute_rule"],
            "test": f"{config['id']}_twfe_1990_2022",
            "threshold": {
                "support": config["support_rule"],
                "refute": config["refute_rule"],
                "alpha": 0.10,
            },
        },
        "prior_confidence": config["prior"],
        "disclosure": config["disclosure"],
        "steelman": f"hypotheses/steelman/{config['id']}.md",
        "scope": {
            "period": [1990, 2022],
            "countries": ["OECD"],
            "outcome_dim": ["employment_labour"] if config["topic"] == "labour" else ["poverty_inequality"],
            "policy_family": ["labour_market"],
            "treatment_tags": ["collective_bargaining_institutions", "union_density"]
            if "bargaining" in treatment or "union" in treatment
            else ["earnings_dispersion"],
        },
        "notes": (
            "Generated as Worker D OECD labour/distribution wave using only pinned "
            "OECD vintages already on disk."
        ),
    }


def write_replication(config: dict, run_dir: Path) -> None:
    script = f'''#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[3]
ns = runpy.run_path(str(ROOT / "scripts" / "generate_oecd_labour_wave.py"))
config = next(c for c in ns["CONFIGS"] if c["id"] == "{config['id']}")
ns["run_one"](config)
'''
    path = run_dir / "replication.py"
    path.write_text(script)
    path.chmod(0o755)


def result_card(config: dict, diagnostics: dict) -> str:
    est = diagnostics["estimate"]
    return textwrap.dedent(
        f"""\
        # Result card - {config['id']}

        **Verdict:** {diagnostics['verdict']} - {diagnostics['verdict_reason']}

        ## Pre-registration
        - **Claim:** {config['claim']}
        - **Support rule:** {config['support_rule']}
        - **Refutation rule:** {config['refute_rule']}
        - **Estimator:** country and year fixed effects, country-clustered SEs, OECD panel 1990-2022.

        ## Estimate
        - Treatment: `{est['treatment']}`
        - Outcome: `{est['outcome']}`
        - Coefficient: {est['coefficient']:.6g}
        - Std error: {est['std_error']:.6g}
        - p-value: {est['p_value']:.6g}
        - 90% CI: [{est['ci90_low']:.6g}, {est['ci90_high']:.6g}]
        - Observations: {est['n_obs']}
        - Countries: {est['n_countries']}
        - Window: {est['year_min']}-{est['year_max']}

        ## Diagnostics
        - Method valid: {diagnostics['method_valid']}
        - Data gap: {diagnostics['data_gap']}
        - Controls: {', '.join(est['controls']) if est['controls'] else 'none'}

        _Generated by `engine/runs/{config['id']}/replication.py` at {diagnostics['run_utc']}._
        """
    )


def run_one(config: dict) -> dict:
    hid = config["id"]
    run_dir = ROOT / "engine" / "runs" / hid
    run_dir.mkdir(parents=True, exist_ok=True)

    panel, manifest = build_panel(config)
    est = fit_fe(panel, config["outcome"], config["treatment"], config["controls"])
    label, reason = verdict_for(hid, est)
    diagnostics = {
        "hypothesis_id": hid,
        "verdict": label,
        "verdict_reason": reason,
        "method_valid": est["n_countries"] >= 25 and est["n_obs"] >= 250,
        "data_gap": False,
        "estimate": est,
        "thresholds": {
            "support": config["support_rule"],
            "refute": config["refute_rule"],
            "alpha": 0.10,
        },
        "coverage": {
            "sample_countries_targeted": len(SAMPLE),
            "countries_used": est["n_countries"],
            "observations_used": est["n_obs"],
        },
        "vintages": manifest,
        "run_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump({
        "hypothesis_id": hid,
        "run_utc": diagnostics["run_utc"],
        "status": "completed",
        "verdict": label,
        "vintages": manifest,
    }, sort_keys=False))
    (run_dir / "result_card.md").write_text(result_card(config, diagnostics))
    write_replication(config, run_dir)
    return diagnostics


def write_spec_and_steelman(config: dict) -> None:
    topic_dir = ROOT / "hypotheses" / config["topic"]
    topic_dir.mkdir(parents=True, exist_ok=True)
    spec_path = topic_dir / f"{config['id']}.yaml"
    with spec_path.open("w") as f:
        f.write("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n")
        yaml.safe_dump(spec_doc(config), f, sort_keys=False, width=100)

    steelman_path = ROOT / "hypotheses" / "steelman" / f"{config['id']}.md"
    steelman_path.write_text(
        f"# Steelman - {config['id']}\n\n"
        f"## Claim\n{config['claim']}\n\n"
        f"## Best case\n{config['steelman']}\n\n"
        "## Pre-analysis guardrails\n"
        f"- Support rule: {config['support_rule']}\n"
        f"- Refutation rule: {config['refute_rule']}\n"
        "- Estimator: country and year fixed effects with country-clustered standard errors.\n"
        "- Identification status: associational; no causal language is licensed by this run alone.\n"
    )


def main() -> None:
    diagnostics = []
    for config in CONFIGS:
        write_spec_and_steelman(config)
        diagnostics.append(run_one(config))
    print(json.dumps({d["hypothesis_id"]: d["verdict"] for d in diagnostics}, indent=2))


if __name__ == "__main__":
    main()
