#!/usr/bin/env python3
"""Two source-pinned descriptive holdouts with a commit gate before outcome access.

--preflight hashes pinned inputs and reads only date/country/indicator keys.
--run requires all registration files unchanged since their joint first-addition
commit before any held-out value read. --check replays a stored packet read-only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_temporal_calibration_holdouts_v2.py"
CANADA = "canada_gdp_pc_2024_2025_peer_holdout_v2"
RRP = "fed_on_rrp_2025_durability_holdout_v2"
SPEC_RELS = {
    "canada": f"hypotheses/growth/{CANADA}.yaml",
    "rrp": f"hypotheses/monetary/{RRP}.yaml",
}
STEELMAN_RELS = {
    "canada": f"hypotheses/steelman/{CANADA}.md",
    "rrp": f"hypotheses/steelman/{RRP}.md",
}
HIDS = {"canada": CANADA, "rrp": RRP}
OLD_IDS = {
    "canada": "canada_gdp_per_capita_stagnation_post_2015",
    "rrp": "financial_fed_reverse_repo_facility_usage_2021_2024",
}
REGISTRATION_FILES = (
    SPEC_RELS["canada"], STEELMAN_RELS["canada"],
    SPEC_RELS["rrp"], STEELMAN_RELS["rrp"], RUNNER_REL,
)
CANADA_COUNTRIES = ("CAN", "USA", "AUS", "NZL", "GBR", "NOR", "CHE")
CANADA_YEARS = (2024, 2025)
RRP_QUARTERS = ("2025Q1", "2025Q2", "2025Q3", "2025Q4")
SOURCES = {
    "canada": {
        "publisher": "world_bank_wdi", "series_id": "NY.GDP.PCAP.PP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.PP.KD@2026-05-05T194648Z.parquet",
        "sha256": "6432d570bd5e7d94d659d310c48454caedb7b105db0bfeebbe1e44189c63ecfb",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "source_url": "https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.PP.KD?format=json",
    },
    "rrp": {
        "publisher": "fred", "series_id": "RRPONTSYD",
        "path": "data/vintages/fred/RRPONTSYD@2026-04-30T115134Z.parquet",
        "sha256": "4ed716e07b2843a319510dc5074231a33e3afe08706ebc9f6546b62624093335",
        "custody_manifest": "engine/runs/financial_fed_reverse_repo_facility_usage_2021_2024/manifest.yaml",
        "source_url": "https://fred.stlouisfed.org/series/RRPONTSYD",
        "fetch_time_manifest": None,
        "custody_scope": "old run's SHA-pinned local file plus official FRED series metadata; original fetch transaction unverified",
    },
}
THRESHOLDS = {
    "canada": {
        "old_hypothesis_id": OLD_IDS["canada"], "old_result_seen": "SUPPORTED",
        "focal_country": "CAN", "peer_countries": list(CANADA_COUNTRIES[1:]),
        "holdout_years": list(CANADA_YEARS), "minimum_countries": 7,
        "minimum_country_years": 14,
        "support_max_canada_log_growth": 0.0, "support_max_peer_gap": -0.01,
        "refute_min_canada_log_growth_exclusive": 0.0, "refute_min_peer_gap": 0.01,
        "source_file": {key: SOURCES["canada"][key]
                        for key in ("path", "sha256", "manifest")},
    },
    "rrp": {
        "old_hypothesis_id": OLD_IDS["rrp"], "old_result_seen": "SUPPORTED",
        "holdout_year": 2025, "quarters": list(RRP_QUARTERS),
        "minimum_unique_days_per_quarter": 55,
        "support_quarter_median_usd_bn_exclusive_max": 500.0,
        "refute_quarter_median_usd_bn_min": 1000.0,
        "refute_min_quarters": 2,
        "source_file": {key: SOURCES["rrp"][key]
                        for key in ("path", "sha256", "custody_manifest", "source_url",
                                    "fetch_time_manifest")},
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_parquet(path: Path, columns: list[str]) -> list[dict[str, Any]]:
    # Imported only when a preflight or run actually needs the local raw vintage.
    import pyarrow.parquet as pq

    return pq.read_table(path, columns=columns).to_pylist()


def _write_coefficients(path: Path, rows: list[dict[str, Any]]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    schema = pa.schema([
        pa.field("metric", pa.string()), pa.field("estimate", pa.float64()),
        pa.field("n_obs", pa.int32()),
    ])
    pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)


def _read_coefficients(path: Path) -> list[dict[str, Any]]:
    return _read_parquet(path, ["metric", "estimate", "n_obs"])


def validate_spec(study: str) -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_RELS[study]).read_text(encoding="utf-8"))
    expected_countries = list(CANADA_COUNTRIES) if study == "canada" else ["USA"]
    expected_period = list(CANADA_YEARS) if study == "canada" else [2025, 2025]
    if any((
        spec.get("hypothesis_id") != HIDS[study],
        spec.get("status") != "pre_registered",
        spec.get("evidence_type") != "descriptive",
        spec.get("covers_claims") != [],
        spec.get("sample", {}).get("countries") != expected_countries,
        spec.get("sample", {}).get("period") != expected_period,
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_RELS[study],
        spec.get("falsification", {}).get("threshold") != THRESHOLDS[study],
    )):
        raise ValueError(f"{study} registration differs from the frozen runner contract")
    expected_source = ("world_bank_wdi:NY.GDP.PCAP.PP.KD" if study == "canada"
                       else "fred:RRPONTSYD")
    if [item.get("source") for item in spec.get("variables", {}).get("outcome", [])] != [expected_source]:
        raise ValueError(f"{study} outcome source changed")
    return spec


def verified_source(study: str) -> dict[str, Any]:
    source = SOURCES[study]
    path = ROOT / source["path"]
    if sha256(path) != source["sha256"]:
        raise ValueError(f"pinned source hash mismatch: {source['path']}")
    manifest_rel = source.get("manifest", source.get("custody_manifest"))
    assert manifest_rel is not None
    manifest_path = ROOT / manifest_rel
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if study == "canada":
        entries = [entry for entry in manifest.get("entries", [])
                   if entry.get("parquet_path") == source["path"]]
        if len(entries) != 1 or any((
            entries[0].get("publisher") != source["publisher"],
            entries[0].get("series_id") != source["series_id"],
            entries[0].get("sha256") != source["sha256"],
            entries[0].get("source_url") != source["source_url"],
        )):
            raise ValueError("Canada source fetch manifest does not match pinned vintage")
    else:
        comparison = manifest.get("vintages", {}).get("comparison_primary", {})
        outcome = manifest.get("vintages", {}).get("outcome_on_rrp_usage_daily_1", {})
        if any((
            manifest.get("hypothesis_id") != OLD_IDS[study],
            comparison.get("vintage_file") != source["path"],
            comparison.get("sha256") != source["sha256"],
            outcome.get("publisher") != source["publisher"],
            outcome.get("series") != source["series_id"],
            outcome.get("sha256") != source["sha256"],
        )):
            raise ValueError("RRP old-run custody manifest does not match pinned vintage")
    return {**source, "custody_file": manifest_rel,
            "custody_file_sha256": sha256(manifest_path)}


def _quarter(day: str) -> str:
    parsed = date.fromisoformat(day)
    return f"{parsed.year}Q{(parsed.month - 1) // 3 + 1}"


def preflight(study: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Read source integrity and selected dimension keys; no outcome values."""
    validate_spec(study)
    source = verified_source(study)
    if study == "canada":
        rows = _read_parquet(ROOT / source["path"], ["country_iso3", "year", "indicator_id"])
        expected = {(country, year) for country in CANADA_COUNTRIES for year in CANADA_YEARS}
        selected = [(row["country_iso3"], int(row["year"])) for row in rows
                    if row["country_iso3"] in CANADA_COUNTRIES
                    and int(row["year"]) in CANADA_YEARS
                    and row["indicator_id"] == source["series_id"]]
        if len(selected) != len(set(selected)) or set(selected) != expected:
            raise ValueError("Canada exact fixed country-year keys are incomplete or duplicated")
        gate = {"passed": True, "country_year_keys": len(selected),
                "minimum_country_years": len(expected),
                "years": list(CANADA_YEARS), "heldout_values_accessed": False,
                "value_completeness_unchecked": True}
    else:
        rows = _read_parquet(ROOT / source["path"], ["date"])
        selected = [str(row["date"])[:10] for row in rows
                    if str(row["date"])[:4] == "2025"]
        if len(selected) != len(set(selected)):
            raise ValueError("duplicate 2025 RRP date keys")
        counts = {quarter: sum(_quarter(day) == quarter for day in selected)
                  for quarter in RRP_QUARTERS}
        if any(count < 55 for count in counts.values()):
            raise ValueError("RRP structural dates fewer than 55 in a fixed quarter")
        gate = {"passed": True, "date_keys_2025": len(selected),
                "date_keys_by_quarter": counts, "minimum_days_per_quarter": 55,
                "heldout_values_accessed": False, "value_completeness_unchecked": True}
    return gate, source


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require identical HEAD and joint first-addition bytes, without early results."""
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
        raise RuntimeError("both holdouts and runner must share one first-addition commit")
    first = additions[0]
    for relative in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{relative}")
        if frozen.returncode or frozen.stdout != (ROOT / relative).read_bytes():
            raise RuntimeError(f"registration changed since first addition: {relative}")
    for study in HIDS:
        run_rel = f"engine/runs/{HIDS[study]}"
        tree = _git("ls-tree", "-r", "--name-only", first, "--", run_rel)
        if tree.returncode or tree.stdout.strip():
            raise RuntimeError(f"run artifacts existed at registration: {run_rel}")
    return first, records


def classify_canada(growth: float, gap: float) -> tuple[str, str]:
    if growth <= 0 and gap <= -0.01:
        return "SUPPORTED", "Canada's new interval is nonpositive and at least one log percentage point below peers"
    if growth > 0 and gap >= 0.01:
        return "REFUTED", "Canada's new interval is positive and at least one log percentage point above peers"
    return "PARTIAL", "the two registered Canada durability conditions do not jointly clear a directional gate"


def classify_rrp(medians: dict[str, float]) -> tuple[str, str]:
    if all(medians[quarter] < 500 for quarter in RRP_QUARTERS):
        return "SUPPORTED", "all four 2025 quarter medians are below USD 500 billion"
    if sum(medians[quarter] >= 1000 for quarter in RRP_QUARTERS) >= 2:
        return "REFUTED", "at least two 2025 quarter medians are at or above USD 1000 billion"
    return "PARTIAL", "the four quarter medians clear neither registered durability nor rebound gate"


def evaluate(study: str) -> tuple[str, str, dict[str, Any]]:
    """Value access is permitted only after registration_files has passed."""
    source = SOURCES[study]
    if study == "canada":
        rows = _read_parquet(ROOT / source["path"],
                             ["country_iso3", "year", "indicator_id", "value"])
        values: dict[tuple[str, int], float] = {}
        for row in rows:
            country = row["country_iso3"]
            year = int(row["year"])
            if country not in CANADA_COUNTRIES or year not in CANADA_YEARS:
                continue
            if row["indicator_id"] != source["series_id"]:
                continue
            key = (country, year)
            if key in values:
                raise ValueError("duplicate Canada country-year value")
            value = float(row["value"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Canada country-year value is missing, nonfinite, or nonpositive")
            values[key] = value
        if len(values) != 14:
            raise ValueError("fewer than 14 complete Canada country-year values")
        growth = {country: math.log(values[(country, 2025)] / values[(country, 2024)])
                  for country in CANADA_COUNTRIES}
        peer_median = float(statistics.median(growth[country]
                                             for country in CANADA_COUNTRIES[1:]))
        canada_growth = growth["CAN"]
        gap = canada_growth - peer_median
        label, reason = classify_canada(canada_growth, gap)
        estimate = {"method": "fixed six-peer median of 2024-to-2025 log changes, descriptive",
                    "n_countries": 7, "n_country_years": 14,
                    "canada_log_growth": canada_growth,
                    "peer_median_log_growth": peer_median, "peer_gap_log_points": gap}
    else:
        rows = _read_parquet(ROOT / source["path"], ["date", "value"])
        amounts: dict[str, list[float]] = {quarter: [] for quarter in RRP_QUARTERS}
        seen = set()
        for row in rows:
            day = str(row["date"])[:10]
            if day[:4] != "2025":
                continue
            if day in seen:
                raise ValueError("duplicate RRP daily value date")
            seen.add(day)
            if row["value"] is None:
                continue
            value = float(row["value"])
            if not math.isfinite(value) or value < 0:
                raise ValueError("RRP daily amount is nonfinite or negative")
            amounts[_quarter(day)].append(value)
        counts = {quarter: len(amounts[quarter]) for quarter in RRP_QUARTERS}
        if any(count < 55 for count in counts.values()):
            raise ValueError("fewer than 55 finite RRP daily amounts in a fixed quarter")
        medians = {quarter: float(statistics.median(amounts[quarter]))
                   for quarter in RRP_QUARTERS}
        label, reason = classify_rrp(medians)
        estimate = {"method": "four fixed 2025 calendar-quarter daily medians, USD billions",
                    "n_daily_observations": sum(counts.values()),
                    "n_days_by_quarter": counts, "quarter_medians_usd_bn": medians}
    return label, reason, estimate


def calculate(study: str) -> tuple[dict[str, Any], dict[str, Any] | None,
                                   str, str, dict[str, Any] | None]:
    try:
        gate, source = preflight(study)
    except (ValueError, FileNotFoundError, KeyError, TypeError, OSError, ImportError) as error:
        reason = f"pinned source or structural key gate failed: {type(error).__name__}: {error}"
        return {"passed": False, "heldout_values_accessed": False, "method_failure": reason}, None, "INCONCLUSIVE", reason, None
    try:
        label, reason, estimate = evaluate(study)
    except (ValueError, TypeError, KeyError, OverflowError, ImportError) as error:
        reason = f"registered measured endpoint invalid: {type(error).__name__}: {error}"
        return gate, source, "INCONCLUSIVE", reason, None
    return gate, source, label, reason, estimate


def replication_wrapper(study: str) -> str:
    return (
        "#!/usr/bin/env python3\n"
        f'"""Read-only exact replay of {HIDS[study]}."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), "
        f"'--study', {study!r}, '--check'], cwd=root))\n"
    )


