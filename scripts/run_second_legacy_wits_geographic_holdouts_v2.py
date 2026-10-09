#!/usr/bin/env python3
"""Two source-pinned WITS country-disjoint measured-association holdouts.

Preflight reads only country/year keys and categorical source selectors. Values
can be loaded only after this runner, both specs, and both steelmen first
appear unchanged in one earlier Git commit containing no run artifacts.
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

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_second_legacy_wits_geographic_holdouts_v2.py"
OLD_RUN_COMMIT = "441b76cba266e45285ffc1e4bdc81dc303a88e29"
OLD_COUNTRIES = frozenset(
    "ARG AUS AUT BEL BRA CAN CHE CHL CHN COL DEU DNK ESP FIN FRA GBR HUN IDN "
    "IND IRL ITA JPN KOR MEX MYS NLD NOR NZL PER PHL POL PRT SGP SWE THA "
    "TUR USA VNM ZAF".split()
)
FAMILY_ID = "second_legacy_wits_geographic_holdouts_2026_10_09"
FAMILY_P_MAX = 0.10 / 2
PERIOD = [1996, 2021]
MIN_OBSERVATIONS = 500
MIN_COUNTRIES = 40
MIN_PAIRS_PER_COUNTRY = 5
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
    "n_countries", "r_squared", "method",
)

SOURCE_FILES: dict[str, dict[str, Any]] = {
    "tariff": {
        "source": "wits:tariff_average",
        "path": "data/vintages/wits/tariff_average@2026-07-23T151542Z.parquet",
        "sha256": "5eb706954c8197b5108dddae749ae1aed9d3faa3404c02f48eef9c4390bfd398",
        "manifest": "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
        "series_id": "tariff_average",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/TM.TAX.MRCH.WM.AR.ZS?format=json",
    },
    "import_lines": {
        "source": "wits:product_lines",
        "path": "data/vintages/wits/product_lines@2026-07-23T153655Z.parquet",
        "sha256": "085606c8406c963618bf34d141f4dd34b845b3af0493ebd759347acc3ca6441b",
        "manifest": "data/manifests/fetch_run_2026-07-23T153659Z.yaml",
        "series_id": "product_lines",
        "source_url": "https://wits.worldbank.org/API/V1/SDMX/V21/datasource/tradestats-trade/reporter/all/year/1988-2023/indicator/NMBR-MPRT-HS6-PRDCT",
    },
    "export_hhi": {
        "source": "wits:export_product_hhi_wits",
        "path": "data/vintages/wits/export_product_hhi_wits@2026-05-16T094546Z.parquet",
        "sha256": "88528dd4d46c0efebc928f2c4c3ac63d2b60bee5505d313184342b8e071b7d47",
        "manifest": "data/manifests/fetch_run_wits_export_product_hhi_2026-05-16T094546Z.json",
        "series_id": "export_product_hhi_wits",
        "source_url": "https://datacatalog.worldbank.org/search/dataset/0064718/herfindahl-hirschman-product-concentration-index-export",
    },
    "hightech": {
        "source": "wits:high_tech_exports",
        "path": "data/vintages/wits/high_tech_exports@2026-07-23T153650Z.parquet",
        "sha256": "812e79d58bb1a18c4e6725639d7faec21e8302d87201cd58e1a6027bb8d30cb1",
        "manifest": "data/manifests/fetch_run_2026-07-23T153659Z.yaml",
        "series_id": "high_tech_exports",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/TX.VAL.TECH.CD?format=json",
    },
}

# The relevant pinned files each contain one intended dimensional slice. Check
# these selectors in both key-only preflight and the post-registration value run.
SOURCE_DIMENSIONS = {
    "tariff": {"indicator_id": "TM.TAX.MRCH.WM.AR.ZS", "series_id": "tariff_average"},
    "import_lines": {
        "partner_iso3": "WLD", "product_code": "999999",
        "indicator_id": "NMBR-MPRT-HS6-PRDCT", "series_id": "product_lines",
    },
    "export_hhi": {
        "classification": "H0", "partner_iso3": "WLD", "product_cluster": "Tier3",
    },
    "hightech": {"indicator_id": "TX.VAL.TECH.CD", "series_id": "high_tech_exports"},
}

COHORT: dict[str, dict[str, Any]] = {
    "wits_tariff_import_product_variety_geographic_holdout_v2": {
        "old_id": "wits_tariff_cuts_import_variety_panel",
        "old_verdict": "PARTIAL", "old_n_obs": 1030, "old_n_countries": 39,
        "treatment": "tariff", "outcome": "import_lines",
        "treatment_name": "applied_weighted_mean_tariff_pct",
        "outcome_name": "next_year_log_imported_hs6_line_growth",
        "measurement_limit": (
            "Applied weighted-mean merchandise tariffs are not every trade barrier; "
            "HS6 line counts can move with customs reporting and classification. "
            "This association does not establish consumer welfare or a policy effect."
        ),
    },
    "wits_export_concentration_hightech_growth_geographic_holdout_v2": {
        "old_id": "wits_export_concentration_hightech_drag_panel",
        "old_verdict": "SUPPORTED", "old_n_obs": 580, "old_n_countries": 39,
        "treatment": "export_hhi", "outcome": "hightech",
        "treatment_name": "export_product_hhi",
        "outcome_name": "next_year_log_hightech_export_value_growth",
        "measurement_limit": (
            "Product HHI and high-technology exports may share underlying trade "
            "records. Current-dollar growth includes prices and exchange rates. "
            "This association does not establish innovation or a policy effect."
        ),
    },
}


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    return (
        f"hypotheses/trade/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


def git_show(revision: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=ROOT,
        capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"missing committed file {revision}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_spec(hypothesis_id: str) -> dict[str, Any]:
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, _ = paths(hypothesis_id)
    spec = yaml.safe_load((ROOT / spec_rel).read_text(encoding="utf-8"))
    old_spec = yaml.safe_load(git_show(
        OLD_RUN_COMMIT, f"hypotheses/trade/{config['old_id']}.yaml"
    ))
    old_diagnostics = json.loads(git_show(
        OLD_RUN_COMMIT, f"engine/runs/{config['old_id']}/diagnostics.json"
    ))
    historical_runner = git_show(OLD_RUN_COMMIT, "scripts/run_panel_fe.py").decode()
    if set(old_spec["sample"]["countries"]) != OLD_COUNTRIES or \
            len(old_spec["sample"]["countries"]) != len(OLD_COUNTRIES):
        raise ValueError(f"historical old-country roster changed: {hypothesis_id}")
    if ('out = out[out["country_iso3"].isin(countries)]' not in historical_runner or
            "panel_filt = filter_sample(panel, spec)" not in historical_runner or
            "est = run_panel_ols(\n        panel_filt," not in historical_runner):
        raise ValueError("historical runner does not prove old-country restriction")
    if old_diagnostics["estimate"]["n_obs"] != config["old_n_obs"] or \
            old_diagnostics["estimate"]["n_countries"] != config["old_n_countries"] or \
            old_diagnostics["verdict_label"] != config["old_verdict"]:
        raise ValueError(f"historical old result changed: {hypothesis_id}")
    if spec.get("hypothesis_id") != hypothesis_id or spec.get("status") != "pre_registered" or \
            spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-":
        raise ValueError(f"invalid new registration: {spec_rel}")
    if spec["sample"].get("countries") != ["GLOBAL"] or spec["sample"].get("period") != PERIOD:
        raise ValueError(f"sample changed: {spec_rel}")
    expected_exclusion = (
        "Exclude all 39 countries in the historical old specification: "
        + " ".join(sorted(OLD_COUNTRIES)) + "."
    )
    if spec["sample"]["exclusion_rules"][0] != expected_exclusion:
        raise ValueError(f"old-country exclusion changed: {spec_rel}")
    expected_threshold = {
        "family_id": FAMILY_ID, "family_size": len(COHORT),
        "family_alpha": 0.10, "family_p_max": FAMILY_P_MAX,
        "expected_sign": "-", "min_observations": MIN_OBSERVATIONS,
        "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
        "old_hypothesis_id": config["old_id"],
        "old_result_bucket": config["old_verdict"],
        "old_country_count": len(OLD_COUNTRIES),
        "old_country_ids": sorted(OLD_COUNTRIES),
        "old_run_commit": OLD_RUN_COMMIT,
        "source_files": {
            "treatment": SOURCE_FILES[config["treatment"]],
            "outcome": SOURCE_FILES[config["outcome"]],
        },
    }
    if spec["falsification"]["threshold"] != expected_threshold:
        raise ValueError(f"frozen threshold or source custody changed: {spec_rel}")
    variables = spec["variables"]
    if variables.get("controls") != [] or \
            variables["treatment"][0]["name"] != config["treatment_name"] or \
            variables["treatment"][0]["source"] != SOURCE_FILES[config["treatment"]]["source"] or \
            variables["outcome"][0]["name"] != config["outcome_name"] or \
            variables["outcome"][0]["source"] != SOURCE_FILES[config["outcome"]]["source"] or \
            len(variables["treatment"]) != 1 or len(variables["outcome"]) != 1:
        raise ValueError(f"measured variables changed: {spec_rel}")
    if spec["estimator"]["template"] != "panel_fe" or \
            spec["estimator"]["fixed_effects"] != ["country", "year"] or \
            spec["estimator"]["clustering"] != "country":
        raise ValueError(f"estimator changed: {spec_rel}")
    if spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != [] or \
            spec.get("linked_conditions") != []:
        raise ValueError(f"school links prohibited: {spec_rel}")
    if spec.get("steelman") != steelman_rel or not (ROOT / steelman_rel).is_file():
        raise ValueError(f"missing steelman: {steelman_rel}")
    return spec


def verify_sources(hypothesis_id: str, spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    pins = spec["falsification"]["threshold"]["source_files"]
    for role, pin in pins.items():
        relative = Path(pin["path"])
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or path.suffix != ".parquet":
            raise ValueError(f"invalid source path: {relative}")
        if sha256(path) != pin["sha256"]:
            raise ValueError(f"source SHA-256 mismatch: {relative}")
        manifest_path = ROOT / pin["manifest"]
        manifest = (json.loads(manifest_path.read_text(encoding="utf-8"))
                    if manifest_path.suffix == ".json" else
                    yaml.safe_load(manifest_path.read_text(encoding="utf-8")))
        if not any(
            item.get("parquet_path") == pin["path"] and
            item.get("sha256") == pin["sha256"] and
            item.get("series_id") == pin["series_id"] and
            item.get("source_url") == pin["source_url"]
            for item in manifest.get("entries", [])
        ):
            raise ValueError(f"source absent from pinned fetch manifest: {relative}")
        records[role] = {"source": pin["source"], "vintage_file": pin["path"],
                         "sha256": pin["sha256"], "source_manifest": pin["manifest"],
                         "source_url": pin["source_url"], "series_id": pin["series_id"]}
    return records


def source_frame(record: dict[str, Any], source_key: str, *, values: bool):
    """Load only registered keys/selectors unless committed-run mode asks for values."""
    import pandas as pd
    import pycountry

    selectors = SOURCE_DIMENSIONS[source_key]
    columns = ["country_iso3", "year", *selectors]
    if values:
        columns.append("value")
    frame = pd.read_parquet(ROOT / record["vintage_file"], columns=columns)
    for field, expected in selectors.items():
        observed = set(frame[field].dropna().astype(str))
        if observed != {expected}:
            raise ValueError(f"registered source dimension changed: {source_key}.{field}")
    valid_countries = {item.alpha_3 for item in pycountry.countries} | {"XKX"}
    frame = frame[frame["country_iso3"].isin(valid_countries) &
                  ~frame["country_iso3"].isin(OLD_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country-year keys: {record['vintage_file']}")
    return frame[["country_iso3", "year"] + (["value"] if values else [])]


def key_envelope(hypothesis_id: str, sources: dict[str, dict[str, Any]]) -> set[tuple[str, int]]:
    config = COHORT[hypothesis_id]
    treatment = source_frame(sources["treatment"], config["treatment"], values=False)
    outcome = source_frame(sources["outcome"], config["outcome"], values=False)
    t_keys = set(zip(treatment["country_iso3"], treatment["year"]))
    y_keys = set(zip(outcome["country_iso3"], outcome["year"]))
    keys = t_keys & y_keys & {(country, year - 1) for country, year in y_keys}
    keys = {(country, year) for country, year in keys if PERIOD[0] <= year <= PERIOD[1]}
    counts: dict[str, int] = {}
    for country, _ in keys:
        counts[country] = counts.get(country, 0) + 1
    return {(country, year) for country, year in keys
            if counts[country] >= MIN_PAIRS_PER_COUNTRY}


def preflight(hypothesis_id: str) -> dict[str, Any]:
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    keys = key_envelope(hypothesis_id, sources)
    countries = {country for country, _ in keys}
    years = [year for _, year in keys]
    return {
        "hypothesis_id": hypothesis_id,
        "key_pairs_upper_bound": len(keys),
        "key_countries_upper_bound": len(countries),
        "treatment_years": [min(years), max(years)] if years else [],
        "old_countries_excluded": len(OLD_COUNTRIES),
        "old_country_overlap": len(countries & OLD_COUNTRIES),
        "key_envelope_passed": len(keys) >= MIN_OBSERVATIONS and
        len(countries) >= MIN_COUNTRIES and not bool(countries & OLD_COUNTRIES),
        "complete_case_coverage_verified": False,
        "counts_are_upper_bounds": True,
        "coefficient_estimated": False,
        "outcome_values_loaded": False,
    }


def registration_commit() -> str:
    files = [RUNNER_REL]
    for hypothesis_id in COHORT:
        files.extend(paths(hypothesis_id)[:2])
    additions = []
    for relative in files:
        current = (ROOT / relative).read_bytes()
        if git_show("HEAD", relative) != current:
            raise RuntimeError(f"commit the complete two-test preregistration: {relative}")
        result = subprocess.run(
            ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"missing first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("both specs, steelmen, and runner must first appear together")
    commit = additions[0]
    for relative in files:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes differ from first addition: {relative}")
    for hypothesis_id in COHORT:
        _, _, run_rel = paths(hypothesis_id)
        result = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit, "--", run_rel],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode or result.stdout.strip():
            raise RuntimeError(f"run artifacts existed in registration commit: {run_rel}")
    return commit


def load_values(record: dict[str, Any], source_key: str, role: str):
    import numpy as np
    import pandas as pd

    frame = source_frame(record, source_key, values=True)
    frame[role] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame[role])].copy()
    return frame[["country_iso3", "year", role]]


def build_panel(hypothesis_id: str, sources: dict[str, dict[str, Any]]):
    import numpy as np

    config = COHORT[hypothesis_id]
    treatment = load_values(sources["treatment"], config["treatment"], "treatment")
    outcome = load_values(sources["outcome"], config["outcome"], "outcome")
    next_outcome = outcome.rename(columns={"outcome": "outcome_next"}).copy()
    next_outcome["year"] -= 1
    panel = treatment.merge(outcome, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(next_outcome, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[(panel["outcome"] > 0) & (panel["outcome_next"] > 0)].copy()
    panel[config["outcome_name"]] = np.log(panel["outcome_next"]) - np.log(panel["outcome"])
    panel[config["treatment_name"]] = panel["treatment"]
    panel = panel[panel["year"].between(*PERIOD)].copy()
    required = [config["outcome_name"], config["treatment_name"]]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & OLD_COUNTRIES:
        raise AssertionError("old countries entered the new fitted sample")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate_one(hypothesis_id: str, sources: dict[str, dict[str, Any]]):
    import statsmodels.formula.api as smf

    config = COHORT[hypothesis_id]
    panel = build_panel(hypothesis_id, sources)
    countries = int(panel["country_iso3"].nunique())
    gate = {
        "observations": len(panel), "countries": countries,
        "old_country_overlap": 0,
        "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
        "passed": len(panel) >= MIN_OBSERVATIONS and countries >= MIN_COUNTRIES,
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case sample gate failed", None
    treatment = config["treatment_name"]
    formula = f"{config['outcome_name']} ~ {treatment} + C(country_iso3) + C(year)"
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"], "use_correction": True}
        )
        coefficient = float(fit.params[treatment])
        std_error = float(fit.bse[treatment])
        p_value = float(fit.pvalues[treatment])
        ci95 = [float(x) for x in fit.conf_int().loc[treatment].tolist()]
        if fit.model.rank < fit.model.exog.shape[1] or \
                not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95)) or \
                std_error <= 0:
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    if coefficient < 0 and p_value <= FAMILY_P_MAX:
        verdict, reason = "SUPPORTED", "negative coefficient clears the two-test family threshold"
    elif coefficient > 0 and p_value <= FAMILY_P_MAX:
        verdict, reason = "REFUTED", "positive coefficient clears the two-test family threshold"
    else:
        verdict, reason = "PARTIAL", "estimable coefficient does not clear the directional family rule"
    estimate = {
        "coefficient": coefficient, "std_error": std_error, "p_value": p_value,
        "ci95": ci95, "n_obs": len(panel), "n_countries": countries,
        "r_squared": float(fit.rsquared),
        "method": "country/year FE OLS, country-clustered standard errors",
    }
    return gate, verdict, reason, estimate


def artifact_records(hypothesis_id: str, prereg_commit: str,
                     sources: dict[str, dict[str, Any]], gate: dict[str, Any],
                     verdict: str, reason: str, estimate: dict[str, Any] | None,
                     stamp: str):
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, run_rel = paths(hypothesis_id)
    source_list = [{"role": role, **record} for role, record in sources.items()]
    limitations = [
        "Country-disjoint measured association, not a causal policy effect.",
        f"Old same-commit {config['old_verdict']} result was seen before this registration.",
        "Two tests share trade source families and use a fixed within-family correction.",
        "No linked school or position receives score credit from this calibration test.",
        "Source vintages and eligible countries may overlap other IESET v2 studies.",
        config["measurement_limit"],
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "panel_fe",
        "preflight": gate, "estimate": estimate, "family_id": FAMILY_ID,
        "family_size": len(COHORT), "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": source_list},
        "evidence_tier_recommendation": "calibration",
        "correction": {"school_score_eligible": False, "school_score_credit": 0,
                       "reason": "descriptive calibration only"},
        "limitations": limitations,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": verdict,
        "old_hypothesis_id": config["old_id"], "old_verdict": config["old_verdict"],
        "old_run_commit": OLD_RUN_COMMIT, "vintages": source_list,
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_rel, "topic": "trade"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": steelman_rel,
                            "family_id": FAMILY_ID, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {RUNNER_REL} --check {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": source_list, "old_country_overlap": 0},
        "results": estimate, "limitations": limitations,
    }
    card = (
        f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
        f"Old same-commit run: {config['old_id']} ({config['old_verdict']} known).\n"
        f"Preregistration commit: {prereg_commit}.\n"
        f"Held-out sample: {gate['observations']} country-year pairs, "
        f"{gate['countries']} countries, zero old-country overlap.\n"
        f"Family threshold: two-sided p <= {FAMILY_P_MAX:.8f} over two tests.\n"
    )
    if estimate is not None:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; "
                 f"clustered SE {estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += ("\nMeasurement boundary: " + config["measurement_limit"]
             + "\nDescriptive calibration only. The old broad mechanism is not validated. "
             "No school-score credit.\n")
    wrapper = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        "raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / {RUNNER_REL!r}), '--check', {hypothesis_id!r}], cwd=root))\n"
    )
    chart = {
        "hypothesis_id": hypothesis_id, "verdict": verdict,
        "coefficient": estimate["coefficient"] if estimate else None,
        "ci95": estimate["ci95"] if estimate else None,
        "family_p_max": FAMILY_P_MAX,
    }
    rows = ([{key: ({"term": config["treatment_name"], **estimate}).get(key)
              for key in COEFFICIENT_COLUMNS}] if estimate else [])
    return diagnostics, manifest, packet, card, wrapper, chart, rows


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label} fields mismatch")
        for key, value in expected.items():
            assert_equal(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, (list, tuple)):
        if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
            raise AssertionError(f"{label} length mismatch")
        for index, value in enumerate(expected):
            assert_equal(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, bool) or expected is None or isinstance(expected, str):
        if actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, int):
        if isinstance(actual, bool) or not isinstance(actual, int) or actual != expected:
            raise AssertionError(f"{label} mismatch")
    elif isinstance(expected, float):
        try:
            number = float(actual)
        except (ValueError, TypeError) as error:
            raise AssertionError(f"{label} is not numeric") from error
        if not math.isfinite(number) or not math.isclose(number, expected, rel_tol=1e-8, abs_tol=1e-10):
            raise AssertionError(f"{label} mismatch")
    elif actual != expected:
        raise AssertionError(f"{label} mismatch")


def read_coefficient_rows(path: Path) -> list[dict[str, Any]]:
    import pandas as pd

    frame = pd.read_parquet(path)
    if list(frame.columns) != list(COEFFICIENT_COLUMNS):
        raise AssertionError("stored coefficient columns mismatch")
    return [
        {key: value.tolist() if hasattr(value, "tolist") else value
         for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def write_run(hypothesis_id: str, prereg_commit: str, sources: dict[str, dict[str, Any]],
              gate: dict[str, Any], verdict: str, reason: str,
              estimate: dict[str, Any] | None) -> dict[str, Any]:
    import pandas as pd

    spec_rel, _, run_rel = paths(hypothesis_id)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, wrapper, chart, rows = artifact_records(
        hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate, stamp
    )
    run_dir = ROOT / run_rel
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "hypothesis.yaml").write_bytes((ROOT / spec_rel).read_bytes())
    (run_dir / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (run_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (run_dir / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (run_dir / "result_card.md").write_text(card, encoding="utf-8")
    (run_dir / "replication.py").write_text(wrapper, encoding="utf-8")
    (run_dir / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(run_dir / "coefficients.parquet", index=False)
    return {"hypothesis_id": hypothesis_id, "verdict": verdict, "run_dir": run_rel}


def run_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit()
    _, _, run_rel = paths(hypothesis_id)
    if (ROOT / run_rel).exists():
        raise FileExistsError(f"existing run: {run_rel}")
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    return write_run(hypothesis_id, prereg_commit, sources, gate, verdict, reason, estimate)


def check_one(hypothesis_id: str) -> dict[str, Any]:
    prereg_commit = registration_commit()
    spec_rel, _, run_rel = paths(hypothesis_id)
    run_dir = ROOT / run_rel
    if not run_dir.is_dir():
        raise FileNotFoundError(f"missing run: {run_rel}")
    diagnostics = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8"))
    packet = yaml.safe_load((run_dir / "evidence_packet.yaml").read_text(encoding="utf-8"))
    chart = json.loads((run_dir / "chart_data.json").read_text(encoding="utf-8"))
    card = (run_dir / "result_card.md").read_text(encoding="utf-8")
    wrapper = (run_dir / "replication.py").read_text(encoding="utf-8")
    hypothesis = (run_dir / "hypothesis.yaml").read_bytes()
    coefficients = read_coefficient_rows(run_dir / "coefficients.parquet")
    if hypothesis != (ROOT / spec_rel).read_bytes():
        raise AssertionError("stored hypothesis snapshot mismatch")
    spec = validate_spec(hypothesis_id)
    sources = verify_sources(hypothesis_id, spec)
    expected = artifact_records(
        hypothesis_id, prereg_commit, sources, diagnostics["preflight"],
        diagnostics["verdict_label"], diagnostics["verdict_reason"],
        diagnostics["estimate"], diagnostics["run_utc"],
    )
    for label, actual, should in zip(
        ("diagnostics", "manifest", "evidence_packet", "chart_data", "coefficients"),
        (diagnostics, manifest, packet, chart, coefficients),
        (expected[0], expected[1], expected[2], expected[5], expected[6]),
    ):
        assert_equal(actual, should, label)
    if card != expected[3] or wrapper != expected[4]:
        raise AssertionError("stored text artifact mismatch")
    gate, verdict, reason, estimate = estimate_one(hypothesis_id, sources)
    assert_equal(diagnostics["preflight"], gate, "sample gate")
    assert_equal(diagnostics["verdict_label"], verdict, "verdict")
    assert_equal(diagnostics["verdict_reason"], reason, "verdict reason")
    assert_equal(diagnostics["estimate"], estimate, "estimate")
    return {"hypothesis_id": hypothesis_id, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", metavar="ID", choices=[*COHORT, "all"])
    mode.add_argument("--check", metavar="ID", choices=[*COHORT, "all"])
    args = parser.parse_args()
    selected = args.run or args.check
    ids = list(COHORT) if args.preflight or selected == "all" else [selected]
    if args.preflight:
        results = {hypothesis_id: preflight(hypothesis_id) for hypothesis_id in ids}
        print(json.dumps(results, indent=2, sort_keys=True))
        return 0 if all(row["key_envelope_passed"] for row in results.values()) else 1
    if args.check:
        results = {hypothesis_id: check_one(hypothesis_id) for hypothesis_id in ids}
    else:
        results = {hypothesis_id: run_one(hypothesis_id) for hypothesis_id in ids}
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
