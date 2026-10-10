#!/usr/bin/env python3
"""Frozen first-look JST pre-1914 money/inflation calibration.

Plan and source-lock read source keys only. Run and verify may read selected
values only after registration and metadata source-lock commits. Raw JST rows
are never written to the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats
import yaml

ROOT = Path(__file__).resolve().parents[1]
HID = "jst_pre1914_money_inflation_decades_v2"
FAMILY = "jst_pre1914_money_inflation_one_historical_family_2026"
RUNNER_REL = "scripts/run_jst_pre1914_money_inflation_2026.py"
PLAN_REL = "engine/audits/jst_pre1914_money_inflation_2026_source_plan.md"
SPEC_REL = f"hypotheses/monetary/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
LOCK_REL = "data/pinned_evidence/jst_pre1914_money_inflation_2026.source.json"
RUN_REL = f"engine/runs/{HID}"
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)
SOURCE_DEFAULT = ROOT / "data/vintages/jst/jst_macrohistory@2026-05-05T195309Z.parquet"
SOURCE_SHA256 = "4219d53e595e50b05430b5e4edd91f5f9ebff3987e3d0b6f21d2f2f50bc03a6f"
SOURCE_URL = "https://www.macrohistory.net/app/download/9834512569/JSTdatasetR6.xlsx"
DOC_URL = "https://www.macrohistory.net/database/"
COUNTRIES = (
    "AUS", "BEL", "CAN", "CHE", "DEU", "DNK", "ESP", "FIN", "FRA",
    "GBR", "IRL", "ITA", "JPN", "NLD", "NOR", "PRT", "SWE", "USA",
)
WINDOWS = (("1870_1880", 1870, 1880), ("1880_1890", 1880, 1890),
           ("1890_1900", 1890, 1900), ("1900_1910", 1900, 1910))
YEARS = (1870, 1880, 1890, 1900, 1910)
EXPECTED_KEYS = {(c, y) for c in COUNTRIES for y in YEARS}
SOURCE_COLUMNS = ("country_iso3", "year", "money", "cpi", "rgdpmad", "pop")
FLOORS = {
    "countries": 12, "country_decades": 48, "decades_per_country": 3,
    "countries_per_decade": 10, "within_treatment_sd_pp": 0.5,
    "maximum_country_treatment_share": 0.20,
}
assert len(EXPECTED_KEYS) == 90 and len(COUNTRIES) * len(WINDOWS) == 72


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and out.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {out.stderr.decode(errors='replace').strip()}")
    return out


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative).stdout.decode().splitlines()
    if not commits:
        raise RuntimeError(f"no committed first addition: {relative}")
    return commits[0]


def committed_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def registration_commit() -> str:
    additions = {first_addition(relative) for relative in REGISTRATION_FILES}
    if len(additions) != 1:
        raise RuntimeError("registration files were not first committed together")
    commit = additions.pop()
    for relative in REGISTRATION_FILES:
        current = (ROOT / relative).read_bytes()
        if current != committed_bytes(commit, relative) or current != committed_bytes("HEAD", relative):
            raise RuntimeError(f"frozen registration bytes changed: {relative}")
    if git("ls-tree", "-r", "--name-only", commit, "--", LOCK_REL, RUN_REL).stdout.strip():
        raise RuntimeError("source lock or result existed in registration commit")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_check(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"licensed local JST parquet unavailable: {path}")
    if sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("source SHA-256 differs from frozen JST R6")
    missing = set(SOURCE_COLUMNS) - set(pq.ParquetFile(path).schema_arrow.names)
    if missing:
        raise RuntimeError(f"source lacks frozen columns: {sorted(missing)}")


def key_check(path: Path) -> dict[str, Any]:
    """Read country/year only, never selected values or null masks."""
    source_check(path)
    frame = pd.read_parquet(path, columns=["country_iso3", "year"])
    frame = frame[frame.country_iso3.isin(COUNTRIES) & frame.year.isin(YEARS)]
    observed = [(str(c), int(y)) for c, y in frame.itertuples(index=False, name=None)]
    if len(observed) != len(EXPECTED_KEYS) or set(observed) != EXPECTED_KEYS:
        raise RuntimeError(f"fixed JST source-key grid differs: {len(observed)} rows, "
                           f"{len(EXPECTED_KEYS - set(observed))} absent")
    if len(set(observed)) != len(observed):
        raise RuntimeError("duplicate JST source key")
    canonical = "".join(f"{c},{y}\n" for c, y in sorted(observed)).encode()
    return {"source_key_count": len(observed),
            "source_key_roster_sha256": hashlib.sha256(canonical).hexdigest()}


def source_lock(path: Path) -> None:
    registration = registration_commit()
    target = ROOT / LOCK_REL
    if target.exists():
        raise RuntimeError("source lock already exists; never overwrite")
    info = key_check(path)
    lock = {
        "family_id": FAMILY, "hypothesis_id": HID,
        "registration_commit": registration,
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database",
        "release": "R6", "source_url": SOURCE_URL,
        "documentation_url": DOC_URL,
        "fetch_manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "original_parquet_basename": SOURCE_DEFAULT.name,
        "original_parquet_sha256": SOURCE_SHA256,
        "original_parquet_bytes": path.stat().st_size,
        "source_columns_for_replay": list(SOURCE_COLUMNS),
        "countries": list(COUNTRIES), "endpoint_years": list(YEARS),
        "candidate_country_decades": 72,
        **info,
        "license": "CC BY-NC-SA 4.0; local licensed source required for replay; no source-value rows redistributed",
        "attribution": "Jordà, Schularick and Taylor (2017), Macrofinancial History and the New Business Cycle Facts",
        "contains_source_values": False,
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote metadata-only source lock for {info['source_key_count']} keys; commit it separately.")


def committed_lock(path: Path, registration: str) -> tuple[dict[str, Any], str]:
    lock_commit = first_addition(LOCK_REL)
    if not strict_ancestor(registration, lock_commit):
        raise RuntimeError("source lock was not committed after registration")
    current = (ROOT / LOCK_REL).read_bytes()
    if current != committed_bytes(lock_commit, LOCK_REL) or current != committed_bytes("HEAD", LOCK_REL):
        raise RuntimeError("source lock bytes changed")
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("run artifact existed in source-lock commit")
    lock = json.loads(current)
    if lock.get("registration_commit") != registration or lock.get("contains_source_values") is not False:
        raise RuntimeError("source lock does not match frozen registration")
    if lock.get("original_parquet_sha256") != SOURCE_SHA256 or path.stat().st_size != lock.get("original_parquet_bytes"):
        raise RuntimeError("local source identity differs from source lock")
    if key_check(path)["source_key_roster_sha256"] != lock.get("source_key_roster_sha256"):
        raise RuntimeError("source-key roster differs from source lock")
    return lock, lock_commit


def valid_endpoint(row: dict[str, Any] | None) -> tuple[float, float, float, float] | None:
    if row is None:
        return None
    try:
        values = tuple(float(row[column]) for column in ("money", "cpi", "rgdpmad", "pop"))
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) and value > 0 for value in values):
        return None
    return values


def load_values(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Selected values are accessible only after committed_lock succeeds."""
    frame = pd.read_parquet(path, columns=list(SOURCE_COLUMNS))
    frame = frame[frame.country_iso3.isin(COUNTRIES) & frame.year.isin(YEARS)]
    rows: dict[tuple[str, int], dict[str, Any]] = {}
    for record in frame.to_dict(orient="records"):
        key = (str(record["country_iso3"]), int(record["year"]))
        if key in rows:
            raise RuntimeError("duplicate source-value key")
        rows[key] = record
    if set(rows) != EXPECTED_KEYS:
        raise RuntimeError("source-value keys differ from frozen roster")
    return rows