def coefficient_rows(study: str, estimate: dict[str, Any] | None) -> list[dict[str, Any]]:
    if estimate is None:
        return []
    if study == "canada":
        return [{"metric": key, "estimate": float(estimate[key]), "n_obs": 14}
                for key in ("canada_log_growth", "peer_median_log_growth", "peer_gap_log_points")]
    return [{"metric": f"{quarter}_median_usd_bn",
             "estimate": float(estimate["quarter_medians_usd_bn"][quarter]),
             "n_obs": estimate["n_days_by_quarter"][quarter]}
            for quarter in RRP_QUARTERS]


def artifacts(study: str, stamp: str, prereg_commit: str,
              registration: list[dict[str, str]], gate: dict[str, Any],
              source: dict[str, Any] | None, label: str, reason: str,
              estimate: dict[str, Any] | None) -> dict[str, Any]:
    hid = HIDS[study]
    run_rel = f"engine/runs/{hid}"
    limitations = [
        "The old same-commit SUPPORTED result was known before this new registration.",
        "This later measured endpoint is descriptive calibration only; no causal or automatic scoreboard credit.",
        ("One annual interval cannot establish a productivity or policy effect."
         if study == "canada" else
         "RRP amounts do not identify the Treasury-bill absorption mechanism."),
    ]
    diagnostics = {
        "hypothesis_id": hid, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "method_valid": label != "INCONCLUSIVE",
        "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "old_hypothesis_id": OLD_IDS[study], "old_result_seen": "SUPPORTED",
        "preflight": gate, "estimate": estimate, "limitations": limitations,
        "data_status": {"input_status": "verified" if estimate is not None else "unverified",
                        "variables_missing": [] if estimate is not None else ["registered_endpoint_invalid"],
                        "input_vintages": [source["path"]] if source else []},
    }
    manifest = {
        "hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "old_hypothesis_id": OLD_IDS[study], "old_result_seen": "SUPPORTED",
        "registration_files": registration,
        "vintages": [source] if source else [], "derived_sample": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hid, "path": SPEC_RELS[study],
                       "topic": "growth" if study == "canada" else "monetary"},
        "preregistration": {"spec_commit": prereg_commit,
                            "steelman": STEELMAN_RELS[study],
                            "registration_files": registration,
                            "gate": THRESHOLDS[study]},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {run_rel}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": [source] if source else [],
                 "heldout_window": [2024, 2025] if study == "canada" else [2025]},
        "results": estimate, "limitations": limitations,
    }
    card = (f"# Result card: {hid}\n\nVerdict: **{label}**. {reason}.\n\n"
            f"Old study: `{OLD_IDS[study]}` (SUPPORTED, known before registration).\n"
            f"Preregistration commit: `{prereg_commit}`.\n"
            f"Window: {'2024–25' if study == 'canada' else '2025 calendar quarters'}.\n"
            "Estimator: fixed descriptive change/median rule.\n\n"
            f"Registered measurements: {json.dumps(estimate, sort_keys=True) if estimate is not None else 'unavailable'}.\n\n"
            "This result supplies no causal policy credit and no automatic scoreboard credit.\n")
    chart = {"hypothesis_id": hid, "verdict": label,
             "estimate": estimate, "threshold": THRESHOLDS[study]}
    return {"diagnostics.json": json.dumps(diagnostics, indent=2) + "\n",
            "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False),
            "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False),
            "result_card.md": card,
            "chart_data.json": json.dumps(chart, indent=2) + "\n",
            "replication.py": replication_wrapper(study),
            "coefficient_rows": coefficient_rows(study, estimate)}


