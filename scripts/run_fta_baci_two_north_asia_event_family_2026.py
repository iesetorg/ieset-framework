#!/usr/bin/env python3
"""Frozen two-treaty CEPII BACI descriptive family with source custody.

The plan command reads no outcomes. Extract first requires a commit containing
both specifications, steelmen, source plan, and this runner. Run and verify
require a later commit containing the exact extracted source slice.
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
RUNNER_REL = "scripts/run_fta_baci_two_north_asia_event_family_2026.py"
PLAN_REL = "engine/audits/fta_baci_two_north_asia_event_family_2026_source_plan.md"
SLICE_REL = "data/pinned_evidence/fta_baci_two_north_asia_event_family_2026.csv"
MANIFEST_REL = "data/pinned_evidence/fta_baci_two_north_asia_event_family_2026.manifest.json"
SOURCE_URL = "https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip"
SOURCE_MEMBER = "Gravity_V202211.csv"
SOURCE_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
SOURCE_DEFAULT = ROOT / "data/raw/cepii/Gravity_csv_V202211.zip"
SOURCE_FIELDS = (
    "source_row_number", "year", "iso3_o", "iso3_d", "country_exists_o",
    "country_exists_d", "fta_wto", "tradeflow_baci",
)
PRETREND_MAX = 0.03
EFFECT_THRESHOLD = math.log(1.15)
FAMILY_SIZE = 2
CASES = {
    "australia_korea_kafta_bilateral_exports_2014": {
        "focal": "AUS", "destination": "KOR", "event_year": 2014,
        "effective_date": "2014-12-12", "event_fta": 0,
        "donors": ("RUS", "BRA", "ARG", "ZAF", "SAU", "MEX"),
        "policy_id": "au_kafta_jaepa_chafta_ftas_2014_2015",
        "old_hypothesis_id": None, "old_result": None,
        "specific_limit": "This is a separate agreement within the recorded Australia North Asia bundle. The earlier AUS>CHN ChAFTA direct-flow test was INCONCLUSIVE on pretrend, and the old ChAFTA WDI result was PARTIAL; both were known before this registration. Korean demand, commodity prices, Australia's terms of trade and Korea's own simultaneous FTAs can move nominal exports.",
        "effective_url": "https://www.dfat.gov.au/trade/agreements/in-force/kafta/korea-australia-fta",
    },
    "australia_japan_jaepa_bilateral_exports_2015": {
        "focal": "AUS", "destination": "JPN", "event_year": 2015,
        "effective_date": "2015-01-15", "event_fta": 1,
        "donors": ("USA", "RUS", "BRA", "ARG", "ZAF", "SAU"),
        "policy_id": "au_kafta_jaepa_chafta_ftas_2014_2015",
        "old_hypothesis_id": None, "old_result": None,
        "specific_limit": "This is a separate agreement within the recorded Australia North Asia bundle. The earlier AUS>CHN ChAFTA direct-flow test was INCONCLUSIVE on pretrend, and the old ChAFTA WDI result was PARTIAL; both were known before this registration. Japan's demand, commodity prices, Australia's terms of trade and Japan's monetary policy can move nominal exports.",
        "effective_url": "https://www.dfat.gov.au/trade/agreements/in-force/jaepa/japan-australia-economic-partnership-agreement",
    },
}
HIDS = tuple(CASES)
REGISTRATION_FILES = (PLAN_REL, RUNNER_REL) + tuple(
    path for hid in HIDS for path in
    (f"hypotheses/trade/{hid}.yaml", f"hypotheses/steelman/{hid}.md")
)
RUN_RELS = {hid: f"engine/runs/{hid}" for hid in HIDS}
YEARS = {hid: tuple(range(c["event_year"] - 4, c["event_year"] + 5))
         for hid, c in CASES.items()}
PRE = {hid: tuple(range(c["event_year"] - 4, c["event_year"]))
       for hid, c in CASES.items()}
POST = {hid: tuple(range(c["event_year"] + 1, c["event_year"] + 5))
        for hid, c in CASES.items()}
EXPECTED_KEYS = {
    (origin, c["destination"], year)
    for hid, c in CASES.items()
    for origin in (c["focal"],) + c["donors"]
    for year in YEARS[hid]
}
MAX_CUSTODY_ROWS = len(EXPECTED_KEYS) + 1


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)
    if check and result.returncode:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}"
        )
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
        raise RuntimeError("both specs, steelmen, plan and runner must first appear together")
    commit = additions[0]
    for relative in REGISTRATION_FILES:
        if git_bytes(commit, relative) != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registered bytes changed after first addition: {relative}")
    for run_rel in RUN_RELS.values():
        if git("ls-tree", "-r", "--name-only", commit, "--", run_rel).stdout.strip():
            raise RuntimeError("run artifacts cannot appear in the registration commit")
    if git("ls-tree", "-r", "--name-only", commit, "--", SLICE_REL, MANIFEST_REL).stdout.strip():
        raise RuntimeError("outcome slice cannot appear in the registration commit")
    return commit


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bool01(value: str, field: str) -> int:
    cleaned = value.strip()
    if cleaned in {"1", "1.0"}:
        return 1
    if cleaned in {"0", "0.0"}:
        return 0
    raise ValueError(f"{field} must be explicit 0/1; found {value!r}")


def extraction_rows(source_zip: Path) -> tuple[list[dict[str, str]], int, int, int]:
    """Select fixed dyad-year keys and existing countries, preserving one excess row."""
    selected: list[dict[str, str]] = []
    selected_total = raw_matches = excluded_nonexisting = 0
    with zipfile.ZipFile(source_zip) as archive:
        if SOURCE_MEMBER not in archive.namelist():
            raise ValueError(f"missing source member: {SOURCE_MEMBER}")
        with archive.open(SOURCE_MEMBER) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8-sig", newline="") as stream:
                reader = csv.reader(stream)
                header = next(reader)
                needed = set(SOURCE_FIELDS) - {"source_row_number"}
                if not needed.issubset(header):
                    raise ValueError(f"missing CEPII columns: {sorted(needed - set(header))}")
                indices = {field: header.index(field) for field in needed}
                for row_number, values in enumerate(reader, start=2):
                    if len(values) != len(header):
                        raise ValueError(f"malformed source row {row_number}")
                    origin, destination = values[indices["iso3_o"]], values[indices["iso3_d"]]
                    try:
                        year = int(values[indices["year"]])
                    except ValueError:
                        continue
                    if (origin, destination, year) not in EXPECTED_KEYS:
                        continue
                    raw_matches += 1
                    try:
                        exists = bool01(values[indices["country_exists_o"]], "country_exists_o") == 1
                        exists = exists and bool01(values[indices["country_exists_d"]], "country_exists_d") == 1
                    except ValueError:
                        exists = False
                    if not exists:
                        excluded_nonexisting += 1
                        continue
                    selected_total += 1
                    if len(selected) < MAX_CUSTODY_ROWS:
                        selected.append({
                            "source_row_number": str(row_number),
                            **{field: values[indices[field]] for field in SOURCE_FIELDS
                               if field != "source_row_number"},
                        })
    selected.sort(key=lambda row: (
        row["iso3_o"], row["iso3_d"], int(row["year"]), int(row["source_row_number"])
    ))
    return selected, selected_total, raw_matches, excluded_nonexisting


def canonical_slice_bytes(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=SOURCE_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def extract(source_zip: Path) -> None:
    commit = registration_commit()
    if (ROOT / SLICE_REL).exists() or (ROOT / MANIFEST_REL).exists():
        raise RuntimeError("source custody files already exist; do not overwrite")
    if not source_zip.is_file():
        raise RuntimeError(f"source ZIP unavailable: {source_zip}")
    actual_sha = sha256_file(source_zip)
    if actual_sha != SOURCE_SHA256:
        raise RuntimeError(f"CEPII source SHA mismatch: {actual_sha}")
    rows, total, raw_matches, excluded = extraction_rows(source_zip)
    content = canonical_slice_bytes(rows)
    manifest = {
        "family": "fta_baci_two_north_asia_event_family_2026",
        "hypothesis_ids": list(HIDS),
        "publisher": "cepii",
        "dataset": "Gravity V202211",
        "source_url": SOURCE_URL,
        "source_member": SOURCE_MEMBER,
        "source_zip_sha256": SOURCE_SHA256,
        "registration_commit": commit,
        "extractor": RUNNER_REL,
        "slice_path": SLICE_REL,
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
        "source_row_number_definition": "one-based CSV record ordinal including header as record 1",
    }
    path = ROOT / SLICE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    (ROOT / MANIFEST_REL).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                                      encoding="utf-8")
    print(f"Preserved {len(rows)} source rows ({total} existing matches; "
          f"{excluded} nonexisting excluded); SHA-256 {manifest['slice_sha256']}")
    print("Commit the small source slice and manifest before analysis.")


def committed_slice(registration: str) -> tuple[list[dict[str, str]], dict[str, Any], str]:
    additions = [first_addition(relative) for relative in (SLICE_REL, MANIFEST_REL)]
    if len(set(additions)) != 1 or not strict_ancestor(registration, additions[0]):
        raise RuntimeError("slice and manifest must first appear together after registration")
    for relative in (SLICE_REL, MANIFEST_REL):
        current = (ROOT / relative).read_bytes()
        if git_bytes("HEAD", relative) != current or git_bytes(additions[0], relative) != current:
            raise RuntimeError(f"source custody bytes changed after first addition: {relative}")
    for run_rel in RUN_RELS.values():
        if git("ls-tree", "-r", "--name-only", additions[0], "--", run_rel).stdout.strip():
            raise RuntimeError("run artifacts cannot appear in the source-slice commit")
    manifest = json.loads((ROOT / MANIFEST_REL).read_text(encoding="utf-8"))
    content = (ROOT / SLICE_REL).read_bytes()
    if manifest.get("registration_commit") != registration:
        raise RuntimeError("slice registration commit mismatch")
    if manifest.get("source_zip_sha256") != SOURCE_SHA256 or manifest.get("source_member") != SOURCE_MEMBER:
        raise RuntimeError("source vintage mismatch")
    if manifest.get("slice_sha256") != hashlib.sha256(content).hexdigest():
        raise RuntimeError("source slice SHA mismatch")
    with io.StringIO(content.decode("utf-8"), newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != SOURCE_FIELDS:
            raise RuntimeError("source slice column order mismatch")
        rows = list(reader)
    ordered = sorted(rows, key=lambda row: (
        row["iso3_o"], row["iso3_d"], int(row["year"]), int(row["source_row_number"])
    ))
    if rows != ordered or manifest.get("row_count") != len(rows):
        raise RuntimeError("source slice ordering or row count mismatch")
    total = manifest.get("selected_existing_rows_total")
    if (not isinstance(total, int) or total < len(rows)
            or manifest.get("selection_truncated") is not (total > len(rows))
            or manifest.get("max_custody_rows") != MAX_CUSTODY_ROWS
            or manifest.get("expected_unique_keys") != len(EXPECTED_KEYS)
            or len(rows) > MAX_CUSTODY_ROWS):
        raise RuntimeError("source selection metadata mismatch")
    if manifest.get("row_keys") != [f"{r['iso3_o']}>{r['iso3_d']}:{r['year']}" for r in rows]:
        raise RuntimeError("source row keys mismatch")
    return rows, manifest, additions[0]


def verify_source(source_zip: Path) -> None:
    registration = registration_commit()
    _, manifest, _ = committed_slice(registration)
    if not source_zip.is_file():
        raise RuntimeError(f"source ZIP unavailable: {source_zip}")
    if sha256_file(source_zip) != SOURCE_SHA256:
        raise RuntimeError("CEPII source SHA mismatch")
    rows, total, raw_matches, excluded = extraction_rows(source_zip)
    content = canonical_slice_bytes(rows)
    if content != (ROOT / SLICE_REL).read_bytes():
        raise RuntimeError("committed source slice differs byte-for-byte from CEPII re-extraction")
    if (total != manifest["selected_existing_rows_total"]
            or raw_matches != manifest["raw_key_matches_total"]
            or excluded != manifest["excluded_nonexisting_rows"]):
        raise RuntimeError("source selection counts differ")
    print(f"Verified official source custody: {total} existing-key matches, "
          f"{len(rows)} retained rows")


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


def analyse_case(hid: str, rows: list[dict[str, str]],
                 manifest: dict[str, Any]) -> dict[str, Any]:
    c = CASES[hid]
    if manifest["selection_truncated"]:
        return {"verdict": "INCONCLUSIVE", "reason": "family source selection exceeds bounded custody slice"}
    keyed: dict[tuple[str, str, int], list[dict[str, str]]] = {}
    for row in rows:
        key = (row["iso3_o"], row["iso3_d"], int(row["year"]))
        keyed.setdefault(key, []).append(row)
    origins = (c["focal"],) + c["donors"]
    values: dict[str, dict[int, float]] = {}
    try:
        for origin in origins:
            values[origin] = {}
            for year in YEARS[hid]:
                key = (origin, c["destination"], year)
                matches = keyed.get(key, [])
                if len(matches) != 1:
                    raise ValueError(f"{key} has {len(matches)} source rows; expected one")
                row = matches[0]
                if bool01(row["country_exists_o"], "country_exists_o") != 1:
                    raise ValueError(f"{key} origin does not exist")
                if bool01(row["country_exists_d"], "country_exists_d") != 1:
                    raise ValueError(f"{key} destination does not exist")
                if origin == c["focal"]:
                    expected_fta = 0 if year < c["event_year"] else (
                        c["event_fta"] if year == c["event_year"] else 1
                    )
                else:
                    expected_fta = 0
                if bool01(row["fta_wto"], "fta_wto") != expected_fta:
                    raise ValueError(f"{key} agreement status differs from registered schedule")
                values[origin][year] = log_flow(row)
    except ValueError as error:
        return {"verdict": "INCONCLUSIVE",
                "reason": f"structural, treatment or outcome-completeness gate failed: {error}"}
    slopes = {origin: slope(values[origin], PRE[hid]) for origin in origins}
    donor_slope = statistics.median(slopes[origin] for origin in c["donors"])
    gap = slopes[c["focal"]] - donor_slope
    pretrend = {
        "focal_slope": slopes[c["focal"]],
        "median_donor_slope": donor_slope,
        "gap": gap,
        "max_abs_gap": PRETREND_MAX,
    }
    if abs(gap) > PRETREND_MAX:
        return {"verdict": "INCONCLUSIVE", "reason": "registered pretrend gate failed",
                "pretrend": pretrend}
    changes = {
        origin: statistics.mean(values[origin][year] for year in POST[hid])
                - statistics.mean(values[origin][year] for year in PRE[hid])
        for origin in origins
    }
    donor_median = statistics.median(changes[origin] for origin in c["donors"])
    contrast = changes[c["focal"]] - donor_median
    if contrast >= EFFECT_THRESHOLD:
        verdict = "SUPPORTED"
    elif contrast <= -EFFECT_THRESHOLD:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return {
        "verdict": verdict,
        "reason": "fixed-donor descriptive contrast under the registered gates",
        "pretrend": pretrend,
        "focal_log_change": changes[c["focal"]],
        "median_donor_log_change": donor_median,
        "contrast_log_units": contrast,
        "contrast_ratio": math.exp(contrast),
        "directional_threshold_log_units": EFFECT_THRESHOLD,
        "donor_log_changes": {origin: changes[origin] for origin in c["donors"]},
        "pre_years": list(PRE[hid]),
        "post_years": list(POST[hid]),
        "omitted_event_year": c["event_year"],
    }


def result_card(hid: str, diagnostics: dict[str, Any]) -> str:
    c = CASES[hid]
    a = diagnostics["analysis"]
    lines = [
        f"# {hid}", "", f"**Verdict: {a['verdict']}** — {a['reason']}", "",
        f"Measured dyad: {c['focal']} → {c['destination']}. This is a "
        "descriptive merchandise-flow comparison, not a causal treaty effect.",
        "", f"- Agreement effective: {c['effective_date']} ({c['effective_url']}).",
        f"- Pre: {PRE[hid][0]}–{PRE[hid][-1]}; post: {POST[hid][0]}–{POST[hid][-1]}; "
        f"{c['event_year']} excluded from means.",
        f"- Donor origins to {c['destination']}: {', '.join(c['donors'])}.",
        f"- CEPII source archive SHA-256: {SOURCE_SHA256}.",
        f"- Committed slice SHA-256: {diagnostics['slice_sha256']}.",
        f"- Registration commit: {diagnostics['preregistration_commit']}.",
        f"- Slice commit: {diagnostics['slice_commit']}.",
        "- Family size: two fixed treaty tests; no optional reverse-direction or product result.",
        "- School and policy score credit: zero.",
    ]
    if c["old_hypothesis_id"]:
        lines.append(f"- Old result disclosed: {c['old_hypothesis_id']} was "
                     f"{c['old_result']} on a different WDI country-outcome design.")
    if "pretrend" in a:
        lines.append(f"- Pretrend slope gap: {a['pretrend']['gap']:.6f} "
                     "log units/year; maximum absolute gap 0.030000.")
    if "contrast_log_units" in a:
        lines.append(f"- Registered contrast: {a['contrast_log_units']:.6f} "
                     f"log units (ratio {a['contrast_ratio']:.4f}); threshold ±ln(1.15).")
    lines += ["", "## Limits", "",
              "BACI values are nominal goods trade in thousands of current US dollars; "
              "they mix prices and quantities. CEPII fta_wto records agreement status, "
              "not tariff intensity. " + c["specific_limit"] +
              " The fixed donor set and pretrend screen do not remove remaining confounding.",
              "", f"Reproduce: python3 {RUNNER_REL} verify --case {hid}", ""]
    return "\n".join(lines)


def artifacts_for(hid: str, registration: str, slice_commit: str,
                  manifest: dict[str, Any], rows: list[dict[str, str]],
                  stamp: str) -> dict[str, bytes]:
    c = CASES[hid]
    run_rel = RUN_RELS[hid]
    spec_rel = f"hypotheses/trade/{hid}.yaml"
    steelman_rel = f"hypotheses/steelman/{hid}.md"
    analysis = analyse_case(hid, rows, manifest)
    limitations = [
        "Descriptive treaty-level association only; no causal policy effect identified.",
        "Nominal merchandise values, not real trade volumes or welfare.",
        "Two correlated treaty tests in one source family; donor dyads are not independent tests.",
        c["specific_limit"],
    ]
    correction = {
        "disposition": "descriptive_calibration_only",
        "school_score_eligible": False,
        "school_score_credit": 0,
        "policy_score_eligible": False,
        "policy_score_credit": 0,
    }
    diagnostics = {
        "hypothesis_id": hid,
        "verdict": analysis["verdict"],
        "method": "descriptive fixed-donor log pre/post comparison, no causal identification",
        "run_utc": stamp,
        "preregistration_commit": registration,
        "slice_commit": slice_commit,
        "slice_sha256": manifest["slice_sha256"],
        "selected_rows_total": manifest["selected_existing_rows_total"],
        "selection_truncated": manifest["selection_truncated"],
        "source_zip_sha256": SOURCE_SHA256,
        "runner": RUNNER_REL,
        "analysis": analysis,
        "family_size": FAMILY_SIZE,
        "family_member_ids": list(HIDS),
        "evidence_tier_recommendation": "calibration",
        "correction": correction,
        "limitations": limitations,
    }
    source = {
        "publisher": "cepii",
        "dataset": "Gravity V202211",
        "source_url": SOURCE_URL,
        "source_zip_sha256": SOURCE_SHA256,
        "source_member": SOURCE_MEMBER,
        "slice_path": SLICE_REL,
        "slice_sha256": manifest["slice_sha256"],
        "slice_commit": slice_commit,
        "row_count": manifest["row_count"],
        "selected_existing_rows_total": manifest["selected_existing_rows_total"],
        "selection_truncated": manifest["selection_truncated"],
    }
    run_manifest = {
        "hypothesis_id": hid,
        "run_utc": stamp,
        "status": analysis["verdict"],
        "runner": RUNNER_REL,
        "hypothesis_snapshot": f"{run_rel}/hypothesis.yaml",
        "preregistration_commit": registration,
        "source": source,
        "correction": correction,
    }
    packet = {
        "packet_version": 1,
        "generated_utc": stamp,
        "hypothesis": {"id": hid, "path": spec_rel, "policy_id": c["policy_id"]},
        "preregistration": {
            "commit": registration,
            "steelman": steelman_rel,
            "source_plan": PLAN_REL,
            "frozen_hypothesis_snapshot": f"{run_rel}/hypothesis.yaml",
        },
        "source": source,
        "reproduction": {
            "runner": RUNNER_REL,
            "command": f"python3 {RUNNER_REL} verify --case {hid}",
        },
        "gate": {
            "fixed_dyad_year_rows": len(YEARS[hid]) * (len(c["donors"]) + 1),
            "directed_treated_dyad": f"{c['focal']}>{c['destination']}",
            "donor_dyads": [f"{d}>{c['destination']}" for d in c["donors"]],
            "pre_years": list(PRE[hid]),
            "post_years": list(POST[hid]),
            "pretrend_max_abs_log_slope_gap": PRETREND_MAX,
            "pretrend": analysis.get("pretrend"),
            "family_size": FAMILY_SIZE,
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
        f"raise SystemExit(subprocess.call([sys.executable, "
        f"str(root / '{RUNNER_REL}'), 'verify', '--case', '{hid}'], cwd=root))\n"
    )
    artifacts: dict[str, bytes] = {
        "hypothesis.yaml": (ROOT / spec_rel).read_bytes(),
        "manifest.yaml": yaml.safe_dump(run_manifest, sort_keys=False).encode("utf-8"),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode("utf-8"),
        "result_card.md": result_card(hid, diagnostics).encode("utf-8"),
        "replication.py": wrapper.encode("utf-8"),
    }
    if "contrast_log_units" in analysis:
        chart = {
            "hypothesis_id": hid,
            "verdict": analysis["verdict"],
            "metric": "pre/post change in mean log1p nominal BACI merchandise exports",
            "unit": "log units",
            "pre_years": list(PRE[hid]),
            "post_years": list(POST[hid]),
            "points": [
                {"origin": origin, "destination": c["destination"],
                 "treated": origin == c["focal"],
                 "log_change": (analysis["focal_log_change"]
                                if origin == c["focal"]
                                else analysis["donor_log_changes"][origin])}
                for origin in (c["focal"],) + c["donors"]
            ],
            "donor_median_log_change": analysis["median_donor_log_change"],
            "contrast_log_units": analysis["contrast_log_units"],
            "directional_threshold_log_units": EFFECT_THRESHOLD,
        }
        artifacts["chart_data.json"] = (json.dumps(chart, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return artifacts


def run(verify: bool, only_case: str | None) -> None:
    registration = registration_commit()
    rows, manifest, slice_commit = committed_slice(registration)
    targets = (only_case,) if only_case else HIDS
    if not verify:
        present = [hid for hid in targets if (ROOT / RUN_RELS[hid]).exists()]
        if present:
            raise RuntimeError(f"run directories already exist: {present}; use verify")
    for hid in targets:
        run_dir = ROOT / RUN_RELS[hid]
        if verify:
            stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
            stamp = stored.get("run_utc")
            if not isinstance(stamp, str) or datetime.fromisoformat(stamp).tzinfo is None:
                raise RuntimeError(f"{hid} has invalid stored run_utc")
        else:
            stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        expected = artifacts_for(hid, registration, slice_commit, manifest, rows, stamp)
        if verify:
            if {p.name for p in run_dir.iterdir() if p.is_file()} != set(expected):
                raise RuntimeError(f"{hid} artifact set differs from runner output")
            for name, content in expected.items():
                if (run_dir / name).read_bytes() != content:
                    raise RuntimeError(f"{hid} byte-exact replication mismatch: {name}")
            print(f"Verified {hid}: {json.loads(expected['diagnostics.json'])['verdict']} "
                  f"and all {len(expected)} artifacts")
        else:
            run_dir.mkdir(parents=True, exist_ok=False)
            for name, content in expected.items():
                (run_dir / name).write_bytes(content)
            print(f"{hid}: {json.loads(expected['diagnostics.json'])['verdict']}")


def plan() -> None:
    print(json.dumps({
        "family": "fta_baci_two_north_asia_event_family_2026",
        "value_access": False,
        "source_zip_sha256": SOURCE_SHA256,
        "source_manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "source_slice_unique_keys": len(EXPECTED_KEYS),
        "two_case_membership_rows": sum(len(YEARS[hid]) * (len(c["donors"]) + 1)
                                         for hid, c in CASES.items()),
        "pretrend_max_abs_slope_gap": PRETREND_MAX,
        "effect_threshold_log": EFFECT_THRESHOLD,
        "cases": {
            hid: {
                "treated_dyad": f"{c['focal']}>{c['destination']}",
                "donor_origins": list(c["donors"]),
                "effective_date": c["effective_date"],
                "pre": list(PRE[hid]), "post": list(POST[hid]),
                "event_year_excluded": c["event_year"],
                "event_year_fta_status": c["event_fta"],
            } for hid, c in CASES.items()
        },
    }, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan")
    extractor = commands.add_parser("extract")
    extractor.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    verifier = commands.add_parser("verify-source")
    verifier.add_argument("--source-zip", type=Path, default=SOURCE_DEFAULT)
    runner = commands.add_parser("run")
    runner.add_argument("--case", choices=HIDS)
    replay = commands.add_parser("verify")
    replay.add_argument("--case", choices=HIDS)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            plan()
        elif args.command == "extract":
            extract(args.source_zip)
        elif args.command == "verify-source":
            verify_source(args.source_zip)
        else:
            run(verify=args.command == "verify", only_case=args.case)
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
