#!/usr/bin/env python3
"""Prospective, source-locked OECD PDB productivity -> future employment family.

The plan and source-lock paths read source schema and categorical keys only.
Selected observations and their status/missingness are opened only by run or
verify, after one registration commit and three separate metadata-lock commits.
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

import numpy as np
import pyarrow.parquet as pq
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "oecd_pdb_sector_productivity_employment_forward_2026_10_10"
SECTORS = {
    "C": ("manufacturing", "Manufacturing", -1),
    "G": ("retail", "Wholesale and retail trade", -1),
    "J": ("ict", "Information and communication", 1),
}
IDS = tuple(f"oecd_pdb_{name}_productivity_next_year_employment_2026"
            for name, _, _ in SECTORS.values())
SOURCE_REL = "data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet"
SOURCE_SHA = "3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c"
MANIFEST_REL = "data/manifests/fetch_run_2026-05-19T095056Z.yaml"
MANIFEST_SHA = "cf2f7e75af5612b302af7fbb0479c196598aa060c20f858723108a8c95455de4"
SOURCE_URL = "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0/all?format=csvfilewithlabels"
DOC_URL = "https://data-explorer.oecd.org/vis?fs[0]=Topic&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_PDB"
RUNNER_REL = "scripts/run_oecd_pdb_sector_productivity_employment_2026.py"
PLAN_REL = "engine/audits/oecd_pdb_sector_productivity_employment_prereg_2026-10-10.md"
RESULT_REL = "engine/audits/oecd_pdb_sector_productivity_employment_results_2026-10-10.md"
ROSTER_REL = "data/pinned_evidence/oecd_pdb_sector_productivity_employment_2026_key_roster.csv"
ROSTER_SHA = "d3de10283b9e5f666aae16d407800afbd65d2a7c2f094ee825de0847bcbc3f9d"
SPEC_RELS = tuple(f"hypotheses/labour/{hid}.yaml" for hid in IDS)
STEELMAN_RELS = tuple(f"hypotheses/steelman/{hid}.md" for hid in IDS)
LOCK_RELS = tuple(f"data/pinned_evidence/{hid}.source.json" for hid in IDS)
DIAG_RELS = tuple(f"engine/runs/{hid}/diagnostics.json" for hid in IDS)
REGISTERED = SPEC_RELS + STEELMAN_RELS + (RUNNER_REL, PLAN_REL, ROSTER_REL)
OECD_CORE = set("AUS AUT BEL CAN CHE CZE DEU DNK ESP FIN FRA GBR GRC HUN IRL ISL ITA JPN KOR LUX MEX NLD NOR NZL POL PRT SVK SVN SWE TUR USA".split())
KEY_COLUMNS = ("REF_AREA", "FREQ", "MEASURE", "ACTIVITY", "UNIT_MEASURE",
               "PRICE_BASE", "TRANSFORMATION", "ASSET_CODE", "CONVERSION_TYPE", "period")
VALUE_COLUMNS = KEY_COLUMNS + ("value", "OBS_STATUS", "UNIT_MULT")
GATES = {
    "family_size": 3, "holm_alpha": 0.05,
    "meaningful_beta_abs_pp_per_productivity_pp": 0.05,
    "minimum_rows": 450, "minimum_countries": 22,
    "minimum_years_with_twelve_countries": 20,
    "minimum_complete_years_per_country": 10,
    "minimum_residual_productivity_sd_pp": 1.0,
    "minimum_residual_employment_sd_pp": 0.5,
    "maximum_country_productivity_ss_share": 0.20,
    "maximum_top_one_percent_productivity_ss_share": 0.30,
    "minimum_same_sign_hash_folds": 4,
    "minimum_fold_rows": 320, "minimum_fold_countries": 17,
    "maximum_abs_productivity_growth_pp": 50.0,
    "maximum_abs_employment_growth_log_pp": 50.0,
}
LIMITS = [
    "Three sector cells share one OECD PDB vintage, country roster and design; they are one correlated family, not independent replications.",
    "Productivity growth uses real sector value added per hour; subsequent employment growth uses persons. Higher productivity can reflect demand, hours or measurement changes rather than labor-saving technology.",
    "The prior employment growth control and country/year effects do not identify a causal productivity effect, automation effect or policy intervention.",
    "The frozen OECD core and finite +/-50 growth bounds exclude some countries and extreme sector changes; no interpolation or source substitution is permitted.",
    "Sector choices and directional priors followed visibility of the older IESET archive; Holm adjustment covers only these three frozen tests, not archive-wide selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def js(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def ya(value: Any) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode()


def git(*args: str, check: bool = True) -> bytes:
    proc = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if check and proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace')}")
    return proc.stdout if proc.returncode == 0 else b""


def first_add(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}: {commits}")
    return commits[0]


def strict_ancestor(earlier: str, later: str) -> bool:
    return earlier != later and subprocess.run(
        ["git", "merge-base", "--is-ancestor", earlier, later], cwd=ROOT,
        capture_output=True).returncode == 0


def verify_frozen(relative: str, revision: str) -> None:
    if (ROOT / relative).read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"registered file changed: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"registered file has uncommitted changes: {relative}")


def registration_commit() -> str:
    commits = {first_add(path) for path in REGISTERED}
    if len(commits) != 1:
        raise RuntimeError(f"registration files must share first commit: {commits}")
    commit = commits.pop()
    for relative in REGISTERED:
        verify_frozen(relative, commit)
    if sha256(ROOT / ROSTER_REL) != ROSTER_SHA:
        raise RuntimeError("registered key roster hash mismatch")
    if git("ls-tree", "-r", "--name-only", commit, "--", *LOCK_RELS, *DIAG_RELS).strip():
        raise RuntimeError("registration commit contained source lock or measured result")
    schema = json.loads(git("show", f"{commit}:schemas/hypothesis.schema.json"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for relative in SPEC_RELS:
        if not validator.is_valid(yaml.safe_load((ROOT / relative).read_bytes())):
            raise RuntimeError(f"frozen first spec is schema-invalid: {relative}")
    return commit


def source_path(source_root: Path) -> Path:
    path = source_root / SOURCE_REL
    if not path.is_file() or sha256(path) != SOURCE_SHA:
        raise RuntimeError("pinned OECD PDB source absent or hash mismatch")
    manifest = ROOT / MANIFEST_REL
    if not manifest.is_file() or sha256(manifest) != MANIFEST_SHA:
        raise RuntimeError("pinned OECD fetch manifest absent or hash mismatch")
    entries = yaml.safe_load(manifest.read_text()).get("entries", [])
    matched = [entry for entry in entries if entry.get("publisher") == "oecd"
               and entry.get("series_id") == "DSD_PDB"
               and entry.get("parquet_path") == SOURCE_REL
               and entry.get("sha256") == SOURCE_SHA]
    if len(matched) != 1:
        raise RuntimeError("no exact OECD source/fetch-manifest entry")
    cols = set(pq.ParquetFile(path).schema_arrow.names)
    if not set(VALUE_COLUMNS).issubset(cols):
        raise RuntimeError(f"OECD source lacks frozen columns: {sorted(set(VALUE_COLUMNS) - cols)}")
    return path


def key_sets(path: Path) -> tuple[set[tuple[str, str, int]], set[tuple[str, str, int]]]:
    """Inspect categorical identities and time keys; do not open value/status/null masks."""
    table = pq.read_table(path, columns=list(KEY_COLUMNS)).to_pandas()
    common = (table.FREQ.eq("A") & table.ACTIVITY.isin(SECTORS)
              & table.REF_AREA.isin(OECD_CORE) & table.ASSET_CODE.eq("_Z")
              & table.CONVERSION_TYPE.eq("_Z"))
    productivity = table[common & table.MEASURE.eq("GVAHRS")
                         & table.UNIT_MEASURE.eq("XDC_H")
                         & table.PRICE_BASE.eq("LR")
                         & table.TRANSFORMATION.eq("GY")]
    employment = table[common & table.MEASURE.eq("EMP")
                       & table.UNIT_MEASURE.eq("PS")
                       & table.PRICE_BASE.eq("_Z")
                       & table.TRANSFORMATION.eq("N")]
    def keys(frame: Any) -> set[tuple[str, str, int]]:
        rows = [(str(s), str(c), int(y)) for s, c, y in zip(
            frame.ACTIVITY, frame.REF_AREA, frame.period)]
        if len(rows) != len(set(rows)):
            raise RuntimeError("duplicate selected OECD series key")
        return set(rows)
    return keys(productivity), keys(employment)


def roster_bytes(path: Path) -> bytes:
    productivity, employment = key_sets(path)
    rows = sorted((s, c, t) for s, c, t in productivity
                  if 1996 <= t <= 2023
                  and all((s, c, year) in employment for year in (t - 1, t, t + 1)))
    f = io.StringIO()
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(("sector", "country_iso3", "treatment_year"))
    writer.writerows(rows)
    return f.getvalue().encode()


def source_key_info(path: Path) -> dict[str, Any]:
    expected = roster_bytes(path)
    if hashlib.sha256(expected).hexdigest() != ROSTER_SHA:
        raise RuntimeError("pinned OECD key roster changed")
    if not (ROOT / ROSTER_REL).is_file() or (ROOT / ROSTER_REL).read_bytes() != expected:
        raise RuntimeError("registered key roster differs from source keys")
    rows = list(csv.DictReader(io.StringIO(expected.decode())))
    return {"key_roster_sha256": ROSTER_SHA, "source_key_rows": len(rows),
            "source_key_rows_per_sector": {s: sum(r["sector"] == s for r in rows)
                                           for s in SECTORS},
            "selected_schema": {name: str(pq.ParquetFile(path).schema_arrow.field(name).type)
                                for name in VALUE_COLUMNS}}


def create_lock(path: Path, hypothesis_id: str) -> None:
    registration = registration_commit()
    index = IDS.index(hypothesis_id)
    previous = registration if index == 0 else first_add(LOCK_RELS[index - 1])
    if git("rev-parse", "HEAD").decode().strip() != previous:
        raise RuntimeError("source locks must be generated and committed in sector order")
    relative = LOCK_RELS[index]
    if (ROOT / relative).exists():
        raise RuntimeError(f"source lock already exists: {relative}")
    info = source_key_info(path)
    lock = {"hypothesis_id": hypothesis_id, "family_id": FAMILY, "family_size": 3,
            "registration_commit": registration, "publisher": "OECD Productivity Database",
            "dataflow": "OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0", "source_url": SOURCE_URL,
            "documentation_url": DOC_URL, "license": "OECD standard permissions; attribution required",
            "source_path": SOURCE_REL, "source_sha256": SOURCE_SHA,
            "source_bytes": path.stat().st_size,
            "fetch_manifest": MANIFEST_REL, "fetch_manifest_sha256": MANIFEST_SHA,
            "key_roster_sha256": ROSTER_SHA,
            "selected_values_or_status_read": False, **info}
    target = ROOT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(js(lock))
    print(json.dumps({"lock": relative, "registration_commit": registration,
                      "key_rows": info["source_key_rows"]}, sort_keys=True))


def committed_locks(registration: str, path: Path) -> tuple[list[str], dict[str, Any]]:
    info = source_key_info(path)
    commits: list[str] = []
    for index, relative in enumerate(LOCK_RELS):
        revision = first_add(relative)
        previous = registration if index == 0 else commits[-1]
        if not strict_ancestor(previous, revision):
            raise RuntimeError("source-lock chronology failed")
        changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", revision).decode().splitlines()
        if changed != [relative]:
            raise RuntimeError(f"source lock commit must contain exactly one file: {relative}")
        verify_frozen(relative, revision)
        lock = json.loads((ROOT / relative).read_text())
        expected = {"hypothesis_id": IDS[index], "family_id": FAMILY, "family_size": 3,
                    "registration_commit": registration, "source_sha256": SOURCE_SHA,
                    "key_roster_sha256": ROSTER_SHA, **info}
        if any(lock.get(k) != v for k, v in expected.items()):
            raise RuntimeError(f"source lock identity or source key mismatch: {relative}")
        commits.append(revision)
    if git("ls-tree", "-r", "--name-only", commits[-1], "--", *DIAG_RELS).strip():
        raise RuntimeError("measured result predates final source lock")
    return commits, info


def selected_rows(path: Path) -> dict[tuple[str, str, int, str], tuple[Any, Any, Any]]:
    """Only reached after all registered metadata locks have been committed."""
    table = pq.read_table(path, columns=list(VALUE_COLUMNS)).to_pandas()
    common = (table.FREQ.eq("A") & table.ACTIVITY.isin(SECTORS)
              & table.REF_AREA.isin(OECD_CORE) & table.ASSET_CODE.eq("_Z")
              & table.CONVERSION_TYPE.eq("_Z"))
    prod = table[common & table.MEASURE.eq("GVAHRS")
                 & table.UNIT_MEASURE.eq("XDC_H") & table.PRICE_BASE.eq("LR")
                 & table.TRANSFORMATION.eq("GY")].copy()
    emp = table[common & table.MEASURE.eq("EMP")
                & table.UNIT_MEASURE.eq("PS") & table.PRICE_BASE.eq("_Z")
                & table.TRANSFORMATION.eq("N")].copy()
    out: dict[tuple[str, str, int, str], tuple[Any, Any, Any]] = {}
    for role, frame in (("productivity", prod), ("employment", emp)):
        for row in frame.itertuples(index=False):
            key = (str(row.ACTIVITY), str(row.REF_AREA), int(row.period), role)
            if key in out:
                raise RuntimeError("duplicate selected OECD value key")
            out[key] = (row.value, row.OBS_STATUS, row.UNIT_MULT)
    return out


def admissible(cell: tuple[Any, Any, Any] | None, *, growth: bool) -> float | None:
    if cell is None:
        return None
    value, status, multiplier = cell
    if status is not None and str(status) not in ("", "A", "nan", "None"):
        return None
    try:
        number = float(value)
        power = 0 if multiplier is None or str(multiplier) in ("", "nan", "None") else float(multiplier)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number) or not math.isfinite(power) or power != int(power) or abs(power) > 9:
        return None
    if growth:
        return number if power == 0 and abs(number) <= GATES["maximum_abs_productivity_growth_pp"] else None
    actual = number * (10.0 ** int(power))
    return actual if math.isfinite(actual) and actual > 0 else None


def panel(source: dict[tuple[str, str, int, str], tuple[Any, Any, Any]],
          sector: str) -> tuple[list[tuple[str, int, float, float, float]], dict[str, Any]]:
    roster = list(csv.DictReader((ROOT / ROSTER_REL).open(newline="")))
    candidate = [r for r in roster if r["sector"] == sector]
    complete: list[tuple[str, int, float, float, float]] = []
    dropped: Counter[str] = Counter()
    for item in candidate:
        country, year = item["country_iso3"], int(item["treatment_year"])
        x = admissible(source.get((sector, country, year, "productivity")), growth=True)
        if x is None:
            dropped["missing_or_invalid_productivity"] += 1
            continue
        ends = [admissible(source.get((sector, country, y, "employment")), growth=False)
                for y in (year - 1, year, year + 1)]
        if any(v is None for v in ends):
            dropped["missing_or_invalid_employment_level"] += 1
            continue
        e_prev, e_now, e_next = ends
        prior, future = 100.0 * math.log(e_now/e_prev), 100.0 * math.log(e_next/e_now)
        if abs(prior) > GATES["maximum_abs_employment_growth_log_pp"] or abs(future) > GATES["maximum_abs_employment_growth_log_pp"]:
            dropped["employment_growth_out_of_range"] += 1
            continue
        complete.append((country, year, x, future, prior))
    counts = Counter(row[0] for row in complete)
    rows = [row for row in complete if counts[row[0]] >= GATES["minimum_complete_years_per_country"]]
    dropped["country_below_ten_year_floor"] = len(complete) - len(rows)
    year_counts = Counter(row[1] for row in rows)
    sample = {"key_roster_rows": len(candidate), "key_roster_countries": len({r["country_iso3"] for r in candidate}),
              "complete_rows_before_country_floor": len(complete),
              "valid_rows": len(rows), "valid_countries": len({r[0] for r in rows}),
              "years_with_twelve_countries": sum(v >= 12 for v in year_counts.values()),
              "treatment_year_min": min((r[1] for r in rows), default=None),
              "treatment_year_max": max((r[1] for r in rows), default=None),
              "dropped": dict(sorted(dropped.items())),
              "selected_values_read_after_committed_locks": True}
    return sorted(rows), sample


def fit(rows: list[tuple[str, int, float, float, float]], *, full: bool = True) -> dict[str, Any] | None:
    countries = sorted({r[0] for r in rows})
    years = sorted({r[1] for r in rows})
    n = len(rows)
    fixed = np.ones((n, 1 + len(countries) - 1 + len(years) - 1 + 1))
    for i, (country, year, _, _, prior) in enumerate(rows):
        fixed[i, 1:len(countries)] = [float(country == c) for c in countries[1:]]
        fixed[i, len(countries):len(countries)+len(years)-1] = [float(year == t) for t in years[1:]]
        fixed[i, -1] = prior
    x = np.array([r[2] for r in rows], dtype=float)
    y = np.array([r[3] for r in rows], dtype=float)
    design = np.column_stack((fixed[:, 0], x, fixed[:, 1:]))
    k = design.shape[1]
    if n <= k or np.linalg.matrix_rank(design) != k:
        return None
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    out: dict[str, Any] = {"beta": float(beta[1]), "n_rows": n, "n_countries": len(countries),
                           "model_rank": k, "model_columns": k}
    if not full:
        return out
    x_resid = x - fixed @ np.linalg.lstsq(fixed, x, rcond=None)[0]
    y_resid = y - fixed @ np.linalg.lstsq(fixed, y, rcond=None)[0]
    x_ss = float(x_resid @ x_resid)
    if x_ss <= 1e-12:
        return None
    country_ss = [float(x_resid[[r[0] == c for r in rows]] @ x_resid[[r[0] == c for r in rows]]) / x_ss
                  for c in countries]
    top = max(1, math.ceil(n * .01))
    residual = y - design @ beta
    inv = np.linalg.inv(design.T @ design)
    meat = np.zeros((k, k), dtype=float)
    for country in countries:
        ix = np.array([r[0] == country for r in rows])
        score = design[ix].T @ residual[ix]
        meat += np.outer(score, score)
    g = len(countries)
    variance = float((g/(g-1)) * ((n-1)/(n-k)) * (inv @ meat @ inv)[1,1])
    if not math.isfinite(variance) or variance <= 0:
        return None
    se = math.sqrt(variance)
    p = float(2 * student_t.sf(abs(out["beta"] / se), g - 1))
    out.update({"country_cluster_se": se, "p_two_sided": p,
                "df_inference": g - 1,
                "residual_productivity_sd_pp": float(np.std(x_resid, ddof=1)),
                "residual_employment_sd_pp": float(np.std(y_resid, ddof=1)),
                "maximum_country_productivity_ss_share": max(country_ss),
                "top_one_percent_productivity_ss_share": float(np.sort(x_resid**2)[-top:].sum() / x_ss),
                "method": "equal-row country/year FE OLS with prior employment growth; country CR1 cluster t(G-1)"})
    return out


def fold(country: str) -> int:
    return int(hashlib.sha256(country.encode()).hexdigest()[:8], 16) % 5


def evaluate(source: dict[tuple[str, str, int, str], tuple[Any, Any, Any]], sector: str) -> dict[str, Any]:
    rows, sample = panel(source, sector)
    failures = []
    if sample["valid_rows"] < GATES["minimum_rows"]:
        failures.append("row_floor")
    if sample["valid_countries"] < GATES["minimum_countries"]:
        failures.append("country_floor")
    if sample["years_with_twelve_countries"] < GATES["minimum_years_with_twelve_countries"]:
        failures.append("year_coverage_floor")
    primary = fit(rows) if rows else None
    if primary is None:
        failures.append("primary_estimator_or_rank_failure")
    else:
        for key, limit, small in (
            ("residual_productivity_sd_pp", GATES["minimum_residual_productivity_sd_pp"], True),
            ("residual_employment_sd_pp", GATES["minimum_residual_employment_sd_pp"], True),
            ("maximum_country_productivity_ss_share", GATES["maximum_country_productivity_ss_share"], False),
            ("top_one_percent_productivity_ss_share", GATES["maximum_top_one_percent_productivity_ss_share"], False),
        ):
            value = primary[key]
            if not math.isfinite(value) or (value < limit if small else value > limit):
                failures.append(key + "_gate")
    folds = []
    for omitted in range(5):
        part = [row for row in rows if fold(row[0]) != omitted]
        record: dict[str, Any] = {"omitted_hash_fold": omitted, "rows": len(part),
                                  "countries": len({r[0] for r in part})}
        if record["rows"] < GATES["minimum_fold_rows"] or record["countries"] < GATES["minimum_fold_countries"]:
            failures.append(f"fold_{omitted}_sample_floor")
        estimate = fit(part, full=False) if part else None
        if estimate is None or not math.isfinite(estimate["beta"]):
            failures.append(f"fold_{omitted}_estimator_failure")
        else:
            record["beta"] = estimate["beta"]
        folds.append(record)
    return {"sample": sample, "primary": primary, "hash_folds": folds,
            "gate_failures": sorted(set(failures)), "verdict": "INCONCLUSIVE",
            "holm_adjusted_p": None, "same_direction_folds": None}


def holm_adjusted(values: list[float | None]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda i: 1.0 if values[i] is None else values[i])
    adjusted = [1.0] * len(values)
    running = 0.0
    for rank, i in enumerate(ordered):
        p = 1.0 if values[i] is None else values[i]
        running = max(running, min(1.0, (len(values) - rank) * p))
        adjusted[i] = running
    return adjusted


def measured_results(path: Path, run_utc: str) -> list[dict[str, Any]]:
    registration = registration_commit()
    lock_commits, _ = committed_locks(registration, path)
    source = selected_rows(path)
    cases = [evaluate(source, sector) for sector in SECTORS]
    adjusted = holm_adjusted([
        case["primary"]["p_two_sided"] if not case["gate_failures"] and case["primary"] else None
        for case in cases])
    output = []
    for index, ((sector, (name, label, direction)), case) in enumerate(zip(SECTORS.items(), cases)):
        primary = case["primary"]
        if primary is not None:
            signs = sum(math.copysign(1, item["beta"]) == direction
                        for item in case["hash_folds"] if "beta" in item)
            opposite = sum(math.copysign(1, item["beta"]) == -direction
                           for item in case["hash_folds"] if "beta" in item)
        else:
            signs = opposite = 0
        case["same_direction_folds"] = signs
        case["opposite_direction_folds"] = opposite
        case["holm_adjusted_p"] = adjusted[index]
        if not case["gate_failures"] and primary is not None:
            magnitude = GATES["meaningful_beta_abs_pp_per_productivity_pp"]
            if (direction * primary["beta"] >= magnitude and adjusted[index] <= GATES["holm_alpha"]
                    and signs >= GATES["minimum_same_sign_hash_folds"]):
                case["verdict"] = "SUPPORTED"
            elif (-direction * primary["beta"] >= magnitude and adjusted[index] <= GATES["holm_alpha"]
                  and opposite >= GATES["minimum_same_sign_hash_folds"]):
                case["verdict"] = "REFUTED"
            else:
                case["verdict"] = "PARTIAL"
        output.append({"hypothesis_id": IDS[index], "family_id": FAMILY, "family_size": 3,
                       "sector": sector, "sector_label": label, "registered_direction": direction,
                       "registration_commit": registration, "source_lock_commit": lock_commits[index],
                       "source_sha256": SOURCE_SHA, "source_key_roster_sha256": ROSTER_SHA,
                       "run_utc": run_utc, "runner": RUNNER_REL, "thresholds": GATES,
                       "result": case, "limitations": LIMITS,
                       "correction": {"disposition": "descriptive_calibration_only", "causal_credit": 0,
                                      "policy_score_eligible": False, "policy_score_credit": 0,
                                      "school_score_eligible": False, "school_score_credit": 0,
                                      "featured_eligible": False}})
    return output


def packet_files(diag: dict[str, Any], spec_bytes: bytes) -> dict[str, bytes]:
    hid = diag["hypothesis_id"]
    index = IDS.index(hid)
    case = diag["result"]
    verdict = case["verdict"]
    source = {"publisher": "OECD Productivity Database", "dataflow": "OECD.SDD.TPS,DSD_PDB@DF_PDB,2.0",
              "source_url": SOURCE_URL, "documentation_url": DOC_URL,
              "source_sha256": SOURCE_SHA, "source_lock_commit": diag["source_lock_commit"],
              "source_lock_manifest": LOCK_RELS[index], "fetch_manifest": MANIFEST_REL,
              "key_roster_sha256": ROSTER_SHA, "license": "OECD standard permissions; attribution required",
              "contains_source_values": False}
    family = {"id": FAMILY, "size": 3, "members": list(IDS), "holm_alpha": GATES["holm_alpha"],
              "interpretation": "Three correlated OECD sector cells, one vintage and one design; not independent replication"}
    diag_bytes = js(diag)
    manifest = {"hypothesis_id": hid, "run_date": "2026-10-10", "status": verdict,
                "runner": RUNNER_REL, "preregistration_commit": diag["registration_commit"],
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
    card = (f"# {hid}\n\n**{verdict}** in the frozen three-sector OECD PDB family. "
            f"The registered directional claim is {'negative' if diag['registered_direction'] < 0 else 'positive'} "
            f"for {diag['sector_label']}.\n\n"
            f"Complete panel: {case['sample']['valid_rows']} country-years in "
            f"{case['sample']['valid_countries']} countries. Beta {beta} next-year employment "
            f"log percentage points per 1 percentage-point same-year real value-added-per-hour growth; "
            f"country-cluster two-sided p={p}, three-test Holm p={case['holm_adjusted_p']:.6g}. "
            f"Gate failures: {case['gate_failures'] or 'none'}.\n\n"
            "The outcome follows the productivity measure by one year and controls prior employment growth. "
            "Sector demand, hours and selection remain confounders. One correlated descriptive family; "
            "no causal, policy, school, position or featured credit.\n\n"
            f"Registration `{diag['registration_commit']}`; source lock `{diag['source_lock_commit']}`. "
            f"Replay: `python3 {RUNNER_REL} verify --source-root /path/to/IESET`.\n")
    replication = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
                   f"runner = Path(__file__).resolve().parents[3] / {RUNNER_REL!r}\n"
                   "raise SystemExit(subprocess.call([sys.executable, str(runner), 'verify', *sys.argv[1:]]))\n")
    return {"diagnostics.json": diag_bytes, "hypothesis.yaml": spec_bytes,
            "manifest.yaml": ya(manifest), "evidence_packet.yaml": ya(packet),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def result_report(diags: list[dict[str, Any]]) -> bytes:
    lines = ["# OECD PDB sector productivity to next-year employment — locked results", "",
             "Three cells share one source, roster and model. Their Holm adjustment applies only to this frozen family. "
             "All results are descriptive calibration with zero causal, policy, school, position and featured credit.", "",
             "| Sector | Verdict | Rows / countries | Beta | Two-sided p | Holm p | Failed gates |",
             "| --- | --- | ---: | ---: | ---: | ---: | --- |"]
    for d in diags:
        r = d["result"]
        p = r["primary"] or {}
        lines.append(f"| {d['sector_label']} | {r['verdict']} | {r['sample']['valid_rows']} / {r['sample']['valid_countries']} | "
                     f"{p.get('beta', 'unavailable')} | {p.get('p_two_sided', 'unavailable')} | "
                     f"{r['holm_adjusted_p']} | {', '.join(r['gate_failures']) or 'none'} |")
    lines += ["", f"Registration `{diags[0]['registration_commit']}`. "
              f"Final source-lock commit `{diags[-1]['source_lock_commit']}`. "
              f"Source SHA-256 `{SOURCE_SHA}`; frozen roster SHA-256 `{ROSTER_SHA}`.", "",
              "Exact replay: `python3 scripts/run_oecd_pdb_sector_productivity_employment_2026.py verify --source-root /path/to/IESET`.", "",
              "OECD PDB growth-rate and employment series are not intervention measures. The registered signs test sector-displacement "
              "versus expansion patterns, not causal automation or labor-policy effects. OECD standard permissions require attribution; "
              "raw and country-level values are not committed.", ""]
    return "\n".join(lines).encode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "source-lock", "run", "verify"))
    parser.add_argument("--source-root", type=Path, default=ROOT)
    parser.add_argument("--id", choices=IDS)
    args = parser.parse_args()
    path = source_path(args.source_root)
    if args.command == "plan":
        info = source_key_info(path)
        print(js(info).decode(), end="")
        return
    if args.command == "source-lock":
        if args.id is None:
            parser.error("--id required for source-lock")
        create_lock(path, args.id)
        return
    registration = registration_commit()
    lock_commits, _ = committed_locks(registration, path)
    if args.command == "run":
        if any((ROOT / relative).exists() for relative in DIAG_RELS) or (ROOT / RESULT_REL).exists():
            raise RuntimeError("result already exists; use verify")
        run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    else:
        if any(not (ROOT / relative).exists() for relative in DIAG_RELS) or not (ROOT / RESULT_REL).exists():
            raise RuntimeError("saved complete family result required for verify")
        prior = json.loads((ROOT / DIAG_RELS[0]).read_text())
        run_utc = prior["run_utc"]
    diags = measured_results(path, run_utc)
    packets = {d["hypothesis_id"]: packet_files(d, (ROOT / SPEC_RELS[i]).read_bytes())
               for i, d in enumerate(diags)}
    report = result_report(diags)
    if args.command == "run":
        for hid, files in packets.items():
            target = ROOT / "engine/runs" / hid
            target.mkdir(parents=True)
            for name, payload in files.items():
                (target / name).write_bytes(payload)
        (ROOT / RESULT_REL).write_bytes(report)
    else:
        run_commits = {first_add(relative) for relative in DIAG_RELS}
        if len(run_commits) != 1 or not strict_ancestor(lock_commits[-1], next(iter(run_commits))):
            raise RuntimeError("family result commit predates final lock or differs across cells")
        for hid, files in packets.items():
            for name, payload in files.items():
                target = ROOT / "engine/runs" / hid / name
                if not target.is_file() or target.read_bytes() != payload:
                    raise RuntimeError(f"exact replay mismatch: {target}")
        if (ROOT / RESULT_REL).read_bytes() != report:
            raise RuntimeError("exact replay mismatch: result audit")
    for d in diags:
        r = d["result"]
        print(json.dumps({"hypothesis_id": d["hypothesis_id"], "verdict": r["verdict"],
                          "rows": r["sample"]["valid_rows"], "countries": r["sample"]["valid_countries"],
                          "beta": None if r["primary"] is None else r["primary"]["beta"],
                          "holm_p": r["holm_adjusted_p"], "failed_gates": r["gate_failures"]}, sort_keys=True))


if __name__ == "__main__":
    main()
