#!/usr/bin/env python3
"""Register a value-blind CCKP -> single-item annual FAOSTAT PPI family.

This script reads source hashes, schema, country/year/item/element/month keys,
item labels/CPC codes and the documented unit. It never selects the Value or
Flag columns, inspects their null masks, or fits an outcome model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
import pycountry
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "cckp_faostat_weather_tomatoes_ppi_family_2026_10_10"
ROSTER = "data/pinned_evidence/cckp_faostat_weather_tomatoes_ppi_2026_key_roster.csv"
PREREG = "engine/audits/cckp_faostat_weather_tomatoes_ppi_prereg_2026-10-10.md"
LOCK = "data/pinned_evidence/cckp_faostat_weather_tomatoes_ppi_2026.manifest.json"
CCKP_MANIFEST = "data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml"
CCKP_RAW = "data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json"
CCKP_SHA = "b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14"
PRICE_PANEL = "data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet"
PRICE_SHA = "c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c"
PRICE_ARCHIVE = "data/vintages/faostat/prices@2026-05-02T212150Z.zip"
PRICE_ARCHIVE_SHA = "0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b"
ITEM_CODE, ITEM_LABEL, ITEM_CPC = 388, "Tomatoes", "01234"
INDEX_ELEMENT, ANNUAL_MONTH = 5539, 7021
START, END = 1992, 2024
FAMILY_ALPHA = 0.01
CASES = ("temperature", "precipitation")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iso3(m49: object) -> str | None:
    try:
        country = pycountry.countries.get(numeric=str(m49).strip().replace("'", "").zfill(3))
        return country.alpha_3 if country else None
    except (TypeError, AttributeError):
        return None


def case_id(exposure: str) -> str:
    return f"cckp_faostat_tomatoes_{exposure}_forward_ppi_2026"


def key_selection(source_root: Path) -> tuple[list[tuple[str, int]], list[tuple[int, int, int, str, str]]]:
    source_manifest = yaml.safe_load((ROOT / CCKP_MANIFEST).read_text())
    if source_manifest["raw_path"] != CCKP_RAW or source_manifest["raw_sha256"] != CCKP_SHA:
        raise RuntimeError("CCKP source acquisition manifest differs from fixed source")
    for name, expected in ((CCKP_RAW, CCKP_SHA), (PRICE_PANEL, PRICE_SHA),
                           (PRICE_ARCHIVE, PRICE_ARCHIVE_SHA)):
        if sha256(source_root / name) != expected:
            raise RuntimeError(f"source hash mismatch: {name}")
    # JSON decoding creates numeric scalars, but only dictionary keys are used.
    # No climate measurement is retrieved or summarized by registration.
    climate = json.loads((source_root / CCKP_RAW).read_bytes())["data"]
    keys = {
        variable: {(country, int(period[:4]))
                   for country, periods in climate[variable].items() if country != "KSV"
                   for period in periods.keys()}
        for variable in ("tas", "pr")
    }
    if keys["tas"] != keys["pr"]:
        raise RuntimeError("CCKP tas/pr key grids differ")
    baseline_countries = {
        country for country, _ in keys["tas"]
        if all((country, year) in keys["tas"] for year in range(1961, 1991))
    }
    columns = ["Area Code (M49)", "Item Code", "Item Code (CPC)", "Item",
               "Element Code", "Months Code", "Year"]
    table = pq.read_table(source_root / PRICE_PANEL, columns=columns)
    item_keys: dict[int, set[tuple[str, int]]] = defaultdict(set)
    descriptors: dict[int, tuple[str, str]] = {}
    for m49, item, cpc, label, element, month, year in zip(
            *(table[column].to_pylist() for column in columns)):
        if element != INDEX_ELEMENT or month != ANNUAL_MONTH or year is None:
            continue
        country = iso3(m49)
        if country not in baseline_countries:
            continue
        code = int(item)
        clean_cpc = str(cpc).lstrip("'").strip()
        clean_label = str(label).strip()
        # CPC 01 = crop products; FAO F-prefixed codes are aggregate groups.
        # "Other" and n.e.c. labels are deliberately not a named crop.
        if not clean_cpc.startswith("01") or re.search(r"\bother\b|n\.e\.c\.|\btotal\b|\bprimary\b",
                                                       clean_label, re.I):
            continue
        descriptor = (clean_label, clean_cpc)
        if code in descriptors and descriptors[code] != descriptor:
            raise RuntimeError(f"item descriptor changes within code {code}")
        descriptors[code] = descriptor
        key = (country, int(year))
        if key in item_keys[code]:
            raise RuntimeError(f"duplicate annual PPI key: {code}, {key}")
        item_keys[code].add(key)
    ranked = []
    rosters = {}
    for code, annual_keys in item_keys.items():
        roster = sorted(
            (country, year) for country, year in annual_keys
            if START <= year <= END
            and (country, year - 1) in annual_keys
            and (country, year + 1) in annual_keys
            and (country, year) in keys["tas"]
        )
        countries = len({country for country, _ in roster})
        if len(roster) >= 1300 and countries >= 55:
            label, cpc = descriptors[code]
            ranked.append((len(roster), countries, code, label, cpc))
            rosters[code] = roster
    ranked.sort(key=lambda row: (-row[0], row[2]))
    if not ranked or ranked[0][2:] != (ITEM_CODE, ITEM_LABEL, ITEM_CPC):
        raise RuntimeError(f"top eligible named crop changed: {ranked[:3]}")
    return rosters[ITEM_CODE], ranked


def write_registration(source_root: Path, verify: bool) -> None:
    roster, ranked = key_selection(source_root)
    roster_text = "country_iso3,exposure_year\n" + "".join(f"{country},{year}\n" for country, year in roster)
    roster_sha = hashlib.sha256(roster_text.encode()).hexdigest()
    countries = sorted({country for country, _ in roster})
    table = "\n".join(
        f"| {rank} | {label} | {code} | {cpc} | {n} | {c} |"
        for rank, (n, c, code, label, cpc) in enumerate(ranked[:10], start=1))
    prereg = f"""# Value-blind CCKP weather to FAOSTAT tomatoes PPI preregistration

