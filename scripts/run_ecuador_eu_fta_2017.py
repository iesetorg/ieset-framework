#!/usr/bin/env python3
"""Frozen Ecuador–EU five-destination BACI descriptive registration.

`plan` accesses no outcome. `extract` requires an earlier registration commit;
`run` requires a later committed source slice. `verify` is byte-exact replay.
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
HID = "ecuador_eu_fta_five_destination_exports_2017"
RUNNER = "scripts/run_ecuador_eu_fta_2017.py"
SPEC = f"hypotheses/trade/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PLAN = "engine/audits/ecuador_eu_fta_source_plan_2026-10-10.md"
SLICE = "data/pinned_evidence/ecuador_eu_fta_2017.csv"
SOURCE_MANIFEST = "data/pinned_evidence/ecuador_eu_fta_2017.manifest.json"
RUN_DIR = f"engine/runs/{HID}"
REGISTRATION_FILES = (SPEC, STEELMAN, PLAN, RUNNER)
SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
SOURCE_MEMBER = "Gravity_V202211.csv"
SOURCE_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
SOURCE_DEFAULT = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
DATE_URL = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:22016X1229(02)"
ORIGINS = ("ECU", "ARG", "BOL", "BRA", "PRY", "URY")
DONORS = ORIGINS[1:]
DESTINATIONS = ("DEU", "ESP", "FRA", "ITA", "NLD")
YEARS = tuple(range(2012, 2020))
PRE = (2012, 2013, 2014, 2015)
POST = (2017, 2018, 2019)
PRETREND_MAX = 0.03
EFFECT_THRESHOLD = math.log(1.15)
SOURCE_FIELDS = ("source_row_number", "year", "iso3_o", "iso3_d",
                 "country_exists_o", "country_exists_d", "fta_wto", "tradeflow_baci")
EXPECTED_KEYS = {(o, d, y) for o in ORIGINS for d in DESTINATIONS for y in YEARS}
MAX_CUSTODY_ROWS = len(EXPECTED_KEYS) + 1


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
    return result


def git_bytes(revision: str, relative: str) -> bytes:
    return git("show", f"{revision}:{relative}").stdout


def first_addition(relative: str) -> str:
    result = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative)
    commits = result.stdout.decode().strip().splitlines()
    if not commits:
        raise RuntimeError(f"{relative} has no first-addition commit")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def registration_commit() -> str:
    additions = []
    for relative in REGISTRATION_FILES:
        path = ROOT / relative
        if not path.is_file() or git_bytes("HEAD", relative) != path.read_bytes():
            raise RuntimeError(f"commit unchanged registration before value access: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, source plan, and runner must first appear together")
    commit = additions[0]
    for relative in REGISTRATION_FILES:
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration changed after first addition: {relative}")
    if git("ls-tree", "-r", "--name-only", commit, "--", SLICE, SOURCE_MANIFEST, RUN_DIR).stdout.strip():
        raise RuntimeError("registration commit contains source outcome or run artifacts")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool01(value: str, field: str) -> int:
    if value.strip() in {"1", "1.0"}:
        return 1
    if value.strip() in {"0", "0.0"}:
        return 0
    raise ValueError(f"{field} is not explicit 0/1: {value!r}")


def extraction_rows(source_zip: Path) -> tuple[list[dict[str, str]], int, int, int]:
    """Extract only fixed keys, retaining one excess existing row as duplicate evidence."""
    selected: list[dict[str, str]] = []
    existing_total = raw_matches = excluded_nonexisting = 0
    with zipfile.ZipFile(source_zip) as archive:
        if SOURCE_MEMBER not in archive.namelist():
            raise ValueError(f"missing member: {SOURCE_MEMBER}")
        with archive.open(SOURCE_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader)
                needed = set(SOURCE_FIELDS) - {"source_row_number"}
                if not needed.issubset(header):
                    raise ValueError(f"missing CEPII columns: {sorted(needed - set(header))}")
                indices = {field: header.index(field) for field in needed}
                for ordinal, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        raise ValueError(f"malformed source record {ordinal}")
                    try:
                        year = int(values[indices["year"]])
                    except ValueError:
                        continue
                    origin = values[indices["iso3_o"]]
                    destination = values[indices["iso3_d"]]
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
                        selected.append({"source_row_number": str(ordinal), **{
                            field: values[indices[field]] for field in SOURCE_FIELDS
                            if field != "source_row_number"
                        }})
    selected.sort(key=lambda row: (
        row["iso3_o"], row["iso3_d"], int(row["year"]), int(row["source_row_number"])
    ))
    return selected, existing_total, raw_matches, excluded_nonexisting


def canonical_slice_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def extract(source_zip: Path) -> None:
    registration = registration_commit()
    if (ROOT / SLICE).exists() or (ROOT / SOURCE_MANIFEST).exists():
        raise RuntimeError("source custody files already exist; do not overwrite")
    if not source_zip.is_file() or sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("official CEPII ZIP unavailable or SHA-256 mismatch")
    rows, total, raw_matches, excluded = extraction_rows(source_zip)
    content = canonical_slice_bytes(rows)
    manifest = {
        "family": HID,
        "hypothesis_ids": [HID],
        "publisher": "cepii",
        "dataset": "Gravity V202211",
        "source_url": SOURCE_URL,
        "source_member": SOURCE_MEMBER,
        "source_zip_sha256": SOURCE_SHA256,
        "registration_commit": registration,
        "extractor": RUNNER,
        "slice_path": SLICE,
        "slice_sha256": hashlib.sha256(content).hexdigest(),
        "row_count": len(rows),
        "selected_existing_rows_total": total,
        "raw_key_matches_total": raw_matches,
        "excluded_nonexisting_rows": excluded,
        "selection_truncated": total > len(rows),
        "max_custody_rows": MAX_CUSTODY_ROWS,
        "expected_unique_keys": len(EXPECTED_KEYS),
        "row_keys": [f"{r['iso3_o']}>{r['iso3_d']}:{r['year']}" for r in rows],
        "columns": list(SOURCE_FIELDS),
        "tradeflow_baci_units": "thousands of current US dollars, directed origin to destination",
        "fta_wto_definition": "regional agreement status; not tariff intensity",
    }
    path = ROOT / SLICE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    (ROOT / SOURCE_MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Preserved {len(rows)} records; {total} existing, {excluded} nonexisting excluded")
    print("Commit source slice and manifest in a later commit before running.")


def committed_slice(registration: str) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    additions = [first_addition(relative) for relative in (SLICE, SOURCE_MANIFEST)]
    if len(set(additions)) != 1 or not strict_ancestor(registration, additions[0]):
        raise RuntimeError("slice and manifest must first appear together after registration")
    for relative in (SLICE, SOURCE_MANIFEST):
        current = (ROOT / relative).read_bytes()
        if git_bytes("HEAD", relative) != current or git_bytes(additions[0], relative) != current:
            raise RuntimeError(f"source custody changed after first addition: {relative}")
    if git("ls-tree", "-r", "--name-only", additions[0], "--", RUN_DIR).stdout.strip():
        raise RuntimeError("source-slice commit contains run artifacts")
    manifest = json.loads((ROOT / SOURCE_MANIFEST).read_text())
    content = (ROOT / SLICE).read_bytes()
    if (manifest.get("registration_commit") != registration
            or manifest.get("source_zip_sha256") != SOURCE_SHA256
            or manifest.get("source_member") != SOURCE_MEMBER
            or manifest.get("slice_sha256") != hashlib.sha256(content).hexdigest()):
        raise RuntimeError("source custody manifest mismatch")
    with io.StringIO(content.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise RuntimeError("source slice columns differ")
        rows = list(reader)
    ordered = sorted(rows, key=lambda row: (
        row["iso3_o"], row["iso3_d"], int(row["year"]), int(row["source_row_number"])
    ))
    total = manifest.get("selected_existing_rows_total")
    if (rows != ordered or manifest.get("row_count") != len(rows)
            or manifest.get("expected_unique_keys") != len(EXPECTED_KEYS)
            or manifest.get("max_custody_rows") != MAX_CUSTODY_ROWS
            or not isinstance(total, int) or total < len(rows)
            or manifest.get("selection_truncated") is not (total > len(rows))
            or manifest.get("row_keys") != [f"{r['iso3_o']}>{r['iso3_d']}:{r['year']}" for r in rows]):
        raise RuntimeError("source slice ordering or selection metadata mismatch")
    return rows, manifest, additions[0]


def verify_source(source_zip: Path) -> None:
    registration = registration_commit()
    _, manifest, _ = committed_slice(registration)
    if not source_zip.is_file() or sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("official CEPII ZIP unavailable or SHA-256 mismatch")
    rows, total, raw_matches, excluded = extraction_rows(source_zip)
    if (canonical_slice_bytes(rows) != (ROOT / SLICE).read_bytes()
            or total != manifest["selected_existing_rows_total"]
            or raw_matches != manifest["raw_key_matches_total"]
            or excluded != manifest["excluded_nonexisting_rows"]):
        raise RuntimeError("committed slice differs from byte-exact source re-extraction")
    print(f"Verified source: {len(rows)} preserved records from official archive")


def log_flow(row: dict[str, str]) -> float:
    try:
        value = float(row["tradeflow_baci"].strip())
    except ValueError as error:
        raise ValueError("BACI flow absent or nonnumeric") from error
    if not math.isfinite(value) or value < 0:
        raise ValueError("BACI flow nonfinite or negative")
    return math.log1p(value)


def slope(values: dict[int, float], years: tuple[int, ...]) -> float:
    mean_year = statistics.mean(years)
    denominator = sum((year - mean_year) ** 2 for year in years)
    return sum((year - mean_year) * values[year] for year in years) / denominator


def analyse(rows: list[dict[str, str]], manifest: dict[str, Any]) -> dict[str, Any]:
    if manifest["selection_truncated"]:
        return {"verdict": "INCONCLUSIVE", "reason": "source selection exceeded bounded custody slice"}
    keyed: dict[tuple[str, str, int], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["iso3_o"], row["iso3_d"], int(row["year"]))
        keyed.setdefault(key, []).append(row)
    values: dict[tuple[str, str], dict[int, float]] = {}
    try:
        for origin in ORIGINS:
            for destination in DESTINATIONS:
                values[(origin, destination)] = {}
                for year in YEARS:
                    key = (origin, destination, year)
                    matches = keyed.get(key, [])
                    if len(matches) != 1:
                        raise ValueError(f"{key} has {len(matches)} existing rows; expected one")
                    row = matches[0]
                    if (bool01(row["country_exists_o"], "country_exists_o") != 1
                            or bool01(row["country_exists_d"], "country_exists_d") != 1):
                        raise ValueError(f"{key} country-existence gate failed")
                    expected_fta = int(origin == "ECU" and year >= 2017)
                    if bool01(row["fta_wto"], "fta_wto") != expected_fta:
                        raise ValueError(f"{key} FTA status differs from registration")
                    values[(origin, destination)][year] = log_flow(row)
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE", "reason": f"source or outcome completeness gate failed: {error}"}

    pre_gap = {
        year: statistics.median(
            values[("ECU", destination)][year] -
            statistics.median(values[(origin, destination)][year] for origin in DONORS)
            for destination in DESTINATIONS
        ) for year in PRE
    }
    pretrend_slope = slope(pre_gap, PRE)
    pretrend = {
        "yearly_pooled_log_gaps": {str(y): pre_gap[y] for y in PRE},
        "pooled_slope_log_units_per_year": pretrend_slope,
        "max_abs_slope": PRETREND_MAX,
    }
    if abs(pretrend_slope) > PRETREND_MAX:
        return {"verdict": "INCONCLUSIVE", "reason": "registered pooled pretrend gate failed",
                "pretrend": pretrend}

    components: dict[str, dict[str, float]] = {}
    for destination in DESTINATIONS:
        changes = {
            origin: statistics.mean(values[(origin, destination)][y] for y in POST)
                    - statistics.mean(values[(origin, destination)][y] for y in PRE)
            for origin in ORIGINS
        }
        donor_change = statistics.median(changes[origin] for origin in DONORS)
        components[destination] = {
            "ecuador_log_change": changes["ECU"],
            "median_donor_log_change": donor_change,
            "descriptive_difference": changes["ECU"] - donor_change,
        }
    contrast = statistics.median(c["descriptive_difference"] for c in components.values())
    verdict = ("SUPPORTED" if contrast >= EFFECT_THRESHOLD else
               "REFUTED" if contrast <= -EFFECT_THRESHOLD else "PARTIAL")
    return {
        "verdict": verdict,
        "reason": "frozen pooled five-destination descriptive contrast under registered gates",
        "pretrend": pretrend,
        "destination_components_diagnostic_only": components,
        "contrast_log_units": contrast,
        "contrast_ratio": math.exp(contrast),
        "directional_threshold_log_units": EFFECT_THRESHOLD,
        "pre_years": list(PRE),
        "post_years": list(POST),
        "omitted_signing_year": 2016,
    }


def result_card(diagnostics: dict[str, Any]) -> str:
    a = diagnostics["analysis"]
    lines = [
        f"# {HID}", "", f"**Verdict: {a['verdict']}** — {a['reason']}", "",
        "One EU–Ecuador treaty-level descriptive merchandise-flow comparison, not a causal effect.", "",
        f"- Provisional application: 2017-01-01 ([Official Journal]({DATE_URL})).",
        "- ECU exports to DEU, ESP, FRA, ITA, NLD; donors ARG, BOL, BRA, PRY, URY.",
        "- Pre 2012–2015, post 2017–2019; 2016 omitted from averages.",
        f"- CEPII archive SHA-256: {SOURCE_SHA256}.",
        f"- Committed slice SHA-256: {diagnostics['slice_sha256']}.",
        f"- Registration commit: {diagnostics['preregistration_commit']}.",
        f"- Source-slice commit: {diagnostics['slice_commit']}.",
        "- Family size: one pooled test; destination components are diagnostics only.",
        "- Causal, featured, school, and policy-score credit: zero.",
    ]
    if "pretrend" in a:
        lines.append(f"- Pooled pretrend slope: {a['pretrend']['pooled_slope_log_units_per_year']:.6f} log units/year (absolute maximum 0.030000).")
    if "contrast_log_units" in a:
        lines.append(f"- Contrast: {a['contrast_log_units']:.6f} log units (ratio {a['contrast_ratio']:.4f}); threshold ±ln(1.15).")
    lines += ["", "## Limits", "",
              "Nominal BACI merchandise values mix prices and quantities. CEPII agreement status is not tariff intensity. "
              "The 2015–2016 EU preference bridge weakens treatment discontinuity; the 2016 Ecuador earthquake, "
              "commodity prices, exchange rates, and partner-specific product mix remain confounders. "
              "The same-destination donor comparison and pretrend gate do not identify a treaty effect.",
              "", f"Reproduce: python3 {RUNNER} verify", ""]
    return "\n".join(lines)


def artifacts(registration: str, source_commit: str, manifest: dict[str, Any],
              rows: list[dict[str, str]], stamp: str) -> dict[str, bytes]:
    analysis = analyse(rows, manifest)
    correction = {
        "disposition": "descriptive_calibration_only",
        "school_score_eligible": False,
        "school_score_credit": 0,
        "policy_score_eligible": False,
        "policy_score_credit": 0,
    }
    limitations = [
        "One descriptive treaty-level test; no causal policy effect identified.",
        "Nominal merchandise values, not real trade volumes or welfare.",
        "Five correlated EU destination components are not independent tests.",
        "The 2015–2016 preference bridge and Ecuador's 2016 earthquake limit interpretation.",
    ]
    source = {
        "publisher": "cepii", "dataset": "Gravity V202211",
        "source_url": SOURCE_URL, "source_zip_sha256": SOURCE_SHA256,
        "source_member": SOURCE_MEMBER, "slice_path": SLICE,
        "slice_sha256": manifest["slice_sha256"], "slice_commit": source_commit,
        "row_count": manifest["row_count"],
        "selected_existing_rows_total": manifest["selected_existing_rows_total"],
        "selection_truncated": manifest["selection_truncated"],
    }
    diagnostics = {
        "hypothesis_id": HID, "verdict": analysis["verdict"],
        "method": "descriptive median-of-five destination-matched log pre/post comparison",
        "run_utc": stamp, "preregistration_commit": registration,
        "slice_commit": source_commit, "slice_sha256": manifest["slice_sha256"],
        "selected_rows_total": manifest["selected_existing_rows_total"],
        "selection_truncated": manifest["selection_truncated"],
        "source_zip_sha256": SOURCE_SHA256, "runner": RUNNER,
        "analysis": analysis, "family_size": 1, "family_member_ids": [HID],
        "evidence_tier_recommendation": "calibration", "correction": correction,
        "limitations": limitations,
    }
    run_manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "status": analysis["verdict"],
        "runner": RUNNER, "hypothesis_snapshot": f"{RUN_DIR}/hypothesis.yaml",
        "preregistration_commit": registration, "source": source, "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "policy_id": "ec_eu_andean_fta_2016"},
        "preregistration": {"commit": registration, "steelman": STEELMAN,
                             "source_plan": PLAN, "frozen_hypothesis_snapshot": f"{RUN_DIR}/hypothesis.yaml"},
        "source": source,
        "reproduction": {"runner": RUNNER, "command": f"python3 {RUNNER} verify"},
        "gate": {"fixed_dyad_year_rows": len(EXPECTED_KEYS),
                 "treated_dyads": [f"ECU>{d}" for d in DESTINATIONS],
                 "donor_dyads": [f"{o}>{d}" for o in DONORS for d in DESTINATIONS],
                 "pre_years": list(PRE), "post_years": list(POST),
                 "omitted_signing_year": 2016,
                 "pretrend_max_abs_log_slope": PRETREND_MAX,
                 "pretrend": analysis.get("pretrend"), "family_size": 1},
        "result": analysis, "limitations": limitations, "correction": correction,
    }
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER}'), 'verify'], cwd=root))\n")
    output = {
        "hypothesis.yaml": (ROOT / SPEC).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode(),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": result_card(diagnostics).encode(),
        "replication.py": wrapper.encode(),
    }
    if "contrast_log_units" in analysis:
        chart = {
            "hypothesis_id": HID, "verdict": analysis["verdict"],
            "metric": "median of five EU destination-matched pre/post log export differences",
            "unit": "log units", "pre_years": list(PRE), "post_years": list(POST),
            "destination_components_diagnostic_only": analysis["destination_components_diagnostic_only"],
            "contrast_log_units": analysis["contrast_log_units"],
            "directional_threshold_log_units": EFFECT_THRESHOLD,
        }
        output["chart_data.json"] = (json.dumps(chart, indent=2, sort_keys=True) + "\n").encode()
    return output


def run(verify: bool) -> None:
    registration = registration_commit()
    rows, manifest, source_commit = committed_slice(registration)
    run_dir = ROOT / RUN_DIR
    if verify:
        stored = json.loads((run_dir / "diagnostics.json").read_text())
        stamp = stored.get("run_utc")
        if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("invalid stored run_utc")
    else:
        if run_dir.exists():
            raise RuntimeError("run directory already exists; use verify")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = artifacts(registration, source_commit, manifest, rows, stamp)
    if verify:
        if {p.name for p in run_dir.iterdir() if p.is_file()} != set(expected):
            raise RuntimeError("run artifact set differs from frozen runner")
        for name, content in expected.items():
            if (run_dir / name).read_bytes() != content:
                raise RuntimeError(f"byte-exact replication mismatch: {name}")
        print(f"Verified {HID}: {json.loads(expected['diagnostics.json'])['verdict']} and {len(expected)} artifacts")
    else:
        run_dir.mkdir(parents=True, exist_ok=False)
        for name, content in expected.items():
            (run_dir / name).write_bytes(content)
        print(f"{HID}: {json.loads(expected['diagnostics.json'])['verdict']}")


def plan() -> None:
    print(json.dumps({
        "hypothesis_id": HID, "value_access": False,
        "source_zip_sha256": SOURCE_SHA256,
        "source_manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "expected_existing_dyad_year_keys": len(EXPECTED_KEYS),
        "treated_origin": "ECU", "donor_origins": list(DONORS),
        "destinations": list(DESTINATIONS), "pre": list(PRE), "post": list(POST),
        "omitted_signing_year": 2016, "pretrend_max_abs_slope": PRETREND_MAX,
        "effect_threshold_log": EFFECT_THRESHOLD,
    }, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    extract_command = commands.add_parser("extract")
    extract_command.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    verify_source_command = commands.add_parser("verify-source")
    verify_source_command.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
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
