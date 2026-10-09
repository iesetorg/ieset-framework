#!/usr/bin/env python3
"""Pinned Germany manufacturing/electricity comparison, guarded before values.

--preflight reads source hashes and selected dimension keys only. --run first
requires an unchanged first-addition Git registration; --check replays a saved
run without writes. The old fitted 2024 WDI value is disclosed, not hidden.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
HID = "germany_2025_manufacturing_electricity_peer_comovement_v2"
OLD_ID = "germany_decline_2018_2025_regulatory_not_fiscal"
SPEC_REL = f"hypotheses/energy/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL)
OLD_DIAGNOSTICS = f"engine/runs/{OLD_ID}/diagnostics.json"
OLD_MANIFEST = f"engine/runs/{OLD_ID}/manifest.yaml"
OLD_DIAGNOSTICS_SHA256 = "6465851fd86e9b9c8afad875c3954cf0025d5a025a3e34a8c7b37a4f5fd0a17d"
OLD_MANIFEST_SHA256 = "1ad033b58c91428159a089a87d0c89e1dc384e563c88567270005feb17608718"
SOURCE_MANIFEST = "data/manifests/fetch_run_2026-07-23T154936Z.yaml"
SOURCE_MANIFEST_SHA256 = "c2215e0e796c4697d0596848a7498c7a369e5fb2e9baed660e25a8791ffa580d"
FOCAL = "DEU"
PEERS = ("FRA", "NLD", "BEL", "ITA", "ESP", "POL", "CZE", "AUT", "SWE", "FIN")
COUNTRIES = (FOCAL, *PEERS)
ISO3_TO_EUROSTAT = {
    "DEU": "DE", "FRA": "FR", "NLD": "NL", "BEL": "BE", "ITA": "IT",
    "ESP": "ES", "POL": "PL", "CZE": "CZ", "AUT": "AT", "SWE": "SE", "FIN": "FI",
}
MANUFACTURING_PERIODS = ("2024", "2025")
ELECTRICITY_PERIODS = ("2024-S1", "2024-S2", "2025-S1", "2025-S2")
MIN_MANUFACTURING_KEYS = len(COUNTRIES) * len(MANUFACTURING_PERIODS)
MIN_ELECTRICITY_KEYS = len(COUNTRIES) * len(ELECTRICITY_PERIODS)
SOURCES: dict[str, dict[str, Any]] = {
    "manufacturing": {
        "publisher": "eurostat", "series_id": "nama_10_a10",
        "path": "data/vintages/eurostat/nama_10_a10@2026-07-23T154308Z.parquet",
        "sha256": "33d3a3a8023d474185c1dfdaad4975ad6c81afc5e95bc92fe49bb6490dcc463c",
        "selector": {"freq": "A", "unit": "CLV_I20", "nace_r2": "C", "na_item": "B1G"},
        "periods": MANUFACTURING_PERIODS,
    },
    "electricity": {
        "publisher": "eurostat", "series_id": "nrg_pc_205",
        "path": "data/vintages/eurostat/nrg_pc_205@2026-07-23T154402Z.parquet",
        "sha256": "ca3c2e524ba47c219f2e1dff0927f2d366d8e11d2c0418681f66891de51b00f4",
        "selector": {
            "freq": "S", "siec": "E7000", "nrg_cons": "MWH500-1999",
            "unit": "KWH", "tax": "X_VAT", "currency": "EUR",
        },
        "periods": ELECTRICITY_PERIODS,
    },
}
EXPECTED_THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "PARTIAL",
    "old_run_2024_wdi_industrial_values_present": True,
    "old_run_2025_wdi_industrial_values_present": False,
    "focal_country": FOCAL,
    "peer_countries": list(PEERS),
    "holdout_years": [2024, 2025],
    "minimum_countries": len(COUNTRIES),
    "minimum_manufacturing_country_years": MIN_MANUFACTURING_KEYS,
    "minimum_electricity_country_semesters": MIN_ELECTRICITY_KEYS,
    "manufacturing_gap_support_max_exclusive": 0.0,
    "electricity_gap_support_min_exclusive": 0.0,
    "quality_flag_status": "unavailable_in_pinned_parquet",
    "source_files": {
        role: {key: source[key] for key in ("path", "sha256", "selector")}
        for role, source in SOURCES.items()
    },
}
LIMITATIONS = [
    "Pre-analysis registered retrospective validation: July 2026 source vintages predate the registration.",
    "2024 WDI industrial GVA was present in the old fit; only 2025 is a new calendar endpoint.",
    "Manufacturing GVA and the selected non-household price band are different measures from the old WDI industrial GVA.",
    "The local Eurostat parquet files omit observation-status flags; this limits a valid result to descriptive calibration.",
    "Nominal EUR/kWh X_VAT excludes VAT and recoverable taxes or levies, not all taxes.",
    "No nuclear-closure, regulatory, fiscal-channel, or other causal effect follows from these two changes.",
    "This test has no school-score credit or automatic policy evidence link.",
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
        spec.get("sample", {}).get("period") != [2024, 2025],
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
        spec.get("covers_claims") != [],
    )):
        raise ValueError("Germany registration differs from the frozen runner contract")
    if [row.get("source") for row in spec["variables"]["outcome"]] != [
        "eurostat:nama_10_a10", "eurostat:nrg_pc_205",
    ]:
        raise ValueError("Germany outcome source changed")
    return spec


def old_run_boundary() -> dict[str, Any]:
    """Verify the old fit's actual observed years without copying its values."""
    if sha256(ROOT / OLD_DIAGNOSTICS) != OLD_DIAGNOSTICS_SHA256:
        raise ValueError("old Germany diagnostics changed")
    if sha256(ROOT / OLD_MANIFEST) != OLD_MANIFEST_SHA256:
        raise ValueError("old Germany manifest changed")
    old = json.loads((ROOT / OLD_DIAGNOSTICS).read_text(encoding="utf-8"))
    old_manifest = yaml.safe_load((ROOT / OLD_MANIFEST).read_text(encoding="utf-8"))
    if not str(old.get("verdict", "")).lower().startswith("partial"):
        raise ValueError("old Germany verdict changed")
    sources = old_manifest.get("vintages") or {}
    if sources.get("ind_gva", {}).get("series") != "NV.IND.TOTL.KD":
        raise ValueError("old Germany primary industrial source changed")
    if any(row.get("publisher") == "eurostat" for row in sources.values()):
        raise ValueError("old Germany run unexpectedly used a Eurostat source")
    fit = old.get("synthetic_control") or {}
    years = fit.get("post_years") or []
    series = [fit.get(key) or [] for key in ("treated_post", "synth_post", "gap_post")]
    if not all(len(row) == len(years) for row in series):
        raise ValueError("old Germany post-fit arrays do not align")
    presence = {year: [row[i] is not None for row in series] for i, year in enumerate(years)}
    if presence.get(2024) != [True, True, True] or presence.get(2025) != [False, False, False]:
        raise ValueError("old Germany fitted-year boundary changed")
    return {
        "old_id": OLD_ID, "old_diagnostics_sha256": OLD_DIAGNOSTICS_SHA256,
        "old_manifest_sha256": OLD_MANIFEST_SHA256,
        "old_2024_wdi_industrial_values_present": True,
        "old_2025_wdi_industrial_values_present": False,
        "old_source_family": "world_bank_wdi",
        "new_source_family": "eurostat",
        "calendar_disjoint_2024_2025": False,
    }


