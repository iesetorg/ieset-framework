#!/usr/bin/env python3
"""Key-only preflight, guarded first result, and read-only replay for one CEPAL/IMF study."""

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
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
HID = "cepal_imf_inflation_next_year_national_poverty_panel"
SPEC_REL = f"hypotheses/distribution/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
LOCK_REL = f"data/source_locks/{HID}.yaml"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
SOURCE_MANIFEST = "data/manifests/fetch_run_2026-10-09T121824Z.yaml"
SOURCE_MANIFEST_SHA256 = "befe6a588f0e2c0de0fd42566f34e76226ce161151432e0373bf3dced401d960"
WEO_APPENDIX_URL = (
    "https://data.imf.org/-/media/iData/External-Storage/Documents/"
    "4AA1F4D0624C46E98F95988F1F83E770/en/April-2026-WEO-Database-Appendix.pdf"
)
COUNTRIES = (
    "BOL", "BRA", "CHL", "COL", "CRI", "DOM", "ECU", "HND", "MEX", "PAN",
    "PER", "PRY", "SLV", "URY",
)
EXPOSURE_YEARS = tuple(range(2000, 2024))
EXPECTED_KEY_COUNT = 281
EXPECTED_KEY_SHA256 = "d0c1d057a04c63a1a771a2fb64ebe532a5646f7270fd57945847abb3c858cc32"
MIN_TRIPLETS = 200
MIN_PER_COUNTRY = 8
MIN_OUTCOME_YEARS = 18
ALPHA = 0.025
MIN_EFFECT_PP = 0.5
MIN_LOO_SHARE = 0.8
SOURCES: dict[str, dict[str, str]] = {
    "poverty": {
        "publisher": "cepalstat", "series_id": "indicator_3328",
        "path": "data/vintages/cepalstat/indicator_3328@2026-10-09T121816Z.parquet",
        "sha256": "8d6d5303adf4a0dd92fe5262779398962f00652bf5a63481326865a69c39cc9a",
    },
    "inflation": {
        "publisher": "imf_weo_sdmx", "series_id": "WEO__PCPIPCH",
        "path": "data/vintages/imf_weo_sdmx/WEO__PCPIPCH@2026-10-09T121600Z.parquet",
        "sha256": "89564e357988848ac8801d946f958c4dcef37881bf35ca77d4c03c225caa0568",
    },
    "real_gdp_growth": {
        "publisher": "imf_weo_sdmx", "series_id": "WEO__NGDP_RPCH",
        "path": "data/vintages/imf_weo_sdmx/WEO__NGDP_RPCH@2026-10-09T121556Z.parquet",
        "sha256": "6ec4c363b7d191f454840fc10abec6598aa28e7b17f934527dea17484addaf00",
    },
}
# IMF April 2026 WEO Database Appendix, Country Data Documentation, pp. 9-14.
# The two fields below are the latest actual annual NATIONAL ACCOUNTS and CPI
# years, respectively. They were transcribed before any selected values or null
# masks were read. This study uses t<=2023, below every listed actual boundary.
ACTUAL_LAST = {
    "BOL": (2025, 2025), "BRA": (2025, 2025), "CHL": (2025, 2025),
    "COL": (2025, 2025), "CRI": (2025, 2025), "DOM": (2025, 2025),
    "ECU": (2025, 2025), "HND": (2024, 2025), "MEX": (2024, 2025),
    "PAN": (2025, 2025), "PER": (2025, 2025), "PRY": (2024, 2025),
    "SLV": (2024, 2025), "URY": (2024, 2025),
}
LIMITATIONS = [
    "Pre-analysis registered retrospective validation of files already collected on 2026-10-09.",
    "The one-year lag, country effects, year effects, and GDP-growth control do not identify a causal effect.",
    "CEPAL poverty survey timing, definitions, and note codes are not fully harmonized in the pinned local table.",
    "The broad tracked fetch manifest contains unrelated absolute local paths; the narrow source lock does not copy them.",
    "Earlier IESET inflation/poverty work was visible before this source pair was selected; p<0.025 reserves a second primary design.",
    "This measured association has no policy, ideology, or school-score credit.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def first_added(rel: str) -> str:
    result = git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", rel)
    commits = result.stdout.decode("ascii", errors="replace").strip().splitlines()
    if result.returncode or not commits:
        raise RuntimeError(f"no first-addition commit for {rel}")
    return commits[0]


def committed_unchanged(rel: str, first: str) -> dict[str, str]:
    current = (ROOT / rel).read_bytes()
    at_head = git("show", f"HEAD:{rel}")
    at_first = git("show", f"{first}:{rel}")
    if any((at_head.returncode, at_first.returncode,
            at_head.stdout != current, at_first.stdout != current)):
        raise RuntimeError(f"committed first-addition bytes changed: {rel}")
    return {"path": rel, "sha256": hashlib.sha256(current).hexdigest()}


def registration_files() -> tuple[str, list[dict[str, str]]]:
    first = first_added(SPEC_REL)
    records = [committed_unchanged(rel, first) for rel in REGISTRATION_FILES]
    first_run = git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if first_run.returncode or first_run.stdout.strip():
        raise RuntimeError("run artifact existed in the registration commit")
    return first, records


def validate_spec() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    gate = spec.get("falsification", {}).get("threshold", {})
    if any((
        spec.get("hypothesis_id") != HID,
        spec.get("version") != 1,
        spec.get("status") != "pre_registered",
        spec.get("evidence_type") != "descriptive",
        spec.get("sample", {}).get("countries") != list(COUNTRIES),
        spec.get("sample", {}).get("period") != [2000, 2024],
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("covers_claims") != [],
        gate.get("country_roster") != list(COUNTRIES),
        gate.get("structural_key_count") != EXPECTED_KEY_COUNT,
        gate.get("structural_key_sha256") != EXPECTED_KEY_SHA256,
        gate.get("minimum_complete_triplets") != MIN_TRIPLETS,
        gate.get("minimum_countries") != len(COUNTRIES),
        gate.get("minimum_triplets_per_country") != MIN_PER_COUNTRY,
        gate.get("minimum_outcome_years") != MIN_OUTCOME_YEARS,
        gate.get("effect_size_threshold_pp") != MIN_EFFECT_PP,
        gate.get("two_sided_p_max_exclusive") != ALPHA,
        gate.get("leave_one_country_out_sign_share_min") != MIN_LOO_SHARE,
        gate.get("source_manifest") != {"path": SOURCE_MANIFEST, "sha256": SOURCE_MANIFEST_SHA256},
        gate.get("source_files") != {
            role: {"path": row["path"], "sha256": row["sha256"]}
            for role, row in SOURCES.items()
        },
    )):
        raise ValueError("spec differs from frozen CEPAL/IMF runner contract")
    return spec


def manifest_entries() -> dict[str, dict[str, Any]]:
    if sha256(ROOT / SOURCE_MANIFEST) != SOURCE_MANIFEST_SHA256:
        raise ValueError("tracked broad source manifest hash changed")
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    records: dict[str, dict[str, Any]] = {}
    allowed = (
        "publisher", "series_id", "source_url", "methodology_url", "license",
        "fetch_utc", "rows", "frequency", "units", "currency", "start_date",
        "end_date", "sha256", "parquet_path",
    )
    for role, source in SOURCES.items():
        found = [row for row in manifest.get("entries", [])
                 if row.get("parquet_path") == source["path"]]
        if len(found) != 1:
            raise ValueError(f"source manifest lacks unique {role} entry")
        row = found[0]
        if any(row.get(key) != source[expected] for key, expected in (
            ("publisher", "publisher"), ("series_id", "series_id"),
            ("sha256", "sha256"), ("parquet_path", "path"),
        )):
            raise ValueError(f"source manifest identity mismatch: {role}")
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"raw source SHA mismatch: {role}")
        records[role] = {key: row.get(key) for key in allowed}
    return records


