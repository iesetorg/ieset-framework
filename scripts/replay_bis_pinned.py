#!/usr/bin/env python3
"""Read-only replay of archived BIS batch01/batch04 result packets.

The promotion runners are imported only for their panel construction, model,
and predeclared gates.  Their artifact-writing entry points are never called.
Each replay loads the exact files listed in its own run manifest and rejects
missing or changed bytes before fitting the model.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
from pathlib import Path, PurePosixPath

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "engine" / "runs"
RUNNERS = {
    "batch01": "promote_bis_batch01_credit_cycle_2026_05_12.py",
    "batch04": "promote_bis_batch04_wave_2026_05_12.py",
}
REL_TOL = 1e-9
ABS_TOL = 1e-10


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _compare(actual, stored, name: str) -> None:
    """Compare a stored packet field, with tolerance only for finite floats."""
    if isinstance(actual, float) and isinstance(stored, (float, int)):
        if not (math.isfinite(actual) and math.isfinite(stored)) or not math.isclose(
            actual, stored, rel_tol=REL_TOL, abs_tol=ABS_TOL
        ):
            raise ValueError(f"stored {name} differs from pinned replay")
        return
    if isinstance(actual, dict) and isinstance(stored, dict):
        if actual.keys() != stored.keys():
            raise ValueError(f"stored {name} fields differ from pinned replay")
        for key in actual:
            _compare(actual[key], stored[key], f"{name}.{key}")
        return
    if isinstance(actual, list) and isinstance(stored, list):
        if len(actual) != len(stored):
            raise ValueError(f"stored {name} length differs from pinned replay")
        for index, (left, right) in enumerate(zip(actual, stored)):
            _compare(left, right, f"{name}[{index}]")
        return
    if type(actual) is not type(stored) or actual != stored:
        raise ValueError(f"stored {name} differs from pinned replay")


def _runner(batch: str):
    if batch not in RUNNERS:
        raise ValueError(f"unknown BIS batch: {batch}")
    path = ROOT / "scripts" / RUNNERS[batch]
    spec = importlib.util.spec_from_file_location(f"bis_{batch}_frozen", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load BIS runner: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pinned_sources(manifest: dict, module) -> dict[tuple[str, str], Path]:
    vintages = manifest.get("vintages")
    if not isinstance(vintages, dict) or not vintages:
        raise ValueError("missing BIS pinned vintages")
    pins = {}
    for key, row in vintages.items():
        if not isinstance(row, dict) or set(row) != {"publisher", "series", "vintage_file", "sha256"}:
            raise ValueError(f"incomplete pinned vintage: {key}")
        publisher, series = row["publisher"], row["series"]
        if not isinstance(key, str) or series != key or publisher not in {"bis", "world_bank_wdi"}:
            raise ValueError(f"invalid pinned vintage identity: {key}")
        raw = row["vintage_file"]
        if not isinstance(raw, str):
            raise ValueError(f"invalid pinned vintage path: {key}")
        relative = PurePosixPath(raw)
        expected_parent = PurePosixPath("data") / "vintages" / publisher
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or relative.parent != expected_parent
            or not relative.name.startswith(f"{series}@")
            or relative.suffix != ".parquet"
        ):
            raise ValueError(f"invalid pinned vintage path: {key}")
        expected_hash = row["sha256"]
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
            character not in "0123456789abcdef" for character in expected_hash
        ):
            raise ValueError(f"invalid pinned vintage hash: {key}")
        path = ROOT / raw
        path.resolve().relative_to((ROOT / "data" / "vintages" / publisher).resolve())
        if not path.is_file() or sha256(path) != expected_hash:
            raise ValueError(f"pinned vintage mismatch: {key}")
        pins[(publisher, series)] = path
    if len(pins) != len(vintages):
        raise ValueError("duplicate BIS pinned vintage identity")
    return pins


def _build_pinned_panel(module, pins: dict[tuple[str, str], Path], vintages: dict):
    observed = set()
    original_latest = module.latest

    def pinned_latest(root: Path, series: str) -> Path:
        if root == module.BIS:
            publisher = "bis"
        elif root == module.WDI:
            publisher = "world_bank_wdi"
        else:
            raise ValueError(f"unexpected BIS vintage root: {root}")
        key = (publisher, series)
        if key not in pins:
            raise ValueError(f"unregistered BIS vintage: {publisher}:{series}")
        observed.add(key)
        return pins[key]

    module.latest = pinned_latest
    try:
        panel, generated_vintages = module.build_panel()
    finally:
        module.latest = original_latest
    if observed != set(pins):
        raise ValueError("BIS panel source set differs from pinned manifest")
    _compare(generated_vintages, vintages, "manifest.vintages")
    return panel


def _card(hypothesis_id: str, cfg: dict, diag: dict) -> str:
    # The archival result-card format is shared by the two promotion runners.
    return f"""# Result card - {hypothesis_id}

