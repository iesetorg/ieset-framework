#!/usr/bin/env python3
"""Register every coverage-qualified named crop PPI/weather case without values.

Only source hashes, item/CPC labels, and country/year/element/month keys are
used. Value, Flag and their null masks are never selected from the parquet.
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
FAMILY = "cckp_faostat_weather_named_crop_ppi_family_2026_10_10"
ROSTER = "data/pinned_evidence/cckp_faostat_weather_named_crop_ppi_2026_key_roster.csv"
PREREG = "engine/audits/cckp_faostat_weather_named_crop_ppi_prereg_2026-10-10.md"
LOCK = "data/pinned_evidence/cckp_faostat_weather_named_crop_ppi_2026.manifest.json"
CCKP_MANIFEST = "data/manifests/source_lock_cckp_cru_ts410_2026-10-10.yaml"
CCKP_RAW = "data/vintages/world_bank_cckp/cru_ts4_10_tas_pr_annual_global@2026-10-10T141853Z.json"
CCKP_SHA = "b3477a2f1186990e3cdf156e9dd5788573e25ab5381db6ee6cb08e90fe225a14"
PRICE_PANEL = "data/vintages/faostat/faostat_prices_main@2026-05-02T212150Z.parquet"
PRICE_SHA = "c59917daee0645066ee5730cf24b9d8058900c81d8510f3892cb7819d1e5a05c"
PRICE_ARCHIVE = "data/vintages/faostat/prices@2026-05-02T212150Z.zip"
PRICE_ARCHIVE_SHA = "0eaff92014d4af5fc2f477dbd436a792bfed1a408645e9ed18d8e45ab14fdc6b"
INDEX_ELEMENT, ANNUAL_MONTH = 5539, 7021
START, END = 1995, 2022
MIN_KEY_ROWS, MIN_KEY_COUNTRIES = 1300, 55
EXPOSURES = ("temperature", "precipitation")
FAMILY_ALPHA = 0.01
SUPERSEDED_REGISTRATION_COMMIT = "278af727f3004e271b87df6d920cdb8a8fea2e11"


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


def case_id(code: int, exposure: str) -> str:
    return f"cckp_faostat_crop{code}_{exposure}_forward_ppi_2026"


def source_keys(source_root: Path) -> dict[int, tuple[str, str, list[tuple[str, int]]]]:
    acquisition = yaml.safe_load((ROOT / CCKP_MANIFEST).read_text())
    if acquisition["raw_path"] != CCKP_RAW or acquisition["raw_sha256"] != CCKP_SHA:
        raise RuntimeError("CCKP source acquisition manifest differs")
    for name, expected in ((CCKP_RAW, CCKP_SHA), (PRICE_PANEL, PRICE_SHA),
                           (PRICE_ARCHIVE, PRICE_ARCHIVE_SHA)):
        if sha256(source_root / name) != expected:
            raise RuntimeError(f"source hash mismatch: {name}")
    # JSON decoding constructs scalar objects but registration accesses only keys.
    climate = json.loads((source_root / CCKP_RAW).read_bytes())["data"]
    climate_keys = {
        variable: {(country, int(period[:4]))
                   for country, series in climate[variable].items() if country != "KSV"
                   for period in series.keys()}
        for variable in ("tas", "pr")
    }
    if climate_keys["tas"] != climate_keys["pr"]:
        raise RuntimeError("CCKP variable key grids differ")
    baseline_countries = {
        country for country, _ in climate_keys["tas"]
        if all((country, year) in climate_keys["tas"] for year in range(1961, 1991))
    }
    columns = ["Area Code (M49)", "Item Code", "Item Code (CPC)", "Item",
               "Element Code", "Months Code", "Year"]
    table = pq.read_table(source_root / PRICE_PANEL, columns=columns)
    keys: dict[int, set[tuple[str, int]]] = defaultdict(set)
    names: dict[int, tuple[str, str]] = {}
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
        # CPC division 01 identifies crop products. F-prefixed FAO aggregate
        # codes and 02 livestock are absent. Generic catchalls are excluded.
        if (not clean_cpc.startswith("01") or
                re.search(r"\bother\b|n\.e\.c\.|\btotal\b|\bprimary\b",
                          clean_label, re.I)):
            continue
        descriptor = (clean_label, clean_cpc)
        if code in names and names[code] != descriptor:
            raise RuntimeError(f"item descriptor changed for code {code}")
        names[code] = descriptor
        key = (country, int(year))
        if key in keys[code]:
            raise RuntimeError(f"duplicate annual PPI key {code}, {key}")
        keys[code].add(key)
    eligible = {}
    for code, annual in keys.items():
        roster = sorted(
            (country, year) for country, year in annual
            if START <= year <= END
            and (country, year - 1) in annual
            and (country, year + 1) in annual
            and (country, year) in climate_keys["tas"]
        )
        if len(roster) >= MIN_KEY_ROWS and len({c for c, _ in roster}) >= MIN_KEY_COUNTRIES:
            eligible[code] = (*names[code], roster)
    if len(eligible) != 59 or 388 not in eligible or 826 not in eligible:
        raise RuntimeError(f"unexpected frozen key-qualified crop set: {sorted(eligible)}")
    return dict(sorted(eligible.items()))


def outputs(source_root: Path) -> tuple[dict[str, bytes], int, int, int, str]:
    eligible = source_keys(source_root)
    family_size = len(eligible) * len(EXPOSURES)
    p_max = FAMILY_ALPHA / family_size
    roster_rows = [
        (code, country, year)
        for code, (_label, _cpc, keys) in eligible.items()
        for country, year in keys
    ]
    roster_text = "item_code,country_iso3,exposure_year\n" + "".join(
        f"{code},{country},{year}\n" for code, country, year in roster_rows)
    roster_hash = hashlib.sha256(roster_text.encode()).hexdigest()
    table = "\n".join(
        f"| {code} | {label} | {cpc} | {len(keys)} | {len({c for c, _ in keys})} |"
        for code, (label, cpc, keys) in eligible.items())
    prereg = f"""# Value-blind CCKP annual weather to named-crop FAOSTAT PPI preregistration

