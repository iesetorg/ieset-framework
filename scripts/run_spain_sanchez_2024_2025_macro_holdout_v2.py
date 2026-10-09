#!/usr/bin/env python3
"""Source-pinned descriptive Spain holdout with a commit gate before value access.

Default/--preflight checks source hashes and selected key coverage, never the
2024-25 values. --run requires the unchanged first-addition registration in
HEAD before reading values or writing standard run artifacts. --check replays
an existing packet without writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "spain_sanchez_2024_2025_macro_holdout_v2"
OLD_ID = "spain_sanchez_economic_trajectory_2018_2023"
SPEC_REL = f"hypotheses/growth/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
FOCAL = "ESP"
PEERS = ("FRA", "ITA", "PRT", "GRC", "DEU", "NLD", "BEL")
COUNTRIES = (FOCAL, *PEERS)
YEARS = (2024, 2025)
ISO3_TO_EUROSTAT = {
    "ESP": "ES", "FRA": "FR", "ITA": "IT", "PRT": "PT",
    "GRC": "EL", "DEU": "DE", "NLD": "NL", "BEL": "BE",
}
MIN_COUNTRY_YEARS = len(COUNTRIES) * len(YEARS)

SOURCES: dict[str, dict[str, Any]] = {
    "real_gdp": {
        "publisher": "eurostat", "series_id": "nama_10_gdp",
        "path": "data/vintages/eurostat/nama_10_gdp@2026-07-23T154118Z.parquet",
        "sha256": "c02fd991a250c967cd6bd4350cf3bf6cde186bd38acc50a3dd984866415c9824",
        "selector": {"na_item": "B1GQ", "unit": "CLV20_MEUR"},
        "manifest": "data/manifests/fetch_run_2026-07-23T154936Z.yaml",
    },
    "population": {
        "publisher": "eurostat", "series_id": "demo_pjan",
        "path": "data/vintages/eurostat/demo_pjan@2026-05-05T205848Z.parquet",
        "sha256": "c0910d085947e1c95da781ea3679f79909f41cab5c2cf5731db4e8fcf415f3e3",
        "selector": {"unit": "NR", "age": "TOTAL", "sex": "T"},
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
    },
    "employment": {
        "publisher": "eurostat", "series_id": "lfsi_emp_a",
        "path": "data/vintages/eurostat/lfsi_emp_a@2026-04-30T115837Z.parquet",
        "sha256": "974340d9c78f8def6f7dca019bad810e31c5ca595552451bcc58361b57d22ec0",
        "selector": {"indic_em": "EMP_LFS", "age": "Y15-64", "sex": "T", "unit": "PC_POP"},
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
    },
}

EXPECTED_THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "PARTIAL",
    "focal_country": FOCAL,
    "peer_countries": list(PEERS),
    "holdout_years": list(YEARS),
    "minimum_countries": len(COUNTRIES),
    "minimum_country_years_per_source": MIN_COUNTRY_YEARS,
    "gdp_growth_gap_support_min": 0.0,
    "employment_change_gap_support_min_pp": 0.0,
    "source_files": {
        name: {key: source[key] for key in ("path", "sha256", "selector")}
        for name, source in SOURCES.items()
    },
}

LIMITATIONS = [
    "Descriptive 2024-25 peer comparison; no causal credit to the 2018 government or any later policy.",
    "The old same-commit PARTIAL result was known before this new registration.",
    "Tourism, migration, labour composition, and country shocks can change these gaps.",
    "This narrow test does not measure the older housing or real-wage claim.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_spec() -> dict[str, Any]:
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text(encoding="utf-8"))
    if any((
        spec.get("hypothesis_id") != HID,
        spec.get("status") != "pre_registered",
        spec.get("evidence_type") != "descriptive",
        spec.get("sample", {}).get("countries") != list(COUNTRIES),
        spec.get("sample", {}).get("period") != list(YEARS),
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
    )):
        raise ValueError("Spain holdout registration differs from frozen runner contract")
    if [item.get("source") for item in spec["variables"]["outcome"]] != [
        "eurostat:nama_10_gdp; eurostat:demo_pjan",
        "eurostat:lfsi_emp_a",
    ]:
        raise ValueError("Spain holdout outcome source changed")
    return spec


def verified_sources() -> list[dict[str, Any]]:
    records = []
    for role, source in SOURCES.items():
        actual = sha256(ROOT / source["path"])
        if actual != source["sha256"]:
            raise ValueError(f"pinned source hash mismatch: {source['path']}")
        manifest_path = ROOT / source["manifest"]
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        entries = [item for item in manifest.get("entries", [])
                   if item.get("parquet_path") == source["path"]]
        expected_url = (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
            f"{source['series_id']}?format=JSON"
        )
        if len(entries) != 1 or any((
            entries[0].get("publisher") != source["publisher"],
            entries[0].get("series_id") != source["series_id"],
            entries[0].get("sha256") != source["sha256"],
            entries[0].get("source_url") != expected_url,
        )):
            raise ValueError(f"pinned source custody mismatch: {source['manifest']}")
        records.append({"role": role, **source, "manifest_sha256": sha256(manifest_path),
                        "source_url": expected_url})
    return records


def _selected_rows(role: str, *, include_value: bool) -> pd.DataFrame:
    """The preflight path reads only dimension keys, never the value column."""
    source = SOURCES[role]
    columns = ["geo_code", "period", *source["selector"]]
    if include_value:
        columns.append("value")
    frame = pd.read_parquet(ROOT / source["path"], columns=columns)
    frame = frame[
        frame["geo_code"].isin(ISO3_TO_EUROSTAT.values())
        & frame["period"].isin([str(year) for year in YEARS])
    ]
    for column, expected in source["selector"].items():
        frame = frame[frame[column] == expected]
    frame = frame[["geo_code", "period"] + (["value"] if include_value else [])].copy()
    if frame.duplicated(["geo_code", "period"]).any():
        raise ValueError(f"duplicate selected country-year keys in {role}")
    return frame


def preflight() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_spec()
    sources = verified_sources()
    expected = {(geo, str(year)) for geo in ISO3_TO_EUROSTAT.values() for year in YEARS}
    coverage: dict[str, int] = {}
    for role in SOURCES:
        keys = _selected_rows(role, include_value=False)
        present = set(zip(keys["geo_code"], keys["period"]))
        coverage[role] = len(present)
        if len(keys) != len(present):
            raise ValueError(f"duplicate selected keys in {role}")
        if present != expected:
            raise ValueError(f"missing or unexpected fixed country-years in {role}")
    gate = {
        "countries": len(COUNTRIES), "years": list(YEARS),
        "country_years_per_source": coverage,
        "minimum_country_years_per_source": MIN_COUNTRY_YEARS,
        "passed": all(count == MIN_COUNTRY_YEARS for count in coverage.values()),
        "heldout_values_accessed": False,
    }
    return gate, sources


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require HEAD and the spec's first-addition commit to have exact bytes."""
    committed: list[dict[str, str]] = []
    for relative_path in REGISTRATION_FILES:
        current = (ROOT / relative_path).read_bytes()
        head = _git("show", f"HEAD:{relative_path}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit the exact registration before value access: {relative_path}")
        committed.append({"path": relative_path, "sha256": hashlib.sha256(current).hexdigest()})
    history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
    if history.returncode or not commits:
        raise RuntimeError("the new spec has no first-addition commit")
    first = commits[0]
    old_run_tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if old_run_tree.returncode or old_run_tree.stdout.strip():
        raise RuntimeError("run artifacts existed at the registration commit")
    for relative_path in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{relative_path}")
        if frozen.returncode or frozen.stdout != (ROOT / relative_path).read_bytes():
            raise RuntimeError(f"registration changed after first-addition commit: {relative_path}")
    return first, committed