**Verdict:** {diag['verdict_label']} - {diag['verdict_reason']}.

## Plain-English Claim

{cfg['claim']}

## What Was Measured

- Outcome: `{cfg['outcome']}`.
- Treatment: `{cfg['treatment']}`.
- Controls: {', '.join(f'`{c}`' for c in cfg['controls'])}.

## Results

- Usable panel: **{diag['n_observations']:,} observations**, **{diag['n_countries']} countries**.
- Coefficient on treatment: **{diag['coefficient']:.4f}** (SE {diag['standard_error_cluster_country']:.4f}, p={diag['p_value']:.4f}).
- Raw treated-control mean difference: **{diag['raw_treated_minus_control_mean']:.4f}**.
- Treated observations: **{diag['treated_count']:,}**.

## Specification

`{cfg['formula']}`

This is a panel fixed-effects screen with country and calendar-year effects. It tests whether the signal consistently predicts later outcomes; it does not by itself prove a structural causal mechanism.
"""


def replay_one(hypothesis_id: str, batch: str, run_dir: Path | None = None) -> dict:
    """Fit one case on manifest-pinned sources and verify all archived outputs."""
    if not hypothesis_id.startswith("bis_") or Path(hypothesis_id).name != hypothesis_id:
        raise ValueError("invalid BIS hypothesis ID")
    module = _runner(batch)
    if hypothesis_id not in module.CASES:
        raise ValueError(f"unknown {batch} case: {hypothesis_id}")
    cfg = module.CASES[hypothesis_id]
    run_dir = RUNS / hypothesis_id if run_dir is None else Path(run_dir)
    manifest = yaml.safe_load((run_dir / "manifest.yaml").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or set(manifest) != {
        "hypothesis_id", "run_utc", "runner", "formula", "vintages"
    }:
        raise ValueError("invalid BIS pinned manifest")
    expected_runner = f"scripts/{RUNNERS[batch]}"
    for key, expected in {
        "hypothesis_id": hypothesis_id,
        "runner": expected_runner,
        "formula": cfg["formula"],
    }.items():
        if manifest[key] != expected:
            raise ValueError(f"stored manifest.{key} differs from pinned replay")
    pins = _pinned_sources(manifest, module)
    panel = _build_pinned_panel(module, pins, manifest["vintages"])
    data, actual = module.fit_case(hypothesis_id, cfg, panel)

    stored = json.loads((run_dir / "diagnostics.json").read_text(encoding="utf-8"))
    if stored.get("run_utc") != manifest["run_utc"]:
        raise ValueError("stored diagnostics.run_utc differs from pinned manifest")
    actual["run_utc"] = manifest["run_utc"]
    # Older packets preserve the computed verdict_label but never recorded the
    # canonical verdict field. Verify their frozen bytes without inventing it.
    if "verdict" in stored:
        actual["verdict"] = actual["verdict_label"]
    _compare(actual, stored, "diagnostics")

    coefficients = pd.read_parquet(run_dir / "coefficients.parquet")
    expected_coefficient = {
        "hypothesis_id": hypothesis_id,
        "term": cfg["treatment"],
        "estimate": actual["coefficient"],
        "std_error": actual["standard_error_cluster_country"],
        "p_value": actual["p_value"],
        "ci95_low": actual["ci95"][0],
        "ci95_high": actual["ci95"][1],
        "n_observations": actual["n_observations"],
        "n_countries": actual["n_countries"],
    }
    if len(coefficients) != 1 or set(coefficients.columns) != set(expected_coefficient):
        raise ValueError("stored coefficient table shape differs from pinned replay")
    for key, expected in expected_coefficient.items():
        value = coefficients.iloc[0][key]
        if isinstance(expected, float):
            value = float(value)
        elif isinstance(expected, int):
            value = int(value)
        else:
            value = str(value)
        _compare(expected, value, f"coefficients.{key}")

    chart = data.groupby(["year", cfg["treatment"]], as_index=False)[cfg["outcome"]].mean()
    chart = chart.rename(columns={cfg["outcome"]: "mean_outcome"})
    expected_chart = {"series": chart.to_dict("records")}
    stored_chart = json.loads((run_dir / "chart_data.json").read_text(encoding="utf-8"))
    _compare(expected_chart, stored_chart, "chart_data")
    if (run_dir / "result_card.md").read_text(encoding="utf-8") != _card(hypothesis_id, cfg, actual):
        raise ValueError("stored result card differs from pinned replay")
    return {
        "hypothesis_id": hypothesis_id,
        "verdict": actual["verdict_label"],
        "n_observations": actual["n_observations"],
        "n_countries": actual["n_countries"],
        "coefficient": actual["coefficient"],
        "p_value": actual["p_value"],
    }