This registration **supersedes the narrower two-cell registration in commit `{SUPERSEDED_REGISTRATION_COMMIT}` before any new source-lock commit, selected price/climate measurement or flag access, or model fit**. The earlier registration kept only the top-coverage item rather than the complete eligible family. Its files are removed in the superseding commit; its first-addition history remains visible. The 59-item, {family_size}-cell family below is the sole executable registration.

## Key-only item selection

Use annual FAOSTAT producer price index element {INDEX_ELEMENT}, annual month {ANNUAL_MONTH}, country M49 mapped to current ISO3 by pycountry, and exact years t−1,t,t+1 for t={START}–{END}. Require CCKP tas and pr keys at t and all 1961–1990 baseline years; omit KSV. Named crops have CPC code prefix 01. Exclude F-code aggregates and labels containing other, n.e.c., total or primary. Include nonfood crop products such as cotton lint and unmanufactured tobacco because they satisfy the same CPC rule; do not hand-pick crop types. Require at least {MIN_KEY_ROWS:,} country-year triples and {MIN_KEY_COUNTRIES} countries per item. **Every** qualified item is registered with two weather exposures. Only identifiers, labels, codebook, schema and source hashes were read; no Value/Flag columns, null masks or climate measurements were inspected.

Frozen key roster `{ROSTER}`, SHA-256 `{roster_hash}`: **{len(roster_rows):,} item-country-year keys, {len(eligible)} named items, {family_size} tests**. Potential keys are not complete measured cases.

| FAO item code | Named item | CPC | Key years | Countries |
| ---: | --- | --- | ---: | ---: |
{table}

## Source and analysis contract

World Bank CCKP CRU TS4.10 annual country tas (°C) and pr (mm): `{CCKP_RAW}`, SHA-256 `{CCKP_SHA}`, acquisition manifest `{CCKP_MANIFEST}`. FAOSTAT agricultural producer-price parquet: `{PRICE_PANEL}`, SHA-256 `{PRICE_SHA}`; raw ZIP: `{PRICE_ARCHIVE}`, SHA-256 `{PRICE_ARCHIVE_SHA}`. The parquet is a locally derived cache without a tracked archive-to-parquet transform; selected archive rows will be compared to the cache after lock. The PPI uses base 2014–2016=100 under the official FAO codebook. The local PPI Unit field is blank, so element/month codes and official metadata define the measure. Matching ignored local source files are required for replay.