def verified_sources() -> list[dict[str, Any]]:
    if sha256(ROOT / SOURCE_MANIFEST) != SOURCE_MANIFEST_SHA256:
        raise ValueError("Eurostat fetch manifest changed")
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    records = []
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise ValueError(f"pinned source hash mismatch: {source['path']}")
        rows = [row for row in manifest.get("entries", [])
                if row.get("parquet_path") == source["path"]]
        expected_url = (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
            f"{source['series_id']}?format=JSON"
        )
        if len(rows) != 1 or any((
            rows[0].get("publisher") != source["publisher"],
            rows[0].get("series_id") != source["series_id"],
            rows[0].get("source_url") != expected_url,
            rows[0].get("sha256") != source["sha256"],
        )):
            raise ValueError(f"source provenance mismatch: {source['path']}")
        records.append({
            "role": role, "publisher": source["publisher"],
            "series_id": source["series_id"], "path": source["path"],
            "sha256": source["sha256"], "selector": source["selector"],
            "source_url": expected_url, "manifest": SOURCE_MANIFEST,
            "manifest_sha256": SOURCE_MANIFEST_SHA256,
            "observation_flags": "not_preserved_in_local_parquet",
        })
    return records


def selected_rows(role: str, *, include_value: bool) -> pd.DataFrame:
    """The preflight branch never projects the value column from parquet."""
    source = SOURCES[role]
    cols = ["geo_code", "period", *source["selector"]]
    if include_value:
        cols.append("value")
    frame = pd.read_parquet(ROOT / source["path"], columns=cols)
    frame = frame[
        frame["geo_code"].isin(ISO3_TO_EUROSTAT.values())
        & frame["period"].isin(source["periods"])
    ]
    for col, expected in source["selector"].items():
        frame = frame[frame[col] == expected]
    output_cols = ["geo_code", "period"] + (["value"] if include_value else [])
    frame = frame[output_cols].copy()
    if frame.duplicated(["geo_code", "period"]).any():
        raise ValueError(f"duplicate selected {role} geo-period key")
    return frame


