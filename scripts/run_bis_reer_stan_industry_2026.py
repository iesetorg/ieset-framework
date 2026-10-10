#!/usr/bin/env python3
"""Frozen BIS REER to OECD STAN manufacturing calibration family.

--prepare reads OECD categorical dimensions and keys, never outcome values,
missingness or statuses. --lock pins the sources in a second Git commit.
Only --run/--verify open selected OECD outcome values after both commits.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "bis_reer_oecd_stan_manufacturing_forward_2026_10_10"
RUNNER = "scripts/run_bis_reer_stan_industry_2026.py"
PREREG = "engine/audits/bis_reer_stan_industry_family_prereg_2026-10-10.md"
SUMMARY = "engine/audits/bis_reer_stan_industry_family_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/bis_reer_stan_industry_family_2026_key_roster.csv"
LOCK = "data/pinned_evidence/bis_reer_stan_industry_family_2026.source_lock.json"
BIS = "data/vintages/bis/WS_EER@2026-07-23T151604Z.parquet"
STAN = "data/vintages/oecd_stan/STAN@DF_STAN_2015_2022@2026-05-02T201942Z.parquet"
BIS_MANIFEST = "data/manifests/fetch_run_2026-07-23T151632Z.yaml"
SOURCE_HASHES = {
    BIS: "57bbce3e22fc428c8cd8ddee8a998d273b5240a816af89e532b81d41ade35170",
    STAN: "aad25afe7f2ab27e00f6dc10cfc049affe40d679e08528503416bf1e9c19d0c7",
    BIS_MANIFEST: "1768f0d7c38c93f1ad4df591b0b1634b3460faa964f6267874b8798b7b8dbb81",
}
ISO2_TO_3 = {
    "AT": "AUT", "AU": "AUS", "BE": "BEL", "CA": "CAN", "CH": "CHE", "CL": "CHL",
    "CO": "COL", "CZ": "CZE", "DE": "DEU", "DK": "DNK", "EE": "EST", "ES": "ESP",
    "FI": "FIN", "FR": "FRA", "GB": "GBR", "GR": "GRC", "HU": "HUN", "IE": "IRL",
    "IS": "ISL", "IT": "ITA", "JP": "JPN", "KR": "KOR", "LT": "LTU", "LU": "LUX",
    "LV": "LVA", "MX": "MEX", "NL": "NLD", "NO": "NOR", "NZ": "NZL", "PL": "POL",
    "PT": "PRT", "SE": "SWE", "SI": "SVN", "SK": "SVK", "TR": "TUR", "US": "USA",
}
SECTORS = tuple([f"C{i}" for i in range(16, 31)] + ["C31_32", "C33"])
MEASURES = {
    "real_value_added": {"code": "B1G", "base": "L", "unit": "XDC", "label": "real value added", "min_n": 20},
    "persons_employed": {"code": "EMP", "base": "_Z", "unit": "PS", "label": "persons employed", "min_n": 20},
}
FAMILY_SIZE = len(SECTORS) * len(MEASURES)
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MIN_BETA = 0.2  # outcome log-percentage points per REER log-percentage point
MIN_X_SPREAD = 3.0
MAX_X_SHARE = 0.45
MIN_DIRECTION_COUNTRIES = 4
CORRECTION = {
    "disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
    "bonferroni_p_max": P_MAX, "school_score_eligible": False,
    "school_score_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False,
}
LIMITATIONS = [
    "A shared country-level REER shock and period makes the sector tests correlated, not independent confirmations.",
    "BIS CPI-adjusted REER is an exchange-rate index, not an enacted policy or evidence of currency misvaluation.",
    "OECD STAN includes estimated industry detail; estimation and observation flags are reported but not used to select signs.",
    "The preserved STAN parquet is a partial 2015-2019 snapshot with no matching fetch manifest, despite a 2015_2022 filename.",
    "Common shocks, commodity prices, industrial mix and reverse anticipation can explain cross-country associations.",
    "The local 34-test correction does not repair selection across the older IESET hypothesis archive.",
    "No causal, policy, school, position or featured credit follows from these descriptive results.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_commit(rel: str) -> str:
    history = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if not history:
        raise RuntimeError(f"missing committed first addition: {rel}")
    return history[-1]


def frozen(rel: str, commit: str) -> None:
    path = ROOT / rel
    if not path.exists() or path.read_bytes() != git("show", f"{commit}:{rel}"):
        raise RuntimeError(f"frozen artifact changed since {commit}: {rel}")
    if git("status", "--porcelain", "--", rel).strip():
        raise RuntimeError(f"uncommitted frozen artifact: {rel}")


def case_id(measure: str, sector: str) -> str:
    return f"bis_reer_stan_{sector.lower()}_{measure}_forward_2026"


def case_rows() -> list[tuple[str, str, dict[str, object]]]:
    return [(measure, sector, cfg) for measure, cfg in MEASURES.items() for sector in SECTORS]


def spec_rel(measure: str, sector: str) -> str:
    return f"hypotheses/growth/{case_id(measure, sector)}.yaml"


def steelman_rel(measure: str, sector: str) -> str:
    return f"hypotheses/steelman/{case_id(measure, sector)}.md"


def run_rel(measure: str, sector: str) -> str:
    return f"engine/runs/{case_id(measure, sector)}"


def verify_sources() -> dict[str, object]:
    for rel, expected in SOURCE_HASHES.items():
        if sha256(ROOT / rel) != expected:
            raise RuntimeError(f"source hash mismatch: {rel}")
    manifest = yaml.safe_load((ROOT / BIS_MANIFEST).read_text())
    found = [entry for entry in manifest["entries"] if entry.get("publisher") == "bis"
             and entry.get("series_id") == "WS_EER" and entry.get("parquet_path") == BIS]
    if len(found) != 1 or found[0]["sha256"] != SOURCE_HASHES[BIS]:
        raise RuntimeError("BIS fetch manifest does not match preserved parquet")
    schema = pq.ParquetFile(ROOT / STAN).schema_arrow
    if any(name not in schema.names for name in ("STRUCTURE_ID", "FREQ", "REF_AREA", "ACTIVITY",
                                                  "MEASURE", "PRICE_BASE", "UNIT_MEASURE",
                                                  "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "EST_METHOD")):
        raise RuntimeError("STAN source schema mismatch")
    return {"bis": {"path": BIS, "sha256": SOURCE_HASHES[BIS], "fetch_manifest": BIS_MANIFEST,
                    "fetch_manifest_sha256": SOURCE_HASHES[BIS_MANIFEST],
                    "source_url": found[0]["source_url"], "methodology_url": found[0]["methodology_url"],
                    "license": found[0]["license"], "fetch_utc": found[0]["fetch_utc"]},
            "stan": {"path": STAN, "sha256": SOURCE_HASHES[STAN],
                     "source_dataflow": "OECD.STI.PIE:DSD_STAN@DF_STAN(1.0)",
                     "source_url": "https://data-explorer.oecd.org/vis?df%5Bag%5D=OECD.STI.PIE&df%5Bid%5D=DSD_STAN%40DF_STAN&df%5Bvs%5D=1.0",
                     "rights_url": "https://www.oecd.org/en/about/terms-conditions.html",
                     "fetch_manifest": None, "custody_note": "Locally preserved partial 2015-2019 parquet; exact fetch manifest absent. Filename says 2015_2022 but no rows follow 2019."}}


def bis_exposure() -> tuple[dict[str, float], set[str]]:
    columns = ["FREQ", "EER_TYPE", "EER_BASKET", "REF_AREA", "period", "value"]
    data = pq.read_table(ROOT / BIS, columns=columns).to_pandas()
    data = data.loc[(data.FREQ == "M") & (data.EER_TYPE == "R") &
                    (data.EER_BASKET == "B") & data.period.str[:4].isin(("2015", "2016"))].copy()
    data["year"] = data.period.str[:4]
    if data.duplicated(["REF_AREA", "period"]).any():
        raise RuntimeError("duplicate BIS monthly series keys")
    counts = data.groupby(["REF_AREA", "year"]).period.nunique().unstack(fill_value=0)
    complete = set(counts.index[(counts["2015"] == 12) & (counts["2016"] == 12)])
    data = data[data.REF_AREA.isin(complete)]
    exposure = {}
    for area, rows in data.groupby("REF_AREA"):
        if area not in ISO2_TO_3:
            continue  # XM is a currency area, not a country; other codes lack STAN match.
        if not np.isfinite(rows.value.to_numpy(dtype=float)).all() or (rows.value <= 0).any():
            continue
        means = rows.groupby("year").value.mean()
        exposure[ISO2_TO_3[area]] = float(100 * math.log(means["2016"] / means["2015"]))
    return exposure, {ISO2_TO_3[a] for a in complete if a in ISO2_TO_3}


def roster_and_labels() -> tuple[dict[str, list[str]], dict[str, str], dict[str, float]]:
    exposure, complete_bis = bis_exposure()
    # Deliberately no OBS_VALUE, OBS_STATUS or EST_METHOD column in this read.
    columns = ["STRUCTURE_ID", "FREQ", "REF_AREA", "ACTIVITY", "Economic activity", "MEASURE",
               "Measure", "PRICE_BASE", "Price base", "UNIT_MEASURE", "Unit of measure", "TIME_PERIOD"]
    data = pq.read_table(ROOT / STAN, columns=columns).to_pandas()
    if set(data.STRUCTURE_ID.unique()) != {"OECD.STI.PIE:DSD_STAN@DF_STAN(1.0)"}:
        raise RuntimeError("unexpected STAN dataflow")
    labels = {}
    for sector in SECTORS:
        names = set(data.loc[data.ACTIVITY == sector, "Economic activity"].dropna())
        if len(names) != 1:
            raise RuntimeError(f"STAN industry label mismatch: {sector}")
        labels[sector] = names.pop()
    out = {}
    for measure, sector, cfg in case_rows():
        selected = data.loc[(data.FREQ == "A") & (data.ACTIVITY == sector) &
                            (data.MEASURE == cfg["code"]) & (data.PRICE_BASE == cfg["base"]) &
                            (data.UNIT_MEASURE == cfg["unit"]) &
                            data.TIME_PERIOD.isin((2017, 2018)) & data.REF_AREA.isin(complete_bis)]
        if selected.duplicated(["REF_AREA", "TIME_PERIOD"]).any():
            raise RuntimeError(f"duplicate STAN outcome key: {measure}/{sector}")
        countries = selected.groupby("REF_AREA").TIME_PERIOD.nunique()
        countries = sorted(set(countries.index[countries == 2]) & set(exposure))
        out[case_id(measure, sector)] = countries
    return out, labels, exposure


def roster_bytes(roster: dict[str, list[str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(("case_id", "country_iso3"))
    for measure, sector, _ in case_rows():
        case = case_id(measure, sector)
        for country in roster[case]:
            writer.writerow((case, country))
    return buf.getvalue().encode()


def verify_roster() -> tuple[dict[str, list[str]], dict[str, str], dict[str, float], str]:
    roster, labels, exposure = roster_and_labels()
    raw = roster_bytes(roster)
    if (ROOT / ROSTER).read_bytes() != raw:
        raise RuntimeError("frozen key-only roster differs from source keys")
    return roster, labels, exposure, hashlib.sha256(raw).hexdigest()


def registration_commit() -> str:
    files = [RUNNER, PREREG, ROSTER]
    files += [spec_rel(m, s) for m, s, _ in case_rows()]
    files += [steelman_rel(m, s) for m, s, _ in case_rows()]
    commits = {first_commit(rel) for rel in files}
    if len(commits) != 1:
        raise RuntimeError("preregistration files lack one first-addition commit")
    commit = commits.pop()
    for rel in files:
        frozen(rel, commit)
    if git("ls-tree", "-r", "--name-only", commit, "--", "engine/runs/").decode().find("bis_reer_stan_") >= 0:
        raise RuntimeError("results existed in registration commit")
    roster, _, _, digest = verify_roster()
    for measure, sector, cfg in case_rows():
        spec = yaml.safe_load((ROOT / spec_rel(measure, sector)).read_text())
        threshold = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] != case_id(measure, sector) or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational" or spec["covers_claims"] != []
                or spec["linked_hypotheses"] != [] or spec["linked_conditions"] != []
                or threshold["family_id"] != FAMILY or threshold["family_size"] != FAMILY_SIZE
                or threshold["roster_sha256"] != digest or
                threshold["expected_key_countries"] != len(roster[case_id(measure, sector)])
                or threshold["min_valid_countries"] != cfg["min_n"]):
            raise RuntimeError(f"registered spec mismatch: {measure}/{sector}")
    return commit


def source_lock_commit() -> tuple[str, dict[str, object]]:
    register = registration_commit()
    commit = first_commit(LOCK)
    if commit == register or not git("merge-base", "--is-ancestor", register, commit) == b"":
        raise RuntimeError("source lock must follow registration")
    frozen(LOCK, commit)
    lock = json.loads((ROOT / LOCK).read_text())
    _, _, _, digest = verify_roster()
    if lock != {"family_id": FAMILY, "registration_commit": register,
                "key_roster": ROSTER, "key_roster_sha256": digest, "sources": verify_sources()}:
        raise RuntimeError("source lock differs from pinned sources")
    if git("ls-tree", "-r", "--name-only", commit, "--", "engine/runs/").decode().find("bis_reer_stan_") >= 0:
        raise RuntimeError("results existed in source-lock commit")
    return commit, lock


def prepare() -> None:
    if (ROOT / ROSTER).exists() or (ROOT / PREREG).exists():
        raise FileExistsError("family registration already exists")
    verify_sources()
    roster, labels, exposure = roster_and_labels()
    raw = roster_bytes(roster)
    digest = hashlib.sha256(raw).hexdigest()
    (ROOT / ROSTER).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ROSTER).write_bytes(raw)
    lines = ["# BIS REER → OECD STAN manufacturing: frozen prospective registration", "",
             "This is a 34-cell descriptive family, registered before any selected STAN outcome value, null mask or observation status was read. Preflight read only STAN schema, categorical labels and country/year keys, BIS treatment values, source hashes and prior hypothesis text. No policy, causal, school, position or featured score credit is available.", "",
             "## Exact sources and rights", "",
             f"- BIS `WS_EER` raw `{BIS}`, SHA-256 `{SOURCE_HASHES[BIS]}`; tracked manifest `{BIS_MANIFEST}`, SHA-256 `{SOURCE_HASHES[BIS_MANIFEST]}`. Official <https://data.bis.org/topics/EER> defines broad real effective exchange rate; an increase is appreciation. <https://data.bis.org/help/legal> permits statistical use with BIS citation and no implied endorsement.",
             f"- OECD STAN raw `{STAN}`, SHA-256 `{SOURCE_HASHES[STAN]}`, dataflow `OECD.STI.PIE:DSD_STAN@DF_STAN(1.0)`. Official <https://www.oecd.org/en/data/datasets/structural-analysis-database.html> defines detailed annual ISIC Rev.4 industry measures, including estimated/flagged detail. <https://www.oecd.org/en/about/terms-conditions.html> permits reuse with citation subject to third-party metadata restrictions. No tracked fetch manifest exists for this partial local parquet; its 2015_2022 filename overstates actual 2015–2019 key coverage. Do not describe it as a complete extract or an independent future-data holdout.",
             "", "## Frozen key-only sample", "",
             f"Roster `{ROSTER}`, SHA-256 `{digest}`. It contains exactly the source-key countries below, not outcome completeness. BIS `FREQ=M,EER_TYPE=R,EER_BASKET=B` requires all 12 months in 2015 and 2016, no duplicate month. The country-level treatment is `X=100*log(mean_REER_2016/mean_REER_2015)` using arithmetic calendar-year means; `XM` euro-area aggregate is excluded. STAN outcome key requires exact annual 2017 and 2018 country/industry/measure rows. No interpolation or alternate time window.",
             "", "| Outcome | ISIC activity | Sector | Key countries | Depreciating countries | REER p90−p10 (log pp) |",
             "| --- | --- | --- | ---: | ---: | ---: |"]
    for measure, sector, cfg in case_rows():
        countries = roster[case_id(measure, sector)]
        xx = np.array([exposure[c] for c in countries])
        lines.append(f"| {cfg['label']} | `{sector}` | {labels[sector]} | {len(countries)} | {sum(xx < 0)} | {np.quantile(xx,.9)-np.quantile(xx,.1):.2f} |")
    lines += ["", "## Locked estimator and verdict", "",
              "Selected STAN columns are `B1G/L/XDC` (value added, chain-linked volume, national currency) and `EMP/_Z/PS` (total employment, persons). These are distinct output and workforce outcomes. Do not use `B1G/D/IX`: D is a **deflator**. The 17 activity codes C16–C30, C31_32 and C33 form a disjoint detailed manufacturing partition; no parent aggregates enter. For each cell, `Y=100*log(STAN_2018/STAN_2017)`. A complete pair requires two finite positive values, and the same frozen country key with a finite positive BIS annual mean. Record STAN `OBS_STATUS` and `EST_METHOD` counts after source lock; keep all numeric published observations regardless of flag and do not select by flag/sign. No outcome winsorisation, imputation or substitute source.", "",
              "Fit one cross-sectional OLS per cell: `Y_c = alpha + beta X_c + error_c`, country equally weighted, HC3 standard error and two-sided Student t with n−2 degrees of freedom. The sample is a single 2015–2018 episode, so no country/year fixed effects or causal design is claimed. Require ≥20 complete countries, ≥4 positive and ≥4 negative REER changes, p90−p10 exposure spread ≥3 log percentage points, centered exposure squared-share maximum ≤0.45, full rank and finite positive HC3 uncertainty. A failed gate is INCONCLUSIVE.", "",
              f"All 34 tests remain in one Bonferroni family at alpha 0.01, two-sided p≤{P_MAX:.12g} per cell even when others fail. SUPPORTED requires beta≤−0.2 outcome log percentage point per one REER log percentage point and the corrected p cutoff; REFUTED requires beta≥+0.2 and the same p cutoff. Otherwise an estimable result is PARTIAL. No post-result changes to sample, sign, threshold or industry roster. The local correction does not account for wider IESET exploration.", "",
              "## Distinctness and limits", "",
              "The visible archive already has `bis_reer_appreciation_industrial_share_panel_1964_2026` (BIS REER against WDI aggregate manufacturing share), as well as REER export growth/variety and tourism-arrival hypotheses. These sector-level real-value-added and person-employment outcomes are narrower, use different source variables and timing, and do not algebraically copy aggregate share. They still share the same REER treatment, period, countries and shocks. Prospective here means this narrow measurement protocol was frozen before selected outcomes were opened, not that source data were unpublished or the broader archive unseen.", "",
              "STAN `P51G/L/XDC` sector investment is conceptually separate but excluded before outcome inspection: only 13–19 paired-country keys per sector and only three depreciation countries in each. STAN `P1` gross output was excluded because it overlaps value added through intermediate consumption. The sparse 2019 year was not selected because this key-only extract has far fewer rows than 2018.", "",
              "Commodity prices, global demand, industrial mix, expected growth and common macro shocks can move REER and each outcome. The REER uses consumer prices and trade weights, not sector prices. STAN volume measures use national currencies within countries; only within-country log changes enter. Interpret results as descriptive cross-country predictions, with zero policy, causal, school, position or featured credit.", ""]
    (ROOT / PREREG).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / PREREG).write_text("\n".join(lines))
    for measure, sector, cfg in case_rows():
        cid = case_id(measure, sector)
        countries = roster[cid]
        threshold = {"family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
                     "p_max_two_sided_bonferroni": P_MAX,
                     "minimum_adverse_beta_logpp_per_reer_logpp": MIN_BETA,
                     "min_valid_countries": cfg["min_n"], "min_appreciation_countries": MIN_DIRECTION_COUNTRIES,
                     "min_depreciation_countries": MIN_DIRECTION_COUNTRIES,
                     "min_exposure_p90_p10_logpp": MIN_X_SPREAD,
                     "max_top_country_exposure_share": MAX_X_SHARE,
                     "expected_key_countries": len(countries), "roster_sha256": digest,
                     "bis_sha256": SOURCE_HASHES[BIS], "stan_sha256": SOURCE_HASHES[STAN],
                     "school_score_eligible": False, "school_score_credit": 0,
                     "policy_score_eligible": False, "policy_score_credit": 0}
        spec = {"hypothesis_id": cid, "version": 1, "status": "pre_registered", "topic": "growth",
                "claim_direction": "-", "claim": f"Across the frozen country sample, larger 2015-to-2016 broad real effective exchange-rate appreciations predict lower 2017-to-2018 {labels[sector]} {cfg['label']} growth.",
                "methodology_note": f"One of 34 source-key-registered descriptive outcomes; exact contract in {PREREG}. STAN outcome values and statuses were unopened before registration and source lock.",
                "evidence_type": "associational",
                "sample": {"countries": countries, "period": [2015, 2018],
                           "temporal_structure": "cross_section_with_justification",
                           "cross_section_justification": "One predeclared REER episode and later industry growth pair; this measures association across countries only.",
                           "exclusion_rules": ["Use only the exact committed country roster and 2017/2018 STAN industry rows.",
                                               "Require 12 monthly BIS broad-real REER values in each of 2015 and 2016.",
                                               "After source lock, retain only finite positive values at both outcome endpoints and both BIS annual means; no imputation, status-based sign selection, winsorisation or replacement." ]},
                "variables": {"treatment": [{"name": "prior_broad_real_eer_appreciation_logpp", "source": "bis:WS_EER",
                                             "transformation": "100*log(mean 2016 monthly broad-real REER / mean 2015 monthly broad-real REER)."}],
                              "outcome": [{"name": f"forward_{sector.lower()}_{measure}_growth_logpp",
                                           "source": "oecd_stan:OECD.STI.PIE,DSD_STAN@DF_STAN,1.0",
                                           "transformation": f"100*log(2018/2017) for ACTIVITY={sector}, MEASURE={cfg['code']}, PRICE_BASE={cfg['base']}, UNIT_MEASURE={cfg['unit']}.",
                                           "notes": f"{labels[sector]}; {cfg['label']}. OECD STAN may include Secretariat estimates."}]},
                "estimator": {"template": "descriptive", "notes": "Cross-country OLS with intercept, HC3 robust SE, two-sided t(n-2); no fitted covariates or alternate periods."},
                "falsification": {"test": FAMILY, "rule": "INCONCLUSIVE if the frozen sample, exposure variation, leverage, rank, or uncertainty gate fails. Otherwise SUPPORTED for beta <= -0.2 at two-sided Bonferroni p <= 0.01/34, REFUTED for beta >= +0.2 at the same cutoff, and PARTIAL for any other estimable result. All 34 cells stay in the family denominator.",
                                  "threshold": threshold},
                "prior_confidence": 0.2,
                "disclosure": "Shared macro exposure, one episode, correlated sectors, estimated STAN detail, partial unmanifested local source and visible related REER hypotheses limit interpretation to descriptive calibration. No policy, causal, school or featured credit.",
                "steelman": steelman_rel(measure, sector),
                "scope": {"period": [2015, 2018], "countries": countries,
                          "outcome_dim": ["industrial_capability"], "policy_family": ["none"], "treatment_tags": []},
                "covers_claims": [], "linked_hypotheses": [], "linked_conditions": []}
        spath = ROOT / spec_rel(measure, sector)
        spath.parent.mkdir(parents=True, exist_ok=True)
        spath.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" +
                         yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        steelman = (f"# Steelman: {labels[sector]} {cfg['label']} after REER appreciation\n\n"
                    f"A currency appreciation can reduce price competitiveness for exporters and import-competing firms, which could later slow {labels[sector]} {cfg['label']} growth. The fixed 2015–2016 exposure and 2017–2018 outcome timing provides a narrow prospective measurement of that prediction.\n\n"
                    "The strongest alternative is that appreciated currencies can lower imported input and capital-goods costs, while aggregate demand, commodity prices, industrial specialisation and anticipated growth jointly affect the REER and industry outcomes. Some sectors sell largely at home. The same countries and REER changes are reused across 34 correlated tests; OECD STAN includes estimated detail, and the partial local parquet lacks a fetch manifest. Negative, positive, null and inconclusive results must remain visible. No result identifies an exchange-rate policy effect.\n")
        path = ROOT / steelman_rel(measure, sector)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(steelman)
    print(f"Prepared {FAMILY_SIZE} specifications; roster SHA-256 {digest}; no outcome values/statuses opened")


def lock_sources() -> None:
    if (ROOT / LOCK).exists():
        raise FileExistsError("source lock already exists")
    register = registration_commit()
    _, _, _, digest = verify_roster()
    lock = {"family_id": FAMILY, "registration_commit": register,
            "key_roster": ROSTER, "key_roster_sha256": digest, "sources": verify_sources()}
    (ROOT / LOCK).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print(f"Wrote narrow source lock after registration {register}; commit it separately before --run")


def load_outcome_values() -> dict[tuple[str, str], pd.DataFrame]:
    # This function must only be reached after the committed source-lock check.
    columns = ["FREQ", "REF_AREA", "ACTIVITY", "MEASURE", "PRICE_BASE", "UNIT_MEASURE",
               "TIME_PERIOD", "OBS_VALUE", "OBS_STATUS", "EST_METHOD"]
    data = pq.read_table(ROOT / STAN, columns=columns).to_pandas()
    data = data[data.TIME_PERIOD.isin((2017, 2018)) & data.ACTIVITY.isin(SECTORS)]
    out = {}
    for measure, sector, cfg in case_rows():
        rows = data[(data.FREQ == "A") & (data.ACTIVITY == sector) &
                    (data.MEASURE == cfg["code"]) & (data.PRICE_BASE == cfg["base"]) &
                    (data.UNIT_MEASURE == cfg["unit"])]
        if rows.duplicated(["REF_AREA", "TIME_PERIOD"]).any():
            raise RuntimeError(f"duplicate selected OECD outcome values: {measure}/{sector}")
        out[(measure, sector)] = rows
    return out


def evaluate(measure: str, sector: str, countries: list[str], exposure: dict[str, float],
             values: pd.DataFrame) -> dict[str, object]:
    pairs = []
    statuses, methods = Counter(), Counter()
    missing, nonpositive = 0, 0
    for country in countries:
        rows = values[values.REF_AREA == country].set_index("TIME_PERIOD")
        if set(rows.index) != {2017, 2018}:
            raise RuntimeError("registered outcome key disappeared")
        numbers = rows.loc[[2017, 2018], "OBS_VALUE"].to_numpy(dtype=float)
        if not np.isfinite(numbers).all():
            missing += 1
            continue
        if (numbers <= 0).any():
            nonpositive += 1
            continue
        for item in rows.loc[[2017, 2018], "OBS_STATUS"]:
            statuses[str(item) if item is not None else "<null>"] += 1
        for item in rows.loc[[2017, 2018], "EST_METHOD"]:
            methods[str(item) if item is not None else "<null>"] += 1
        pairs.append((country, exposure[country], float(100 * math.log(numbers[1] / numbers[0]))))
    x = np.array([item[1] for item in pairs], dtype=float)
    y = np.array([item[2] for item in pairs], dtype=float)
    n = len(pairs)
    span = float(np.quantile(x, .9) - np.quantile(x, .1)) if n else None
    centered = x - x.mean() if n else np.array([])
    share = float(np.max(centered ** 2) / np.sum(centered ** 2)) if n and np.sum(centered ** 2) > 0 else None
    gate = {"key_countries": len(countries), "complete_countries": n, "missing_numeric_pairs": missing,
            "nonpositive_pairs": nonpositive, "appreciation_countries": int(sum(x > 0)),
            "depreciation_countries": int(sum(x < 0)), "exposure_p90_p10_logpp": span,
            "max_top_country_centered_exposure_share": share,
            "selected_outcome_status_counts": dict(sorted(statuses.items())),
            "selected_estimation_method_counts": dict(sorted(methods.items()))}
    failed = []
    if n < int(MEASURES[measure]["min_n"]): failed.append("min_complete_countries")
    if gate["appreciation_countries"] < MIN_DIRECTION_COUNTRIES: failed.append("min_appreciation_countries")
    if gate["depreciation_countries"] < MIN_DIRECTION_COUNTRIES: failed.append("min_depreciation_countries")
    if span is None or span < MIN_X_SPREAD: failed.append("min_exposure_spread")
    if share is None or share > MAX_X_SHARE: failed.append("max_exposure_concentration")
    primary = None
    if not failed:
        design = sm.add_constant(x)
        if np.linalg.matrix_rank(design) != 2:
            failed.append("full_rank")
        else:
            fit = sm.OLS(y, design).fit(cov_type="HC3", use_t=True)
            beta, se = float(fit.params[1]), float(fit.bse[1])
            if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
                failed.append("finite_positive_hc3_uncertainty")
            else:
                p = float(2 * student_t.sf(abs(beta / se), n - 2))
                crit = float(student_t.ppf(.975, n - 2))
                if not math.isfinite(p):
                    failed.append("finite_two_sided_p")
                else:
                    primary = {"beta_logpp_per_reer_logpp": beta, "hc3_se": se,
                               "p_two_sided": p, "ci95": [beta - crit * se, beta + crit * se],
                               "n_countries": n, "df": n - 2,
                               "method": "cross-country OLS intercept + REER exposure, HC3, Student t(n-2)"}
    verdict = "INCONCLUSIVE" if failed else ("SUPPORTED" if beta <= -MIN_BETA and p <= P_MAX else
                                              "REFUTED" if beta >= MIN_BETA and p <= P_MAX else "PARTIAL")
    return {"hypothesis_id": case_id(measure, sector), "family_id": FAMILY, "verdict": verdict,
            "failed_gates": failed, "gate": gate, "primary": primary,
            "correction": CORRECTION, "limitations": LIMITATIONS}


def results() -> tuple[dict[str, dict[str, object]], str, str, str]:
    lock_commit, lock = source_lock_commit()
    registration = lock["registration_commit"]
    roster, labels, exposure, _ = verify_roster()
    selected = load_outcome_values()
    outcomes = {}
    for measure, sector, _ in case_rows():
        cid = case_id(measure, sector)
        outcomes[cid] = evaluate(measure, sector, roster[cid], exposure, selected[(measure, sector)])
    return outcomes, registration, lock_commit, lock["key_roster_sha256"]


def summary_text(outcomes: dict[str, dict[str, object]], registration: str, lock_commit: str) -> str:
    counts = Counter(r["verdict"] for r in outcomes.values())
    lines = ["# BIS REER → OECD STAN manufacturing: 34-cell result audit", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`. Selected STAN outcome values/statuses were first opened after both commits. The 34 disjoint-sector × two distinct-measure tests share the same country-level treatment and are correlated.", "",
             f"Family alpha {FAMILY_ALPHA}; Bonferroni two-sided per-test p≤{P_MAX:.12g}; magnitude |beta|≥{MIN_BETA}. Verdict counts: " + ", ".join(f"{k}={counts[k]}" for k in ("SUPPORTED", "REFUTED", "PARTIAL", "INCONCLUSIVE")) + ".", "",
             "| Industry | Outcome | Complete/key countries | Beta | Two-sided p | Verdict | Failed gates |",
             "| --- | --- | ---: | ---: | ---: | --- | --- |"]
    for measure, sector, cfg in case_rows():
        r = outcomes[case_id(measure, sector)]
        p = r["primary"]
        beta = f"{p['beta_logpp_per_reer_logpp']:+.4g}" if p else "not estimated"
        pv = f"{p['p_two_sided']:.4g}" if p else "not estimated"
        lines.append(f"| `{sector}` | {cfg['label']} | {r['gate']['complete_countries']}/{r['gate']['key_countries']} | {beta} | {pv} | **{r['verdict']}** | {', '.join(r['failed_gates']) or 'none'} |")
    lines += ["", "Beta is 2017–2018 outcome log-percentage-point growth per one 2015–2016 REER log-percentage-point appreciation. All published numeric STAN observations are kept irrespective of status or Secretariat estimation method; counts are in each diagnostic. Negative, positive, partial and inconclusive results stay visible.", "",
              "The STAN raw parquet is a partial local 2015–2019 extract with no tracked fetch manifest. This limits source custody and independent replay; the ignored parquet must be present at the exact hash. The 34-cell Bonferroni correction is local to this batch and does not repair archive-wide search or overlap with earlier aggregate manufacturing-share REER hypotheses. Descriptive calibration only; zero policy, causal, school, position or featured credit.", ""]
    return "\n".join(lines)


def artifact_payload(measure: str, sector: str, result: dict[str, object], register: str,
                     lock_commit: str, roster_sha: str, stamp: str) -> dict[str, object]:
    cid = case_id(measure, sector)
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": cid, "path": spec_rel(measure, sector), "topic": "growth"},
              "preregistration": {"spec_commit": register, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": FAMILY_SIZE,
                                  "key_roster": ROSTER, "key_roster_sha256": roster_sha,
                                  "steelman": steelman_rel(measure, sector)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(measure, sector),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                          "reason": ", ".join(result["failed_gates"]) or "frozen estimable test"},
              "data": {"inputs": {"bis": SOURCE_HASHES[BIS], "stan": SOURCE_HASHES[STAN]},
                       "sample": result["gate"]},
              "results": {"primary": result["primary"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {**result, "runner": RUNNER, "run_utc": stamp,
                   "preregistration_commit": register, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "descriptive",
                   "p_max_two_sided_bonferroni": P_MAX,
                   "data_status": {"variables_missing": [], "input_vintages": [BIS, STAN]}}
    manifest = {"hypothesis_id": cid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": register, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": result["verdict"],
                "vintages": [BIS, STAN], "derived_panel": result["gate"],
                "correction": CORRECTION}
    card = (f"# Result card: {cid}\n\nVerdict: **{result['verdict']}**. "
            f"Preregistration `{register}`; source lock `{lock_commit}`.\n\n"
            f"Frozen 2015–2016 BIS broad-real REER change versus 2017–2018 `{sector}` {MEASURES[measure]['label']} growth. "
            f"{result['gate']['complete_countries']}/{result['gate']['key_countries']} complete/key countries. "
            f"Failed gates: {', '.join(result['failed_gates']) or 'none'}.\n")
    if result["primary"]:
        p = result["primary"]
        card += (f"\nBeta={p['beta_logpp_per_reer_logpp']:+.6g}, HC3 SE={p['hc3_se']:.6g}, "
                 f"two-sided p={p['p_two_sided']:.6g}, 95% CI={p['ci95']}.\n")
    card += ("\nThis is one of 34 correlated descriptive tests under Bonferroni family alpha 0.01. "
             "STAN source is a partial locally preserved parquet without a fetch manifest. "
             "No policy, causal, school, position or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper,
            "chart": {"hypothesis_id": cid, "family_id": FAMILY,
                      "verdict": result["verdict"], "primary": result["primary"]}}


def write_results() -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_rel(m, s)).exists() for m, s, _ in case_rows()):
        raise FileExistsError("one or more result artifacts already exist")
    outcomes, register, lock_commit, roster_sha = results()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for measure, sector, _ in case_rows():
        cid = case_id(measure, sector)
        payload = artifact_payload(measure, sector, outcomes[cid], register, lock_commit, roster_sha, stamp)
        folder = ROOT / run_rel(measure, sector)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(measure, sector)).read_bytes())
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    (ROOT / SUMMARY).write_text(summary_text(outcomes, register, lock_commit))
    print(Counter(r["verdict"] for r in outcomes.values()))


def verify_results() -> None:
    outcomes, register, lock_commit, roster_sha = results()
    for measure, sector, _ in case_rows():
        cid = case_id(measure, sector)
        folder = ROOT / run_rel(measure, sector)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(measure, sector, outcomes[cid], register, lock_commit,
                                   roster_sha, saved["run_utc"])
        if saved != payload["diagnostics"] or yaml.safe_load((folder / "evidence_packet.yaml").read_text()) != payload["packet"]:
            raise AssertionError(f"evidence replay differs: {cid}")
        if yaml.safe_load((folder / "manifest.yaml").read_text()) != payload["manifest"]:
            raise AssertionError(f"manifest replay differs: {cid}")
        if json.loads((folder / "chart_data.json").read_text()) != payload["chart"]:
            raise AssertionError(f"chart replay differs: {cid}")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(measure, sector)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"text artifact replay differs: {cid}")
    if (ROOT / SUMMARY).read_text() != summary_text(outcomes, register, lock_commit):
        raise AssertionError("family summary differs from exact replay")
    print("All 34 family artifacts replay exactly against pinned sources and frozen gates")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true", help="write key-only preregistration artifacts")
    group.add_argument("--lock", action="store_true", help="write source lock after committed registration")
    group.add_argument("--run", action="store_true", help="read outcome values after committed source lock")
    group.add_argument("--verify", action="store_true", help="replay committed results")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.lock: lock_sources()
    elif args.run: write_results()
    else: verify_results()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
