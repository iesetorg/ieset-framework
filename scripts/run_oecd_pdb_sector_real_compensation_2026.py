#!/usr/bin/env python3
"""Source-locked OECD PDB sector productivity -> future real pay family.

Plan and locks inspect only schema/series/country/year keys. Selected values
and observation-status masks are opened after registration and three locks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml
from jsonschema import Draft202012Validator

import run_oecd_pdb_sector_productivity_employment_2026 as core

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "oecd_pdb_sector_productivity_forward_real_compensation_2026_10_10"
SECTORS = {
    "C": ("manufacturing", "Manufacturing"),
    "G": ("wholesale_retail", "Wholesale and retail trade"),
    "J": ("ict", "Information and communication"),
}
IDS = tuple(f"oecd_pdb_{name}_productivity_next_year_real_compensation_2026"
            for name, _ in SECTORS.values())
PDB_REL = "data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet"
PDB_SHA = "3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c"
PDB_MANIFEST = "data/manifests/fetch_run_2026-05-19T095056Z.yaml"
PDB_MANIFEST_SHA = "cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4"
CPI_REL = "data/vintages/world_bank_wdi/FP.CPI.TOTL.ZG@2026-05-05T194737Z.parquet"
CPI_SHA = "dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0"
CPI_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
CPI_MANIFEST_SHA = "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"
CORE_RUNNER_REL = "scripts/run_oecd_pdb_sector_productivity_employment_2026.py"
CORE_RUNNER_SHA = "9d43de35863e63f4b184883e818cd7c05b67f13a4af7397128c56085831e6f0c"
RUNNER_REL = "scripts/run_oecd_pdb_sector_real_compensation_2026.py"
PLAN_REL = "engine/audits/oecd_pdb_sector_real_compensation_prereg_2026-10-10.md"
REPORT_REL = "engine/audits/oecd_pdb_sector_real_compensation_results_2026-10-10.md"
ROSTER_REL = "data/pinned_evidence/oecd_pdb_sector_real_compensation_2026_key_roster.csv"
ROSTER_SHA = "d3e0e611f9f3407efbc646a5b2d00b3a1a3ccd685d15fd37136d215082cea18b"
SPEC_RELS = tuple(f"hypotheses/labour/{hid}.yaml" for hid in IDS)
STEELMAN_RELS = tuple(f"hypotheses/steelman/{hid}.md" for hid in IDS)
LOCK_RELS = tuple(f"data/pinned_evidence/{hid}.source.json" for hid in IDS)
DIAG_RELS = tuple(f"engine/runs/{hid}/diagnostics.json" for hid in IDS)
REGISTERED = SPEC_RELS + STEELMAN_RELS + (RUNNER_REL, PLAN_REL, ROSTER_REL)
PDB_KEYS = ("REF_AREA", "FREQ", "MEASURE", "ACTIVITY", "UNIT_MEASURE",
            "PRICE_BASE", "TRANSFORMATION", "ASSET_CODE", "CONVERSION_TYPE", "period")
PDB_VALUES = PDB_KEYS + ("value", "OBS_STATUS", "UNIT_MULT")
CPI_KEYS = ("country_iso3", "indicator_id", "year")
CPI_VALUES = CPI_KEYS + ("value", "obs_status")
GATES = {"family_size": 3, "holm_alpha": 0.05,
         "meaningful_beta_abs_real_pay_log_pp_per_productivity_pp": 0.05,
         "minimum_rows": 450, "minimum_countries": 22,
         "minimum_years_with_twelve_countries": 20,
         "minimum_complete_years_per_country": 10,
         "minimum_residual_productivity_sd_pp": 1.0,
         "minimum_residual_real_pay_sd_log_pp": 0.5,
         "maximum_country_productivity_ss_share": 0.20,
         "maximum_top_one_percent_productivity_ss_share": 0.30,
         "minimum_same_sign_hash_folds": 4,
         "minimum_fold_rows": 320, "minimum_fold_countries": 17,
         "maximum_abs_productivity_growth_pp": 50.0,
         "nominal_comp_growth_min_pp": -50.0,
         "nominal_comp_growth_max_pp": 100.0,
         "cpi_inflation_min_pp": -20.0,
         "cpi_inflation_max_pp": 50.0,
         "maximum_abs_real_pay_growth_log_pp": 50.0}
LIMITS = [
    "Three sectors share the same productivity source, CPI deflator, countries, years and model; this is one correlated family, not three replications.",
    "OECD PDB LCEMP is nominal labour compensation per employee; national WDI CPI is a broad consumer basket, not each sector's output deflator or a measure of median wages.",
    "Compensation per employee can change with worker composition and hours; employment and wage bargaining can respond jointly to demand and productivity.",
    "Country/year effects, prior real-pay growth and a one-year lead do not identify causal productivity pass-through or a policy effect.",
    "The frozen OECD core and moderate-growth/inflation bounds limit generalization; no post-result source or threshold change is permitted.",
    "Sectors and signs were selected after related archive visibility. Holm controls this three-cell family only, not archive-wide selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def js(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False,
                       ensure_ascii=False) + "\n").encode()


def ya(value: Any) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode()


def git(*args: str) -> bytes:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if process.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {process.stderr.decode(errors='replace')}")
    return process.stdout


def first_add(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}: {commits}")
    return commits[0]


def ancestor(earlier: str, later: str) -> bool:
    return earlier != later and subprocess.run(
        ["git", "merge-base", "--is-ancestor", earlier, later], cwd=ROOT,
        capture_output=True).returncode == 0


def frozen(relative: str, revision: str) -> None:
    if (ROOT / relative).read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"registered file changed: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted registered file: {relative}")


def registration_commit() -> str:
    commits = {first_add(relative) for relative in REGISTERED}
    if len(commits) != 1:
        raise RuntimeError(f"registration files do not share first commit: {commits}")
    commit = commits.pop()
    for relative in REGISTERED:
        frozen(relative, commit)
    if sha(ROOT / ROSTER_REL) != ROSTER_SHA:
        raise RuntimeError("key roster hash mismatch")
    if git("ls-tree", "-r", "--name-only", commit, "--", *LOCK_RELS, *DIAG_RELS).strip():
        raise RuntimeError("registration commit contained lock or measured result")
    schema = json.loads(git("show", f"{commit}:schemas/hypothesis.schema.json"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for relative in SPEC_RELS:
        if not validator.is_valid(yaml.safe_load((ROOT / relative).read_bytes())):
            raise RuntimeError(f"first committed spec invalid: {relative}")
    return commit


def source_paths(source_root: Path) -> tuple[Path, Path]:
    if sha(ROOT / CORE_RUNNER_REL) != CORE_RUNNER_SHA:
        raise RuntimeError("frozen shared estimator dependency changed")
    entries = ((PDB_REL, PDB_SHA, PDB_MANIFEST, PDB_MANIFEST_SHA, "oecd", "DSD_PDB"),
               (CPI_REL, CPI_SHA, CPI_MANIFEST, CPI_MANIFEST_SHA, "world_bank_wdi", "FP.CPI.TOTL.ZG"))
    paths = []
    for relative, digest, manifest_rel, manifest_digest, publisher, series in entries:
        path = source_root / relative
        manifest = ROOT / manifest_rel
        if not path.is_file() or sha(path) != digest:
            raise RuntimeError(f"pinned source absent/hash mismatch: {relative}")
        if not manifest.is_file() or sha(manifest) != manifest_digest:
            raise RuntimeError(f"pinned fetch manifest absent/hash mismatch: {manifest_rel}")
        records = yaml.safe_load(manifest.read_text()).get("entries", [])
        matched = [row for row in records if row.get("publisher") == publisher
                   and row.get("series_id") == series and row.get("parquet_path") == relative
                   and row.get("sha256") == digest]
        if len(matched) != 1:
            raise RuntimeError(f"no exact fetch-manifest entry: {relative}")
        paths.append(path)
    if not set(PDB_VALUES).issubset(pq.ParquetFile(paths[0]).schema_arrow.names):
        raise RuntimeError("PDB source schema lacks frozen columns")
    if not set(CPI_VALUES).issubset(pq.ParquetFile(paths[1]).schema_arrow.names):
        raise RuntimeError("WDI CPI source schema lacks frozen columns")
    return paths[0], paths[1]


def roster_bytes(pdb_path: Path, cpi_path: Path) -> bytes:
    """Categorical identities and country/year keys only; never value/status columns."""
    frame = pq.read_table(pdb_path, columns=list(PDB_KEYS)).to_pandas()
    common = (frame.FREQ.eq("A") & frame.ACTIVITY.isin(SECTORS)
              & frame.REF_AREA.isin(core.OECD_CORE) & frame.ASSET_CODE.eq("_Z")
              & frame.CONVERSION_TYPE.eq("_Z"))
    def pdb_keys(measure: str, unit: str, price: str) -> set[tuple[str, str, int]]:
        part = frame[common & frame.MEASURE.eq(measure) & frame.UNIT_MEASURE.eq(unit)
                     & frame.PRICE_BASE.eq(price) & frame.TRANSFORMATION.eq("GY")]
        rows = [(str(s), str(c), int(y)) for s, c, y in zip(part.ACTIVITY, part.REF_AREA, part.period)]
        if len(rows) != len(set(rows)):
            raise RuntimeError("duplicate selected OECD key")
        return set(rows)
    productivity = pdb_keys("GVAHRS", "XDC_H", "LR")
    compensation = pdb_keys("LCEMP", "XDC_PS", "V")
    wdi = pq.read_table(cpi_path, columns=list(CPI_KEYS)).to_pandas()
    wdi = wdi[wdi.country_iso3.isin(core.OECD_CORE) & wdi.indicator_id.eq("FP.CPI.TOTL.ZG")]
    cpi_rows = [(str(c), int(y)) for c, y in zip(wdi.country_iso3, wdi.year)]
    if len(cpi_rows) != len(set(cpi_rows)):
        raise RuntimeError("duplicate selected WDI CPI key")
    cpi = set(cpi_rows)
    roster = sorted((s, c, t) for s, c, t in productivity if 1996 <= t <= 2023
                    and (s, c, t) in compensation and (s, c, t + 1) in compensation
                    and (c, t) in cpi and (c, t + 1) in cpi)
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(("sector", "country_iso3", "treatment_year"))
    writer.writerows(roster)
    return out.getvalue().encode()


def key_info(pdb_path: Path, cpi_path: Path) -> dict[str, Any]:
    expected = roster_bytes(pdb_path, cpi_path)
    if hashlib.sha256(expected).hexdigest() != ROSTER_SHA:
        raise RuntimeError("pinned key roster changed")
    if not (ROOT / ROSTER_REL).is_file() or (ROOT / ROSTER_REL).read_bytes() != expected:
        raise RuntimeError("tracked roster differs from source keys")
    rows = list(csv.DictReader(io.StringIO(expected.decode())))
    return {"key_roster_sha256": ROSTER_SHA, "source_key_rows": len(rows),
            "source_key_rows_per_sector": {s: sum(item["sector"] == s for item in rows)
                                           for s in SECTORS},
            "pdb_selected_schema": {field: str(pq.ParquetFile(pdb_path).schema_arrow.field(field).type)
                                    for field in PDB_VALUES},
            "cpi_selected_schema": {field: str(pq.ParquetFile(cpi_path).schema_arrow.field(field).type)
                                    for field in CPI_VALUES}}


def create_lock(pdb_path: Path, cpi_path: Path, hypothesis_id: str) -> None:
    registration = registration_commit()
    index = IDS.index(hypothesis_id)
    previous = registration if index == 0 else first_add(LOCK_RELS[index - 1])
    if git("rev-parse", "HEAD").decode().strip() != previous:
        raise RuntimeError("metadata locks must be created/committed in frozen sector order")
    relative = LOCK_RELS[index]
    if (ROOT / relative).exists():
        raise RuntimeError("source lock already exists")
    info = key_info(pdb_path, cpi_path)
    lock = {"hypothesis_id": hypothesis_id, "family_id": FAMILY, "family_size": 3,
            "registration_commit": registration, "source_sha256": PDB_SHA,
            "secondary_source_sha256": CPI_SHA, "key_roster_sha256": ROSTER_SHA,
            "sources": [{"publisher": "OECD Productivity Database", "path": PDB_REL,
                         "sha256": PDB_SHA, "fetch_manifest": PDB_MANIFEST,
                         "fetch_manifest_sha256": PDB_MANIFEST_SHA,
                         "license": "OECD standard permissions; attribution required"},
                        {"publisher": "World Bank World Development Indicators", "path": CPI_REL,
                         "sha256": CPI_SHA, "fetch_manifest": CPI_MANIFEST,
                         "fetch_manifest_sha256": CPI_MANIFEST_SHA,
                         "license": "World Bank CC BY 4.0 attribution"}],
            "selected_values_or_status_read": False, **info}
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(js(lock))
    print(json.dumps({"lock": relative, "registration_commit": registration,
                      "key_rows": info["source_key_rows"]}, sort_keys=True))


def committed_locks(registration: str, pdb_path: Path, cpi_path: Path) -> list[str]:
    info = key_info(pdb_path, cpi_path)
    commits: list[str] = []
    for index, relative in enumerate(LOCK_RELS):
        revision = first_add(relative)
        previous = registration if index == 0 else commits[-1]
        if not ancestor(previous, revision):
            raise RuntimeError("metadata source-lock chronology failed")
        if git("diff-tree", "--no-commit-id", "--name-only", "-r", revision).decode().splitlines() != [relative]:
            raise RuntimeError("each source-lock commit must contain one exact file")
        frozen(relative, revision)
        lock = json.loads((ROOT / relative).read_text())
        expected = {"hypothesis_id": IDS[index], "family_id": FAMILY,
                    "family_size": 3, "registration_commit": registration,
                    "source_sha256": PDB_SHA, "secondary_source_sha256": CPI_SHA,
                    "key_roster_sha256": ROSTER_SHA, **info}
        if any(lock.get(k) != v for k, v in expected.items()):
            raise RuntimeError(f"source lock mismatch: {relative}")
        commits.append(revision)
    if git("ls-tree", "-r", "--name-only", commits[-1], "--", *DIAG_RELS).strip():
        raise RuntimeError("result predates final source lock")
    return commits


def selected_values(pdb_path: Path, cpi_path: Path) -> tuple[dict[tuple[str, str, int, str], tuple[Any, Any, Any]],
                                                             dict[tuple[str, int], tuple[Any, Any]]]:
    """Called only after registration and all three committed source locks pass."""
    frame = pq.read_table(pdb_path, columns=list(PDB_VALUES)).to_pandas()
    common = (frame.FREQ.eq("A") & frame.ACTIVITY.isin(SECTORS)
              & frame.REF_AREA.isin(core.OECD_CORE) & frame.ASSET_CODE.eq("_Z")
              & frame.CONVERSION_TYPE.eq("_Z") & frame.TRANSFORMATION.eq("GY"))
    series = (("productivity", "GVAHRS", "XDC_H", "LR"),
              ("compensation", "LCEMP", "XDC_PS", "V"))
    out: dict[tuple[str, str, int, str], tuple[Any, Any, Any]] = {}
    for role, measure, unit, price in series:
        part = frame[common & frame.MEASURE.eq(measure)
                     & frame.UNIT_MEASURE.eq(unit) & frame.PRICE_BASE.eq(price)]
        for row in part.itertuples(index=False):
            key = (str(row.ACTIVITY), str(row.REF_AREA), int(row.period), role)
            if key in out:
                raise RuntimeError("duplicate selected OECD value key")
            out[key] = (row.value, row.OBS_STATUS, row.UNIT_MULT)
    frame = pq.read_table(cpi_path, columns=list(CPI_VALUES)).to_pandas()
    frame = frame[frame.country_iso3.isin(core.OECD_CORE) & frame.indicator_id.eq("FP.CPI.TOTL.ZG")]
    cpi: dict[tuple[str, int], tuple[Any, Any]] = {}
    for row in frame.itertuples(index=False):
        key = (str(row.country_iso3), int(row.year))
        if key in cpi:
            raise RuntimeError("duplicate selected WDI CPI value key")
        cpi[key] = (row.value, row.obs_status)
    return out, cpi


def allowed_status(status: Any) -> bool:
    return status is None or str(status).strip() in ("", "A", "nan", "None")


def pdb_growth(cell: tuple[Any, Any, Any] | None, low: float, high: float) -> float | None:
    if cell is None or not allowed_status(cell[1]):
        return None
    try:
        value = float(cell[0])
        multiplier = float(cell[2]) if cell[2] is not None else 0.0
    except (TypeError, ValueError):
        return None
    if not math.isfinite(value) or not math.isfinite(multiplier) or multiplier != 0:
        return None
    return value if low <= value <= high else None


def wdi_cpi(cell: tuple[Any, Any] | None) -> float | None:
    if cell is None or not allowed_status(cell[1]):
        return None
    try:
        value = float(cell[0])
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) and GATES["cpi_inflation_min_pp"] <= value <= GATES["cpi_inflation_max_pp"] else None


def panel(pdb: dict[tuple[str, str, int, str], tuple[Any, Any, Any]],
          cpi: dict[tuple[str, int], tuple[Any, Any]],
          sector: str) -> tuple[list[tuple[str, int, float, float, float]], dict[str, Any]]:
    roster = list(csv.DictReader((ROOT / ROSTER_REL).open(newline="")))
    candidates = [row for row in roster if row["sector"] == sector]
    rows: list[tuple[str, int, float, float, float]] = []
    dropped: Counter[str] = Counter()
    for row in candidates:
        country, year = row["country_iso3"], int(row["treatment_year"])
        x = pdb_growth(pdb.get((sector, country, year, "productivity")),
                       -GATES["maximum_abs_productivity_growth_pp"],
                       GATES["maximum_abs_productivity_growth_pp"])
        if x is None:
            dropped["missing_or_invalid_productivity"] += 1
            continue
        nominal = [pdb_growth(pdb.get((sector, country, t, "compensation")),
                              GATES["nominal_comp_growth_min_pp"], GATES["nominal_comp_growth_max_pp"])
                   for t in (year, year + 1)]
        inflation = [wdi_cpi(cpi.get((country, t))) for t in (year, year + 1)]
        if any(v is None for v in nominal):
            dropped["missing_or_invalid_nominal_compensation"] += 1
            continue
        if any(v is None for v in inflation):
            dropped["missing_or_invalid_cpi"] += 1
            continue
        prior, future = [100.0 * (math.log1p(n / 100.0) - math.log1p(p / 100.0))
                         for n, p in zip(nominal, inflation)]
        if (abs(prior) > GATES["maximum_abs_real_pay_growth_log_pp"]
                or abs(future) > GATES["maximum_abs_real_pay_growth_log_pp"]):
            dropped["real_compensation_growth_out_of_range"] += 1
            continue
        rows.append((country, year, x, future, prior))
    complete_before_floor = len(rows)
    counts = Counter(row[0] for row in rows)
    rows = [row for row in rows if counts[row[0]] >= GATES["minimum_complete_years_per_country"]]
    dropped["country_below_ten_year_floor"] = complete_before_floor - len(rows)
    year_counts = Counter(row[1] for row in rows)
    sample = {"key_roster_rows": len(candidates), "key_roster_countries": len({r["country_iso3"] for r in candidates}),
              "complete_rows_before_country_floor": complete_before_floor,
              "valid_rows": len(rows), "valid_countries": len({r[0] for r in rows}),
              "years_with_twelve_countries": sum(n >= 12 for n in year_counts.values()),
              "treatment_year_min": min((r[1] for r in rows), default=None),
              "treatment_year_max": max((r[1] for r in rows), default=None),
              "dropped": dict(sorted(dropped.items())),
              "selected_values_read_after_committed_locks": True}
    return sorted(rows), sample


def evaluate(pdb: dict[tuple[str, str, int, str], tuple[Any, Any, Any]],
             cpi: dict[tuple[str, int], tuple[Any, Any]], sector: str) -> dict[str, Any]:
    rows, sample = panel(pdb, cpi, sector)
    failures = []
    if sample["valid_rows"] < GATES["minimum_rows"]:
        failures.append("row_floor")
    if sample["valid_countries"] < GATES["minimum_countries"]:
        failures.append("country_floor")
    if sample["years_with_twelve_countries"] < GATES["minimum_years_with_twelve_countries"]:
        failures.append("year_coverage_floor")
    primary = core.fit(rows) if rows else None
    if primary is None:
        failures.append("estimator_or_rank_failure")
    else:
        # The shared fixed-effect estimator calls its generic outcome spread
        # "employment"; in this family the outcome is CPI-deflated pay.
        primary["residual_real_pay_sd_log_pp"] = primary.pop("residual_employment_sd_pp")
        rules = (("residual_productivity_sd_pp", GATES["minimum_residual_productivity_sd_pp"], True),
                 ("residual_real_pay_sd_log_pp", GATES["minimum_residual_real_pay_sd_log_pp"], True),
                 ("maximum_country_productivity_ss_share", GATES["maximum_country_productivity_ss_share"], False),
                 ("top_one_percent_productivity_ss_share", GATES["maximum_top_one_percent_productivity_ss_share"], False))
        for key, limit, lower in rules:
            value = primary[key]
            if not math.isfinite(value) or (value < limit if lower else value > limit):
                failures.append(key + "_gate")
    folds = []
    for omitted in range(5):
        part = [row for row in rows if core.fold(row[0]) != omitted]
        item: dict[str, Any] = {"omitted_hash_fold": omitted, "rows": len(part),
                                "countries": len({row[0] for row in part})}
        if item["rows"] < GATES["minimum_fold_rows"] or item["countries"] < GATES["minimum_fold_countries"]:
            failures.append(f"fold_{omitted}_sample_floor")
        fit = core.fit(part, full=False) if part else None
        if fit is None or not math.isfinite(fit["beta"]):
            failures.append(f"fold_{omitted}_estimator_failure")
        else:
            item["beta"] = fit["beta"]
        folds.append(item)
    return {"sample": sample, "primary": primary, "hash_folds": folds,
            "gate_failures": sorted(set(failures)), "holm_adjusted_p": None,
            "same_direction_folds": None, "opposite_direction_folds": None,
            "verdict": "INCONCLUSIVE"}


def measured_results(pdb_path: Path, cpi_path: Path, run_utc: str) -> list[dict[str, Any]]:
    registration = registration_commit()
    commits = committed_locks(registration, pdb_path, cpi_path)
    pdb, cpi = selected_values(pdb_path, cpi_path)
    cases = [evaluate(pdb, cpi, sector) for sector in SECTORS]
    adjusted = core.holm_adjusted([
        case["primary"]["p_two_sided"] if not case["gate_failures"] and case["primary"] else None
        for case in cases])
    output = []
    for index, ((sector, (_, label)), case) in enumerate(zip(SECTORS.items(), cases)):
        primary = case["primary"]
        same = sum(item.get("beta", 0) > 0 for item in case["hash_folds"])
        opposite = sum(item.get("beta", 0) < 0 for item in case["hash_folds"])
        case["same_direction_folds"] = same
        case["opposite_direction_folds"] = opposite
        case["holm_adjusted_p"] = adjusted[index]
        if not case["gate_failures"] and primary is not None:
            magnitude = GATES["meaningful_beta_abs_real_pay_log_pp_per_productivity_pp"]
            if (primary["beta"] >= magnitude and adjusted[index] <= GATES["holm_alpha"]
                    and same >= GATES["minimum_same_sign_hash_folds"]):
                case["verdict"] = "SUPPORTED"
            elif (primary["beta"] <= -magnitude and adjusted[index] <= GATES["holm_alpha"]
                  and opposite >= GATES["minimum_same_sign_hash_folds"]):
                case["verdict"] = "REFUTED"
            else:
                case["verdict"] = "PARTIAL"
        output.append({"hypothesis_id": IDS[index], "family_id": FAMILY, "family_size": 3,
                       "sector": sector, "sector_label": label, "registered_direction": 1,
                       "registration_commit": registration, "source_lock_commit": commits[index],
                       "source_sha256": PDB_SHA, "secondary_source_sha256": CPI_SHA,
                       "source_key_roster_sha256": ROSTER_SHA, "run_utc": run_utc,
                       "runner": RUNNER_REL, "shared_estimator_sha256": CORE_RUNNER_SHA,
                       "thresholds": GATES, "result": case, "limitations": LIMITS,
                       "correction": {"disposition": "descriptive_calibration_only",
                                      "causal_credit": 0, "policy_score_eligible": False,
                                      "policy_score_credit": 0, "school_score_eligible": False,
                                      "school_score_credit": 0, "featured_eligible": False}})
    return output


def packet_files(diag: dict[str, Any], spec_bytes: bytes) -> dict[str, bytes]:
    hid = diag["hypothesis_id"]
    index = IDS.index(hid)
    case = diag["result"]
    source = {"publisher": "OECD Productivity Database plus World Bank WDI CPI",
              "source_sha256": PDB_SHA, "secondary_source_sha256": CPI_SHA,
              "source_lock_commit": diag["source_lock_commit"],
              "source_lock_manifest": LOCK_RELS[index], "key_roster_sha256": ROSTER_SHA,
              "input_vintages": [{"path": PDB_REL, "sha256": PDB_SHA, "manifest": PDB_MANIFEST},
                                 {"path": CPI_REL, "sha256": CPI_SHA, "manifest": CPI_MANIFEST}],
              "license": "OECD standard permissions and World Bank CC BY 4.0; attribution required",
              "contains_source_values": False}
    family = {"id": FAMILY, "size": 3, "members": list(IDS),
              "holm_alpha": GATES["holm_alpha"],
              "interpretation": "Three correlated sectors, common sources and model; not independent replication"}
    diag_bytes = js(diag)
    manifest = {"hypothesis_id": hid, "run_date": "2026-10-10",
                "status": case["verdict"], "runner": RUNNER_REL,
                "preregistration_commit": diag["registration_commit"],
                "source": source, "family": family, "correction": diag["correction"]}
    packet = {"packet_version": 1, "hypothesis": {"id": hid, "path": SPEC_RELS[index]},
              "preregistration": {"commit": diag["registration_commit"],
                                  "steelman": STEELMAN_RELS[index], "source_plan": PLAN_REL,
                                  "key_roster": ROSTER_REL},
              "source": source, "family": family,
              "reproduction": {"runner": RUNNER_REL,
                               "command": f"python3 {RUNNER_REL} verify --source-root /path/to/IESET",
                               "result_sha256": hashlib.sha256(diag_bytes).hexdigest()},
              "result": case, "limitations": LIMITS, "correction": diag["correction"]}
    primary = case["primary"] or {}
    beta = "unavailable" if not primary else f"{primary['beta']:+.5f}"
    p = "unavailable" if not primary else f"{primary['p_two_sided']:.6g}"
    card = (f"# {hid}\n\n**{case['verdict']}** in one frozen three-sector descriptive family. "
            f"Complete sample: {case['sample']['valid_rows']} country-years in "
            f"{case['sample']['valid_countries']} countries. Beta {beta} next-year real "
            f"compensation log percentage points per 1 percentage-point same-year real "
            f"value-added-per-hour growth; country-cluster two-sided p={p}, "
            f"three-test Holm p={case['holm_adjusted_p']:.6g}. "
            f"Gate failures: {case['gate_failures'] or 'none'}.\n\n"
            "OECD compensation is per employee, deflated by broad national CPI; it does not measure "
            "median pay or a causal productivity effect. One correlated family; zero causal, policy, "
            "school, position and featured credit.\n\n"
            f"Registration `{diag['registration_commit']}`; source lock `{diag['source_lock_commit']}`. "
            f"Replay: `python3 {RUNNER_REL} verify --source-root /path/to/IESET`.\n")
    replication = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
                   f"runner = Path(__file__).resolve().parents[3] / {RUNNER_REL!r}\n"
                   "raise SystemExit(subprocess.call([sys.executable, str(runner), 'verify', *sys.argv[1:]]))\n")
    return {"diagnostics.json": diag_bytes, "hypothesis.yaml": spec_bytes,
            "manifest.yaml": ya(manifest), "evidence_packet.yaml": ya(packet),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def report(diags: list[dict[str, Any]]) -> bytes:
    lines = ["# OECD PDB sector productivity to next-year real compensation — locked results", "",
             "Three sectors share the two exact sources, country roster and design. Holm adjustment covers this family only. "
             "These are descriptive calibrations with zero causal, policy, school, position and featured credit.", "",
             "| Sector | Verdict | Rows / countries | Beta | Two-sided p | Holm p | Failed gates |",
             "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for diag in diags:
        case = diag["result"]
        primary = case["primary"] or {}
        lines.append(f"| {diag['sector_label']} | {case['verdict']} | "
                     f"{case['sample']['valid_rows']} / {case['sample']['valid_countries']} | "
                     f"{primary.get('beta', 'unavailable')} | {primary.get('p_two_sided', 'unavailable')} | "
                     f"{case['holm_adjusted_p']} | {', '.join(case['gate_failures']) or 'none'} |")
    lines += ["", f"Registration `{diags[0]['registration_commit']}`; final source lock "
              f"`{diags[-1]['source_lock_commit']}`. PDB SHA-256 `{PDB_SHA}`; WDI CPI SHA-256 `{CPI_SHA}`; "
              f"frozen roster SHA-256 `{ROSTER_SHA}`.", "",
              f"Exact replay: `python3 {RUNNER_REL} verify --source-root /path/to/IESET`.", "",
              "Real compensation per employee uses OECD nominal compensation growth deflated by WDI broad CPI. "
              "Worker composition, hours, wage bargaining and sector demand can confound the relation; these "
              "results do not estimate an intervention or median wage effect. Raw and country-level values are not committed.", ""]
    return "\n".join(lines).encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "source-lock", "run", "verify"))
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--id", choices=IDS)
    args = parser.parse_args()
    pdb_path, cpi_path = source_paths(args.source_root)
    if args.command == "plan":
        print(js(key_info(pdb_path, cpi_path)).decode(), end="")
        return
    if args.command == "source-lock":
        if args.id is None:
            parser.error("--id required for source-lock")
        create_lock(pdb_path, cpi_path, args.id)
        return
    registration = registration_commit()
    commits = committed_locks(registration, pdb_path, cpi_path)
    if args.command == "run":
        if any((ROOT / relative).exists() for relative in DIAG_RELS) or (ROOT / REPORT_REL).exists():
            raise RuntimeError("family result exists; use verify")
        run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    else:
        if any(not (ROOT / relative).exists() for relative in DIAG_RELS) or not (ROOT / REPORT_REL).exists():
            raise RuntimeError("saved complete family result required for verify")
        run_utc = json.loads((ROOT / DIAG_RELS[0]).read_text())["run_utc"]
    diags = measured_results(pdb_path, cpi_path, run_utc)
    packets = {d["hypothesis_id"]: packet_files(d, (ROOT / SPEC_RELS[i]).read_bytes())
               for i, d in enumerate(diags)}
    aggregate = report(diags)
    if args.command == "run":
        for hid, files in packets.items():
            directory = ROOT / "engine/runs" / hid
            directory.mkdir(parents=True)
            for name, payload in files.items():
                (directory / name).write_bytes(payload)
        (ROOT / REPORT_REL).write_bytes(aggregate)
    else:
        run_commits = {first_add(relative) for relative in DIAG_RELS}
        if len(run_commits) != 1 or not ancestor(commits[-1], next(iter(run_commits))):
            raise RuntimeError("family result commit predates final lock or varies by cell")
        for hid, files in packets.items():
            for name, payload in files.items():
                target = ROOT / "engine/runs" / hid / name
                if not target.is_file() or target.read_bytes() != payload:
                    raise RuntimeError(f"exact replay mismatch: {target}")
        if (ROOT / REPORT_REL).read_bytes() != aggregate:
            raise RuntimeError("exact replay mismatch: aggregate audit")
    for diag in diags:
        case = diag["result"]
        print(json.dumps({"hypothesis_id": diag["hypothesis_id"],
                          "verdict": case["verdict"], "rows": case["sample"]["valid_rows"],
                          "countries": case["sample"]["valid_countries"],
                          "beta": None if case["primary"] is None else case["primary"]["beta"],
                          "holm_p": case["holm_adjusted_p"], "failed_gates": case["gate_failures"]},
                         sort_keys=True))


if __name__ == "__main__":
    main()
