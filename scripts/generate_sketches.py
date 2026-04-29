#!/usr/bin/env python3
"""Generate real-data sketches for hypotheses that have a parseable outcome
spec but no run artifact yet.

A "sketch" is the raw outcome variable trajectory across the sample countries
over the sample period — no model, no verdict, no coefficients. It uses the
same chart_data.json schema as a run output (so the frontend renders it via
the same component) plus an extra `kind: "sketch"` flag so the UI can badge
it appropriately.

This replaces the stylised PlaceholderChart fallback for any hypothesis whose
spec resolves to data on disk. Rules:

  - skip hypotheses that already have engine/runs/<id>/chart_data.json
    (a real run takes precedence — never overwrite results)
  - skip hypotheses with no parseable outcome source
  - skip hypotheses where the named vintage parquet doesn't exist
  - colour treated countries (where `variables.treatment` lists an
    indicator like "venezuela_post_chavismo") if we can extract them;
    everyone else gets a tasteful donor-pool palette

The output filename is `engine/runs/<id>/chart_data.json` — same path the
frontend already reads.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
HYP_ROOT = REPO / "hypotheses"
RUNS_ROOT = REPO / "engine" / "runs"
VINTAGES = REPO / "data" / "vintages"
SKIP_DIRS = {"steelman", "conditional_taxonomy", "country_year_ideology"}

DONOR_COLORS = [
    "#4E79A7", "#59A14F", "#B07AA1", "#E15759",
    "#F28E2B", "#76B7B2", "#EDC948", "#B6992D", "#9C755F",
    "#8884d8", "#82ca9d", "#ffc658", "#ff7300",
]
TREATED_COLOR = "#1f4e79"

SOURCE_RE = re.compile(r"^([a-z][a-z0-9_]*):([A-Za-z0-9_.\-]+)")


def parse_source(source: str | None) -> tuple[str, str] | None:
    if not isinstance(source, str):
        return None
    m = SOURCE_RE.match(source.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def latest_vintage(pub: str, series: str) -> Path | None:
    d = VINTAGES / pub
    if not d.exists():
        return None
    files = sorted(d.glob(f"{series}@*.parquet"), key=lambda p: p.stat().st_mtime)
    return files[-1] if files else None


def list_hypothesis_files() -> list[Path]:
    out: list[Path] = []
    for topic_dir in HYP_ROOT.iterdir():
        if not topic_dir.is_dir() or topic_dir.name in SKIP_DIRS:
            continue
        for f in topic_dir.glob("*.yaml"):
            if not f.name.startswith("_"):
                out.append(f)
    return out


def extract_treated_countries(doc: dict) -> set[str]:
    """Best-effort: any country mentioned in a treatment-indicator's source
    string (e.g. 'country=VEN' or 'asian_treated' set membership) ends up in
    the treated set. We only colour these specially in the chart."""
    treated: set[str] = set()
    for v in (doc.get("variables") or {}).get("treatment", []) or []:
        src = v.get("source") if isinstance(v, dict) else None
        if not isinstance(src, str):
            continue
        for m in re.finditer(r"\b([A-Z]{3})\b", src):
            treated.add(m.group(1))
    return treated


def first_outcome_source(doc: dict) -> str | None:
    for v in (doc.get("variables") or {}).get("outcome", []) or []:
        if isinstance(v, dict) and v.get("source"):
            return str(v["source"])
    return None


def first_outcome_meta(doc: dict) -> tuple[str, str | None] | None:
    """Return (variable_name, transformation) of the first outcome variable."""
    for v in (doc.get("variables") or {}).get("outcome", []) or []:
        if isinstance(v, dict) and v.get("name"):
            return (str(v["name"]), v.get("transformation"))
    return None


def build_sketch(
    doc: dict, vintage: Path, pub: str, series: str
) -> dict | None:
    import pandas as pd
    import pyarrow.parquet as pq

    sample = doc.get("sample") or {}
    countries = list(sample.get("countries") or [])
    period = sample.get("period") or [None, None]
    if len(period) != 2 or not all(isinstance(p, int) for p in period):
        return None
    start, end = period

    table = pq.read_table(vintage).to_pandas()
    # Many fetchers normalise to (country_iso3, year, value); some don't.
    # If columns differ, try common aliases; otherwise skip.
    if "country_iso3" not in table.columns:
        return None
    if "year" not in table.columns:
        for alt in ("period", "TIME_PERIOD", "fecha"):
            if alt in table.columns:
                table = table.rename(columns={alt: "year"})
                break
        else:
            return None
    if "value" not in table.columns:
        for alt in ("valor", "obs_value", "OBS_VALUE"):
            if alt in table.columns:
                table = table.rename(columns={alt: "value"})
                break
        else:
            return None

    table = table[
        (table["country_iso3"].notna()) & (table["country_iso3"].str.len() == 3)
    ]
    table["year"] = pd.to_numeric(table["year"], errors="coerce").dropna().astype(int) if not table["year"].dtype.kind == "i" else table["year"].astype(int)
    table["value"] = pd.to_numeric(table["value"], errors="coerce")
    table = table[
        (table["country_iso3"].isin(countries))
        & (table["year"] >= start)
        & (table["year"] <= end)
    ].dropna(subset=["value"])

    if table.empty:
        return None

    treated = extract_treated_countries(doc)
    var_meta = first_outcome_meta(doc) or ("outcome", None)
    var_name, transform = var_meta

    series_out = []
    donor_idx = 0
    for code in countries:
        sub = (
            table[table["country_iso3"] == code]
            [["year", "value"]]
            .sort_values("year")
        )
        if sub.empty:
            continue
        is_treated = code in treated
        if is_treated:
            color = TREATED_COLOR
        else:
            color = DONOR_COLORS[donor_idx % len(DONOR_COLORS)]
            donor_idx += 1
        series_out.append(
            {
                "id": code,
                "label": code,
                "color": color,
                "treated": is_treated,
                "points": [
                    {"x": int(r.year), "y": float(r.value)}
                    for r in sub.itertuples()
                ],
            }
        )

    if not series_out:
        return None

    title = doc.get("title") or doc.get("hypothesis_id", "")
    return {
        "kind": "sketch",
        "chart_id": f"{doc['hypothesis_id']}/sketch",
        "title": (
            f"{var_name.replace('_', ' ')} across sample countries, "
            f"{start}–{end}"
        ),
        "subtitle": (
            "Descriptive sketch from raw publisher data. The model has not "
            "yet run — no coefficients, no verdict; this is the outcome "
            "variable's trajectory only."
        ),
        "type": "line",
        "x_axis": {"label": "Year", "type": "linear"},
        "y_axis": {
            "label": var_name + (f" ({transform})" if transform else ""),
            "type": "linear",
        },
        "series": series_out,
        "sources": [
            {
                "publisher_id": pub,
                "series_id": series,
                "vintage_file": str(vintage.relative_to(REPO)),
            }
        ],
        "permalink": f"/h/{doc['hypothesis_id']}",
    }


def main() -> None:
    written = 0
    skipped_have_run = 0
    skipped_no_source = 0
    skipped_no_data = 0
    skipped_no_sample = 0

    for path in list_hypothesis_files():
        try:
            doc = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if not isinstance(doc, dict) or not doc.get("hypothesis_id"):
            continue
        hid = doc["hypothesis_id"]
        out_path = RUNS_ROOT / hid / "chart_data.json"
        if out_path.exists():
            # Don't clobber a real run. Sketches only fill empty slots.
            skipped_have_run += 1
            continue

        sample = doc.get("sample") or {}
        if not sample.get("countries") or not sample.get("period"):
            skipped_no_sample += 1
            continue

        src = first_outcome_source(doc)
        parsed = parse_source(src)
        if parsed is None:
            skipped_no_source += 1
            continue
        pub, series = parsed
        vintage = latest_vintage(pub, series)
        if vintage is None:
            skipped_no_data += 1
            continue

        chart = build_sketch(doc, vintage, pub, series)
        if chart is None:
            skipped_no_data += 1
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(chart, indent=2) + "\n")
        written += 1

    print(f"wrote {written} sketches")
    print(f"  skipped (real run already): {skipped_have_run}")
    print(f"  skipped (no parseable source): {skipped_no_source}")
    print(f"  skipped (no sample / period): {skipped_no_sample}")
    print(f"  skipped (no data on disk):   {skipped_no_data}")


if __name__ == "__main__":
    main()