def expected_source_lock() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "study_id": HID,
        "original_tracked_manifest": {
            "path": SOURCE_MANIFEST, "sha256": SOURCE_MANIFEST_SHA256,
            "custody_note": (
                "The original tracked run manifest includes unrelated absolute "
                "local paths in other entries. This narrow lock copies only "
                "the three selected source entries and does not erase that "
                "existing history risk."
            ),
        },
        "selected_source_entries": manifest_entries(),
        "actual_year_status": {
            "source": "IMF April 2026 WEO Database Appendix, Country Data Documentation, pp. 9-14",
            "url": WEO_APPENDIX_URL,
            "flow": "WEO",
            "latest_actual_national_accounts_and_cpi_by_country": {
                country: list(ACTUAL_LAST[country]) for country in COUNTRIES
            },
            "frozen_exposure_year_end": 2023,
            "all_selected_exposure_years_actual": all(
                min(ACTUAL_LAST[country]) >= max(EXPOSURE_YEARS) for country in COUNTRIES
            ),
            "exclusions": {
                "ARG": "No National CEPAL poverty keys in this vintage",
                "VEN": "IMF appendix latest actual national-accounts year 2018",
                "GTM": "Only two structural lagged country-years",
                "NIC": "Only four structural lagged country-years",
            },
        },
    }