def matrix(sample: list[tuple[str, str, float, float]]) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    countries = sorted({item[0] for item in sample})
    periods = [item[0] for item in WINDOWS]
    n = len(sample)
    z = np.ones((n, 1 + len(countries) - 1 + len(periods) - 1), dtype=float)
    z[:, 1:] = 0.0
    for i, (country, period, _, _) in enumerate(sample):
        if country != countries[0]:
            z[i, 1 + countries[1:].index(country)] = 1.0
        if period != periods[0]:
            z[i, len(countries) + periods[1:].index(period)] = 1.0
    x = np.array([item[2] for item in sample], dtype=float)
    y = np.array([item[3] for item in sample], dtype=float)
    return z, x, y, countries


def fit(sample: list[tuple[str, str, float, float]], clustered: bool) -> dict[str, float]:
    z, x, y, countries = matrix(sample)
    X = np.column_stack((z, x))
    n, k = X.shape
    if n <= k or np.linalg.matrix_rank(X) != k:
        raise ValueError("fixed-effects design rank deficient")
    coef = np.linalg.lstsq(X, y, rcond=None)[0]
    out = {"beta": float(coef[-1])}
    if clustered:
        groups = len(countries)
        residual = y - X @ coef
        bread = np.linalg.inv(X.T @ X)
        meat = np.zeros((k, k), dtype=float)
        for country in countries:
            idx = np.array([item[0] == country for item in sample])
            score = X[idx].T @ residual[idx]
            meat += np.outer(score, score)
        adjustment = groups / (groups - 1) * (n - 1) / (n - k)
        variance = adjustment * (bread @ meat @ bread)[-1, -1]
        if not np.isfinite(variance) or variance <= 0:
            raise ValueError("cluster variance nonpositive or nonfinite")
        se = float(np.sqrt(variance))
        statistic = float(coef[-1] / se)
        p = float(2 * stats.t.sf(abs(statistic), df=groups - 1))
        critical = float(stats.t.ppf(0.975, df=groups - 1))
        out.update(se=se, t=statistic, p=p,
                   ci95_low=float(coef[-1] - critical * se),
                   ci95_high=float(coef[-1] + critical * se),
                   residual_df=n - k, cluster_df=groups - 1)
    return out


