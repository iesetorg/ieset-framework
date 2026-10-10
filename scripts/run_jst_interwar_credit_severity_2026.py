#!/usr/bin/env python3
"""Prospectively locked two-outcome JST interwar credit-intensity calibration.

plan/source-lock read only country/year keys and Parquet schema. run/verify read
selected values only after two immutable metadata locks were committed.
No country-level source values are written into the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import subprocess
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "jst_interwar_credit_intensity_real_price_losses_2026_10_10"
IDS = (
    "jst_1929_credit_intensity_real_gdp_pc_loss_v2",
    "jst_1929_credit_intensity_cpi_deflation_v2",
)
TOPICS = ("growth", "monetary")
FIELDS = ("rgdpmad", "cpi")
COUNTRIES = ("AUS", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
             "GBR", "IRL", "ITA", "JPN", "NLD", "NOR", "PRT", "SWE", "USA")
YEARS = (1929, 1933)
SOURCE_COLUMNS = ("country_iso3", "year", "tloans", "gdp", "rgdpmad", "cpi")
SOURCE_BASENAME = "jst_macrohistory@2026-05-05T195309Z.parquet"
SOURCE_DEFAULT = ROOT / "data/vintages/jst" / SOURCE_BASENAME
SOURCE_SHA256 = "4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f"
SOURCE_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
DOC_URL = "https://www.macrohistory.net/database/"
PLAN_REL = "engine/audits/jst_interwar_credit_severity_source_plan_2026.md"
RUNNER_REL = "scripts/run_jst_interwar_credit_severity_2026.py"
SPEC_RELS = tuple(f"hypotheses/{topic}/{hid}.yaml" for topic, hid in zip(TOPICS, IDS))
STEELMAN_RELS = tuple(f"hypotheses/steelman/{hid}.md" for hid in IDS)
LOCK_RELS = tuple(f"data/pinned_evidence/{hid}.source.json" for hid in IDS)
RESULT_RELS = tuple(f"engine/runs/{hid}/diagnostics.json" for hid in IDS)
REGISTRATION_FILES = SPEC_RELS + STEELMAN_RELS + (PLAN_REL, RUNNER_REL)
EXPECTED_KEYS = {(country, year) for country in COUNTRIES for year in YEARS}
FLOORS = {
    "minimum_common_complete_countries": 12,
    "minimum_credit_intensity_spread_pp": 20.0,
    "minimum_outcome_loss_spread_log_pp": 5.0,
    "family_size": 2,
    "bonferroni_two_sided_p_max_each": 0.025,
    "permutations_each": 99999,
    "support_rho_min": 0.4,
    "refute_rho_max": -0.4,
}
assert len(EXPECTED_KEYS) == 36


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and process.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {process.stderr.decode(errors='replace').strip()}")
    return process


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).stdout.decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}, found {len(commits)}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registration_commit() -> str:
    commits = {first_addition(path) for path in REGISTRATION_FILES}
    if len(commits) != 1:
        raise RuntimeError("two specs, steelmans, plan, and runner were not registered together")
    commit = commits.pop()
    for path in REGISTRATION_FILES:
        if git_bytes(commit, path) != (ROOT / path).read_bytes():
            raise RuntimeError(f"frozen registration changed after first commit: {path}")
    if git("ls-tree", "-r", "--name-only", commit, "--", *LOCK_RELS, *RESULT_RELS).stdout.strip():
        raise RuntimeError("source lock or result appeared in registration commit")
    return commit


def source_check(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError("local JST R6 source unavailable")
    if sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("JST R6 source SHA-256 mismatch")
    schema = pq.ParquetFile(path).schema_arrow
    missing = set(SOURCE_COLUMNS) - set(schema.names)
    if missing:
        raise RuntimeError(f"JST source missing frozen columns: {sorted(missing)}")
    return {column: str(schema.field(column).type) for column in SOURCE_COLUMNS}


def source_key_check(path: Path) -> dict[str, Any]:
    """Read only country/year keys; do not open selected values or null masks."""
    schema = source_check(path)
    table = pq.read_table(path, columns=["country_iso3", "year"])
    selected = [(str(c), int(y)) for c, y in zip(table["country_iso3"].to_pylist(), table["year"].to_pylist())
                if c in COUNTRIES and y in YEARS]
    if len(selected) != len(EXPECTED_KEYS) or set(selected) != EXPECTED_KEYS or len(set(selected)) != len(selected):
        raise RuntimeError("fixed 18-country x two-year JST key roster missing, duplicated, or changed")
    roster = "".join(f"{c},{y}\n" for c, y in sorted(selected)).encode()
    return {
        "selected_key_count": len(selected),
        "key_roster_sha256": hashlib.sha256(roster).hexdigest(),
        "selected_schema": schema,
    }


def write_lock(path: Path, hypothesis_id: str) -> None:
    registration = registration_commit()
    index = IDS.index(hypothesis_id)
    lock_path = ROOT / LOCK_RELS[index]
    if lock_path.exists():
        raise RuntimeError("source lock already exists; never overwrite")
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    if index == 0 and head != registration:
        raise RuntimeError("first source lock must follow registration directly")
    if index == 1 and head != first_addition(LOCK_RELS[0]):
        raise RuntimeError("second source lock must follow first source lock directly")
    info = source_key_check(path)
    lock = {
        "hypothesis_id": hypothesis_id,
        "family_id": FAMILY,
        "family_size": 2,
        "registration_commit": registration,
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database",
        "release": "R6",
        "official_source_url": SOURCE_URL,
        "documentation_url": DOC_URL,
        "citation": "Jordà, Schularick and Taylor (2017), Macrofinancial History and the New Business Cycle Facts",
        "license": "CC BY-NC-SA 4.0; no source or country-level values committed",
        "source_basename": SOURCE_BASENAME,
        "source_sha256": SOURCE_SHA256,
        "source_bytes": path.stat().st_size,
        "fetch_manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "countries": list(COUNTRIES),
        "years": list(YEARS),
        **info,
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(canonical_json(lock))
    print(json.dumps({"source_lock": LOCK_RELS[index], "registration_commit": registration,
                      "key_roster_sha256": info["key_roster_sha256"]}, sort_keys=True))


def committed_locks(registration: str, path: Path) -> tuple[list[str], dict[str, Any]]:
    info = source_key_check(path)
    commits = []
    for index, relative in enumerate(LOCK_RELS):
        local = ROOT / relative
        if not local.is_file():
            raise RuntimeError(f"missing committed source lock: {relative}")
        commit = first_addition(relative)
        if not strict_ancestor(registration, commit):
            raise RuntimeError("source lock precedes registration")
        if index and not strict_ancestor(commits[0], commit):
            raise RuntimeError("family source locks not in frozen order")
        if git_bytes(commit, relative) != local.read_bytes():
            raise RuntimeError(f"source lock changed after commit: {relative}")
        if git("ls-tree", "-r", "--name-only", commit, "--", *RESULT_RELS).stdout.strip():
            raise RuntimeError("result appeared in source-lock commit")
        lock = json.loads(local.read_text())
        if (lock.get("hypothesis_id") != IDS[index]
                or lock.get("family_id") != FAMILY
                or lock.get("family_size") != 2
                or lock.get("registration_commit") != registration
                or lock.get("source_sha256") != SOURCE_SHA256):
            raise RuntimeError("source lock identity mismatch")
        for key in ("selected_key_count", "key_roster_sha256", "selected_schema"):
            if lock.get(key) != info[key]:
                raise RuntimeError(f"selected source metadata changed: {key}")
        commits.append(commit)
    return commits, info


def selected_values(path: Path) -> list[tuple[float, float, float]]:
    """Only called after registration and both committed source locks validate."""
    table = pq.read_table(path, columns=list(SOURCE_COLUMNS))
    rows: dict[tuple[str, int], tuple[Any, ...]] = {}
    columns = [table[name].to_pylist() for name in SOURCE_COLUMNS]
    for c, year, loans, gdp, real_pc, cpi in zip(*columns):
        if c in COUNTRIES and year in YEARS:
            key = (str(c), int(year))
            if key in rows:
                raise RuntimeError("duplicate selected JST country-year")
            rows[key] = (loans, gdp, real_pc, cpi)
    if set(rows) != EXPECTED_KEYS:
        raise RuntimeError("selected JST source-key roster changed")
    selected = []
    for country in COUNTRIES:
        loans, gdp, real_1929, cpi_1929 = rows[(country, 1929)]
        _, _, real_1933, cpi_1933 = rows[(country, 1933)]
        values = (loans, gdp, real_1929, real_1933, cpi_1929, cpi_1933)
        if any(value is None or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0
               for value in values):
            continue
        x = 100.0 * float(loans) / float(gdp)
        real_loss = -100.0 * math.log(float(real_1933) / float(real_1929))
        price_loss = -100.0 * math.log(float(cpi_1933) / float(cpi_1929))
        if not all(math.isfinite(v) for v in (x, real_loss, price_loss)):
            continue
        selected.append((x, real_loss, price_loss))
    return selected


def average_ranks(values: list[float]) -> list[float]:
    ordered = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        average = (start + 1 + end) / 2.0
        for position in range(start, end):
            ranks[ordered[position]] = average
        start = end
    return ranks


def pearson(x: list[float], y: list[float]) -> float:
    mx, my = sum(x) / len(x), sum(y) / len(y)
    xx = sum((a - mx) ** 2 for a in x)
    yy = sum((b - my) ** 2 for b in y)
    if xx <= 0 or yy <= 0:
        return float("nan")
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / math.sqrt(xx * yy)


def rank_rho(x: list[float], y: list[float]) -> float:
    return pearson(average_ranks(x), average_ranks(y))


def permutation_p(x: list[float], y: list[float], seed: int) -> float:
    rx, ry = average_ranks(x), average_ranks(y)
    observed = abs(pearson(rx, ry))
    rng = random.Random(seed)
    count = 0
    for _ in range(FLOORS["permutations_each"]):
        permuted = list(ry)
        rng.shuffle(permuted)
        if abs(pearson(rx, permuted)) >= observed - 1e-12:
            count += 1
    return (count + 1) / (FLOORS["permutations_each"] + 1)


def evaluate(rows: list[tuple[float, float, float]], index: int) -> dict[str, Any]:
    x = [row[0] for row in rows]
    y = [row[index + 1] for row in rows]
    n = len(rows)
    x_spread = max(x) - min(x) if x else None
    y_spread = max(y) - min(y) if y else None
    failures = []
    if n < FLOORS["minimum_common_complete_countries"]:
        failures.append("common_complete_country_floor")
    if x_spread is None or x_spread < FLOORS["minimum_credit_intensity_spread_pp"]:
        failures.append("credit_intensity_spread_floor")
    if y_spread is None or y_spread < FLOORS["minimum_outcome_loss_spread_log_pp"]:
        failures.append("outcome_loss_spread_floor")
    if failures:
        return {
            "verdict": "INCONCLUSIVE", "gate_failures": failures,
            "common_complete_countries": n, "excluded_countries": len(COUNTRIES) - n,
            "credit_intensity_spread_pp": x_spread, "outcome_loss_spread_log_pp": y_spread,
            "spearman_rho": None, "permutation_p_two_sided": None,
            "leave_one_out_rho_min": None, "leave_one_out_rho_max": None,
        }
    rho = rank_rho(x, y)
    p = permutation_p(x, y, 20261010 + index)
    loo = [rank_rho(x[:i] + x[i + 1:], y[:i] + y[i + 1:]) for i in range(n)]
    if not all(math.isfinite(value) for value in (rho, p, *loo)):
        raise RuntimeError("non-finite rank statistic after variation gates")
    if rho >= FLOORS["support_rho_min"] and p <= FLOORS["bonferroni_two_sided_p_max_each"] and min(loo) > 0:
        verdict = "SUPPORTED"
    elif rho <= FLOORS["refute_rho_max"] and p <= FLOORS["bonferroni_two_sided_p_max_each"] and max(loo) < 0:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return {
        "verdict": verdict, "gate_failures": [],
        "common_complete_countries": n, "excluded_countries": len(COUNTRIES) - n,
        "credit_intensity_spread_pp": x_spread, "outcome_loss_spread_log_pp": y_spread,
        "spearman_rho": rho, "permutation_p_two_sided": p,
        "leave_one_out_rho_min": min(loo), "leave_one_out_rho_max": max(loo),
    }


def make_results(path: Path) -> list[dict[str, Any]]:
    registration = registration_commit()
    locks, info = committed_locks(registration, path)
    rows = selected_values(path)
    results = []
    for index, hypothesis_id in enumerate(IDS):
        results.append({
            "hypothesis_id": hypothesis_id,
            "family_id": FAMILY,
            "family_size": 2,
            "claim_scope": "18 advanced JST economies; 1929 credit intensity and 1929-1933 real/price losses",
            "source_sha256": SOURCE_SHA256,
            "registration_commit": registration,
            "source_lock_commit": locks[index],
            "source_key_roster_sha256": info["key_roster_sha256"],
            "country_roster": list(COUNTRIES),
            "entry_year": 1929,
            "outcome_year": 1933,
            "outcome_field": FIELDS[index],
            "thresholds": FLOORS,
            "result": evaluate(rows, index),
            "credit_boundary": "descriptive association only; no credit causation, policy, school, position or featured credit; two correlated outcomes, not independent replication",
            "source_citation": "Jordà, Schularick and Taylor (2017), JST Macrohistory R6; CC BY-NC-SA 4.0",
        })
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "source-lock", "run", "verify"))
    parser.add_argument("--source-parquet", type=Path, default=SOURCE_DEFAULT)
    parser.add_argument("--id", choices=IDS)
    args = parser.parse_args()
    if args.command == "plan":
        print(canonical_json(source_key_check(args.source_parquet)).decode(), end="")
    elif args.command == "source-lock":
        if not args.id:
            parser.error("--id is required for source-lock")
        write_lock(args.source_parquet, args.id)
    elif args.command == "run":
        if any((ROOT / relative).exists() for relative in RESULT_RELS):
            raise RuntimeError("a family result already exists; never overwrite")
        results = make_results(args.source_parquet)
        for relative, result in zip(RESULT_RELS, results):
            target = ROOT / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            output = canonical_json(result)
            target.write_bytes(output)
            print(json.dumps({"result": relative, "sha256": hashlib.sha256(output).hexdigest()}, sort_keys=True))
    elif args.command == "verify":
        registration = registration_commit()
        locks, _ = committed_locks(registration, args.source_parquet)
        additions = []
        for relative in RESULT_RELS:
            target = ROOT / relative
            if not target.is_file():
                raise RuntimeError(f"committed result missing: {relative}")
            commit = first_addition(relative)
            if not strict_ancestor(locks[1], commit):
                raise RuntimeError("result was not committed after both source locks")
            if git_bytes(commit, relative) != target.read_bytes():
                raise RuntimeError("committed result changed")
            additions.append(commit)
        if len(set(additions)) != 1:
            raise RuntimeError("two family results were not committed together")
        expected = make_results(args.source_parquet)
        for relative, result in zip(RESULT_RELS, expected):
            target = ROOT / relative
            payload = canonical_json(result)
            if target.read_bytes() != payload:
                raise RuntimeError(f"exact replay mismatch: {relative}")
            print(json.dumps({"verified": True, "result": relative,
                              "sha256": hashlib.sha256(payload).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