def write_source_lock() -> dict[str, Any]:
    registration_files()
    validate_spec()
    path = ROOT / LOCK_REL
    if path.exists():
        raise FileExistsError(f"source lock already exists: {LOCK_REL}")
    lock = expected_source_lock()
    if not lock["actual_year_status"]["all_selected_exposure_years_actual"]:
        raise ValueError("IMF actual-year cutoff fails")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(lock, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return {"source_lock": LOCK_REL, "sha256": sha256(path), "wrote_values": False}


def locked_sources(prereg_commit: str) -> tuple[str, dict[str, Any]]:
    expected = expected_source_lock()
    path = ROOT / LOCK_REL
    lock = yaml.safe_load(path.read_text(encoding="utf-8"))
    if lock != expected or not lock["actual_year_status"]["all_selected_exposure_years_actual"]:
        raise ValueError("narrow source lock or IMF actual-year status changed")
    lock_commit = first_added(LOCK_REL)
    if git("merge-base", "--is-ancestor", prereg_commit, lock_commit).returncode:
        raise RuntimeError("source lock is not after the registration commit")
    if lock_commit == prereg_commit:
        raise RuntimeError("source lock entered with the registration")
    committed_unchanged(LOCK_REL, lock_commit)
    first_run = git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_REL)
    if first_run.returncode or first_run.stdout.strip():
        raise RuntimeError("result entered with the source lock")
    return lock_commit, lock


def _structural_rows(role: str) -> pd.DataFrame:
    source = SOURCES[role]
    if role == "poverty":
        columns = ["iso3", "year", "years", "poverty_and_extreme_poverty", "geographical_area__(hs)"]
        rows = pd.read_parquet(ROOT / source["path"], columns=columns)
        rows = rows[(rows["iso3"].isin(COUNTRIES))
                    & (rows["poverty_and_extreme_poverty"] == "Poverty")
                    & (rows["geographical_area__(hs)"] == "National")].copy()
        if not (rows["year"].astype(str) == rows["years"].astype(str)).all():
            raise ValueError("CEPAL year dimensions disagree")
        rows["country_iso3"] = rows["iso3"].astype(str)
        rows["year"] = rows["year"].astype(int)
    else:
        rows = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "year", "weo_flow"])
        rows = rows[(rows["country_iso3"].isin(COUNTRIES)) & (rows["weo_flow"] == "WEO")].copy()
        rows["year"] = rows["year"].astype(int)
    rows = rows[["country_iso3", "year"]]
    if rows.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate {role} country-year source key")
    return rows


def structural_preflight() -> dict[str, Any]:
    validate_spec()
    manifest_entries()  # verifies source hashes but projects no measured column
    sets = {
        role: set(map(tuple, _structural_rows(role).itertuples(index=False, name=None)))
        for role in SOURCES
    }
    keys = sorted((country, year) for country, year in sets["inflation"] & sets["real_gdp_growth"]
                  if country in COUNTRIES and year in EXPOSURE_YEARS
                  and (country, year + 1) in sets["poverty"])
    encoded = "".join(f"{country},{year},{year + 1}\n" for country, year in keys).encode("ascii")
    digest = hashlib.sha256(encoded).hexdigest()
    country_counts = {country: sum(row[0] == country for row in keys) for country in COUNTRIES}
    if len(keys) != EXPECTED_KEY_COUNT or digest != EXPECTED_KEY_SHA256:
        raise ValueError("structural source-key envelope changed")
    if any(count < MIN_PER_COUNTRY for count in country_counts.values()):
        raise ValueError("fixed roster lacks eight structural keys per country")
    return {
        "selected_structural_keys": len(keys),
        "structural_key_sha256": digest,
        "country_structural_counts": country_counts,
        "exposure_years": [min(EXPOSURE_YEARS), max(EXPOSURE_YEARS)],
        "outcome_years": [min(EXPOSURE_YEARS) + 1, max(EXPOSURE_YEARS) + 1],
        "measured_values_or_null_masks_read": False,
    }


