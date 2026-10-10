#!/usr/bin/env python3
"""One blind, descriptive historical JST credit-boom/crisis test.

`plan` reads country/year keys only. `source-lock` writes metadata only after
the four registration files are committed. `run` reads JST values only after
the metadata lock is committed in a later commit. No source value rows are
written into the repository; replay requires the licensed local JST R6 file.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow.parquet as pq
import yaml

ROOT = Path(__file__).resolve().parents[1]
HID = "jst_pre1980_credit_boom_crisis_onset_v2"
RUNNER_REL = "scripts/run_jst_pre1980_credit_crisis_2026.py"
PLAN_REL = "engine/audits/jst_pre1980_credit_crisis_2026_source_plan.md"
SPEC_REL = f"hypotheses/regulatory/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
LOCK_REL = "data/pinned_evidence/jst_pre1980_credit_crisis_2026.source.json"
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
ERA_ANCHORS = {
    "1870_1913": (1875, 1880, 1885, 1890, 1895, 1900, 1905),
    "1920_1939": (1925, 1930),
    "1946_1979": (1955, 1960, 1965, 1970),
}
SOURCE_YEARS = tuple(range(1870, 1911)) + tuple(range(1920, 1936)) + tuple(range(1950, 1976))
EXPECTED_KEYS = {(country, year) for country in COUNTRIES for year in SOURCE_YEARS}
EXPECTED_KEY_COUNT = 1494
CANDIDATE_COUNT = 234
SOURCE_COLUMNS = ("country_iso3", "year", "tloans", "gdp", "crisisjst")
FLOORS = {
    "loan_valid_per_era": 15,
    "max_high_share_per_era": 0.35,
    "countries": 12,
    "at_risk_anchors": 100,
    "high_anchors": 25,
    "other_anchors": 70,
    "incident_events": 10,
    "event_countries": 5,
    "event_eras": 2,
    "other_incident_events": 3,
}
assert len(EXPECTED_KEYS) == EXPECTED_KEY_COUNT
assert sum(len(v) for v in ERA_ANCHORS.values()) * len(COUNTRIES) == CANDIDATE_COUNT


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    history = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative)
    commits = history.stdout.decode().strip().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit: {relative}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def analysis_ast(raw: bytes) -> str:
    """Compare all frozen analysis code while allowing a path-only replay erratum."""
    tree = ast.parse(raw)
    tree.body = [
        node for node in tree.body
        if not (
            isinstance(node, ast.FunctionDef) and node.name in {"registration_commit", "analysis_ast"}
        )
        and not (
            isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "SOURCE_DEFAULT"
                    for target in node.targets)
        )
        and not (
            isinstance(node, ast.Import)
            and all(alias.name in {"ast", "re"} for alias in node.names)
        )
    ]
    return ast.dump(tree, include_attributes=False)


def registration_commit() -> str:
    histories = {}
    for relative in REGISTRATION_FILES:
        path = ROOT / relative
        if not path.is_file() or git_bytes("HEAD", relative) != path.read_bytes():
            raise RuntimeError(f"commit unchanged registration before value access: {relative}")
        histories[relative] = git("log", "--format=%H", "HEAD", "--", relative).stdout.decode().splitlines()
    additions = {history[-1] for history in histories.values()}
    if len(additions) != 1:
        raise RuntimeError("hypothesis, steelman, plan, runner first additions differ")
    first = additions.pop()
    spec_history = histories[SPEC_REL]
    if (histories[STEELMAN_REL] != spec_history or len(spec_history) != 2
            or spec_history[1] != first or not strict_ancestor(first, spec_history[0])):
        raise RuntimeError("expected original registration plus one pre-source correction")
    commit = spec_history[0]
    plan_history = histories[PLAN_REL]
    runner_history = histories[RUNNER_REL]
    if (plan_history != runner_history or len(plan_history) != 3
            or plan_history[1:] != spec_history
            or not strict_ancestor(
                first_addition(f"{RUN_REL}/diagnostics.json"), plan_history[0]
            )):
        raise RuntimeError("expected one disclosed post-result path redaction")
    redacted_plan = re.sub(
        rb"/Users/[A-Za-z0-9._-]+/IESET/",
        b"<local-source-root>/",
        git_bytes(commit, PLAN_REL),
    )
    if (ROOT / PLAN_REL).read_bytes() != redacted_plan:
        raise RuntimeError("source plan changed beyond local path redaction")
    if analysis_ast(git_bytes(commit, RUNNER_REL)) != analysis_ast((ROOT / RUNNER_REL).read_bytes()):
        raise RuntimeError("frozen analytic runner changed beyond replay path guard")
    for relative in (SPEC_REL, STEELMAN_REL):
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registered bytes changed after pre-source correction: {relative}")
    for revision in (first, commit):
        if git("ls-tree", "-r", "--name-only", revision, "--", LOCK_REL, RUN_REL).stdout.strip():
            raise RuntimeError("source lock or result appeared before corrected registration")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_check(path: Path) -> None:
    if not path.is_file():
        raise RuntimeError(f"licensed local JST R6 parquet unavailable: {path}")
    if sha256_file(path) != SOURCE_SHA256:
        raise RuntimeError("JST R6 parquet SHA-256 differs from frozen source")
    columns = set(pq.ParquetFile(path).schema_arrow.names)
    if not set(SOURCE_COLUMNS).issubset(columns):
        raise RuntimeError(f"JST source missing frozen columns: {set(SOURCE_COLUMNS)-columns}")


def canonical_keys(keys: set[tuple[str, int]]) -> bytes:
    return "".join(f"{country},{year}\n" for country, year in sorted(keys)).encode("utf-8")


def source_key_check(path: Path) -> dict[str, Any]:
    """Reads only country/year, never loan/GDP/crisis values or their null masks."""
    source_check(path)
    keys = pd.read_parquet(path, columns=["country_iso3", "year"])
    selected = keys[keys["country_iso3"].isin(COUNTRIES) & keys["year"].isin(SOURCE_YEARS)]
    observed = [(str(c), int(y)) for c, y in selected.itertuples(index=False, name=None)]
    if len(observed) != EXPECTED_KEY_COUNT or set(observed) != EXPECTED_KEYS:
        missing = len(EXPECTED_KEYS - set(observed))
        raise RuntimeError(f"JST fixed key grid mismatch: {len(observed)} rows, {missing} absent keys")
    if len(set(observed)) != len(observed):
        raise RuntimeError("JST fixed key grid has duplicate country-year keys")
    return {
        "expected_country_year_keys": EXPECTED_KEY_COUNT,
        "observed_country_year_keys": len(observed),
        "key_roster_sha256": hashlib.sha256(canonical_keys(set(observed))).hexdigest(),
    }


def source_lock(path: Path) -> None:
    registration = registration_commit()
    lock_path = ROOT / LOCK_REL
    if lock_path.exists():
        raise RuntimeError("metadata source lock already exists; never overwrite")
    key_info = source_key_check(path)
    manifest = {
        "family": "jst_pre1980_credit_crisis_one_historical_family_2026",
        "hypothesis_id": HID,
        "registration_commit": registration,
        "publisher": "Jordà-Schularick-Taylor Macrohistory Database",
        "release": "R6",
        "official_source_url": SOURCE_URL,
        "documentation_url": DOC_URL,
        "original_parquet_basename": SOURCE_DEFAULT.name,
        "original_parquet_sha256": SOURCE_SHA256,
        "original_parquet_bytes": path.stat().st_size,
        "fetch_manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source_columns_for_replay": list(SOURCE_COLUMNS),
        "candidate_country_anchors": CANDIDATE_COUNT,
        "country_count": len(COUNTRIES),
        "anchor_years": [year for years in ERA_ANCHORS.values() for year in years],
        "source_year_intervals": [[1870, 1910], [1920, 1935], [1950, 1975]],
        **key_info,
        "license": "CC BY-NC-SA 4.0; local licensed source required for replay; no value rows redistributed",
        "required_attribution": "Jordà, Schularick and Taylor (2017), Macrofinancial History and the New Business Cycle Facts",
        "contains_source_values": False,
    }
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote metadata-only source lock with {key_info['observed_country_year_keys']} keys; "
          "commit it separately before running the test.")


def committed_lock(path: Path, registration: str) -> tuple[dict[str, Any], str]:
    lock_commit = first_addition(LOCK_REL)
    if not strict_ancestor(registration, lock_commit):
        raise RuntimeError("source lock must first appear after registration")
    lock_path = ROOT / LOCK_REL
    if not lock_path.is_file():
        raise RuntimeError("source lock missing")
    current = lock_path.read_bytes()
    if git_bytes(lock_commit, LOCK_REL) != current or git_bytes("HEAD", LOCK_REL) != current:
        raise RuntimeError("source lock bytes changed after first addition")
    if git("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("run artifacts appeared in source-lock commit")
    manifest = json.loads(current)
    if manifest.get("registration_commit") != registration:
        raise RuntimeError("source lock points to a different preregistration commit")
    if manifest.get("original_parquet_sha256") != SOURCE_SHA256 or manifest.get("contains_source_values") is not False:
        raise RuntimeError("source lock is not the frozen metadata-only source")
    if source_key_check(path)["key_roster_sha256"] != manifest.get("key_roster_sha256"):
        raise RuntimeError("licensed local JST key roster differs from source lock")
    if path.stat().st_size != manifest.get("original_parquet_bytes"):
        raise RuntimeError("licensed local JST byte count differs from source lock")
    return manifest, lock_commit


def quantile_linear(values: list[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("empty quantile input")
    location = (len(ordered) - 1) * p
    left = int(math.floor(location))
    right = int(math.ceil(location))
    return ordered[left] + (ordered[right] - ordered[left]) * (location - left)


def valid_ratio(row: dict[str, Any] | None) -> float | None:
    if row is None:
        return None
    try:
        loans = float(row["tloans"])
        gdp = float(row["gdp"])
    except (TypeError, ValueError):
        return None
    if not math.isfinite(loans) or not math.isfinite(gdp) or loans < 0 or gdp <= 0:
        return None
    return loans / gdp


def crisis01(row: dict[str, Any] | None) -> int | None:
    if row is None:
        return None
    try:
        value = float(row["crisisjst"])
    except (TypeError, ValueError):
        return None
    return int(value) if value in (0.0, 1.0) else None


def load_fixed_values(path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Call only after the metadata source lock is a separate Git commit."""
    frame = pd.read_parquet(path, columns=list(SOURCE_COLUMNS))
    frame = frame[frame["country_iso3"].isin(COUNTRIES) & frame["year"].isin(SOURCE_YEARS)]
    keyed: dict[tuple[str, int], dict[str, Any]] = {}
    for row in frame.to_dict(orient="records"):
        key = (str(row["country_iso3"]), int(row["year"]))
        if key in keyed:
            raise RuntimeError("duplicate JST fixed key after source lock")
        keyed[key] = row
    if set(keyed) != EXPECTED_KEYS:
        raise RuntimeError("JST fixed value rows do not match preregistered key grid")
    return keyed