def analyze(rows: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    candidate: list[tuple[str, str, float, float]] = []
    missing = 0
    for country in COUNTRIES:
        for period, start, end in WINDOWS:
            a = valid_endpoint(rows.get((country, start)))
            b = valid_endpoint(rows.get((country, end)))
            if a is None or b is None:
                missing += 1
                continue
            span = end - start
            money, cpi, real_pc, pop = (math.log(b[j] / a[j]) * 100 / span for j in range(4))
            candidate.append((country, period, money - real_pc - pop, cpi))
    counts = Counter(item[0] for item in candidate)
    retained = [item for item in candidate if counts[item[0]] >= FLOORS["decades_per_country"]]
    countries = sorted({item[0] for item in retained})
    periods = Counter(item[1] for item in retained)
    analysis: dict[str, Any] = {
        "family_id": FAMILY, "family_size": 1,
        "candidate_country_decades": 72,
        "invalid_endpoint_country_decades": missing,
        "complete_country_decades_before_country_floor": len(candidate),
        "retained_country_decades": len(retained),
        "retained_country_count": len(countries),
        "retained_by_decade": dict(sorted(periods.items())),
    }
    failures = []
    if len(countries) < FLOORS["countries"]:
        failures.append("fewer than 12 countries with at least three valid decades")
    if len(retained) < FLOORS["country_decades"]:
        failures.append("fewer than 48 valid country-decades")
    for period, _, _ in WINDOWS:
        if periods[period] < FLOORS["countries_per_decade"]:
            failures.append(f"{period}: fewer than 10 countries")
    if not failures:
        z, x, _, countries = matrix(retained)
        if np.linalg.matrix_rank(z) != z.shape[1]:
            failures.append("fixed-effects nuisance design rank deficient")
        else:
            residual_x = x - z @ np.linalg.lstsq(z, x, rcond=None)[0]
            exposure_sd = float(np.sqrt(np.mean(residual_x ** 2)))
            squares = float(np.sum(residual_x ** 2))
            maximum_share = max(float(np.sum(residual_x[[item[0] == c for item in retained]] ** 2) / squares)
                                for c in countries) if squares > 0 else 1.0
            analysis.update(within_treatment_sd_pp=exposure_sd,
                            maximum_country_treatment_share=maximum_share)
            if exposure_sd < FLOORS["within_treatment_sd_pp"]:
                failures.append("within-FE treatment SD below 0.5 percentage points")
            if maximum_share > FLOORS["maximum_country_treatment_share"]:
                failures.append("one country exceeds 20 percent of within-FE treatment variation")
    if failures:
        analysis.update(sample_floor_failures=failures, verdict="INCONCLUSIVE",
                        reason="registered sample or exposure gate failed")
        return analysis
    try:
        estimate = fit(retained, clustered=True)
        deleted = {country: fit([item for item in retained if item[0] != country], clustered=False)["beta"]
                   for country in countries}
    except (ValueError, np.linalg.LinAlgError) as exc:
        analysis.update(sample_floor_failures=[str(exc)], verdict="INCONCLUSIVE",
                        reason="registered estimator gate failed")
        return analysis
    beta = estimate["beta"]
    p = estimate["p"]
    minimum_deleted = min(deleted.values())
    if 0.5 <= beta <= 1.5 and p <= 0.05 and minimum_deleted > 0:
        verdict = "SUPPORTED"
    elif beta <= 0 and p <= 0.05:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    analysis.update(estimate=estimate, country_deletion_slopes=deleted,
                    minimum_country_deletion_slope=minimum_deleted,
                    sample_floor_failures=[], verdict=verdict,
                    reason="frozen historical two-way fixed-effects monetary calibration")
    return analysis


def result_card(d: dict[str, Any]) -> str:
    a = d["analysis"]
    lines = [f"# {HID}", "", f"**Verdict: {a['verdict']}** — {a['reason']}", "",
             "One descriptive 1870–1910 JST R6 historical money/inflation question.", "",
             f"- Complete endpoint pairs: {a['complete_country_decades_before_country_floor']}/72; "
             f"retained: {a['retained_country_decades']} in {a['retained_country_count']} countries.",
             f"- Frozen source SHA-256: {SOURCE_SHA256}.",
             f"- Registration commit: {d['preregistration_commit']}.",
             f"- Metadata source-lock commit: {d['source_lock_commit']}."]
    if "estimate" in a:
        e = a["estimate"]
        lines += [f"- Country/decanal fixed-effects slope: {e['beta']:.6f}; "
                  f"cluster SE {e['se']:.6f}; two-sided p={e['p']:.6f}; "
                  f"95% CI [{e['ci95_low']:.6f}, {e['ci95_high']:.6f}].",
                  f"- Minimum country-deletion slope: {a['minimum_country_deletion_slope']:.6f}."]
    if a["sample_floor_failures"]:
        lines += ["", "Failed frozen gates:"] + [f"- {reason}." for reason in a["sample_floor_failures"]]
    lines += ["", "This contemporaneous association does not identify a monetary or policy effect. "
              "No school, position, policy, causal, or featured credit is granted. "
              "The old 1960–2023 result remains archived and unchanged.", "",
              "JST historical data are CC BY-NC-SA 4.0. No source-value rows are committed; "
              "replay requires a lawfully held exact-hash local copy. "
              "Cite Jordà, Schularick and Taylor (2017).", "",
              f"Reproduce: python3 {RUNNER_REL} verify --source-parquet <local-JST-R6-parquet>", ""]
    return "\n".join(lines)


def artifacts(registration: str, lock_commit: str, lock: dict[str, Any],
              analysis: dict[str, Any], stamp: str) -> dict[str, bytes]:
    correction = {"disposition": "descriptive_calibration_only",
                  "school_score_eligible": False, "school_score_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0}
    source = {"publisher": lock["publisher"], "release": "R6", "source_url": SOURCE_URL,
              "documentation_url": DOC_URL, "source_sha256": SOURCE_SHA256,
              "source_lock_manifest": LOCK_REL, "source_lock_commit": lock_commit,
              "key_roster_sha256": lock["source_key_roster_sha256"],
              "license": lock["license"], "contains_source_values": False}
    diagnostics = {"hypothesis_id": HID, "verdict": analysis["verdict"],
                   "status": analysis["verdict"], "run_utc": stamp,
                   "method": "two-way fixed-effects historical decadal slope with country-cluster t inference",
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_sha256": SOURCE_SHA256,
                   "key_roster_sha256": lock["source_key_roster_sha256"],
                   "analysis": analysis, "family_size": 1,
                   "evidence_tier_recommendation": "calibration" if analysis["verdict"] != "INCONCLUSIVE" else "archive",
                   "correction": correction,
                   "limitations": ["Historical advanced-economy sample only.",
                                   "Contemporaneous money and prices are endogenous.",
                                   "No causal, policy, or school inference.",
                                   "Licensed JST values are not redistributed."]}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": HID, "path": SPEC_REL},
              "preregistration": {"commit": registration, "steelman": STEELMAN_REL,
                                  "source_plan": PLAN_REL,
                                  "frozen_hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml"},
              "source": source,
              "reproduction": {"runner": RUNNER_REL,
                               "command": f"python3 {RUNNER_REL} verify --source-parquet <local-JST-R6-parquet>"},
              "gate": {"candidate_country_decades": 72, "source_keys": 90,
                       "windows": [list(item) for item in WINDOWS], "floors": FLOORS,
                       "family_size": 1},
              "result": analysis, "correction": correction}
    manifest = {"hypothesis_id": HID, "run_utc": stamp, "status": analysis["verdict"],
                "runner": RUNNER_REL, "hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
                "preregistration_commit": registration, "source": source,
                "correction": correction}
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), "
               "'verify', *sys.argv[1:]], cwd=root))\n")
    return {
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False).encode(),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": result_card(diagnostics).encode(),
        "replication.py": wrapper.encode(),
    }