def _values(role: str) -> pd.DataFrame:
    frame = _selected_rows(role, include_value=True)
    frame[role] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.drop(columns="value")
    if len(frame) != MIN_COUNTRY_YEARS or not frame[role].map(math.isfinite).all():
        raise ValueError(f"incomplete or nonfinite selected values in {role}")
    if role in {"real_gdp", "population"} and not (frame[role] > 0).all():
        raise ValueError(f"nonpositive GDP or population in {role}")
    if role == "employment" and not frame[role].between(0, 100).all():
        raise ValueError(f"rate outside 0-100 in {role}")
    return frame


def classify(gdp_gap: float, employment_gap_pp: float) -> tuple[str, str]:
    if gdp_gap >= 0.0 and employment_gap_pp >= 0.0:
        return "SUPPORTED", "both registered descriptive gaps are nonnegative"
    if gdp_gap < 0.0 and employment_gap_pp < 0.0:
        return "REFUTED", "both registered descriptive gaps are negative"
    return "PARTIAL", "the registered GDP and employment gaps have split signs"


def evaluate(gate: dict[str, Any]) -> tuple[str, str, dict[str, Any] | None]:
    """This function may read values only after registration_files has passed."""
    if not gate["passed"]:
        return "INCONCLUSIVE", "fixed source coverage failed", None
    panel = _values("real_gdp")
    for role in ("population", "employment"):
        panel = panel.merge(_values(role), on=["geo_code", "period"], validate="one_to_one")
    panel["country_iso3"] = panel["geo_code"].map({v: k for k, v in ISO3_TO_EUROSTAT.items()})
    panel["year"] = panel["period"].astype(int)
    panel["real_gdp_per_resident"] = panel["real_gdp"] / panel["population"]
    wide = panel.pivot(index="country_iso3", columns="year")
    gdp_growth = (wide["real_gdp_per_resident"][2025] / wide["real_gdp_per_resident"][2024]).map(math.log)
    employment_change = wide["employment"][2025] - wide["employment"][2024]
    gdp_peer_median = float(gdp_growth.loc[list(PEERS)].median())
    employment_peer_median = float(employment_change.loc[list(PEERS)].median())
    gdp_gap = float(gdp_growth.loc[FOCAL]) - gdp_peer_median
    employment_gap = float(employment_change.loc[FOCAL]) - employment_peer_median
    label, reason = classify(gdp_gap, employment_gap)
    estimate = {
        "method": "fixed seven-peer median of 2024-to-2025 changes, descriptive",
        "n_countries": len(COUNTRIES), "n_country_years": MIN_COUNTRY_YEARS,
        "gdp_pc_log_growth_spain": float(gdp_growth.loc[FOCAL]),
        "gdp_pc_log_growth_peer_median": gdp_peer_median,
        "gdp_pc_log_growth_gap": gdp_gap,
        "employment_change_spain_pp": float(employment_change.loc[FOCAL]),
        "employment_change_peer_median_pp": employment_peer_median,
        "employment_change_gap_pp": employment_gap,
    }
    return label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of the Spain holdout packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