def analyze(rows: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    exposure: list[tuple[str, str, int, float]] = []
    era_valid = Counter()
    for era, years in ERA_ANCHORS.items():
        for country in COUNTRIES:
            for t in years:
                past = valid_ratio(rows.get((country, t - 5)))
                present = valid_ratio(rows.get((country, t)))
                if past is None or present is None:
                    continue
                delta = 100.0 * (present - past)
                if math.isfinite(delta):
                    exposure.append((era, country, t, delta))
                    era_valid[era] += 1
    era_cutoffs: dict[str, float] = {}
    era_high_share: dict[str, float] = {}
    fail_reasons = []
    for era in ERA_ANCHORS:
        values = [delta for e, _, _, delta in exposure if e == era]
        if len(values) < FLOORS["loan_valid_per_era"]:
            fail_reasons.append(f"{era}: fewer than 15 loan-valid anchors")
            continue
        cutoff = quantile_linear(values, 0.8)
        share = sum(v >= cutoff for v in values) / len(values)
        era_cutoffs[era] = cutoff
        era_high_share[era] = share
        if cutoff <= 0:
            fail_reasons.append(f"{era}: nonpositive top-quintile cutoff")
        if share > FLOORS["max_high_share_per_era"]:
            fail_reasons.append(f"{era}: cutoff ties make high share exceed 35 percent")
    analysis: dict[str, Any] = {
        "candidate_country_anchors": CANDIDATE_COUNT,
        "loan_valid_anchors": len(exposure),
        "loan_valid_by_era": dict(era_valid),
        "cutoff_pp_by_era": era_cutoffs,
        "high_share_by_era": era_high_share,
        "family_size": 1,
        "inferential_alpha": "none_descriptive",
        "sample_floor_failures": fail_reasons,
    }
    if fail_reasons:
        analysis.update(verdict="INCONCLUSIVE", reason="registered exposure floor or cutoff gate failed")
        return analysis
    at_risk: list[tuple[str, str, int, bool, int]] = []
    excluded_recent = excluded_crisis_missing = 0
    for era, country, t, delta in exposure:
        statuses = {year: crisis01(rows.get((country, year))) for year in range(t - 4, t + 6)}
        if any(v is None for v in statuses.values()):
            excluded_crisis_missing += 1
            continue
        if any(statuses[year] == 1 for year in range(t - 4, t + 1)):
            excluded_recent += 1
            continue
        high = delta >= era_cutoffs[era]
        # JST crisisjst is itself an onset-year dummy, not an active-year flag.
        incident = int(any(statuses[year] == 1 for year in range(t + 1, t + 6)))
        at_risk.append((era, country, t, high, incident))
    n_high = sum(row[3] for row in at_risk)
    e_high = sum(row[4] for row in at_risk if row[3])
    n_other = len(at_risk) - n_high
    e_other = sum(row[4] for row in at_risk if not row[3])
    event_rows = [row for row in at_risk if row[4]]
    countries = {row[1] for row in at_risk}
    event_countries = {row[1] for row in event_rows}
    event_eras = {row[0] for row in event_rows}
    analysis.update({
        "excluded_missing_crisis_window": excluded_crisis_missing,
        "excluded_recent_crisis": excluded_recent,
        "at_risk_anchors": len(at_risk),
        "at_risk_countries": len(countries),
        "high_anchors": n_high,
        "other_anchors": n_other,
        "high_incident_events": e_high,
        "other_incident_events": e_other,
        "incident_events": len(event_rows),
        "event_countries": len(event_countries),
        "event_eras": len(event_eras),
        "at_risk_by_era": dict(Counter(row[0] for row in at_risk)),
        "events_by_era": dict(Counter(row[0] for row in event_rows)),
    })
    gates = (
        (len(countries) >= FLOORS["countries"], "fewer than 12 at-risk countries"),
        (len(at_risk) >= FLOORS["at_risk_anchors"], "fewer than 100 at-risk anchors"),
        (n_high >= FLOORS["high_anchors"], "fewer than 25 high-exposure anchors"),
        (n_other >= FLOORS["other_anchors"], "fewer than 70 comparison anchors"),
        (len(event_rows) >= FLOORS["incident_events"], "fewer than 10 incident events"),
        (len(event_countries) >= FLOORS["event_countries"], "fewer than five event countries"),
        (len(event_eras) >= FLOORS["event_eras"], "event onsets occur in fewer than two eras"),
        (e_other >= FLOORS["other_incident_events"],
         "fewer than three comparison-group incident events"),
    )
    failures = [message for passes, message in gates if not passes]
    analysis["sample_floor_failures"] = failures
    if failures:
        analysis.update(verdict="INCONCLUSIVE", reason="registered risk-set or incident-event floor failed")
        return analysis
    high_risk = e_high / n_high
    other_risk = e_other / n_other
    risk_ratio = high_risk / other_risk
    risk_diff = high_risk - other_risk
    if risk_ratio >= 2.0 and risk_diff >= 0.02 and e_high >= 4:
        verdict = "SUPPORTED"
    elif risk_ratio <= 1.0 and risk_diff <= 0:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    analysis.update({
        "high_risk": high_risk,
        "other_risk": other_risk,
        "risk_ratio": risk_ratio,
        "risk_difference": risk_diff,
        "verdict": verdict,
        "reason": "frozen descriptive five-year incident-onset risk contrast",
    })
    return analysis


def result_card(diagnostics: dict[str, Any]) -> str:
    a = diagnostics["analysis"]
    lines = [
        f"# {HID}", "", f"**Verdict: {a['verdict']}** — {a['reason']}", "",
        "Original JST R6 advanced-economy panel, before 1980. Descriptive risk comparison; "
        "no causal credit-policy effect is identified.", "",
        f"- Frozen candidates: {CANDIDATE_COUNT} country-anchors in 18 countries across 13 years; "
        f"{a['loan_valid_anchors']} had valid loan/GDP exposure.",
        f"- At-risk anchors: {a.get('at_risk_anchors', 'not evaluated')}; "
        f"incident onsets: {a.get('incident_events', 'not evaluated')}.",
        f"- High group: {a.get('high_incident_events', 'not evaluated')}/"
        f"{a.get('high_anchors', 'not evaluated')}; other group: "
        f"{a.get('other_incident_events', 'not evaluated')}/"
        f"{a.get('other_anchors', 'not evaluated')}.",
        f"- Original local parquet SHA-256: {SOURCE_SHA256}.",
        f"- Registration commit: {diagnostics['preregistration_commit']}.",
        f"- Metadata source-lock commit: {diagnostics['source_lock_commit']}.",
        "- One descriptive family; no p-value, causal, school, position, or policy-score credit.",
    ]
    if "risk_ratio" in a:
        lines.append(f"- Raw risk ratio: {a['risk_ratio']:.4f}; risk difference: "
                     f"{a['risk_difference']:.4f} (probability scale).")
    if a["sample_floor_failures"]:
        lines.extend(["", "Failed registered gates:"] +
                     [f"- {item}." for item in a["sample_floor_failures"]])
    lines.extend([
        "", "## Evidence boundary", "",
        "The original JST R6 data cover 18 advanced economies and are subject to "
        "CC BY-NC-SA 4.0 terms. Historical series may be spliced across archival "
        "sources. Crises and credit growth share macroeconomic causes; the raw "
        "contrast has no causal interpretation. The old post-1980 result is untouched.",
        "The repository contains no JST value rows. Replay needs a lawfully held "
        "local copy with the exact pinned SHA-256 and source attribution:",
        f"Jordà, Schularick and Taylor (2017). {DOC_URL}", "",
        f"Reproduce: python3 {RUNNER_REL} verify --source-parquet <local-JST-R6-parquet>", "",
    ])
    return "\n".join(lines)


def artifacts(registration: str, lock_commit: str, manifest: dict[str, Any],
              analysis: dict[str, Any], stamp: str) -> dict[str, bytes]:
    correction = {
        "disposition": "descriptive_calibration_only",
        "school_score_eligible": False,
        "school_score_credit": 0,
        "policy_score_eligible": False,
        "policy_score_credit": 0,
    }
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": analysis["verdict"],
        "method": "fixed-era top-quintile descriptive forward-onset risk ratio",
        "run_utc": stamp,
        "preregistration_commit": registration,
        "source_lock_commit": lock_commit,
        "source_sha256": SOURCE_SHA256,
        "key_roster_sha256": manifest["key_roster_sha256"],
        "analysis": analysis,
        "family_size": 1,
        "evidence_tier_recommendation": "calibration",
        "correction": correction,
        "limitations": [
            "Historical 18-economy advanced-country sample only.",
            "Raw risk contrast is descriptive, with no causal identification.",
            "Wars omitted by fixed anchor windows; common era shocks may still confound.",
            "Licensed JST values are not distributed in the repository.",
        ],
    }
    source = {
        "publisher": manifest["publisher"],
        "release": "R6",
        "source_url": SOURCE_URL,
        "documentation_url": DOC_URL,
        "source_sha256": SOURCE_SHA256,
        "source_lock_manifest": LOCK_REL,
        "source_lock_commit": lock_commit,
        "key_roster_sha256": manifest["key_roster_sha256"],
        "license": manifest["license"],
        "contains_source_values": False,
    }
    packet = {
        "packet_version": 1,
        "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL},
        "preregistration": {"commit": registration, "steelman": STEELMAN_REL,
                            "source_plan": PLAN_REL, "frozen_hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml"},
        "source": source,
        "reproduction": {"runner": RUNNER_REL,
                         "command": f"python3 {RUNNER_REL} verify --source-parquet <local-JST-R6-parquet>"},
        "gate": {"candidate_anchors": CANDIDATE_COUNT, "source_keys": EXPECTED_KEY_COUNT,
                 "anchor_years": manifest["anchor_years"], "floors": FLOORS,
                 "family_size": 1},
        "result": analysis,
        "correction": correction,
    }
    run_manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "status": analysis["verdict"],
        "runner": RUNNER_REL, "hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
        "preregistration_commit": registration, "source": source,
        "correction": correction,
    }
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), "
        "'verify', *sys.argv[1:]], cwd=root))\n"
    )
    return {
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode("utf-8"),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode("utf-8"),
        "result_card.md": result_card(diagnostics).encode("utf-8"),
        "replication.py": wrapper.encode("utf-8"),
    }


