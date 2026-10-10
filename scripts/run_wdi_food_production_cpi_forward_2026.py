#!/usr/bin/env python3
"""Frozen food-production/CPI forward panel, registered before selected values."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import patsy
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "wdi_food_production_growth_cpi_forward_2026"
FAMILY = "wdi_food_production_cpi_forward_2026_10_10"
SPEC = f"hypotheses/monetary/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
RUNNER = "scripts/run_wdi_food_production_cpi_forward_2026.py"
PREREG = "engine/audits/wdi_food_production_cpi_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_food_production_cpi_2026_key_roster.csv"
ROSTER_SHA = "52f4a4f8b333ad6fecb6e41fffa6f3217a32ab98a309a47eecd2ebb551619823"
LOCK = "data/pinned_evidence/wdi_food_production_cpi_2026.source.json"
RUN = f"engine/runs/{ID}"
SUMMARY = "engine/audits/wdi_food_production_cpi_results_2026-10-10.md"
MANIFEST_1 = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MANIFEST_2 = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
MANIFEST_SHA_1 = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
MANIFEST_SHA_2 = "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"
SOURCES = {
    "food": {"publisher": "world_bank_wdi", "series_id": "AG.PRD.FOOD.XD",
             "path": "data/vintages/world_bank_wdi/AG.PRD.FOOD.XD@2026-05-05T203847Z.parquet",
             "sha256": "05863480f2da10e8d59cb591a008fb54ad23e7b35d1818d1682fd7a673536876",
             "manifest": MANIFEST_2, "manifest_sha256": MANIFEST_SHA_2},
    "cpi": {"publisher": "world_bank_wdi", "series_id": "FP.CPI.TOTL.ZG",
            "path": "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-05-05T194737Z.parquet",
            "sha256": "dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0",
            "manifest": MANIFEST_1, "manifest_sha256": MANIFEST_SHA_1},
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
            "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
            "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
            "manifest": MANIFEST_1, "manifest_sha256": MANIFEST_SHA_1},
}
T_START, T_END = 2001, 2018
MIN_YEARS = 5
MIN_ROWS, MIN_COUNTRIES = 1000, 100
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 250, 60
MATERIAL = 5.0
FOOD_MAX, CPI_MIN, CPI_MAX = 1000.0, -20.0, 50.0
GDP_MIN, GDP_MAX, X_MAX = -30.0, 30.0, 30.0
MAX_COUNTRY_SHARE, MAX_TOP_ONE_PERCENT = 0.15, 0.25
MIN_FOLD_ROWS, MIN_FOLD_COUNTRIES = 800, 80
P_MAX, MEANINGFUL_BETA = 0.01, 0.05
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 1, "family_alpha": P_MAX, "p_max_two_sided": P_MAX,
              "causal_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "school_score_eligible": False,
              "school_score_credit": 0, "featured_eligible": False}
LIMITS = [
    "The FAO/WDI food index measures price-weighted production volume, not local retail availability or food prices.",
    "The outcome is broad CPI inflation, not a food-price subindex; food can be exported, imported, stored or wasted.",
    "Trade, global food and energy prices, weather, currencies, demand and policy responses can confound both series.",
    "The [-20,50] CPI and +/-30 log-point food-growth eligibility bounds limit inference to a moderate-inflation panel.",
    "Country/year effects, prior inflation and GDP growth, and forward timing do not identify a causal supply or policy effect.",
    "This family was selected after related archive results were visible; its p cutoff does not correct archive-wide selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_add(path: str) -> str:
    lines = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if len(lines) != 1:
        raise RuntimeError(f"expected exactly one first-addition commit for {path}: {lines}")
    return lines[0]


def frozen(path: str, revision: str) -> None:
    full = ROOT / path
    if not full.is_file() or full.read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"registered bytes changed: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted registered path: {path}")


def registration() -> str:
    paths = [SPEC, STEELMAN, RUNNER, PREREG, ROSTER]
    additions = {first_add(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError(f"registration paths have different first-addition commits: {additions}")
    revision = additions.pop()
    for path in paths:
        frozen(path, revision)
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("source-key roster hash changed")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("registration commit already included measured result")
    doc = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = doc["falsification"]["threshold"]
    if (doc.get("hypothesis_id") != ID or doc.get("status") != "pre_registered"
            or doc.get("claim_direction") != "-" or doc.get("evidence_type") != "associational"
            or doc["sample"]["period"] != [2000, 2019]
            or threshold.get("family_id") != FAMILY or threshold.get("family_size") != 1
            or threshold.get("source_key_roster_sha256") != ROSTER_SHA
            or threshold.get("source_lock_path") != LOCK
            or doc.get("covers_claims") != []):
        raise RuntimeError("frozen spec does not match runner")
    return revision


def source_lock(reg: str) -> tuple[str, dict]:
    revision = first_add(LOCK)
    frozen(LOCK, revision)
    if subprocess.run(["git", "merge-base", "--is-ancestor", reg, revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock was not committed after registration")
    data = json.loads((ROOT / LOCK).read_text())
    if (data.get("family_id") != FAMILY or data.get("hypothesis_id") != ID
            or data.get("registration_commit") != reg
            or data.get("source_key_roster_sha256") != ROSTER_SHA
            or data.get("sources") != SOURCES):
        raise RuntimeError("source lock differs from preregistered source roles")
    return revision, data


def check_sources(source_root: Path) -> None:
    for role, src in SOURCES.items():
        raw = source_root / src["path"]
        manifest = source_root / src["manifest"]
        if not raw.is_file() or sha256(raw) != src["sha256"]:
            raise RuntimeError(f"raw source hash mismatch: {role}")
        if not manifest.is_file() or sha256(manifest) != src["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest hash mismatch: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [e for e in entries if e.get("publisher") == src["publisher"]
                   and e.get("series_id") == src["series_id"]
                   and e.get("parquet_path") == src["path"]
                   and e.get("sha256") == src["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"no exact source-manifest entry: {role}")


def roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("roster bytes mismatch")
    with (ROOT / ROSTER).open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["country_iso3", "treatment_year"]:
            raise RuntimeError("roster header mismatch")
        rows = [(r["country_iso3"], int(r["treatment_year"])) for r in reader]
    if (len(rows) != 3888 or len({c for c, _ in rows}) != 216
            or rows != sorted(rows) or len(set(rows)) != len(rows)
            or any(len(c) != 3 or not c.isupper() or not T_START <= y <= T_END for c, y in rows)):
        raise RuntimeError("roster order or key shape changed")
    return rows


def cell_map(source_root: Path, role: str) -> dict[tuple[str, int], tuple[object, object]]:
    src = SOURCES[role]
    frame = pd.read_parquet(source_root / src["path"], columns=[
        "country_iso3", "indicator_id", "year", "value", "obs_status"])
    if set(frame["indicator_id"].dropna()) != {src["series_id"]}:
        raise RuntimeError(f"indicator mismatch: {role}")
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate source key: {role}")
    return {(c, int(y)): (v, s) for c, y, v, s in zip(
        frame.country_iso3, frame.year, frame.value, frame.obs_status)}


def admissible(cell: tuple[object, object] | None, low: float, high: float,
               positive: bool = False) -> float | None:
    if cell is None:
        return None
    value, status = cell
    if status is not None and not pd.isna(status) and str(status).strip() not in ("", "A"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or number < low or number > high or (positive and number <= 0):
        return None
    return number


def build_panel(source_root: Path, keys: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict]:
    food = cell_map(source_root, "food")
    cpi = cell_map(source_root, "cpi")
    gdp = cell_map(source_root, "gdp")
    kept, dropped = [], Counter()
    for country, year in keys:
        f0 = admissible(food.get((country, year-1)), 0, FOOD_MAX, True)
        f1 = admissible(food.get((country, year)), 0, FOOD_MAX, True)
        if f0 is None or f1 is None:
            dropped["missing_or_invalid_food_endpoints"] += 1
            continue
        growth = 100.0 * math.log(f1 / f0)
        if abs(growth) > X_MAX:
            dropped["food_growth_out_of_range"] += 1
            continue
        p0 = admissible(cpi.get((country, year)), CPI_MIN, CPI_MAX)
        p1 = admissible(cpi.get((country, year+1)), CPI_MIN, CPI_MAX)
        if p0 is None or p1 is None:
            dropped["missing_or_invalid_cpi_endpoints"] += 1
            continue
        g0 = admissible(gdp.get((country, year)), GDP_MIN, GDP_MAX)
        if g0 is None:
            dropped["missing_or_invalid_gdp_growth"] += 1
            continue
        kept.append((country, year, growth, p1, p0, g0))
    frame = pd.DataFrame(kept, columns=["country", "year", "x", "y", "pi_t", "gdp_t"])
    before_floor = len(frame)
    if not frame.empty:
        counts = frame.country.value_counts()
        frame = frame.loc[frame.country.map(counts).ge(MIN_YEARS)].copy()
        dropped["country_below_five_year_floor"] = before_floor - len(frame)
    else:
        dropped["country_below_five_year_floor"] = 0
    frame = frame.sort_values(["year", "country"]).reset_index(drop=True)
    material = frame.x.abs().ge(MATERIAL) if not frame.empty else pd.Series(dtype=bool)
    sample = {"key_roster_rows": len(keys), "key_roster_countries": len({c for c,_ in keys}),
              "complete_rows_before_country_floor": before_floor,
              "valid_rows": len(frame), "valid_countries": int(frame.country.nunique()) if not frame.empty else 0,
              "material_rows": int(material.sum()),
              "material_countries": int(frame.loc[material, "country"].nunique()) if not frame.empty else 0,
              "dropped": dict(sorted(dropped.items())),
              "selected_values_read_after_committed_lock": True}
    return frame, sample


def fit(frame: pd.DataFrame) -> dict:
    if len(frame) < 10 or frame.country.nunique() < 5:
        raise ValueError("too few rows/countries for fixed-effects estimator")
    design = patsy.dmatrix("1 + x + pi_t + gdp_t + C(country) + C(year)", frame,
                           return_type="dataframe")
    matrix = design.to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != matrix.shape[1]:
        raise ValueError(f"rank deficient design {rank}/{matrix.shape[1]}")
    model = sm.OLS(frame.y.to_numpy(dtype=float), matrix).fit(
        cov_type="cluster", cov_kwds={"groups": frame.country.to_numpy(),
                                      "use_correction": True, "df_correction": True})
    ix = list(design.columns).index("x")
    beta, se = float(model.params[ix]), float(model.bse[ix])
    countries = int(frame.country.nunique())
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        raise ValueError("nonfinite or nonpositive country-cluster uncertainty")
    p = float(2 * student_t.sf(abs(beta / se), df=countries - 1))
    if not math.isfinite(p):
        raise ValueError("nonfinite two-sided p")
    z = patsy.dmatrix("1 + pi_t + gdp_t + C(country) + C(year)", frame,
                      return_type="dataframe").to_numpy(dtype=float)
    x = frame.x.to_numpy(dtype=float)
    residual = x - z @ np.linalg.lstsq(z, x, rcond=None)[0]
    square = residual ** 2
    total = float(square.sum())
    if not math.isfinite(total) or total <= 1e-12:
        raise ValueError("no residualized food-growth variation")
    shares = pd.DataFrame({"country": frame.country.to_numpy(), "square": square})
    country_share = float(shares.groupby("country").square.sum().max() / total)
    k = max(1, math.ceil(len(frame) * .01))
    top_row_share = float(np.sort(square)[-k:].sum() / total)
    critical = float(student_t.ppf(1 - P_MAX / 2, df=countries - 1))
    return {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
            "confidence_interval_99pct": [beta - critical * se, beta + critical * se],
            "n_rows": len(frame), "n_countries": countries, "df_inference": countries - 1,
            "model_rank": rank, "model_columns": matrix.shape[1],
            "top_country_residualized_exposure_share": country_share,
            "top_one_percent_residualized_exposure_share": top_row_share,
            "method": "country/year fixed-effects OLS; country-cluster CR1; Student t(G-1)"}


def fold(country: str) -> int:
    return int(hashlib.sha256(country.encode()).hexdigest()[:8], 16) % 5


def analyze(source_root: Path, run_utc: str, reg: str, lock_commit: str) -> tuple[dict, pd.DataFrame]:
    keys = roster()
    frame, sample = build_panel(source_root, keys)
    failures = []
    if sample["valid_rows"] < MIN_ROWS:
        failures.append("complete_row_floor")
    if sample["valid_countries"] < MIN_COUNTRIES:
        failures.append("complete_country_floor")
    if sample["material_rows"] < MIN_MATERIAL_ROWS:
        failures.append("material_row_floor")
    if sample["material_countries"] < MIN_MATERIAL_COUNTRIES:
        failures.append("material_country_floor")
    primary = None
    if not frame.empty:
        try:
            primary = fit(frame)
        except ValueError as exc:
            failures.append("primary_estimator: " + str(exc))
    if primary:
        if primary["top_country_residualized_exposure_share"] > MAX_COUNTRY_SHARE:
            failures.append("top_country_residual_concentration")
        if primary["top_one_percent_residualized_exposure_share"] > MAX_TOP_ONE_PERCENT:
            failures.append("top_one_percent_residual_concentration")
    folds = []
    for omitted in range(5):
        part = frame.loc[frame.country.map(fold).ne(omitted)].copy()
        record = {"omitted_hash_fold": omitted, "n_rows": len(part),
                  "n_countries": int(part.country.nunique()) if not part.empty else 0}
        if record["n_rows"] < MIN_FOLD_ROWS or record["n_countries"] < MIN_FOLD_COUNTRIES:
            failures.append(f"fold_{omitted}_sample_floor")
        try:
            fitted = fit(part)
            record.update({"coefficient": fitted["coefficient"],
                           "std_error": fitted["std_error"],
                           "p_value_two_sided": fitted["p_value_two_sided"]})
        except ValueError as exc:
            record["fit_error"] = str(exc)
            failures.append(f"fold_{omitted}_estimator")
        folds.append(record)
    negative_folds = sum(row.get("coefficient", 0) < 0 for row in folds)
    positive_folds = sum(row.get("coefficient", 0) > 0 for row in folds)
    if failures:
        verdict, reason = "INCONCLUSIVE", "; ".join(sorted(set(failures)))
    elif (primary["coefficient"] <= -MEANINGFUL_BETA
          and primary["p_value_two_sided"] <= P_MAX and negative_folds >= 4):
        verdict, reason = "SUPPORTED", "negative meaningful slope and four-fold sign rule clear"
    elif (primary["coefficient"] >= MEANINGFUL_BETA
          and primary["p_value_two_sided"] <= P_MAX and positive_folds >= 4):
        verdict, reason = "REFUTED", "positive meaningful slope and four-fold sign rule clear"
    else:
        verdict, reason = "PARTIAL", "estimable panel misses a directional gate"
    diag = {"hypothesis_id": ID, "family_id": FAMILY, "family_size": 1,
            "run_utc": run_utc, "runner": RUNNER, "registration_commit": reg,
            "source_lock_commit": lock_commit, "source_lock": LOCK,
            "source_key_roster_sha256": ROSTER_SHA,
            "verdict": verdict, "verdict_label": verdict, "verdict_reason": reason,
            "template": "panel_fe", "preflight": sample, "primary": primary,
            "holdout_folds": folds, "negative_fold_signs": negative_folds,
            "positive_fold_signs": positive_folds, "failed_gates": sorted(set(failures)),
            "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MEANINGFUL_BETA,
            "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
            "correction": CORRECTION, "limitations": LIMITS}
    return diag, frame


def payloads(diag: dict, frame: pd.DataFrame) -> dict[str, bytes]:
    verdict = diag["verdict"]
    manifest = {"hypothesis_id": ID, "run_utc": diag["run_utc"], "runner": RUNNER,
                "preregistration_commit": diag["registration_commit"],
                "source_lock_commit": diag["source_lock_commit"], "source_lock": LOCK,
                "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": diag["preflight"], "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": diag["run_utc"],
              "hypothesis": {"id": ID, "path": SPEC, "topic": "monetary"},
              "preregistration": {"spec_commit": diag["registration_commit"],
                                  "source_lock_commit": diag["source_lock_commit"],
                                  "family_id": FAMILY, "family_size": 1,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": STEELMAN},
              "reproduction": {"runner": RUNNER, "run_dir": RUN,
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(),
                          "reason": diag["verdict_reason"]},
              "data": {"inputs": SOURCES, "sample": diag["preflight"]},
              "results": {"primary": diag["primary"], "folds": diag["holdout_folds"]},
              "failed_gates": diag["failed_gates"], "limitations": LIMITS,
              "correction": CORRECTION}
    years = []
    if not frame.empty:
        for year, group in frame.groupby("year", sort=True):
            years.append({"treatment_year": int(year), "n": len(group),
                          "median_food_growth_log_points": float(group.x.median()),
                          "median_next_year_cpi_inflation": float(group.y.median())})
    chart = {"hypothesis_id": ID, "interpretation": "descriptive valid-row annual medians only",
             "years": years}
    primary = diag["primary"] or {}
    coeff = pd.DataFrame([{"term": "food_production_growth",
                           "coefficient": primary.get("coefficient", math.nan),
                           "std_error": primary.get("std_error", math.nan),
                           "p_value_two_sided": primary.get("p_value_two_sided", math.nan),
                           "n_rows": primary.get("n_rows", 0),
                           "n_countries": primary.get("n_countries", 0)}])
    import io
    buffer = io.BytesIO()
    coeff.to_parquet(buffer, index=False)
    beta_text = (f"{primary['coefficient']:+.6f}" if primary else "unavailable")
    p_text = (f"{primary['p_value_two_sided']:.6g}" if primary else "unavailable")
    card = (f"# {ID}\n\n**{verdict}** — {diag['verdict_reason']}.\n\n"
            f"The locked country/year fixed-effects coefficient is {beta_text} broad CPI inflation "
            f"percentage points per +1 log-percentage point annual food-production growth; "
            f"two-sided country-cluster p={p_text}. "
            f"Complete sample: {diag['preflight']['valid_rows']} country-years in "
            f"{diag['preflight']['valid_countries']} countries. "
            f"This is a prospective descriptive calibration, not a policy or causal effect.\n\n"
            f"Registration: `{diag['registration_commit']}`; source lock: "
            f"`{diag['source_lock_commit']}`. Replay with `python3 {RUNNER} --verify`.\n\n"
            "The FAO index is production volume; CPI covers the full consumer basket. "
            "The design excludes extreme inflation and production changes. "
            "No school, position, policy, causal or featured credit.\n")
    replication = ("#!/usr/bin/env python3\nimport subprocess\nimport sys\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify']))\n")
    def js(value: object) -> bytes:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    def ya(value: object) -> bytes:
        return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()
    return {"hypothesis.yaml": (ROOT / SPEC).read_bytes(),
            "manifest.yaml": ya(manifest), "evidence_packet.yaml": ya(packet),
            "diagnostics.json": js(diag), "chart_data.json": js(chart),
            "coefficients.parquet": buffer.getvalue(),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def summary(diag: dict) -> str:
    p = diag["primary"] or {}
    return ("# Food-production volume to next-year CPI — locked result\n\n"
            f"**{diag['verdict']}**. {diag['verdict_reason']}.\n\n"
            f"Fixed key roster: {diag['preflight']['key_roster_rows']} rows / "
            f"{diag['preflight']['key_roster_countries']} countries. "
            f"Complete eligible panel after the five-year country floor: "
            f"{diag['preflight']['valid_rows']} rows / {diag['preflight']['valid_countries']} countries. "
            f"Material food-growth rows: {diag['preflight']['material_rows']} across "
            f"{diag['preflight']['material_countries']} countries.\n\n"
            f"Primary beta {p.get('coefficient', 'unavailable')}; country-cluster SE "
            f"{p.get('std_error', 'unavailable')}; two-sided p "
            f"{p.get('p_value_two_sided', 'unavailable')}; "
            f"negative/positive fold signs {diag['negative_fold_signs']}/"
            f"{diag['positive_fold_signs']}. Failed gates: {diag['failed_gates']}.\n\n"
            "The coefficient relates earlier food-production *volume* to later broad CPI inflation "
            "within the registered moderate-inflation panel. The source may miss market availability "
            "and CPI food prices; climate, imports/exports, currencies, global prices, demand, "
            "policy and measurement can confound both. No causal, policy, school, position, "
            "or featured credit. Within-family p=0.01 does not correct archive-wide selection.\n\n"
            f"Spec commit `{diag['registration_commit']}`; source lock commit "
            f"`{diag['source_lock_commit']}`. Exact replay: `python3 {RUNNER} --verify`.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    reg = registration()
    lock_commit, _ = source_lock(reg)
    check_sources(args.source_root)
    keys = roster()
    if args.preflight:
        print(json.dumps({"registration_commit": reg, "source_lock_commit": lock_commit,
                          "source_key_rows": len(keys), "source_key_countries": len({c for c,_ in keys}),
                          "source_hashes": {role: src["sha256"] for role,src in SOURCES.items()}},
                         sort_keys=True))
        return 0
    out = ROOT / RUN
    if args.verify:
        if not out.is_dir() or not (ROOT / SUMMARY).is_file():
            raise RuntimeError("no saved run to verify")
        prior = json.loads((out / "diagnostics.json").read_text())
        run_utc = prior["run_utc"]
    else:
        if out.exists() or (ROOT / SUMMARY).exists():
            raise RuntimeError("result already exists; use --verify")
        run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diag, frame = analyze(args.source_root, run_utc, reg, lock_commit)
    files = payloads(diag, frame)
    report = summary(diag).encode()
    if args.verify:
        for name, data in files.items():
            if (out / name).read_bytes() != data:
                raise RuntimeError(f"replay mismatch: {name}")
        if (ROOT / SUMMARY).read_bytes() != report:
            raise RuntimeError("replay mismatch: result audit")
        print(f"OK exact replay: {len(files)} run artifacts + result audit; {diag['verdict']}")
        return 0
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    (ROOT / SUMMARY).write_bytes(report)
    print(f"{diag['verdict']} beta={diag['primary']['coefficient'] if diag['primary'] else None} "
          f"p={diag['primary']['p_value_two_sided'] if diag['primary'] else None} "
          f"n={diag['preflight']['valid_rows']} countries={diag['preflight']['valid_countries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