def evidence_packet(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    sources: list[dict[str, Any]], label: str, reason: str,
    estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "growth"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL,
                            "registration_files": registration, "gate": EXPECTED_THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": sources, "heldout_years": list(YEARS)},
        "results": estimate, "limitations": LIMITATIONS,
    }


def result_card(prereg_commit: str, label: str, reason: str,
                estimate: dict[str, Any] | None) -> str:
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Old study: `{OLD_ID}` (PARTIAL, known before registration).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        f"Sample: Spain and seven fixed euro-area peers, {YEARS[0]}–{YEARS[1]}.\n"
        "Estimator: two descriptive change gaps relative to the peer median.\n"
    )
    if estimate is not None:
        card += (
            f"\nGDP-per-resident log-growth gap: {estimate['gdp_pc_log_growth_gap']:+.8g}.\n"
            f"Employment-rate change gap: {estimate['employment_change_gap_pp']:+.8g} pp.\n"
        )
    return card + "\nThis packet supplies no causal credit to a government, no housing or wage verdict, and no automatic scoreboard credit.\n"


COEFFICIENT_COLUMNS = ("term", "coefficient", "std_error", "p_value", "n_obs", "n_countries")


def artifact_records(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], sources: list[dict[str, Any]], label: str,
    reason: str, estimate: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any], list[dict[str, Any]]]:
    input_valid = gate["passed"] and not (label == "INCONCLUSIVE" and estimate is None)
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "preflight": gate, "estimate": estimate, "old_hypothesis_id": OLD_ID,
        "old_result_seen": "PARTIAL", "limitations": LIMITATIONS,
        "data_status": {
            "variables_missing": [] if input_valid else ["required_endpoint_inputs_unverified"],
            "input_status": "verified" if input_valid else "unverified",
            "input_vintages": [source["path"] for source in sources],
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "PARTIAL",
        "registration_files": registration, "vintages": sources,
        "derived_panel": gate,
    }
    packet = evidence_packet(stamp, prereg_commit, registration, sources, label, reason, estimate)
    card = result_card(prereg_commit, label, reason, estimate)
    chart = {
        "hypothesis_id": HID, "verdict": label, "years": list(YEARS),
        "gdp_pc_log_growth_gap": estimate["gdp_pc_log_growth_gap"] if estimate else None,
        "employment_change_gap_pp": estimate["employment_change_gap_pp"] if estimate else None,
        "registered_zero_threshold": 0.0,
    }
    rows = [] if estimate is None else [
        {"term": "gdp_pc_log_growth_gap", "coefficient": estimate["gdp_pc_log_growth_gap"],
         "std_error": None, "p_value": None, "n_obs": MIN_COUNTRY_YEARS, "n_countries": len(COUNTRIES)},
        {"term": "employment_change_gap_pp", "coefficient": estimate["employment_change_gap_pp"],
         "std_error": None, "p_value": None, "n_obs": MIN_COUNTRY_YEARS, "n_countries": len(COUNTRIES)},
    ]
    return diagnostics, manifest, packet, card, chart, rows


