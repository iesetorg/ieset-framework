#!/usr/bin/env python3
"""Blind two-commit CEPII BACI test for the Korea–EU5 treaty-flow claim.

`plan` reads no outcome. `extract` requires the exact committed registration;
`run` requires a later committed source slice. `verify` and `verify-source`
replay the complete result and source custody byte for byte.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
HID = "korea_eu_fta_eu5_baci_exports_2011_v2"
POLICY_REL = "policies/kr_eu_fta_provisional_application_2011.yaml"
SPEC_REL = f"hypotheses/trade/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
PLAN_REL = "engine/audits/korea_eu_fta_eu5_baci_2026_source_plan.md"
RUNNER_REL = "scripts/run_korea_eu_fta_eu5_baci_2026.py"
REGISTRATION_FILES = (POLICY_REL, SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)
SLICE_REL = "data/pinned_evidence/korea_eu_fta_eu5_baci_2011.csv"
SOURCE_MANIFEST_REL = "data/pinned_evidence/korea_eu_fta_eu5_baci_2011.manifest.json"
RUN_REL = f"engine/runs/{HID}"
SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
SOURCE_MEMBER = "Gravity_V202211.csv"
SOURCE_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
SOURCE_DEFAULT = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
ORIGINS = ("KOR", "JPN", "TWN", "CHN", "MYS", "THA", "IDN", "VNM", "IND")
DONORS = ORIGINS[1:]
DESTINATIONS = ("DEU", "FRA", "ITA", "ESP", "NLD")
YEARS = tuple(range(2007, 2016))
PRE = (2007, 2008, 2009, 2010)
POST = (2012, 2013, 2014, 2015)
EVENT_YEAR = 2011
EFFECT_THRESHOLD = math.log(1.15)
PRETREND_MAX = 0.03
EXPECTED_KEYS = {(origin, destination, year)
                 for origin in ORIGINS for destination in DESTINATIONS for year in YEARS}
MAX_CUSTODY_ROWS = len(EXPECTED_KEYS) + 1
SOURCE_FIELDS = ("source_row_number", "year", "iso3_o", "iso3_d",
                 "country_exists_o", "country_exists_d", "fta_wto", "tradeflow_baci")


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.decode(errors='replace').strip()}")
    return result


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    result = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative)
    commits = result.stdout.decode().strip().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f"expected one first-addition commit for {relative}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def registration_commit() -> str:
    additions = []
    for relative in REGISTRATION_FILES:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing registered file: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("policy, hypothesis, steelman, plan and runner must first appear together")
    commit = additions[0]
    for relative in REGISTRATION_FILES:
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registered bytes changed since first addition: {relative}")
    for relative in (SLICE_REL, SOURCE_MANIFEST_REL):
        if git("ls-tree", "-r", "--name-only", commit, "--", relative).stdout.strip():
            raise RuntimeError("source values cannot appear in the registration commit")
    if git("ls-tree", "-r", "--name-only", commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("run artifacts cannot appear in the registration commit")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool01(value: str, field: str) -> int:
    if value.strip() in ("1", "1.0"):
        return 1
    if value.strip() in ("0", "0.0"):
        return 0
    raise ValueError(f"{field} must be explicit 0/1, found {value!r}")


def extraction_rows(source_zip: Path) -> tuple[list[dict[str, str]], int, int, int]:
    selected: list[dict[str, str]] = []
    existing_total = raw_matches = excluded_nonexisting = 0
    with zipfile.ZipFile(source_zip) as archive:
        if SOURCE_MEMBER not in archive.namelist():
            raise ValueError(f"missing source member: {SOURCE_MEMBER}")
        with archive.open(SOURCE_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader)
                needed = set(SOURCE_FIELDS) - {"source_row_number"}
                if not needed.issubset(header):
                    raise ValueError(f"missing source columns: {sorted(needed - set(header))}")
                indices = {field: header.index(field) for field in needed}
                for row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        raise ValueError(f"malformed source row {row_number}")
                    origin = values[indices["iso3_o"]]
                    destination = values[indices["iso3_d"]]
                    try:
                        year = int(values[indices["year"]])
                    except ValueError:
                        continue
                    if (origin, destination, year) not in EXPECTED_KEYS:
                        continue
                    raw_matches += 1
                    try:
                        exists = (bool01(values[indices["country_exists_o"]], "country_exists_o") == 1
                                  and bool01(values[indices["country_exists_d"]], "country_exists_d") == 1)
                    except ValueError:
                        exists = False
                    if not exists:
                        excluded_nonexisting += 1
                        continue
                    existing_total += 1
                    if len(selected) < MAX_CUSTODY_ROWS:
                        selected.append({
                            "source_row_number": str(row_number),
                            **{field: values[indices[field]] for field in SOURCE_FIELDS
                               if field != "source_row_number"},
                        })
    selected.sort(key=lambda r: (r["iso3_o"], r["iso3_d"], int(r["year"]),
                                 int(r["source_row_number"])))
    return selected, existing_total, raw_matches, excluded_nonexisting


def canonical_slice_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def extract(source_zip: Path) -> None:
    registration = registration_commit()
    if (ROOT / SLICE_REL).exists() or (ROOT / SOURCE_MANIFEST_REL).exists():
        raise RuntimeError("source custody files already exist; do not overwrite")
    if not source_zip.is_file() or sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("official CEPII source ZIP absent or SHA-256 mismatch")
    rows, existing_total, raw_matches, excluded = extraction_rows(source_zip)
    content = canonical_slice_bytes(rows)
    manifest = {
        "hypothesis_id": HID,
        "publisher": "CEPII",
        "source_url": SOURCE_URL,
        "source_member": SOURCE_MEMBER,
        "source_zip_sha256": SOURCE_SHA256,
        "registration_commit": registration,
        "extractor": RUNNER_REL,
        "slice_path": SLICE_REL,
        "slice_sha256": hashlib.sha256(content).hexdigest(),
        "columns": list(SOURCE_FIELDS),
        "row_count": len(rows),
        "selected_existing_rows_total": existing_total,
        "raw_key_matches_total": raw_matches,
        "excluded_nonexisting_rows": excluded,
        "selection_truncated": existing_total > len(rows),
        "max_custody_rows": MAX_CUSTODY_ROWS,
        "expected_unique_keys": len(EXPECTED_KEYS),
        "row_keys": [f"{r['iso3_o']}>{r['iso3_d']}:{r['year']}" for r in rows],
        "tradeflow_baci_units": "thousands of current US dollars, directed origin to destination",
    }
    for relative, data in ((SLICE_REL, content),
                           (SOURCE_MANIFEST_REL, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())):
        path = ROOT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"Extracted {len(rows)} retained source rows; {existing_total} existing matches; "
          f"{len(EXPECTED_KEYS)} required keys")


def committed_slice(registration: str) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    additions = [first_addition(path) for path in (SLICE_REL, SOURCE_MANIFEST_REL)]
    if len(set(additions)) != 1 or not strict_ancestor(registration, additions[0]):
        raise RuntimeError("source slice and manifest need one later commit")
    source_commit = additions[0]
    for relative in (SLICE_REL, SOURCE_MANIFEST_REL):
        if git_bytes(source_commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"source custody bytes changed since commit: {relative}")
    if git("ls-tree", "-r", "--name-only", source_commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("result cannot appear in the source-lock commit")
    manifest = json.loads((ROOT / SOURCE_MANIFEST_REL).read_text(encoding="utf-8"))
    content = (ROOT / SLICE_REL).read_bytes()
    if (manifest.get("registration_commit") != registration
            or manifest.get("source_zip_sha256") != SOURCE_SHA256
            or manifest.get("source_member") != SOURCE_MEMBER
            or manifest.get("slice_sha256") != hashlib.sha256(content).hexdigest()
            or manifest.get("expected_unique_keys") != len(EXPECTED_KEYS)
            or manifest.get("max_custody_rows") != MAX_CUSTODY_ROWS):
        raise RuntimeError("source custody manifest mismatch")
    with io.StringIO(content.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise RuntimeError("source slice column order mismatch")
        rows = list(reader)
    ordered = sorted(rows, key=lambda r: (r["iso3_o"], r["iso3_d"], int(r["year"]),
                                          int(r["source_row_number"])))
    if (rows != ordered or len(rows) != manifest.get("row_count")
            or len(rows) > MAX_CUSTODY_ROWS
            or manifest.get("row_keys") != [f"{r['iso3_o']}>{r['iso3_d']}:{r['year']}" for r in rows]
            or manifest.get("selection_truncated") is not
            (manifest.get("selected_existing_rows_total", 0) > len(rows))):
        raise RuntimeError("source slice ordering, row count or selection mismatch")
    return rows, manifest, source_commit


def verify_source(source_zip: Path) -> None:
    registration = registration_commit()
    _, manifest, _ = committed_slice(registration)
    if not source_zip.is_file() or sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("official CEPII source ZIP absent or SHA-256 mismatch")
    rows, existing_total, raw_matches, excluded = extraction_rows(source_zip)
    if canonical_slice_bytes(rows) != (ROOT / SLICE_REL).read_bytes():
        raise RuntimeError("committed source slice differs from exact ZIP re-extraction")
    if (existing_total != manifest["selected_existing_rows_total"]
            or raw_matches != manifest["raw_key_matches_total"]
            or excluded != manifest["excluded_nonexisting_rows"]):
        raise RuntimeError("source row-selection counts differ on replay")
    print(f"Verified source custody: {existing_total} existing rows, {len(rows)} retained")


def slope(values: dict[int, float], years: tuple[int, ...]) -> float:
    mean_year = statistics.mean(years)
    return sum((year - mean_year) * values[year] for year in years) / sum(
        (year - mean_year) ** 2 for year in years)


def analyse(rows: list[dict[str, str]], manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest["selection_truncated"] or manifest["selected_existing_rows_total"] != len(EXPECTED_KEYS):
        return {"verdict": "INCONCLUSIVE", "reason": "bounded source selection is incomplete or duplicated"}
    keyed: dict[tuple[str, str, int], list[dict[str, str]]] = {}
    for row in rows:
        try:
            key = (row["iso3_o"], row["iso3_d"], int(row["year"]))
        except ValueError:
            return {"verdict": "INCONCLUSIVE", "reason": "malformed source year"}
        keyed.setdefault(key, []).append(row)
    aggregates: dict[str, dict[int, float]] = {origin: {} for origin in ORIGINS}
    try:
        for origin in ORIGINS:
            for year in YEARS:
                total = 0.0
                for destination in DESTINATIONS:
                    key = (origin, destination, year)
                    matches = keyed.get(key, [])
                    if len(matches) != 1:
                        raise ValueError(f"{key} has {len(matches)} existing source rows")
                    row = matches[0]
                    if (bool01(row["country_exists_o"], "country_exists_o") != 1
                            or bool01(row["country_exists_d"], "country_exists_d") != 1):
                        raise ValueError(f"{key} country-existence flag failed")
                    expected_fta = int(origin == "KOR" and year > EVENT_YEAR)
                    if bool01(row["fta_wto"], "fta_wto") != expected_fta:
                        raise ValueError(f"{key} agreement status changed")
                    try:
                        value = float(row["tradeflow_baci"].strip())
                    except ValueError as error:
                        raise ValueError(f"{key} missing or nonnumeric BACI flow") from error
                    if not math.isfinite(value) or value < 0:
                        raise ValueError(f"{key} nonfinite or negative BACI flow")
                    total += value
                aggregates[origin][year] = math.log1p(total)
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE", "reason": f"source/treatment/outcome gate failed: {error}"}
    slopes = {origin: slope(aggregates[origin], PRE) for origin in ORIGINS}
    donor_slope = statistics.median(slopes[origin] for origin in DONORS)
    gap = slopes["KOR"] - donor_slope
    pretrend = {"korea_slope": slopes["KOR"], "median_donor_slope": donor_slope,
                "gap": gap, "max_abs_gap": PRETREND_MAX}
    if abs(gap) > PRETREND_MAX:
        return {"verdict": "INCONCLUSIVE", "reason": "registered pretrend gate failed",
                "pretrend": pretrend}
    changes = {origin: statistics.mean(aggregates[origin][y] for y in POST)
               - statistics.mean(aggregates[origin][y] for y in PRE) for origin in ORIGINS}
    donor_change = statistics.median(changes[origin] for origin in DONORS)
    contrast = changes["KOR"] - donor_change
    verdict = ("SUPPORTED" if contrast >= EFFECT_THRESHOLD else
               "REFUTED" if contrast <= -EFFECT_THRESHOLD else "PARTIAL")
    return {
        "verdict": verdict,
        "reason": "fixed-EU5, fixed-donor descriptive contrast under registered gates",
        "pretrend": pretrend,
        "korea_log_change": changes["KOR"],
        "median_donor_log_change": donor_change,
        "contrast_log_units": contrast,
        "contrast_ratio": math.exp(contrast),
        "directional_threshold_log_units": EFFECT_THRESHOLD,
        "donor_log_changes": {origin: changes[origin] for origin in DONORS},
        "pre_years": list(PRE),
        "post_years": list(POST),
        "omitted_event_year": EVENT_YEAR,
    }


def result_card(diagnostics: dict[str, Any]) -> str:
    analysis = diagnostics["analysis"]
    lines = [
        f"# {HID}", "", f"**Verdict: {analysis['verdict']}** — {analysis['reason']}", "",
        "KOR-origin nominal merchandise exports to DEU, FRA, ITA, ESP and NLD,",
        "compared with the same destinations for eight Asian origins.", "",
        "- EU–Korea FTA provisionally applied 1 July 2011 (European Commission).",
        "- Pre: 2007–2010; post: 2012–2015; 2011 omitted from means.",
        f"- Donor origins: {', '.join(DONORS)}.",
        f"- CEPII source ZIP SHA-256: {SOURCE_SHA256}.",
        f"- Committed slice SHA-256: {diagnostics['slice_sha256']}.",
        f"- Registration commit: {diagnostics['preregistration_commit']}.",
        f"- Slice commit: {diagnostics['slice_commit']}.",
        "- School, policy, featured and causal credit: zero.",
    ]
    if "pretrend" in analysis:
        lines.append(f"- Pretrend slope gap: {analysis['pretrend']['gap']:.6f} "
                     "log units/year; maximum absolute gap 0.030000.")
    if "contrast_log_units" in analysis:
        lines.append(f"- Registered contrast: {analysis['contrast_log_units']:.6f} "
                     f"log units (ratio {analysis['contrast_ratio']:.4f}); threshold ±ln(1.15).")
    lines += ["", "## Limits", "",
              "BACI nominal values mix prices and quantities. The five destinations are a fixed subset of "
              "the EU. The 2008 crisis, sector mix, currency changes, and overlapping KOR–USA treaty "
              "can move the contrast. This is exploratory descriptive calibration, not causal evidence.",
              "", f"Reproduce: python3 {RUNNER_REL} verify", ""]
    return "\n".join(lines)


def artifacts(registration: str, source_commit: str, manifest: dict[str, Any],
              rows: list[dict[str, str]], stamp: str) -> dict[str, bytes]:
    analysis = analyse(rows, manifest)
    correction = {"disposition": "descriptive_calibration_only",
                  "school_score_eligible": False, "school_score_credit": 0,
                  "policy_score_eligible": False, "policy_score_credit": 0}
    limitations = [
        "Exploratory descriptive contrast; no causal treaty effect identified.",
        "Nominal goods values mix prices and quantities; only five EU destinations are covered.",
        "Other FTA cases were previously screened; KOR–USA timing and the 2008 crisis overlap.",
    ]
    source = {"publisher": "CEPII", "dataset": "Gravity V202211", "source_url": SOURCE_URL,
              "source_zip_sha256": SOURCE_SHA256, "source_member": SOURCE_MEMBER,
              "slice_path": SLICE_REL, "slice_sha256": manifest["slice_sha256"],
              "slice_commit": source_commit, "row_count": manifest["row_count"],
              "selected_existing_rows_total": manifest["selected_existing_rows_total"],
              "selection_truncated": manifest["selection_truncated"]}
    diagnostics = {"hypothesis_id": HID, "verdict": analysis["verdict"],
                   "method": "descriptive fixed-EU5 summed BACI log pre/post comparison",
                   "run_utc": stamp, "preregistration_commit": registration,
                   "slice_commit": source_commit, "slice_sha256": manifest["slice_sha256"],
                   "source_zip_sha256": SOURCE_SHA256, "runner": RUNNER_REL,
                   "analysis": analysis, "evidence_tier_recommendation": "calibration",
                   "correction": correction, "limitations": limitations}
    run_manifest = {"hypothesis_id": HID, "run_utc": stamp, "status": analysis["verdict"],
                    "runner": RUNNER_REL, "hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
                    "preregistration_commit": registration, "source": source,
                    "correction": correction}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": HID, "path": SPEC_REL,
                             "policy_id": "kr_eu_fta_provisional_application_2011"},
              "preregistration": {"commit": registration, "steelman": STEELMAN_REL,
                                  "source_plan": PLAN_REL,
                                  "frozen_hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml"},
              "source": source, "reproduction": {"runner": RUNNER_REL,
                                                 "command": f"python3 {RUNNER_REL} verify"},
              "gate": {"fixed_directed_cells": len(EXPECTED_KEYS),
                       "origins": list(ORIGINS), "destinations": list(DESTINATIONS),
                       "pre_years": list(PRE), "post_years": list(POST),
                       "pretrend_max_abs_log_slope_gap": PRETREND_MAX,
                       "pretrend": analysis.get("pretrend")},
              "result": analysis, "limitations": limitations, "correction": correction}
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), "
               "'verify'], cwd=root))\n")
    return {
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode(),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": result_card(diagnostics).encode(),
        "replication.py": wrapper.encode(),
    }


def run(verify: bool) -> None:
    registration = registration_commit()
    rows, manifest, source_commit = committed_slice(registration)
    run_dir = ROOT / RUN_REL
    if verify:
        stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
        stamp = stored.get("run_utc")
        if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("stored run UTC stamp invalid")
    else:
        if run_dir.exists():
            raise RuntimeError("run directory exists; use verify")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = artifacts(registration, source_commit, manifest, rows, stamp)
    if verify:
        if {p.name for p in run_dir.iterdir() if p.is_file()} != set(expected):
            raise RuntimeError("run artifact set differs")
        for name, content in expected.items():
            if (run_dir / name).read_bytes() != content:
                raise RuntimeError(f"byte-exact replay failed: {name}")
        print(f"Verified {HID}: {json.loads(expected['diagnostics.json'])['verdict']} "
              f"and all {len(expected)} artifacts")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        for name, content in expected.items():
            (run_dir / name).write_bytes(content)
        print(f"{HID}: {json.loads(expected['diagnostics.json'])['verdict']}")


def plan() -> None:
    print(json.dumps({"hypothesis_id": HID, "value_access": False,
                      "source_zip_sha256": SOURCE_SHA256,
                      "source_manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
                      "fixed_directed_cells": len(EXPECTED_KEYS), "origins": list(ORIGINS),
                      "destinations": list(DESTINATIONS), "years": list(YEARS),
                      "pre": list(PRE), "post": list(POST),
                      "event_year_fta_status": 0,
                      "pretrend_max_abs_slope_gap": PRETREND_MAX,
                      "effect_threshold_log": EFFECT_THRESHOLD}, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    extraction = commands.add_parser("extract")
    extraction.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    source_replay = commands.add_parser("verify-source")
    source_replay.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    commands.add_parser("run")
    commands.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            plan()
        elif args.command == "extract":
            extract(args.source_zip)
        elif args.command == "verify-source":
            verify_source(args.source_zip)
        else:
            run(verify=args.command == "verify")
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