Temperature exposure at t is absolute annual country mean departure from its 1961–1990 mean in °C. Precipitation exposure is absolute annual country departure from its 1961–1990 mean divided by baseline sample SD. Require both variables finite at t and every baseline year, with positive pr SD. Outcome is subsequent `log(PPI_(t+1)/PPI_t)`; control prior `log(PPI_t/PPI_(t-1))` and the other departure. All three annual single-item PPI values must be finite and positive with row flags A, E or X; I, B, M, blank and unknown flags fail. Disclose admitted flag counts. Exclude absolute prior or subsequent PPI log growth >1.0 and countries with fewer than five complete exposure years. No interpolation, index substitution, source refresh or alternate model.

Each cell uses country and exposure-year fixed effects, prior PPI growth, and the other weather departure in OLS; country-cluster CR1 SE and two-sided Student t(G−1). Gates: at least 500 complete rows and 30 countries; ≥100 material-exposure rows in ≥20 countries (focal departure ≥1 °C or ≥1 baseline pr SD); full-rank design; positive finite SE; and top country ≤20% of focal exposure sum of squares residualized on all nuisance terms. Failed gate = INCONCLUSIVE. Directional prediction: unusually large weather departure is associated with higher subsequent nominal PPI growth. SUPPORTED iff beta ≥+0.02 and two-sided p≤0.01/{family_size}={p_max:.12g}; REFUTED iff beta ≤−0.02 at the same p cutoff; otherwise PARTIAL when estimable. All {family_size} cells, including failures, remain in one Bonferroni denominator. No post-value tuning.

Annual national weather misses crop zones and seasons. Nominal local-currency farm-gate indices respond to inflation, exchange rates, imports, demand, policy, storage and reporting. FAO may estimate source data upstream. The correlated item/exposure cells are not independent replications; this correction does not adjust wider IESET research selection. This is **descriptive calibration only** with zero causal, policy, position, school or featured credit.