def preflight() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_spec()
    old_boundary = old_run_boundary()
    sources = verified_sources()
    counts: dict[str, int] = {}
    for role, source in SOURCES.items():
        rows = selected_rows(role, include_value=False)
        observed = set(zip(rows["geo_code"], rows["period"]))
        expected = {(geo, period) for geo in ISO3_TO_EUROSTAT.values()
                    for period in source["periods"]}
        if observed != expected or len(rows) != len(expected):
            raise ValueError(f"fixed {role} key coverage is incomplete or ambiguous")
        counts[role] = len(observed)
    gate = {
        "countries": len(COUNTRIES), "holdout_years": [2024, 2025],
        "selected_keys": counts,
        "minimum_manufacturing_keys": MIN_MANUFACTURING_KEYS,
        "minimum_electricity_keys": MIN_ELECTRICITY_KEYS,
        "old_run_boundary": old_boundary,
        "source_quality_flags": "unavailable_in_pinned_parquet",
        "passed": counts == {
            "manufacturing": MIN_MANUFACTURING_KEYS,
            "electricity": MIN_ELECTRICITY_KEYS,
        },
        "heldout_values_accessed": False,
    }
    return gate, sources


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require first-addition spec/steelman/runner and no same-commit result."""
    records = []
    for rel in REGISTRATION_FILES:
        current = (ROOT / rel).read_bytes()
        head = _git("show", f"HEAD:{rel}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit exact registration bytes before value access: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
    if history.returncode or not commits:
        raise RuntimeError("new Germany spec has no first-addition commit")
    first = commits[0]
    first_run_tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if first_run_tree.returncode or first_run_tree.stdout.strip():
        raise RuntimeError("run artifact existed in the registration commit")
    for rel in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{rel}")
        if frozen.returncode or frozen.stdout != (ROOT / rel).read_bytes():
            raise RuntimeError(f"registration file changed after first addition: {rel}")
    return first, records


def selected_values(role: str) -> dict[tuple[str, str], float]:
    rows = selected_rows(role, include_value=True)
    expected_count = MIN_MANUFACTURING_KEYS if role == "manufacturing" else MIN_ELECTRICITY_KEYS
    if len(rows) != expected_count:
        raise ValueError(f"incomplete {role} selected cells")
    values: dict[tuple[str, str], float] = {}
    for geo, period, raw in rows.itertuples(index=False, name=None):
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise ValueError(f"non-numeric {role} selected value") from None
        if not math.isfinite(number) or number <= 0:
            raise ValueError(f"nonfinite or nonpositive {role} selected value")
        values[(str(geo), str(period))] = number
    if len(values) != expected_count:
        raise ValueError(f"ambiguous {role} values")
    return values


def classify(manufacturing_gap: float, electricity_gap: float) -> tuple[str, str]:
    if manufacturing_gap < 0 and electricity_gap > 0:
        return "SUPPORTED", "both registered descriptive co-movement signs appear"
    if manufacturing_gap > 0 and electricity_gap < 0:
        return "REFUTED", "both registered descriptive co-movement signs reverse"
    return "PARTIAL", "registered gaps are mixed or touch a zero boundary"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    """Read selected values only after registration_files and preflight pass."""
    manufacturing = selected_values("manufacturing")
    electricity = selected_values("electricity")
    manufacturing_change: dict[str, float] = {}
    electricity_change: dict[str, float] = {}
    for iso3, geo in ISO3_TO_EUROSTAT.items():
        manufacturing_change[iso3] = math.log(
            manufacturing[(geo, "2025")] / manufacturing[(geo, "2024")]
        )
        price_2024 = statistics.mean(electricity[(geo, p)] for p in ("2024-S1", "2024-S2"))
        price_2025 = statistics.mean(electricity[(geo, p)] for p in ("2025-S1", "2025-S2"))
        electricity_change[iso3] = math.log(price_2025 / price_2024)
    manufacturing_peer = statistics.median(manufacturing_change[c] for c in PEERS)
    electricity_peer = statistics.median(electricity_change[c] for c in PEERS)
    manufacturing_gap = manufacturing_change[FOCAL] - manufacturing_peer
    electricity_gap = electricity_change[FOCAL] - electricity_peer
    label, reason = classify(manufacturing_gap, electricity_gap)
    estimate = {
        "method": "fixed ten-peer median of two 2024-to-2025 log changes, descriptive",
        "n_countries": len(COUNTRIES), "n_manufacturing_cells": MIN_MANUFACTURING_KEYS,
        "n_electricity_cells": MIN_ELECTRICITY_KEYS,
        "manufacturing_log_change_germany": manufacturing_change[FOCAL],
        "manufacturing_log_change_peer_median": manufacturing_peer,
        "manufacturing_growth_gap": manufacturing_gap,
        "electricity_log_change_germany": electricity_change[FOCAL],
        "electricity_log_change_peer_median": electricity_peer,
        "electricity_price_growth_gap": electricity_gap,
    }
    return label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of the Germany descriptive packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


def artifact_records(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], sources: list[dict[str, Any]], label: str,
    reason: str, estimate: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any], list[dict[str, Any]]]:
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "preflight": gate, "estimate": estimate,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "PARTIAL",
        "correction": {"disposition": "descriptive_calibration_only", "school_score_credit": 0},
        "limitations": LIMITATIONS,
        "data_status": {
            "variables_missing": [] if estimate is not None else ["selected_endpoint_invalid"],
            "input_status": "verified" if estimate is not None else "unverified",
            "input_vintages": [row["path"] for row in sources],
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "PARTIAL",
        "registration_files": registration, "vintages": sources,
        "derived_panel": gate,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "energy"},
        "preregistration": {"spec_commit": prereg_commit, "steelman": STEELMAN_REL,
                            "registration_files": registration, "gate": EXPECTED_THRESHOLD},
        "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                         "command": f"python3 {RUN_REL}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"inputs": sources, "holdout_years": [2024, 2025],
                 "old_run_boundary": gate["old_run_boundary"]},
        "results": estimate, "limitations": LIMITATIONS,
        "credit_ceiling": "descriptive calibration only; zero school score",
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Old study: `{OLD_ID}` (PARTIAL; old WDI fit has 2024 values and null 2025).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        "Sample: Germany and ten fixed European peers, 2024 to 2025.\n"
        "Method: joint descriptive gaps in manufacturing-volume and selected non-household electricity-price changes.\n"
    )
    if estimate is not None:
        card += (
            f"\nManufacturing log-growth gap: {estimate['manufacturing_growth_gap']:+.8g}.\n"
            f"Electricity-price log-growth gap: {estimate['electricity_price_growth_gap']:+.8g}.\n"
        )
    card += (
        "\nObservation-status flags are absent from the pinned local parquet. "
        "This is descriptive calibration only, with no nuclear-closure, "
        "regulatory, fiscal-channel, or school-score claim.\n"
    )
    chart = {
        "hypothesis_id": HID, "verdict": label,
        "years": [2024, 2025],
        "manufacturing_growth_gap": estimate["manufacturing_growth_gap"] if estimate else None,
        "electricity_price_growth_gap": estimate["electricity_price_growth_gap"] if estimate else None,
        "registered_zero_boundary": 0.0,
    }
    columns = ("term", "coefficient", "std_error", "p_value", "n_obs", "n_countries")
    rows = [] if estimate is None else [
        {"term": "manufacturing_growth_gap", "coefficient": estimate["manufacturing_growth_gap"],
         "std_error": None, "p_value": None, "n_obs": MIN_MANUFACTURING_KEYS,
         "n_countries": len(COUNTRIES)},
        {"term": "electricity_price_growth_gap", "coefficient": estimate["electricity_price_growth_gap"],
         "std_error": None, "p_value": None, "n_obs": MIN_ELECTRICITY_KEYS,
         "n_countries": len(COUNTRIES)},
    ]
    assert all(tuple(row) == columns for row in rows)
    return diagnostics, manifest, packet, card, chart, rows


def calculate() -> tuple[dict[str, Any], list[dict[str, Any]], str, str, dict[str, Any] | None]:
    gate, sources = preflight()
    try:
        label, reason, estimate = evaluate()
    except (KeyError, ValueError, OverflowError) as error:
        label, reason, estimate = "INCONCLUSIVE", f"selected endpoint invalid: {error}", None
    return gate, sources, label, reason, estimate


def write_run(
    prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], sources: list[dict[str, Any]],
    label: str, reason: str, estimate: dict[str, Any] | None,
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
    pd.DataFrame(rows, columns=[
        "term", "coefficient", "std_error", "p_value", "n_obs", "n_countries",
    ]).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "wrote_files": True, "estimate": estimate}


def run_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # must precede value access
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check")
    gate, sources, label, reason, estimate = calculate()
    return write_run(prereg_commit, registration, gate, sources, label, reason, estimate)


def same_estimate(actual: dict[str, Any] | None, expected: dict[str, Any] | None) -> bool:
    if actual is None or expected is None:
        return actual is None and expected is None
    if actual.keys() != expected.keys():
        return False
    for key, value in expected.items():
        saved = actual[key]
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isclose(float(saved), float(value), rel_tol=1e-12, abs_tol=1e-12):
                return False
        elif saved != value:
            return False
    return True


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()
    saved = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    saved_manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    saved_packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8"))
    saved_card = (RUN_DIR / "result_card.md").read_text(encoding="utf-8")
    saved_chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    saved_wrapper = (RUN_DIR / "replication.py").read_text(encoding="utf-8")
    saved_snapshot = (RUN_DIR / "hypothesis.yaml").read_bytes()
    saved_coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    gate, sources, label, reason, estimate = calculate()
    expected = artifact_records(saved["run_utc"], prereg_commit, registration,
                                gate, sources, label, reason, estimate)
    diagnostics, manifest, packet, card, chart, rows = expected
    if any((
        {k: v for k, v in saved.items() if k != "estimate"} !=
        {k: v for k, v in diagnostics.items() if k != "estimate"},
        not same_estimate(saved.get("estimate"), diagnostics["estimate"]),
        saved_manifest != manifest, saved_packet != packet,
        saved_card != card, saved_chart != chart,
        saved_wrapper != replication_wrapper(),
        saved_snapshot != (ROOT / SPEC_REL).read_bytes(),
        list(saved_coefficients["term"]) != [row["term"] for row in rows],
    )):
        raise AssertionError("saved Germany packet differs from exact pinned replay")
    if rows:
        for actual, expected_row in zip(saved_coefficients.to_dict(orient="records"), rows):
            for key in ("coefficient", "n_obs", "n_countries"):
                if not math.isclose(float(actual[key]), float(expected_row[key]), rel_tol=1e-12, abs_tol=1e-12):
                    raise AssertionError(f"coefficient packet mismatch: {key}")
            for key in ("std_error", "p_value"):
                if not pd.isna(actual[key]):
                    raise AssertionError(f"unexpected inferential metric: {key}")
    return {"hypothesis_id": HID, "verified": True, "verdict": label, "wrote_files": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--preflight", action="store_true", help="hashes and dimension keys only")
    mode.add_argument("--run", action="store_true", help="guarded first result after registration")
    mode.add_argument("--check", action="store_true", help="read-only replay of stored result")
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
