#!/usr/bin/env python3
"""Frozen WDI to Eurostat foreign-citizenship immigration calibration family.

--prepare reads Eurostat categorical keys only, never selected outcome values or
null masks. --lock commits source custody separately. Only --run and --verify
open outcome values, after both registration and source-lock commits.
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
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import pycountry
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_growth_eurostat_citizenship_immigration_forward_2026_10_10"
RUNNER = "scripts/run_wdi_eurostat_citizenship_migration_2026.py"
PREREG = "engine/audits/wdi_eurostat_citizenship_migration_prereg_2026-10-10.md"
SUMMARY = "engine/audits/wdi_eurostat_citizenship_migration_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_eurostat_citizenship_migration_2026_key_roster.csv"
LOCK = "data/pinned_evidence/wdi_eurostat_citizenship_migration_2026.source_lock.json"
WDI = "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet"
MIGR = "data/vintages/eurostat/migr_imm1ctz@2026-05-05T205902Z.parquet"
WDI_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
MIGR_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
SOURCE_HASHES = {
    WDI: "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
    MIGR: "b0b178278dd7d1ef68d4a03188e496b580d3e30b61f9fa21c7db13ed547bfeb1",
    WDI_MANIFEST: "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    MIGR_MANIFEST: "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
}
CITIZENSHIPS = tuple("AL AR BD BR CN CO DE DZ ES FR UK GH IN IT MA MD MX NG NL PK PH PL PT RO RU TR UA US VE VN".split())
FAMILY_SIZE = len(CITIZENSHIPS)
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
MIN_BETA = 0.5  # response log percentage points per one prior GDP log percentage point
MIN_N = 20
MIN_MATERIAL = 15  # at least 50 immigrants in both outcome years
MATERIAL_COUNT = 50
MIN_X_SPREAD = 3.0
MAX_X_SHARE = 0.35
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Eurostat citizenship denotes legal nationality, not country of previous residence, birthplace, or migration origin.",
    "The 30 citizenship streams share destinations, exposure and time, so their tests are correlated.",
    "Administrative registration, national collection practices, small flows, border regimes and origin-specific events affect immigration counts.",
    "Prior destination GDP growth is neither a policy intervention nor exogenous; no causal migration effect is identified.",
    "A single 2013–2019 episode and 30-test local correction do not repair wider archive selection.",
    "No policy, causal, school, position or featured credit follows from these descriptive results.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
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


def case_id(citizen: str) -> str:
    return f"wdi_growth_eurostat_immigration_citizenship_{citizen.lower()}_forward_2026"


def spec_rel(citizen: str) -> str:
    return f"hypotheses/growth/{case_id(citizen)}.yaml"


def steelman_rel(citizen: str) -> str:
    return f"hypotheses/steelman/{case_id(citizen)}.md"


def run_rel(citizen: str) -> str:
    return f"engine/runs/{case_id(citizen)}"


def verify_sources() -> dict[str, object]:
    for rel, expected in SOURCE_HASHES.items():
        if sha256(ROOT / rel) != expected:
            raise RuntimeError(f"source hash mismatch: {rel}")
    sources = {}
    for label, path, manifest, publisher, series in (
        ("wdi", WDI, WDI_MANIFEST, "world_bank_wdi", "NY.GDP.PCAP.KD"),
        ("eurostat", MIGR, MIGR_MANIFEST, "eurostat", "migr_imm1ctz"),
    ):
        rows = yaml.safe_load((ROOT / manifest).read_text())["entries"]
        matching = [e for e in rows if e.get("publisher") == publisher and
                    e.get("series_id") == series and e.get("parquet_path") == path]
        if len(matching) != 1 or matching[0]["sha256"] != SOURCE_HASHES[path]:
            raise RuntimeError(f"fetch manifest does not match {path}")
        e = matching[0]
        sources[label] = {"path": path, "sha256": SOURCE_HASHES[path],
                          "fetch_manifest": manifest, "fetch_manifest_sha256": SOURCE_HASHES[manifest],
                          "source_url": e["source_url"], "methodology_url": e["methodology_url"],
                          "license": e["license"], "fetch_utc": e["fetch_utc"]}
    if set(pq.ParquetFile(ROOT / MIGR).schema_arrow.names) != {
            "freq", "citizen", "agedef", "age", "unit", "sex", "geo_code", "period", "value"}:
        raise RuntimeError("unexpected Eurostat schema")
    if not {"country_iso3", "year", "value"} <= set(pq.ParquetFile(ROOT / WDI).schema_arrow.names):
        raise RuntimeError("unexpected WDI schema")
    return sources


def destination_iso3(code: str) -> str | None:
    if code in {"EL": "GRC", "UK": "GBR"}:
        return {"EL": "GRC", "UK": "GBR"}[code]
    if len(code) != 2:
        return None
    item = pycountry.countries.get(alpha_2=code)
    return item.alpha_3 if item is not None else None


def treatment() -> dict[str, float]:
    data = pq.read_table(ROOT / WDI, columns=["country_iso3", "indicator_id", "year", "value"]).to_pandas()
    data = data[(data.indicator_id == "NY.GDP.PCAP.KD") & data.year.isin((2013, 2016)) &
                data.country_iso3.str.fullmatch("[A-Z]{3}")].copy()
    if data.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI country-year treatment keys")
    out = {}
    for country, rows in data.groupby("country_iso3"):
        if set(rows.year) != {2013, 2016}:
            continue
        points = rows.set_index("year").value
        if not np.isfinite(points.to_numpy(dtype=float)).all() or (points <= 0).any():
            continue
        out[country] = float(100 * math.log(points[2016] / points[2013]))
    return out


def selected_keys() -> pd.DataFrame:
    # No outcome value or null-mask column is accessed in registration or lock.
    predicate = ((ds.field("freq") == "A") & (ds.field("unit") == "NR") &
                 (ds.field("sex") == "T") & (ds.field("age") == "TOTAL") &
                 (ds.field("agedef") == "COMPLET") &
                 ds.field("citizen").isin(CITIZENSHIPS) &
                 ds.field("period").isin(("2017", "2019")))
    return ds.dataset(ROOT / MIGR).to_table(columns=["geo_code", "citizen", "period"], filter=predicate).to_pandas()


def roster_and_exposure() -> tuple[dict[str, list[tuple[str, str]]], dict[str, float]]:
    exposure = treatment()
    keys = selected_keys()
    if keys.duplicated(["geo_code", "citizen", "period"]).any():
        raise RuntimeError("duplicate selected Eurostat dimension keys")
    keys["country_iso3"] = keys.geo_code.map(destination_iso3)
    keys = keys[keys.country_iso3.isin(exposure)]
    keys = keys[keys.citizen != keys.geo_code]  # foreign citizenship, not national citizens
    out = {}
    for citizen in CITIZENSHIPS:
        subset = keys[keys.citizen == citizen]
        paired = subset.groupby(["geo_code", "country_iso3"]).period.nunique()
        out[case_id(citizen)] = sorted([(geo, iso) for geo, iso in paired.index[paired == 2]])
    return out, exposure


def roster_bytes(roster: dict[str, list[tuple[str, str]]]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(("case_id", "destination_geo", "destination_iso3"))
    for citizen in CITIZENSHIPS:
        for geo, iso in roster[case_id(citizen)]:
            writer.writerow((case_id(citizen), geo, iso))
    return buf.getvalue().encode()


def verify_roster() -> tuple[dict[str, list[tuple[str, str]]], dict[str, float], str]:
    roster, exposure = roster_and_exposure()
    raw = roster_bytes(roster)
    if (ROOT / ROSTER).read_bytes() != raw:
        raise RuntimeError("frozen key-only roster differs from source keys")
    return roster, exposure, hashlib.sha256(raw).hexdigest()


def registration_commit() -> str:
    files = [RUNNER, PREREG, ROSTER]
    files += [spec_rel(c) for c in CITIZENSHIPS]
    files += [steelman_rel(c) for c in CITIZENSHIPS]
    commits = {first_commit(rel) for rel in files}
    if len(commits) != 1:
        raise RuntimeError("registration files do not share one first-addition commit")
    commit = commits.pop()
    for rel in files:
        frozen(rel, commit)
    if any(case_id(c) in git("ls-tree", "-r", "--name-only", commit, "--", "engine/runs/").decode()
           for c in CITIZENSHIPS):
        raise RuntimeError("results existed in registration commit")
    roster, _, digest = verify_roster()
    for c in CITIZENSHIPS:
        spec = yaml.safe_load((ROOT / spec_rel(c)).read_text())
        gate = spec["falsification"]["threshold"]
        if (spec["hypothesis_id"] != case_id(c) or spec["status"] != "pre_registered" or
                spec["evidence_type"] != "associational" or spec["covers_claims"] != [] or
                spec["linked_hypotheses"] != [] or spec["linked_conditions"] != [] or
                gate["family_id"] != FAMILY or gate["family_size"] != FAMILY_SIZE or
                gate["roster_sha256"] != digest or
                gate["expected_key_destinations"] != len(roster[case_id(c)])):
            raise RuntimeError(f"registered specification mismatch: {c}")
    return commit


def source_lock_commit() -> tuple[str, dict[str, object]]:
    registration = registration_commit()
    commit = first_commit(LOCK)
    if commit == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, commit],
                                                 cwd=ROOT).returncode != 0:
        raise RuntimeError("source lock must follow committed registration")
    frozen(LOCK, commit)
    _, _, digest = verify_roster()
    expected = {"family_id": FAMILY, "registration_commit": registration,
                "key_roster": ROSTER, "key_roster_sha256": digest, "sources": verify_sources()}
    lock = json.loads((ROOT / LOCK).read_text())
    if lock != expected:
        raise RuntimeError("source lock differs from pinned source manifest")
    if any(case_id(c) in git("ls-tree", "-r", "--name-only", commit, "--", "engine/runs/").decode()
           for c in CITIZENSHIPS):
        raise RuntimeError("results existed in source-lock commit")
    return commit, lock


def prepare() -> None:
    if (ROOT / ROSTER).exists() or (ROOT / PREREG).exists():
        raise FileExistsError("family registration already exists")
    verify_sources()
    roster, exposure = roster_and_exposure()
    raw = roster_bytes(roster)
    digest = hashlib.sha256(raw).hexdigest()
    (ROOT / ROSTER).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / ROSTER).write_bytes(raw)
    lines = ["# WDI prior growth → Eurostat foreign-citizenship immigration: frozen prospective registration", "",
             "This is a 30-cell descriptive family registered before reading selected Eurostat outcome values or null masks. Preflight inspected only categorical Eurostat keys and WDI treatment values. The preserved datasets predate this registration; prospective refers only to this frozen analysis protocol. Zero policy, causal, school, position or featured credit.", "",
             "## Source custody and definitions", "",
             f"- WDI `NY.GDP.PCAP.KD` raw `{WDI}`, SHA-256 `{SOURCE_HASHES[WDI]}`; tracked fetch manifest `{WDI_MANIFEST}`, SHA-256 `{SOURCE_HASHES[WDI_MANIFEST]}`; official <https://databank.worldbank.org/metadataglossary/sustainable-development-goals-(sdgs)/series/NY.GDP.PCAP.KD>; CC BY 4.0. GDP per capita is in constant 2015 US dollars.",
             f"- Eurostat `migr_imm1ctz` raw `{MIGR}`, SHA-256 `{SOURCE_HASHES[MIGR]}`; tracked fetch manifest `{MIGR_MANIFEST}`, SHA-256 `{SOURCE_HASHES[MIGR_MANIFEST]}`; official <https://ec.europa.eu/eurostat/databrowser/view/migr_imm1ctz>, <https://ec.europa.eu/eurostat/web/migration-asylum/international-migration-citizenship/methodology>, <https://ec.europa.eu/eurostat/cache/metadata/en/migr_immi_esms.htm>; dataset manifest `cc_by_4_0`, Eurostat reuse notice <https://ec.europa.eu/eurostat/help/copyright-notice>. Immigration requires establishing usual residence for at least 12 months, having previously resided abroad. `citizen` is legal citizenship, **not** prior residence, birthplace or departure country.", "",
             "## Frozen dimensions and sample", "",
             f"Fixed citizenship list: {', '.join(CITIZENSHIPS)}. Retain annual `freq=A`, count `unit=NR`, total sex `sex=T`, total age `age=TOTAL`, age definition `agedef=COMPLET`, years 2017 and 2019. Exclude national citizenship (`citizen=geo_code`); `UK` maps to GBR for destination WDI; Eurostat EL maps to GRC. Retain sovereign two-letter destinations with WDI positive finite 2013 and 2016 treatment and both Eurostat year keys. No outcome-value completeness screening in the roster `{ROSTER}`, SHA-256 `{digest}`. WDI exposure `X=100*log(GDPpc_2016/GDPpc_2013)`. Do not use source alternatives or other windows.", "",
             "| Citizenship | Paired destination keys | WDI exposure p90−p10 log pp | Max centered X share |",
             "| --- | ---: | ---: | ---: |"]
    for c in CITIZENSHIPS:
        pairs = roster[case_id(c)]
        x = np.array([exposure[iso] for _, iso in pairs])
        span = float(np.quantile(x, .9)-np.quantile(x, .1)) if len(x) else float("nan")
        dev = (x-x.mean())**2 if len(x) else np.array([])
        share = float(max(dev)/sum(dev)) if sum(dev) > 0 else float("nan")
        lines.append(f"| `{c}` | {len(pairs)} | {span:.2f} | {share:.3f} |")
    lines += ["", "## Frozen outcome, estimator and verdict", "",
              "For each foreign citizenship, `Y=100*[log1p(immigrant_count_2019)-log1p(immigrant_count_2017)]` in a destination. A complete pair requires two finite **nonnegative** numeric counts; zero is retained via log1p. Report zero, sub-50 and sub-100 endpoint flows and missing/invalid pairs. No imputation, winsorisation, alternate source or post-value sample choice. The raw parquet retains no Eurostat quality flags, so no flag-based filter or quality claim is possible.", "",
              f"Fit one equal-destination cross-sectional OLS with intercept and HC3 standard error. Two-sided Student t uses n−2 degrees of freedom. Require ≥{MIN_N} complete destinations and ≥{MIN_MATERIAL} destinations with counts ≥{MATERIAL_COUNT} in **both** years, exposure p90−p10 ≥{MIN_X_SPREAD} log percentage points, maximum centered exposure squared share ≤{MAX_X_SHARE}, full rank and finite positive HC3 uncertainty. A failed gate makes the cell INCONCLUSIVE and still counts in the family denominator. The material-flow gate is frozen before counts are opened and does not drop small/zero observations from estimation.", "",
              f"One 30-test Bonferroni correction uses family alpha {FAMILY_ALPHA}, two-sided p≤{P_MAX:.12g} in every cell, including inconclusive cells. SUPPORTED requires beta≥+{MIN_BETA} outcome log pp per one prior GDP log pp and corrected p; REFUTED requires beta≤−{MIN_BETA} and corrected p; every other estimable result is PARTIAL. Do not reinterpret a null or gate failure as support. The local correction does not cover wider archive exploration.", "",
              "## Interpretation and distinctness", "",
              "The 30 nationality cells are disjoint foreign-citizenship counts, not algebraic copies of the same total. They share country-level growth exposure and period, so they are correlated. This differs from the existing employment/activity-by-age/sex/citizenship LFS family and the weather-to-producer-price family. No citizenship group is treated as an origin-country departure flow. Destination policy, register design, origin crises, networks and common shocks can drive counts; prior GDP growth is an observational proxy for destination opportunity, not a policy intervention. All verdicts remain descriptive calibration only.", ""]
    (ROOT / PREREG).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / PREREG).write_text("\n".join(lines))
    for c in CITIZENSHIPS:
        cid = case_id(c)
        pairs = roster[cid]
        countries = sorted({iso for _, iso in pairs})
        gate = {"family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
                "p_max_two_sided_bonferroni": P_MAX, "minimum_positive_beta": MIN_BETA,
                "min_valid_destinations": MIN_N, "min_material_destinations": MIN_MATERIAL,
                "material_flow_count_each_year": MATERIAL_COUNT,
                "min_exposure_p90_p10_logpp": MIN_X_SPREAD,
                "max_top_destination_exposure_share": MAX_X_SHARE,
                "expected_key_destinations": len(pairs), "roster_sha256": digest,
                "wdi_sha256": SOURCE_HASHES[WDI], "eurostat_sha256": SOURCE_HASHES[MIGR],
                "school_score_eligible": False, "school_score_credit": 0,
                "policy_score_eligible": False, "policy_score_credit": 0}
        spec = {"hypothesis_id": cid, "version": 1, "status": "pre_registered", "topic": "growth",
                "claim_direction": "+",
                "claim": f"Across frozen European destinations, larger prior 2013–2016 real GDP per capita growth predicts greater 2017–2019 immigration-count growth among people with {c} citizenship.",
                "methodology_note": f"One of 30 predeclared citizenship streams; exact contract in {PREREG}. Eurostat outcome values and null masks unopened before registration and source lock.",
                "evidence_type": "associational",
                "sample": {"countries": countries, "period": [2013, 2019],
                           "temporal_structure": "cross_section_with_justification",
                           "cross_section_justification": "One preregistered prior GDP growth episode and subsequent two-point immigration-flow change, across destinations only.",
                           "exclusion_rules": ["Only committed destination/citizenship key roster and fixed annual Eurostat dimensions.",
                                               "Exclude same-country citizenship; require finite positive WDI endpoints and finite nonnegative Eurostat endpoints.",
                                               "Retain low and zero counts in log1p; no imputation, winsorisation, value-based replacement or alternate window."]},
                "variables": {"treatment": [{"name": "prior_destination_real_gdp_per_capita_growth_logpp",
                                              "source": "world_bank_wdi:NY.GDP.PCAP.KD",
                                              "transformation": "100*log(constant-2015-USD GDP per capita 2016 / 2013)."}],
                              "outcome": [{"name": f"immigration_count_change_citizenship_{c.lower()}_logpp",
                                           "source": "eurostat:migr_imm1ctz",
                                           "transformation": f"100*(log1p(2019 immigrant count)-log1p(2017 immigrant count)); citizen={c}, freq=A, unit=NR, sex=T, age=TOTAL, agedef=COMPLET.",
                                           "notes": "Citizenship is legal nationality, not prior residence, origin or birthplace. Count includes zero via log1p."}]},
                "estimator": {"template": "descriptive", "notes": "Cross-destination OLS with intercept, HC3 robust SE, two-sided t(n-2); no adjusted covariates or substitute periods."},
                "falsification": {"test": FAMILY,
                                  "rule": f"INCONCLUSIVE on frozen sample, material-flow, exposure, rank or uncertainty gate failure. Otherwise SUPPORTED for beta >= {MIN_BETA} and Bonferroni two-sided p <= 0.01/30; REFUTED for beta <= -{MIN_BETA} at that p; otherwise PARTIAL. All 30 cells remain in denominator.",
                                  "threshold": gate},
                "prior_confidence": 0.2,
                "disclosure": "Observational destination growth proxy; citizenship does not denote prior residence. Small flows, heterogeneous reporting, shared destinations and historical shocks limit inference. No policy, causal, school or featured credit.",
                "steelman": steelman_rel(c),
                "scope": {"period": [2013, 2019], "countries": countries,
                          "outcome_dim": ["demographics_migration"], "policy_family": ["none"], "treatment_tags": []},
                "covers_claims": [], "linked_hypotheses": [], "linked_conditions": []}
        path = ROOT / spec_rel(c)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" +
                        yaml.safe_dump(spec, sort_keys=False, allow_unicode=True))
        steel = (f"# Steelman: prior destination growth and {c}-citizenship immigration\n\n"
                 "Rising real income per person may signal better destination opportunity, and established migrant networks may transmit that signal before subsequent moves. The fixed prior growth and later count-change windows make the descriptive prediction testable.\n\n"
                 "The competing explanation is destination policy, registration practice, family reunification, origin-specific events, migration networks and changing legal status. People with a given citizenship can move from any prior residence; citizenship is not departure country. Small and zero flows can yield unstable percentage changes, so the frozen material-flow gate and diagnostics must be enforced. The 30 streams reuse destination growth and are correlated. No result identifies a GDP-growth or migration-policy effect.\n")
        path = ROOT / steelman_rel(c)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(steel)
    print(f"Prepared {FAMILY_SIZE} specifications and key roster SHA-256 {digest}; no Eurostat values/null masks opened")


def lock_sources() -> None:
    if (ROOT / LOCK).exists():
        raise FileExistsError("source lock already exists")
    registration = registration_commit()
    _, _, digest = verify_roster()
    lock = {"family_id": FAMILY, "registration_commit": registration,
            "key_roster": ROSTER, "key_roster_sha256": digest, "sources": verify_sources()}
    (ROOT / LOCK).write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
    print(f"Wrote source lock after registration {registration}; commit separately before --run")


def selected_outcomes() -> pd.DataFrame:
    predicate = ((ds.field("freq") == "A") & (ds.field("unit") == "NR") &
                 (ds.field("sex") == "T") & (ds.field("age") == "TOTAL") &
                 (ds.field("agedef") == "COMPLET") &
                 ds.field("citizen").isin(CITIZENSHIPS) &
                 ds.field("period").isin(("2017", "2019")))
    data = ds.dataset(ROOT / MIGR).to_table(
        columns=["geo_code", "citizen", "period", "value"], filter=predicate).to_pandas()
    if data.duplicated(["geo_code", "citizen", "period"]).any():
        raise RuntimeError("duplicate selected outcome values")
    return data


def evaluate(citizen: str, pairs: list[tuple[str, str]], exposure: dict[str, float],
             data: pd.DataFrame) -> dict[str, object]:
    subset = data[data.citizen == citizen].set_index(["geo_code", "period"])
    sample = []
    missing = invalid = zeros_2017 = zeros_2019 = 0
    low50_2017 = low50_2019 = low100_2017 = low100_2019 = material = 0
    for geo, iso in pairs:
        a, b = subset.loc[(geo, "2017"), "value"], subset.loc[(geo, "2019"), "value"]
        if not math.isfinite(float(a)) or not math.isfinite(float(b)):
            missing += 1
            continue
        if a < 0 or b < 0 or a != int(a) or b != int(b):
            invalid += 1
            continue
        zeros_2017 += int(a == 0)
        zeros_2019 += int(b == 0)
        low50_2017 += int(a < 50)
        low50_2019 += int(b < 50)
        low100_2017 += int(a < 100)
        low100_2019 += int(b < 100)
        material += int(a >= MATERIAL_COUNT and b >= MATERIAL_COUNT)
        sample.append((geo, iso, exposure[iso], float(100 * (math.log1p(b) - math.log1p(a)))))
    x = np.array([r[2] for r in sample], dtype=float)
    y = np.array([r[3] for r in sample], dtype=float)
    n = len(sample)
    span = float(np.quantile(x, .9)-np.quantile(x, .1)) if n else None
    dev = (x-x.mean())**2 if n else np.array([])
    share = float(max(dev)/sum(dev)) if sum(dev) > 0 else None
    gate = {"key_destinations": len(pairs), "complete_destinations": n,
            "missing_numeric_pairs": missing, "invalid_numeric_pairs": invalid,
            "material_destinations_50_each_year": material,
            "zero_2017": zeros_2017, "zero_2019": zeros_2019,
            "below_50_2017": low50_2017, "below_50_2019": low50_2019,
            "below_100_2017": low100_2017, "below_100_2019": low100_2019,
            "exposure_p90_p10_logpp": span,
            "max_top_destination_centered_exposure_share": share,
            "measured_destinations": [r[1] for r in sample]}
    failed = []
    if n < MIN_N: failed.append("min_complete_destinations")
    if material < MIN_MATERIAL: failed.append("min_material_destinations")
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
                p = float(2 * student_t.sf(abs(beta/se), n-2))
                crit = float(student_t.ppf(.975, n-2))
                if not math.isfinite(p):
                    failed.append("finite_two_sided_p")
                else:
                    primary = {"beta_logpp_per_gdp_logpp": beta, "hc3_se": se,
                               "p_two_sided": p, "ci95": [beta-crit*se, beta+crit*se],
                               "n_destinations": n, "df": n-2,
                               "method": "cross-destination OLS intercept + prior GDP growth, HC3, Student t(n-2)"}
    verdict = "INCONCLUSIVE" if failed else ("SUPPORTED" if beta >= MIN_BETA and p <= P_MAX else
                                              "REFUTED" if beta <= -MIN_BETA and p <= P_MAX else "PARTIAL")
    return {"hypothesis_id": case_id(citizen), "family_id": FAMILY, "verdict": verdict,
            "failed_gates": failed, "gate": gate, "primary": primary,
            "correction": CORRECTION, "limitations": LIMITATIONS}


def results() -> tuple[dict[str, dict[str, object]], str, str, str]:
    lock_commit, lock = source_lock_commit()
    roster, exposure, digest = verify_roster()
    data = selected_outcomes()
    outcomes = {case_id(c): evaluate(c, roster[case_id(c)], exposure, data) for c in CITIZENSHIPS}
    return outcomes, lock["registration_commit"], lock_commit, digest


def summary_text(outcomes: dict[str, dict[str, object]], registration: str, lock_commit: str) -> str:
    counts = Counter(r["verdict"] for r in outcomes.values())
    lines = ["# WDI prior growth → Eurostat immigration by foreign citizenship: 30-cell result audit", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`. Selected Eurostat outcome values and null masks were opened only after both commits. The 30 citizenship groups are disjoint counts but their destination exposure, years and shocks overlap.", "",
             f"Family alpha {FAMILY_ALPHA}; Bonferroni two-sided per-test p≤{P_MAX:.12g}; |beta| threshold {MIN_BETA}. Verdicts: " + ", ".join(f"{k}={counts[k]}" for k in ("SUPPORTED", "REFUTED", "PARTIAL", "INCONCLUSIVE")) + ".", "",
             "| Citizenship | Complete/key | ≥50 each year | Zero 2017/2019 | <100 2017/2019 | Beta | p | Verdict | Failed gates |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |"]
    for c in CITIZENSHIPS:
        r = outcomes[case_id(c)]; g = r["gate"]; p = r["primary"]
        lines.append(f"| `{c}` | {g['complete_destinations']}/{g['key_destinations']} | {g['material_destinations_50_each_year']} | {g['zero_2017']}/{g['zero_2019']} | {g['below_100_2017']}/{g['below_100_2019']} | " +
                     (f"{p['beta_logpp_per_gdp_logpp']:+.4g} | {p['p_two_sided']:.4g}" if p else "not estimated | not estimated") +
                     f" | **{r['verdict']}** | {', '.join(r['failed_gates']) or 'none'} |")
    lines += ["", "Every finite nonnegative count, including zero and low flows, enters estimation; ≥50 in both years is a preregistered *sample quality gate*, not a value-based exclusion. All 30 cells remain in the correction denominator. Per-cell diagnostics include missing and invalid counts, exposure leverage and exact measured destination list. The preserved Eurostat parquet has no quality-flag column.", "",
              "Citizenship is legal nationality, not country of previous residence, birth or departure. Immigration is residence establishment for at least 12 months. National statistical systems and policy differ. This is one observational episode of prior destination GDP growth and later immigrant-flow change; no causal, policy, school, position or featured credit. Local Bonferroni does not account for the wider IESET archive.", ""]
    return "\n".join(lines)


def artifact_payload(c: str, result: dict[str, object], registration: str,
                     lock_commit: str, digest: str, stamp: str) -> dict[str, object]:
    cid = case_id(c)
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": cid, "path": spec_rel(c), "topic": "growth"},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": FAMILY_SIZE,
                                  "key_roster": ROSTER, "key_roster_sha256": digest,
                                  "steelman": steelman_rel(c)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(c),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": result["verdict"], "bucket": result["verdict"].lower(),
                          "reason": ", ".join(result["failed_gates"]) or "frozen estimable test"},
              "data": {"inputs": {"wdi": SOURCE_HASHES[WDI], "eurostat": SOURCE_HASHES[MIGR]},
                       "sample": result["gate"]},
              "results": {"primary": result["primary"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {**result, "runner": RUNNER, "run_utc": stamp,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "descriptive",
                   "p_max_two_sided_bonferroni": P_MAX,
                   "data_status": {"variables_missing": [], "input_vintages": [WDI, MIGR]}}
    manifest = {"hypothesis_id": cid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": result["verdict"],
                "vintages": [WDI, MIGR], "derived_panel": result["gate"],
                "correction": CORRECTION}
    g = result["gate"]
    card = (f"# Result card: {cid}\n\nVerdict: **{result['verdict']}**. Preregistration `{registration}`; source lock `{lock_commit}`.\n\n"
            f"Prior 2013–2016 WDI destination GDP-per-capita growth versus 2017–2019 immigrant-count change among people with `{c}` citizenship. "
            f"{g['complete_destinations']}/{g['key_destinations']} complete/key destinations; {g['material_destinations_50_each_year']} have ≥50 arrivals in both years. "
            f"Zero 2017/2019: {g['zero_2017']}/{g['zero_2019']}; below 100: {g['below_100_2017']}/{g['below_100_2019']}. "
            f"Failed gates: {', '.join(result['failed_gates']) or 'none'}.\n")
    if result["primary"]:
        p = result["primary"]
        card += (f"\nBeta={p['beta_logpp_per_gdp_logpp']:+.6g}, HC3 SE={p['hc3_se']:.6g}, "
                 f"two-sided p={p['p_two_sided']:.6g}, 95% CI={p['ci95']}.\n")
    card += ("\nCitizenship is not prior residence or birthplace. This is one of 30 correlated, Bonferroni-corrected descriptive tests; "
             "zero policy, causal, school, position or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper,
            "chart": {"hypothesis_id": cid, "family_id": FAMILY,
                      "verdict": result["verdict"], "primary": result["primary"]}}


def write_results() -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_rel(c)).exists() for c in CITIZENSHIPS):
        raise FileExistsError("one or more result artifacts already exist")
    outcomes, registration, lock_commit, digest = results()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for c in CITIZENSHIPS:
        cid = case_id(c)
        payload = artifact_payload(c, outcomes[cid], registration, lock_commit, digest, stamp)
        folder = ROOT / run_rel(c)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(c)).read_bytes())
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    (ROOT / SUMMARY).write_text(summary_text(outcomes, registration, lock_commit))
    print(Counter(r["verdict"] for r in outcomes.values()))


def verify_results() -> None:
    outcomes, registration, lock_commit, digest = results()
    for c in CITIZENSHIPS:
        cid = case_id(c)
        folder = ROOT / run_rel(c)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(c, outcomes[cid], registration, lock_commit, digest, saved["run_utc"])
        if saved != payload["diagnostics"] or yaml.safe_load((folder / "evidence_packet.yaml").read_text()) != payload["packet"]:
            raise AssertionError(f"evidence replay differs: {cid}")
        if yaml.safe_load((folder / "manifest.yaml").read_text()) != payload["manifest"]:
            raise AssertionError(f"manifest replay differs: {cid}")
        if json.loads((folder / "chart_data.json").read_text()) != payload["chart"]:
            raise AssertionError(f"chart replay differs: {cid}")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(c)).read_bytes() or
                (folder / "result_card.md").read_text() != payload["card"] or
                (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"text artifact replay differs: {cid}")
    if (ROOT / SUMMARY).read_text() != summary_text(outcomes, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")
    print("All 30 family artifacts replay exactly against pinned sources and frozen gates")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--prepare", action="store_true")
    group.add_argument("--lock", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.prepare: prepare()
    elif args.lock: lock_sources()
    elif args.run: write_results()
    else: verify_results()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