Official documentation: FAOSTAT agricultural producer prices https://data.fao.org/catalog/dataset/47c17894-8ca1-4bd0-ba4d-6078e919e9b1 ; FAO PPI methodology https://files-faostat.fao.org/production/PP/PP_e.pdf ; World Bank CCKP https://climateknowledgeportal.worldbank.org/download-data ; CRU methods https://worldbank.github.io/climateknowledgeportal/docs/collections/cru-x0.5.html . FAO/World Bank source rights and attribution apply.
"""
    files = {ROSTER: roster_text.encode(), PREREG: prereg.encode()}
    for code, (label, cpc, keys) in eligible.items():
        countries = sorted({country for country, _ in keys})
        for exposure in EXPOSURES:
            ident = case_id(code, exposure)
            other = "precipitation" if exposure == "temperature" else "temperature"
            unit = "°C" if exposure == "temperature" else "baseline sample SD"
            steelman = f"hypotheses/steelman/{ident}.md"
            threshold = {
                "family_id": FAMILY, "family_size": family_size,
                "family_alpha": FAMILY_ALPHA, "p_max_two_sided_bonferroni": p_max,
                "expected_beta_sign": "+", "meaningful_beta_min_abs": 0.02,
                "min_complete_rows": 500, "min_complete_countries": 30,
                "min_material_rows": 100, "min_material_countries": 20,
                "min_complete_years_per_country": 5,
                "material_abs_temperature_departure_deg_c": 1.0,
                "material_abs_precipitation_departure_baseline_sd": 1.0,
                "max_abs_ppi_log_growth": 1.0,
                "max_top_country_residualized_exposure_share": 0.20,
                "baseline_years": [1961, 1990], "exposure_years": [START, END],
                "item_code": code, "index_element": INDEX_ELEMENT,
                "annual_month_code": ANNUAL_MONTH, "roster_sha256": roster_hash,
                "source_lock_path": LOCK, "causal_credit": 0,
                "school_score_eligible": False, "school_score_credit": 0,
                "policy_score_eligible": False, "policy_score_credit": 0,
                "featured_eligible": False,
            }
            spec = {
                "hypothesis_id": ident, "version": 1, "status": "pre_registered",
                "topic": "growth", "claim_direction": "+",
                "claim": f"Larger absolute annual country {exposure} departure at year t is associated with higher next-year {label} single-item producer price index log growth after prior PPI growth, the other weather departure, and country/year effects.",
                "methodology_note": f"Value-blind named CPC 01 crop family ({family_size} correlated tests), all eligible items by key coverage; FAO item {code}, CPC {cpc}, annual single-item producer price index 2014–2016=100. No measurements, flags or null masks opened at registration.",
                "evidence_type": "associational",
                "sample": {"countries": countries, "period": [1994, 2023],
                           "temporal_structure": "panel",
                           "exclusion_rules": [
                               "Use only committed item/country/exposure-year roster keys; no interpolation or substitutes.",
                               "Require exact annual single-item PPI at t-1,t,t+1, finite and positive, A/E/X flags at all three years; exclude I/B/M/blank/unknown.",
                               "Require finite tas/pr at t and all 1961–1990 baseline years and positive pr baseline sample SD.",
                               "Exclude absolute prior/future PPI log growth >1.0 and countries with fewer than five complete years.",
                               "No post-value changes to item, years, flags, estimator, gates, sign or family size."]},
                "variables": {
                    "outcome": [{"name": "subsequent_single_item_ppi_log_growth",
                                 "source": "faostat:producer_prices",
                                 "transformation": f"log(item {code} annual PPI at t+1) minus log(PPI at t); 2014–2016=100"}],
                    "treatment": [{"name": f"absolute_{exposure}_departure",
                                   "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                                   "transformation": f"absolute country annual {exposure} departure from 1961–1990 normal, {unit}"}],
                    "controls": [{"name": "prior_single_item_ppi_log_growth",
                                  "source": "faostat:producer_prices",
                                  "transformation": "log(PPI at t) minus log(PPI at t-1)"},
                                 {"name": f"other_{other}_departure",
                                  "source": "world_bank_cckp:cru_ts4_10_tas_pr_annual_global",
                                  "transformation": f"absolute country annual {other} departure"}]},
                "estimator": {"template": "panel_fe", "fixed_effects": ["country", "year"],
                              "clustering": "country",
                              "notes": "Country/exposure-year FE OLS, prior PPI growth and other-weather control; country CR1, two-sided Student t(G-1), full-rank and residual concentration gates."},
                "falsification": {"test": f"{FAMILY}_{code}_{exposure}",
                                  "rule": f"INCONCLUSIVE if source, complete-case (500/30), material-exposure (100/20), five-year-country, full-rank, positive finite SE or 20% top-country residualized exposure gate fails. SUPPORTED iff beta >= +0.02 and p <= 0.01/{family_size}; REFUTED iff beta <= -0.02 at same cutoff; otherwise PARTIAL when estimable. All {family_size} cells remain in denominator.",
                                  "threshold": threshold},
                "prior_confidence": 0.20,
                "disclosure": "Descriptive calibration only. Annual country weather and nominal local-currency farm-gate PPI are confounded and do not identify a causal weather or policy effect. Zero causal, policy, school, position and featured credit.",
                "steelman": steelman,
                "scope": {"period": [1994, 2023], "countries": countries,
                          "outcome_dim": ["inflation"], "policy_family": [],
                          "treatment_tags": [f"faostat_item_{code}", exposure, "climate_weather"]},
                "covers_claims": [], "linked_hypotheses": [], "linked_conditions": [],
            }
            files[f"hypotheses/growth/{ident}.yaml"] = (
                "# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n"
                + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True)).encode()
            files[steelman] = (
                f"# Steelman: {label}, {exposure}, and later producer prices\n\n"
                f"Unusual annual {exposure} departures may disrupt or signal reduced expected supply of {label} and raise later farm-gate prices. "
                "The frozen positive prediction is compared within countries and common years, with prior price growth and the other departure controlled.\n\n"
                "National annual weather may miss growing regions or seasons. Some departures can improve yields; nominal prices move with inflation, exchange rates, trade, demand, storage and policy. "
                "FAO reporting and estimated data also matter. A fitted coefficient remains an association, not a causal crop or price response.\n\n"
                f"This is one of {family_size} correlated cells under a common two-sided 0.01/{family_size} cutoff and strict failure gates. Zero causal, policy, school, position and featured credit.\n"
            ).encode()
    return files, len(eligible), family_size, len(roster_rows), roster_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    files, items, cases, keys, digest = outputs(args.source_root)
    for name, content in files.items():
        path = ROOT / name
        if args.verify:
            if not path.is_file() or path.read_bytes() != content:
                raise RuntimeError(f"exact key-only registration mismatch: {name}")
        else:
            if path.exists():
                raise RuntimeError(f"registration target exists: {name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    print(f"{'Exact key-only replay passed' if args.verify else 'Registered'}: "
          f"{items} named items, {cases} tests, {keys} item-country-years, roster SHA {digest}")


if __name__ == "__main__":
    main()
