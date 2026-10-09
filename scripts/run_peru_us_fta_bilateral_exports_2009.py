#!/usr/bin/env python3
"""Registered, source-custodied descriptive test of USA -> PER BACI exports.

`plan` opens no outcome file. `extract` and `run` require the immutable first
registration commit; `run` also requires a separately committed small slice.
See the hypothesis YAML and source plan for the frozen design.
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
HID = "peru_us_fta_bilateral_exports_2009"
SPEC_REL = f"hypotheses/trade/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
PLAN_REL = f"engine/audits/{HID}_source_plan.md"
RUNNER_REL = f"scripts/run_{HID}.py"
SLICE_REL = f"data/pinned_evidence/{HID}.csv"
MANIFEST_REL = f"data/pinned_evidence/{HID}.manifest.json"
RUN_REL = f"engine/runs/{HID}"
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)

SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
SOURCE_MEMBER = "Gravity_V202211.csv"
SOURCE_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
SOURCE_DEFAULT = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
DESTINATIONS = ("ARG", "BOL", "BRA", "ECU", "PER", "PRY", "URY")
DONORS = tuple(country for country in DESTINATIONS if country != "PER")
YEARS = tuple(range(2004, 2015))
PRE = tuple(range(2004, 2009))
POST = tuple(range(2010, 2015))
EXPECTED_KEYS = {(destination, year) for destination in DESTINATIONS for year in YEARS}
MAX_CUSTODY_ROWS = len(EXPECTED_KEYS) + 1  # Preserve one extra row to prove an overfull selection.
SOURCE_FIELDS = (
    "source_row_number", "year", "iso3_o", "iso3_d", "country_exists_o",
    "country_exists_d", "fta_wto", "tradeflow_baci",
)
PRETREND_MAX = 0.03
EFFECT_THRESHOLD = math.log(1.15)


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, check=False
    )
    if check and result.returncode:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}"
        )
    return result


def git_bytes(rev: str, relative: str) -> bytes:
    return git("show", f"{rev}:{relative}").stdout


def first_addition(relative: str) -> str:
    result = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", relative)
    commits = result.stdout.decode().strip().splitlines()
    if not commits:
        raise RuntimeError(f"{relative} has no first-addition commit")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and git("merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def registration_commit() -> str:
    """Enforce immutable, pre-outcome first registration before value access."""
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
            raise RuntimeError(f"registered bytes changed after first addition: {relative}")
    if git("ls-tree", "-r", "--name-only", commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("run artifacts cannot appear in the registration commit")
    if git("ls-tree", "-r", "--name-only", commit, "--", SLICE_REL, MANIFEST_REL).stdout.strip():
        raise RuntimeError("the outcome slice cannot appear in the registration commit")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool01(value: str, field: str) -> bool:
    cleaned = value.strip()
    if cleaned in {"1", "1.0"}:
        return True
    if cleaned in {"0", "0.0"}:
        return False
    raise ValueError(f"{field} must be an explicit 0/1, found {value!r}")


def validate_structure(rows: list[dict[str, str]]) -> dict[tuple[str, int], dict[str, str]]:
    if len(rows) != len(EXPECTED_KEYS):
        raise ValueError(f"expected {len(EXPECTED_KEYS)} rows, found {len(rows)}")
    keyed: dict[tuple[str, int], dict[str, str]] = {}
    for row in rows:
        if row["iso3_o"] != "USA" or row["iso3_d"] not in DESTINATIONS:
            raise ValueError("slice includes an unregistered directed dyad")
        try:
            year = int(row["year"])
            source_row = int(row["source_row_number"])
        except ValueError as error:
            raise ValueError("noninteger year or source row number") from error
        if source_row < 2:
            raise ValueError("source row number precedes CSV data")
        key = (row["iso3_d"], year)
        if key not in EXPECTED_KEYS or key in keyed:
            raise ValueError(f"unexpected or duplicate dyad-year {key}")
        if not bool01(row["country_exists_o"], "country_exists_o"):
            raise ValueError(f"origin does not exist for {key}")
        if not bool01(row["country_exists_d"], "country_exists_d"):
            raise ValueError(f"destination does not exist for {key}")
        is_fta = bool01(row["fta_wto"], "fta_wto")
        expected_fta = row["iso3_d"] == "PER" and year >= 2009
        if is_fta != expected_fta:
            raise ValueError(f"unexpected FTA status for {key}: {row['fta_wto']!r}")
        keyed[key] = row
    if set(keyed) != EXPECTED_KEYS:
        raise ValueError("the fixed dyad-year grid is incomplete")
    return keyed


def extraction_rows(source_zip: Path) -> tuple[list[dict[str, str]], int]:
    """Keep a bounded raw selection, including structural anomalies, without interpreting BACI."""
    selected: list[dict[str, str]] = []
    selected_total = 0
    with zipfile.ZipFile(source_zip) as archive:
        if SOURCE_MEMBER not in archive.namelist():
            raise ValueError(f"missing source member: {SOURCE_MEMBER}")
        with archive.open(SOURCE_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as text:
                reader = csv.reader(text)
                header = next(reader)
                required = {field for field in SOURCE_FIELDS if field != "source_row_number"}
                if not required.issubset(header):
                    raise ValueError(f"missing CEPII columns: {sorted(required - set(header))}")
                indices = {field: header.index(field) for field in required}
                for source_row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        raise ValueError(f"malformed source row {source_row_number}")
                    if values[indices["iso3_o"]] != "USA":
                        continue
                    destination = values[indices["iso3_d"]]
                    if destination not in DESTINATIONS:
                        continue
                    try:
                        year = int(values[indices["year"]])
                    except ValueError:
                        continue
                    if year not in YEARS:
                        continue
                    selected_total += 1
                    if len(selected) < MAX_CUSTODY_ROWS:
                        selected.append({
                            "source_row_number": str(source_row_number),
                            **{field: values[indices[field]] for field in SOURCE_FIELDS if field != "source_row_number"},
                        })
    return sorted(selected, key=lambda row: (row["iso3_d"], int(row["year"]), int(row["source_row_number"]))), selected_total


def canonical_slice_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def extract(source_zip: Path) -> None:
    commit = registration_commit()  # Must run before opening any outcome source.
    if not source_zip.is_file():
        raise RuntimeError(f"source ZIP unavailable: {source_zip}")
    actual_sha = sha256_file(source_zip)
    if actual_sha != SOURCE_SHA256:
        raise RuntimeError(f"CEPII archive SHA-256 mismatch: {actual_sha}")
    rows, selected_total = extraction_rows(source_zip)
    slice_bytes = canonical_slice_bytes(rows)
    slice_sha = hashlib.sha256(slice_bytes).hexdigest()
    manifest = {
        "hypothesis_id": HID,
        "publisher": "cepii",
        "dataset": "Gravity V202211",
        "source_url": SOURCE_URL,
        "source_member": SOURCE_MEMBER,
        "source_zip_sha256": SOURCE_SHA256,
        "registration_commit": commit,
        "extractor": RUNNER_REL,
        "slice_path": SLICE_REL,
        "slice_sha256": slice_sha,
        "row_count": len(rows),
        "selected_rows_total": selected_total,
        "selection_truncated": selected_total > len(rows),
        "max_custody_rows": MAX_CUSTODY_ROWS,
        "row_keys": [f"USA>{row['iso3_d']}:{row['year']}" for row in rows],
        "columns": list(SOURCE_FIELDS),
        "tradeflow_baci_units": "thousands of current US dollars, directed origin to destination",
        "fta_wto_definition": "1 if CEPII records the country pair in a regional trade agreement; not tariff intensity",
        "country_exists_definition": "CEPII origin and destination country-existence flags",
        "source_row_number_definition": "one-based CSV record ordinal, including header as record 1",
    }
    path = ROOT / SLICE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(slice_bytes)
    (ROOT / MANIFEST_REL).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Preserved {len(rows)} selected rows ({selected_total} source matches); slice SHA-256 {slice_sha}")
    print("Commit the small slice and manifest before running the outcome analysis.")


def committed_slice(registration: str) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    additions = [first_addition(relative) for relative in (SLICE_REL, MANIFEST_REL)]
    if len(set(additions)) != 1 or not strict_ancestor(registration, additions[0]):
        raise RuntimeError("slice and manifest must first appear together in a later commit")
    for relative in (SLICE_REL, MANIFEST_REL):
        current = (ROOT / relative).read_bytes()
        if git_bytes("HEAD", relative) != current or git_bytes(additions[0], relative) != current:
            raise RuntimeError(f"source-custody file changed after first addition: {relative}")
    if git("ls-tree", "-r", "--name-only", additions[0], "--", RUN_REL).stdout.strip():
        raise RuntimeError("run artifacts cannot appear in the source-slice commit")
    manifest = json.loads((ROOT / MANIFEST_REL).read_text(encoding="utf-8"))
    slice_bytes = (ROOT / SLICE_REL).read_bytes()
    if manifest.get("source_zip_sha256") != SOURCE_SHA256 or manifest.get("source_member") != SOURCE_MEMBER:
        raise RuntimeError("source vintage does not match registration")
    if manifest.get("registration_commit") != registration:
        raise RuntimeError("slice was extracted against a different registration")
    if manifest.get("slice_sha256") != hashlib.sha256(slice_bytes).hexdigest():
        raise RuntimeError("slice SHA-256 does not match custody manifest")
    with io.StringIO(slice_bytes.decode("utf-8"), newline="") as text:
        reader = csv.DictReader(text)
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise RuntimeError("slice column order differs from registered source fields")
        rows = list(reader)
    ordered = sorted(rows, key=lambda row: (row["iso3_d"], int(row["year"]), int(row["source_row_number"])))
    if rows != ordered or manifest.get("row_count") != len(rows):
        raise RuntimeError("slice row order or manifest count differs from registration")
    total = manifest.get("selected_rows_total")
    if (not isinstance(total, int) or total < len(rows)
            or manifest.get("selection_truncated") is not (total > len(rows))
            or manifest.get("max_custody_rows") != MAX_CUSTODY_ROWS
            or len(rows) > MAX_CUSTODY_ROWS):
        raise RuntimeError("bounded source selection metadata differs from registration")
    if manifest.get("row_keys") != [f"USA>{row['iso3_d']}:{row['year']}" for row in rows]:
        raise RuntimeError("slice row keys differ from manifest")
    return rows, manifest, additions[0]


def verify_source(source_zip: Path) -> None:
    registration = registration_commit()
    _, manifest, _ = committed_slice(registration)
    if not source_zip.is_file():
        raise RuntimeError(f"source ZIP unavailable: {source_zip}")
    actual_sha = sha256_file(source_zip)
    if actual_sha != SOURCE_SHA256:
        raise RuntimeError(f"CEPII archive SHA-256 mismatch: {actual_sha}")
    reextracted_rows, selected_total = extraction_rows(source_zip)
    reextracted = canonical_slice_bytes(reextracted_rows)
    if reextracted != (ROOT / SLICE_REL).read_bytes():
        raise RuntimeError("committed slice differs byte-for-byte from raw CEPII re-extraction")
    if hashlib.sha256(reextracted).hexdigest() != manifest["slice_sha256"]:
        raise RuntimeError("re-extracted slice hash differs from custody manifest")
    if selected_total != manifest["selected_rows_total"]:
        raise RuntimeError("re-extracted selected-row total differs from custody manifest")
    print(f"Verified source custody: {selected_total} source matches, {len(reextracted_rows)} retained rows")


def log_flow(row: dict[str, str]) -> float:
    raw = row["tradeflow_baci"].strip()
    try:
        value = float(raw)
    except ValueError as error:
        raise ValueError("BACI flow is absent or nonnumeric") from error
    if not math.isfinite(value) or value < 0:
        raise ValueError("BACI flow is nonfinite or negative")
    return math.log1p(value)


def slope(values: dict[int, float]) -> float:
    # OLS of log flow on calendar year for 2004-2008; mean year = 2006.
    return sum((year - 2006) * values[year] for year in PRE) / 10.0


def analyse(rows: list[dict[str, str]], *, selection_truncated: bool = False) -> dict[str, Any]:
    if selection_truncated:
        return {"verdict": "INCONCLUSIVE", "reason": "registered dyad-year selection exceeds bounded custody slice"}
    try:
        keyed = validate_structure(rows)
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE", "reason": f"structural/treatment gate failed: {error}"}
    pre: dict[str, dict[int, float]] = {}
    try:
        for country in DESTINATIONS:
            pre[country] = {year: log_flow(keyed[country, year]) for year in PRE}
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE", "reason": f"pre outcome completeness gate failed: {error}"}
    slopes = {country: slope(pre[country]) for country in DESTINATIONS}
    slope_gap = slopes["PER"] - statistics.median(slopes[country] for country in DONORS)
    pretrend = {"peru_slope": slopes["PER"], "median_donor_slope": statistics.median(slopes[country] for country in DONORS), "gap": slope_gap, "max_abs_gap": PRETREND_MAX}
    if abs(slope_gap) > PRETREND_MAX:
        return {"verdict": "INCONCLUSIVE", "reason": "registered pretrend gate failed", "pretrend": pretrend}
    try:
        post = {
            country: {year: log_flow(keyed[country, year]) for year in POST}
            for country in DESTINATIONS
        }
        # 2009 is omitted from the means but still must have a complete value.
        for country in DESTINATIONS:
            log_flow(keyed[country, 2009])
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE", "reason": f"post outcome completeness gate failed: {error}", "pretrend": pretrend}
    changes = {
        country: statistics.mean(post[country].values()) - statistics.mean(pre[country].values())
        for country in DESTINATIONS
    }
    donor_median = statistics.median(changes[country] for country in DONORS)
    contrast = changes["PER"] - donor_median
    if contrast >= EFFECT_THRESHOLD:
        verdict = "SUPPORTED"
    elif contrast <= -EFFECT_THRESHOLD:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return {
        "verdict": verdict,
        "reason": "fixed-donor descriptive contrast under the registered gate",
        "pretrend": pretrend,
        "peru_log_change": changes["PER"],
        "median_donor_log_change": donor_median,
        "contrast_log_units": contrast,
        "contrast_ratio": math.exp(contrast),
        "directional_threshold_log_units": EFFECT_THRESHOLD,
        "donor_log_changes": {country: changes[country] for country in DONORS},
        "pre_years": list(PRE),
        "post_years": list(POST),
        "omitted_year": 2009,
    }


def card(diagnostics: dict[str, Any]) -> str:
    analysis = diagnostics["analysis"]
    lines = [
        f"# {HID}", "", f"**Verdict: {analysis['verdict']}** — {analysis['reason']}", "",
        "This verdict tests a descriptive USA → PER merchandise-flow contrast. It does not identify the TPA's causal effect or welfare impact.", "",
        "- Agreement effective: 2009-02-01.",
        "- Pre: 2004–2008; post: 2010–2014; 2009 excluded from means.",
        "- Donors: USA → ARG, BOL, BRA, ECU, PRY, URY; fixed before outcome access.",
        f"- CEPII source archive SHA-256: `{SOURCE_SHA256}`.",
        f"- Small-slice SHA-256: `{diagnostics['slice_sha256']}`.",
        f"- Registration commit: `{diagnostics['preregistration_commit']}`.",
        f"- Source slice commit: `{diagnostics['slice_commit']}`.",
        "- School score credit: zero.",
    ]
    if "pretrend" in analysis:
        lines.append(f"- Pretrend gap: {analysis['pretrend']['gap']:.6f} log units/year; maximum absolute gap 0.030000.")
    if "contrast_log_units" in analysis:
        lines.append(f"- Registered contrast: {analysis['contrast_log_units']:.6f} log units (ratio {analysis['contrast_ratio']:.4f}); threshold ±ln(1.15).")
    lines += [
        "", "## Limits", "",
        "Nominal BACI goods values mix volume and price changes. The countries differ in demand, product composition and policy context; the 2008–2009 crisis overlaps the event. CEPII `fta_wto` is agreement status, not measured tariff intensity. One treaty contributes one test.",
        "", f"Reproduce: `python3 {RUNNER_REL} verify`", "",
    ]
    return "\n".join(lines)


def run(verify: bool = False) -> None:
    registration = registration_commit()
    rows, manifest, slice_commit = committed_slice(registration)
    analysis = analyse(rows, selection_truncated=manifest["selection_truncated"])
    run_dir = ROOT / RUN_REL
    if verify:
        stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
        stamp = stored.get("run_utc")
        if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("stored run_utc is invalid")
    else:
        if run_dir.exists():
            raise RuntimeError("run directory already exists; use verify rather than overwriting results")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    limitations = [
        "Descriptive treaty-level association only; no causal policy effect identified.",
        "Nominal merchandise values, not real trade volumes or welfare.",
        "Only one independent treaty event; donor dyads are not independent tests.",
    ]
    correction = {
        "disposition": "descriptive_calibration_only",
        "school_score_eligible": False,
        "school_score_credit": 0,
    }
    diagnostics = {
        "hypothesis_id": HID,
        "verdict": analysis["verdict"],
        "method": "descriptive fixed-donor log pre/post comparison, no causal identification",
        "run_utc": stamp,
        "preregistration_commit": registration,
        "slice_commit": slice_commit,
        "slice_sha256": manifest["slice_sha256"],
        "selected_rows_total": manifest["selected_rows_total"],
        "selection_truncated": manifest["selection_truncated"],
        "source_zip_sha256": SOURCE_SHA256,
        "runner": RUNNER_REL,
        "analysis": analysis,
        "evidence_tier_recommendation": "calibration",
        "correction": correction,
        "limitations": limitations,
    }
    run_manifest = {
        "hypothesis_id": HID,
        "run_utc": stamp,
        "status": analysis["verdict"],
        "runner": RUNNER_REL,
        "hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
        "preregistration_commit": registration,
        "source": {
            "publisher": "cepii",
            "dataset": "Gravity V202211",
            "source_url": SOURCE_URL,
            "source_zip_sha256": SOURCE_SHA256,
            "source_member": SOURCE_MEMBER,
            "slice_path": SLICE_REL,
            "slice_sha256": manifest["slice_sha256"],
            "slice_commit": slice_commit,
            "row_count": manifest["row_count"],
            "selected_rows_total": manifest["selected_rows_total"],
            "selection_truncated": manifest["selection_truncated"],
        },
        "correction": correction,
    }
    packet = {
        "packet_version": 1,
        "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "policy_id": "pe_us_fta_implementation_2009"},
        "preregistration": {
            "commit": registration,
            "steelman": STEELMAN_REL,
            "source_plan": PLAN_REL,
            "frozen_hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
        },
        "source": run_manifest["source"],
        "reproduction": {"runner": RUNNER_REL, "command": f"python3 {RUNNER_REL} verify"},
        "gate": {
            "fixed_dyad_year_rows": len(EXPECTED_KEYS),
            "directed_treated_dyad": "USA>PER",
            "donor_dyads": [f"USA>{country}" for country in DONORS],
            "pre_years": list(PRE),
            "post_years": list(POST),
            "pretrend_max_abs_log_slope_gap": PRETREND_MAX,
            "pretrend": analysis.get("pretrend"),
        },
        "result": analysis,
        "limitations": limitations,
        "correction": correction,
    }
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\n"
        "import subprocess\n"
        "import sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), 'verify'], cwd=root))\n"
    )
    artifacts: dict[str, bytes] = {
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode("utf-8"),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode("utf-8"),
        "result_card.md": card(diagnostics).encode("utf-8"),
        "replication.py": wrapper.encode("utf-8"),
    }
    if "contrast_log_units" in analysis:
        chart = {
            "hypothesis_id": HID,
            "verdict": analysis["verdict"],
            "metric": "pre/post change in mean log1p nominal BACI exports",
            "unit": "log units",
            "pre_years": list(PRE),
            "post_years": list(POST),
            "points": [
                {"destination": country, "treated": country == "PER", "log_change": (
                    analysis["peru_log_change"] if country == "PER"
                    else analysis["donor_log_changes"][country]
                )}
                for country in DESTINATIONS
            ],
            "donor_median_log_change": analysis["median_donor_log_change"],
            "contrast_log_units": analysis["contrast_log_units"],
            "directional_threshold_log_units": EFFECT_THRESHOLD,
        }
        artifacts["chart_data.json"] = (json.dumps(chart, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if verify:
        if {path.name for path in run_dir.iterdir() if path.is_file()} != set(artifacts):
            raise RuntimeError("run artifact set differs from the registered runner output")
        for relative, expected_bytes in artifacts.items():
            if (run_dir / relative).read_bytes() != expected_bytes:
                raise RuntimeError(f"replication mismatch in {relative}")
        print(f"Verified {HID}: {analysis['verdict']} and all {len(artifacts)} artifacts")
        return
    run_dir.mkdir(parents=True, exist_ok=False)
    for relative, content in artifacts.items():
        (run_dir / relative).write_bytes(content)
    print(f"{HID}: {analysis['verdict']}; inspect {RUN_REL}/ before committing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="print frozen settings without opening outcome files")
    extractor = commands.add_parser("extract", help="extract registered small slice after preregistration commit")
    extractor.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    source_verifier = commands.add_parser("verify-source", help="compare committed slice with official ZIP after registration")
    source_verifier.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    commands.add_parser("run", help="analyse committed small slice after registration")
    commands.add_parser("verify", help="recompute and compare existing result artifacts")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            print(json.dumps({
                "hypothesis_id": HID, "effective_date": "2009-02-01",
                "primary_dyad": "USA>PER", "donor_dyads": [f"USA>{d}" for d in DONORS],
                "years": [YEARS[0], YEARS[-1]], "pre": list(PRE), "post": list(POST),
                "source_zip_sha256": SOURCE_SHA256, "slice_rows": len(EXPECTED_KEYS),
                "pretrend_max_abs_slope_gap": PRETREND_MAX,
                "directional_log_threshold": EFFECT_THRESHOLD,
                "value_access": False,
            }, indent=2, sort_keys=True))
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
