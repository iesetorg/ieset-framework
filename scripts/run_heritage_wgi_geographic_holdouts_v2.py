#!/usr/bin/env python3
"""Run seven preregistered, country-disjoint WGI/WDI panel holdouts.

Preflight verifies pinned hashes and complete-case coverage only. Estimation
requires the specs, steelmans, and this runner to exist unchanged in HEAD.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_heritage_wgi_geographic_holdouts_v2.py"
FAMILY_P_MAX = 0.10 / 7  # Bonferroni over the complete seven-claim cohort.
MIN_OBSERVATIONS = 1_000
MIN_COUNTRIES = 50
OLD_COUNTRIES = frozenset(
    "ARG AUS AUT BEL BRA CAN CHE CHL CHN COL CRI CZE DEU DNK EGY ESP EST "
    "FIN FRA GBR GHA GRC HUN IDN IND IRL ISR ITA JPN KEN KOR LTU LVA MAR "
    "MEX MYS NGA NLD NOR NZL PER PHL POL PRT SGP SVK SVN SWE THA TUR URY "
    "USA ZAF".split()
)
CONTROLS = (
    "log_gdp_pc_ppp",
    "population_growth",
    "trade_openness_control",
    "government_consumption_share",
)
COHORT = {
    "heritage_business_freedom_life_expectancy_wgi_panel_geographic_holdout_v2":
        ("healthcare", "life_expectancy", "regulatory_quality_wgi", "PARTIAL"),
    "heritage_government_integrity_life_expectancy_wgi_panel_geographic_holdout_v2":
        ("healthcare", "life_expectancy", "control_corruption_wgi", "PARTIAL"),
    "heritage_government_integrity_private_consumption_pc_wgi_panel_geographic_holdout_v2":
        ("growth", "private_consumption_pc", "control_corruption_wgi", "PARTIAL"),
    "heritage_property_rights_private_consumption_pc_wgi_panel_geographic_holdout_v2":
        ("growth", "private_consumption_pc", "rule_of_law_wgi", "PARTIAL"),
    "heritage_business_freedom_private_credit_depth_wgi_panel_geographic_holdout_v2":
        ("regulatory", "private_credit_depth", "regulatory_quality_wgi", "PARTIAL"),
    "heritage_government_integrity_private_credit_depth_wgi_panel_geographic_holdout_v2":
        ("regulatory", "private_credit_depth", "control_corruption_wgi", "REFUTED"),
    "heritage_property_rights_private_credit_depth_wgi_panel_geographic_holdout_v2":
        ("regulatory", "private_credit_depth", "rule_of_law_wgi", "PARTIAL"),
}
VINTAGES = {
    "life_expectancy": (
        "world_bank_wdi:SP.DYN.LE00.IN",
        "data/vintages/world_bank_wdi/SP.DYN.LE00.IN@2026-05-05T194852Z.parquet",
        "7cf0d3919a1cf11890afa40a521b46bc131fc446c4e57e15ec8702f4a47eb03d",
    ),
    "private_consumption_pc": (
        "world_bank_wdi:NE.CON.PRVT.PC.KD",
        "data/vintages/world_bank_wdi/NE.CON.PRVT.PC.KD@2026-05-05T194704Z.parquet",
        "e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe",
    ),
    "private_credit_depth": (
        "world_bank_wdi:FS.AST.PRVT.GD.ZS",
        "data/vintages/world_bank_wdi/FS.AST.PRVT.GD.ZS@2026-05-05T194720Z.parquet",
        "57d2717d9097b3142f9b116242218621e4560a6bf4e29ddc22081dd66b2a1b19",
    ),
    "regulatory_quality_wgi": (
        "wgi:GOV_WGI_RQ.EST",
        "data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet",
        "4d8084d77990bc1d10f5630cdf8100c9ce2e1b610ade3aa7b46340fb658c8e2e",
    ),
    "control_corruption_wgi": (
        "wgi:CC.EST",
        "data/vintages/wgi/CC.EST@2026-04-30T114239Z.parquet",
        "192e9da5c623e2894758bd6cc3fa69f49485edbc06e2150f894bf95666d9d79e",
    ),
    "rule_of_law_wgi": (
        "wgi:RL.EST",
        "data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet",
        "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d",
    ),
    "log_gdp_pc_ppp": (
        "world_bank_wdi:NY.GDP.PCAP.PP.KD",
        "data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet",
        "6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb",
    ),
    "population_growth": (
        "world_bank_wdi:SP.POP.GROW",
        "data/vintages/world_bank_wdi/SP.POP.GROW@2026-05-05T194839Z.parquet",
        "5a185bf4e21062c792856bca9176b6dfc9d6a70c6eca22736904ce14e6d10964",
    ),
    "trade_openness_control": (
        "world_bank_wdi:NE.TRD.GNFS.ZS",
        "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
        "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1",
    ),
    "government_consumption_share": (
        "world_bank_wdi:NE.CON.GOVT.ZS",
        "data/vintages/world_bank_wdi/NE.CON.GOVT.ZS@2026-05-05T194701Z.parquet",
        "a6605c618d3dd91b061c4dae7960c4c0baad66c037125aec44cb6b71ccb6a79d",
    ),
}


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id][0]
    return (
        f"hypotheses/{topic}/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verified_sources(names: tuple[str, ...]) -> list[dict[str, str]]:
    records = []
    for name in names:
        source, path, expected = VINTAGES[name]
        actual = hash_file(ROOT / path)
        if actual != expected:
            raise ValueError(f"pinned source hash mismatch: {path}")
        records.append({"role": name, "source": source, "vintage_file": path, "sha256": expected})
    return records


def load_series(name: str) -> pd.DataFrame:
    _, relative_path, _ = VINTAGES[name]
    frame = pd.read_parquet(ROOT / relative_path, columns=["country_iso3", "year", "value"])
    frame = frame[
        frame["country_iso3"].astype(str).str.fullmatch(r"[A-Z]{3}")
        & ~frame["country_iso3"].isin(OLD_COUNTRIES)
    ].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame[name] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[frame["year"].between(1996, 2023)].dropna(subset=[name])
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year in pinned {name} vintage")
    return frame[["country_iso3", "year", name]]


def build_panel(hypothesis_id: str) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    _, outcome, treatment, _ = COHORT[hypothesis_id]
    names = (outcome, treatment, *CONTROLS)
    sources = verified_sources(names)
    frames = [load_series(name) for name in names]
    panel = frames[0]
    for frame in frames[1:]:
        panel = panel.merge(frame, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["log_gdp_pc_ppp"] > 0].copy()
    panel["log_gdp_pc_ppp"] = np.log(panel["log_gdp_pc_ppp"])
    panel = panel.replace([math.inf, -math.inf], np.nan).dropna(subset=list(names))
    if set(panel["country_iso3"]) & OLD_COUNTRIES:
        raise AssertionError("old and holdout countries overlap")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True), sources


def preflight(hypothesis_id: str) -> tuple[dict[str, Any], pd.DataFrame, list[dict[str, str]]]:
    panel, sources = build_panel(hypothesis_id)
    observations = len(panel)
    countries = int(panel["country_iso3"].nunique())
    result = {
        "observations": observations,
        "countries": countries,
        "period": [int(panel["year"].min()), int(panel["year"].max())] if observations else [],
        "old_countries_excluded": len(OLD_COUNTRIES),
        "overlap_with_old_countries": 0,
        "minimum_observations": MIN_OBSERVATIONS,
        "minimum_countries": MIN_COUNTRIES,
        "passed": observations >= MIN_OBSERVATIONS and countries >= MIN_COUNTRIES,
        "coefficient_estimated": False,
    }
    return result, panel, sources


def registration_commit(hypothesis_id: str) -> str:
    spec, steelman, _ = paths(hypothesis_id)
    for relative_path in (spec, steelman, RUNNER_REL):
        committed = subprocess.run(
            ["git", "show", f"HEAD:{relative_path}"], cwd=ROOT, capture_output=True, check=False
        )
        if committed.returncode != 0 or committed.stdout != (ROOT / relative_path).read_bytes():
            raise RuntimeError(f"commit preregistration file before estimation: {relative_path}")
    first = subprocess.run(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", spec],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    commits = first.stdout.strip().splitlines()
    if first.returncode != 0 or not commits:
        raise RuntimeError(f"no first-addition commit for {spec}")
    return commits[0]


def classify(coefficient: float, p_value: float) -> tuple[str, str]:
    if p_value <= FAMILY_P_MAX and coefficient > 0:
        return "SUPPORTED", "positive association clears the seven-test family threshold"
    if p_value <= FAMILY_P_MAX and coefficient < 0:
        return "REFUTED", "negative association clears the seven-test family threshold"
    return "PARTIAL", "estimable association does not clear the seven-test family threshold"


def write_run(
    hypothesis_id: str,
    prereg_commit: str,
    gate: dict[str, Any],
    sources: list[dict[str, str]],
    label: str,
    reason: str,
    estimate: dict[str, Any] | None,
    error: Exception | None = None,
) -> dict[str, Any]:
    spec, steelman, run_rel = paths(hypothesis_id)
    run_dir = ROOT / run_rel
    topic, outcome, treatment, old_verdict = COHORT[hypothesis_id]
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    limitations = [
        "Associational geographic holdout; it does not identify a causal policy effect.",
        f"The old 53-country {old_verdict} result was known at registration.",
        "The seven holdout tests share sources and countries; results are correlated.",
    ]
    if error is not None:
        limitations.append(f"Estimation error: {type(error).__name__}: {error}")
    diagnostics = {
        "hypothesis_id": hypothesis_id,
        "verdict": label,
        "verdict_label": label,
        "verdict_reason": reason,
        "run_utc": stamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "template": "panel_fe",
        "preflight": gate,
        "estimate": estimate,
        "family_size": len(COHORT),
        "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": [x["vintage_file"] for x in sources]},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": hypothesis_id,
        "run_utc": stamp,
        "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit,
        "status": label,
        "old_hypothesis_id": hypothesis_id.removesuffix("_geographic_holdout_v2"),
        "old_verdict": old_verdict,
        "vintages": sources,
        "derived_panel": {
            "rows_after_join": gate.get("observations"),
            "countries_after_join": gate.get("countries"),
            "years": gate.get("period"),
            "excluded_old_country_count": len(OLD_COUNTRIES),
        },
    }
    packet = {
        "packet_version": 1,
        "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec, "topic": topic},
        "preregistration": {
            "spec_commit": prereg_commit,
            "steelman": steelman,
            "gate": {"min_observations": MIN_OBSERVATIONS, "min_countries": MIN_COUNTRIES,
                     "family_p_max": FAMILY_P_MAX},
        },
        "reproduction": {
            "runner": RUNNER_REL,
            "run_dir": run_rel,
            "command": f"python3 {RUNNER_REL} --run {hypothesis_id} --force",
        },
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": sources, "old_country_overlap": 0},
        "results": estimate,
        "limitations": limitations,
    }
    card = (
        f"# Result card: {hypothesis_id}\n\n"
        f"Verdict: **{label}**. {reason}.\n\n"
        f"Old study: `{manifest['old_hypothesis_id']}` ({old_verdict}, known at registration).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        f"Held-out sample: {gate.get('observations', 0)} country-years, "
        f"{gate.get('countries', 0)} countries, zero countries shared with the old study.\n"
        "Estimator: country and year fixed effects with country-clustered standard errors.\n"
        f"Outcome: {outcome}; treatment: {treatment}.\n"
        f"Decision threshold: two-sided p <= {FAMILY_P_MAX:.8f} across seven tests.\n\n"
    )
    if estimate is not None:
        card += (
            f"Primary coefficient: {estimate['coefficient']:+.6g}; "
            f"clustered SE {estimate['std_error']:.6g}; p={estimate['p_value']:.6g}; "
            f"95% CI [{estimate['ci95'][0]:+.6g}, {estimate['ci95'][1]:+.6g}].\n\n"
        )
    card += "This is an association in previously excluded countries, not a causal policy estimate.\n"
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--run', {hypothesis_id!r}, '--force'], cwd=root))\n"
    )
    chart = {
        "hypothesis_id": hypothesis_id, "verdict": label,
        "coefficient": estimate["coefficient"] if estimate else None,
        "ci95": estimate["ci95"] if estimate else None,
        "family_p_max": FAMILY_P_MAX,
    }
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "hypothesis.yaml").write_bytes((ROOT / spec).read_bytes())
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    coefficients = ([{"term": treatment, **estimate}] if estimate else [])
    pd.DataFrame(coefficients, columns=["term", "coefficient", "std_error", "p_value", "ci95",
                                        "n_obs", "n_countries", "r_squared", "method"]).to_parquet(
        run_dir / "coefficients.parquet", index=False
    )
    return {"hypothesis_id": hypothesis_id, "verdict": label, "estimate": estimate, "run_dir": run_rel}


def run_one(hypothesis_id: str, *, force: bool = False) -> dict[str, Any]:
    prereg_commit = registration_commit(hypothesis_id)
    _, _, run_rel = paths(hypothesis_id)
    if (ROOT / run_rel).exists() and not force:
        raise FileExistsError(f"run exists: {run_rel}; use --force for replication")
    try:
        gate, panel, sources = preflight(hypothesis_id)
    except Exception as error:
        return write_run(hypothesis_id, prereg_commit, {"passed": False}, [], "INCONCLUSIVE",
                         f"pinned input preflight error: {type(error).__name__}: {error}", None, error)
    if not gate["passed"]:
        return write_run(hypothesis_id, prereg_commit, gate, sources, "INCONCLUSIVE",
                         "registered complete-case coverage gate did not pass", None)
    _, outcome, treatment, _ = COHORT[hypothesis_id]
    formula = (
        f"{outcome} ~ {treatment} + "
        "log_gdp_pc_ppp + population_growth + trade_openness_control + "
        "government_consumption_share + C(country_iso3) + C(year)"
    )
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True}
        )
        coef = float(fit.params[treatment])
        se = float(fit.bse[treatment])
        p = float(fit.pvalues[treatment])
        ci = [float(x) for x in fit.conf_int().loc[treatment].tolist()]
        if not all(math.isfinite(x) for x in (coef, se, p, *ci)) or se <= 0:
            raise ValueError("nonfinite or zero primary uncertainty")
        if np.linalg.matrix_rank(fit.model.exog) < fit.model.exog.shape[1]:
            raise ValueError("primary fixed-effect design is rank deficient")
    except Exception as error:
        return write_run(hypothesis_id, prereg_commit, gate, sources, "INCONCLUSIVE",
                         f"primary estimation error: {type(error).__name__}: {error}", None, error)
    label, reason = classify(coef, p)
    estimate = {
        "coefficient": coef, "std_error": se, "p_value": p, "ci95": ci,
        "n_obs": len(panel), "n_countries": int(panel["country_iso3"].nunique()),
        "r_squared": float(fit.rsquared),
        "method": "OLS country/year FE with country-clustered standard errors",
    }
    return write_run(hypothesis_id, prereg_commit, gate, sources, label, reason, estimate)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    command = parser.add_mutually_exclusive_group(required=True)
    command.add_argument("--preflight", action="store_true")
    command.add_argument("--run", metavar="HYPOTHESIS_ID", choices=[*COHORT, "all"])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    ids = list(COHORT) if args.preflight or args.run == "all" else [args.run]
    if args.preflight:
        results = {key: preflight(key)[0] for key in ids}
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(row["passed"] for row in results.values()) else 1
    results = {key: run_one(key, force=args.force) for key in ids}
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
