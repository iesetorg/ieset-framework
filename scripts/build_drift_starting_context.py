"""Build dated context for the first coded movement in each country.

These observations are levels from external datasets, kept separate from the
movement-direction score. A measurement is an opening observation only when
it is at or before the first coded year and no more than five years earlier.
Later observations are retained with an explicit later-only label.

Normal regeneration uses a small, checked-in extraction of the selected source
rows. Full source vintages are gitignored; --refresh-extraction verifies their
bytes before refreshing the extraction, and --verify-vintages audits it against
those local files. A clean checkout can still verify the public artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DRIFT = ROOT / "data/derived/country_drift.json"
OUTPUT = ROOT / "data/derived/country_drift_starting_context.json"
EXTRACTION = ROOT / "data/inputs/drift_starting_context_observations.json"
OPENING_WINDOW_YEARS = 5

SOURCES = {
    "expense": {
        "path": "data/vintages/world_bank_wdi/GC.XPN.TOTL.GD.ZS@2026-04-30T131014Z.parquet",
        "sha256": "6415fec35cc561ac0d5743aa3ef38de80ea1e8a831eb95dbb214f6f58a5ed9ad",
        "source_url": "https://data.worldbank.org/indicator/GC.XPN.TOTL.GD.ZS",
        "definition_url": "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/GC.XPN.TOTL.GD.ZS",
        "publisher": "World Bank WDI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "government_expense_pct_gdp",
        "label": "Government expense",
        "unit": "% of GDP",
        "caveat": "Expense includes transfers and interest but not all public spending or ownership. Coverage may be central-government only and is not fully comparable across countries.",
        "column": "value",
    },
    "consumption": {
        "path": "data/vintages/world_bank_wdi/NE.CON.GOVT.ZS@2026-05-05T194701Z.parquet",
        "sha256": "a6605c618d3dd91b061c4dae7960c4c0baad66c037125aec44cb6b71ccb6a79d",
        "source_url": "https://data.worldbank.org/indicator/NE.CON.GOVT.ZS",
        "definition_url": "https://databank.worldbank.org/metadataglossary/world-development-indicators/series/NE.CON.GOVT.ZS",
        "publisher": "World Bank WDI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "government_final_consumption_pct_gdp",
        "label": "Government final consumption",
        "unit": "% of GDP",
        "caveat": "Narrower fallback: government purchases of goods and services; it excludes transfers and is not total spending.",
        "column": "value",
    },
    "wgi_regulatory_quality": {
        "path": "data/vintages/wgi/GOV_WGI_RQ.EST@2026-05-05T195213Z.parquet",
        "sha256": "4d8084d77990bc1d10f5630cdf8100c9ce2e1b610ade3aa7b46340fb658c8e2e",
        "source_url": "https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators",
        "definition_url": "https://www.worldbank.org/en/publication/worldwide-governance-indicators/frequently-asked-questions",
        "publisher": "World Bank WGI",
        "license": "CC BY 4.0",
        "license_url": "https://datacatalog.worldbank.org/public-licenses#cc-by",
        "metric_id": "wgi_regulatory_quality_estimate",
        "label": "Regulatory Quality estimate",
        "unit": "WGI estimate",
        "caveat": "Perceptions of how regulations support private-sector development; higher means better perceived quality on an approximately −2.5 to +2.5 scale. It is not economic freedom, ownership or an absolute market/state level. Estimates have uncertainty and later publisher vintages may revise history; small differences should not be overread.",
        "column": "value",
    },
}

USA_1862_CONTEXT = {
    "as_of_year": 1862,
    "summary": (
        "Civil War taxes and the federal internal-revenue office were being "
        "established. Currency included state-bank notes and newly authorized "
        "federal greenbacks; nationwide bank-charter rules followed in 1863–64. "
        "This describes selected institutions, not an economy-wide market/state score."
    ),
    "sources": [
        {"label": "IRS history (1862 revenue law)", "url": "https://www.irs.gov/irs-history-timeline"},
        {"label": "Federal Reserve history (banking before national acts)", "url": "https://www.federalreservehistory.org/essays/national-banking-acts"},
    ],
}


def verified_rows(spec: dict) -> dict[str, list[tuple[int, float]]]:
    path = ROOT / spec["path"]
    if not path.is_file():
        raise FileNotFoundError(f"required pinned vintage missing: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"pinned vintage hash mismatch: {spec['path']}")
    frame = pd.read_parquet(path, columns=["country_iso3", "year", spec["column"]])
    frame = frame.dropna(subset=["country_iso3", "year", spec["column"]])
    result: dict[str, list[tuple[int, float]]] = {}
    for row in frame.itertuples(index=False, name=None):
        iso3, year, value = row
        if not isinstance(iso3, str) or len(iso3) != 3:
            continue
        result.setdefault(iso3, []).append((int(year), float(value)))
    for observations in result.values():
        observations.sort()
    return result


def select_observation(
    rows: list[tuple[int, float]], first_year: int
) -> tuple[int, float, str] | None:
    opening = [(year, value) for year, value in rows if first_year - OPENING_WINDOW_YEARS <= year <= first_year]
    if opening:
        year, value = max(opening, key=lambda row: row[0])
        return year, value, "opening"
    later = [(year, value) for year, value in rows if year > first_year]
    if later:
        year, value = min(later, key=lambda row: row[0])
        return year, value, "later_only"
    return None


def public_observation(spec: dict, selected: tuple[int, float, str] | None) -> dict | None:
    if selected is None:
        return None
    year, value, relation = selected
    return {
        "metric_id": spec["metric_id"],
        "label": spec["label"],
        "value": round(value, 2),
        "unit": spec["unit"],
        "transformation": "Rounded to two decimals from the pinned vintage; no interpolation.",
        "observed_year": year,
        "relation_to_first_coded_year": relation,
        "source_url": spec["source_url"],
        "definition_url": spec["definition_url"],
        "publisher": spec["publisher"],
        "license": spec["license"],
        "license_url": spec["license_url"],
        "vintage_file": spec["path"],
        "vintage_sha256": spec["sha256"],
        "caveat": spec["caveat"],
    }


def extract_selected_rows(drift: dict, source_rows: dict[str, dict]) -> dict:
    """Retain only rows needed to reconstruct each displayed observation."""
    countries = {}
    for iso3, country in sorted(drift["countries"].items()):
        first_year = country["first_coded_year"]
        if first_year is None:
            continue
        selected = {}
        for source in SOURCES:
            row = select_observation(source_rows[source].get(iso3, []), first_year)
            selected[source] = {"year": row[0], "value": round(row[1], 8)} if row else None
        countries[iso3] = {"first_coded_year": first_year, "sources": selected}
    return {
        "schema": "ieset-country-drift-observation-extraction-v1",
        "selection": "Latest observation within five years at or before first coded year, otherwise earliest later observation.",
        "pinned_sources": {
            key: {"vintage_file": spec["path"], "vintage_sha256": spec["sha256"], "source_url": spec["source_url"]}
            for key, spec in SOURCES.items()
        },
        "countries": countries,
    }


def rows_from_extraction(extraction: dict, drift: dict) -> dict[str, dict]:
    if extraction.get("schema") != "ieset-country-drift-observation-extraction-v1":
        raise ValueError("unsupported starting-context extraction schema")
    for key, spec in SOURCES.items():
        pinned = extraction.get("pinned_sources", {}).get(key) or {}
        if pinned.get("vintage_file") != spec["path"] or pinned.get("vintage_sha256") != spec["sha256"] or pinned.get("source_url") != spec["source_url"]:
            raise ValueError(f"starting-context extraction source drift: {key}")
    current_years = {
        iso3: country["first_coded_year"]
        for iso3, country in drift["countries"].items()
        if country["first_coded_year"] is not None
    }
    extraction_years = {
        iso3: country["first_coded_year"]
        for iso3, country in extraction.get("countries", {}).items()
    }
    unexpected = set(extraction_years) - set(current_years)
    changed = {
        iso3 for iso3 in set(extraction_years) & set(current_years)
        if extraction_years[iso3] != current_years[iso3]
    }
    if unexpected or changed:
        raise ValueError("first coded years changed; refresh the source extraction")
    rows: dict[str, dict[str, list[tuple[int, float]]]] = {key: {} for key in SOURCES}
    for iso3, country in extraction["countries"].items():
        for key in SOURCES:
            observation = country.get("sources", {}).get(key)
            if observation is not None:
                rows[key][iso3] = [(int(observation["year"]), float(observation["value"]))]
    return rows


def build_context(drift: dict, source_rows: dict[str, dict]) -> dict:
    countries = {}
    for iso3, country in sorted(drift["countries"].items()):
        first_year = country["first_coded_year"]
        if first_year is None:
            continue
        expense = select_observation(source_rows["expense"].get(iso3, []), first_year)
        consumption = select_observation(source_rows["consumption"].get(iso3, []), first_year)
        # Use the fuller fiscal expense measure when it is available at the
        # opening. A consumption opening is preferable to a much later expense.
        if expense and expense[2] == "opening":
            fiscal_spec, fiscal_selected = SOURCES["expense"], expense
        elif consumption and consumption[2] == "opening":
            fiscal_spec, fiscal_selected = SOURCES["consumption"], consumption
        elif expense and consumption:
            # With no opening observation, prefer the earliest dated later
            # reference point. A later expense is not an opening baseline.
            fiscal_spec, fiscal_selected = (
                (SOURCES["expense"], expense)
                if expense[0] <= consumption[0]
                else (SOURCES["consumption"], consumption)
            )
        elif expense:
            fiscal_spec, fiscal_selected = SOURCES["expense"], expense
        else:
            fiscal_spec, fiscal_selected = SOURCES["consumption"], consumption
        market = select_observation(source_rows["wgi_regulatory_quality"].get(iso3, []), first_year)
        countries[iso3] = {
            "first_coded_year": first_year,
            "fiscal": public_observation(fiscal_spec, fiscal_selected),
            "fiscal_note": (
                "The pinned extraction lacks a source row for this country; refresh from the full source vintage when available."
                if iso3 not in source_rows["expense"] and iso3 not in source_rows["consumption"]
                else ""
            ),
            "market_institutions": public_observation(SOURCES["wgi_regulatory_quality"], market),
            "market_institutions_note": (
                "The pinned extraction lacks a source row for this country; refresh from the full source vintage when available."
                if market is None and iso3 not in source_rows["wgi_regulatory_quality"]
                else "No observation in the pinned World Bank Regulatory Quality series."
                if market is None else ""
            ),
            "market_institutions_source_url": SOURCES["wgi_regulatory_quality"]["source_url"],
            "historical_context": USA_1862_CONTEXT if iso3 == "USA" and first_year == 1862 else None,
        }
    return {
        "schema": "ieset-country-drift-starting-context-v1",
        "opening_window_years": OPENING_WINDOW_YEARS,
        "method": (
            "A source observation is an opening context only when dated at or "
            "before the first coded movement and within five years. Otherwise "
            "the earliest later observation is explicitly marked later-only. "
            "Fiscal and regulatory-quality levels are separate and do not "
            "offset the movement-direction score."
        ),
        "countries": countries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare regenerated output with checked-in JSON")
    parser.add_argument("--refresh-extraction", action="store_true", help="rebuild the checked-in extraction from verified local vintages")
    parser.add_argument("--verify-vintages", action="store_true", help="compare the extraction to verified local vintages")
    args = parser.parse_args()
    drift = json.loads(DRIFT.read_text())
    if args.refresh_extraction:
        full_rows = {key: verified_rows(spec) for key, spec in SOURCES.items()}
        extraction = extract_selected_rows(drift, full_rows)
        EXTRACTION.parent.mkdir(parents=True, exist_ok=True)
        EXTRACTION.write_text(json.dumps(extraction, indent=2, ensure_ascii=False) + "\n")
    else:
        extraction = json.loads(EXTRACTION.read_text())
    if args.verify_vintages:
        full_rows = {key: verified_rows(spec) for key, spec in SOURCES.items()}
        if extract_selected_rows(drift, full_rows) != extraction:
            raise ValueError("checked-in extraction differs from pinned local vintages")
        print("starting-context extraction verified against pinned local vintages")
    source_rows = rows_from_extraction(extraction, drift)
    output = json.dumps(build_context(drift, source_rows), indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != output:
            print(f"stale starting context: {OUTPUT.relative_to(ROOT)}")
            return 1
        print(f"starting context current: {len(drift['countries'])} countries")
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output)
    print(f"wrote {OUTPUT.relative_to(ROOT)} for {len(drift['countries'])} countries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