def selected_measure(role: str) -> dict[tuple[str, int], Any]:
    source = SOURCES[role]
    if role == "poverty":
        columns = ["iso3", "year", "years", "poverty_and_extreme_poverty", "geographical_area__(hs)", "value"]
        rows = pd.read_parquet(ROOT / source["path"], columns=columns)
        rows = rows[(rows["iso3"].isin(COUNTRIES))
                    & (rows["poverty_and_extreme_poverty"] == "Poverty")
                    & (rows["geographical_area__(hs)"] == "National")].copy()
        rows["country_iso3"] = rows["iso3"].astype(str)
    else:
        rows = pd.read_parquet(ROOT / source["path"], columns=["country_iso3", "year", "weo_flow", "value"])
        rows = rows[(rows["country_iso3"].isin(COUNTRIES)) & (rows["weo_flow"] == "WEO")].copy()
    rows["year"] = rows["year"].astype(int)
    rows = rows[["country_iso3", "year", "value"]]
    if rows.duplicated(["country_iso3", "year"]).any():
        raise ValueError(f"duplicate selected {role} measure key")
    return {(str(country), int(year)): value for country, year, value in rows.itertuples(index=False, name=None)}


def numeric_value(raw: Any, *, poverty: bool = False) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or (poverty and not 0 <= value <= 100):
        return None
    return value


def complete_panel() -> tuple[pd.DataFrame, dict[str, Any]]:
    values = {role: selected_measure(role) for role in SOURCES}
    rows: list[dict[str, Any]] = []
    invalid = {role: 0 for role in SOURCES}
    for country in COUNTRIES:
        for year in EXPOSURE_YEARS:
            key = (country, year)
            outcome_key = (country, year + 1)
            if not all((key in values["inflation"], key in values["real_gdp_growth"],
                        outcome_key in values["poverty"])):
                continue  # structurally absent; fixed preflight records the exact envelope
            poverty = numeric_value(values["poverty"][outcome_key], poverty=True)
            inflation = numeric_value(values["inflation"][key])
            growth = numeric_value(values["real_gdp_growth"][key])
            selected = {"poverty": poverty, "inflation": inflation, "real_gdp_growth": growth}
            for role, value in selected.items():
                if value is None:
                    invalid[role] += 1
            if any(value is None for value in selected.values()):
                continue
            assert poverty is not None and inflation is not None and growth is not None
            rows.append({
                "country_iso3": country, "exposure_year": year, "outcome_year": year + 1,
                "poverty_pp": poverty, "inflation_asinh": math.asinh(inflation / 10.0),
                "gdp_growth_div10": growth / 10.0,
            })
    frame = pd.DataFrame(rows, columns=[
        "country_iso3", "exposure_year", "outcome_year", "poverty_pp",
        "inflation_asinh", "gdp_growth_div10",
    ])
    counts = {country: int((frame["country_iso3"] == country).sum()) for country in COUNTRIES}
    gate = {
        "structural_keys": EXPECTED_KEY_COUNT, "complete_triplets": len(frame),
        "country_complete_counts": counts,
        "distinct_outcome_years": int(frame["outcome_year"].nunique()),
        "invalid_or_missing_value_cells_by_role": invalid,
        "minimum_complete_triplets": MIN_TRIPLETS,
        "minimum_per_fixed_country": MIN_PER_COUNTRY,
        "minimum_outcome_years": MIN_OUTCOME_YEARS,
    }
    gate["passed"] = bool(
        len(frame) >= MIN_TRIPLETS
        and all(count >= MIN_PER_COUNTRY for count in counts.values())
        and gate["distinct_outcome_years"] >= MIN_OUTCOME_YEARS
    )
    return frame, gate


