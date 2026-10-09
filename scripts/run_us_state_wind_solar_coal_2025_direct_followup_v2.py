#!/usr/bin/env python3
"""Guarded EIA state-generation follow-up with key-only preflight and exact replay.

--preflight verifies source hashes and dimension keys without projecting any
generation values. --run and --check require an unchanged first-addition Git
registration before either can read the candidate generation column.
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
HID = "us_state_wind_solar_coal_2025_direct_followup_v2"
OLD_ID = "owid_wind_solar_coal_displacement_2000_2024"
SPEC_REL = f"hypotheses/energy/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
RUNNER_REL = f"scripts/run_{HID}.py"
RUN_REL = f"engine/runs/{HID}"
RUN_DIR = ROOT / RUN_REL
SOURCE_MANIFEST = "data/manifests/fetch_run_2026-10-09T122012Z.yaml"
SOURCE_MANIFEST_SHA256 = "7631d7e49eaf6cf6d2f9296392f9af1b913a2a8996f83337eb3bba9ac67c8274"
SOURCE_PARQUET = (
    "data/vintages/eia_v2/"
    "electricity_electric-power-operational-data_annual_"
    "fueltypeid-ALL-SUN-WND-NG-COW-NUC_sectorid-99@2026-10-09T122006Z.parquet"
)
SOURCE_PARQUET_SHA256 = "010a1293474b6197950230ff6e61ee2683d9c18c47657042686b7c82f21ce8c7"
SOURCE_SERIES_ID = (
    "electricity_electric-power-operational-data_annual_"
    "fueltypeid-ALL-SUN-WND-NG-COW-NUC_sectorid-99"
)
SOURCE_URL_PREFIX = "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/"
REGISTRATION_FILES = (SPEC_REL, STEELMAN_REL, RUNNER_REL, SOURCE_MANIFEST)
OLD_DIAGNOSTICS = f"engine/runs/{OLD_ID}/diagnostics.json"
OLD_MANIFEST = f"engine/runs/{OLD_ID}/manifest.yaml"
OLD_DIAGNOSTICS_SHA256 = "b5d5640fbdee467781aa703110b225d372fe6048f82129304b55defd0c4e8d06"
OLD_MANIFEST_SHA256 = "33a605a685d83e8b398c628967260b84db1e44bd1eb5e6114ef7586f721ee31a"
STATES = (
    "AK", "AZ", "CA", "CO", "CT", "DE", "IA", "ID", "IL", "IN", "KS", "MA", "MD",
    "ME", "MI", "MN", "MO", "MS", "MT", "NC", "NE", "NH", "NJ", "NM", "NV", "NY",
    "OH", "OK", "PA", "RI", "SD", "TN", "TX", "UT", "VA", "WA", "WI", "WV", "WY",
)
PERIODS = ("2024", "2025")
FUELS = ("ALL", "SUN", "WND", "NG", "COW")
FUEL_LABELS = {
    "ALL": "all fuels", "SUN": "solar", "WND": "wind",
    "NG": "natural gas", "COW": "all coal products",
}
SECTOR = "99"
REQUIRED_KEYS = len(STATES) * len(PERIODS) * len(FUELS)
MIN_QUALIFIED = 20
EXPECTED_THRESHOLD = {
    "old_hypothesis_id": OLD_ID,
    "old_result_seen": "REFUTED",
    "period": [2024, 2025],
    "states": list(STATES),
    "sectorid": SECTOR,
    "fueltypeids": list(FUELS),
    "coal_fuel_code_label": "all coal products",
    "required_selected_keys": REQUIRED_KEYS,
    "minimum_positive_wind_solar_change_states": MIN_QUALIFIED,
    "coal_decline_pass_change_max_exclusive": 0.0,
    "support_pass_fraction_min_inclusive": 0.60,
    "refute_pass_fraction_max_exclusive": 0.40,
    "source_manifest": {"path": SOURCE_MANIFEST, "sha256": SOURCE_MANIFEST_SHA256},
    "source_parquet": {"path": SOURCE_PARQUET, "sha256": SOURCE_PARQUET_SHA256},
}
LIMITATIONS = [
    "The known old OWID country-share verdict remains REFUTED; this new ID cannot repair it.",
    "The 2025 endpoint is new in calendar time, but the 2024 baseline overlaps the old window.",
    "This October 2026 EIA vintage predates the pre-analysis registration and may be revised.",
    "State generation signs do not identify causal displacement or any policy effect.",
    "Demand, gas, imports, other fuels, weather, storage, and interconnection can explain the signs.",
    "This descriptive test has no school-score credit or automatic policy evidence link.",
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
        spec.get("sample", {}).get("countries") != ["USA"],
        spec.get("sample", {}).get("period") != [2024, 2025],
        spec.get("estimator", {}).get("template") != "descriptive",
        spec.get("steelman") != STEELMAN_REL,
        spec.get("falsification", {}).get("threshold") != EXPECTED_THRESHOLD,
        spec.get("covers_claims") != [],
        spec.get("linked_hypotheses") != [],
    )):
        raise ValueError("EIA registration differs from the frozen runner contract")
    expected_sources = ["eia_v2:electric-power-operational-data"]
    if [row.get("source") for row in spec["variables"]["outcome"]] != expected_sources:
        raise ValueError("EIA outcome source changed")
    return spec


def old_run_boundary() -> dict[str, Any]:
    """Verify old outcome and source identity without using its fitted values."""
    if sha256(ROOT / OLD_DIAGNOSTICS) != OLD_DIAGNOSTICS_SHA256:
        raise ValueError("old OWID diagnostics changed")
    if sha256(ROOT / OLD_MANIFEST) != OLD_MANIFEST_SHA256:
        raise ValueError("old OWID manifest changed")
    old = json.loads((ROOT / OLD_DIAGNOSTICS).read_text(encoding="utf-8"))
    manifest = yaml.safe_load((ROOT / OLD_MANIFEST).read_text(encoding="utf-8"))
    if old.get("hypothesis_id") != OLD_ID or old.get("verdict") != "refuted":
        raise ValueError("old OWID outcome changed")
    old_source = (manifest.get("vintages") or {}).get("share-elec-by-source")
    if not old_source or not old_source.startswith("data/vintages/owid/"):
        raise ValueError("old OWID source family changed")
    return {
        "old_hypothesis_id": OLD_ID,
        "old_verdict": "REFUTED",
        "old_diagnostics_sha256": OLD_DIAGNOSTICS_SHA256,
        "old_manifest_sha256": OLD_MANIFEST_SHA256,
        "old_source_family": "owid country electricity shares",
        "new_source_family": "eia_v2 state electricity generation",
        "calendar_disjoint_2024_2025": False,
    }


def verified_source() -> dict[str, Any]:
    if sha256(ROOT / SOURCE_MANIFEST) != SOURCE_MANIFEST_SHA256:
        raise ValueError("EIA fetch manifest hash changed")
    if sha256(ROOT / SOURCE_PARQUET) != SOURCE_PARQUET_SHA256:
        raise ValueError("EIA parquet hash changed")
    manifest = yaml.safe_load((ROOT / SOURCE_MANIFEST).read_text(encoding="utf-8"))
    entries = manifest.get("entries") or []
    if len(entries) != 1:
        raise ValueError("EIA fetch manifest is not the pinned single-entry manifest")
    entry = entries[0]
    if any((
        entry.get("publisher") != "eia_v2",
        entry.get("series_id") != SOURCE_SERIES_ID,
        entry.get("parquet_path") != SOURCE_PARQUET,
        entry.get("sha256") != SOURCE_PARQUET_SHA256,
        not str(entry.get("source_url", "")).startswith(SOURCE_URL_PREFIX),
        entry.get("frequency") != "annual",
        entry.get("units") != "thousand megawatthours",
        entry.get("end_date") != "2025",
    )):
        raise ValueError("EIA source provenance changed")
    return {
        "publisher": "eia_v2",
        "series_id": SOURCE_SERIES_ID,
        "source_url": entry["source_url"],
        "methodology_url": entry.get("methodology_url"),
        "manifest": SOURCE_MANIFEST,
        "manifest_sha256": SOURCE_MANIFEST_SHA256,
        "path": SOURCE_PARQUET,
        "sha256": SOURCE_PARQUET_SHA256,
        "selector": {"sectorid": SECTOR, "fueltypeids": list(FUELS), "periods": list(PERIODS)},
        "units": "thousand megawatthours",
        "revision_status": "fixed_local_vintage; subsequent EIA revisions not followed",
    }


def selected_rows(*, include_value: bool, include_labels: bool = False) -> pd.DataFrame:
    """Preflight never projects the generation value column from parquet."""
    columns = ["period", "location", "sectorid", "fueltypeid"]
    label_cols = ["sectorDescription", "fuelTypeDescription", "generation-units"] if include_labels else []
    columns += label_cols
    if include_value:
        columns.append("generation")
    frame = pd.read_parquet(ROOT / SOURCE_PARQUET, columns=columns)
    frame = frame[
        frame["period"].isin(PERIODS)
        & frame["location"].isin(STATES)
        & (frame["sectorid"] == SECTOR)
        & frame["fueltypeid"].isin(FUELS)
    ].copy()
    key_cols = ["location", "period", "fueltypeid"]
    if frame.duplicated(key_cols).any():
        raise ValueError("duplicate EIA state-year-fuel selected key")
    return frame[key_cols + label_cols + (["generation"] if include_value else [])]


def preflight() -> tuple[dict[str, Any], dict[str, Any]]:
    validate_spec()
    old = old_run_boundary()
    source = verified_source()
    rows = selected_rows(include_value=False, include_labels=True)
    observed = set(rows[["location", "period", "fueltypeid"]].itertuples(index=False, name=None))
    expected = {(state, period, fuel)
                for state in STATES for period in PERIODS for fuel in FUELS}
    if observed != expected or len(rows) != REQUIRED_KEYS:
        raise ValueError("fixed 39-state EIA key coverage is incomplete or ambiguous")
    if any((
        not (rows["sectorDescription"] == "All Sectors").all(),
        not (rows["fuelTypeDescription"] == rows["fueltypeid"].map(FUEL_LABELS)).all(),
        not (rows["generation-units"] == "thousand megawatthours").all(),
    )):
        raise ValueError("EIA fuel labels, sector label, or annual generation units changed")
    gate = {
        "states": len(STATES),
        "periods": list(PERIODS),
        "fueltypeids": list(FUELS),
        "selected_keys": len(observed),
        "coal_fuel_code_label": FUEL_LABELS["COW"],
        "selected_units": "thousand megawatthours",
        "minimum_positive_wind_solar_change_states": MIN_QUALIFIED,
        "old_run_boundary": old,
        "passed": True,
        "heldout_values_accessed": False,
    }
    return gate, source


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def registration_files() -> tuple[str, list[dict[str, str]]]:
    """Require same first-addition bytes for every registration file, and no result."""
    records: list[dict[str, str]] = []
    for rel in REGISTRATION_FILES:
        current = (ROOT / rel).read_bytes()
        head = _git("show", f"HEAD:{rel}")
        if head.returncode or head.stdout != current:
            raise RuntimeError(f"commit exact registration bytes before value access: {rel}")
        records.append({"path": rel, "sha256": hashlib.sha256(current).hexdigest()})
    history = _git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", SPEC_REL)
    commits = history.stdout.decode("ascii", errors="replace").strip().splitlines()
    if history.returncode or len(commits) != 1:
        raise RuntimeError("EIA spec requires one identifiable first-addition commit")
    first = commits[0]
    first_run_tree = _git("ls-tree", "-r", "--name-only", first, "--", RUN_REL)
    if first_run_tree.returncode or first_run_tree.stdout.strip():
        raise RuntimeError("run artifact existed in the registration commit")
    for rel in REGISTRATION_FILES:
        frozen = _git("show", f"{first}:{rel}")
        if frozen.returncode or frozen.stdout != (ROOT / rel).read_bytes():
            raise RuntimeError(f"registration file changed after first addition: {rel}")
    return first, records


def selected_values() -> dict[tuple[str, str, str], float]:
    rows = selected_rows(include_value=True)
    if len(rows) != REQUIRED_KEYS:
        raise ValueError("incomplete selected EIA generation cells")
    values: dict[tuple[str, str, str], float] = {}
    for state, period, fuel, raw in rows.itertuples(index=False, name=None):
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise ValueError("nonnumeric selected EIA generation cell") from None
        if not math.isfinite(number) or (number <= 0 if fuel == "ALL" else number < 0):
            raise ValueError("invalid selected EIA generation cell")
        values[(state, period, fuel)] = number
    if len(values) != REQUIRED_KEYS:
        raise ValueError("ambiguous selected EIA generation cells")
    return values


def classify(n_qualified: int, n_coal_declines: int) -> tuple[str, str]:
    if n_qualified < MIN_QUALIFIED:
        return "INCONCLUSIVE", "fewer than 20 fixed states had a positive wind-plus-solar change"
    if n_coal_declines * 5 >= n_qualified * 3:
        return "SUPPORTED", "at least 60% of qualified states had a coal-generation decline"
    if n_coal_declines * 5 < n_qualified * 2:
        return "REFUTED", "fewer than 40% of qualified states had a coal-generation decline"
    return "PARTIAL", "the coal-decline fraction was between 40% and 60%"


def evaluate() -> tuple[str, str, dict[str, Any]]:
    """Read candidate magnitudes only after the registration and key gates pass."""
    values = selected_values()
    state_rows: list[dict[str, Any]] = []
    for state in STATES:
        get = lambda period, fuel: values[(state, period, fuel)]
        wind_solar_change = (
            get("2025", "WND") + get("2025", "SUN")
            - get("2024", "WND") - get("2024", "SUN")
        )
        coal_change = get("2025", "COW") - get("2024", "COW")
        qualified = wind_solar_change > 0
        state_rows.append({
            "state": state,
            "wind_solar_change_thousand_mwh": wind_solar_change,
            "coal_change_thousand_mwh": coal_change,
            "qualified": qualified,
            "coal_decline_pass": qualified and coal_change < 0,
            "natural_gas_change_thousand_mwh": get("2025", "NG") - get("2024", "NG"),
            "all_fuels_change_thousand_mwh": get("2025", "ALL") - get("2024", "ALL"),
        })
    n_qualified = sum(row["qualified"] for row in state_rows)
    n_coal_declines = sum(row["coal_decline_pass"] for row in state_rows)
    label, reason = classify(n_qualified, n_coal_declines)
    estimate = {
        "method": "fixed-state endpoint MWh sign comparison; no causal displacement estimate",
        "n_fixed_states": len(STATES),
        "n_selected_cells": REQUIRED_KEYS,
        "n_positive_wind_solar_states": n_qualified,
        "n_coal_decline_states_among_qualified": n_coal_declines,
        "coal_decline_fraction": n_coal_declines / n_qualified if n_qualified else None,
        "state_rows": state_rows,
    }
    return label, reason, estimate


def calculate() -> tuple[dict[str, Any], dict[str, Any], str, str, dict[str, Any] | None]:
    gate, source = preflight()
    try:
        label, reason, estimate = evaluate()
    except (KeyError, ValueError, OverflowError) as error:
        label, reason, estimate = "INCONCLUSIVE", f"selected EIA generation invalid: {error}", None
    return gate, source, label, reason, estimate


def replication_wrapper() -> str:
    return (
        "#!/usr/bin/env python3\n"
        '"""Read-only exact replay of the EIA state-generation packet."""\n'
        "from pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--check'], cwd=root))\n"
    )


COEFFICIENT_COLUMNS = ["term", "coefficient", "std_error", "p_value", "n_obs", "n_states"]


def artifact_records(
    stamp: str, prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], source: dict[str, Any], label: str,
    reason: str, estimate: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, dict[str, Any], list[dict[str, Any]]]:
    diagnostics = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "template": "descriptive",
        "preflight": gate, "estimate": estimate,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "REFUTED",
        "correction": {"disposition": "new_descriptive_followup_only", "school_score_credit": 0},
        "limitations": LIMITATIONS,
        "data_status": {
            "variables_missing": [] if estimate is not None else ["selected_generation_invalid"],
            "input_status": "verified" if estimate is not None else "unverified",
            "input_vintages": [SOURCE_PARQUET],
        },
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": prereg_commit, "status": label,
        "old_hypothesis_id": OLD_ID, "old_result_seen": "REFUTED",
        "registration_files": registration, "vintages": [source],
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
        "data": {"inputs": [source], "holdout_years": [2024, 2025],
                 "old_run_boundary": gate["old_run_boundary"]},
        "results": estimate, "limitations": LIMITATIONS,
        "credit_ceiling": "descriptive follow-up only; zero school score",
    }
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Old OWID study: `{OLD_ID}` (REFUTED; result unchanged).\n"
        f"Preregistration commit: `{prereg_commit}`.\n"
        "Sample: 39 fixed US states, 2024 to 2025, EIA all-sector generation.\n"
        "Method: coal-generation decline fraction among states whose wind-plus-solar generation increased.\n"
    )
    if estimate is not None:
        card += (
            f"\nQualifying states: {estimate['n_positive_wind_solar_states']} / 39.\n"
            f"Coal declines among qualifying states: {estimate['n_coal_decline_states_among_qualified']}.\n"
            f"Coal-decline fraction: {estimate['coal_decline_fraction']!s}.\n"
        )
    card += (
        "\nThis state MWh sign check cannot establish displacement, a policy effect, "
        "or the old country-share claim. It earns no school-score credit.\n"
    )
    chart = {
        "hypothesis_id": HID, "verdict": label, "years": [2024, 2025],
        "n_fixed_states": len(STATES),
        "n_positive_wind_solar_states": estimate["n_positive_wind_solar_states"] if estimate else None,
        "n_coal_decline_states_among_qualified": estimate["n_coal_decline_states_among_qualified"] if estimate else None,
        "coal_decline_fraction": estimate["coal_decline_fraction"] if estimate else None,
        "minimum_positive_wind_solar_states": MIN_QUALIFIED,
        "support_fraction": 0.60, "refute_fraction_exclusive": 0.40,
        "state_rows": estimate["state_rows"] if estimate else [],
    }
    rows = [] if estimate is None or estimate["coal_decline_fraction"] is None else [{
        "term": "coal_decline_fraction_among_qualified",
        "coefficient": estimate["coal_decline_fraction"],
        "std_error": None, "p_value": None,
        "n_obs": estimate["n_positive_wind_solar_states"],
        "n_states": len(STATES),
    }]
    return diagnostics, manifest, packet, card, chart, rows


def write_run(
    prereg_commit: str, registration: list[dict[str, str]],
    gate: dict[str, Any], source: dict[str, Any], label: str,
    reason: str, estimate: dict[str, Any] | None,
) -> dict[str, Any]:
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        stamp, prereg_commit, registration, gate, source, label, reason, estimate
    )
    RUN_DIR.mkdir(parents=True, exist_ok=False)
    (RUN_DIR / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (RUN_DIR / "manifest.yaml").write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
    (RUN_DIR / "evidence_packet.yaml").write_text(yaml.safe_dump(packet, sort_keys=False), encoding="utf-8")
    (RUN_DIR / "result_card.md").write_text(card, encoding="utf-8")
    (RUN_DIR / "replication.py").write_text(replication_wrapper(), encoding="utf-8")
    (RUN_DIR / "chart_data.json").write_text(json.dumps(chart, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS).to_parquet(RUN_DIR / "coefficients.parquet", index=False)
    return {"hypothesis_id": HID, "verdict": label, "run_dir": RUN_REL,
            "wrote_files": True, "estimate": estimate}


def run_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before value access
    if RUN_DIR.exists():
        raise FileExistsError(f"run already exists: {RUN_REL}; use --check")
    gate, source, label, reason, estimate = calculate()
    return write_run(prereg_commit, registration, gate, source, label, reason, estimate)


def check_one() -> dict[str, Any]:
    prereg_commit, registration = registration_files()  # before value access
    saved = json.loads((RUN_DIR / "diagnostics.json").read_text(encoding="utf-8"))
    saved_manifest = yaml.safe_load((RUN_DIR / "manifest.yaml").read_text(encoding="utf-8"))
    saved_packet = yaml.safe_load((RUN_DIR / "evidence_packet.yaml").read_text(encoding="utf-8"))
    saved_card = (RUN_DIR / "result_card.md").read_text(encoding="utf-8")
    saved_chart = json.loads((RUN_DIR / "chart_data.json").read_text(encoding="utf-8"))
    saved_wrapper = (RUN_DIR / "replication.py").read_text(encoding="utf-8")
    saved_snapshot = (RUN_DIR / "hypothesis.yaml").read_bytes()
    saved_coefficients = pd.read_parquet(RUN_DIR / "coefficients.parquet")
    gate, source, label, reason, estimate = calculate()
    diagnostics, manifest, packet, card, chart, rows = artifact_records(
        saved["run_utc"], prereg_commit, registration, gate, source, label, reason, estimate
    )
    if any((
        saved != diagnostics,
        saved_manifest != manifest,
        saved_packet != packet,
        saved_card != card,
        saved_chart != chart,
        saved_wrapper != replication_wrapper(),
        saved_snapshot != (ROOT / SPEC_REL).read_bytes(),
    )):
        raise AssertionError("saved EIA packet differs from exact pinned replay")
    expected_coefficients = pd.DataFrame(rows, columns=COEFFICIENT_COLUMNS)
    pd.testing.assert_frame_equal(saved_coefficients, expected_coefficients, check_dtype=False)
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
