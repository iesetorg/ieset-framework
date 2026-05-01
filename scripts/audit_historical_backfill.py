#!/usr/bin/env python3
"""Audit how far back the repo's data, movement, and policy coverage really goes.

Writes:
  - engine/audits/historical_backfill.json
  - engine/historical_backfill.report.md

Use this to steer the 1900-era backfill deliberately instead of guessing.
"""
from __future__ import annotations

import json
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import yaml

try:
    import pyarrow.parquet as pq
except ImportError as e:  # pragma: no cover
    raise SystemExit("pyarrow required; run with venv/bin/python") from e

ROOT = Path(__file__).resolve().parents[1]
MOVEMENTS = ROOT / "movements"
POLICIES = ROOT / "policies"
PUBLISHERS = ROOT / "data" / "fetchers" / "publishers.yaml"
VINTAGES = ROOT / "data" / "vintages"
AUDIT_JSON = ROOT / "engine" / "audits" / "historical_backfill.json"
REPORT_MD = ROOT / "engine" / "historical_backfill.report.md"

HISTORICAL_PRIORITY_IDS = {
    "maddison", "jst", "vdem", "polity5", "nber_historical", "pwt",
    "wid", "shiller", "boe", "bls", "world_bank_wdi", "wgi", "who_gho",
    "owid", "un_desa", "ucdp", "chinn_ito",
}
MAJOR_BACKFILL_COUNTRIES = [
    "USA", "FRA", "ITA", "DEU", "IND", "JPN", "KOR", "PHL", "IDN", "PAK",
    "BRA", "MEX", "CHN", "RUS",
]
HISTORICAL_NOTE_RE = re.compile(r"histor|1800|1870|1900|pre-1929|year 1", re.I)
YEARLIKE_COLUMNS = ("year", "date", "period", "time", "obs_date")

warnings.filterwarnings(
    "ignore",
    message="Could not infer format, so each element will be parsed individually",
    category=UserWarning,
)


def load_yaml(path: Path) -> dict | None:
    doc = yaml.safe_load(path.read_text())
    return doc if isinstance(doc, dict) else None