Two directional, correlated tests are fixed before opening selected PPI values, flags, null masks, climate measurements, or fitted results. This is descriptive calibration only.

## Selection by identifiers alone

The official FAOSTAT annual single-item producer price index uses element {INDEX_ELEMENT}, annual month code {ANNUAL_MONTH}, and base 2014–2016=100. Eligible named crop items have a CPC code starting 01; FAO F-code aggregates and labels containing other, n.e.c., total, or primary are excluded. For each candidate, count countries and exposure years t={START}–{END} with exact country item-index keys at t-1, t, t+1 and CCKP tas/pr keys at t plus every 1961–1990 baseline year. Convert FAO M49 to current ISO3 with pycountry; exclude noncountries and KSV. Require at least 1,300 triple-year keys and 55 countries. Select most keys, breaking ties by ascending item code. No measured values, flags, or missingness are used. The selected named item is **{ITEM_LABEL}**, FAO {ITEM_CODE}, CPC {ITEM_CPC}, with **{len(roster)} keys across {len(countries)} countries**.

| Rank | Named item | Code | CPC | Key years | Countries |
| ---: | --- | ---: | --- | ---: | ---: |
{table}

Frozen key roster: `{ROSTER}`, SHA-256 `{roster_sha}`. Keys are potential observations, not complete cases.

## Sources and analysis fixed before values

World Bank CCKP observed CRU TS4.10 annual country tas (°C) and pr (mm), raw `{CCKP_RAW}`, SHA-256 `{CCKP_SHA}`, previously acquired under `{CCKP_MANIFEST}`. FAOSTAT annual producer-price panel `{PRICE_PANEL}`, SHA-256 `{PRICE_SHA}`; source archive `{PRICE_ARCHIVE}`, SHA-256 `{PRICE_ARCHIVE_SHA}`. The parquet is a locally derived cache without a tracked archive-to-parquet transform. Matching ignored source files are needed for replay. The selected archive rows will be compared with the parquet after lock, including values and flags. The index Unit field in this local parquet is blank; element and official codebook define the 2014–2016=100 index.

