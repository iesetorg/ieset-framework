#!/usr/bin/env python3
"""Build country-year vintages from movement YAML labels.

The hypothesis runners can already load arbitrary publisher vintages from
data/vintages/<publisher>/<series>@<stamp>.parquet. This script turns the
curated movement position labels into dense annual panels so sources like
``movements:developmentalism_alignment`` resolve as normal data.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from data.fetchers._base import FetchResult, utc_now, utc_stamp, write_manifest, write_vintage

MOVEMENTS = ROOT / "movements"
POSITIONS = ROOT / "positions"
HYPOTHESES = ROOT / "hypotheses"
VINTAGES = ROOT / "data" / "vintages"

ALIGNMENT_VALUE = {
    "aligned": 1.0,
    "partially_aligned": 0.5,
    "opposed": -1.0,
}

AXIS_DIRECTION_VALUE = {
    "+": 1.0,
    "-": -1.0,
    "0": 0.0,
    "mixed": 0.0,
}

AXIS_MAGNITUDE_VALUE = {
    "weak": 1.0 / 3.0,
    "moderate": 2.0 / 3.0,
    "strong": 1.0,
}

# Legacy labels that appeared in older specs or movement backfills. The output
# keeps canonical IDs primary while also writing alias series for compatibility.
POSITION_ALIASES = {
    "chicago_monetarist": "chicago_monetarism",
    "christian_democratic": "institutionalism",
    "conservative_nationalism": "developmentalism",
    "dependency_theory": "marxian",
    "developmentalist": "developmentalism",
    "ethno_nationalist_developmentalism": "developmentalism",
    "ecological": "eco_socialist",
    "green_interventionism": "eco_socialist",
    "green_political_economy": "eco_socialist",
    "imf_washington_consensus": "chicago_monetarism",
    "keynesian": "new_keynesian",
    "libertarian": "austrian",
    "market_liberal": "classical_liberal",
    "modern_monetary_theory": "mmt",
    "national_conservative": "developmentalism",
    "neoclassical": "empirical_pragmatist",
    "neoconservative": "developmentalism",
    "neoliberal": "classical_liberal",
    "ordo_liberal": "ordoliberal",
    "political_islam": "developmentalism",
    "populist_nationalism": "developmentalism",
    "right_populism": "developmentalism",
    "social_democracy": "social_democratic",
    "social_liberal": "empirical_pragmatist",
    "supply_side": "chicago_monetarism",
    "third_way": "social_democratic",
}

RESOURCE_RENT_SERIES = "NY.GDP.TOTL.RT.ZS"
RESOURCE_RENT_THRESHOLD = 5.0
DEFAULT_START_YEAR = 1800


def read_yaml(path: Path) -> dict:
    with path.open() as f:
        return yaml.safe_load(f) or {}


def load_position_ids() -> list[str]:
    out: list[str] = []
    for path in sorted(POSITIONS.glob("*.yaml")):
        if path.stem.startswith("_"):
            continue
        doc = read_yaml(path)
        position_id = doc.get("position_id")
        if not position_id:
            raise ValueError(f"{path} is missing position_id")
        if position_id != path.stem:
            raise ValueError(f"{path} has position_id={position_id!r}; expected {path.stem!r}")
        out.append(position_id)
    return out


def canonical_position_id(position_id: object, valid_ids: set[str]) -> str | None:
    raw = str(position_id or "").strip()
    if raw in valid_ids:
        return raw
    alias = POSITION_ALIASES.get(raw)
    if alias in valid_ids:
        return alias
    return None


def load_movements(valid_ids: set[str]) -> list[dict]:
    movements: list[dict] = []
    skipped: dict[str, int] = {}
    for path in sorted(MOVEMENTS.glob("*.yaml")):
        doc = read_yaml(path)
        if not doc.get("movement_id"):
            continue
        normalised: list[dict] = []
        for rec in doc.get("position_alignments") or []:
            pos_id = canonical_position_id(rec.get("position_id"), valid_ids)
            if not pos_id:
                skipped[str(rec.get("position_id") or "<missing>")] = (
                    skipped.get(str(rec.get("position_id") or "<missing>"), 0) + 1
                )
                continue
            alignment = rec.get("alignment")
            if alignment not in ALIGNMENT_VALUE:
                continue
            normalised.append({"position_id": pos_id, "alignment": alignment})
        doc["_position_alignments_normalised"] = normalised
        movements.append(doc)
    if skipped:
        detail = ", ".join(f"{k}={v}" for k, v in sorted(skipped.items()))
        raise ValueError(f"unmapped position IDs in movements: {detail}")
    return movements


def load_hypothesis_countries() -> set[str]:
    countries: set[str] = set()
    for path in HYPOTHESES.glob("**/*.yaml"):
        try:
            doc = read_yaml(path)
        except Exception:
            continue
        for raw in ((doc.get("sample") or {}).get("countries") or []):
            if isinstance(raw, str) and len(raw) == 3 and raw.isupper():
                countries.add(raw)
    return countries


def load_vintage_country_years() -> tuple[set[str], int | None, int | None]:
    countries: set[str] = set()
    min_year: int | None = None
    max_year: int | None = None
    patterns = [
        VINTAGES / "pwt" / "pwt_full@*.parquet",
        VINTAGES / "world_bank_wdi" / "NY.GDP.PCAP.KD.ZG@*.parquet",
        VINTAGES / "world_bank_wdi" / "NY.GDP.PCAP.KD@*.parquet",
    ]
    for pattern in patterns:
        paths = sorted(pattern.parent.glob(pattern.name))
        if not paths:
            continue
        df = pd.read_parquet(paths[-1], columns=["country_iso3", "year"])
        iso = df["country_iso3"].astype(str).str.strip()
        valid = iso.str.fullmatch(r"[A-Z]{3}", na=False)
        countries.update(iso[valid].unique().tolist())
        years = pd.to_numeric(df["year"], errors="coerce").dropna().astype(int)
        if not years.empty:
            lo = int(years.min())
            hi = int(years.max())
            min_year = lo if min_year is None else min(min_year, lo)
            max_year = hi if max_year is None else max(max_year, hi)
    return countries, min_year, max_year


def movement_years(movement: dict, end_year: int) -> list[int]:
    timeframe = movement.get("timeframe") or {}
    start = timeframe.get("start")
    if start is None:
        return []
    end = timeframe.get("end", start)
    if end == "ongoing":
        end = end_year
    start_i = int(start)
    end_i = int(end)
    if end_i < start_i:
        return []
    return list(range(start_i, min(end_i, end_year) + 1))


def build_base_grid(
    movements: list[dict],
    *,
    start_year: int,
    end_year: int,
) -> pd.DataFrame:
    countries, vintage_min, vintage_max = load_vintage_country_years()
    countries.update(load_hypothesis_countries())
    for movement in movements:
        countries.update(str(c) for c in movement.get("countries") or [])
    countries = {c for c in countries if len(c) == 3 and c.isupper()}

    grid_start = min(start_year, vintage_min or start_year)
    grid_end = max(end_year, vintage_max or end_year)
    index = pd.MultiIndex.from_product(
        [sorted(countries), range(grid_start, grid_end + 1)],
        names=["country_iso3", "year"],
    )
    return index.to_frame(index=False)


def active_position_rows(
    movements: list[dict],
    *,
    end_year: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for movement in movements:
        years = movement_years(movement, end_year)
        if not years:
            continue
        countries = [str(c) for c in movement.get("countries") or []]
        for rec in movement.get("_position_alignments_normalised") or []:
            value = ALIGNMENT_VALUE[rec["alignment"]]
            for country in countries:
                for year in years:
                    rows.append(
                        {
                            "country_iso3": country,
                            "year": year,
                            "position_id": rec["position_id"],
                            "value": value,
                            "movement_id": movement.get("movement_id"),
                        }
                    )
    if not rows:
        return pd.DataFrame(
            columns=["country_iso3", "year", "position_id", "value", "movement_id"]
        )
    df = pd.DataFrame(rows)
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def active_axis_rows(
    movements: list[dict],
    *,
    end_year: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    for movement in movements:
        years = movement_years(movement, end_year)
        if not years:
            continue
        countries = [str(c) for c in movement.get("countries") or []]
        for rec in movement.get("axes_summary") or []:
            axis = str(rec.get("axis") or "").strip()
            if not axis:
                continue
            direction = AXIS_DIRECTION_VALUE.get(str(rec.get("direction")), 0.0)
            magnitude = AXIS_MAGNITUDE_VALUE.get(str(rec.get("magnitude") or "moderate"), 2.0 / 3.0)
            value = direction * magnitude
            series = f"axis_{axis.replace('.', '_')}"
            for country in countries:
                for year in years:
                    rows.append(
                        {
                            "country_iso3": country,
                            "year": year,
                            "series": series,
                            "value": value,
                        }
                    )
    if not rows:
        return pd.DataFrame(columns=["country_iso3", "year", "series", "value"])
    df = pd.DataFrame(rows)
    df["year"] = df["year"].astype(int)
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df


def dense_series(base: pd.DataFrame, active: pd.DataFrame) -> pd.DataFrame:
    if active.empty:
        out = base.copy()
        out["value"] = 0.0
        return out
    active = (
        active.groupby(["country_iso3", "year"], as_index=False)["value"]
        .sum()
        .assign(value=lambda d: d["value"].clip(-1.0, 1.0))
    )
    out = base.merge(active, on=["country_iso3", "year"], how="left")
    out["value"] = out["value"].fillna(0.0).astype(float)
    return out[["country_iso3", "year", "value"]]


def latest_vintage_path(publisher: str, series: str) -> Path | None:
    paths = sorted((VINTAGES / publisher).glob(f"{series}@*.parquet"))
    return paths[-1] if paths else None


def load_resource_rent_flags(base: pd.DataFrame) -> pd.DataFrame:
    out = base.copy()
    out["_resource_year_flag"] = False
    out["_resource_year_has_value"] = False
    out["_resource_country_flag"] = False

    path = latest_vintage_path("world_bank_wdi", RESOURCE_RENT_SERIES)
    if path is None:
        return out
    rents = pd.read_parquet(path)
    rents = rents[["country_iso3", "year", "value"]].copy()
    rents["country_iso3"] = rents["country_iso3"].astype(str).str.strip()
    rents = rents[rents["country_iso3"].str.fullmatch(r"[A-Z]{3}", na=False)]
    rents["year"] = pd.to_numeric(rents["year"], errors="coerce")
    rents["value"] = pd.to_numeric(rents["value"], errors="coerce")
    rents = rents.dropna(subset=["country_iso3", "year", "value"])
    rents["year"] = rents["year"].astype(int)

    annual = rents[["country_iso3", "year", "value"]].copy()
    annual["_resource_year_flag"] = annual["value"] >= RESOURCE_RENT_THRESHOLD
    annual["_resource_year_has_value"] = True
    annual = annual[["country_iso3", "year", "_resource_year_flag", "_resource_year_has_value"]]
    out = out.merge(annual, on=["country_iso3", "year"], how="left", suffixes=("", "_rents"))
    out["_resource_year_flag"] = (
        out["_resource_year_flag_rents"].astype("boolean").fillna(False).astype(bool)
    )
    out["_resource_year_has_value"] = (
        out["_resource_year_has_value_rents"].astype("boolean").fillna(False).astype(bool)
    )
    out = out.drop(columns=["_resource_year_flag_rents", "_resource_year_has_value_rents"])

    sample = rents[(rents["year"] >= 1970) & (rents["year"] <= 2020)]
    country_flag = (
        sample.groupby("country_iso3")["value"]
        .mean()
        .ge(RESOURCE_RENT_THRESHOLD)
        .rename("_resource_country_flag")
        .reset_index()
    )
    out = out.merge(country_flag, on="country_iso3", how="left", suffixes=("", "_rents"))
    out["_resource_country_flag"] = (
        out["_resource_country_flag_rents"].astype("boolean").fillna(False).astype(bool)
    )
    out = out.drop(columns=["_resource_country_flag_rents"])
    return out


def build_resource_developmentalism(base: pd.DataFrame, developmentalism: pd.DataFrame) -> pd.DataFrame:
    rents = load_resource_rent_flags(base)
    merged = rents.merge(
        developmentalism.rename(columns={"value": "_developmentalism"}),
        on=["country_iso3", "year"],
        how="left",
    )
    resource_flag = merged["_resource_year_flag"] | (
        merged["_resource_country_flag"] & ~merged["_resource_year_has_value"]
    )

    merged["value"] = merged["_developmentalism"].clip(lower=0.0).fillna(0.0)
    merged.loc[~resource_flag, "value"] = 0.0
    return merged[["country_iso3", "year", "value"]]


def write_series(
    *,
    publisher: str,
    series_id: str,
    frame: pd.DataFrame,
    fetch_ts: datetime,
    units: str,
    source_url: str,
    extra: dict,
) -> FetchResult:
    out, digest = write_vintage(
        publisher=publisher,
        series_id=series_id,
        frame=frame.sort_values(["country_iso3", "year"]).reset_index(drop=True),
        fetch_utc=fetch_ts,
    )
    return FetchResult(
        publisher=publisher,
        series_id=series_id,
        source_url=source_url,
        methodology_url="local://scripts/build_movement_vintages.py",
        license="internal_derived_from_curated_yaml",
        fetch_utc=fetch_ts,
        rows=len(frame),
        frequency="annual",
        units=units,
        currency=None,
        start_date=str(int(frame["year"].min())) if not frame.empty else None,
        end_date=str(int(frame["year"].max())) if not frame.empty else None,
        sha256=digest,
        parquet_path=out,
        extra=extra,
    )


def build_pwt_rgdpo_pop(fetch_ts: datetime) -> FetchResult | None:
    path = latest_vintage_path("pwt", "pwt_full")
    if path is None:
        return None
    df = pd.read_parquet(path, columns=["country_iso3", "country", "year", "rgdpo", "pop"])
    df["value"] = pd.to_numeric(df["rgdpo"], errors="coerce") / pd.to_numeric(
        df["pop"], errors="coerce"
    )
    df = df[["country_iso3", "country", "year", "value"]]
    return write_series(
        publisher="pwt",
        series_id="rgdpo_pop",
        frame=df,
        fetch_ts=fetch_ts,
        units="rgdpo divided by pop, PWT 2017 PPP output-side GDP per capita",
        source_url=f"local://{path.relative_to(ROOT)}",
        extra={"parent": "pwt_full", "derived": "rgdpo / pop"},
    )


def build(args: argparse.Namespace) -> list[FetchResult]:
    fetch_ts = (
        datetime.strptime(args.stamp, "%Y-%m-%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if args.stamp
        else utc_now()
    )
    end_year = args.end_year or datetime.now(timezone.utc).year
    start_year = args.start_year or DEFAULT_START_YEAR
    position_ids = load_position_ids()
    valid_ids = set(position_ids)
    movements = load_movements(valid_ids)
    base = build_base_grid(movements, start_year=start_year, end_year=end_year)
    position_rows = active_position_rows(movements, end_year=end_year)
    axis_rows = active_axis_rows(movements, end_year=end_year)

    results: list[FetchResult] = []
    by_canonical: dict[str, pd.DataFrame] = {}
    units = "movement alignment intensity: -1 opposed, 0 uncoded/no active alignment, 0.5 partial, 1 aligned"

    for position_id in position_ids:
        active = position_rows[position_rows["position_id"].eq(position_id)][
            ["country_iso3", "year", "value"]
        ]
        frame = dense_series(base, active)
        by_canonical[position_id] = frame
        for series_id in (
            f"position_alignments_{position_id}",
            f"{position_id}_alignment",
        ):
            results.append(
                write_series(
                    publisher="movements",
                    series_id=series_id,
                    frame=frame,
                    fetch_ts=fetch_ts,
                    units=units,
                    source_url="local://movements/*.yaml",
                    extra={
                        "source_movements": len(movements),
                        "position_id": position_id,
                        "aggregation": "sum active movement values by country-year, clipped to [-1, 1]",
                        "zero_fill": "all local vintage, hypothesis-sample, and movement countries across the generated year grid",
                    },
                )
            )

    for alias, canonical in sorted(POSITION_ALIASES.items()):
        if canonical not in by_canonical:
            continue
        frame = by_canonical[canonical]
        for series_id in (
            f"position_alignments_{alias}",
            f"{alias}_alignment",
        ):
            results.append(
                write_series(
                    publisher="movements",
                    series_id=series_id,
                    frame=frame,
                    fetch_ts=fetch_ts,
                    units=units,
                    source_url="local://movements/*.yaml",
                    extra={
                        "alias_for_position_id": canonical,
                        "legacy_alias": alias,
                        "source_movements": len(movements),
                    },
                )
            )

    developmentalism = by_canonical["developmentalism"]
    resource_dev = build_resource_developmentalism(base, developmentalism)
    for series_id in ("resource_developmentalism", "resource_developmentalism_alignment"):
        results.append(
            write_series(
                publisher="movements",
                series_id=series_id,
                frame=resource_dev,
                fetch_ts=fetch_ts,
                units=(
                    "positive developmentalism alignment in country-years with "
                    f"resource rents >= {RESOURCE_RENT_THRESHOLD:g}% of GDP"
                ),
                source_url="local://movements/*.yaml + world_bank_wdi:NY.GDP.TOTL.RT.ZS",
                extra={
                    "base_position_id": "developmentalism",
                    "resource_rent_series": f"world_bank_wdi:{RESOURCE_RENT_SERIES}",
                    "resource_rent_threshold_pct_gdp": RESOURCE_RENT_THRESHOLD,
                },
            )
        )

    for series in sorted(axis_rows["series"].unique().tolist()) if not axis_rows.empty else []:
        active = axis_rows[axis_rows["series"].eq(series)][["country_iso3", "year", "value"]]
        frame = dense_series(base, active)
        results.append(
            write_series(
                publisher="movements",
                series_id=series,
                frame=frame,
                fetch_ts=fetch_ts,
                units="axis direction intensity: -1 negative, 0 neutral/mixed/uncoded, +1 positive",
                source_url="local://movements/*.yaml",
                extra={
                    "source_movements": len(movements),
                    "axis_series": True,
                    "aggregation": "sum active movement axis values by country-year, clipped to [-1, 1]",
                },
            )
        )

    if args.build_pwt_helper:
        pwt_result = build_pwt_rgdpo_pop(fetch_ts)
        if pwt_result is not None:
            results.append(pwt_result)

    manifest = write_manifest(results, run_stamp=f"movement_vintages_{utc_stamp(fetch_ts)}")
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    print(
        yaml.safe_dump(
            {
                "generated_at": fetch_ts.isoformat(),
                "manifest": str(manifest.relative_to(ROOT)),
                "manifest_sha256": digest,
                "movement_count": len(movements),
                "country_count": int(base["country_iso3"].nunique()),
                "year_min": int(base["year"].min()),
                "year_max": int(base["year"].max()),
                "series_written": len(results),
            },
            sort_keys=False,
        ).strip()
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stamp", help="UTC stamp to use, format YYYY-MM-DDTHHMMSSZ")
    parser.add_argument("--start-year", type=int, default=DEFAULT_START_YEAR)
    parser.add_argument("--end-year", type=int)
    parser.add_argument(
        "--no-pwt-helper",
        dest="build_pwt_helper",
        action="store_false",
        help="Skip deriving pwt:rgdpo_pop from pwt_full.",
    )
    parser.set_defaults(build_pwt_helper=True)
    args = parser.parse_args()
    build(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
