#!/usr/bin/env python3
"""Build a Berlin Mietspiegel qualified-rent-index panel from the official PDF table.

The Berlin Mietspiegel is the *qualifizierter Mietspiegel* (qualified rent index)
published by the Berlin Senatsverwaltung. It is the legal reference table of
customary comparative net cold rents (ortsübliche Vergleichsmiete, Nettokaltmiete
in EUR/m2/month) and was the statutory basis around the 2020-2021 Mietendeckel.

These are *index / legal reference* values (a rent-board style benchmark), NOT
observed transaction or listing rents. One row per Mietspiegel cell:
    location_quality (Wohnlage) x building_age_class (Bezugsfertigkeit)
    x dwelling_size_class (Wohnfläche)
with the published Spanne (untere/obere) and Mittelwert in EUR/m2 net cold.

The Mietspiegeltabelle is published only as a machine-readable-but-PDF table;
the open-data portal (daten.berlin.de) exposes only the Wohnlagen geometry (WFS),
not the rent values. We therefore parse the official Mietspiegeltabelle PDF with
pdfplumber. The table is line-ruled and extracts cleanly (3 sub-tables, one per
Wohnlage, with a contiguous Zeile numbering).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import re
import sys
import unicodedata
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_fetcher_base():
    spec = importlib.util.spec_from_file_location("ieset_fetcher_base", ROOT / "data" / "fetchers" / "_base.py")
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

# Default to the most recent edition. The PDF naming convention is stable:
# https://mietspiegel.berlin.de/wp-content/uploads/<YYYY>/<MM>/mietspiegeltabelle<YYYY>.pdf
DEFAULT_EDITION_YEAR = 2026
DEFAULT_TABLE_URL = "https://mietspiegel.berlin.de/wp-content/uploads/2026/05/mietspiegeltabelle2026.pdf"
SOURCE_URL = "https://mietspiegel.berlin.de/"
METHODOLOGY_URL = "https://mietspiegel.berlin.de/"
LICENSE = "Berlin Senatsverwaltung Mietspiegel; verify reuse terms"
SOURCE_DATASET = "Berlin Mietspiegel qualified rent index (Mietspiegeltabelle)"
RENT_INDEX_TYPE = "qualified_rent_index_legal_reference"

# The three Wohnlagen (residential location quality classes), in the order the
# sub-tables appear in the Mietspiegeltabelle and in which Zeile is numbered.
WOHNLAGEN = ["Einfache Wohnlage", "Mittlere Wohnlage", "Gute Wohnlage"]

USER_AGENT = "IESET city-level data builder"

# Berlin's GHSL urban-centre id in the city spine.
BERLIN_GHSL_CITY_ID = "ghsl_ucdb_r2024a:5483"
BERLIN_GHSL_NAME = "Berlin"


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


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


def parse_eur(value: object) -> float | None:
    """Parse a German-formatted EUR/m2 cell like '9,58 €' -> 9.58."""
    if value is None:
        return None
    text = str(value).replace("€", "").replace(" ", "").strip()
    # German decimal comma; thousands separators do not occur at this scale.
    text = text.replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.+-]", "", text)
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def fetch_pdf_bytes(url: str = DEFAULT_TABLE_URL) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as response:
        return response.read()


def assemble_size_class(c2: object, c3: object, c4: object) -> str:
    """Wohnfläche is split across up to three cells, e.g.
    ('40 m²', 'bis unter', '45 m²') or ('', 'ab', '85 m²')."""
    parts = [str(x).strip() for x in (c2, c3, c4) if x is not None and str(x).strip()]
    return " ".join(parts)


def parse_tables(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract the Mietspiegel cells from the table PDF.

    Returns one dict per cell with original German labels preserved.
    """
    rows: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        tables: list[list[list[Any]]] = []
        for page in pdf.pages:
            tables.extend(page.extract_tables() or [])

    # Keep only sub-tables that look like Mietspiegel value tables (carry the
    # untere/Mittelwert/obere triple) and have data rows.
    value_tables: list[list[list[Any]]] = []
    for table in tables:
        has_numeric_row = any(
            row and re.match(r"^\d+$", str(row[0]).strip() or "") and len(row) >= 8
            for row in table
        )
        if has_numeric_row:
            value_tables.append(table)

    if len(value_tables) != len(WOHNLAGEN):
        raise ValueError(
            f"expected {len(WOHNLAGEN)} Wohnlage value tables, found {len(value_tables)}; "
            "PDF layout may have changed"
        )

    for wol, table in zip(WOHNLAGEN, value_tables):
        current_age: str | None = None
        for row in table:
            zeile = str(row[0]).strip() if row[0] is not None else ""
            if not re.match(r"^\d+$", zeile):
                continue
            if len(row) < 8:
                continue
            age = str(row[1]).strip() if row[1] is not None else ""
            if age:
                current_age = age
            size_class = assemble_size_class(row[2], row[3], row[4])
            lower = parse_eur(row[5])
            mittel = parse_eur(row[6])
            upper = parse_eur(row[7])
            rows.append(
                {
                    "zeile": int(zeile),
                    "location_quality_de": wol,
                    "building_age_class_de": current_age,
                    "dwelling_size_class_de": size_class,
                    "net_cold_rent_lower_eur_m2": lower,
                    "net_cold_rent_mean_eur_m2": mittel,
                    "net_cold_rent_upper_eur_m2": upper,
                }
            )
    return rows