At exposure year t, temperature is absolute annual mean departure from the country's 1961–1990 mean, °C. Precipitation is absolute annual departure from its 1961–1990 mean divided by its baseline sample SD. Both climate variables at t and all 30 baseline years must be finite; baseline precipitation SD must be positive. The response is **log(PPI(t+1)/PPI(t))**; prior PPI growth log(PPI(t)/PPI(t-1)) and the other weather departure are controls. Require exact positive finite PPI values at t-1,t,t+1, index element/month, and flags A, E or X at all three years; exclude I, B, M, blanks, and unknown flags. Disclose admitted flags. Exclude absolute prior or future log growth above 1.0 and countries with fewer than five complete exposure years. No interpolation, nearest-year join, substitute index, source refresh, alternate item, or estimator.

For each of two exposures, fit OLS with country and exposure-year fixed effects, prior PPI growth and the other weather exposure. Use country-cluster CR1 SE and two-sided Student t(G−1). Require at least 500 complete years and 30 countries; at least 100 years and 20 countries with focal absolute departure ≥1 °C or ≥1 baseline precipitation SD; full rank; positive finite country-cluster SE; and no country contributing over 20% of focal exposure sum of squares after residualizing all nuisance terms. Any failed gate is INCONCLUSIVE. The directional hypothesis is **positive** subsequent nominal farm-gate PPI growth after unusually large annual weather departures. A coefficient ≥+0.02 and p≤0.01/2=0.005 is SUPPORTED; ≤−0.02 at the same cutoff is REFUTED; every other estimable result is PARTIAL. Both registered cells remain in the denominator even on failure. No alternative sign, test, item, years, flags, or thresholds may be substituted after opening values.

National annual climate averages do not isolate tomato growing zones or seasons. Local-currency nominal producer prices reflect inflation, currency, market policy, imports, demand, and reporting; these effects can confound country/year FE. FAO data may be estimated or imputed upstream despite the selected row flags. The two exposures share observations and are not independent replications. The 0.01/2 correction does not adjust the wider IESET research search. Zero causal, policy, school, position, or featured credit.

