#!/usr/bin/env python3
"""Guarded Eurostat direct-measurement comparison; preflight reads keys only.

The new specification, steelman, and runner must have identical bytes in
their shared first-addition commit before --run or --check accesses values.
--check re-estimates and compares the complete stored packet without writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "eurozone_distribution_2008_2014_direct_measures_v2"
OLD_ID = "eurozone_austerity_distributional_incidence"
SPEC_REL = f"hypotheses/distribution/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = "scripts/run_eurozone_distribution_direct_measures_v2.py"
RUN_REL = f"engine/runs/{HID}"
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
PERIPHERY = ("GRC", "ESP", "PRT", "IRL", "ITA")
CORE = ("AUT", "BEL", "DEU", "FRA", "FIN", "NLD")
COUNTRIES = PERIPHERY + CORE
YEARS = (2008, 2014)
GEO_CODES = {country: "EL" if country == "GRC" else {
    "ESP": "ES", "PRT": "PT", "IRL": "IE", "ITA": "IT",
    "AUT": "AT", "BEL": "BE", "DEU": "DE", "FRA": "FR",
    "FIN": "FI", "NLD": "NL",
}.get(country, country) for country in COUNTRIES}
ISO_CODES = {geo: country for country, geo in GEO_CODES.items()}
ROLES = ("income_share", "poverty_rate")
SOURCES = {
    "income_share": {
        "source": "eurostat:ilc_di01",
        "series_id": "ilc_di01",
        "path": "data/vintages/eurostat/ilc_di01@2026-04-30T115754Z.parquet",
        "sha256": "6dc9948f57c6dc32e967628f541bbb19c894680ae7304b9de59fd50e641c29b5",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_di01?format=JSON",
        "dimensions": {"freq": "A", "quantile": "QU1", "indic_il": "SHARE", "currency": "EUR"},
    },
    "poverty_rate": {
        "source": "eurostat:ilc_li02",
        "series_id": "ilc_li02",
        "path": "data/vintages/eurostat/ilc_li02@2026-05-05T205827Z.parquet",
        "sha256": "f49a93b5183acddb13c89b07bba923693eee92a31cf7f065bd0e652e52ea4648",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "source_url": "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/ilc_li02?format=JSON",
        "dimensions": {"freq": "A", "unit": "PC", "indic_il": "LI_R_M60", "sex": "T", "age": "TOTAL"},
    },
}
THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "INCONCLUSIVE",
    "old_window_known": list(YEARS),
    "periphery_countries": list(PERIPHERY),
    "core_countries": list(CORE),
    "eurostat_geo_alias": {"GRC": "EL"},
    "years": list(YEARS),
    "required_country_years_per_indicator": 22,
    "required_total_values": 44,
    "valid_value_min": 0.0,
    "valid_value_max": 100.0,
    "support_max_share_gap_pp": -0.5,
    "support_min_poverty_gap_pp": 2.0,
    "refute_min_share_gap_pp": 0.5,
    "refute_max_poverty_gap_pp": -2.0,
    "source_files": {
        role: {key: SOURCES[role][key]
               for key in ("source", "path", "sha256", "manifest", "dimensions")}
        for role in ROLES
    },
}
KEY_COLUMNS = {
    role: [*SOURCES[role]["dimensions"], "geo_code", "period"]
    for role in ROLES
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_parquet(path: Path, columns: list[str]) -> list[dict[str, Any]]:
    # pyarrow is loaded only in a preflight or a post-registration run.
    import pyarrow.parquet as pq

    return pq.read_table(path, columns=columns).to_pylist()


def read_candidate_rows(role: str, *, include_value: bool) -> list[dict[str, Any]]:
    """Stream exact selector rows; never materialize the million-row vintage."""
    import pyarrow.parquet as pq

    if include_value:
        registration_files()  # Direct value-reader calls are guarded too.
    columns = [*KEY_COLUMNS[role], *(["value"] if include_value else [])]
    selected = []
    parquet = pq.ParquetFile(ROOT / SOURCES[role]["path"])
    for batch in parquet.iter_batches(batch_size=65_536, columns=columns):
        selected.extend(row for row in batch.to_pylist()
                        if selected_row_key(row, role) is not None)
    return selected


def validate_spec() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    if any((
        spec.get("hypothesis_id") != HID,
        spec.get("version") != 1,
        spec.get("status") != "pre_registered",
        spec.get("topic") != "distribution",
        spec.get("evidence_type") != "descriptive",
        spec.get("covers_claims") != [],
        spec.get("sample", {}).get("countries") != list(COUNTRIES),
        spec.get("sample", {}).get("period") != list(YEARS),
        spec.get("scope", {}).get("countries") != list(COUNTRIES),
        spec.get("scope", {}).get("period") != list(YEARS),
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("falsification", {}).get("test") !=
        "eurozone_fixed_groups_bottom_quintile_share_and_relative_poverty_2008_2014_v2",
        spec.get("falsification", {}).get("threshold") != THRESHOLD,
    )):
        raise ValueError("Eurozone registration differs from frozen runner contract")
    sources = [item.get("source") for item in spec.get("variables", {}).get("outcome", [])]
    if sources != [SOURCES[role]["source"] for role in ROLES]:
        raise ValueError("Eurozone outcome sources changed")
    if not (ROOT / STEELMAN_REL).is_file():
        raise ValueError("Eurozone steelman absent")
    return spec


def verified_sources() -> dict[str, dict[str, Any]]:
    """Verify complete file bytes and tracked fetch records, not values."""
    verified = {}
    for role in ROLES:
        source = SOURCES[role]
        path = (ROOT / source["path"]).resolve()
        if not path.is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError(f"missing or nonlocal source: {source['path']}")
        if sha256(path) != source["sha256"]:
            raise ValueError(f"source hash mismatch: {source['path']}")
        manifest_path = ROOT / source["manifest"]
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        entries = [item for item in manifest.get("entries", [])
                   if item.get("parquet_path") == source["path"]]
        if len(entries) != 1 or any((
            entries[0].get("publisher") != "eurostat",
            entries[0].get("series_id") != source["series_id"],
            entries[0].get("sha256") != source["sha256"],
            entries[0].get("source_url") != source["source_url"],
        )):
            raise ValueError(f"source fetch manifest mismatch: {source['path']}")
        verified[role] = {**source, "manifest_sha256": sha256(manifest_path)}
    return verified


def selected_keys(rows: list[dict[str, Any]], role: str) -> list[tuple[str, int]]:
    selected: list[tuple[str, int]] = []
    for row in rows:
        key = selected_row_key(row, role)
        if key is not None:
            selected.append(key)
    return selected


def selected_row_key(row: dict[str, Any], role: str) -> tuple[str, int] | None:
    if any(row.get(key) != expected
           for key, expected in SOURCES[role]["dimensions"].items()):
        return None
    geo = row.get("geo_code")
    if geo not in ISO_CODES or str(row.get("period")) not in {"2008", "2014"}:
        return None
    return ISO_CODES[geo], int(row["period"])


def complete_keys(keys: list[tuple[str, int]], role: str) -> None:
    expected = {(country, year) for country in COUNTRIES for year in YEARS}
    if len(keys) != len(set(keys)) or set(keys) != expected:
        raise ValueError(f"{role} must have all 22 unique fixed country-year keys")


def preflight() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Only hashes, manifests, schema/dimension keys; never value or null mask."""
    validate_spec()
    source_info = verified_sources()
    counts = {}
    for role in ROLES:
        rows = read_candidate_rows(role, include_value=False)
        keys = selected_keys(rows, role)
        complete_keys(keys, role)
        counts[role] = len(keys)
    return {
        "passed": True, "country_year_keys_by_indicator": counts,
        "required_total_values": 44,
        "values_accessed": False, "value_completeness_unchecked": True,
        "period_semantics": "2008 and 2014 EU-SILC survey-wave labels, not literal income calendar years",
        "quality_flags": "not preserved in pinned Parquets; selected status flags uninspected",
        "years": list(YEARS), "periphery_countries": list(PERIPHERY),
        "core_countries": list(CORE),
    }, source_info


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require exact first-addition bytes for all registration files."""
    records = []
    additions = []
    for relative in REGISTRATION_FILES:
        current = (ROOT / relative).read_bytes()
        head = _git("show", f"HEAD:{relative}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit exact registration before outcome access: {relative}")
        history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative)
        commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
        if history.returncode or not commits:
            raise RuntimeError(f"no first-addition commit for {relative}")
        additions.append(commits[0])
        records.append({"path": relative, "sha256": hashlib.sha256(current).hexdigest()})
    if len(set(additions)) != 1:
        raise RuntimeError("Eurozone spec, steelman, and runner need one first-addition commit")
    first = additions[0]
    for relative in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{relative}")
        if frozen.returncode or frozen.stdout != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration changed since first addition: {relative}")
    tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if tree.returncode or tree.stdout.strip():
        raise RuntimeError("Eurozone run artifacts existed in registration commit")
    return first, records


def classify(share_gap_pp: float, poverty_gap_pp: float) -> tuple[str, str]:
    if share_gap_pp <= -0.5 and poverty_gap_pp >= 2.0:
        return "SUPPORTED", "both predeclared relative periphery-versus-core change thresholds cleared"
    if share_gap_pp >= 0.5 and poverty_gap_pp <= -2.0:
        return "REFUTED", "both predeclared relative reverse-direction change thresholds cleared"
    return "PARTIAL", "complete direct measures did not clear either joint directional gate"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    """Guard even direct calls before any candidate value is loaded."""
    registration_files()
    changes: dict[str, dict[str, float]] = {}
    for role in ROLES:
        rows = read_candidate_rows(role, include_value=True)
        keys = selected_keys(rows, role)
        complete_keys(keys, role)
        values: dict[tuple[str, int], float] = {}
        for row in rows:
            key = selected_row_key(row, role)
            if key is None:
                continue
            raw = row["value"]
            if raw is None:
                raise ValueError(f"{role} missing value: {key}")
            value = float(raw)
            if not math.isfinite(value) or not 0.0 <= value <= 100.0:
                raise ValueError(f"{role} nonfinite or out-of-range value: {key}")
            values[key] = value
        if len(values) != 22:
            raise ValueError(f"{role} fewer than 22 complete values")
        changes[role] = {
            country: values[(country, 2014)] - values[(country, 2008)]
            for country in COUNTRIES
        }
    group_means = {
        role: {
            "periphery_mean_change_pp": float(statistics.mean(changes[role][c]
                                                             for c in PERIPHERY)),
            "core_mean_change_pp": float(statistics.mean(changes[role][c]
                                                        for c in CORE)),
        }
        for role in ROLES
    }
    share_gap = (group_means["income_share"]["periphery_mean_change_pp"]
                 - group_means["income_share"]["core_mean_change_pp"])
    poverty_gap = (group_means["poverty_rate"]["periphery_mean_change_pp"]
                   - group_means["poverty_rate"]["core_mean_change_pp"])
    label, reason = classify(share_gap, poverty_gap)
    estimate = {
        "method": "equal-country mean differences between 2008 and 2014 EU-SILC survey-wave observations, periphery minus core; descriptive",
        "n_countries": 11, "n_country_years_per_indicator": 22,
        "n_complete_values": 44,
        "group_means": group_means,
        "bottom_quintile_share_gap_pp": share_gap,
        "relative_poverty_rate_gap_pp": poverty_gap,
        "country_changes_pp": changes,
    }
    return label, reason, estimate


def calculate() -> tuple[dict[str, Any], dict[str, dict[str, Any]] | None,
                         str, str, dict[str, Any] | None]:
    try:
        gate, sources = preflight()
    except (ValueError, FileNotFoundError, KeyError, TypeError, OSError, ImportError) as error:
        reason = f"pinned source or structural key gate failed: {type(error).__name__}: {error}"
        return {"passed": False, "values_accessed": False, "method_failure": reason}, None, "INCONCLUSIVE", reason, None
    try:
        label, reason, estimate = evaluate()
    except (ValueError, TypeError, KeyError, OverflowError, ImportError) as error:
        reason = f"registered complete-value gate failed: {type(error).__name__}: {error}"
        return gate, sources, "INCONCLUSIVE", reason, None
    return gate, sources, label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        f'"""Read-only exact replay of {HID}."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), "
        "'--check'], cwd=root))\n"
    )