def run_one(study: str) -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # Must precede all value access.
    run_dir = ROOT / "engine" / "runs" / HIDS[study]
    if run_dir.exists():
        raise FileExistsError(f"run already exists: {run_dir}; use --check")
    gate, source, label, reason, estimate = calculate(study)
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    files = artifacts(study, stamp, prereg_commit, registration, gate, source,
                      label, reason, estimate)
    run_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{HIDS[study]}-", dir=run_dir.parent) as temp:
        temp_dir = Path(temp)
        (temp_dir / "hypothesis.yaml").write_bytes((ROOT / SPEC_RELS[study]).read_bytes())
        for name, content in files.items():
            if name != "coefficient_rows":
                (temp_dir / name).write_text(content, encoding="utf-8")
        _write_coefficients(temp_dir / "coefficients.parquet", files["coefficient_rows"])
        temp_dir.rename(run_dir)
    return {"hypothesis_id": HIDS[study], "verdict": label,
            "run_dir": str(run_dir.relative_to(ROOT)), "wrote_files": True,
            "estimate": estimate}


def _same_numbers(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(
            _same_numbers(actual[key], expected[key]) for key in expected)
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(
            _same_numbers(a, e) for a, e in zip(actual, expected))
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return isinstance(actual, (int, float)) and math.isclose(
            float(actual), float(expected), rel_tol=1e-12, abs_tol=1e-12)
    return actual == expected


def check_one(study: str) -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # Before held-out replay.
    run_dir = ROOT / "engine" / "runs" / HIDS[study]
    stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    gate, source, label, reason, estimate = calculate(study)
    expected = artifacts(study, stored["run_utc"], prereg_commit, registration,
                         gate, source, label, reason, estimate)
    for name in ("diagnostics.json", "manifest.yaml", "evidence_packet.yaml",
                 "result_card.md", "chart_data.json", "replication.py"):
        if (run_dir / name).read_text(encoding="utf-8") != expected[name]:
            raise AssertionError(f"stored {study} packet does not match pinned replay: {name}")
    if (run_dir / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_RELS[study]).read_bytes():
        raise AssertionError(f"stored {study} hypothesis snapshot differs")
    if not _same_numbers(_read_coefficients(run_dir / "coefficients.parquet"),
                         expected["coefficient_rows"]):
        raise AssertionError(f"stored {study} coefficients differ from pinned replay")
    return {"hypothesis_id": HIDS[study], "verified": True,
            "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--study", required=True, choices=tuple(HIDS))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and keys only")
    mode.add_argument("--run", action="store_true", help="guarded first run after preregistration")
    mode.add_argument("--check", action="store_true", help="read-only exact replay")
    args = parser.parse_args()
    if args.run:
        result = run_one(args.study)
    elif args.check:
        result = check_one(args.study)
    else:
        result = preflight(args.study)[0]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