Official source documentation: World Bank CCKP https://climateknowledgeportal.worldbank.org/download-data ; CRU methods https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html ; FAOSTAT agricultural producer prices https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 ; FAO methodology https://files-faostat.fao.org/production/PP/PP_e.pdf . FAO/World Bank source rights and attribution apply.
"""
    outputs = {ROSTER: roster_text.encode(), PREREG: prereg.encode()}
    for exposure in CASES:
        ident = case_id(exposure)
        label = ("temperature °C" if exposure == "temperature" else "precipitation baseline SD")
        other = "precipitation" if exposure == "temperature" else "temperature"
        threshold = {
            "family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": FAMILY_ALPHA / 2,
            "expected_beta_sign": "+", "meaningful_beta_min_abs": 0.02,
            "min_complete_rows": 500, "min_complete_countries": 30,
            "min_material_rows": 100, "min_material_countries": 20,
            "min_complete_years_per_country": 5,
            "material_abs_temperature_departure_deg_c": 1.0,
            "material_abs_precipitation_departure_baseline_sd": 1.0,
            "max_abs_ppi_log_growth": 1.0,
            "max_top_country_residualized_exposure_share": 0.20,
            "baseline_years": [1961, 1990], "exposure_years": [START, END],
            "item_code": ITEM_CODE, "index_element": INDEX_ELEMENT,
            "annual_month_code": ANNUAL_MONTH, "roster_sha256": roster_sha,
            "source_lock_path": LOCK, "causal_credit": 0,
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0,
            "featured_eligible": False,
        }
        steelman = f"hypotheses/steelman/{ident}.md"
        spec = {
            "hypothesis_id": ident, "version": 1, "status": "pre_registered",
            "topic": "growth", "claim_direction": "+",
            "claim": f"Larger absolute annual country {label} departure at year t is associated with higher next-year Tomatoes single-item producer price index log growth t→t+1 after prior PPI growth, the other weather departure, and country/year effects.",
            "methodology_note": "Value-blind key-selected single named crop, two-exposure Bonferroni family. Annual FAOSTAT single-item PPI, not an aggregate price index; 2014–2016=100. Source hashes, codes, schema and keys alone were inspected at registration.",
            "evidence_type": "associational",
            "sample": {"countries": countries, "period": [1991, 2025], "temporal_structure": "panel",
                       "exclusion_rules": [
                           "Use only country/exposure-year keys in the committed roster; no interpolation or substitutions.",
                           "Use exact annual Tomatoes single-item PPI values at t-1,t,t+1, finite and positive, with A/E/X flags at all three years; exclude I/B/M/blank/unknown.",
                           "Require complete finite tas and pr at t and every 1961–1990 baseline year and positive pr sample SD.",
                           "Exclude absolute prior/future PPI log growth above 1.0 and countries with fewer than five complete years.",
                           "Do not change item, exposure, years, transformation, gates, estimator, flags or family size after opening measurements."]},
            "variables": {
                "outcome": [{"name": "next_year_tomatoes_ppi_log_growth", "source": "faostat:producer_prices",
                             "transformation": "log(Tomatoes single-item annual PPI at t+1) minus log(PPI at t); index 2014–2016=100"}],
                "treatment": [{"name": f"absolute_{exposure}_departure", "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                               "transformation": f"Absolute annual country {label} departure from 1961–1990 normal"}],
                "controls": [{"name": "prior_tomatoes_ppi_log_growth", "source": "faostat:producer_prices",
                              "transformation": "log(PPI at t) minus log(PPI at t-1)"},
                             {"name": f"other_{other}_departure", "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                              "transformation": f"Absolute annual country {other} departure"}]},
            "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country",
                          "notes": "Country/exposure-year FE OLS, prior PPI growth and other-weather control; country CR1 and two-sided Student t(G-1); full-rank and concentration gates."},
            "falsification": {"test": f"{FAMILY}_{exposure}",
                              "rule": "INCONCLUSIVE on any exact-source, complete-case, material-exposure, five-year-country, full-rank, positive finite SE, or 20% top-country residualized-exposure gate failure. SUPPORTED iff beta >= +0.02 and two-sided p <= 0.005; REFUTED iff beta <= -0.02 at the same cutoff; otherwise PARTIAL when estimable. Both cases remain in one family.",
                              "threshold": threshold},
            "prior_confidence": 0.20,
            "disclosure": "Descriptive calibration only. Annual country weather and nominal local-currency farm-gate price indices are confounded and do not identify a causal weather or policy effect. Zero causal, policy, school, position and featured credit.",
            "steelman": steelman,
            "scope": {"period": [1991, 2025], "countries": countries, "outcome_dim": ["inflation"],
                      "policy_family": [], "treatment_tags": ["tomatoes", exposure, "climate_weather"]},
            "covers_claims": [], "linked_hypotheses": [], "linked_conditions": [],
        }
        outputs[f"hypotheses/growth/{ident}.yaml"] = (
            "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
            + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)).encode()
        outputs[steelman] = (
            f"# Steelman: annual {exposure} departure and later Tomatoes producer prices\n\n"
            f"Large annual {exposure} departures can disrupt harvests or anticipated supply and raise subsequent farm-gate prices. "
            "The frozen positive prediction is tested within countries, removing common exposure years and controlling prior price growth and the other weather departure.\n\n"
            "The strongest alternative is that national annual climate averages miss tomato growing regions and seasons. "
            "Rainfall surplus can help dry areas, and warmth can benefit cooler areas. Prices also move with inflation, exchange rates, imports, demand, policy, energy, storage, crop substitution and FAO estimation. "
            "Even a positive, family-significant coefficient would be descriptive, not causal.\n\n"
            "Both correlated cells share one two-sided 0.01/2 cutoff, strict source and sample gates, and zero causal, policy, school, position or featured credit.\n"
        ).encode()
    for name, content in outputs.items():
        path = ROOT / name
        if verify:
            if not path.is_file() or path.read_bytes() != content:
                raise RuntimeError(f"registration replay mismatch: {name}")
        else:
            if path.exists():
                raise RuntimeError(f"registration target already exists: {name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(f"{'Exact key-only registration replay passed' if verify else 'Registered'}: "
          f"{len(CASES)} cells, {len(roster)} potential rows, {len(countries)} countries, SHA {roster_sha}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    write_registration(args.source_root, args.verify)


if __name__ == "__main__":
    main()