def coefficient_rows(estimate: dict[str, Any] | None) -> list[dict[str, Any]]:
    if estimate is None:
        return []
    rows = []
    for role in ROLES:
        for group in ("periphery", "core"):
            rows.append({"metric": f"{role}_{group}_mean_change_pp",
                         "estimate": estimate["group_means"][role][f"{group}_mean_change_pp"],
                         "n_countries": len(PERIPHERY if group == "periphery" else CORE)})
    rows.extend([
        {"metric": "bottom_quintile_share_gap_pp",
         "estimate": estimate["bottom_quintile_share_gap_pp"], "n_countries": 11},
        {"metric": "relative_poverty_rate_gap_pp",
         "estimate": estimate["relative_poverty_rate_gap_pp"], "n_countries": 11},
    ])
    return rows


def write_coefficients(path: Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema([
        pa.field("metric", pa.string()),
        pa.field("estimate", pa.float64()),
        pa.field("n_countries", pa.int32()),
    ])
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)


def artifacts(stamp: str, first_commit: str, registration: list[dict[str, str]],
              gate: dict[str, Any], sources: dict[str, dict[str, Any]] | None,
              label: str, reason: str, estimate: dict[str, Any] | None) -> dict[str, Any]:
    limitations = [
        "The old same-commit inconclusive result and 2008/2014 survey-wave comparison were known before this registration.",
        "Survey-wave labels are not literal income calendar years; income usually refers to 2007/2013, while Ireland used rolling 12-month reference periods.",
        "The local Eurostat vintages omit observation status flags; selected flags were not inspected and flag-clean comparability is unverified.",
        "The rule measures relative group-change gaps; support does not require an absolute periphery share fall or poverty-rate rise.",
        "This is descriptive calibration in the old survey period, not an out-of-time or causal replication.",
        "No narrative consolidation shocks or identified treatment/control contrast are present.",
        "The relative poverty rate is not an absolute poverty or real-income measure.",
        "Eurostat source vintages are local ignored files needed for exact replay.",
        "No automatic position-claim or scoreboard credit follows from this result.",
    ]
    source_list = [sources[role] for role in ROLES] if sources else []
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "method_valid": estimate is not None,
        "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": first_commit, "template": "descriptive",
        "old_hypothesis_id": OLD_ID, "old_result_seen": "INCONCLUSIVE",
        "preflight": gate, "estimate": estimate, "limitations": limitations,
        "flag_clean_verified": False,
        "data_status": {
            "input_status": "verified" if estimate is not None else "unverified",
            "variables_missing": [] if estimate is not None else ["complete_direct_endpoints"],
            "input_vintages": [s["path"] for s in source_list],
            "quality_flags": "not preserved; selected flags uninspected",
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": first_commit, "status": label,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "INCONCLUSIVE",
        "registration_files": registration,
        "vintages": source_list, "derived_sample": gate,
        "quality_flags": "not preserved; selected flags uninspected",
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "distribution"},
        "preregistration": {"spec_commit": first_commit, "steelman": STEELMAN_REL,
                            "registration_files": registration, "gate": THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": source_list, "survey_wave_labels": list(YEARS),
                 "income_reference_period": "usually prior calendar year; Ireland rolling 12 months before interview",
                 "quality_flags": "not preserved; selected flags uninspected"},
        "results": estimate, "limitations": limitations,
    }
    card = (
        f"# Result card: {HID}\n\n"
        f"Verdict: **{label}**. {reason}.\n\n"
        f"Old study: `{OLD_ID}` (INCONCLUSIVE, known before registration).\n"
        f"Preregistration commit: `{first_commit}`. Wave labels: 2008 and 2014.\n"
        "Income usually refers to 2007/2013; Ireland used rolling 12 months before interview.\n"
        "Estimator: fixed-group equal-country mean differences between survey-wave observations.\n"
        "The rule concerns relative changes and can clear without an absolute periphery share fall or poverty-rate rise.\n\n"
        f"Registered measurements: {json.dumps(estimate, sort_keys=True) if estimate is not None else 'unavailable'}.\n\n"
        "The pinned vintages omit observation status flags; selected flags were not inspected, so flag-clean comparability is unverified.\n"
        "This comparison does not identify austerity effects and supplies no automatic claim or scoreboard credit.\n"
    )
    chart = {"hypothesis_id": HID, "verdict": label,
             "estimate": estimate, "threshold": THRESHOLD}
    return {
        "diagnostics.json": json.dumps(diagnostics, indent=2) + "\n",
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False),
        "result_card.md": card,
        "chart_data.json": json.dumps(chart, indent=2) + "\n",
        "replication.py": replication_wrapper(),
        "coefficient_rows": coefficient_rows(estimate),
    }