def run(path: Path, verify: bool) -> None:
    registration = registration_commit()
    manifest, lock_commit = committed_lock(path, registration)
    run_dir = ROOT / RUN_REL
    if verify:
        stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
        stamp = stored["run_utc"]
        if datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("run timestamp lacks timezone")
    else:
        if run_dir.exists():
            raise RuntimeError("run directory already exists; use verify")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    rows = load_fixed_values(path)
    analysis = analyze(rows)
    expected = artifacts(registration, lock_commit, manifest, analysis, stamp)
    if verify:
        if {p.name for p in run_dir.iterdir() if p.is_file()} != set(expected):
            raise RuntimeError("run artifact set differs from registered runner")
        for name, content in expected.items():
            if (run_dir / name).read_bytes() != content:
                raise RuntimeError(f"byte-exact replay mismatch: {name}")
        print(f"Verified {HID}: {analysis['verdict']} and all {len(expected)} artifacts")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        for name, content in expected.items():
            (run_dir / name).write_bytes(content)
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
            key_info = source_key_check(args.source_parquet)
            print(json.dumps({
                "value_access": False, "source_sha256": SOURCE_SHA256,
                "candidate_country_anchors": CANDIDATE_COUNT,
                "country_count": len(COUNTRIES), "anchor_years": ERA_ANCHORS,
                **key_info,
            }, indent=2, sort_keys=True))
        elif args.command == "source-lock":
            source_lock(args.source_parquet)
        else:
            run(args.source_parquet, verify=args.command == "verify")
    except (OSError, ValueError, RuntimeError, KeyError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