FORMULA = (
    "poverty_pp ~ inflation_asinh + gdp_growth_div10 + "
    "C(country_iso3) + C(outcome_year)"
)


def estimate(frame: pd.DataFrame) -> dict[str, Any]:
    countries = sorted(frame["country_iso3"].unique())
    g = len(countries)
    fit = smf.ols(FORMULA, data=frame).fit(
        cov_type="cluster",
        cov_kwds={"groups": frame["country_iso3"], "use_correction": True},
    )
    if np.linalg.matrix_rank(fit.model.exog) != fit.model.exog.shape[1]:
        raise ValueError("full panel design matrix is rank deficient")
    beta = float(fit.params["inflation_asinh"])
    se = float(fit.bse["inflation_asinh"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        raise ValueError("nonfinite or zero clustered treatment uncertainty")
    stat = beta / se
    p_value = float(2 * student_t.sf(abs(stat), df=g - 1))
    loo: dict[str, float] = {}
    for omitted in countries:
        subset = frame[frame["country_iso3"] != omitted]
        one = smf.ols(FORMULA, data=subset).fit()
        if np.linalg.matrix_rank(one.model.exog) != one.model.exog.shape[1]:
            raise ValueError(f"leave-one-out design rank deficient: {omitted}")
        coefficient = float(one.params["inflation_asinh"])
        if not math.isfinite(coefficient):
            raise ValueError(f"leave-one-out coefficient invalid: {omitted}")
        loo[omitted] = coefficient
    positive_share = sum(value > 0 for value in loo.values()) / len(loo)
    negative_share = sum(value < 0 for value in loo.values()) / len(loo)
    return {
        "formula": FORMULA, "treatment_coefficient_pp": beta,
        "country_cluster_cr1_standard_error": se,
        "two_sided_t_p_value": p_value, "cluster_degrees_of_freedom": g - 1,
        "n_obs": len(frame), "n_countries": g,
        "leave_one_country_out_coefficients_pp": loo,
        "leave_one_out_positive_share": positive_share,
        "leave_one_out_negative_share": negative_share,
    }


def classify(value: dict[str, Any]) -> tuple[str, str]:
    beta = value["treatment_coefficient_pp"]
    p_value = value["two_sided_t_p_value"]
    if beta >= MIN_EFFECT_PP and p_value < ALPHA and value["leave_one_out_positive_share"] >= MIN_LOO_SHARE:
        return "SUPPORTED", "registered material positive descriptive association passes precision and stability gates"
    if beta <= -MIN_EFFECT_PP and p_value < ALPHA and value["leave_one_out_negative_share"] >= MIN_LOO_SHARE:
        return "REFUTED", "registered material negative descriptive association passes precision and stability gates"
    return "PARTIAL", "valid panel does not cross the registered materiality, precision, and stability gates"


def calculate() -> tuple[dict[str, Any], dict[str, Any], str, str, dict[str, Any] | None]:
    structure = structural_preflight()
    frame, coverage = complete_panel()
    if not coverage["passed"]:
        return structure, coverage, "INCONCLUSIVE", "complete-case coverage gate failed", None
    try:
        result = estimate(frame)
    except (ValueError, np.linalg.LinAlgError) as error:
        return structure, coverage, "INCONCLUSIVE", f"estimator validity gate failed: {error}", None
    label, reason = classify(result)
    return structure, coverage, label, reason, result


def wrapper_text() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of the CEPAL/IMF descriptive packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


def artifacts(
    stamp: str, prereg_commit: str, source_lock_commit: str,
    registration: list[dict[str, str]], structure: dict[str, Any],
    coverage: dict[str, Any], label: str, reason: str,
    result: dict[str, Any] | None,
) -> dict[str, Any]:
    source_pins = {role: {"path": source["path"], "sha256": source["sha256"]}
                   for role, source in SOURCES.items()}
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "source_lock_commit": source_lock_commit,
        "evidence_type": "descriptive", "template": "descriptive_panel_fe",
        "source_manifest": {"path": SOURCE_MANIFEST, "sha256": SOURCE_MANIFEST_SHA256},
        "source_lock": LOCK_REL, "structural_preflight": structure,
        "complete_case_gate": coverage, "estimate": result,
        "correction": {"disposition": "descriptive_calibration_only", "school_score_credit": 0},
        "limitations": LIMITATIONS,
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "source_lock_commit": source_lock_commit,
        "status": label, "registration_files": registration,
        "source_lock": {"path": LOCK_REL, "sha256": sha256(ROOT / LOCK_REL)},
        "vintages": source_pins, "structural_preflight": structure,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "distribution"},
        "preregistration": {"spec_commit": prereg_commit,
                            "source_lock_commit": source_lock_commit,
                            "registration_files": registration},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"source_lock": LOCK_REL, "inputs": source_pins,
                 "actual_year_rule": "April 2026 WEO appendix; t<=2023; fixed 14 countries"},
        "coverage": coverage, "results": result, "limitations": LIMITATIONS,
        "credit_ceiling": "descriptive calibration only; zero school score",
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Preregistration commit: `{prereg_commit}`. Source-lock commit: `{source_lock_commit}`.\n"
        "\nFixed sample: 14 Latin American countries; IMF inflation and real-GDP growth in 2000–2023; "
        "CEPALSTAT National poverty in the following years 2001–2024.\n"
        f"Structural keys: {structure['selected_structural_keys']}; complete triplets: {coverage['complete_triplets']}.\n"
    )
    if result is not None:
        card += (
            f"\nInflation coefficient: {result['treatment_coefficient_pp']:+.8g} poverty percentage points "
            "per asinh(inflation percent / 10) unit.\n"
            f"Country-cluster CR1 SE: {result['country_cluster_cr1_standard_error']:.8g}; "
            f"two-sided t p: {result['two_sided_t_p_value']:.8g}.\n"
            f"Leave-one-country-out positive share: {result['leave_one_out_positive_share']:.3f}; "
            f"negative share: {result['leave_one_out_negative_share']:.3f}.\n"
        )
    card += (
        "\nPre-analysis registered retrospective validation of already collected sources. "
        "This is a descriptive association, not a causal inflation or policy effect. "
        "CEPAL survey comparability and source notes limit interpretation. "
        "No school or policy-score credit.\n"
    )
    return {
        "diagnostics.json": json.dumps(diagnostics, indent=2, sort_keys=True) + "\n",
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False, allow_unicode=True),
        "result_card.md": card,
        "replication.py": wrapper_text(),
        "hypothesis.yaml": (ROOT / SPEC_REL).read_text(encoding="utf-8"),
    }