def collect_temporal_floor(kind_dir: Path, id_key: str) -> dict:
    starts: list[int] = []
    earliest_by_country: dict[str, int] = {}
    counts_by_country: Counter[str] = Counter()
    earliest_docs: list[dict] = []

    for path in sorted(kind_dir.glob("*.yaml")):
        doc = load_yaml(path)
        if not doc:
            continue
        start = (doc.get("timeframe") or {}).get("start")
        if not isinstance(start, int):
            continue
        starts.append(start)
        label = doc.get("name") or doc.get("title") or doc.get(id_key) or path.stem
        if start <= 1945:
            earliest_docs.append({
                "start": start,
                "file": path.name,
                "id": doc.get(id_key, path.stem),
                "label": label,
            })
        for country in doc.get("countries") or []:
            counts_by_country[country] += 1
            if country not in earliest_by_country or start < earliest_by_country[country]:
                earliest_by_country[country] = start

    starts_sorted = sorted(starts)
    decade_counts = Counter((year // 10) * 10 for year in starts)
    gaps = [
        {"country": c, "earliest_start": y, "count": counts_by_country[c], "missing_from_1900_years": y - 1900}
        for c, y in earliest_by_country.items()
        if y > 1900
    ]
    gaps.sort(key=lambda r: (-r["missing_from_1900_years"], r["country"]))

    return {
        "count": len(starts),
        "min_start": min(starts_sorted) if starts_sorted else None,
        "median_start": starts_sorted[len(starts_sorted) // 2] if starts_sorted else None,
        "count_le_1900": sum(1 for y in starts if y <= 1900),
        "count_le_1910": sum(1 for y in starts if y <= 1910),
        "count_le_1945": sum(1 for y in starts if y <= 1945),
        "decade_counts": dict(sorted(decade_counts.items())),
        "earliest_by_country": dict(sorted(earliest_by_country.items())),
        "countries_with_floor_after_1900": gaps,
        "earliest_docs": sorted(earliest_docs, key=lambda r: (r["start"], r["id"])),
    }


def load_publisher_registry() -> dict[str, dict]:
    doc = load_yaml(PUBLISHERS) or {}
    return doc.get("publishers") or {}


def latest_files_by_series(pub_dir: Path) -> list[Path]:
    latest: dict[str, Path] = {}
    for path in sorted(pub_dir.glob("*.parquet")):
        series = path.name.split("@", 1)[0]
        prev = latest.get(series)
        if prev is None or path.stat().st_mtime > prev.stat().st_mtime:
            latest[series] = path
    return sorted(latest.values())


def extract_year_bounds(path: Path) -> tuple[int | None, int | None, str | None]:
    schema_names = set(pq.ParquetFile(path).schema.names)
    col = next((c for c in YEARLIKE_COLUMNS if c in schema_names), None)
    if col is None:
        return None, None, None
    series = pq.read_table(path, columns=[col]).to_pandas()[col]
    if col == "year":
        vals = pd.to_numeric(series, errors="coerce").dropna()
    else:
        dt = pd.to_datetime(series, errors="coerce")
        vals = dt.dt.year.dropna()
    if vals.empty:
        return None, None, col
    return int(vals.min()), int(vals.max()), col


def collect_publisher_floor() -> dict:
    registry = load_publisher_registry()
    summaries = []
    materialized = {p.name for p in VINTAGES.iterdir() if p.is_dir()} if VINTAGES.exists() else set()

    for pub_id, rec in sorted(registry.items()):
        pub_dir = VINTAGES / pub_id
        files = latest_files_by_series(pub_dir) if pub_dir.exists() else []
        bounds = []
        no_year_cols = 0
        for file in files:
            min_year, max_year, col = extract_year_bounds(file)
            if min_year is None:
                no_year_cols += 1
                continue
            bounds.append((file.name.split("@", 1)[0], min_year, max_year, col))
        earliest = min((b[1] for b in bounds), default=None)
        latest = max((b[2] for b in bounds), default=None)
        series_pre1900 = sum(1 for _, lo, _, _ in bounds if lo <= 1900)
        series_pre1950 = sum(1 for _, lo, _, _ in bounds if lo <= 1950)
        summaries.append({
            "publisher_id": pub_id,
            "status": rec.get("status"),
            "materialized": pub_id in materialized,
            "ready": rec.get("status") == "ready",
            "series_count": len(bounds),
            "series_without_year_column": no_year_cols,
            "earliest_year": earliest,
            "latest_year": latest,
            "series_pre1900": series_pre1900,
            "series_pre1950": series_pre1950,
            "notes": rec.get("notes", ""),
        })

    ready_unmaterialized = [
        s for s in summaries
        if s["ready"] and not s["materialized"] and s["publisher_id"] in HISTORICAL_PRIORITY_IDS
    ]
    ready_unmaterialized.sort(key=lambda r: r["publisher_id"])

    materialized_historical = [
        s for s in summaries
        if s["materialized"] and s["earliest_year"] is not None
    ]
    materialized_historical.sort(key=lambda r: (r["earliest_year"], r["publisher_id"]))

    return {
        "publishers": summaries,
        "ready_unmaterialized_historical": ready_unmaterialized,
        "materialized_sorted_by_earliest_year": materialized_historical,
    }


def render_report(mov: dict, pol: dict, pub: dict) -> str:
    major_rows = []
    for country in MAJOR_BACKFILL_COUNTRIES:
        m_start = mov["earliest_by_country"].get(country)
        p_start = pol["earliest_by_country"].get(country)
        if m_start is None and p_start is None:
            continue
        major_rows.append((country, m_start, p_start))

    lines: list[str] = []
    lines.append("# Historical Backfill Audit")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Movements: `{mov['count']}` total, earliest start `{mov['min_start']}`, median start `{mov['median_start']}`, `<=1945`: `{mov['count_le_1945']}`")
    lines.append(f"- Policies: `{pol['count']}` total, earliest start `{pol['min_start']}`, median start `{pol['median_start']}`, `<=1945`: `{pol['count_le_1945']}`")
    lines.append(f"- Historical-ready publishers still unmaterialized: `{len(pub['ready_unmaterialized_historical'])}`")
    lines.append("")

    lines.append("## Major-Country Floors")
    lines.append("")
    lines.append("| Country | Earliest movement | Earliest policy |")
    lines.append("|---|---:|---:|")
    for country, m_start, p_start in major_rows:
        lines.append(f"| {country} | {m_start if m_start is not None else 'n/a'} | {p_start if p_start is not None else 'n/a'} |")
    lines.append("")

    lines.append("## Movement Floor Gaps")
    lines.append("")
    lines.append("| Country | Earliest movement start | Missing years from 1900 | Movement count |")
    lines.append("|---|---:|---:|---:|")
    for row in mov["countries_with_floor_after_1900"][:30]:
        lines.append(f"| {row['country']} | {row['earliest_start']} | {row['missing_from_1900_years']} | {row['count']} |")
    lines.append("")

    lines.append("## Policy Floor Gaps")
    lines.append("")
    lines.append("| Country | Earliest policy start | Missing years from 1900 | Policy count |")
    lines.append("|---|---:|---:|---:|")
    for row in pol["countries_with_floor_after_1900"][:30]:
        lines.append(f"| {row['country']} | {row['earliest_start']} | {row['missing_from_1900_years']} | {row['count']} |")
    lines.append("")

    lines.append("## Existing Pre-1945 Movement Anchors")
    lines.append("")
    for row in mov["earliest_docs"][:20]:
        lines.append(f"- `{row['start']}` — `{row['id']}`: {row['label']}")
    lines.append("")

    lines.append("## Existing Pre-1945 Policy Anchors")
    lines.append("")
    for row in pol["earliest_docs"][:25]:
        lines.append(f"- `{row['start']}` — `{row['id']}`: {row['label']}")
    lines.append("")

    lines.append("## Historical Data Substrate")
    lines.append("")
    lines.append("| Publisher | Earliest year | Latest year | Series | Series <=1900 | Series <=1950 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in pub["materialized_sorted_by_earliest_year"][:25]:
        lines.append(
            f"| {row['publisher_id']} | {row['earliest_year']} | {row['latest_year']} | {row['series_count']} | {row['series_pre1900']} | {row['series_pre1950']} |"
        )
    lines.append("")

    lines.append("## Ready Historical Publishers Still Missing Vintages")
    lines.append("")
    for row in pub["ready_unmaterialized_historical"]:
        lines.append(f"- `{row['publisher_id']}`")
    lines.append("")

    lines.append("## Recommended Backfill Order")
    lines.append("")
    lines.append("1. Land the long-run data spine first: Maddison, JST, V-Dem, Polity5, NBER historical, then the manual-drop PWT/WID queue.")
    lines.append("2. Fill country-level movement floors for the biggest modern states still starting after 1900 or 1945: USA, FRA, ITA, DEU, IND, JPN, KOR, PHL, IDN, PAK.")
    lines.append("3. Backfill policy anchors underneath those movements using historically central statutes rather than trying to create every micro-policy immediately.")
    lines.append("4. Re-run this audit after every batch so the historical floor moves in visible steps instead of disappearing into ad hoc edits.")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    mov = collect_temporal_floor(MOVEMENTS, "movement_id")
    pol = collect_temporal_floor(POLICIES, "policy_id")
    pub = collect_publisher_floor()
    payload = {
        "movements": mov,
        "policies": pol,
        "publishers": pub,
    }
    AUDIT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    REPORT_MD.write_text(render_report(mov, pol, pub))

    print(f"wrote {AUDIT_JSON.relative_to(ROOT)}")
    print(f"wrote {REPORT_MD.relative_to(ROOT)}")
    print(
        f"movements<=1945={mov['count_le_1945']} policies<=1945={pol['count_le_1945']} "
        f"historical_ready_unmaterialized={len(pub['ready_unmaterialized_historical'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
