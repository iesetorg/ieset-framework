#!/usr/bin/env python3
"""Source-pinned, country-disjoint BIS property-price/income calibration.

--preflight reads dimensions and country/year keys only. --run and --check
enforce an unchanged first-addition preregistration before opening values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ID = "bis_real_residential_price_growth_income_growth_country_holdout_v2"
RUNNER_REL = f"scripts/run_{ID}.py"
SPEC_REL = f"hypotheses/housing/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUN_REL = f"engine/runs/{ID}"
OLD_ID = "land_use_regulation_real_wage_drag"
OLD_COMMIT = "e786a95e676c9d6283c123682d43bf54dbacd73b"
FAMILY_ID = "legacy_source_pair_frontier_2026_10_09"
FAMILY_SIZE = 84
FAMILY_ALPHA = 0.1
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MIN_OBS = 400
MIN_COUNTRIES = 20
MIN_YEARS_PER_COUNTRY = 5
START_YEAR, END_YEAR = 1996, 2023
PRIMARY = "real_residential_price_yoy_pct_q4_t"
OLD_COUNTRIES = tuple("ARG AUS BGD BRA CAN CHL CHN COL DEU DNK EGY ESP EST FIN FRA GBR IDN IND ITA JPN KEN KOR LKA MAR MEX MYS NGA NLD NOR NZL PAK PER PHL POL SWE THA TUR USA VNM ZAF".split())
HELD_COUNTRIES = tuple("AUT BEL BGR CHE CYP CZE GRC HKG HRV HUN IRL ISL ISR LTU LUX LVA MKD MLT PRT ROU RUS SGP SRB SVK SVN".split())
BIS_TO_ISO3 = dict(zip(
    "AT BE BG CH CY CZ GR HK HR HU IE IS IL LT LU LV MK MT PT RO RU SG RS SK SI".split(),
    HELD_COUNTRIES,
))
SOURCE_FILES = {
    "property": {
        "source": "bis:WS_SPP",
        "path": "data/vintages/bis/WS_SPP@2026-07-23T151601Z.parquet",
        "sha256": "2d21f842356c92d9d8698e350e693add58505c67569a932cd735843ec085c583",
        "manifest": "data/manifests/fetch_run_2026-07-23T151632Z.yaml",
        "series_id": "WS_SPP",
        "source_url": "https://stats.bis.org/api/v2/data/dataflow/BIS/WS_SPP/1.0/?format=csv",
        "dimensions": {"FREQ": "Q", "VALUE": "R", "UNIT_MEASURE": 771,
                       "OBS_STATUS": "A", "quarter": "Q4"},
    },
    "income": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.PCAP.KD",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json",
        "indicator_id": "NY.GDP.PCAP.KD",
    },
    "rule": {
        "source": "wgi:RL.EST",
        "path": "data/vintages/wgi/RL.EST@2026-04-30T114245Z.parquet",
        "sha256": "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "series_id": "RL.EST",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/RL.EST?format=json&source=3",
        "indicator_id": "GOV_WGI_RL.EST",
    },
}
COLUMNS = ("term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
           "n_countries", "r_squared", "method")


def git_show(rev: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{rev}:{relative}"], cwd=ROOT,
                            capture_output=True)
    if result.returncode:
        raise RuntimeError(f"missing committed file {rev}:{relative}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pair(spec: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    variables = spec.get("variables") or {}
    return tuple(tuple(sorted({x["source"] for x in variables.get(role, [])
                               if isinstance(x, dict) and x.get("source")}))
                 for role in ("treatment", "outcome"))


def verify_old() -> None:
    old = yaml.safe_load(git_show(OLD_COMMIT, f"hypotheses/housing/{OLD_ID}.yaml"))
    diag = json.loads(git_show(OLD_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"))
    runner = git_show(OLD_COMMIT, "scripts/run_panel_fe.py").decode()
    if (tuple(sorted(old["sample"]["countries"])) != OLD_COUNTRIES
            or pair(old) != (("bis:WS_SPP",), ("world_bank_wdi:NY.GDP.PCAP.KD",))
            or diag["verdict_label"] != "PARTIAL"
            or diag["estimate"]["n_obs"] != 757
            or diag["estimate"]["n_countries"] != 32):
        raise ValueError("historical source pair, roster, or result changed")
    if ('out = out[out["country_iso3"].isin(countries)]' not in runner
            or "panel_filt = filter_sample(panel, spec)" not in runner
            or "est = run_panel_ols(\n        panel_filt," not in runner):
        raise ValueError("historical fitted-country filter proof unavailable")
    if set(OLD_COUNTRIES) & set(HELD_COUNTRIES):
        raise ValueError("old and held-out country rosters overlap")


def assert_distinct_strict_pair() -> None:
    target = (("bis:WS_SPP",), ("world_bank_wdi:NY.GDP.PCAP.KD",))
    for path in (ROOT / "hypotheses").rglob("*.yaml"):
        if path == ROOT / SPEC_REL:
            continue
        try:
            item = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if item.get("status") == "pre_registered" and pair(item) == target:
            raise ValueError(f"strict source-pair duplicate: {path}")


def verify_spec() -> dict[str, Any]:
    verify_old()
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    frozen = {
        "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
        "family_alpha": FAMILY_ALPHA, "family_p_max": P_MAX,
        "expected_sign": "-", "min_observations": MIN_OBS,
        "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_YEARS_PER_COUNTRY,
        "old_hypothesis_id": OLD_ID, "old_result_bucket": "PARTIAL",
        "old_n_obs": 757, "old_n_countries": 32,
        "old_spec_commit": OLD_COMMIT, "old_run_commit": OLD_COMMIT,
        "old_country_count": 40, "old_country_ids": list(OLD_COUNTRIES),
        "heldout_country_ids": list(HELD_COUNTRIES),
        "school_score_credit": 0, "school_score_eligible": False,
        "source_files": SOURCE_FILES,
    }
    if spec["falsification"]["threshold"] != frozen:
        raise ValueError("frozen threshold or source pins changed")
    if (spec.get("hypothesis_id") != ID
            or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("claim_direction") != "-"
            or spec["sample"]["countries"] != list(HELD_COUNTRIES)
            or spec["sample"]["period"] != [START_YEAR, END_YEAR]
            or spec.get("scope", {}).get("countries") != list(HELD_COUNTRIES)
            or spec.get("steelman") != STEELMAN_REL
            or not (ROOT / STEELMAN_REL).is_file()
            or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or pair(spec) != (("bis:WS_SPP",), ("world_bank_wdi:NY.GDP.PCAP.KD",))
            or spec["estimator"].get("fixed_effects") != ["country", "year"]
            or spec["estimator"].get("clustering") != "country"):
        raise ValueError("registration, variable pair, or estimator changed")
    expected = {
        "outcome": [("next_year_real_gdp_pc_log_growth_pct", SOURCE_FILES["income"]["source"])],
        "treatment": [(PRIMARY, SOURCE_FILES["property"]["source"])],
        "controls": [("log_real_gdp_pc_t", SOURCE_FILES["income"]["source"]),
                     ("current_real_gdp_pc_log_growth_pct", SOURCE_FILES["income"]["source"]),
                     ("rule_of_law_t", SOURCE_FILES["rule"]["source"])],
    }
    actual = {role: [(x["name"], x["source"]) for x in spec["variables"][role]]
              for role in expected}
    if actual != expected:
        raise ValueError("registered measured variables changed")
    assert_distinct_strict_pair()
    return spec


def verify_sources() -> None:
    for pin in SOURCE_FILES.values():
        path = (ROOT / pin["path"]).resolve()
        if (not path.is_relative_to(ROOT.resolve()) or not path.is_file()
                or sha256(path) != pin["sha256"]):
            raise ValueError(f"pinned source absent or changed: {pin['path']}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text(encoding="utf-8"))
        if not any(all(row.get(key) == pin[key]
                       for key in ("parquet_path", "sha256", "series_id", "source_url")
                       if key != "parquet_path")
                   and row.get("parquet_path") == pin["path"]
                   for row in manifest.get("entries", [])):
            raise ValueError(f"pinned source missing from manifest: {pin['path']}")


def keyed_source(role: str, *, values: bool):
    import pandas as pd
    pin = SOURCE_FILES[role]
    columns = (["FREQ", "REF_AREA", "VALUE", "UNIT_MEASURE", "period", "OBS_STATUS"]
               if role == "property" else ["country_iso3", "year", "indicator_id"])
    if values:
        columns.append("value")
    frame = pd.read_parquet(ROOT / pin["path"], columns=columns)
    if role == "property":
        for dimension, required in pin["dimensions"].items():
            if dimension != "quarter":
                frame = frame[frame[dimension] == required]
        frame = frame[frame["period"].astype(str).str.fullmatch(r"\d{4}-Q4")].copy()
        frame = frame[frame["REF_AREA"].isin(BIS_TO_ISO3)].copy()
        frame["country_iso3"] = frame["REF_AREA"].map(BIS_TO_ISO3)
        frame["year"] = frame["period"].str[:4].astype(int)
    else:
        frame = frame[(frame["country_iso3"].isin(HELD_COUNTRIES))
                      & (frame["indicator_id"] == pin["indicator_id"])].copy()
        frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
        frame = frame[frame["year"].notna()].copy()
        frame["year"] = frame["year"].astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate country/year keys in pinned {role} source")
    return frame[["country_iso3", "year", *(["value"] if values else [])]]


def preflight() -> dict[str, Any]:
    verify_spec()
    verify_sources()
    property_keys = set(keyed_source("property", values=False).itertuples(index=False, name=None))
    income_keys = set(keyed_source("income", values=False).itertuples(index=False, name=None))
    rule_keys = set(keyed_source("rule", values=False).itertuples(index=False, name=None))
    keys = {(country, year) for country, year in property_keys
            if START_YEAR <= year <= END_YEAR
            and (country, year - 1) in income_keys
            and (country, year) in income_keys
            and (country, year + 1) in income_keys
            and (country, year) in rule_keys}
    counts = Counter(country for country, _ in keys)
    keys = {(country, year) for country, year in keys
            if counts[country] >= MIN_YEARS_PER_COUNTRY}
    result = {
        "hypothesis_id": ID, "key_pairs_upper_bound": len(keys),
        "key_countries_upper_bound": len({country for country, _ in keys}),
        "old_countries_excluded": len(OLD_COUNTRIES),
        "old_country_overlap": len({country for country, _ in keys} & set(OLD_COUNTRIES)),
        "complete_case_coverage_verified": False, "outcome_values_loaded": False,
        "coefficient_estimated": False, "counts_are_upper_bounds": True,
    }
    result["key_envelope_passed"] = (
        result["key_pairs_upper_bound"] >= MIN_OBS
        and result["key_countries_upper_bound"] >= MIN_COUNTRIES
        and result["old_country_overlap"] == 0)
    return result


def registration_commit() -> str:
    # New ignored source slices must be added in the same commit as this runner,
    # spec, and steelman; WDI income is already tracked in the branch.
    first_add = [RUNNER_REL, SPEC_REL, STEELMAN_REL,
                 SOURCE_FILES["property"]["path"], SOURCE_FILES["rule"]["path"]]
    additions = []
    for relative in first_add:
        if git_show("HEAD", relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"commit unchanged preregistration before values: {relative}")
        result = subprocess.run(["git", "log", "--diff-filter=A", "--reverse", "--format=%H",
                                 "--", relative], cwd=ROOT, capture_output=True, text=True)
        commits = result.stdout.strip().splitlines()
        if result.returncode or not commits:
            raise RuntimeError(f"no first-addition commit: {relative}")
        additions.append(commits[0])
    if len(set(additions)) != 1:
        raise RuntimeError("runner, registration, steelman, and source slices were not first added together")
    commit = additions[0]
    for relative in first_add:
        if git_show(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"first-addition bytes changed: {relative}")
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", commit, "--", RUN_REL],
                            cwd=ROOT, capture_output=True, text=True)
    if result.returncode or result.stdout.strip():
        raise RuntimeError("run artifacts existed at preregistration commit")
    return commit


def annual_source(role: str):
    import numpy as np
    import pandas as pd
    frame = keyed_source(role, values=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame[np.isfinite(frame["value"])].copy()
    if role == "income":
        frame = frame[frame["value"] > 0]
    return frame


def build_panel():
    import numpy as np
    property_frame = annual_source("property").rename(columns={"value": PRIMARY})
    income = annual_source("income")
    current = income.rename(columns={"value": "income_t"})
    previous = income.rename(columns={"value": "income_t_minus_1"}).copy()
    previous["year"] += 1
    future = income.rename(columns={"value": "income_t_plus_1"}).copy()
    future["year"] -= 1
    rule = annual_source("rule").rename(columns={"value": "rule_of_law_t"})
    panel = property_frame
    for frame in (current, previous, future, rule):
        panel = panel.merge(frame, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel[panel["year"].between(START_YEAR, END_YEAR)].copy()
    panel["next_year_real_gdp_pc_log_growth_pct"] = 100.0 * (
        np.log(panel["income_t_plus_1"]) - np.log(panel["income_t"]))
    panel["current_real_gdp_pc_log_growth_pct"] = 100.0 * (
        np.log(panel["income_t"]) - np.log(panel["income_t_minus_1"]))
    panel["log_real_gdp_pc_t"] = np.log(panel["income_t"])
    needed = [PRIMARY, "next_year_real_gdp_pc_log_growth_pct", "log_real_gdp_pc_t",
              "current_real_gdp_pc_log_growth_pct", "rule_of_law_t"]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=needed)
    counts = panel.groupby("country_iso3")["year"].transform("size")
    panel = panel[counts >= MIN_YEARS_PER_COUNTRY].copy()
    if set(panel["country_iso3"]) & set(OLD_COUNTRIES):
        raise AssertionError("historical-country row entered geographic holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate():
    import statsmodels.formula.api as smf
    panel = build_panel()
    countries = int(panel["country_iso3"].nunique())
    gate = {"observations": len(panel), "countries": countries,
            "old_country_overlap": 0,
            "treatment_years": [int(panel["year"].min()), int(panel["year"].max())]
            if len(panel) else [],
            "min_country_years": int(panel.groupby("country_iso3")["year"].size().min())
            if len(panel) else 0}
    gate["passed"] = (gate["observations"] >= MIN_OBS and countries >= MIN_COUNTRIES
                      and gate["min_country_years"] >= MIN_YEARS_PER_COUNTRY)
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "frozen complete-case sample floor failed", None
    formula = ("next_year_real_gdp_pc_log_growth_pct ~ " + PRIMARY
               + " + log_real_gdp_pc_t + current_real_gdp_pc_log_growth_pct"
               + " + rule_of_law_t + C(country_iso3) + C(year)")
    try:
        fit = smf.ols(formula, data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["country_iso3"],
                                          "use_correction": True, "df_correction": True},
            use_t=True)
        coefficient = float(fit.params[PRIMARY])
        std_error = float(fit.bse[PRIMARY])
        p_value = float(fit.pvalues[PRIMARY])
        ci95 = [float(x) for x in fit.conf_int().loc[PRIMARY].tolist()]
        if (fit.model.rank < fit.model.exog.shape[1] or std_error <= 0
                or not all(math.isfinite(x) for x in (coefficient, std_error, p_value, *ci95))):
            raise ValueError("rank-deficient or nonfinite primary estimate")
    except Exception as error:
        return gate, "INCONCLUSIVE", f"primary estimator failed: {type(error).__name__}: {error}", None
    if coefficient < 0 and p_value <= P_MAX:
        verdict, reason = "SUPPORTED", "negative price-growth coefficient cleared the frozen 84-test family cutoff"
    elif coefficient > 0 and p_value <= P_MAX:
        verdict, reason = "REFUTED", "positive price-growth coefficient cleared the frozen 84-test family cutoff"
    else:
        verdict, reason = "PARTIAL", "method-valid coefficient did not clear the frozen directional cutoff"
    row = {"coefficient": coefficient, "std_error": std_error, "p_value": p_value,
           "ci95": ci95, "n_obs": len(panel), "n_countries": countries,
           "r_squared": float(fit.rsquared),
           "method": f"country/year FE OLS; country-clustered small-sample t({countries - 1}) inference"}
    return gate, verdict, reason, row


def expected_artifacts(commit: str, gate: dict[str, Any], verdict: str, reason: str,
                       row: dict[str, Any] | None, stamp: str):
    inputs = [{"role": role, **pin} for role, pin in SOURCE_FILES.items()]
    correction = {"disposition": "descriptive_calibration_only",
                  "school_score_eligible": False, "school_score_credit": 0}
    limits = [
        "Old same-commit land-use/real-wage proxy result was PARTIAL and seen before this registration.",
        "The country-disjoint sample can share source years or units with other IESET studies.",
        "Residential price changes do not measure zoning, affordability, or wages.",
        "Lagged association does not identify a housing-policy effect or causal direction.",
        "No school, welfare, policy, or causal credit.",
    ]
    diagnostics = {"hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
                   "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
                   "preregistration_commit": commit, "template": "panel_fe",
                   "preflight": gate, "estimate": row,
                   "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
                   "family_p_max": P_MAX,
                   "data_status": {"variables_missing": [], "input_vintages": inputs},
                   "limitations": limits, "correction": correction}
    manifest = {"hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER_REL,
                "preregistration_commit": commit, "status": verdict,
                "old_hypothesis_id": OLD_ID, "old_verdict": "PARTIAL",
                "old_run_commit": OLD_COMMIT, "vintages": inputs,
                "derived_panel": gate, "correction": correction}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "housing"},
              "preregistration": {"spec_commit": commit, "steelman": STEELMAN_REL,
                                  "family_id": FAMILY_ID, "family_size": FAMILY_SIZE,
                                  "family_p_max": P_MAX},
              "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                               "command": f"python3 {RUNNER_REL} --check"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": inputs, "old_country_overlap": 0},
              "results": row, "limitations": limits, "correction": correction}
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Historical proxy screen: {OLD_ID} (same-commit PARTIAL; no prospective credit).\n"
            f"Preregistration commit: {commit}.\n"
            f"Held-out sample: {gate['observations']} country-year pairs, {gate['countries']} countries, zero old-country overlap.\n"
            f"Bonferroni cutoff for 84 screened opportunities: two-sided p <= {P_MAX:.9f}.\n")
    if row:
        card += (f"Primary coefficient: {row['coefficient']:+.6g}; country-clustered SE "
                 f"{row['std_error']:.6g}; p={row['p_value']:.6g}.\n")
    card += "\nMeasured association only; no land-use, wage, causal, policy, or school-score credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "coefficient": row["coefficient"] if row else None,
             "ci95": row["ci95"] if row else None,
             "family_p_max": P_MAX}
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
    if (diagnostics.get("preregistration_commit") != commit
            or diagnostics.get("preflight") != gate
            or diagnostics.get("verdict_label") != verdict
            or diagnostics.get("verdict_reason") != reason):
        raise AssertionError("rerun gate or verdict mismatch")
    saved = diagnostics.get("estimate")
    if (saved is None) != (row is None):
        raise AssertionError("rerun estimate presence mismatch")
    if row:
        for key, value in row.items():
            if isinstance(value, float) and not math.isclose(
                    float(saved[key]), value, rel_tol=1e-8, abs_tol=1e-10):
                raise AssertionError(f"rerun {key} mismatch")
            if isinstance(value, list) and any(
                    not math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-10)
                    for x, y in zip(saved[key], value)):
                raise AssertionError(f"rerun {key} mismatch")
            if not isinstance(value, (float, list)) and saved[key] != value:
                raise AssertionError(f"rerun {key} mismatch")
    expected = expected_artifacts(commit, gate, verdict, reason, row, diagnostics["run_utc"])
    actual = [diagnostics, yaml.safe_load((path / "manifest.yaml").read_text()),
              yaml.safe_load((path / "evidence_packet.yaml").read_text()),
              (path / "result_card.md").read_text(), (path / "replication.py").read_text(),
              json.loads((path / "chart_data.json").read_text())]
    for observed, should in zip(actual, expected[:6]):
        if observed != should:
            raise AssertionError("stored evidence artifact mismatch")
    table = pd.read_parquet(path / "coefficients.parquet")
    if list(table.columns) != list(COLUMNS) or len(table) != len(expected[6]):
        raise AssertionError("stored coefficient table mismatch")
    for observed, should in zip(table.to_dict(orient="records"), expected[6]):
        for key in COLUMNS:
            if key == "ci95":
                left = list(observed[key])
                right = should[key]
                if len(left) != len(right) or any(
                        not math.isclose(float(x), float(y), rel_tol=1e-8, abs_tol=1e-10)
                        for x, y in zip(left, right)):
                    raise AssertionError("stored coefficient interval mismatch")
            elif key in {"coefficient", "std_error", "p_value", "r_squared"}:
                if not math.isclose(float(observed[key]), float(should[key]),
                                    rel_tol=1e-8, abs_tol=1e-10):
                    raise AssertionError(f"stored coefficient {key} mismatch")
            elif observed[key] != should[key]:
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
    commit = registration_commit()  # Before any value-column read.
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