def write_run(
    prereg_commit: str, registration: list[dict[str, str]], gate: dict[str, Any],
    sources: list[dict[str, Any]], label: str, reason: str, estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        stamp, prereg_commit, registration, gate, sources, label, reason, estimate
    )
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(card, encoding="utf-8")
    (RUN_DIR / "replication.py").write_text(replication_wrapper(), encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows, columns=list(COEFFICIENT_COLUMNS)).to_parquet(
        RUN_DIR / "coefficients.parquet", index=False,
    )
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "wrote_files": True, "estimate": estimate}


def calculate() -> tuple[dict[str, Any], list[dict[str, Any]], str, str, dict[str, Any] | None]:
    """Return an explicit inconclusive result when a pinned method gate fails."""
    try:
        gate, sources = preflight()
    except (ValueError, FileNotFoundError, KeyError, OSError) as error:
        reason = f"pinned source or key coverage invalid: {type(error).__name__}: {error}"
        gate = {
            "countries": len(COUNTRIES), "years": list(YEARS),
            "country_years_per_source": {},
            "minimum_country_years_per_source": MIN_COUNTRY_YEARS,
            "passed": False, "heldout_values_accessed": False,
            "method_failure": reason,
        }
        return gate, [], "INCONCLUSIVE", reason, None
    if not gate["passed"]:
        label, reason, estimate = "INCONCLUSIVE", "fixed source coverage failed", None
    else:
        try:
            label, reason, estimate = evaluate(gate)
        except (ValueError, KeyError, OverflowError) as error:
            label, reason, estimate = "INCONCLUSIVE", f"measured endpoint invalid: {error}", None
    return gate, sources, label, reason, estimate


def run_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before all value access
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check for read-only replay")
    gate, sources, label, reason, estimate = calculate()
    return write_run(prereg_commit, registration, gate, sources, label, reason, estimate)


def _estimate_matches(saved: dict[str, Any] | None, fresh: dict[str, Any] | None) -> bool:
    if saved is None or fresh is None:
        return saved is None and fresh is None
    if saved.keys() != fresh.keys():
        return False
    for key in saved:
        old, new = saved[key], fresh[key]
        if isinstance(new, (int, float)) and not isinstance(new, bool):
            if not math.isclose(float(old), float(new), rel_tol=1e-12, abs_tol=1e-12):
                return False
        elif old != new:
            return False
    return True


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before all value access
    stored = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    packet_text = (RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8")
    packet = yaml.safe_load(packet_text)
    card = (RUN_DIR / "result_card.md").read_text(encoding="utf-8")
    chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    wrapper = (RUN_DIR / "replication.py").read_text(encoding="utf-8")
    hypothesis_snapshot = (RUN_DIR / "hypothesis.yaml").read_bytes()
    coefficient_frame = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    gate, sources, label, reason, estimate = calculate()
    expected_stored, expected_manifest, expected_packet, expected_card, expected_chart, expected_rows = artifact_records(
        stored.get("run_utc"), prereg_commit, registration, gate, sources, label, reason, estimate
    )
    actual_except_estimate = {key: value for key, value in stored.items() if key != "estimate"}
    expected_except_estimate = {key: value for key, value in expected_stored.items() if key != "estimate"}
    rows_match = list(coefficient_frame.columns) == list(COEFFICIENT_COLUMNS) and len(coefficient_frame) == len(expected_rows)
    if rows_match:
        for actual, expected in zip(coefficient_frame.to_dict(orient="records"), expected_rows):
            for key in COEFFICIENT_COLUMNS:
                if expected[key] is None:
                    rows_match = rows_match and bool(pd.isna(actual[key]))
                elif isinstance(expected[key], (float, int)):
                    rows_match = rows_match and math.isclose(float(actual[key]), float(expected[key]),
                                                             rel_tol=1e-12, abs_tol=1e-12)
                else:
                    rows_match = rows_match and actual[key] == expected[key]
    if any((
        actual_except_estimate != expected_except_estimate,
        manifest != expected_manifest,
        not _estimate_matches(stored.get("estimate"), estimate),
        packet != expected_packet,
        packet_text != yaml.safe_dump(expected_packet, sort_keys=False),
        card != expected_card,
        chart != expected_chart,
        wrapper != replication_wrapper(),
        hypothesis_snapshot != (ROOT / SPEC_REL).read_bytes(),
        not rows_match,
    )):
        raise AssertionError("stored Spain packet does not match pinned read-only replay")
    return {"hypothesis_id": HID, "verified": True, "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="source hashes and keys only")
    mode.add_argument("--run", action="store_true", help="guarded first run after preregistration")
    mode.add_argument("--check", action="store_true", help="read-only exact replay of stored packet")
    args = parser.parse_args()
    if args.run:
        result = run_one()
    elif args.check:
        result = check_one()
    else:
        result = preflight()[0]
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("passed", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
