#!/usr/bin/env python3
"""Frozen, two-year OECD ALMP × baseline EPL descriptive calibration.

--preflight reads source keys and categorical dimensions only. --extract-slice
can read magnitudes only after the design/runner first-addition commit. --run
requires a separately committed, exactly reproducible selected source slice.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_almp_epl_low_education_unemployment_temporal_holdout_v2"
OLD_ID = "oecd_almp_epl_low_education_unemployment_interaction_panel"
OLD_RUN_COMMIT = "441b76cba266e45285ffc1e4bdc81dc303a88e29"
SPEC_REL = f"hypotheses/labour/{ID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{ID}.md"
RUNNER_REL = f"scripts/run_{ID}.py"
SLICE_REL = f"data/derived/{ID}_source_slice.json"
RUN_REL = f"engine/runs/{ID}"
ROSTER = tuple("AUS AUT BEL BGR CAN CHE CHL COL CRI CZE DEU DNK ESP EST FIN FRA GBR GRC HRV HUN IRL ISL ISR ITA JPN KOR LTU LUX LVA MEX NLD NOR NZL PER POL PRT ROU SVK SVN SWE TUR USA".split())
SOURCE_COLUMNS = {
    "outcome": ["REF_AREA", "SEX", "AGE", "ATTAINMENT_LEV", "period"],
    "almp": ["REF_AREA", "UNIT_MEASURE", "EXPEND_SOURCE", "SPENDING_TYPE", "PROGRAMME_TYPE", "PRICE_BASE", "period"],
    "epl": ["country", "year", "indicator"],
    "gdp": ["country_iso3", "year", "indicator_id"],
}
COUNTRY_NAME_TO_ISO3 = {
    "Australia": "AUS", "Austria": "AUT", "Belgium": "BEL", "Canada": "CAN",
    "Chile": "CHL", "Colombia": "COL", "Costa Rica*": "CRI", "Czech Republic": "CZE",
    "Denmark": "DNK", "Estonia": "EST", "Finland": "FIN", "France": "FRA",
    "Germany": "DEU", "Greece": "GRC", "Hungary": "HUN", "Iceland": "ISL",
    "Ireland": "IRL", "Israel": "ISR", "Italy": "ITA", "Japan": "JPN",
    "Korea": "KOR", "Latvia": "LVA", "Lithuania": "LTU", "Luxembourg": "LUX",
    "Mexico": "MEX", "Netherlands": "NLD", "New Zealand": "NZL", "Norway": "NOR",
    "Poland": "POL", "Portugal": "PRT", "Slovak Republic": "SVK", "Slovenia": "SVN",
    "Spain": "ESP", "Sweden": "SWE", "Switzerland": "CHE", "Turkiye": "TUR",
    "Türkiye": "TUR", "United Kingdom": "GBR", "United States": "USA",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_bytes(revision: str, relative: str) -> bytes:
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
    if result.returncode:
        raise ValueError(f"missing committed file {revision}:{relative}")
    return result.stdout


def first_addition(relative: str) -> str:
    result = subprocess.run(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
        cwd=ROOT, capture_output=True, text=True,
    )
    commits = result.stdout.strip().splitlines()
    if result.returncode or len(commits) != 1:
        raise ValueError(f"expected one first-addition commit for {relative}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    if older == newer:
        return False
    return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT).returncode == 0


def verify_design() -> tuple[dict[str, Any], str]:
    old = yaml.safe_load(git_bytes(OLD_RUN_COMMIT, f"hypotheses/labour/{OLD_ID}.yaml"))
    if (old["sample"]["period"] != [1996, 2019]
            or old["variables"]["outcome"][0]["source"] != "oecd:DSD_LMS_low_education_unemployment_rate"
            or old["variables"]["treatment"][0]["source"] != "oecd:DSD_SOCX@DF_SOCX_AGG"):
        raise ValueError("old fitted-period/source boundary differs")
    if not git_bytes(OLD_RUN_COMMIT, f"engine/runs/{OLD_ID}/diagnostics.json"):
        raise ValueError("old run missing at committed boundary")
    additions = [first_addition(p) for p in (SPEC_REL, STEELMAN_REL, RUNNER_REL)]
    if (len(set(additions)) != 1 or subprocess.run(
            ["git", "merge-base", "--is-ancestor", additions[0], "HEAD"],
            cwd=ROOT).returncode != 0):
        raise ValueError("design/runner were not jointly preregistered before this HEAD")
    for p in (SPEC_REL, STEELMAN_REL, RUNNER_REL):
        if git_bytes(additions[0], p) != (ROOT / p).read_bytes():
            raise ValueError(f"registered design or runner changed: {p}")
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": "oecd_almp_epl_temporal_calibration_2026_10_09",
        "family_size": 1, "family_alpha": 0.01, "family_p_max": 0.01,
        "min_countries": 30, "min_observations": 60,
        "exposure_years": [2020, 2021], "outcome_years": [2021, 2022],
        "baseline_epl_year": 2019, "baseline_epl_center": 1.0,
        "fixed_key_upper_bound": 73, "both_year_key_countries": 36,
        "old_hypothesis_id": OLD_ID, "old_registered_period": [1996, 2019],
        "old_run_commit": OLD_RUN_COMMIT,
        "school_score_eligible": False, "school_score_credit": 0,
        "source_files": threshold["source_files"],
    }
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("claim_direction") != "+"
            or spec["sample"]["countries"] != list(ROSTER)
            or spec["sample"]["period"] != [2020, 2022]
            or spec["estimator"]["template"] != "panel_fe"
            or spec["estimator"]["fixed_effects"] != ["country", "year"]
            or spec["estimator"]["clustering"] != "country"
            or spec.get("steelman") != STEELMAN_REL
            or any(spec.get(k) != [] for k in ("covers_claims", "linked_hypotheses", "linked_conditions"))
            or {k: v for k, v in threshold.items() if k != "source_files"}
            != {k: v for k, v in expected.items() if k != "source_files"}):
        raise ValueError("registered design differs from frozen runner")
    return spec, additions[0]


def verify_sources(spec: dict[str, Any]) -> dict[str, dict[str, str]]:
    pins = spec["falsification"]["threshold"]["source_files"]
    if set(pins) != set(SOURCE_COLUMNS):
        raise ValueError("source roles changed")
    for role, pin in pins.items():
        raw = ROOT / pin["path"]
        manifest = ROOT / pin["manifest"]
        if not raw.is_file() or sha256(raw) != pin["sha256"]:
            raise ValueError(f"source vintage missing or changed: {role}")
        if (sha256(manifest) != pin["manifest_sha256"]
                or git_bytes("HEAD", pin["manifest"]) != manifest.read_bytes()):
            raise ValueError(f"source manifest changed: {role}")
        doc = yaml.safe_load(manifest.read_text(encoding="utf-8"))
        if not any(e.get("parquet_path") == pin["path"] and e.get("sha256") == pin["sha256"]
                   for e in doc.get("entries", [])):
            raise ValueError(f"source pin absent from publisher manifest: {role}")
        if role == "gdp" and git_bytes("HEAD", pin["path"]) != raw.read_bytes():
            raise ValueError("tracked WDI control differs from HEAD")
    return pins


def selected_key(role: str, row: dict[str, Any]) -> tuple[str, int] | None:
    if role == "outcome":
        country, year = row["REF_AREA"], row["period"]
        if (row["SEX"], row["AGE"], row["ATTAINMENT_LEV"]) != ("_T", "Y25T64", "ISCED11A_0T2"):
            return None
        years = (2021, 2022)
    elif role == "almp":
        country, year = row["REF_AREA"], row["period"]
        if (row["UNIT_MEASURE"], row["EXPEND_SOURCE"], row["SPENDING_TYPE"],
                row["PROGRAMME_TYPE"], row["PRICE_BASE"]) != ("PT_B1GQ", "ES10", "_T", "TP60", "_Z"):
            return None
        years = (2020, 2021)
    elif role == "epl":
        country, year = COUNTRY_NAME_TO_ISO3.get(str(row["country"])), row["year"]
        if row["indicator"] != "EPR_V1":
            return None
        years = (2019,)
    else:
        country, year = row["country_iso3"], row["year"]
        if row["indicator_id"] != "NY.GDP.MKTP.KD.ZG":
            return None
        years = (2020, 2021)
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None
    if country not in ROSTER or y not in years:
        return None
    return str(country), y


def selected_rows(role: str, path: Path, *, values: bool) -> list[tuple[tuple[str, int], Any]]:
    import pyarrow.parquet as pq
    columns = SOURCE_COLUMNS[role] + (["value"] if values else [])
    table = pq.read_table(path, columns=columns).to_pydict()
    rows = []
    for i in range(len(next(iter(table.values())))):
        row = {k: v[i] for k, v in table.items()}
        key = selected_key(role, row)
        if key is not None:
            rows.append((key, row.get("value")))
    counts = Counter(key for key, _ in rows)
    duplicates = [key for key, count in counts.items() if count != 1]
    if duplicates:
        raise ValueError(f"duplicate selected {role} country/year keys: {duplicates[:5]}")
    return rows


def key_only_preflight() -> dict[str, Any]:
    spec, _ = verify_design()
    pins = verify_sources(spec)
    rows = {role: selected_rows(role, ROOT / pin["path"], values=False)
            for role, pin in pins.items()}
    keys = {role: {key for key, _ in group} for role, group in rows.items()}
    overlap = {(country, t) for country in ROSTER for t in (2020, 2021)
               if (country, t + 1) in keys["outcome"]
               and (country, t) in keys["almp"]
               and (country, 2019) in keys["epl"]
               and (country, t) in keys["gdp"]}
    paired = [country for country in ROSTER if all((country, t) in overlap for t in (2020, 2021))]
    return {
        "key_only": True, "magnitudes_inspected": False, "null_masks_inspected": False,
        "selected_source_key_counts": {role: len(k) for role, k in keys.items()},
        "intersection_country_year_keys": len(overlap),
        "intersection_countries": len({country for country, _ in overlap}),
        "both_year_key_countries": len(paired),
        "both_year_countries": paired,
    }


def parse_number(value: Any, low: float, high: float) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and low <= number <= high else None


def build_slice() -> dict[str, Any]:
    spec, prereg = verify_design()
    pins = verify_sources(spec)
    preflight = key_only_preflight()
    raw = {role: dict(selected_rows(role, ROOT / pin["path"], values=True))
           for role, pin in pins.items()}
    complete: list[dict[str, Any]] = []
    invalid_by_role: Counter[str] = Counter()
    for country in ROSTER:
        both = []
        epl = parse_number(raw["epl"].get((country, 2019)), 0, 6)
        for year in (2020, 2021):
            values = {
                "outcome": parse_number(raw["outcome"].get((country, year + 1)), 0, 100),
                "almp": parse_number(raw["almp"].get((country, year)), 0, 10),
                "epl": epl,
                "gdp": parse_number(raw["gdp"].get((country, year)), -100, 100),
            }
            missing = [role for role, value in values.items() if value is None]
            if missing:
                invalid_by_role.update(missing)
                continue
            both.append({
                "country": country, "exposure_year": year, "outcome_year": year + 1,
                "almp_spending_pct_gdp": values["almp"],
                "baseline_epl_2019": values["epl"],
                "real_gdp_growth_pct": values["gdp"],
                "next_year_low_education_unemployment_pct": values["outcome"],
            })
        if len(both) == 2:
            complete.extend(both)
    return {
        "schema": "ieset_oecd_almp_epl_temporal_source_slice_v1",
        "hypothesis_id": ID,
        "preregistration_commit": prereg,
        "source_files_sha256": {role: pin["sha256"] for role, pin in pins.items()},
        "key_only_preflight": preflight,
        "complete_country_count": len(complete) // 2,
        "complete_country_year_count": len(complete),
        "invalid_candidate_role_counts": dict(sorted(invalid_by_role.items())),
        "rows": complete,
    }


def canonical_json(doc: Any) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def verify_slice() -> tuple[dict[str, Any], str]:
    _, prereg = verify_design()
    slice_commit = first_addition(SLICE_REL)
    if not strict_ancestor(prereg, slice_commit):
        raise ValueError("source slice was not committed after preregistration")
    path = ROOT / SLICE_REL
    if (not path.is_file() or git_bytes("HEAD", SLICE_REL) != path.read_bytes()
            or path.read_bytes() != canonical_json(build_slice())):
        raise ValueError("committed source slice differs from pinned-source extraction")
    return json.loads(path.read_text(encoding="utf-8")), slice_commit


def estimate(slice_doc: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    import numpy as np
    import statsmodels.api as sm
    from scipy.stats import t as student_t

    grouped: dict[str, dict[int, dict[str, Any]]] = {}
    for row in slice_doc["rows"]:
        grouped.setdefault(row["country"], {})[row["exposure_year"]] = row
    countries = sorted(grouped)
    if len(countries) < 30 or len(slice_doc["rows"]) < 60:
        return "INCONCLUSIVE", "frozen complete-case floor failed", None
    y, x = [], []
    for country in countries:
        if set(grouped[country]) != {2020, 2021}:
            raise ValueError("unbalanced source slice")
        before, after = grouped[country][2020], grouped[country][2021]
        if before["baseline_epl_2019"] != after["baseline_epl_2019"]:
            raise ValueError("baseline EPL differs within country")
        delta_almp = after["almp_spending_pct_gdp"] - before["almp_spending_pct_gdp"]
        y.append(after["next_year_low_education_unemployment_pct"]
                 - before["next_year_low_education_unemployment_pct"])
        x.append([1.0, delta_almp,
                  delta_almp * (before["baseline_epl_2019"] - 1.0),
                  after["real_gdp_growth_pct"] - before["real_gdp_growth_pct"]])
    X, Y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if np.linalg.matrix_rank(X) != X.shape[1]:
        return "INCONCLUSIVE", "first-difference design is rank deficient", None
    fit = sm.OLS(Y, X).fit(cov_type="cluster", cov_kwds={"groups": countries, "use_correction": True})
    if not np.isfinite(fit.params).all() or not np.isfinite(fit.bse).all() or np.any(fit.bse <= 0):
        return "INCONCLUSIVE", "country-clustered uncertainty is nonfinite", None
    df = len(countries) - 1
    p = [float(2 * student_t.sf(abs(coef / se), df)) for coef, se in zip(fit.params, fit.bse)]
    if not all(math.isfinite(v) for v in p):
        return "INCONCLUSIVE", "Student t uncertainty is nonfinite", None
    names = ("intercept", "delta_almp_at_epl_1", "delta_almp_x_baseline_epl_minus_1", "delta_real_gdp_growth")
    coefficients = {name: {"coefficient": float(fit.params[i]), "std_error": float(fit.bse[i]),
                           "p_value_two_sided_t_country_minus_1": p[i]} for i, name in enumerate(names)}
    bmain, bint = float(fit.params[1]), float(fit.params[2])
    if bint > 0 and p[2] <= 0.01 and bmain < 0:
        verdict, reason = "SUPPORTED", "positive interaction passes 0.01 and ALMP slope at EPL=1 is negative"
    elif bint < 0 and p[2] <= 0.01:
        verdict, reason = "REFUTED", "negative interaction passes 0.01"
    else:
        verdict, reason = "PARTIAL", "registered interaction and main-slope rule did not resolve the claim"
    return verdict, reason, {
        "n_countries": len(countries), "n_country_year_pairs": len(slice_doc["rows"]),
        "countries": countries, "first_difference_years": [2020, 2021],
        "outcome_years": [2021, 2022], "degrees_of_freedom_for_t": df,
        "r_squared": float(fit.rsquared), "coefficients": coefficients,
        "method": "balanced country first differences with exposure-year intercept; country-clustered CR1 and t(G-1)",
    }


def make_outputs(slice_doc: dict[str, Any], slice_commit: str, run_utc: str) -> dict[str, bytes]:
    spec, prereg = verify_design()
    pins = verify_sources(spec)
    verdict, reason, fit = estimate(slice_doc)
    data_status = {
        "variables_missing": [],
        "input_vintages": [{"role": role, "path": pin["path"], "sha256": pin["sha256"],
                             "manifest": pin["manifest"], "manifest_sha256": pin["manifest_sha256"]}
                            for role, pin in pins.items()],
        "selected_slice": {"path": SLICE_REL, "sha256": sha256(ROOT / SLICE_REL)},
        "complete_country_year_pairs": slice_doc["complete_country_year_count"],
        "complete_countries": slice_doc["complete_country_count"],
    }
    diagnostics = {
        "hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": run_utc, "runner": RUNNER_REL,
        "preregistration_commit": prereg, "source_slice_commit": slice_commit,
        "template": "panel_fe", "estimate": fit,
        "family_id": "oecd_almp_epl_temporal_calibration_2026_10_09",
        "family_size": 1, "family_p_max": 0.01,
        "data_status": data_status,
        "correction": {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                       "school_score_credit": 0, "causal_credit": 0, "policy_score_credit": 0},
        "limitations": ["2020-2022 pandemic response and reopening can confound all coefficients.",
                        "SOCX is a spending/GDP ratio, not exogenous programme assignment.",
                        "Unemployment misses pandemic labour-force exits and job-retention hours losses.",
                        "Two-year within-country evidence cannot validate the old reform mechanism.",
                        "The 0.01 local threshold does not control the wider IESET search."],
    }
    packet = {
        "packet_version": 1, "generated_utc": run_utc,
        "hypothesis": {"id": ID, "path": SPEC_REL, "topic": "labour"},
        "preregistration": {"spec_commit": prereg, "steelman": STEELMAN_REL,
                            "family_id": diagnostics["family_id"], "family_size": 1, "family_p_max": 0.01},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUNNER_REL} --check"},
        "verdict": {"raw": verdict, "bucket": verdict.lower() if verdict != "INCONCLUSIVE" else "archive",
                    "reason": reason},
        "data": data_status,
        "results": {"first_difference": fit},
        "limitations": diagnostics["limitations"], "correction": diagnostics["correction"],
    }
    manifest = {
        "hypothesis_id": ID, "run_utc": run_utc, "runner": RUNNER_REL,
        "preregistration_commit": prereg, "source_slice_commit": slice_commit,
        "status": verdict, "old_hypothesis_id": OLD_ID, "old_run_commit": OLD_RUN_COMMIT,
        "vintages": data_status["input_vintages"], "selected_slice": data_status["selected_slice"],
        "derived_panel": {"complete_country_year_pairs": data_status["complete_country_year_pairs"],
                          "complete_countries": data_status["complete_countries"]},
        "correction": diagnostics["correction"],
    }
    interaction = fit["coefficients"]["delta_almp_x_baseline_epl_minus_1"] if fit else None
    card = [f"# {ID}", "", f"**Verdict: {verdict}** — {reason}.", "",
            "Out-of-time 2020–21 OECD ALMP spending change, moderated by 2019 EPL, versus the 2021–22 change in low-education unemployment.", ""]
    if interaction:
        card.extend([f"- Interaction coefficient: {interaction['coefficient']:.6g}; country-clustered SE {interaction['std_error']:.6g}; two-sided t p={interaction['p_value_two_sided_t_country_minus_1']:.6g}.",
                     f"- Complete sample: {fit['n_countries']} countries, {fit['n_country_year_pairs']} exposure/outcome pairs."])
    else:
        card.append(f"- Complete sample: {slice_doc['complete_country_count']} countries, {slice_doc['complete_country_year_count']} exposure/outcome pairs; registered estimator not identified.")
    card.extend(["", "This is descriptive COVID-period calibration only. It earns no causal, policy-effect, or school-score credit.",
                 "", f"Preregistration: `{prereg}`. Source slice: `{slice_commit}`.", ""])
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), '--check'], cwd=root))\n")
    return {
        "diagnostics.json": canonical_json(diagnostics),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
        "result_card.md": ("\n".join(card)).encode(),
        "chart_data.json": canonical_json({"hypothesis_id": ID, "verdict": verdict,
                                           "interaction": interaction, "n_countries": slice_doc["complete_country_count"]}),
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "replication.py": wrapper.encode(),
    }


def run(write: bool) -> str:
    slice_doc, slice_commit = verify_slice()
    run_dir = ROOT / RUN_REL
    if write:
        run_utc = datetime.now(timezone.utc).isoformat(timespec="seconds")
    else:
        run_utc = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))["run_utc"]
    outputs = make_outputs(slice_doc, slice_commit, run_utc)
    if write:
        run_dir.mkdir(parents=True, exist_ok=True)
        for name, data in outputs.items():
            (run_dir / name).write_bytes(data)
        fit = json.loads(outputs["diagnostics.json"])["estimate"]
        if fit:
            import pandas as pd
            coefficients = pd.DataFrame([{"term": term, **values} for term, values in fit["coefficients"].items()])
            coefficients.to_parquet(run_dir / "coefficients.parquet", index=False)
    else:
        for name, data in outputs.items():
            if not (run_dir / name).is_file() or (run_dir / name).read_bytes() != data:
                raise ValueError(f"result artifact differs from exact replay: {name}")
        fit = json.loads(outputs["diagnostics.json"])["estimate"]
        if fit:
            import pandas as pd
            actual = pd.read_parquet(run_dir / "coefficients.parquet")
            expected = pd.DataFrame([{"term": term, **values} for term, values in fit["coefficients"].items()])
            pd.testing.assert_frame_equal(actual, expected)
    return json.loads(outputs["diagnostics.json"])["verdict"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--extract-slice", action="store_true")
    mode.add_argument("--verify-source", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.preflight:
            print(json.dumps(key_only_preflight(), indent=2))
        elif args.extract_slice:
            doc = build_slice()
            path = ROOT / SLICE_REL
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_json(doc))
            print(f"selected slice: {doc['complete_country_count']} countries, {doc['complete_country_year_count']} rows")
        elif args.verify_source:
            doc, commit = verify_slice()
            print(f"source slice verified at {commit}: {doc['complete_country_count']} countries")
        else:
            print(f"{ID}: {run(write=args.run)}")
    except (ValueError, OSError, AssertionError) as exc:
        print(f"ERROR: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
