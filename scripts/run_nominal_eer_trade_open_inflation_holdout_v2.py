#!/usr/bin/env python3
"""Guarded, source-pinned nominal-EER/trade/CPI geographic holdout.

--preflight reads source dimensions and country/year keys only. --run and --check
may load values only after an unchanged first-addition preregistration commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ID = "nominal_eer_trade_open_inflation_holdout_v2"
RUNNER_REL = "scripts/run_nominal_eer_trade_open_inflation_holdout_v2.py"
SPEC_REL = f"hypotheses/monetary/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUN_REL = f"engine/runs/{ID}"
OLD_ID = "bis_reer_appreciation_trade_open_disinflation_panel"
OLD_COMMIT = "441b76cba266e45285ffc1e4bdc81dc303a88e29"
FAMILY_ID = "nominal_eer_trade_open_inflation_holdout_2026_10_09"
P_MAX = 0.01
MIN_OBS = 400
MIN_COUNTRIES = 20
MIN_YEARS_PER_COUNTRY = 5
MIN_MONTHS_PER_YEAR = 10
START_YEAR, END_YEAR = 2000, 2022
PRIMARY = "eer_trade_interaction"
OLD_COUNTRIES = tuple("AUS AUT BEL BRA CAN CHE CHL CHN COL CZE DEU DNK ESP FIN FRA GBR GRC HKG HUN IDN IND IRL ISR ITA JPN KOR LUX MEX MYS NLD NOR NZL POL PRT RUS SAU SGP SWE THA TUR USA ZAF".split())
BIS_TO_ISO3 = dict(zip(
    "AE AR BG BA CY DZ EE HR IS LT LV MA MK MT PE PH RO RS SK SI".split(),
    "ARE ARG BGR BIH CYP DZA EST HRV ISL LTU LVA MAR MKD MLT PER PHL ROU SRB SVK SVN".split(),
))
HELD_COUNTRIES = tuple(sorted(BIS_TO_ISO3.values()))
SOURCE_FILES = {
    "eer": {
        "source": "bis:WS_EER", "path": "data/vintages/bis/WS_EER@2026-07-23T151604Z.parquet",
        "sha256": "57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170",
        "manifest": "data/manifests/fetch_run_2026-07-23T151632Z.yaml",
        "series_id": "WS_EER",
        "source_url": "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_EER/1.0/?format=csv",
        "dimensions": {"FREQ": "M", "EER_TYPE": "N", "EER_BASKET": "B", "UNIT_MEASURE": 882, "COLLECTION": "A"},
    },
    "open": {
        "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
        "path": "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
        "sha256": "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NE.TRD.GNFS.ZS", "indicator_id": "NE.TRD.GNFS.ZS",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NE.TRD.GNFS.ZS?format=json",
    },
    "cpi": {
        "source": "world_bank_wdi:FP.CPI.TOTL.ZG",
        "path": "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-05-05T194737Z.parquet",
        "sha256": "dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "FP.CPI.TOTL.ZG", "indicator_id": "FP.CPI.TOTL.ZG",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/FP.CPI.TOTL.ZG?format=json",
    },
    "gdp": {
        "source": "world_bank_wdi:NY.GDP.MKTP.KD.ZG",
        "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
        "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.MKTP.KD.ZG", "indicator_id": "NY.GDP.MKTP.KD.ZG",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KD.ZG?format=json",
    },
}
COLUMNS = ("term", "coefficient", "std_error", "p_value", "ci95", "n_obs", "n_countries", "r_squared", "method")


def git_show(rev: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{rev}:{relative}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"missing committed file {rev}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized_source(source: str) -> str:
    aliases = {
        "wgi:RQ.EST": "wgi:GOV_WGI_RQ.EST", "wgi:CC.EST": "wgi:GOV_WGI_CC.EST",
        "wgi:VA.EST": "wgi:GOV_WGI_VA.EST", "wgi:GE.EST": "wgi:GOV_WGI_GE.EST",
        "wgi:RL.EST": "wgi:GOV_WGI_RL.EST",
        "wits:weighted_mean_applied_tariff": "world_bank_wdi:TM.TAX.MRCH.WM.AR.ZS",
        "wipo:patent_applications_resident": "world_bank_wdi:IP.PAT.RESD",
        "wits:high_tech_exports": "world_bank_wdi:TX.VAL.TECH.CD",
    }
    return aliases.get(source, source)


def pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({normalized_source(x["source"]) for x in variables.get(role, [])
                               if isinstance(x, dict) and x.get("source")}))
                 for role in ("treatment", "outcome"))


def assert_distinct_strict_pair() -> None:
    target = (("bis:WS_EER", "world_bank_wdi:NE.TRD.GNFS.ZS"),
              ("world_bank_wdi:FP.CPI.TOTL.ZG",))
    if pair(yaml.safe_load((ROOT / SPEC_REL).read_text())) != target:
        raise ValueError("the registered source pair changed")
    # Include registered YAMLs even if the generated index has not yet been refreshed.
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC_REL:
            continue
        try:
            spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if spec.get("status") == "pre_registered" and pair(spec) == target:
            raise ValueError(f"strict alias-equivalent source pair already exists: {path}")


def verify_old() -> dict[str, Any]:
    old = yaml.safe_load(git_show(OLD_COMMIT, f"hypotheses/monetary/{OLD_ID}.yaml"))
    diag = json.loads(git_show(OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"))
    runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode()
    if sorted(old["sample"]["countries"]) != list(OLD_COUNTRIES):
        raise ValueError("old country roster changed")
    if (diag["verdict_label"] != "PARTIAL" or diag["estimate"]["n_obs"] != 1230
            or diag["estimate"]["n_countries"] != 41
            or not math.isclose(diag["estimate"]["coefficient"], -0.0009935236582254237)
            or not math.isclose(diag["estimate"]["p_value"], 0.25712889335581957)):
        raise ValueError("historical result changed")
    if ('out = out[out["country_iso3"].isin(countries)]' not in runner
            or "panel_filt = filter_sample(panel, spec)" not in runner
            or "est = run_panel_ols(\n        panel_filt," not in runner):
        raise ValueError("historical fitted-country filter proof unavailable")
    if set(OLD_COUNTRIES) & set(HELD_COUNTRIES):
        raise ValueError("country rosters overlap")
    return old


def verify_spec() -> dict[str, Any]:
    old = verify_old()
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    threshold = spec["falsification"]["threshold"]
    frozen = {
        "family_id": FAMILY_ID, "family_size": 1, "family_alpha": P_MAX,
        "family_p_max": P_MAX, "expected_sign": "-", "min_observations": MIN_OBS,
        "min_countries": MIN_COUNTRIES, "min_pairs_per_country": MIN_YEARS_PER_COUNTRY,
        "min_nonnull_months_per_eer_year": MIN_MONTHS_PER_YEAR,
        "old_hypothesis_id": OLD_ID, "old_result_bucket": "PARTIAL",
        "old_primary_coefficient": -0.0009935236582254237,
        "old_primary_p_value": 0.25712889335581957,
        "old_n_obs": 1230, "old_n_countries": 41,
        "old_spec_commit": OLD_COMMIT, "old_run_commit": OLD_COMMIT,
        "old_runner_filter_proof": "At old_run_commit, scripts/run_panel_fe.py filter_sample restricts country_iso3 to spec.sample.countries before run_panel_ols. Every country in that old roster is excluded.",
        "old_country_count": 42, "old_country_ids": list(OLD_COUNTRIES),
        "heldout_country_ids": list(HELD_COUNTRIES),
        "school_score_credit": 0, "school_score_eligible": False,
        "source_files": SOURCE_FILES,
    }
    if threshold != frozen:
        raise ValueError("frozen threshold or source pins changed")
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec["sample"]["countries"] != list(HELD_COUNTRIES)
            or spec["sample"]["period"] != [START_YEAR, END_YEAR]
            or spec.get("scope", {}).get("countries") != list(HELD_COUNTRIES)
            or spec.get("steelman") != STEELMAN_REL
            or not (ROOT / STEELMAN_REL).is_file()
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []):
        raise ValueError("registration or geographic holdout changed")
    old_sources = pair(old)
    if old_sources != pair(spec):
        raise ValueError("historical measured source pair changed")
    actual = {role: [(x["name"], x["source"]) for x in spec["variables"][role]]
              for role in ("treatment", "outcome", "controls")}
    expected = {
        "treatment": [("nominal_broad_eer_appreciation_pct", SOURCE_FILES["eer"]["source"]),
                      ("trade_share_pct_gdp_at_t", SOURCE_FILES["open"]["source"])],
        "outcome": [("next_year_cpi_inflation_pct", SOURCE_FILES["cpi"]["source"])],
        "controls": [("cpi_inflation_at_t", SOURCE_FILES["cpi"]["source"]),
                     ("real_gdp_growth_at_t", SOURCE_FILES["gdp"]["source"])],
    }
    if actual != expected:
        raise ValueError("registered variables changed")
    if spec["estimator"].get("fixed_effects") != ["country", "year"] or spec["estimator"].get("clustering") != "country":
        raise ValueError("estimator changed")
    assert_distinct_strict_pair()
    return spec


def verify_sources() -> None:
    for pin in SOURCE_FILES.values():
        path = (ROOT / pin["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file() or sha256(path) != pin["sha256"]:
            raise ValueError(f"pinned source absent or changed: {pin['path']}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text(encoding="utf-8"))
        if not any(all(row.get(k) == pin[k] for k in ("parquet_path", "sha256", "series_id", "source_url")
                       if k != "parquet_path") and row.get("parquet_path") == pin["path"]
                   for row in manifest.get("entries", [])):
            raise ValueError(f"pinned source missing from manifest: {pin['path']}")


def keyed_source(role: str, *, values: bool):
    import pandas as pd
    pin = SOURCE_FILES[role]
    columns = (["FREQ", "EER_TYPE", "EER_BASKET", "UNIT_MEASURE", "COLLECTION", "REF_AREA", "period"]
               if role == "eer" else ["country_iso3", "year", "indicator_id"])
    if values:
        columns.append("value")
    frame = pd.read_parquet(ROOT / pin["path"], columns=columns)
    if role == "eer":
        for key, required in pin["dimensions"].items():
            frame = frame[frame[key] == required]
        frame = frame[frame["REF_AREA"].isin(BIS_TO_ISO3)].copy()
        frame["country_iso3"] = frame["REF_AREA"].map(BIS_TO_ISO3)
        frame = frame[frame["period"].astype(str).str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])")].copy()
        if frame.duplicated(["country_iso3", "period"]).any():
            raise ValueError("duplicate pinned BIS monthly keys")
        frame["year"] = frame["period"].str[:4].astype(int)
        frame = frame[frame["year"].between(START_YEAR - 1, END_YEAR)]
        return frame[["country_iso3", "year", "period", *(["value"] if values else [])]]
    frame = frame[(frame["country_iso3"].isin(HELD_COUNTRIES)) &
                  (frame["indicator_id"] == pin["indicator_id"])].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame = frame[frame["year"].notna()].copy()
    frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate pinned WDI annual keys: {role}")
    return frame[["country_iso3", "year", *(["value"] if values else [])]]


def preflight() -> dict[str, Any]:
    verify_spec()
    verify_sources()
    eer = keyed_source("eer", values=False)
    annual = eer.groupby(["country_iso3", "year"])["period"].nunique()
    enough_month_keys = {tuple(k) for k, n in annual.items() if n >= MIN_MONTHS_PER_YEAR}
    open_keys = set(keyed_source("open", values=False).itertuples(index=False, name=None))
    cpi_keys = set(keyed_source("cpi", values=False).itertuples(index=False, name=None))
    gdp_keys = set(keyed_source("gdp", values=False).itertuples(index=False, name=None))
    keys = {(country, year) for country in HELD_COUNTRIES for year in range(START_YEAR, END_YEAR + 1)
            if (country, year) in enough_month_keys and (country, year - 1) in enough_month_keys
            and (country, year) in open_keys and (country, year) in cpi_keys
            and (country, year + 1) in cpi_keys and (country, year) in gdp_keys}
    counts = Counter(country for country, _ in keys)
    keys = {(country, year) for country, year in keys if counts[country] >= MIN_YEARS_PER_COUNTRY}
    result = {
        "hypothesis_id": ID, "key_pairs_upper_bound": len(keys),
        "key_countries_upper_bound": len({country for country, _ in keys}),
        "old_countries_excluded": len(OLD_COUNTRIES),
        "old_country_overlap": len({country for country, _ in keys} & set(OLD_COUNTRIES)),
        "monthly_key_floor": MIN_MONTHS_PER_YEAR,
        "complete_case_coverage_verified": False, "outcome_values_loaded": False,
        "coefficient_estimated": False, "counts_are_upper_bounds": True,
    }
    result["key_envelope_passed"] = (result["key_pairs_upper_bound"] >= MIN_OBS
                                     and result["key_countries_upper_bound"] >= MIN_COUNTRIES
                                     and result["old_country_overlap"] == 0)
    return result


def registration_commit() -> str:
    # The previously ignored BIS and GDP source slices must be force-added with
    # this registration; WDI trade and CPI vintages were tracked already.
    first_add = [RUNNER_REL, SPEC_REL, STEELMAN_REL, SOURCE_FILES["eer"]["path"], SOURCE_FILES["gdp"]["path"]]
    additions = []
    for relative in first_add:
        if git_show("HEAD", relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"commit unchanged preregistration before loading values: {relative}")
        result = subprocess.run(["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
                                cwd=ROOT, capture_output=True, text=True)
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"no first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("runner, spec, steelman, and new source slices must first appear in one commit")
    commit = additions[0]
    for relative in first_add:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration bytes changed after first addition: {relative}")
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode or result.stdout.strip():
        raise RuntimeError("run artifacts existed in preregistration commit")
    return commit


def annual_eer():
    import numpy as np
    import pandas as pd
    frame = keyed_source("eer", values=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"]) & (frame["value"] > 0)].copy()
    grouped = frame.groupby(["country_iso3", "year"]).agg(
        valid_months=("period", "nunique"), eer_mean=("value", "mean")
    ).reset_index()
    grouped = grouped[grouped["valid_months"] >= MIN_MONTHS_PER_YEAR]
    return grouped[["country_iso3", "year", "eer_mean"]]


def annual_wdi(role: str):
    import numpy as np
    import pandas as pd
    frame = keyed_source(role, values=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    return frame[np.isfinite(frame["value"])][["country_iso3", "year", "value"]]


def build_panel():
    import numpy as np
    annual = annual_eer()
    previous = annual.rename(columns={"eer_mean": "eer_previous"}).copy()
    previous["year"] += 1
    panel = annual.merge(previous, on=["country_iso3", "year"], validate="one_to_one")
    panel["nominal_broad_eer_appreciation_pct"] = 100.0 * (np.log(panel["eer_mean"]) - np.log(panel["eer_previous"]))
    trade = annual_wdi("open").rename(columns={"value": "trade_share_pct_gdp_at_t"})
    cpi = annual_wdi("cpi")
    current_cpi = cpi.rename(columns={"value": "cpi_inflation_at_t"})
    future_cpi = cpi.rename(columns={"value": "next_year_cpi_inflation_pct"}).copy()
    future_cpi["year"] -= 1
    gdp = annual_wdi("gdp").rename(columns={"value": "real_gdp_growth_at_t"})
    for frame in (trade, current_cpi, future_cpi, gdp):
        panel = panel.merge(frame, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(START_YEAR, END_YEAR)].copy()
    panel["trade_centered"] = (panel["trade_share_pct_gdp_at_t"] - 100.0) / 100.0
    panel[PRIMARY] = panel["nominal_broad_eer_appreciation_pct"] * panel["trade_centered"]
    required = ["next_year_cpi_inflation_pct", "nominal_broad_eer_appreciation_pct",
                "trade_centered", PRIMARY, "cpi_inflation_at_t", "real_gdp_growth_at_t"]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=required)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_YEARS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & set(OLD_COUNTRIES):
        raise AssertionError("historical fitted-country roster entered holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate():
    import statsmodels.formula.api as smf
    panel = build_panel()
    n_countries = panel["country_iso3"].nunique()
    gate = {"observations": len(panel), "countries": int(n_countries),
            "old_country_overlap": 0,
            "treatment_years": [int(panel["year"].min()), int(panel["year"].max())] if len(panel) else [],
            "min_country_years": int(panel.groupby("country_iso3")["year"].size().min()) if len(panel) else 0}
    gate["passed"] = (gate["observations"] >= MIN_OBS and gate["countries"] >= MIN_COUNTRIES
                      and gate["min_country_years"] >= MIN_YEARS_PER_COUNTRY)
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "frozen complete-case sample gate failed", None
    formula = ("next_year_cpi_inflation_pct ~ nominal_broad_eer_appreciation_pct + "
               "trade_centered + eer_trade_interaction + cpi_inflation_at_t + "
               "real_gdp_growth_at_t + C(country_iso3) + C(year)")
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"],
                                         "use_correction": True, "df_correction": True},
            use_t=True,
        )
        coefficient = float(fit.params[PRIMARY])
        std_error = float(fit.bse[PRIMARY])
        p_value = float(fit.pvalues[PRIMARY])
        ci95 = [float(x) for x in fit.conf_int().loc[PRIMARY].tolist()]
        if (fit.model.rank < fit.model.exog.shape[1] or
                std_error <= 0 or not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95))):
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    if coefficient < 0 and p_value <= P_MAX:
        verdict, reason = "SUPPORTED", "negative interaction cleared the frozen two-sided 0.01 rule"
    elif coefficient > 0 and p_value <= P_MAX:
        verdict, reason = "REFUTED", "positive interaction cleared the frozen two-sided 0.01 rule"
    else:
        verdict, reason = "PARTIAL", "interaction did not clear the frozen directional rule"
    row = {"coefficient": coefficient, "std_error": std_error, "p_value": p_value,
           "ci95": ci95, "n_obs": len(panel), "n_countries": int(n_countries),
           "r_squared": float(fit.rsquared),
           "method": "country/year FE OLS; country-clustered small-sample t(19) inference"}
    return gate, verdict, reason, row


def expected_artifacts(commit: str, gate: dict[str, Any], verdict: str, reason: str,
                       row: dict[str, Any] | None, stamp: str):
    inputs = [{"role": role, **pin} for role, pin in SOURCE_FILES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0}
    limits = ["The known old REER interaction result was PARTIAL; it was seen before this registration.",
              "The nominal EER follow-up is country-disjoint from the old 42-country fit but may share data with other IESET studies.",
              "WDI trade share includes exports as well as imports; euro-area countries share exchange-rate shocks.",
              "Lagged observational association does not identify exchange-rate policy or causal import-price pass-through.",
              "No school, welfare, or policy-score credit."]
    diagnostics = {"hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
                   "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
                   "preregistration_commit": commit, "template": "panel_fe", "preflight": gate,
                   "estimate": row, "family_id": FAMILY_ID, "family_size": 1,
                   "family_p_max": P_MAX, "data_status": {"variables_missing": [],
                   "input_vintages": inputs}, "limitations": limits, "correction": correction}
    manifest = {"hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER_REL,
                "preregistration_commit": commit, "status": verdict,
                "old_hypothesis_id": OLD_ID, "old_verdict": "PARTIAL", "old_run_commit": OLD_COMMIT,
                "vintages": inputs, "derived_panel": gate, "correction": correction}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "monetary"},
              "preregistration": {"spec_commit": commit, "steelman": STEELMAN_REL,
                                  "family_id": FAMILY_ID, "family_p_max": P_MAX},
              "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                               "command": f"python3 {RUNNER_REL} --check"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": inputs, "old_country_overlap": 0},
              "results": row, "limitations": limits, "correction": correction}
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Historical real-EER result: {OLD_ID} (PARTIAL, p=0.257 known).\n"
            f"Preregistration commit: {commit}.\n"
            f"Held-out sample: {gate['observations']} country-year pairs, {gate['countries']} countries, zero old-country overlap.\n"
            f"Single-test threshold: two-sided p <= {P_MAX:.2f}.\n")
    if row:
        card += (f"Primary interaction: {row['coefficient']:+.6g}; clustered SE {row['std_error']:.6g}; "
                 f"p={row['p_value']:.6g}.\n")
    card += "\nMeasured association only; no causal, school, welfare, or policy-score credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "coefficient": row["coefficient"] if row else None,
             "ci95": row["ci95"] if row else None, "family_p_max": P_MAX}
    coefficients = ([{"term": PRIMARY, **row}] if row else [])
    return diagnostics, manifest, packet, card, wrapper, chart, coefficients


def write_run(commit: str, gate: dict[str, Any], verdict: str, reason: str,
              row: dict[str, Any] | None) -> None:
    import pandas as pd
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, wrapper, chart, coefficients = expected_artifacts(
        commit, gate, verdict, reason, row, stamp)
    path = ROOT / RUN_REL
    path.mkdir(parents=True, exist_ok=False)
    (path / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (path / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (path / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (path / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (path / "result_card.md").write_text(card, encoding="utf-8")
    (path / "replication.py").write_text(wrapper, encoding="utf-8")
    (path / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(coefficients, columns=COLUMNS).to_parquet(path / "coefficients.parquet", index=False)


def check_run(commit: str) -> dict[str, Any]:
    import pandas as pd
    path = ROOT / RUN_REL
    diagnostics = json.loads((path / "diagnostics.json").read_text(encoding="utf-8"))
    if (path / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("stored spec differs from preregistration")
    gate, verdict, reason, row = estimate()
    if (diagnostics.get("preregistration_commit") != commit or diagnostics.get("preflight") != gate
            or diagnostics.get("verdict_label") != verdict or diagnostics.get("verdict_reason") != reason):
        raise AssertionError("rerun gate or verdict mismatch")
    saved = diagnostics.get("estimate")
    if (saved is None) != (row is None):
        raise AssertionError("rerun estimate presence mismatch")
    if row:
        for key, value in row.items():
            if isinstance(value, float) and not math.isclose(float(saved[key]), value, rel_tol=1e-8, abs_tol=1e-10):
                raise AssertionError(f"rerun {key} mismatch")
            if isinstance(value, list) and any(not math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-10)
                                               for x, y in zip(saved[key], value)):
                raise AssertionError(f"rerun {key} mismatch")
            if not isinstance(value, (float, list)) and saved[key] != value:
                raise AssertionError(f"rerun {key} mismatch")
    expected = expected_artifacts(commit, gate, verdict, reason, row, diagnostics["run_utc"])
    jsons = [diagnostics, yaml.safe_load((path / "manifest.yaml").read_text()),
             yaml.safe_load((path / "evidence_packet.yaml").read_text()),
             (path / "result_card.md").read_text(), (path / "replication.py").read_text(),
             json.loads((path / "chart_data.json").read_text())]
    for actual, should in zip(jsons, expected[:6]):
        if actual != should:
            raise AssertionError("stored evidence artifact mismatch")
    table = pd.read_parquet(path / "coefficients.parquet")
    if list(table.columns) != list(COLUMNS) or len(table) != len(expected[6]):
        raise AssertionError("stored coefficient table mismatch")
    for actual, should in zip(table.to_dict(orient="records"), expected[6]):
        for key in COLUMNS:
            if key == "ci95":
                observed_ci = list(actual[key])
                expected_ci = should[key]
                if len(observed_ci) != len(expected_ci) or any(
                    not math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-10)
                    for x, y in zip(observed_ci, expected_ci)
                ):
                    raise AssertionError("stored coefficient ci95 mismatch")
            elif key in {"coefficient", "std_error", "p_value", "r_squared"}:
                if not math.isclose(float(actual[key]), float(should[key]), rel_tol=1e-8, abs_tol=1e-10):
                    raise AssertionError(f"stored coefficient {key} mismatch")
            elif actual[key] != should[key]:
                raise AssertionError(f"stored coefficient {key} mismatch")
    return {"hypothesis_id": ID, "verified": True, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        result = preflight()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["key_envelope_passed"] else 1
    commit = registration_commit()  # Deliberately before any value-column read.
    verify_spec()
    verify_sources()
    if args.check:
        result = check_run(commit)
    else:
        if (ROOT / RUN_REL).exists():
            raise FileExistsError(f"run already exists: {RUN_REL}")
        gate, verdict, reason, row = estimate()
        write_run(commit, gate, verdict, reason, row)
        result = {"hypothesis_id": ID, "verdict": verdict, "run_dir": RUN_REL}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
