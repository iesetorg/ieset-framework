#!/usr/bin/env python3
"""Build the U.S. state-year minimum-wage TREATMENT panel.

Combines the USDOL state minimum-wage history vintage (statutory state rate vs
federal rate) with the derived subnational minimum-wage bite-ratio panel, and
codes minimum-wage treatment events (first year a state's statutory rate rises
above the federal floor, plus per-year year-over-year increases).

Grain: one row per (ieset_state_id, year).

Federal and state are kept strictly separated; treatment intensity is NOT routed
through any country-year runner. The USDOL vintage `value` column is already the
*effective* minimum (max of state statutory and federal); the genuine *statutory*
state rate is `state_rate_high` (NaN when a state has no own statutory law, i.e.
parse_note in {no_state_rate, non_hourly_cell, missing}).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]

MW_HISTORY_GLOB = "data/vintages/usdol/state_minimum_wage_history@*.parquet"
BITE_GLOB = "data/vintages/derived/minimum_wage_bite_ratio_subnational_panel@*.parquet"
SPINE_PATH = "data/derived/state_universe_admin1.parquet"

# parse_note values in the USDOL vintage that indicate there is NO genuine state
# statutory rate (the `value`/`state_rate_*` cells were federal fallbacks).
NO_STATUTORY_NOTES = {"no_state_rate", "non_hourly_cell", "missing"}

SOURCE_URL = "https://www.dol.gov/agencies/whd/state/minimum-wage/history"
METHODOLOGY_URL = "https://www.dol.gov/agencies/whd/minimum-wage/history"
LICENSE = "U.S. Department of Labor public domain (federal government work)"


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location(
        "ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py"
    )
    if spec is None or spec.loader is None:
        raise ImportError("Could not load data/fetchers/_base.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_FETCHER_BASE = load_fetcher_base()
FetchResult = _FETCHER_BASE.FetchResult
utc_now = _FETCHER_BASE.utc_now
utc_stamp = _FETCHER_BASE.utc_stamp


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_fetch_utc(value: str | None) -> datetime:
    if not value:
        return utc_now()
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def path_arg(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def newest_glob(pattern: str) -> Path:
    """Return the newest @timestamp vintage matching the glob (lexicographic max)."""
    matches = sorted(glob.glob(str(ROOT / pattern)))
    if not matches:
        raise FileNotFoundError(f"no input vintage matched: {pattern}")
    return Path(matches[-1])


def normalise_fips(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.zfill(2)


def build_panel(
    *,
    mw_history_path: Path,
    bite_path: Path,
    spine_path: Path,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    mw = pd.read_parquet(mw_history_path)
    bite = pd.read_parquet(bite_path)
    spine = pd.read_parquet(spine_path)

    mw = mw.copy()
    mw["state_fips"] = normalise_fips(mw["state_fips"])
    bite = bite.copy()
    bite["state_fips"] = normalise_fips(bite["state_fips"])
    spine = spine.copy()
    spine["state_fips"] = normalise_fips(spine["state_fips"])

    # --- Federal floor: one canonical value per year (defensive de-dup). ---
    federal = (
        mw[["year", "federal_rate"]]
        .dropna(subset=["federal_rate"])
        .drop_duplicates(subset=["year"])
        .rename(columns={"federal_rate": "federal_minimum_wage"})
    )

    # --- Statutory state rate: genuine own-law rate, else NaN. ---
    has_statute = ~mw["parse_note"].fillna("").isin(NO_STATUTORY_NOTES)
    mw["state_statutory_minimum_wage"] = mw["state_rate_high"].where(has_statute)
    # `value` is the published effective rate (already max(statutory, federal)).
    mw["effective_minimum_wage_published"] = mw["value"]

    base = mw[
        [
            "state_fips",
            "state_abbr",
            "state_name",
            "year",
            "state_statutory_minimum_wage",
            "effective_minimum_wage_published",
            "federal_rate",
            "state_rate_low",
            "state_rate_high",
            "raw_value",
            "parse_note",
        ]
    ].copy()
    base = base.rename(columns={"federal_rate": "federal_minimum_wage"})

    if base.duplicated(["state_fips", "year"]).any():
        raise ValueError("duplicate (state_fips, year) in USDOL minimum-wage history")

    # --- Attach canonical ieset_state_id from the state spine. ---
    spine_cols = spine[["state_fips", "state_abbr", "ieset_state_id", "unit_id"]] if "unit_id" in spine.columns else spine[["state_fips", "state_abbr", "ieset_state_id"]]
    panel = base.merge(
        spine_cols.drop(columns=["state_abbr"]),
        on="state_fips",
        how="left",
        validate="many_to_one",
    )
    unmatched = panel[panel["ieset_state_id"].isna()]["state_abbr"].drop_duplicates().tolist()
    if unmatched:
        raise ValueError(f"state_fips without ieset_state_id in spine: {unmatched}")
    # ieset_state_id (e.g. US-AL) doubles as the unit_id for this panel.
    if "unit_id" not in panel.columns:
        panel["unit_id"] = panel["ieset_state_id"]

    # --- Effective minimum = max(statutory, federal). Recompute defensively. ---
    panel["effective_minimum_wage"] = panel[
        ["state_statutory_minimum_wage", "federal_minimum_wage"]
    ].max(axis=1)
    # binds_above_federal: state statutory law strictly exceeds the federal floor.
    panel["binds_above_federal"] = (
        panel["state_statutory_minimum_wage"] > panel["federal_minimum_wage"]
    ).fillna(False)

    # --- Bite ratio join (state_fips + year). ---
    bite_join = bite[["state_fips", "year", "bite_ratio", "denominator_wage", "denominator"]].copy()
    bite_join = bite_join.rename(
        columns={
            "denominator_wage": "bite_denominator_wage",
            "denominator": "bite_denominator",
        }
    )
    if bite_join.duplicated(["state_fips", "year"]).any():
        raise ValueError("duplicate (state_fips, year) in bite-ratio panel")
    panel = panel.merge(bite_join, on=["state_fips", "year"], how="left", validate="many_to_one")

    # --- TREATMENT EVENT CODING (sorted within state, across observed years). ---
    panel = panel.sort_values(["ieset_state_id", "year"]).reset_index(drop=True)
    grp = panel.groupby("ieset_state_id", sort=False)

    # Year-over-year change in the effective minimum (treatment intensity per year).
    panel["minimum_wage_increase"] = grp["effective_minimum_wage"].diff()
    # Year-over-year change in the statutory state rate (NaN until a statute exists).
    panel["statutory_minimum_wage_increase"] = grp["state_statutory_minimum_wage"].diff()

    # First observed year a state's statutory rate binds above federal.
    first_bind_year = (
        panel.loc[panel["binds_above_federal"]]
        .groupby("ieset_state_id")["year"]
        .min()
    )
    panel["first_year_binds_above_federal"] = panel["ieset_state_id"].map(first_bind_year)
    panel["is_first_bind_event"] = (
        panel["year"] == panel["first_year_binds_above_federal"]
    ) & panel["binds_above_federal"]

    # event_type per (state, year):
    #   first_bind   -> first observed year statutory rises above federal
    #   increase     -> effective minimum rose vs prior observed year (not first bind)
    #   decrease     -> effective minimum fell vs prior observed year
    #   no_change    -> effective minimum unchanged vs prior observed year
    #   baseline     -> first observed year for the state (no prior to diff)
    def classify(row: pd.Series) -> str:
        if bool(row["is_first_bind_event"]):
            return "first_bind"
        delta = row["minimum_wage_increase"]
        if pd.isna(delta):
            return "baseline"
        if delta > 0:
            return "increase"
        if delta < 0:
            return "decrease"
        return "no_change"

    panel["event_type"] = panel.apply(classify, axis=1)

    # Real-vs-nominal note: USDOL statutory levels are nominal current dollars.
    panel["nominal_real_note"] = "nominal_current_usd_statutory_levels"

    ordered = [
        "ieset_state_id",
        "unit_id",
        "state_fips",
        "state_abbr",
        "state_name",
        "year",
        "effective_minimum_wage",
        "state_statutory_minimum_wage",
        "federal_minimum_wage",
        "binds_above_federal",
        "bite_ratio",
        "bite_denominator_wage",
        "bite_denominator",
        "minimum_wage_increase",
        "statutory_minimum_wage_increase",
        "event_type",
        "is_first_bind_event",
        "first_year_binds_above_federal",
        "effective_minimum_wage_published",
        "state_rate_low",
        "state_rate_high",
        "raw_value",
        "parse_note",
        "nominal_real_note",
    ]
    panel = panel[ordered].sort_values(["ieset_state_id", "year"]).reset_index(drop=True)

    # Integrity guards (mirror the test acceptance discipline).
    if panel.duplicated(["ieset_state_id", "year"]).any():
        raise ValueError("non-unique (ieset_state_id, year) grain")
    if (panel["effective_minimum_wage"] < panel["federal_minimum_wage"]).any():
        raise ValueError("effective_minimum_wage below federal floor detected")

    matched_bite = panel["bite_ratio"].notna()
    stats = {
        "panel_rows": int(len(panel)),
        "start_year": int(panel["year"].min()),
        "end_year": int(panel["year"].max()),
        "state_count": int(panel["ieset_state_id"].nunique()),
        "year_count": int(panel["year"].nunique()),
        "rows_with_statutory_rate": int(panel["state_statutory_minimum_wage"].notna().sum()),
        "rows_binding_above_federal": int(panel["binds_above_federal"].sum()),
        "states_ever_binding_above_federal": int(first_bind_year.size),
        "first_bind_events": int(panel["is_first_bind_event"].sum()),
        "rows_with_bite_ratio": int(matched_bite.sum()),
        "bite_year_min": int(bite["year"].min()),
        "bite_year_max": int(bite["year"].max()),
        "source_mw_history": rel(mw_history_path),
        "source_mw_history_sha256": sha256_path(mw_history_path),
        "source_bite_panel": rel(bite_path),
        "source_bite_panel_sha256": sha256_path(bite_path),
        "source_state_spine": rel(spine_path),
        "source_state_spine_sha256": sha256_path(spine_path),
        "event_type_counts": {k: int(v) for k, v in panel["event_type"].value_counts().items()},
    }
    return panel, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_us_state_minimum_wage_treatment.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "us_state_minimum_wage_treatment_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame, stats: dict[str, Any], output_path: Path, fetch_ts: datetime
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="usdol_wage_and_hour_division",
        series_id="us_state_minimum_wage_treatment_panel",
        source_url=SOURCE_URL,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="annual",
        units="USD per hour (nominal) and treatment event flags",
        currency="USD",
        start_date=str(stats["start_year"]),
        end_date=str(stats["end_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {"parquet_path": rel(output_path), "parquet_sha256": parquet_sha},
            "stats": stats,
            "columns": list(panel.columns),
            "inputs": {
                "minimum_wage_history": {
                    "path": stats["source_mw_history"],
                    "sha256": stats["source_mw_history_sha256"],
                },
                "bite_ratio_panel": {
                    "path": stats["source_bite_panel"],
                    "sha256": stats["source_bite_panel_sha256"],
                },
                "state_spine": {
                    "path": stats["source_state_spine"],
                    "sha256": stats["source_state_spine_sha256"],
                },
            },
            "construction": (
                "USDOL state minimum-wage history joined to the canonical state spine for "
                "ieset_state_id, then to the derived subnational minimum-wage bite-ratio panel "
                "on state_fips+year. state_statutory_minimum_wage is the genuine own-law rate "
                "(state_rate_high; NaN when parse_note in {no_state_rate, non_hourly_cell, "
                "missing}); effective_minimum_wage is max(statutory, federal); binds_above_federal "
                "is statutory>federal. Treatment events code the first observed year a state binds "
                "above federal (first_bind) plus year-over-year increases. Federal and state floors "
                "are kept separate; intensity is not routed through any country-year runner. Levels "
                "are nominal current USD."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mw-history", default=None, help="Override USDOL min-wage history vintage path.")
    parser.add_argument("--bite-panel", default=None, help="Override bite-ratio panel vintage path.")
    parser.add_argument("--spine", default=SPINE_PATH)
    parser.add_argument("--output", default="data/derived/us_state_minimum_wage_treatment_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)

    mw_history_path = path_arg(args.mw_history).resolve() if args.mw_history else newest_glob(MW_HISTORY_GLOB)
    bite_path = path_arg(args.bite_panel).resolve() if args.bite_panel else newest_glob(BITE_GLOB)
    spine_path = path_arg(args.spine).resolve()

    panel, stats = build_panel(
        mw_history_path=mw_history_path,
        bite_path=bite_path,
        spine_path=spine_path,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, stats, output_path, fetch_ts)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK usdol_wage_and_hour_division:us_state_minimum_wage_treatment_panel "
        f"rows={result.rows} years={stats['start_year']}->{stats['end_year']} "
        f"states={stats['state_count']} first_bind_events={stats['first_bind_events']} "
        f"bite_rows={stats['rows_with_bite_ratio']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
