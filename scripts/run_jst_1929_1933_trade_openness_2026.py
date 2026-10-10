#!/usr/bin/env python3
"""One prospectively locked, descriptive JST interwar trade-share test.

`plan` and `source-lock` read only the country/year keys and Parquet schema.
`run` and `verify` read the three selected values only after a separately
committed source lock. Raw and country-level values are never written.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
HID = "jst_1929_1933_advanced_trade_openness_drop_v2"
SPEC_REL = f"hypotheses/trade/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
PLAN_REL = "engine/audits/jst_1929_1933_trade_openness_source_plan_2026.md"
RUNNER_REL = "scripts/run_jst_1929_1933_trade_openness_2026.py"
LOCK_REL = "data/pinned_evidence/jst_1929_1933_trade_openness_2026.source.json"
RESULT_REL = f"engine/runs/{HID}/diagnostics.json"
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)
SOURCE_BASENAME = "jst_macrohistory@2026-05-05T195309Z.parquet"
SOURCE_DEFAULT = ROOT / "data/vintages/jst" / SOURCE_BASENAME
SOURCE_SHA256 = "4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f"
SOURCE_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
DOC_URL = "https://www.macrohistory.net/database/"
COUNTRIES = ("AUS", "BEL", "CAN", "DEU", "ESP", "FRA", "GBR", "ITA", "JPN", "NLD", "SWE", "USA")
YEARS = tuple(range(1925, 1934))
BASELINE = tuple(range(1925, 1930))
ENDPOINT = (1932, 1933)
SOURCE_COLUMNS = ("country_iso3", "year", "imports", "exports", "gdp")
EXPECTED_KEYS = {(country, year) for country in COUNTRIES for year in YEARS}
FLOORS = {
    "minimum_complete_countries": 10,
    "minimum_countries_with_one_pp_annual_range": 8,
    "maximum_leave_one_out_shift_pp": 3.0,
    "support_decline_pp": 8.0,
    "support_country_declines": 8,
    "refute_decline_below_pp": 5.0,
}
assert len(EXPECTED_KEYS) == 108


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).stdout.decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}, got {len(commits)}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def registration_commit() -> str:
    additions = {first_addition(relative) for relative in REGISTRATION_FILES}
    if len(additions) != 1:
        raise RuntimeError("spec, steelman, plan and runner were not registered together")
    commit = additions.pop()
    for relative in REGISTRATION_FILES:
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"frozen registration changed after first commit: {relative}")
    if git("ls-tree", "-r", "--name-only", commit, "--", LOCK_REL, RESULT_REL).stdout.strip():
        raise RuntimeError("source lock or result appeared in registration commit")
    return commit


def lock_commit(registration: str) -> str:
    path = ROOT / LOCK_REL
    if not path.is_file():
        raise RuntimeError("source lock missing")
    commit = first_addition(LOCK_REL)
    if not strict_ancestor(registration, commit):
        raise RuntimeError("source lock was not committed after registration")
    if git_bytes(commit, LOCK_REL) != path.read_bytes():
        raise RuntimeError("source lock changed after first commit")
    if git("ls-tree", "-r", "--name-only", commit, "--", RESULT_REL).stdout.strip():
        raise RuntimeError("result appeared in source-lock commit")
    lock = json.loads(path.read_text())
    if lock.get("registration_commit") != registration or lock.get("source_sha256") != SOURCE_SHA256:
        raise RuntimeError("source lock does not match registration/source")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_check(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError("licensed local JST R6 source unavailable")
    if sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("JST R6 parquet SHA-256 mismatch")
    schema = pq.ParquetFile(path).schema_arrow
    missing = set(SOURCE_COLUMNS) - set(schema.names)
    if missing:
        raise RuntimeError(f"JST R6 source missing frozen columns: {sorted(missing)}")
    return {column: str(schema.field(column).type) for column in SOURCE_COLUMNS}


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def source_key_check(path: Path) -> dict[str, Any]:
    """Read the two key columns only; never selected values/null masks."""
    schema = source_check(path)
    table = pq.read_table(path, columns=["country_iso3", "year"])
    observed = [(str(c), int(y)) for c, y in zip(table["country_iso3"].to_pylist(), table["year"].to_pylist())
                if c in COUNTRIES and y in YEARS]
    if len(observed) != 108 or set(observed) != EXPECTED_KEYS:
        raise RuntimeError(f"fixed JST key grid mismatch: {len(observed)} rows, {len(EXPECTED_KEYS-set(observed))} missing")
    if len(set(observed)) != len(observed):
        raise RuntimeError("duplicate country-year key in selected JST grid")
    key_bytes = "".join(f"{c},{y}\n" for c, y in sorted(observed)).encode()
    return {"selected_key_count": len(observed), "key_roster_sha256": hashlib.sha256(key_bytes).hexdigest(),
            "selected_schema": schema}


def make_source_lock(path: Path) -> None:
    registration = registration_commit()
    if git("rev-parse", "HEAD").stdout.decode().strip() != registration:
        raise RuntimeError("source lock must be made immediately after registration commit")
    if (ROOT / LOCK_REL).exists():
        raise RuntimeError("source lock already exists; never overwrite")
    key_info = source_key_check(path)
    lock = {
        "hypothesis_id": HID,
        "family_size": 1,
        "registration_commit": registration,
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database",
        "release": "R6",
        "official_source_url": SOURCE_URL,
        "documentation_url": DOC_URL,
        "citation": "Jordà, Schularick and Taylor (2017), Macrofinancial History and the New Business Cycle Facts",
        "license": "CC BY-NC-SA 4.0; non-commercial, attribution, share alike",
        "source_basename": SOURCE_BASENAME,
        "source_sha256": SOURCE_SHA256,
        "source_bytes": path.stat().st_size,
        "fetch_manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "countries": list(COUNTRIES),
        "years": list(YEARS),
        **key_info,
    }
    target = ROOT / LOCK_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_json(lock))
    print(json.dumps({"source_lock": LOCK_REL, "registration_commit": registration,
                      "key_roster_sha256": key_info["key_roster_sha256"]}, sort_keys=True))


def selected_values(path: Path) -> dict[str, dict[int, tuple[float, float, float]]]:
    """Only call after registration and committed source lock are verified."""
    table = pq.read_table(path, columns=list(SOURCE_COLUMNS))
    selected: dict[str, dict[int, tuple[float, float, float]]] = {c: {} for c in COUNTRIES}
    for c, y, imp, exp, gdp in zip(*(table[column].to_pylist() for column in SOURCE_COLUMNS)):
        if c in COUNTRIES and y in YEARS:
            if y in selected[c]:
                raise RuntimeError("duplicate selected JST country-year")
            selected[c][int(y)] = (imp, exp, gdp)
    if {(c, y) for c, years in selected.items() for y in years} != EXPECTED_KEYS:
        raise RuntimeError("selected JST source-key roster changed")
    return selected


def evaluate(selected: dict[str, dict[int, tuple[float, float, float]]]) -> dict[str, Any]:
    deltas: list[float] = []
    range_count = 0
    invalid_country_count = 0
    for country in COUNTRIES:
        rows = selected[country]
        if set(rows) != set(YEARS):
            raise RuntimeError("selected source-key roster incomplete")
        ratios = {}
        for year in YEARS:
            triple = rows[year]
            if any(value is None or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0
                   for value in triple):
                ratios = {}
                break
            imp, exp, gdp = triple
            ratio = 100.0 * (float(imp) + float(exp)) / float(gdp)
            if not math.isfinite(ratio):
                ratios = {}
                break
            ratios[year] = ratio
        if not ratios:
            invalid_country_count += 1
            continue
        if max(ratios.values()) - min(ratios.values()) >= 1.0:
            range_count += 1
        baseline = sum(ratios[y] for y in BASELINE) / len(BASELINE)
        endpoint = sum(ratios[y] for y in ENDPOINT) / len(ENDPOINT)
        deltas.append(baseline - endpoint)
    complete = len(deltas)
    reasons: list[str] = []
    if complete < FLOORS["minimum_complete_countries"]:
        reasons.append("complete_country_floor")
    if range_count < FLOORS["minimum_countries_with_one_pp_annual_range"]:
        reasons.append("within_country_variation_floor")
    mean = sum(deltas) / complete if complete else None
    loo = [(sum(deltas) - delta) / (complete - 1) for delta in deltas] if complete >= 2 else []
    loo_shift = max((abs(value - mean) for value in loo), default=None) if mean is not None else None
    sign_stable = bool(loo) and all(value * mean > 0 for value in loo)
    if not sign_stable:
        reasons.append("leave_one_out_sign_instability")
    if loo_shift is None or loo_shift > FLOORS["maximum_leave_one_out_shift_pp"]:
        reasons.append("leave_one_out_influence_cap")
    if reasons:
        verdict = "INCONCLUSIVE"
    elif mean >= FLOORS["support_decline_pp"] and sum(delta > 0 for delta in deltas) >= FLOORS["support_country_declines"]:
        verdict = "SUPPORTED"
    elif mean < FLOORS["refute_decline_below_pp"]:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return {
        "verdict": verdict,
        "gate_failures": reasons,
        "complete_countries": complete,
        "invalid_countries": invalid_country_count,
        "countries_with_one_pp_annual_range": range_count,
        "declining_countries": sum(delta > 0 for delta in deltas),
        "mean_decline_pp": mean if not reasons else None,
        "leave_one_out_mean_min_pp": min(loo) if not reasons else None,
        "leave_one_out_mean_max_pp": max(loo) if not reasons else None,
        "maximum_leave_one_out_shift_pp": loo_shift if not reasons else None,
    }


def make_result(path: Path) -> dict[str, Any]:
    registration = registration_commit()
    locked = lock_commit(registration)
    key_info = source_key_check(path)
    lock = json.loads((ROOT / LOCK_REL).read_text())
    for field in ("key_roster_sha256", "selected_key_count", "selected_schema"):
        if key_info[field] != lock[field]:
            raise RuntimeError(f"source metadata differs from committed lock: {field}")
    result = evaluate(selected_values(path))
    return {
        "hypothesis_id": HID,
        "family_id": "jst_1929_1933_advanced_trade_openness_one_family_2026",
        "family_size": 1,
        "claim_scope": "twelve JST advanced economies; descriptive trade-to-GDP contrast only",
        "source_sha256": SOURCE_SHA256,
        "registration_commit": registration,
        "source_lock_commit": locked,
        "source_key_roster_sha256": key_info["key_roster_sha256"],
        "baseline_years": list(BASELINE),
        "endpoint_years": list(ENDPOINT),
        "country_roster": list(COUNTRIES),
        "thresholds": FLOORS,
        "result": result,
        "credit_boundary": "one descriptive calibration only; no tariff causation, global claim, policy/school/position/featured credit",
        "source_citation": "Jordà, Schularick and Taylor (2017), JST Macrohistory R6; CC BY-NC-SA 4.0",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "source-lock", "run", "verify"))
    parser.add_argument("--source-parquet", type=Path, default=SOURCE_DEFAULT)
    args = parser.parse_args()
    path = args.source_parquet
    if args.command == "plan":
        print(canonical_json(source_key_check(path)).decode(), end="")
    elif args.command == "source-lock":
        make_source_lock(path)
    elif args.command == "run":
        if (ROOT / RESULT_REL).exists():
            raise RuntimeError("result already exists; never overwrite")
        output = canonical_json(make_result(path))
        target = ROOT / RESULT_REL
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        print(json.dumps({"result": RESULT_REL, "sha256": hashlib.sha256(output).hexdigest()}, sort_keys=True))
    elif args.command == "verify":
        target = ROOT / RESULT_REL
        if not target.is_file():
            raise RuntimeError("committed result missing")
        result_commit = first_addition(RESULT_REL)
        registration = registration_commit()
        locked = lock_commit(registration)
        if not strict_ancestor(locked, result_commit):
            raise RuntimeError("result was not committed after source lock")
        if git_bytes(result_commit, RESULT_REL) != target.read_bytes():
            raise RuntimeError("committed result changed")
        expected = canonical_json(make_result(path))
        if target.read_bytes() != expected:
            raise RuntimeError("exact replay mismatch")
        print(json.dumps({"verified": True, "result": RESULT_REL,
                          "sha256": hashlib.sha256(expected).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
