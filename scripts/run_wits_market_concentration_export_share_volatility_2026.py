#!/usr/bin/env python3
"""Frozen descriptive WITS market concentration to later export-share volatility.

Registration and a metadata-only source lock must be committed separately
before selected values are read. Exact replay rebuilds every output byte.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pycountry
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
ID = "wits_market_concentration_export_share_volatility_2026"
SPEC = f"hypotheses/trade/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
PLAN = f"engine/audits/{ID}_prereg_2026-10-10.md"
RUNNER = f"scripts/run_{ID}.py"
ROSTER = "data/pinned_evidence/wits_market_concentration_export_share_volatility_key_roster.csv"
ROSTER_SHA = "28254b72c7a9ec09fa6d2b8d12989f4d5d0c4809eecdd7deff3426e6dbe5bd02"
LOCK = f"prereg/locks/{ID}.json"
RUN = f"engine/runs/{ID}"
SUMMARY = f"engine/audits/{ID}_result_2026-10-10.md"
REGISTERED = (SPEC, STEELMAN, PLAN, RUNNER, ROSTER)
ARTIFACTS = (
    "hypothesis.yaml", "manifest.yaml", "diagnostics.json",
    "coefficients.parquet", "chart_data.json", "result_card.md",
    "replication.py", "evidence_packet.yaml", "metric_results.parquet",
)
SOURCES = {
    "market": {
        "publisher": "wits", "series_id": "product_concentration",
        "path": "data/vintages/wits/product_concentration@2026-07-23T151543Z.parquet",
        "sha256": "c59b180e07f484546e131fa6a4f47a725ecc790effbb3d395e5d2c4e36381949",
        "manifest": "data/manifests/fetch_run_2026-07-23T151550Z.yaml",
        "manifest_sha256": "96243db0b85df0b1d5ccd10631b356618a9372d62c4741b692129658a49e05a5",
        "years": (2000, 2010),
    },
    "export_share": {
        "publisher": "world_bank_wdi", "series_id": "NE.EXP.GNFS.ZS",
        "path": "data/vintages/world_bank_wdi/NE.EXP.GNFS.ZS@2026-05-05T203013Z.parquet",
        "sha256": "a53b48aa292a8b461a32c19943ad7bbca52f3625899a79d7c92e640724cfb121",
        "manifest": "data/manifests/fetch_run_2026-05-05T203305Z.yaml",
        "manifest_sha256": "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0",
        "years": tuple(range(2000, 2021)),
    },
}
MIN_COUNTRIES = 80
MATERIAL_HHI_CHANGE = 0.05
MIN_MATERIAL = 20
MIN_HHI_IQR = 0.03
MAX_EXPOSURE_SHARE = 0.20
MAX_OUTCOME_SHARE = 0.25
MAX_LOO_FAILURES = 2
MIN_LOO_SIGN_SHARE = 0.75
MEANINGFUL_BETA = 1.0
P_MAX = 0.01


def file_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, stderr=subprocess.PIPE)


def first_addition(path: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H",
                  "HEAD", "--", path).decode().splitlines()
    if len(commits) != 1:
        raise ValueError(f"Expected one first-addition commit: {path}: {commits}")
    return commits[0]


def committed_original(path: str, commit: str) -> None:
    content = (ROOT / path).read_bytes()
    if content != git("show", f"{commit}:{path}") or content != git("show", f"HEAD:{path}"):
        raise ValueError(f"Frozen file changed after first commit: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise ValueError(f"Frozen file has uncommitted changes: {path}")


def ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def roster_codes() -> list[str]:
    path = ROOT / ROSTER
    if file_sha(path) != ROSTER_SHA:
        raise ValueError("Frozen country-key roster hash mismatch")
    lines = path.read_text().splitlines()
    if lines[0] != "country_iso3" or lines[1:] != sorted(set(lines[1:])):
        raise ValueError("Invalid key-only country roster")
    return lines[1:]


def threshold() -> dict:
    return {
        "family_size": 1, "min_complete_economies": MIN_COUNTRIES,
        "min_abs_hhi_change_0_05_economies": MIN_MATERIAL,
        "min_hhi_change_iqr": MIN_HHI_IQR,
        "max_single_economy_residualized_exposure_share": MAX_EXPOSURE_SHARE,
        "max_single_economy_residualized_outcome_share": MAX_OUTCOME_SHARE,
        "max_loo_failures": MAX_LOO_FAILURES,
        "min_loo_sign_share": MIN_LOO_SIGN_SHARE,
        "meaningful_abs_beta_export_share_volatility_pp_per_0_1_hhi": MEANINGFUL_BETA,
        "two_sided_p_max": P_MAX, "roster_sha256": ROSTER_SHA,
        "source_files": {
            role: {key: source[key] for key in ("path", "sha256", "manifest", "manifest_sha256")}
            for role, source in SOURCES.items()
        },
        "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
    }


def registration_commit() -> str:
    commits = {first_addition(path) for path in REGISTERED}
    if len(commits) != 1:
        raise ValueError("Registration files entered in different commits")
    registered = commits.pop()
    for path in REGISTERED:
        committed_original(path, registered)
    if git("ls-tree", "-r", "--name-only", registered, "--", LOCK, RUN, SUMMARY).strip():
        raise ValueError("Registration commit included source lock or results")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "descriptive"
            or spec.get("claim_direction") != "+"
            or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []
            or spec.get("steelman") != STEELMAN
            or spec["falsification"]["threshold"] != threshold()):
        raise ValueError("Frozen spec identity or gates differ")
    return registered


def source_custody(source_root: Path) -> tuple[dict, list[str]]:
    """Inspect bytes, metadata, and country/year keys; never selected values."""
    allowed = {country.alpha_3 for country in pycountry.countries} | {"XKX"}
    custody, key_sets = {}, {}
    for role, source in SOURCES.items():
        path = source_root / source["path"]
        if not path.is_file() or file_sha(path) != source["sha256"]:
            raise ValueError(f"Missing or changed raw vintage: {role}")
        names = pq.ParquetFile(path).schema_arrow.names
        needed = {"country_iso3", "year", "value"}
        if role == "market":
            needed |= {"indicator_id", "indicator_name", "partner_iso3", "product_code"}
        if not needed.issubset(names):
            raise ValueError(f"Unexpected source schema: {role}")
        columns = ["country_iso3", "year"]
        if role == "market":
            columns += ["indicator_id", "indicator_name", "partner_iso3", "product_code"]
        metadata = pq.read_table(path, columns=columns).to_pylist()
        if role == "market":
            if any(row["indicator_id"] != "HH-MKT-CNCNTRTN-NDX"
                   or row["indicator_name"] != "HH Market concentration index"
                   or row["partner_iso3"] != "999"
                   or row["product_code"] != "999999"
                   for row in metadata):
                raise ValueError("WITS vintage is not the declared market concentration index")
        keys = [
            (row["country_iso3"], int(row["year"])) for row in metadata
            if row["country_iso3"] in allowed and int(row["year"]) in source["years"]
        ]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate selected source key: {role}")
        key_sets[role] = set(keys)
        manifest_path = ROOT / source["manifest"]
        if file_sha(manifest_path) != source["manifest_sha256"]:
            raise ValueError(f"Changed fetch manifest: {role}")
        entries = [
            entry for entry in yaml.safe_load(manifest_path.read_text())["entries"]
            if entry.get("publisher") == source["publisher"]
            and entry.get("series_id") == source["series_id"]
            and entry.get("parquet_path") == source["path"]
        ]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise ValueError(f"Fetch manifest does not custody source: {role}")
        entry = entries[0]
        custody[role] = {
            **{key: source[key] for key in ("publisher", "series_id", "path", "sha256", "manifest", "manifest_sha256")},
            "source_url": entry.get("source_url"),
            "methodology_url": entry.get("methodology_url"),
            "license": entry.get("license"), "rows": entry.get("rows"),
            "selected_country_year_keys": len(keys),
            "selected_key_sha256": hashlib.sha256(
                "".join(f"{country},{year}\n" for country, year in sorted(keys)).encode()
            ).hexdigest(),
        }
    roster = sorted(
        country for country in allowed
        if all((country, year) in key_sets[role]
               for role, source in SOURCES.items() for year in source["years"])
    )
    if roster != roster_codes():
        raise ValueError("Raw source keys differ from frozen roster")
    return custody, roster


def expected_lock(source_root: Path) -> dict:
    registered = registration_commit()
    custody, roster = source_custody(source_root)
    return {
        "design_id": ID, "registration_commit": registered,
        "registered_sha256": {path: file_sha(ROOT / path) for path in REGISTERED},
        "source_custody": custody, "candidate_economies": roster,
        "selected_values_read": False,
        "instruction": "Commit this metadata-only source lock before opening selected values.",
    }


def make_lock(source_root: Path) -> None:
    if (ROOT / LOCK).exists():
        raise ValueError("Source lock already exists")
    payload = expected_lock(source_root)
    path = ROOT / LOCK
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n")
    print(f"Metadata-only source lock prepared for {len(payload['candidate_economies'])} economies")


def verified_lock(source_root: Path) -> tuple[dict, str, str]:
    registered = registration_commit()
    locked = first_addition(LOCK)
    committed_original(LOCK, locked)
    if not ancestor(registered, locked) or not ancestor(locked, "HEAD"):
        raise ValueError("Registration and source-lock chronology is not strict")
    if git("ls-tree", "-r", "--name-only", locked, "--", RUN, SUMMARY).strip():
        raise ValueError("Source-lock commit contained results")
    payload = json.loads((ROOT / LOCK).read_text())
    if payload != expected_lock(source_root):
        raise ValueError("Source lock differs from exact raw bytes, keys, or registration")
    return payload, registered, locked


def selected_values(source_root: Path, roster: list[str], role: str) -> dict[tuple[str, int], float | None]:
    source = SOURCES[role]
    columns = ["country_iso3", "year", "value"]
    if role == "market":
        columns += ["indicator_id", "partner_iso3", "product_code"]
    selected = set(roster)
    values = {}
    for row in pq.read_table(source_root / source["path"], columns=columns).to_pylist():
        country, year = row["country_iso3"], int(row["year"])
        if country not in selected or year not in source["years"]:
            continue
        if role == "market" and (row["indicator_id"] != "HH-MKT-CNCNTRTN-NDX"
                                 or row["partner_iso3"] != "999"
                                 or row["product_code"] != "999999"):
            raise ValueError("Unexpected WITS market indicator row")
        key = country, year
        if key in values:
            raise ValueError(f"Duplicate selected value key: {role} {key}")
        try:
            value = float(row["value"])
        except (TypeError, ValueError):
            value = None
        values[key] = value if value is not None and math.isfinite(value) else None
    if len(values) != len(roster) * len(source["years"]):
        raise ValueError(f"Source key roster incomplete for {role}")
    return values


def valid(value: float | None, low: float, high: float) -> bool:
    return value is not None and low <= value <= high


def panel_from_sources(source_root: Path, roster: list[str]) -> tuple[pd.DataFrame, dict]:
    market = selected_values(source_root, roster, "market")
    exports = selected_values(source_root, roster, "export_share")
    rows = []
    exclusions = Counter()
    for country in roster:
        m00, m10 = market[country, 2000], market[country, 2010]
        export_series = [exports[country, year] for year in range(2000, 2021)]
        reasons = []
        if not valid(m00, 0, 1) or not valid(m10, 0, 1):
            reasons.append("market_hhi_missing_or_invalid")
        if any(not valid(value, 0, 300) for value in export_series):
            reasons.append("wdi_export_gdp_share_missing_or_invalid")
        if reasons:
            exclusions.update(reasons)
            continue
        before = np.diff(np.asarray(export_series[:11], dtype=float))
        after = np.diff(np.asarray(export_series[10:], dtype=float))
        rows.append({
            "country_iso3": country,
            "market_hhi_change_per_0_1": (m10-m00)/0.1,
            "market_hhi_2000": m00,
            "export_share_2010": export_series[10],
            "pre_volatility": float(np.std(before, ddof=1)),
            "outcome": float(np.std(after, ddof=1)),
        })
    panel = pd.DataFrame(rows, columns=[
        "country_iso3", "market_hhi_change_per_0_1", "market_hhi_2000",
        "export_share_2010", "pre_volatility", "outcome",
    ]).sort_values("country_iso3").reset_index(drop=True)
    return panel, {
        "source_key_candidate_economies": len(roster),
        "complete_economies": len(panel),
        "exclusion_reasons_overlapping": dict(sorted(exclusions.items())),
    }


def design(panel: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    x = np.column_stack([
        np.ones(len(panel)),
        panel["market_hhi_change_per_0_1"].to_numpy(dtype=float),
        panel["market_hhi_2000"].to_numpy(dtype=float),
        panel["export_share_2010"].to_numpy(dtype=float),
        panel["pre_volatility"].to_numpy(dtype=float),
    ])
    return x, panel["outcome"].to_numpy(dtype=float)


def fit(panel: pd.DataFrame) -> dict:
    x, y = design(panel)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError("Full-rank design unavailable")
    controls = x[:, [0, 2, 3, 4]]
    rx = x[:, 1] - controls @ np.linalg.lstsq(controls, x[:, 1], rcond=None)[0]
    ry = y - controls @ np.linalg.lstsq(controls, y, rcond=None)[0]
    sx, sy = float(np.sum(rx*rx)), float(np.sum(ry*ry))
    if not all(math.isfinite(value) and value > 1e-10 for value in (sx, sy)):
        raise ValueError("No residualized exposure or outcome variation")
    result = sm.OLS(y, x).fit(cov_type="HC3")
    beta, se = float(result.params[1]), float(result.bse[1])
    p = float(2 * student_t.sf(abs(beta/se), df=n-k)) if se > 0 else float("nan")
    if not all(math.isfinite(value) for value in (beta, se, p)) or se <= 0:
        raise ValueError("Nonfinite HC3 estimate")
    return {
        "coefficient": beta, "standard_error": se, "p_value": p,
        "reference_df": n-k, "covariance": "HC3",
        "max_single_economy_residualized_exposure_share": float(np.max(rx*rx)/sx),
        "max_single_economy_residualized_outcome_share": float(np.max(ry*ry)/sy),
        "unit": "SD of 2011-to-2020 annual export/GDP share changes, percentage points, per +0.1 prior market HHI change",
    }


def calculate(panel: pd.DataFrame, diag: dict) -> tuple[dict, str]:
    exposure_hhi = 0.1 * panel["market_hhi_change_per_0_1"].to_numpy(dtype=float)
    n = len(panel)
    diag["material_hhi_change_economies"] = int((np.abs(exposure_hhi) >= MATERIAL_HHI_CHANGE).sum())
    diag["hhi_change_iqr"] = (
        float(np.quantile(exposure_hhi, .75)-np.quantile(exposure_hhi, .25))
        if n else 0.0
    )
    failed = []
    if n < MIN_COUNTRIES:
        failed.append("min_complete_economies")
    if diag["material_hhi_change_economies"] < MIN_MATERIAL:
        failed.append("min_abs_hhi_change_0_05_economies")
    if diag["hhi_change_iqr"] < MIN_HHI_IQR:
        failed.append("min_hhi_change_iqr")
    if failed:
        diag["failed_gates"] = failed
        return {}, "INCONCLUSIVE"
    try:
        estimate = fit(panel)
    except ValueError as exc:
        diag["failed_gates"] = [f"estimator:{exc}"]
        return {}, "INCONCLUSIVE"
    diag["max_single_economy_residualized_exposure_share"] = estimate[
        "max_single_economy_residualized_exposure_share"
    ]
    diag["max_single_economy_residualized_outcome_share"] = estimate[
        "max_single_economy_residualized_outcome_share"
    ]
    if diag["max_single_economy_residualized_exposure_share"] > MAX_EXPOSURE_SHARE:
        failed.append("residualized_exposure_concentration")
    if diag["max_single_economy_residualized_outcome_share"] > MAX_OUTCOME_SHARE:
        failed.append("residualized_outcome_concentration")
    loo = []
    failures = 0
    for country in panel["country_iso3"]:
        try:
            loo.append(fit(panel.loc[panel["country_iso3"] != country])["coefficient"])
        except ValueError:
            failures += 1
    estimate["loo_successes"] = len(loo)
    estimate["loo_failures"] = failures
    estimate["loo_positive_share"] = sum(beta > 0 for beta in loo)/len(loo) if loo else None
    estimate["loo_negative_share"] = sum(beta < 0 for beta in loo)/len(loo) if loo else None
    if failures > MAX_LOO_FAILURES:
        failed.append("leave_one_out_fit_failures")
    diag["failed_gates"] = failed
    if failed:
        return estimate, "INCONCLUSIVE"
    if (estimate["coefficient"] >= MEANINGFUL_BETA and estimate["p_value"] <= P_MAX
            and estimate["loo_positive_share"] >= MIN_LOO_SIGN_SHARE):
        return estimate, "SUPPORTED"
    if (estimate["coefficient"] <= -MEANINGFUL_BETA and estimate["p_value"] <= P_MAX
            and estimate["loo_negative_share"] >= MIN_LOO_SIGN_SHARE):
        return estimate, "REFUTED"
    return estimate, "PARTIAL"


def json_write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n")


def parquet_write(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression="snappy", version="2.6", write_statistics=False)


def emit(directory: Path, diag: dict, estimate: dict, verdict: str,
         registered: str, locked: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    credit = {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0}
    custody = json.loads((ROOT / LOCK).read_text())["source_custody"]
    (directory / "manifest.yaml").write_text(yaml.safe_dump({
        "design_id": ID, "verdict": verdict, "evidence_type": "descriptive",
        "spec_commit": registered, "lock_commit": locked,
        "spec_sha256": file_sha(ROOT / SPEC), "lock_sha256": file_sha(ROOT / LOCK),
        "runner_sha256": file_sha(ROOT / RUNNER), "source_custody": custody,
        "artifacts": list(ARTIFACTS), "credit": credit,
        "chart_data_omitted_for_source_license": True,
    }, sort_keys=True))
    correction = {
        "disposition": "descriptive_calibration_only", "causal_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }
    json_write(directory / "diagnostics.json", {
        **diag, "estimate": estimate, "verdict": verdict,
        "correction": correction, "analysis_scope": "descriptive_only",
    })
    has_estimate = "coefficient" in estimate
    parquet_write(directory / "coefficients.parquet", {
        "term": ["market_hhi_change_per_0_1"] if has_estimate else [],
        "coefficient": [estimate["coefficient"]] if has_estimate else [],
        "standard_error": [estimate["standard_error"]] if has_estimate else [],
        "p_value": [estimate["p_value"]] if has_estimate else [],
    }, pa.schema([
        ("term", pa.string()), ("coefficient", pa.float64()),
        ("standard_error", pa.float64()), ("p_value", pa.float64()),
    ]))
    json_write(directory / "chart_data.json", [])
    lines = [
        "# Earlier export-market concentration and later export-share volatility",
        "", f"**{verdict} — descriptive calibration only.**", "",
        f"Complete economies: {diag['complete_economies']} of {diag['source_key_candidate_economies']} key candidates.",
        f"Material absolute HHI changes (at least 0.05): {diag['material_hhi_change_economies']}.",
        f"HHI change IQR: {diag['hhi_change_iqr']:.6g}.",
    ]
    if has_estimate:
        lines += [
            f"Coefficient {estimate['coefficient']:.6g} export/GDP share-change volatility points per +0.1 market HHI change; HC3 SE {estimate['standard_error']:.6g}; two-sided p {estimate['p_value']:.6g}.",
            f"Max residualized exposure share {estimate['max_single_economy_residualized_exposure_share']:.6g}; max residualized outcome share {estimate['max_single_economy_residualized_outcome_share']:.6g}; leave-one-out successes {estimate['loo_successes']}.",
        ]
    else:
        lines += ["No coefficient was estimated because a frozen gate failed."]
    if diag["failed_gates"]:
        lines += [f"Failed gates: {', '.join(diag['failed_gates'])}."]
    lines += [
        "", "The WITS source field is named product_concentration in the local archive but its indicator code is HH-MKT-CNCNTRTN-NDX: export-destination market concentration. It does not measure product concentration.",
        "The WDI outcome is goods-and-services exports divided by GDP. Its volatility can move because GDP changes, and service exports are outside the WITS merchandise-market measure. The 2020 endpoint includes the pandemic.",
        "The old export-product-diversification resilience screen was PARTIAL under a different generic specification and a product/market label mismatch. It remains unchanged. No causal, policy, school, position, or featured credit follows.",
        "Row-level WITS data are not redistributed; exact replay requires the hash-pinned source vintage and applicable terms.", "",
    ]
    (directory / "result_card.md").write_text("\n".join(lines))
    (directory / "replication.py").write_text(
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"subprocess.run([sys.executable, str(root / '{RUNNER}'), '--verify', *sys.argv[1:]], check=True)\n"
    )
    (directory / "evidence_packet.yaml").write_text(yaml.safe_dump({
        "design_id": ID, "verdict": verdict, "evidence_type": "descriptive",
        "causal_claim": False, "policy_effect_credit": False,
        "school_claim_links": [], "correction": correction,
        "source_hashes_verified": True,
        "strict_spec_lock_chronology_verified": True,
        "interpretation": "Prior export-destination market HHI change associated with later export/GDP-share volatility only.",
    }, sort_keys=True))
    parquet_write(directory / "metric_results.parquet", {
        "verdict": [verdict], "complete_economies": [diag["complete_economies"]],
        "material_hhi_change_economies": [diag["material_hhi_change_economies"]],
    }, pa.schema([
        ("verdict", pa.string()), ("complete_economies", pa.int64()),
        ("material_hhi_change_economies", pa.int64()),
    ]))
    if tuple(sorted(path.name for path in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError("Unexpected run artifact roster")


def result_summary(diag: dict, estimate: dict, verdict: str) -> str:
    lines = [
        "# Earlier export-market concentration and later export-share volatility — frozen result",
        "",
        f"**Verdict: {verdict}.** One prospectively registered descriptive test. Complete economies: {diag['complete_economies']} of {diag['source_key_candidate_economies']} source-key candidates.",
        f"Material HHI changes: {diag['material_hhi_change_economies']}; HHI change IQR: {diag['hhi_change_iqr']:.8g}.",
    ]
    if "coefficient" in estimate:
        lines += [
            f"Beta: {estimate['coefficient']:.8g} export/GDP-share volatility points per +0.1 prior market HHI change; HC3 SE: {estimate['standard_error']:.8g}; two-sided p: {estimate['p_value']:.8g}.",
            f"Maximum residualized exposure share: {estimate['max_single_economy_residualized_exposure_share']:.8g}; maximum residualized outcome share: {estimate['max_single_economy_residualized_outcome_share']:.8g}; leave-one-out successes: {estimate['loo_successes']}; failures: {estimate['loo_failures']}.",
        ]
    else:
        lines += ["No public coefficient because a frozen gate failed."]
    lines += [
        f"Failed gates: {', '.join(diag['failed_gates']) if diag['failed_gates'] else 'none'}.",
        "",
        "The local WITS series id says product_concentration, yet its source indicator is HH-MKT-CNCNTRTN-NDX, the export-**market** Herfindahl-Hirschman concentration index. It measures concentration across destination partners, not export products. The archived wits_export_product_diversification_resilience_panel generic screen was PARTIAL and mislabeled this market series as product concentration. No old verdict is relabeled or regraded.",
        "",
        "The WDI outcome is the sample standard deviation of ten annual changes in exports of goods and services as a percentage of GDP, from 2011 through 2020. Changes in the GDP denominator, services outside the WITS merchandise index, and the 2020 pandemic shock limit interpretation. Neither the predictor nor outcome identifies a trade-policy effect or a causal mechanism. No causal, policy, school, position, or featured credit follows. The nominal 0.01 cutoff does not correct the wider archive's model selection.",
        "",
        "The WITS fetch manifest lists World Bank WITS terms; raw WITS values are not copied into tracked artifacts. Exact replay requires the hash-pinned vintage and its source terms.",
        "",
        "Definitions: [WITS market concentration index](https://wits.worldbank.org/WITS/WITS/TradeIndicatorsHelp/TradeOutcomes_Help.htm?AspxAutoDetectCookieSupport=1); [World Bank exports of goods and services/GDP](https://data.worldbank.org/indicator/NE.EXP.GNFS.ZS).",
        "",
    ]
    return "\n".join(lines)


def run_or_verify(source_root: Path, verify: bool) -> None:
    lock, registered, locked = verified_lock(source_root)
    panel, diag = panel_from_sources(source_root, lock["candidate_economies"])
    estimate, verdict = calculate(panel, diag)
    target = ROOT / RUN
    if verify and not target.is_dir():
        raise ValueError("Missing run artifacts")
    if not verify and target.exists():
        raise ValueError("Run already exists")
    with tempfile.TemporaryDirectory(prefix="ieset_wits_market_volatility_") as temporary:
        generated = Path(temporary) / "run"
        emit(generated, diag, estimate, verdict, registered, locked)
        summary = result_summary(diag, estimate, verdict)
        if verify:
            for name in ARTIFACTS:
                if file_sha(generated / name) != file_sha(target / name):
                    raise ValueError(f"Exact replay differs: {name}")
            if (ROOT / SUMMARY).read_text() != summary:
                raise ValueError("Exact result audit differs")
            print(f"Exact replay matched {len(ARTIFACTS)} run artifacts and result audit; verdict {verdict}")
        else:
            shutil.copytree(generated, target)
            (ROOT / SUMMARY).write_text(summary)
            print(json.dumps({"verdict": verdict, **diag, "estimate": estimate},
                             sort_keys=True, indent=2, allow_nan=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.preflight:
        custody, roster = source_custody(args.source_root)
        print(json.dumps({"candidate_economies": len(roster), "roster_sha256": ROSTER_SHA,
                          "sources": custody}, sort_keys=True, indent=2))
    elif args.lock:
        make_lock(args.source_root)
    else:
        run_or_verify(args.source_root, args.verify)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(2)