def normalise_location_quality(label: str) -> str:
    token = unicodedata.normalize("NFKD", label).encode("ascii", "ignore").decode("ascii").lower()
    if token.startswith("einfach"):
        return "einfache"
    if token.startswith("mittler") or token.startswith("mittel"):
        return "mittlere"
    if token.startswith("gut"):
        return "gute"
    return token


def attach_city_match(panel: pd.DataFrame, city_spine_path: Path) -> pd.DataFrame:
    if not city_spine_path.exists():
        raise FileNotFoundError(f"missing city spine: {city_spine_path}")
    spine = (
        pd.read_csv(city_spine_path)
        if city_spine_path.suffix.lower() == ".csv"
        else pd.read_parquet(city_spine_path)
    )
    match = spine[spine["ieset_city_id"].eq(BERLIN_GHSL_CITY_ID)]
    if match.empty:
        # Fall back to name match on Germany.
        match = spine[
            spine["country_name"].astype(str).eq("Germany")
            & spine["city_name"].astype(str).str.fullmatch("Berlin", case=False)
        ]
    if match.empty:
        panel["ieset_city_id"] = None
        panel["ghsl_city_id"] = None
        panel["ghsl_city_name"] = None
        panel["ghsl_city_rank_2025"] = pd.NA
        panel["ghsl_match_flag"] = False
        return panel
    row = match.iloc[0]
    panel["ieset_city_id"] = row["ieset_city_id"]
    panel["ghsl_city_id"] = str(row["ghsl_city_id"]) if "ghsl_city_id" in match.columns else None
    panel["ghsl_city_name"] = row["city_name"]
    panel["ghsl_city_rank_2025"] = row.get("city_rank_2025", pd.NA)
    panel["ghsl_match_flag"] = True
    return panel


def build_panel(
    *,
    city_spine_path: Path,
    edition_year: int,
    source_url: str,
    pdf_bytes: bytes | None = None,
    table_url: str = DEFAULT_TABLE_URL,
) -> tuple[pd.DataFrame, str, dict[str, Any]]:
    blob = pdf_bytes if pdf_bytes is not None else fetch_pdf_bytes(table_url)
    pdf_sha = sha256_bytes(blob)
    rows = parse_tables(blob)
    if not rows:
        raise ValueError("Berlin Mietspiegeltabelle parse returned no rows")

    panel = pd.DataFrame(rows)
    panel = panel.dropna(
        subset=["net_cold_rent_mean_eur_m2", "net_cold_rent_lower_eur_m2", "net_cold_rent_upper_eur_m2"]
    ).copy()
    if panel.empty:
        raise ValueError("Berlin Mietspiegeltabelle had rows, but none had complete rent values")

    panel["edition_year"] = int(edition_year)
    panel["country_name"] = "Germany"
    panel["city_name"] = "Berlin"
    panel["location_quality_norm"] = panel["location_quality_de"].map(normalise_location_quality)
    panel["rent_index_type"] = RENT_INDEX_TYPE
    panel["source_dataset"] = SOURCE_DATASET
    panel["source_url"] = source_url

    panel = attach_city_match(panel, city_spine_path)

    ordered = [
        "edition_year",
        "country_name",
        "city_name",
        "ieset_city_id",
        "ghsl_city_id",
        "ghsl_city_name",
        "ghsl_city_rank_2025",
        "ghsl_match_flag",
        "zeile",
        "location_quality_de",
        "location_quality_norm",
        "building_age_class_de",
        "dwelling_size_class_de",
        "net_cold_rent_lower_eur_m2",
        "net_cold_rent_mean_eur_m2",
        "net_cold_rent_upper_eur_m2",
        "rent_index_type",
        "source_dataset",
        "source_url",
    ]
    panel = panel[ordered].sort_values(["edition_year", "zeile"]).reset_index(drop=True)

    stats = {
        "panel_rows": int(len(panel)),
        "edition_year": int(edition_year),
        "location_quality_classes": sorted(panel["location_quality_de"].unique().tolist()),
        "building_age_classes": sorted(panel["building_age_class_de"].unique().tolist()),
        "zeile_min": int(panel["zeile"].min()),
        "zeile_max": int(panel["zeile"].max()),
        "ghsl_matched": bool(panel["ghsl_match_flag"].all()),
        "ieset_city_id": panel["ieset_city_id"].iloc[0],
        "net_cold_rent_mean_eur_m2_min": float(panel["net_cold_rent_mean_eur_m2"].min()),
        "net_cold_rent_mean_eur_m2_max": float(panel["net_cold_rent_mean_eur_m2"].max()),
        "source_pdf_sha256": pdf_sha,
        "source_pdf_url": table_url,
    }
    return panel, pdf_sha, stats