def run_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before selected values
    source_lock_commit, _ = locked_sources(prereg_commit)
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check")
    structure, coverage, label, reason, result = calculate()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    content = artifacts(stamp, prereg_commit, source_lock_commit,
                        registration, structure, coverage, label, reason, result)
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    for name, data in content.items():
        (RUN_DIR / name).write_text(data, encoding="utf-8")
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "source_lock_commit": source_lock_commit, "wrote_files": True,
            "complete_triplets": coverage["complete_triplets"]}


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()
    source_lock_commit, _ = locked_sources(prereg_commit)
    stored = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    structure, coverage, label, reason, result = calculate()
    expected = artifacts(stored["run_utc"], prereg_commit, source_lock_commit,
                         registration, structure, coverage, label, reason, result)
    for name, data in expected.items():
        if (RUN_DIR / name).read_text(encoding="utf-8") != data:
            raise AssertionError(f"saved packet differs from exact pinned replay: {name}")
    return {"hypothesis_id": HID, "verified": True, "verdict": label,
            "wrote_files": False, "source_lock_commit": source_lock_commit}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true", help="hashes and keys only")
    mode.add_argument("--write-source-lock", action="store_true", help="selected metadata only")
    mode.add_argument("--run", action="store_true", help="guarded first result")
    mode.add_argument("--check", action="store_true", help="read-only replay")
    args = parser.parse_args()
    if args.preflight:
        result = structural_preflight()
    elif args.write_source_lock:
        result = write_source_lock()
    elif args.run:
        result = run_one()
    else:
        result = check_one()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
