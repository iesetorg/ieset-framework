#!/usr/bin/env python3
"""Register a value-blind, 56-cell country-climate/crop family.

Only source hashes, schema, item codes, country/year keys, and codebook units
are read here. Crop measurements, flags, climate values, and null masks are
deliberately unavailable to the registration logic.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import pyarrow.parquet as pq
import pycountry
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "cckp_faostat_weather_crop_family_2026_10_10"
ROSTER = "data/pinned_evidence/cckp_faostat_weather_crop_2026_key_roster.csv"
PREREG = "engine/audits/cckp_faostat_weather_crop_prereg_2026-10-10.md"
LOCK = "data/pinned_evidence/cckp_faostat_weather_crop_2026.manifest.json"
CCKP_SOURCE_MANIFEST = "data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml"
FAO_PANEL = "data/vintages/faostat/faostat_prod_All_Data_(Normalized)@2026-05-02T212007Z.parquet"
FAO_PANEL_SHA = "02d93061467ca6e9a6cc738ba72702271d26abbaa21480c51d04d29b1017734a"
FAO_ARCHIVE = "data/vintages/faostat/Production_Crops_Livestock_E_All_Data_(Normalized)@2026-05-02T211649Z.zip"
FAO_ARCHIVE_SHA = "c5835418c18f9322e7decbd6800f93a216eaae3cdfa31acb08f0518c0c6d6853"
FAO_FLAGS = "data/vintages/faostat/faostat_prod_Flags@2026-05-02T212007Z.parquet"
FAO_FLAGS_SHA = "c9c44507c716b6fe7bd22d68febe1752c3cb4d08c11d62e2311092a8bacc2a6d"
START, END = 1963, 2024
FAMILY_ALPHA = 0.01
ITEMS = {
    "cereals": (1717, "cereals, primary", "aggregate"),
    "roots": (1720, "roots and tubers", "aggregate"),
    "pulses": (1726, "pulses", "aggregate"),
    "oilcrops": (1732, "oilcrops, oil equivalent", "aggregate"),
    "wheat": (15, "wheat", "crop"),
    "rice": (27, "rice", "crop"),
    "maize": (56, "maize", "crop"),
    "potatoes": (116, "potatoes", "crop"),
    "cassava": (125, "cassava", "crop"),
    "soybean": (236, "soya beans", "crop"),
    "sugarcane": (156, "sugar cane", "crop"),
    "coffee": (656, "coffee, green", "crop"),
    "cotton": (328, "seed cotton, unginned", "crop"),
    "tomatoes": (388, "tomatoes", "crop"),
}
MARGINS = {"yield": (5412, "yield", "kg/ha", "productivity"),
           "area": (5312, "area harvested", "ha", "industrial_capability")}
WEATHER = {"temperature": ("tas", "absolute annual mean-temperature departure from 1961–1990 country normal, degC"),
           "precipitation": ("pr", "absolute annual precipitation departure from 1961–1990 country normal, divided by that baseline's sample SD")}
CASES = [(item, margin, weather) for item in ITEMS for margin in MARGINS for weather in WEATHER]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iso3(m49: object) -> str | None:
    try:
        country = pycountry.countries.get(numeric=str(m49).strip().replace("'", "").zfill(3))
        return country.alpha_3 if country else None
    except (TypeError, AttributeError):
        return None


def ident(item: str, margin: str, weather: str) -> str:
    return f"cckp_faostat_{item}_{weather}_{margin}_2026"


def prepare(fao_root: Path, cckp_root: Path) -> None:
    if any((ROOT / p).exists() for p in (ROSTER, PREREG)):
        raise RuntimeError("registration already exists")
    source = yaml.safe_load((ROOT / CCKP_SOURCE_MANIFEST).read_text())
    raw = cckp_root / source["raw_path"]
    if sha256(raw) != source["raw_sha256"] or sha256(fao_root / FAO_PANEL) != FAO_PANEL_SHA:
        raise RuntimeError("source bytes differ from predeclared snapshot")
    # JSON decoding necessarily constructs scalar objects, but the registration
    # logic accesses only dictionary keys. It never reads or summarizes values.
    climate = json.loads(raw.read_bytes())["data"]
    climate_keys = {v: {(c, int(period[:4])) for c, periods in climate[v].items()
                        if c != "KSV" for period in periods.keys()} for v in ("tas", "pr")}
    if climate_keys["tas"] != climate_keys["pr"]:
        raise RuntimeError("climate keys differ between variables")
    needed = {code for code, _, _ in ITEMS.values()}
    table = pq.read_table(fao_root / FAO_PANEL, columns=["Area Code (M49)", "Item Code", "Element Code", "Year"])
    keys: dict[tuple[int, int], set[tuple[str, int]]] = defaultdict(set)
    for area, item, element, year in zip(*(table[col].to_pylist() for col in table.column_names)):
        if item not in needed or element not in (5312, 5412) or year is None:
            continue
        country = iso3(area)
        if country:
            key = (country, int(year))
            if key in keys[int(item), int(element)]:
                raise RuntimeError(f"duplicate FAO key: {item}, {element}, {key}")
            keys[int(item), int(element)].add(key)
    rows = []
    for item, (code, _, _) in ITEMS.items():
        for margin, (element, _, _, _) in MARGINS.items():
            selected = keys[code, element]
            for country, year in sorted(selected):
                if not START <= year <= END:
                    continue
                if all((country, y) in selected for y in (year - 1, year - 2)) and all(
                    (country, y) in climate_keys[variable] for variable in ("tas", "pr")
                    for y in (year, *range(1961, 1991))
                ):
                    rows.append((item, margin, country, year))
    roster = ROOT / ROSTER
    roster.parent.mkdir(parents=True, exist_ok=True)
    with roster.open("w", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["item", "margin", "country_iso3", "outcome_year"])
        writer.writerows(rows)
    roster_hash = sha256(roster)
    by_cell = defaultdict(list)
    for item, margin, country, year in rows:
        by_cell[item, margin].append((country, year))
    if len(by_cell) != len(ITEMS) * len(MARGINS):
        raise RuntimeError("one or more item/margin key rosters are empty")
    for item, margin, weather in CASES:
        code, label, kind = ITEMS[item]
        element, margin_label, unit, dimension = MARGINS[margin]
        variable, weather_label = WEATHER[weather]
        other = "pr" if variable == "tas" else "tas"
        countries = sorted({country for country, _ in by_cell[item, margin]})
        case_id = ident(item, margin, weather)
        spec_path = ROOT / f"hypotheses/growth/{case_id}.yaml"
        steelman_path = f"hypotheses/steelman/{case_id}.md"
        claim = (f"For the fixed 1963–2024 country-year roster, larger {weather_label} "
                 f"is associated with lower same-year {label} {margin_label} log growth "
                 "after prior crop growth, the other climate-departure measure, and country/year effects.")
        threshold = {
            "family_id": FAMILY, "family_size": len(CASES), "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": FAMILY_ALPHA / len(CASES),
            "expected_beta_sign": "-", "meaningful_beta_min_abs": 0.02,
            "min_complete_rows": 500, "min_complete_countries": 30,
            "min_material_rows": 100, "min_material_countries": 20,
            "material_abs_temperature_departure_deg_c": 1.0,
            "material_abs_precipitation_departure_baseline_sd": 1.0,
            "min_complete_years_per_country": 5,
            "max_abs_outcome_log_growth": 1.0,
            "max_top_country_residualized_exposure_share": 0.20,
            "baseline_years": [1961, 1990], "outcome_years": [START, END],
            "roster_sha256": roster_hash, "source_lock_path": LOCK,
            "causal_credit": 0, "school_score_eligible": False,
            "school_score_credit": 0, "policy_score_eligible": False,
            "policy_score_credit": 0, "featured_eligible": False,
        }
        spec = {
            "hypothesis_id": case_id, "version": 1, "status": "pre_registered",
            "topic": "growth", "claim_direction": "-", "claim": claim,
            "methodology_note": ("Value-blind 56-cell climate/crop family: four FAO aggregate groups and ten named crops, "
                                 "two crop margins, two distinct weather exposures. Only source schema, hashes, "
                                 "item/country/year keys, units and flag codebook were inspected at registration; "
                                 "measurements, null masks and flags remain unopened. All cells share one family "
                                 "multiplicity denominator and are correlated, not independent replications."),
            "evidence_type": "associational",
            "sample": {"countries": countries, "period": [1961, END], "temporal_structure": "panel",
                       "exclusion_rules": [
                           "Use only country-year keys in the committed roster; no interpolation, nearest-year join, or substitutions.",
                           "Map FAOSTAT M49 to current ISO3 with pycountry; exclude noncountries and the CCKP KSV code.",
                           "Require exact crop values at t, t-1 and t-2, finite and positive, exact unit; admit only FAO A, E and X flags and report their counts. Exclude I, B, M, blank or unknown flags.",
                           "Require climate tas and pr at t and all 1961–1990 baseline years; finite values and a positive precipitation baseline sample SD.",
                           "Exclude absolute current or prior crop log growth above 1.0; keep countries with at least five complete years.",
                           "Do not change item, margin, climate exposure, years, transformation, gates, estimator or family size after opening selected measurements."]},
            "variables": {
                "outcome": [{"name": f"same_year_{margin}_log_growth", "source": "faostat:crop_and_livestock_products",
                             "transformation": f"log({margin_label} at year t) minus log({margin_label} at t-1), item {code}, element {element}, unit {unit}"}],
                "treatment": [{"name": f"absolute_{weather}_departure", "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                               "transformation": weather_label,
                               "notes": "Annual country-average gridded observation; does not isolate crop-zone weather."}],
                "controls": [{"name": "prior_crop_log_growth", "source": "faostat:crop_and_livestock_products",
                              "transformation": f"log({margin_label} at t-1) minus log({margin_label} at t-2)"},
                             {"name": f"other_{other}_departure", "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                              "transformation": WEATHER["precipitation" if other == "pr" else "temperature"][1]}]},
            "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"], "clustering": "country",
                          "notes": ("OLS with country and outcome-year fixed effects, prior crop log growth and the other "
                                    "weather-departure control; country-cluster CR1 standard error and two-sided "
                                    "Student t(G-1), full-rank and residualized-exposure concentration gates. "
                                    "No alternate estimator is substituted on failure.")},
            "falsification": {"test": f"{FAMILY}_{item}_{margin}_{weather}",
                              "rule": ("INCONCLUSIVE if exact-source, complete-case (500/30), material exposure (100/20), "
                                       "five-year-country, rank, positive finite country-cluster SE, or 20% top-country "
                                       "residualized-exposure cap fails. SUPPORTED iff beta <= -0.02 and two-sided "
                                       "p <= 0.01/56. REFUTED iff beta >= +0.02 at the same p cutoff; otherwise "
                                       "PARTIAL when estimable. All 56, including failures, remain in the denominator."),
                              "threshold": threshold},
            "prior_confidence": 0.25 if margin == "yield" else 0.15,
            "disclosure": ("Descriptive calibration only. Country-average climate misses crop growing zones and seasonal timing; "
                           "crop mixes, irrigation, technology, reporting and other shocks can confound the association. "
                           "FAO group outcomes overlap named crops. No causal, policy, position, school or featured credit."),
            "steelman": steelman_path,
            "scope": {"period": [1961, END], "countries": countries, "outcome_dim": [dimension],
                      "policy_family": [], "treatment_tags": [item, weather, "climate_weather"]},
            "covers_claims": [], "linked_hypotheses": [], "linked_conditions": [],
        }
        spec_path.parent.mkdir(parents=True, exist_ok=True)
        spec_path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" +
                             yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        steel = (
            f"# Steelman: {weather} departures and {label} {margin_label}\n\n"
            f"{kind.capitalize()} {label} production can be disrupted when annual {weather} departs far from a country's "
            f"1961–1990 normal. The frozen directional prediction is lower within-year {margin_label} growth. "
            "The design compares each country with itself, removes common calendar years, and controls prior crop growth "
            "and the other weather-departure measure.\n\n"
            "A strong alternative is that country-wide annual weather averages do not describe the crop's growing "
            "locations or season. Precipitation surpluses may help dry areas; warmer years may help cold areas. "
            "Irrigation, planting decisions, crop composition, pests, reporting estimates and long-run adaptation "
            "can also dominate. A negative, null or positive coefficient is an association, not a causal crop response.\n\n"
            "This is one of 56 overlapping crop/margin/weather cells. The entire family uses the two-sided 0.01/56 "
            "cutoff, strict source and sample gates, and zero causal, policy, school, position or featured credit.\n"
        )
        (ROOT / steelman_path).write_text(steel)
    lines = ["# Value-blind CCKP weather and FAOSTAT crop preregistration", "",
             "Fifty-six complete, claim-matched cells were fixed before selected climate or crop measurements, flags, null masks, variance, or fits were inspected. Four broad FAO crop groups and ten named crops span staples and agricultural cash crops; two distinct supply margins and two weather departures are tested. Group and named-crop cells overlap and must never be reported as independent replications.", "",
             f"Key roster: `{ROSTER}`; SHA-256 `{roster_hash}`. These are source keys, not measured complete cases.", "",
             "| Crop item | FAO item code | Margin | Country-years | Countries |", "| --- | ---: | --- | ---: | ---: |"]
    for item, (code, _, _) in ITEMS.items():
        for margin in MARGINS:
            cell = by_cell[item, margin]
            lines.append(f"| {item} | {code} | {margin} | {len(cell)} | {len({c for c, _ in cell})} |")
    lines += ["", "## Frozen source custody", "",
              f"World Bank CCKP observed CRU TS4.10 annual country series (tas °C and accumulated pr mm), 1901–2025; exact raw source `{source['raw_path']}`, SHA-256 `{source['raw_sha256']}`. Source acquisition manifest: `{CCKP_SOURCE_MANIFEST}`. FAOSTAT crop panel `{FAO_PANEL}`, SHA-256 `{FAO_PANEL_SHA}`; source ZIP `{FAO_ARCHIVE}`, SHA-256 `{FAO_ARCHIVE_SHA}`; flag legend `{FAO_FLAGS}`, SHA-256 `{FAO_FLAGS_SHA}`. FAO parquet is an earlier locally derived cache without a tracked archive-to-parquet transformation; this limits provenance. Matching ignored raw files are required for replay.", "",
              "FAO crop elements 5312 (harvested area, ha) and 5412 (yield, kg/ha); only A (official), E (estimated) and X (external) flags are admissible. I (imputed), B (break), M (missing), blank and unknown are excluded. Current ISO3 only; geopolitical/historical labels and KSV are not joined.", "",
              "## Frozen analysis and failure gates", "",
              "Outcome year t=1963–2024. Crop response is log(value_t/value_(t-1)); prior crop growth t-2→t-1 is controlled. Temperature exposure is absolute annual mean-temperature departure from the country's 1961–1990 mean in °C. Precipitation exposure is absolute departure from the 1961–1990 mean divided by its sample SD. The other departure is controlled in each cell. Annual CCKP labels `YYYY-07` identify annual observations, not July-only values. Require finite positive crop values, finite weather, exact units, FAO A/E/X flags, at least five complete years per country, and absolute current/prior crop log growth no more than 1.0. No interpolation or proxy.", "",
              "OLS includes country and outcome-year fixed effects, prior crop growth and the other climate departure. CR1 country-cluster standard errors use two-sided Student t(G-1). Each cell needs at least 500 complete country-years in at least 30 countries, at least 100 material-exposure years in at least 20 countries (temperature departure ≥1 °C or precipitation departure ≥1 baseline SD), a full-rank design, positive finite SE, and no country holding over 20% of exposure sum of squares after residualizing all nuisance terms. Failure is INCONCLUSIVE. Negative beta ≤−0.02 with p≤0.01/56 is SUPPORTED; positive beta ≥+0.02 at the same cutoff is REFUTED; all other estimable outcomes are PARTIAL. All 56 remain in the family denominator. The 0.01/56 cutoff does not adjust wider IESET research selection.", "",
              "These are descriptive country-level associations, not crop-zone weather exposure or causal climate effects. Zero causal, policy, school, position and featured credit. Source rights and attribution apply.", "",
              "## Official source documentation", "",
              "- World Bank CCKP selector: https://climateknowledgeportal.worldbank.org/download-data",
              "- World Bank CRU collection and methods: https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html",
              "- FAO crop production catalog: https://data.fao.org/catalog/iso/d24a448b-3b62-4c09-8c1d-4a39bb599876",
              "- FAO database terms: https://www.fao.org/contact-us/terms/db-terms-of-use/en", ""]
    audit = ROOT / PREREG
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text("\n".join(lines))
    print(json.dumps({"family_size": len(CASES), "roster_sha256": roster_hash,
                      "roster_rows": len(rows), "crop_margin_cells": len(by_cell)}, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--faostat-root", type=Path, required=True)
    p.add_argument("--cckp-root", type=Path, required=True)
    a = p.parse_args()
    prepare(a.faostat_root, a.cckp_root)