def execute(path: Path, verify: bool) -> None:
    registration = registration_commit()
    lock, lock_commit = committed_lock(path, registration)
    target = ROOT / RUN_REL
    if verify:
        stored = json.loads((target / "diagnostics.json").read_text())
        stamp = stored["run_utc"]
        if datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("run timestamp lacks timezone")
    else:
        if target.exists():
            raise RuntimeError("result directory already exists; use verify")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = load_values(path)
    analysis = analyze(rows)
    expected = artifacts(registration, lock_commit, lock, analysis, stamp)
    if verify:
        if {item.name for item in target.iterdir() if item.is_file()} != set(expected):
            raise RuntimeError("run artifact set differs from frozen runner")
        for name, content in expected.items():
            if (target / name).read_bytes() != content:
                raise RuntimeError(f"byte-exact replay mismatch: {name}")
        print(f"Verified {HID}: {analysis['verdict']} and {len(expected)} exact artifacts")
    else:
        target.mkdir(parents=True, exist_ok=False)
        for name, content in expected.items():
            (target / name).write_bytes(content)
        print(f"{HID}: {analysis['verdict']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "source-lock", "run", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--source-parquet", type=Path, default=SOURCE_DEFAULT)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            print(json.dumps({"value_access": False, "source_sha256": SOURCE_SHA256,
                              "country_count": len(COUNTRIES), "candidate_country_decades": 72,
                              "endpoint_years": YEARS, **key_check(args.source_parquet)},
                             indent=2, sort_keys=True))
        elif args.command == "source-lock":
            source_lock(args.source_parquet)
        else:
            execute(args.source_parquet, verify=args.command == "verify")
    except (OSError, ValueError, RuntimeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
