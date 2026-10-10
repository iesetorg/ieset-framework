#!/usr/bin/env python3
"""Frozen OECD-tax / EU-SILC later-outcome descriptive family.

--preflight reads hashes and source dimension keys only. Registration and four
separate source-lock commits must precede --run, the first selected-value read.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "eu_tax_social_holdout_2026_10_10"
RUNNER = "scripts/run_eu_tax_social_holdout_2026.py"
PREREG = "engine/audits/eu_tax_social_holdout_prereg_2026-10-10.md"
SUMMARY = "engine/audits/eu_tax_social_holdout_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/eu_tax_social_holdout_2026_key_roster.csv"
ROSTER_SHA = "44cf4948ee9ab46d90f462329a3e14be5e24dcc7cedb17a67fff315b29f4586c"
SOURCES = {
    "tax": {
        "publisher": "OECD", "series_id": "oecd_tax_total_pct_gdp",
        "path": "data/vintages/oecd/oecd_tax_total_pct_gdp@2026-07-23T153857Z.parquet",
        "sha256": "4b07558c8bc42192bff94a0f57dfcc412c56385b1ccb2061bcdd7743e51d11cd",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "source_url": "https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_REV_COMP_OECD@DF_RSOECD,2.0/.TAX_REV.S13.T_4200+T_4300+_T..PT_B1GQ.A?startPeriod=1990&endPeriod=2024&format=csvfilewithlabels",
        "license": "OECD standard permissions; attribution required",
    },
    "pit": {
        "publisher": "OECD", "series_id": "oecd_top_statutory_pit_rate",
        "path": "data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet",
        "sha256": "b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "source_url": "https://sdmx.oecd.org/public/rest/data/OECD.CTP.TPS,DSD_TAX_PIT@DF_PIT_TOP_EARN_THRESH,1.0/.A..TS_PIT.PT_WG_EARN_G.......?startPeriod=1990&endPeriod=2024&format=csvfilewithlabels",
        "license": "OECD standard permissions; attribution required",
    },
    "inwork": {
        "publisher": "Eurostat", "series_id": "ilc_iw01",
        "path": "data/vintages/eurostat/ilc_iw01@2026-04-30T115759Z.parquet",
        "sha256": "100a6bf3f962f53c05133b3e9a7e40f25db36bd03575d3fd7816a4368f1ab246",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/ilc_iw01/",
        "license": "CC BY 4.0",
    },
    "gini": {
        "publisher": "Eurostat", "series_id": "ilc_di12",
        "path": "data/vintages/eurostat/ilc_di12@2026-07-23T154401Z.parquet",
        "sha256": "9b1b03caebf74bf79ad77d5373b04841002ea80c017ff6e3cca884485a8adfa6",
        "manifest": "data/manifests/fetch_run_2026-07-23T154936Z.yaml",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/ilc_di12/",
        "license": "CC BY 4.0",
    },
    "bottom": {
        "publisher": "Eurostat", "series_id": "ilc_di01",
        "path": "data/vintages/eurostat/ilc_di01@2026-04-30T115754Z.parquet",
        "sha256": "6dc9948f57c6dc32e967628f541bbb19c894680ae7304b9de59fd50e641c29b5",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "source_url": "https://ec.europa.eu/eurostat/databrowser/view/ilc_di01/",
        "license": "CC BY 4.0",
    },
}
CASES = (
    ("eu_tax_receipts_inwork_poverty_forward_2026", "tax", "inwork", "-", "2023 tax-to-GDP and later change in employed-adult in-work poverty"),
    ("eu_tax_receipts_gini_forward_2026", "tax", "gini", "-", "2023 tax-to-GDP and later change in disposable-income Gini"),
    ("eu_top_pit_gini_forward_2026", "pit", "gini", "-", "2023 top statutory personal income tax rate and later change in disposable-income Gini"),
    ("eu_tax_receipts_bottom_quintile_forward_2026", "tax", "bottom", "+", "2023 tax-to-GDP and later change in the bottom-quintile disposable-income share"),
)
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / len(CASES)
MIN_N = 20
MIN_IQR = {"tax": 2.0, "pit": 5.0}
MAX_RESIDUAL_SHARE = 0.20
MAX_HAT_LEVERAGE = 0.30
MIN_ABS_BETA = 0.5  # outcome points per 10 exposure points
LIMITATIONS = [
    "2022 EU-SILC income outcomes refer mainly to 2021 income; 2025 income outcomes refer to 2024 income.",
    "These are 24-28-country ecological associations, not effects of tax legislation or transfers. Tax receipts, rates, and social outcomes share economic, demographic, energy-price, and survey confounding.",
    "Total tax receipts do not isolate transfer generosity or tax progressivity; the top statutory PIT rate does not measure effective tax burdens or enforcement.",
    "The four outcomes and two OECD tax measures overlap in countries and constructs. The four tests share one correction denominator and do not represent independent replications.",
    "No causal, policy, school, position, or featured credit is permitted.",
]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(rel: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"missing or ambiguous first addition: {rel}")
    return commits[0]


def unchanged(rel: str, revision: str) -> None:
    if (ROOT / rel).read_bytes() != git("show", f"{revision}:{rel}"):
        raise RuntimeError(f"frozen bytes changed: {rel}")
    if git("status", "--porcelain", "--", rel).strip():
        raise RuntimeError(f"uncommitted frozen path: {rel}")


def spec_rel(case: tuple[str, ...]) -> str:
    return f"hypotheses/distribution/{case[0]}.yaml"


def steel_rel(case: tuple[str, ...]) -> str:
    return f"hypotheses/steelman/{case[0]}.md"


def lock_rel(case: tuple[str, ...]) -> str:
    return f"data/pinned_evidence/{case[0]}.source.json"


def run_rel(case: tuple[str, ...]) -> str:
    return f"engine/runs/{case[0]}"


def checked_sources(source_root: Path) -> dict[str, Path]:
    paths = {}
    for name, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or changed pinned source: {name}")
        paths[name] = path
    return paths


def key_set(path: Path, columns: list[str], predicate) -> set[tuple[str, int]]:
    """Read dimension keys only; never project value or observation-status columns."""
    rows = pq.read_table(path, columns=columns).to_pylist()
    selected = []
    for row in rows:
        if predicate(row):
            selected.append((str(row["geo_code"]), int(row["period"])))
    if len(selected) != len(set(selected)):
        raise RuntimeError(f"duplicate selected source key: {path.name}")
    return set(selected)


def source_keys(paths: dict[str, Path]) -> dict[str, set]:
    result = {}
    for name in ("tax", "pit"):
        rows = pq.read_table(paths[name], columns=["country_iso3", "year"]).to_pylist()
        selected = [(str(r["country_iso3"]), int(r["year"])) for r in rows if r["year"] == 2023]
        if len(selected) != len(set(selected)):
            raise RuntimeError(f"duplicate 2023 tax source key: {name}")
        result[name] = set(selected)
    result["inwork"] = key_set(paths["inwork"], ["freq", "wstatus", "sex", "age", "unit", "geo_code", "period"],
                               lambda r: r["freq"] == "A" and r["wstatus"] == "EMP" and r["sex"] == "T"
                               and r["age"] == "Y18-64" and r["unit"] == "PC" and int(r["period"]) in (2022, 2025))
    result["gini"] = key_set(paths["gini"], ["freq", "age", "statinfo", "geo_code", "period"],
                             lambda r: r["freq"] == "A" and r["age"] == "TOTAL" and r["statinfo"] == "GINI_HND"
                             and int(r["period"]) in (2022, 2025))
    result["bottom"] = key_set(paths["bottom"], ["freq", "quantile", "indic_il", "currency", "geo_code", "period"],
                               lambda r: r["freq"] == "A" and r["quantile"] == "QU1" and r["indic_il"] == "SHARE"
                               and r["currency"] == "EUR" and int(r["period"]) in (2022, 2025))
    return result


def read_roster() -> list[dict[str, str]]:
    path = ROOT / ROSTER
    if sha256(path) != ROSTER_SHA:
        raise RuntimeError("frozen key roster checksum mismatch")
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 28 or list(rows[0]) != ["country_iso3", "eurostat_geo", "pit_2023_key"]:
        raise RuntimeError("frozen roster shape mismatch")
    if [r["country_iso3"] for r in rows] != sorted({r["country_iso3"] for r in rows}):
        raise RuntimeError("frozen roster must be unique and sorted")
    if Counter(r["pit_2023_key"] for r in rows) != {"1": 24, "0": 4}:
        raise RuntimeError("frozen PIT key count mismatch")
    return rows


def preflight(paths: dict[str, Path], roster: list[dict[str, str]]) -> None:
    keys = source_keys(paths)
    for row in roster:
        iso, geo = row["country_iso3"], row["eurostat_geo"]
        if (iso, 2023) not in keys["tax"]:
            raise RuntimeError(f"missing registered total-tax key: {iso}")
        if ((iso, 2023) in keys["pit"]) != (row["pit_2023_key"] == "1"):
            raise RuntimeError(f"registered PIT key disagrees with source: {iso}")
        for outcome in ("inwork", "gini", "bottom"):
            if (geo, 2022) not in keys[outcome] or (geo, 2025) not in keys[outcome]:
                raise RuntimeError(f"missing registered {outcome} key: {geo}")
    if len({r["eurostat_geo"] for r in roster}) != len(roster):
        raise RuntimeError("duplicate Eurostat geography in roster")


def threshold(case: tuple[str, ...]) -> dict[str, object]:
    return {"family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": case[3],
            "meaningful_beta_min_abs_per_10pp": MIN_ABS_BETA,
            "min_complete_countries": MIN_N, "min_exposure_iqr_pp": MIN_IQR[case[1]],
            "max_country_residualized_exposure_share": MAX_RESIDUAL_SHARE,
            "max_hat_leverage": MAX_HAT_LEVERAGE,
            "baseline_survey_year": 2022, "exposure_tax_year": 2023, "outcome_survey_year": 2025,
            "expected_key_countries": 24 if case[1] == "pit" else 28,
            "source_key_roster_sha256": ROSTER_SHA, "source_lock_path": lock_rel(case),
            "source_sha256": {name: SOURCES[name]["sha256"] for name in (case[1], case[2])},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    registered = [PREREG, RUNNER, ROSTER]
    for case in CASES:
        registered.extend((spec_rel(case), steel_rel(case)))
    commits = {first_addition(rel) for rel in registered}
    if len(commits) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = commits.pop()
    for rel in registered:
        unchanged(rel, revision)
    schema = json.loads(git("show", f"{revision}:schemas/hypothesis.schema.json"))
    validator = Draft202012Validator(schema)
    for case in CASES:
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if not validator.is_valid(spec) or spec.get("hypothesis_id") != case[0]:
            raise RuntimeError(f"original registration schema invalid: {case[0]}")
        if (spec["falsification"]["threshold"] != threshold(case)
                or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []):
            raise RuntimeError(f"original registration differs from frozen contract: {case[0]}")
        if git("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
            raise RuntimeError("registration commit already contains measured result")
    return revision


def lock_payload(case: tuple[str, ...], registration: str) -> dict[str, object]:
    return {"schema": "ieset-source-lock-v1", "family_id": FAMILY,
            "family_size": len(CASES), "hypothesis_id": case[0],
            "registration_commit": registration, "key_roster_sha256": ROSTER_SHA,
            "sources": [SOURCES[name] for name in (case[1], case[2])],
            "measurement_boundary": "Registered keys and rules were committed before selected tax or outcome values and null masks were inspected."}


def lock_commit(case: tuple[str, ...], registration: str) -> str:
    rel = lock_rel(case)
    revision = first_addition(rel)
    if revision == registration:
        raise RuntimeError("source lock cannot share registration commit")
    git("merge-base", "--is-ancestor", registration, revision)
    unchanged(rel, revision)
    if json.loads((ROOT / rel).read_text()) != lock_payload(case, registration):
        raise RuntimeError(f"source lock differs from frozen contract: {case[0]}")
    return revision


def selected_values(paths: dict[str, Path], roster: list[dict[str, str]]) -> dict[str, dict]:
    """The first projection of a selected `value` column occurs after all locks."""
    allowed_iso = {r["country_iso3"] for r in roster}
    allowed_geo = {r["eurostat_geo"] for r in roster}
    result: dict[str, dict] = {}
    for name in ("tax", "pit"):
        rows = pq.read_table(paths[name], columns=["country_iso3", "year", "value"]).to_pylist()
        selected = [(str(r["country_iso3"]), r["value"]) for r in rows
                    if r["country_iso3"] in allowed_iso and r["year"] == 2023]
        if len(selected) != len(dict(selected)):
            raise RuntimeError(f"duplicate selected tax value: {name}")
        result[name] = dict(selected)
    configs = {
        "inwork": (["freq", "wstatus", "sex", "age", "unit", "geo_code", "period", "value"],
                   lambda r: r["freq"] == "A" and r["wstatus"] == "EMP" and r["sex"] == "T"
                   and r["age"] == "Y18-64" and r["unit"] == "PC"),
        "gini": (["freq", "age", "statinfo", "geo_code", "period", "value"],
                 lambda r: r["freq"] == "A" and r["age"] == "TOTAL" and r["statinfo"] == "GINI_HND"),
        "bottom": (["freq", "quantile", "indic_il", "currency", "geo_code", "period", "value"],
                   lambda r: r["freq"] == "A" and r["quantile"] == "QU1" and r["indic_il"] == "SHARE"
                   and r["currency"] == "EUR"),
    }
    for name, (cols, pred) in configs.items():
        rows = pq.read_table(paths[name], columns=cols).to_pylist()
        selected = [((str(r["geo_code"]), int(r["period"])), r["value"]) for r in rows
                    if r["geo_code"] in allowed_geo and int(r["period"]) in (2022, 2025) and pred(r)]
        if len(selected) != len(dict(selected)):
            raise RuntimeError(f"duplicate selected Eurostat value: {name}")
        result[name] = dict(selected)
    return result


def finite_percentage(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and 0 <= number <= 100 else None


def measured_case(case: tuple[str, ...], roster: list[dict[str, str]], values: dict[str, dict]) -> dict[str, object]:
    _hypothesis, x_name, y_name, sign, _label = case
    complete = []
    missing = Counter()
    for row in roster:
        if x_name == "pit" and row["pit_2023_key"] != "1":
            continue
        iso, geo = row["country_iso3"], row["eurostat_geo"]
        x = finite_percentage(values[x_name].get(iso))
        y0 = finite_percentage(values[y_name].get((geo, 2022)))
        y1 = finite_percentage(values[y_name].get((geo, 2025)))
        for label, number in (("exposure", x), ("baseline", y0), ("outcome", y1)):
            if number is None:
                missing[f"{label}_missing_or_out_of_range"] += 1
        if None not in (x, y0, y1):
            complete.append((iso, x, y0, y1 - y0))
    n = len(complete)
    sample: dict[str, object] = {"key_countries": 24 if x_name == "pit" else 28,
                                 "complete_countries": n, "excluded_cell_counts": dict(sorted(missing.items()))}
    failures = []
    if n < MIN_N:
        failures.append("sample_below_20_complete_countries")
    primary = None
    if n >= MIN_N:
        a = np.asarray([[x, y0, dy] for _, x, y0, dy in complete], dtype=float)
        x = a[:, 0] / 10.0
        y0 = a[:, 1] / 10.0
        dy = a[:, 2]
        iqr = float(np.quantile(a[:, 0], .75) - np.quantile(a[:, 0], .25))
        sample["exposure_iqr_pp"] = iqr
        if iqr < MIN_IQR[x_name]:
            failures.append("exposure_iqr_below_frozen_floor")
        design = np.column_stack((np.ones(n), x, y0))
        rank = int(np.linalg.matrix_rank(design))
        if rank != 3:
            failures.append("design_not_full_rank")
        else:
            adjust = design[:, [0, 2]]
            residual = x - adjust @ np.linalg.lstsq(adjust, x, rcond=None)[0]
            squared = residual ** 2
            total = float(squared.sum())
            if not math.isfinite(total) or total <= 0:
                failures.append("no_residual_exposure")
            else:
                max_share = float(squared.max() / total)
                hat = design @ np.linalg.pinv(design.T @ design) @ design.T
                max_hat = float(np.diag(hat).max())
                sample["max_country_residual_exposure_share"] = max_share
                sample["max_hat_leverage"] = max_hat
                if max_share > MAX_RESIDUAL_SHARE:
                    failures.append("country_residual_exposure_share_above_20pct")
                if max_hat > MAX_HAT_LEVERAGE:
                    failures.append("country_hat_leverage_above_30pct")
        if not failures:
            fit = sm.OLS(dy, design).fit(cov_type="HC3")
            beta, se = float(fit.params[1]), float(fit.bse[1])
            dof = n - 3
            if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
                failures.append("nonfinite_or_nonpositive_hc3_uncertainty")
            else:
                p = float(2 * student_t.sf(abs(beta / se), dof))
                critical = float(student_t.ppf(1 - P_MAX / 2, dof))
                if not math.isfinite(p) or not math.isfinite(critical):
                    failures.append("nonfinite_inference")
                else:
                    primary = {"coefficient_per_10pp_exposure": beta, "std_error_hc3": se,
                               "p_value_two_sided": p, "confidence_level": 1 - P_MAX,
                               "confidence_interval": [beta - critical * se, beta + critical * se],
                               "n_countries": n, "df_inference": dof, "design_rank": rank,
                               "method": "cross-country OLS of 2025 minus 2022 outcome on 2023 exposure/10 and 2022 outcome/10; HC3; Student t(n-3)"}
    if failures:
        verdict = "INCONCLUSIVE"
        reason = "one or more frozen source, sample, variation, influence, or estimator gates did not pass"
        primary = None
    else:
        assert primary is not None
        oriented = primary["coefficient_per_10pp_exposure"] if sign == "+" else -primary["coefficient_per_10pp_exposure"]
        if primary["p_value_two_sided"] <= P_MAX and oriented >= MIN_ABS_BETA:
            verdict, reason = "SUPPORTED", "signed descriptive association clears the frozen family and magnitude gates"
        elif primary["p_value_two_sided"] <= P_MAX and oriented <= -MIN_ABS_BETA:
            verdict, reason = "REFUTED", "opposite signed descriptive association clears the frozen family and magnitude gates"
        else:
            verdict, reason = "PARTIAL", "estimable descriptive association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate_failures": failures,
            "sample": sample, "primary": primary}


def rendered_files(case: tuple[str, ...], result: dict[str, object], registration: str,
                   lock_revision: str) -> dict[str, bytes]:
    hypothesis, x_name, y_name, _sign, label = case
    vintages = [SOURCES[name] for name in (x_name, y_name)]
    diagnostic = {"hypothesis_id": hypothesis, "family_id": FAMILY,
                  "registration_commit": registration, "source_lock_commit": lock_revision,
                  "source_key_roster_sha256": ROSTER_SHA, "result": result,
                  "correction": CORRECTION, "limitations": LIMITATIONS}
    diagnostic_bytes = (json.dumps(diagnostic, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
    manifest = {"hypothesis_id": hypothesis, "status": result["verdict"], "runner": RUNNER,
                "preregistration_commit": registration, "source_lock": lock_rel(case),
                "source_lock_commit": lock_revision, "vintages": vintages,
                "sample": result["sample"], "family_correction": CORRECTION}
    packet = {"packet_version": 1,
              "hypothesis": {"id": hypothesis, "path": spec_rel(case), "topic": "distribution"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_revision,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA},
              "family": {"id": FAMILY, "size": len(CASES), "members": sorted(c[0] for c in CASES)},
              "source": {"source_lock_manifest": lock_rel(case), "input_vintages": vintages,
                         "attribution": "OECD Global Revenue Statistics; Eurostat EU-SILC"},
              "result": result,
              "reproduction": {"runner": RUNNER,
                               "command": f"python3 {RUNNER} --verify --source-root <pinned-cache-root>",
                               "result_sha256": hashlib.sha256(diagnostic_bytes).hexdigest()},
              "limitations": LIMITATIONS,
              "credit": {"causal": 0, "policy_effect": 0, "school": 0, "position": 0, "featured": 0},
              "correction": CORRECTION}
    if result["primary"]:
        beta = result["primary"]["coefficient_per_10pp_exposure"]
        p = result["primary"]["p_value_two_sided"]
        figure = f"coefficient {beta:+.6f} outcome points per 10 exposure points; two-sided p={p:.6g}"
    else:
        figure = "no admitted coefficient under the frozen gates"
    card = (f"# {hypothesis} — {result['verdict']}\n\n"
            f"**Registered question:** {label}.\n\n"
            f"**Result:** {figure}. {result['reason'].capitalize()}.\n\n"
            f"**Sample:** {result['sample']['complete_countries']} complete countries of "
            f"{result['sample']['key_countries']} source-key countries. Gate findings: "
            f"{', '.join(result['gate_failures']) if result['gate_failures'] else 'none'}.\n\n"
            "The 2025 income data refer to 2024 income; this is ecological and descriptive, "
            "not an identified tax-policy effect. Four correlated questions share one Bonferroni "
            "family; no school, policy, causal, position, or featured credit is assigned.\n")
    wrapper = ("#!/usr/bin/env python3\nimport subprocess, sys\n"
               f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify', *sys.argv[1:]]))\n")
    return {"diagnostics.json": diagnostic_bytes,
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True).encode(),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True).encode(),
            "hypothesis.yaml": (ROOT / spec_rel(case)).read_bytes(),
            "result_card.md": card.encode(), "replication.py": wrapper.encode()}


def summary(results: dict[str, dict[str, object]]) -> bytes:
    lines = ["# OECD tax / EU-SILC later-outcome family — measured results (2026-10-10)", "",
             "Four source-locked descriptive questions use the 2022 EU-SILC baseline, 2023 OECD tax exposure, and 2025 EU-SILC outcome. The 2025 income outcomes refer to 2024 income. No causal, policy, school, position, or featured credit is assigned.", "",
             "| Question | Verdict | Complete countries | Association |", "| --- | --- | ---: | --- |"]
    for case in CASES:
        result = results[case[0]]
        primary = result["primary"]
        estimate = (f"β={primary['coefficient_per_10pp_exposure']:+.4f}; p={primary['p_value_two_sided']:.4g}"
                    if primary else "No admitted coefficient")
        lines.append(f"| `{case[0]}` | {result['verdict']} | {result['sample']['complete_countries']} | {estimate} |")
    lines += ["", "A member remains in the four-test Bonferroni denominator even if its frozen source, sample, variation, influence, or estimator gate is inconclusive.",
              "The source-key roster is a coverage upper bound; selected value completeness is assessed only after source locks. OECD tax receipts are not a transfer or redistribution measure, and the 2025 Eurostat country surveys are not causal experiments.", ""]
    return "\n".join(lines).encode()


def execute(mode: str, source_root: Path) -> None:
    paths = checked_sources(source_root)
    roster = read_roster()
    preflight(paths, roster)
    if mode == "preflight":
        print(json.dumps({"source_key_countries": 28, "pit_key_countries": 24,
                          "selected_values_or_null_masks_opened": False}, sort_keys=True))
        return
    registration = registration_commit()
    locks = {case[0]: lock_commit(case, registration) for case in CASES}
    values = selected_values(paths, roster)
    results = {case[0]: measured_case(case, roster, values) for case in CASES}
    generated = {case[0]: rendered_files(case, results[case[0]], registration, locks[case[0]])
                 for case in CASES}
    generated["summary"] = {SUMMARY: summary(results)}
    for name, files in generated.items():
        base = ROOT if name == "summary" else ROOT / "engine" / "runs" / name
        if mode == "run":
            base.mkdir(parents=True, exist_ok=True)
        for filename, expected in files.items():
            path = base / filename
            if mode == "run":
                path.write_bytes(expected)
            elif not path.is_file() or path.read_bytes() != expected:
                raise RuntimeError(f"exact replay differs: {path.relative_to(ROOT)}")
    print(json.dumps({"mode": mode,
                      "verdicts": dict(sorted(Counter(r["verdict"] for r in results.values()).items())),
                      "cases": {name: {"verdict": r["verdict"], "countries": r["sample"]["complete_countries"]}
                                for name, r in results.items()}}, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    parser.add_argument("--case", choices=[c[0] for c in CASES])
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    source_root = args.source_root.resolve()
    if args.preflight:
        execute("preflight", source_root)
        return
    if args.lock:
        if not args.case:
            parser.error("--lock needs --case")
        paths = checked_sources(source_root)
        roster = read_roster()
        preflight(paths, roster)
        registration = registration_commit()
        case = next(c for c in CASES if c[0] == args.case)
        rel = lock_rel(case)
        if (ROOT / rel).exists():
            raise RuntimeError("source lock already exists")
        (ROOT / rel).write_text(json.dumps(lock_payload(case, registration), sort_keys=True, indent=2) + "\n")
        print(json.dumps({"source_lock": rel, "registration_commit": registration,
                          "selected_values_or_null_masks_opened": False}, sort_keys=True))
        return
    execute("run" if args.run else "verify", source_root)


if __name__ == "__main__":
    main()
