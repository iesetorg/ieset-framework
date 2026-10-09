#!/usr/bin/env python3
"""Frozen Vietnam WTO 2007 descriptive BACI test with source custody.

`plan` reads no flows. `extract` requires the committed first-addition
registration. `run` requires a later committed source slice. `verify-source`
and `verify` replay the source and result bytes, respectively.
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
HID = "vietnam_wto_2007_baci_export_basket_peer_change"
RUNNER_REL = f"scripts/run_{HID}.py"
SPEC_REL = f"hypotheses/trade/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
PLAN_REL = "engine/audits/vietnam_wto_2007_baci_export_basket_source_plan.md"
ERRATUM_NOTE_REL = "engine/audits/vietnam_wto_2007_baci_export_basket_source_census_erratum.md"
PATH_ERRATUM_COMMIT = "bebb591ff7cec043a054b0c3df65bfec55e14e82"
SLICE_REL = f"data/pinned_evidence/{HID}.csv"
SLICE_MANIFEST_REL = f"data/pinned_evidence/{HID}.manifest.json"
RUN_REL = f"engine/runs/{HID}"
SOURCE_DEFAULT = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
SOURCE_MEMBER = "Gravity_V202211.csv"
SOURCE_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
POLICY_URL = "https://www.wto.org/english/thewto_e/acc_e/a1_vietnam_e.htm"
ORIGINS = ("VNM", "THA", "MYS", "IDN", "PHL")
DONORS = ORIGINS[1:]
DESTINATIONS = ("USA", "CAN", "FRA", "DEU", "GBR", "ITA", "ESP", "NLD", "SWE")
YEARS = tuple(range(2002, 2013))
PRE = (2002, 2003, 2004, 2005)
POST = (2008, 2009, 2010, 2011, 2012)
OMITTED = (2006, 2007)
PRETREND_MAX = 0.03
EFFECT_THRESHOLD = math.log(1.15)
EXPECTED_KEYS = {(o, d, y) for o in ORIGINS for d in DESTINATIONS for y in YEARS}
EXPECTED_EXCLUDED_NONEXISTING = 385
EXPECTED_RAW_MATCHES = len(EXPECTED_KEYS) + EXPECTED_EXCLUDED_NONEXISTING
SOURCE_FIELDS = (
    "source_row_number", "year", "iso3_o", "iso3_d", "country_exists_o",
    "country_exists_d", "wto_o", "fta_wto", "tradeflow_baci",
)
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, PLAN_REL, RUNNER_REL)


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
    if not commits:
        raise RuntimeError(f"no first-addition commit for {relative}")
    return commits[0]


def is_strict_ancestor(first: str, later: str) -> bool:
    return first != later and git("merge-base", "--is-ancestor", first, later, check=False).returncode == 0


def registration_commit() -> str:
    additions = []
    for relative in REGISTRATION_FILES:
        path = ROOT / relative
        if not path.is_file() or git_bytes("HEAD", relative) != path.read_bytes():
            raise RuntimeError(f"commit unchanged registration before value access: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1:
        raise RuntimeError("spec, steelman, plan and runner must first appear together")
    commit = additions[0]
    for relative in (SPEC_REL, STEELMAN_REL, PLAN_REL):
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration changed since first addition: {relative}")
    path_erratum, census_erratum = runner_amendment_commits(commit)
    if git("ls-tree", "-r", "--name-only", commit, "--", SLICE_REL,
           SLICE_MANIFEST_REL, RUN_REL).stdout.strip():
        raise RuntimeError("registration commit already contained a source slice or result")
    for amendment in (path_erratum, census_erratum):
        if git("ls-tree", "-r", "--name-only", amendment, "--", SLICE_REL,
               SLICE_MANIFEST_REL, RUN_REL).stdout.strip():
            raise RuntimeError("runner correction already contained source slice or result")
    return commit


def runner_amendment_commits(registration: str) -> tuple[str, str]:
    changes = git("log", "--reverse", "--format=%H", f"{registration}..HEAD", "--",
                  RUNNER_REL).stdout.decode().splitlines()
    if (len(changes) != 2 or changes[0] != PATH_ERRATUM_COMMIT
            or not is_strict_ancestor(registration, changes[0])
            or not is_strict_ancestor(changes[0], changes[1])):
        raise RuntimeError("commit exactly two prospective runner corrections before value access")
    if git_bytes(changes[1], RUNNER_REL) != (ROOT / RUNNER_REL).read_bytes():
        raise RuntimeError("runner changed since source-census correction")
    note = ROOT / ERRATUM_NOTE_REL
    if (not note.is_file() or first_addition(ERRATUM_NOTE_REL) != changes[1]
            or git_bytes(changes[1], ERRATUM_NOTE_REL) != note.read_bytes()):
        raise RuntimeError("commit unchanged source-census erratum note with correction")
    return changes[0], changes[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def flag(value: str, field: str) -> int:
    if value.strip() in {"1", "1.0"}:
        return 1
    if value.strip() in {"0", "0.0"}:
        return 0
    raise ValueError(f"{field} must be explicit 0/1, found {value!r}")


def source_rows(source_zip: Path) -> tuple[list[dict[str, str]], int, int]:
    """Select keys and copy flow text without examining its numeric value."""
    selected: list[dict[str, str]] = []
    raw_matches = excluded_nonexisting = 0
    with zipfile.ZipFile(source_zip) as archive:
        with archive.open(SOURCE_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader)
                needed = set(SOURCE_FIELDS) - {"source_row_number"}
                if not needed.issubset(header):
                    raise RuntimeError(f"missing CEPII fields: {sorted(needed - set(header))}")
                columns = {name: header.index(name) for name in needed}
                for row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        raise RuntimeError(f"malformed source row {row_number}")
                    try:
                        year = int(values[columns["year"]])
                    except ValueError:
                        continue
                    origin = values[columns["iso3_o"]]
                    destination = values[columns["iso3_d"]]
                    if (origin, destination, year) not in EXPECTED_KEYS:
                        continue
                    raw_matches += 1
                    if (flag(values[columns["country_exists_o"]], "country_exists_o") != 1
                            or flag(values[columns["country_exists_d"]], "country_exists_d") != 1):
                        excluded_nonexisting += 1
                        continue
                    selected.append({
                        "source_row_number": str(row_number),
                        **{name: values[columns[name]] for name in SOURCE_FIELDS
                           if name != "source_row_number"},
                    })
    selected.sort(key=lambda row: (row["iso3_o"], row["iso3_d"], int(row["year"])))
    keys = [(row["iso3_o"], row["iso3_d"], int(row["year"])) for row in selected]
    if (len(keys) != len(EXPECTED_KEYS) or set(keys) != EXPECTED_KEYS
            or raw_matches != EXPECTED_RAW_MATCHES
            or excluded_nonexisting != EXPECTED_EXCLUDED_NONEXISTING):
        raise RuntimeError("CEPII frozen key/country-existence census changed")
    if len(set(keys)) != len(keys):
        raise RuntimeError("duplicate valid source key")
    return selected, raw_matches, excluded_nonexisting


def slice_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def extract(source_zip: Path, verify: bool) -> None:
    registration = registration_commit()
    path_erratum, census_erratum = runner_amendment_commits(registration)
    if sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("CEPII source ZIP does not match registered SHA-256")
    selected, raw_matches, excluded = source_rows(source_zip)
    content = slice_bytes(selected)
    manifest = {
        "hypothesis_id": HID,
        "source_url": SOURCE_URL,
        "source_member": SOURCE_MEMBER,
        "source_zip_sha256": SOURCE_SHA256,
        "license": "CEPII Gravity, Etalab Open Licence 2.0; attribution required",
        "registration_commit": registration,
        "runner_amendment_commit": path_erratum,
        "source_census_erratum_commit": census_erratum,
        "source_census_erratum_note": ERRATUM_NOTE_REL,
        "slice_path": SLICE_REL,
        "slice_sha256": hashlib.sha256(content).hexdigest(),
        "row_count": len(selected),
        "raw_matches": raw_matches,
        "excluded_nonexisting": excluded,
    }
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    paths = ((ROOT / SLICE_REL, content), (ROOT / SLICE_MANIFEST_REL, manifest_bytes))
    if verify:
        committed_slice(registration)
        for path, expected in paths:
            if path.read_bytes() != expected:
                raise RuntimeError(f"source reproduction mismatch: {path.relative_to(ROOT)}")
        print(f"Verified CEPII source slice: {len(selected)} rows; byte-exact")
    else:
        if any(path.exists() for path, _ in paths):
            raise RuntimeError("source slice already exists; use verify-source")
        for path, data in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        print(f"Extracted {len(selected)} pinned source rows; no flow magnitudes printed")


def committed_slice(registration: str) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    path_erratum, census_erratum = runner_amendment_commits(registration)
    additions = []
    for relative in (SLICE_REL, SLICE_MANIFEST_REL):
        path = ROOT / relative
        if not path.is_file() or git_bytes("HEAD", relative) != path.read_bytes():
            raise RuntimeError(f"commit unchanged source slice before run: {relative}")
        additions.append(first_addition(relative))
    if len(set(additions)) != 1 or not is_strict_ancestor(census_erratum, additions[0]):
        raise RuntimeError("source slice must first appear together in a later commit")
    slice_commit = additions[0]
    for relative in (SLICE_REL, SLICE_MANIFEST_REL):
        if git_bytes(slice_commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"source slice changed since first addition: {relative}")
    if git("ls-tree", "-r", "--name-only", slice_commit, "--", RUN_REL).stdout.strip():
        raise RuntimeError("source slice commit already contained result artifacts")
    manifest = json.loads((ROOT / SLICE_MANIFEST_REL).read_text())
    if (manifest.get("registration_commit") != registration
            or manifest.get("runner_amendment_commit") != path_erratum
            or manifest.get("source_census_erratum_commit") != census_erratum
            or manifest.get("source_census_erratum_note") != ERRATUM_NOTE_REL
            or manifest.get("source_zip_sha256") != SOURCE_SHA256
            or manifest.get("row_count") != len(EXPECTED_KEYS)
            or manifest.get("raw_matches") != EXPECTED_RAW_MATCHES
            or manifest.get("excluded_nonexisting") != EXPECTED_EXCLUDED_NONEXISTING
            or manifest.get("slice_sha256") != sha256_file(ROOT / SLICE_REL)):
        raise RuntimeError("committed source manifest mismatch")
    with (ROOT / SLICE_REL).open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return rows, manifest, slice_commit


def slope(years: tuple[int, ...], values: dict[int, float]) -> float:
    mean_year = statistics.mean(years)
    mean_value = statistics.mean(values[year] for year in years)
    return sum((year - mean_year) * (values[year] - mean_value) for year in years) / sum(
        (year - mean_year) ** 2 for year in years)


def analyze(rows: list[dict[str, str]]) -> dict[str, Any]:
    if len(rows) != len(EXPECTED_KEYS):
        return {"verdict": "INCONCLUSIVE", "reason": "source row count differs from registration"}
    seen: set[tuple[str, str, int]] = set()
    flows: dict[tuple[str, str, int], float] = {}
    for row in rows:
        try:
            key = (row["iso3_o"], row["iso3_d"], int(row["year"]))
            if (key not in EXPECTED_KEYS or key in seen
                    or flag(row["country_exists_o"], "country_exists_o") != 1
                    or flag(row["country_exists_d"], "country_exists_d") != 1):
                raise ValueError("missing, duplicate or nonexisting country key")
            seen.add(key)
            expected_wto = int(key[0] != "VNM" or key[2] >= 2007)
            if (flag(row["wto_o"], "wto_o") != expected_wto
                    or flag(row["fta_wto"], "fta_wto") != 0):
                raise ValueError("frozen WTO/FTA status mismatch")
            value = float(row["tradeflow_baci"])
            if not math.isfinite(value) or value < 0:
                raise ValueError("nonfinite or negative BACI flow")
            flows[key] = math.log1p(value)
        except (KeyError, TypeError, ValueError) as error:
            return {"verdict": "INCONCLUSIVE", "reason": f"source integrity: {error}"}
    if seen != EXPECTED_KEYS:
        return {"verdict": "INCONCLUSIVE", "reason": "frozen source keys missing"}
    basket = {
        origin: {year: statistics.mean(flows[(origin, destination, year)]
                                       for destination in DESTINATIONS)
                 for year in YEARS}
        for origin in ORIGINS
    }
    slopes = {origin: slope(PRE, basket[origin]) for origin in ORIGINS}
    donor_slope = statistics.median(slopes[origin] for origin in DONORS)
    slope_gap = slopes["VNM"] - donor_slope
    pretrend = {
        "vietnam_slope": slopes["VNM"],
        "median_donor_slope": donor_slope,
        "gap": slope_gap,
        "max_abs_gap": PRETREND_MAX,
    }
    if abs(slope_gap) > PRETREND_MAX:
        return {"verdict": "INCONCLUSIVE", "reason": "registered pretrend gate failed",
                "pretrend": pretrend}
    changes = {
        origin: statistics.mean(basket[origin][year] for year in POST)
                - statistics.mean(basket[origin][year] for year in PRE)
        for origin in ORIGINS
    }
    donor_change = statistics.median(changes[origin] for origin in DONORS)
    contrast = changes["VNM"] - donor_change
    placebos = {
        origin: changes[origin] - statistics.median(
            changes[other] for other in DONORS if other != origin)
        for origin in DONORS
    }
    if contrast >= EFFECT_THRESHOLD and contrast > max(placebos.values()):
        verdict = "SUPPORTED"
    elif contrast <= -EFFECT_THRESHOLD and contrast < min(placebos.values()):
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return {
        "verdict": verdict,
        "reason": "one-case descriptive contrast under fixed pretrend and placebo gates",
        "pretrend": pretrend,
        "vietnam_log_change": changes["VNM"],
        "median_donor_log_change": donor_change,
        "contrast_log_units": contrast,
        "contrast_ratio": math.exp(contrast),
        "threshold_log_units": EFFECT_THRESHOLD,
        "donor_log_changes": {origin: changes[origin] for origin in DONORS},
        "donor_placebo_contrasts": placebos,
        "pre_years": list(PRE),
        "post_years": list(POST),
        "omitted_years": list(OMITTED),
    }


def result_card(diagnostics: dict[str, Any]) -> str:
    analysis = diagnostics["analysis"]
    lines = [
        f"# {HID}", "", f"**Verdict: {analysis['verdict']}** — {analysis['reason']}", "",
        "Directed BACI merchandise exports from VNM to nine fixed destinations",
        "versus the median corresponding change for THA, MYS, IDN and PHL.",
        "This is descriptive calibration, not a causal WTO-accession effect.", "",
        f"- WTO membership: 2007-01-11 ({POLICY_URL}).",
        "- Pre: 2002–2005; 2006–2007 omitted; post: 2008–2012.",
        f"- CEPII Gravity ZIP SHA-256: {SOURCE_SHA256}.",
        f"- Committed slice SHA-256: {diagnostics['slice_sha256']}.",
        f"- Registration commit: {diagnostics['preregistration_commit']}.",
        f"- Slice commit: {diagnostics['slice_commit']}.",
        "- Family size: one fixed event-level hypothesis, not nine destination or 45 dyad tests.",
        "- Causal, featured, school and policy-score credit: zero.",
    ]
    if "pretrend" in analysis:
        lines.append(f"- Pretrend slope gap: {analysis['pretrend']['gap']:.6f} log units/year; "
                     "absolute limit 0.030000.")
    if "contrast_log_units" in analysis:
        lines.append(f"- Contrast: {analysis['contrast_log_units']:.6f} log units "
                     f"(ratio {analysis['contrast_ratio']:.4f}); threshold ±ln(1.15).")
        lines.append("- Donor-placebo range: "
                     f"{min(analysis['donor_placebo_contrasts'].values()):.6f} to "
                     f"{max(analysis['donor_placebo_contrasts'].values()):.6f} log units.")
    lines += [
        "", "## Limits", "",
        "BACI flows are nominal and mix prices with quantities. Viet Nam's 2001",
        "US bilateral agreement, anticipation in 2006, the 2008–2009 crisis, FDI,",
        "exchange rates and domestic reforms can move trade. ASEAN origins are",
        "imperfect peers. The rank check has no conventional significant p-value.",
        "The source's FTA flag is zero for this grid, but other market access",
        "changes and measurement revisions can remain. No policy effect is verified.",
        "", f"Reproduce: python3 {RUNNER_REL} verify", "",
    ]
    return "\n".join(lines)


def artifacts(registration: str, slice_commit: str, source_manifest: dict[str, Any],
              rows: list[dict[str, str]], stamp: str) -> dict[str, bytes]:
    analysis = analyze(rows)
    correction = {
        "disposition": "descriptive_calibration_only",
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0,
    }
    limitations = [
        "No causal WTO or policy effect identified; one event-level descriptive test.",
        "Nominal BACI merchandise flows, not real trade volume or welfare.",
        "US-Viet Nam 2001 agreement, 2006 anticipation, 2008-2009 crisis, FDI and reforms confound the comparison.",
        "Four ASEAN donor origins and nine destinations are not independent hypotheses.",
    ]
    source = {
        "publisher": "cepii", "dataset": "Gravity V202211", "source_url": SOURCE_URL,
        "source_zip_sha256": SOURCE_SHA256, "source_member": SOURCE_MEMBER,
        "license": source_manifest["license"],
        "registration_commit": registration,
        "runner_amendment_commit": source_manifest["runner_amendment_commit"],
        "source_census_erratum_commit": source_manifest["source_census_erratum_commit"],
        "source_census_erratum_note": ERRATUM_NOTE_REL,
        "slice_path": SLICE_REL, "slice_sha256": source_manifest["slice_sha256"],
        "slice_commit": slice_commit, "row_count": len(EXPECTED_KEYS),
    }
    diagnostics = {
        "hypothesis_id": HID, "verdict": analysis["verdict"],
        "method": "descriptive fixed-basket, fixed-donor log pre/post comparison",
        "run_utc": stamp, "preregistration_commit": registration,
        "runner_amendment_commit": source_manifest["runner_amendment_commit"],
        "source_census_erratum_commit": source_manifest["source_census_erratum_commit"],
        "slice_commit": slice_commit, "slice_sha256": source_manifest["slice_sha256"],
        "source_zip_sha256": SOURCE_SHA256, "runner": RUNNER_REL,
        "selected_rows_total": len(EXPECTED_KEYS), "selection_truncated": False,
        "analysis": analysis, "family_size": 1, "family_member_ids": [HID],
        "evidence_tier_recommendation": "calibration", "correction": correction,
        "limitations": limitations,
    }
    run_manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "status": analysis["verdict"],
        "runner": RUNNER_REL, "hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
        "preregistration_commit": registration, "source": source, "correction": correction,
        "runner_amendment_commit": source_manifest["runner_amendment_commit"],
        "source_census_erratum_commit": source_manifest["source_census_erratum_commit"],
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "policy_id": "vn_wto_accession_2007"},
        "preregistration": {
            "commit": registration, "steelman": STEELMAN_REL,
            "runner_amendment_commit": source_manifest["runner_amendment_commit"],
            "source_census_erratum_commit": source_manifest["source_census_erratum_commit"],
            "source_plan": PLAN_REL, "frozen_hypothesis_snapshot": f"{RUN_REL}/hypothesis.yaml",
        },
        "source": source,
        "reproduction": {"runner": RUNNER_REL, "command": f"python3 {RUNNER_REL} verify"},
        "gate": {
            "fixed_dyad_year_rows": len(EXPECTED_KEYS), "origins": list(ORIGINS),
            "destinations": list(DESTINATIONS), "pre_years": list(PRE),
            "post_years": list(POST), "omitted_years": list(OMITTED),
            "pretrend_max_abs_log_slope_gap": PRETREND_MAX,
            "pretrend": analysis.get("pretrend"), "family_size": 1,
        },
        "result": analysis, "limitations": limitations, "correction": correction,
    }
    wrapper = (
        "#!/usr/bin/env python3\n"
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER_REL}'), "
        "'verify'], cwd=root))\n"
    )
    result: dict[str, bytes] = {
        "hypothesis.yaml": (ROOT / SPEC_REL).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode(),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": result_card(diagnostics).encode(),
        "replication.py": wrapper.encode(),
    }
    if "contrast_log_units" in analysis:
        chart = {
            "hypothesis_id": HID, "verdict": analysis["verdict"],
            "metric": "pre/post change in equal-destination mean log1p BACI flow",
            "unit": "log units", "pre_years": list(PRE), "post_years": list(POST),
            "origins": [
                {"origin": origin, "treated": origin == "VNM",
                 "log_change": (analysis["vietnam_log_change"] if origin == "VNM"
                                else analysis["donor_log_changes"][origin])}
                for origin in ORIGINS
            ],
            "contrast_log_units": analysis["contrast_log_units"],
            "donor_placebo_contrasts": analysis["donor_placebo_contrasts"],
            "directional_threshold_log_units": EFFECT_THRESHOLD,
        }
        result["chart_data.json"] = (json.dumps(chart, indent=2, sort_keys=True) + "\n").encode()
    return result


def run(verify: bool) -> None:
    registration = registration_commit()
    rows, source_manifest, slice_commit = committed_slice(registration)
    run_dir = ROOT / RUN_REL
    if verify:
        stored = json.loads((run_dir / "diagnostics.json").read_text())
        stamp = stored.get("run_utc")
        if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
            raise RuntimeError("invalid stored run_utc")
    else:
        if run_dir.exists():
            raise RuntimeError("run directory already exists; use verify")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    expected = artifacts(registration, slice_commit, source_manifest, rows, stamp)
    if verify:
        if {p.name for p in run_dir.iterdir() if p.is_file()} != set(expected):
            raise RuntimeError("result artifact set differs from runner")
        for name, content in expected.items():
            if (run_dir / name).read_bytes() != content:
                raise RuntimeError(f"byte-exact replication mismatch: {name}")
        print(f"Verified {HID}: {json.loads(expected['diagnostics.json'])['verdict']} "
              f"and all {len(expected)} artifacts")
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
        "expected_unique_keys": len(EXPECTED_KEYS), "raw_matches_including_nonexisting": EXPECTED_RAW_MATCHES,
        "excluded_nonexisting": EXPECTED_EXCLUDED_NONEXISTING,
        "origins": list(ORIGINS), "destinations": list(DESTINATIONS),
        "pre": list(PRE), "omitted": list(OMITTED), "post": list(POST),
        "pretrend_max_abs_log_slope_gap": PRETREND_MAX,
        "effect_threshold_log": EFFECT_THRESHOLD, "family_size": 1,
    }, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    extractor = commands.add_parser("extract")
    extractor.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    verifier = commands.add_parser("verify-source")
    verifier.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    commands.add_parser("run")
    commands.add_parser("verify")
    args = parser.parse_args()
    try:
        if args.command == "plan":
            plan()
        elif args.command == "extract":
            extract(args.source_zip, verify=False)
        elif args.command == "verify-source":
            extract(args.source_zip, verify=True)
        elif args.command == "run":
            run(verify=False)
        else:
            run(verify=True)
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