def run_once() -> dict[str, Any]:
    first_commit, registration = registration_files()  # Before value access.
    run_dir = ROOT / RUN_REL
    if run_dir.exists():
        raise FileExistsError(f"run already exists: {run_dir}; use --check")
    gate, sources, label, reason, estimate = calculate()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = artifacts(stamp, first_commit, registration, gate, sources,
                      label, reason, estimate)
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{HID}-", dir=run_dir.parent) as temp:
        temp_dir = Path(temp)
        (temp_dir / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
        for name, content in files.items():
            if name != "coefficient_rows":
                (temp_dir / name).write_text(content, encoding="utf-8")
        write_coefficients(temp_dir / "coefficients.parquet", files["coefficient_rows"])
        temp_dir.rename(run_dir)
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "estimate": estimate, "wrote_files": True}


def same_numbers(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            same_numbers(actual[key], expected[key]) for key in expected)
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            same_numbers(a, e) for a, e in zip(actual, expected))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and float(actual) == float(expected)
    return actual == expected


def check_once() -> dict[str, Any]:
    first_commit, registration = registration_files()  # Before value access.
    run_dir = ROOT / RUN_REL
    stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    gate, sources, label, reason, estimate = calculate()
    expected = artifacts(stored["run_utc"], first_commit, registration,
                         gate, sources, label, reason, estimate)
    for name in ("diagnostics.json", "manifest.yaml", "evidence_packet.yaml",
                 "result_card.md", "chart_data.json", "replication.py"):
        if (run_dir / name).read_text(encoding="utf-8") != expected[name]:
            raise AssertionError(f"stored Eurozone packet differs from pinned replay: {name}")
    if (run_dir / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes():
        raise AssertionError("stored Eurozone hypothesis snapshot differs")
    actual_coefficients = read_parquet(run_dir / "coefficients.parquet",
                                       ["metric", "estimate", "n_countries"])
    if not same_numbers(actual_coefficients, expected["coefficient_rows"]):
        raise AssertionError("stored Eurozone coefficients differ from pinned replay")
    return {"hypothesis_id": HID, "verified": True,
            "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and keys only")
    mode.add_argument("--run", action="store_true", help="guarded first run")
    mode.add_argument("--check", action="store_true", help="read-only exact replay")
    args = parser.parse_args()
    if args.run:
        result = run_once()
    elif args.check:
        result = check_once()
    else:
        result = preflight()[0]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