def manifest_entry(result: FetchResult) -> dict[str, Any]:
    payload = asdict(result)
    payload["fetch_utc"] = result.fetch_utc.isoformat()
    payload["parquet_path"] = rel(result.parquet_path)
    return payload


def write_manifest(result: FetchResult, manifest_dir: Path, run_stamp: str) -> Path:
    manifest_dir.mkdir(parents=True, exist_ok=True)
    path = manifest_dir / f"fetch_run_{run_stamp}_berlin_mietspiegel.yaml"
    payload = {
        "run_utc": run_stamp,
        "pipeline": "berlin_mietspiegel_panel",
        "entries": [manifest_entry(result)],
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True))
    return path


def emit(
    panel: pd.DataFrame,
    pdf_sha: str,
    stats: dict[str, Any],
    output_path: Path,
    fetch_ts: datetime,
    source_url: str,
    table_url: str,
) -> FetchResult:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(output_path, engine="pyarrow", index=False)
    parquet_sha = sha256_path(output_path)
    return FetchResult(
        publisher="berlin_senatsverwaltung",
        series_id="berlin_mietspiegel_panel",
        source_url=source_url,
        methodology_url=METHODOLOGY_URL,
        license=LICENSE,
        fetch_utc=fetch_ts,
        rows=len(panel),
        frequency="biennial_edition",
        units="net cold rent (Nettokaltmiete), euros per square metre per month",
        currency="EUR",
        start_date=str(stats["edition_year"]),
        end_date=str(stats["edition_year"]),
        sha256=parquet_sha,
        parquet_path=output_path,
        extra={
            "artifacts": {
                "parquet_path": rel(output_path),
                "parquet_sha256": parquet_sha,
                "source_pdf_url": table_url,
                "source_pdf_sha256": pdf_sha,
            },
            "stats": stats,
            "columns": list(panel.columns),
            "rent_index_type": RENT_INDEX_TYPE,
            "construction": (
                "Berlin Mietspiegeltabelle (qualifizierter Mietspiegel) parsed from the official "
                "Senatsverwaltung PDF with pdfplumber. One row per index cell: Wohnlage x "
                "Bezugsfertigkeit x Wohnflaeche, with the published Spanne (untere/obere) and "
                "Mittelwert in EUR/m2 net cold rent. These are QUALIFIED-RENT-INDEX legal "
                "reference values (ortsuebliche Vergleichsmiete), distinct from observed "
                "transaction or listing rents. Mapped to the Berlin GHSL urban centre "
                f"({BERLIN_GHSL_CITY_ID})."
            ),
        },
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--city-spine", default="data/derived/city_universe_top1000.parquet")
    parser.add_argument("--input", help="Optional local Mietspiegeltabelle PDF path (offline build).")
    parser.add_argument("--table-url", default=DEFAULT_TABLE_URL)
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--edition-year", type=int, default=DEFAULT_EDITION_YEAR)
    parser.add_argument("--output", default="data/derived/berlin_mietspiegel_panel.parquet")
    parser.add_argument("--manifest-dir", default="data/manifests")
    parser.add_argument("--fetch-utc", help="Optional UTC timestamp for deterministic builds/tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fetch_ts = parse_fetch_utc(args.fetch_utc)
    pdf_bytes = path_arg(args.input).resolve().read_bytes() if args.input else None
    panel, pdf_sha, stats = build_panel(
        city_spine_path=path_arg(args.city_spine).resolve(),
        edition_year=args.edition_year,
        source_url=args.source_url,
        pdf_bytes=pdf_bytes,
        table_url=args.table_url,
    )
    output_path = path_arg(args.output).resolve()
    result = emit(panel, pdf_sha, stats, output_path, fetch_ts, args.source_url, args.table_url)
    manifest = write_manifest(result, path_arg(args.manifest_dir).resolve(), utc_stamp(fetch_ts))
    print(
        "OK berlin_senatsverwaltung:berlin_mietspiegel_panel "
        f"rows={result.rows} edition={stats['edition_year']} ghsl_matched={stats['ghsl_matched']}"
    )
    print(f"artifact: {rel(output_path)} sha256={result.sha256}")
    print(f"source_pdf_sha256={pdf_sha}")
    print(f"manifest: {rel(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
