#!/usr/bin/env python3
"""Frozen three-test descriptive CEPII Gravity/WDI exposure family.

Source-check and key preflight do not open measured columns. Measured values
may be loaded only after one first-addition preregistration commit and a
separate committed source-lock manifest. Adverse and null results are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER_REL = "scripts/run_cepii_wdi_exposure_family_2026.py"
PLAN_REL = "engine/audits/cepii_wdi_exposure_family_prereg_2026-10-09.md"
LOCK_REL = "data/pinned_evidence/cepii_wdi_exposure_family_2026.manifest.json"
FAMILY_ID = "cepii_wdi_exposure_family_2026_10_09"
FAMILY_P_MAX = 1 / 60  # Two-sided Bonferroni alpha 0.05 / three fixed tests.
RAW_CEPII = "data/raw/cepii/Gravity_csv_V202211.zip"
RAW_CEPII_SHA256 = "7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1"
OLD_ID = "liberal_free_trade_partner_growth_panel_1990_2020"
OLD_COUNTRIES = frozenset((
    "ARG AUS AUT BEL BGD BRA CAN CHE CHL CHN COL CRI CZE DEU DNK DOM ECU EGY "
    "ESP EST FIN FRA GBR GRC GTM HND HUN IDN IND IRL ISR ITA JOR JPN KOR LTU "
    "LVA MAR MEX MYS NIC NLD NOR NZL PAK PAN PER PHL POL PRT ROU SGP SLV SVK "
    "SVN SWE THA TUR USA VNM ZAF"
).split())
# Frozen from a country/year-key-only intersection before any family values.
# The explicit roster also excludes WDI regional aggregates and historical codes.
KEY_COUNTRIES = frozenset((
    "ABW AFG AGO ALB AND ARE ARM ASM ATG AZE BDI BEN BFA BGR BHR BHS BIH BLR "
    "BLZ BMU BOL BRB BRN BTN BWA CAF CIV CMR COD COG COM CPV CUB CUW CYM CYP "
    "DJI DMA DZA ERI ETH FJI FRO FSM GAB GEO GHA GIB GIN GMB GNB GNQ GRD GRL "
    "GUM GUY HKG HRV HTI IRN IRQ ISL JAM KAZ KEN KGZ KHM KIR KNA KWT LAO LBN "
    "LBR LBY LCA LIE LKA LSO LUX MAC MCO MDA MDG MDV MHL MKD MLI MLT MMR MNE "
    "MNG MNP MOZ MRT MUS MWI NAM NCL NER NGA NPL NRU OMN PLW PNG PRI PRK PRY "
    "PSE PYF QAT RUS RWA SAU SDN SEN SLB SLE SMR SOM SRB SSD STP SUR SWZ SXM "
    "SYC SYR TCA TCD TGO TJK TKM TLS TON TTO TUN TUV TZA UGA UKR URY UZB VCT "
    "VEN VGB VUT WSM YEM ZMB ZWE"
).split())
if len(OLD_COUNTRIES) != 61 or len(KEY_COUNTRIES) != 151 or OLD_COUNTRIES & KEY_COUNTRIES:
    raise RuntimeError("frozen country rosters changed")

SOURCE_FILES: dict[str, dict[str, str]] = {
    "market": {
        "source": "cepii:gravity_foreign_market_potential",
        "path": "data/vintages/cepii/gravity_foreign_market_potential@2026-05-15T175027Z.parquet",
        "sha256": "4fc1accd300115d9169bcfe6b7018045d8839d3e866bffe3240be46f524eaa3e",
        "manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "series_id": "gravity_foreign_market_potential",
    },
    "fta_market": {
        "source": "cepii:gravity_fta_market_potential_share",
        "path": "data/vintages/cepii/gravity_fta_market_potential_share@2026-05-15T175027Z.parquet",
        "sha256": "64cfa88dfa7a60e78206ca8ee7d35a5e25e4d1677d40aef67fa7637971f82d05",
        "manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "series_id": "gravity_fta_market_potential_share",
    },
    "fta_partner_gdp": {
        "source": "cepii:gravity_fta_partner_gdp_share",
        "path": "data/vintages/cepii/gravity_fta_partner_gdp_share@2026-05-15T175027Z.parquet",
        "sha256": "81571674fa7a41c32518bf84c4c54032b024ba23124c6b158e9189bfe2bf5351",
        "manifest": "data/manifests/fetch_run_2026-05-15T175027Z.yaml",
        "series_id": "gravity_fta_partner_gdp_share",
    },
    "trade": {
        "source": "world_bank_wdi:NE.TRD.GNFS.ZS",
        "path": "data/vintages/world_bank_wdi/NE.TRD.GNFS.ZS@2026-05-05T194657Z.parquet",
        "sha256": "4ecf502c1695a316e0d31dda4a90cb95d69494cf34cec26cee6f96420e4c34b1",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NE.TRD.GNFS.ZS",
    },
    "private": {
        "source": "world_bank_wdi:NE.GDI.FPRV.ZS",
        "path": "data/vintages/world_bank_wdi/NE.GDI.FPRV.ZS@2026-04-30T115003Z.parquet",
        "sha256": "84294f869d513ae4c70154630b31388a53b41c42bf849a006740c9324ebeba14",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "series_id": "NE.GDI.FPRV.ZS",
    },
    "hightech": {
        "source": "world_bank_wdi:TX.VAL.TECH.MF.ZS",
        "path": "data/vintages/world_bank_wdi/TX.VAL.TECH.MF.ZS@2026-05-05T195027Z.parquet",
        "sha256": "b99e36dfce6c0ccbebed61124508f11dd2aac6e6d635bacca7955eacf20a1994",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "TX.VAL.TECH.MF.ZS",
    },
    "income": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.PCAP.KD",
    },
}

COHORT: dict[str, dict[str, Any]] = {
    "cepii_foreign_market_potential_trade_open_change_holdout_2026": {
        "topic": "trade", "exposure": "market", "outcome": "trade",
        "period": [1961, 2020], "min_observations": 800, "min_countries": 50,
        "min_varying_countries": 35, "min_within_country_range": 0.0001,
        "min_positive_share_rows": None, "treatment_transform": "log_change",
        "measurement_limit": "Nominal partner GDP and source coverage can move market potential; trade % GDP also moves with its denominator.",
    },
    "cepii_fta_market_potential_private_investment_change_holdout_2026": {
        "topic": "trade", "exposure": "fta_market", "outcome": "private",
        "period": [1990, 2020], "min_observations": 400, "min_countries": 35,
        "min_varying_countries": 25, "min_within_country_range": 0.01,
        "min_positive_share_rows": 200, "treatment_transform": "share_level",
        "measurement_limit": "FTA status is not tariff depth; private investment is selected by domestic expectations and shares a GDP denominator.",
    },
    "cepii_fta_partner_gdp_hightech_export_change_holdout_2026": {
        "topic": "trade", "exposure": "fta_partner_gdp", "outcome": "hightech",
        "period": [1995, 2020], "min_observations": 400, "min_countries": 35,
        "min_varying_countries": 25, "min_within_country_range": 0.01,
        "min_positive_share_rows": 200, "treatment_transform": "share_level",
        "measurement_limit": "High-tech share can rise when other exports fall and is not product diversification or domestic productivity.",
    },
}
MIN_PAIRS_PER_COUNTRY = 5
COEFFICIENT_COLUMNS = (
    "term", "coefficient", "std_error", "p_value", "ci95", "n_obs",
    "n_countries", "r_squared", "method",
)


def relative_paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = COHORT[hypothesis_id]["topic"]
    return (
        f"hypotheses/{topic}/{hypothesis_id}.yaml",
        f"hypotheses/steelman/{hypothesis_id}.md",
        f"engine/runs/{hypothesis_id}",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"file differs from frozen commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def registration_commit() -> str:
    files = [RUNNER_REL, PLAN_REL]
    for hypothesis_id in COHORT:
        spec, steelman, _ = relative_paths(hypothesis_id)
        files.extend((spec, steelman))
    commits = {first_addition(path) for path in files}
    if len(commits) != 1:
        raise RuntimeError("family files lack one shared first-addition registration commit")
    revision = commits.pop()
    for path in files:
        committed_unchanged(path, revision)
    for hypothesis_id in COHORT:
        run_rel = relative_paths(hypothesis_id)[2]
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel).strip():
            raise RuntimeError("registration commit already contained a run artifact")
    return revision


def check_sources() -> None:
    if sha256(ROOT / RAW_CEPII) != RAW_CEPII_SHA256:
        raise RuntimeError("raw CEPII archive SHA-256 mismatch")
    for role, source in SOURCE_FILES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"pinned source SHA-256 mismatch: {role}")
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        entries = [entry for entry in manifest["entries"]
                   if entry.get("parquet_path") == source["path"]
                   and entry.get("series_id") == source["series_id"]]
        if len(entries) != 1 or entries[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"source file differs from tracked fetch manifest: {role}")
        if role in {"market", "fta_market", "fta_partner_gdp"}:
            if entries[0].get("extra", {}).get("source_zip_sha256") != RAW_CEPII_SHA256:
                raise RuntimeError(f"CEPII source archive is not pinned for {role}")


def validate_specs() -> None:
    old = yaml.safe_load((ROOT / f"hypotheses/trade/{OLD_ID}.yaml").read_text())
    if set(old["sample"]["countries"]) != OLD_COUNTRIES:
        raise RuntimeError("old country roster no longer matches the frozen exclusion")
    pairs: set[tuple[str, str]] = set()
    for hypothesis_id, config in COHORT.items():
        spec_rel, steelman_rel, _ = relative_paths(hypothesis_id)
        spec = yaml.safe_load((ROOT / spec_rel).read_text())
        pair = (SOURCE_FILES[config["exposure"]]["source"], SOURCE_FILES[config["outcome"]]["source"])
        if pair in pairs:
            raise RuntimeError("duplicate source pair within family")
        pairs.add(pair)
        threshold = spec["falsification"]["threshold"]
        expected = {
            "family_id": FAMILY_ID, "family_size": 3, "family_alpha": 0.05,
            "family_p_max": FAMILY_P_MAX, "expected_sign": "+",
            "min_observations": config["min_observations"],
            "min_countries": config["min_countries"],
            "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY,
            "min_varying_countries": config["min_varying_countries"],
            "min_within_country_range": config["min_within_country_range"],
            "old_hypothesis_id": OLD_ID, "old_country_count": 61,
            "school_score_credit": 0, "school_score_eligible": False,
        }
        if config["min_positive_share_rows"] is not None:
            expected["min_positive_share_rows"] = config["min_positive_share_rows"]
        for key, value in expected.items():
            if threshold.get(key) != value:
                raise RuntimeError(f"frozen threshold mismatch: {hypothesis_id}.{key}")
        pin_roles = {"treatment": config["exposure"], "outcome": config["outcome"], "income": "income"}
        for role, name in pin_roles.items():
            pin = threshold["source_files"][role]
            source = SOURCE_FILES[name]
            if pin != {k: source[k] for k in ("path", "sha256", "manifest")}:
                raise RuntimeError(f"spec source pin changed: {hypothesis_id}.{role}")
        if (spec["hypothesis_id"] != hypothesis_id or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["claim_direction"] != "+"
                or spec["sample"]["period"] != config["period"]
                or spec["steelman"] != steelman_rel
                or spec.get("covers_claims") != []
                or spec.get("linked_hypotheses") != []
                or spec.get("linked_conditions") != []):
            raise RuntimeError(f"registration content changed: {hypothesis_id}")
        if spec["variables"]["treatment"][0]["source"] != pair[0] or spec["variables"]["outcome"][0]["source"] != pair[1]:
            raise RuntimeError(f"registered measured source pair changed: {hypothesis_id}")


def lock_payload(prereg_commit: str) -> dict[str, Any]:
    return {
        "family_id": FAMILY_ID, "preregistration_commit": prereg_commit,
        "cepii_raw_archive": {"path": RAW_CEPII, "sha256": RAW_CEPII_SHA256,
                              "member": "Gravity_V202211.csv"},
        "sources": SOURCE_FILES,
        "note": "Source hashes and all three registrations were locked before measured-value access; RTA coverage is not a family source.",
    }


def write_source_lock() -> None:
    revision = registration_commit()
    validate_specs()
    check_sources()
    path = ROOT / LOCK_REL
    if path.exists():
        raise FileExistsError(f"source lock already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(lock_payload(revision), indent=2, sort_keys=True) + "\n")
    print(f"wrote source lock {LOCK_REL}; commit it separately before reading values")


def check_source_lock(prereg_commit: str) -> None:
    path = ROOT / LOCK_REL
    if json.loads(path.read_text()) != lock_payload(prereg_commit):
        raise RuntimeError("source lock differs from registered source pins")
    lock_commit = first_addition(LOCK_REL)
    if lock_commit == prereg_commit:
        raise RuntimeError("source lock was not committed separately after registration")
    committed_unchanged(LOCK_REL, lock_commit)
    for hypothesis_id in COHORT:
        run_rel = relative_paths(hypothesis_id)[2]
        if git_output("ls-tree", "-r", "--name-only", lock_commit, "--", run_rel).strip():
            raise RuntimeError("source-lock commit already contained a run artifact")


@cache
def source_keys(role: str) -> set[tuple[str, int]]:
    frame = pd.read_parquet(ROOT / SOURCE_FILES[role]["path"], columns=["country_iso3", "year"])
    frame = frame[frame.country_iso3.isin(KEY_COUNTRIES)]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate source keys: {role}")
    return {(str(country), int(year)) for country, year in zip(frame.country_iso3, frame.year)
            if str(country) in KEY_COUNTRIES and pd.notna(year)}


def key_preflight() -> dict[str, dict[str, Any]]:
    rows = {}
    for hypothesis_id, config in COHORT.items():
        exp = source_keys(config["exposure"])
        out = source_keys(config["outcome"])
        income = source_keys("income")
        start, end = config["period"]
        paired = {(country, year) for country, year in exp
                  if start <= year <= end and (country, year - 1) in exp
                  and (country, year) in out and (country, year + 1) in out
                  and (country, year) in income}
        counts: dict[str, int] = {}
        for country, _ in paired:
            counts[country] = counts.get(country, 0) + 1
        eligible = {country for country, n in counts.items() if n >= MIN_PAIRS_PER_COUNTRY}
        pairs = sum(n for country, n in counts.items() if country in eligible)
        rows[hypothesis_id] = {
            "upper_pairs": pairs, "upper_countries": len(eligible),
            "wdi_nulls_unchecked": True, "values_read": False,
            "key_envelope_passed": pairs >= config["min_observations"] and len(eligible) >= config["min_countries"],
        }
    return rows


@cache
def load_values(role: str) -> pd.DataFrame:
    frame = pd.read_parquet(ROOT / SOURCE_FILES[role]["path"], columns=["country_iso3", "year", "value"])
    frame = frame[frame.country_iso3.isin(KEY_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    if frame["year"].isna().any() or frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"invalid measured source keys: {role}")
    frame["year"] = frame["year"].astype(int)
    return frame[["country_iso3", "year", "value"]]


def measured_panel(hypothesis_id: str) -> pd.DataFrame:
    config = COHORT[hypothesis_id]
    exposure = load_values(config["exposure"]).rename(columns={"value": "exposure"})
    previous = exposure.rename(columns={"exposure": "previous_exposure"}).copy()
    previous["year"] += 1
    outcome = load_values(config["outcome"]).rename(columns={"value": "baseline_outcome"})
    next_outcome = outcome.rename(columns={"baseline_outcome": "next_outcome"}).copy()
    next_outcome["year"] -= 1
    income = load_values("income").rename(columns={"value": "income"})
    panel = (exposure.merge(previous, on=["country_iso3", "year"], validate="one_to_one")
             .merge(outcome, on=["country_iso3", "year"], validate="one_to_one")
             .merge(next_outcome, on=["country_iso3", "year"], validate="one_to_one")
             .merge(income, on=["country_iso3", "year"], validate="one_to_one"))
    start, end = config["period"]
    panel = panel[panel.year.between(start, end)].copy()
    values = ["exposure", "previous_exposure", "baseline_outcome", "next_outcome", "income"]
    panel = panel.dropna(subset=values)
    panel = panel[np.isfinite(panel[values]).all(axis=1) & (panel.income > 0)].copy()
    panel = panel[(panel.baseline_outcome >= 0) & (panel.next_outcome >= 0)]
    if config["outcome"] == "hightech":
        panel = panel[(panel.baseline_outcome <= 100) & (panel.next_outcome <= 100)]
    if config["treatment_transform"] == "log_change":
        panel = panel[(panel.exposure > 0) & (panel.previous_exposure > 0)].copy()
        panel["treatment"] = np.log(panel.exposure) - np.log(panel.previous_exposure)
    else:
        panel = panel[panel.exposure.between(0, 1) & panel.previous_exposure.between(0, 1)].copy()
        panel["treatment"] = panel.exposure
    panel["outcome_change"] = panel.next_outcome - panel.baseline_outcome
    panel["log_income"] = np.log(panel.income)
    panel = panel[np.isfinite(panel[["treatment", "outcome_change", "log_income"]]).all(axis=1)].copy()
    counts = panel.groupby("country_iso3").year.transform("size")
    panel = panel[counts >= MIN_PAIRS_PER_COUNTRY]
    if set(panel.country_iso3) & OLD_COUNTRIES:
        raise RuntimeError("old countries entered prospective holdout")
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def estimate_one(hypothesis_id: str) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    config = COHORT[hypothesis_id]
    panel = measured_panel(hypothesis_id)
    ranges = panel.groupby("country_iso3").treatment.agg(lambda x: float(x.max() - x.min()))
    varying = int((ranges > config["min_within_country_range"]).sum()) if config["treatment_transform"] == "log_change" else int((ranges >= config["min_within_country_range"]).sum())
    positive = int((panel.treatment > 0).sum()) if config["min_positive_share_rows"] is not None else None
    gate = {
        "observations": int(len(panel)), "countries": int(panel.country_iso3.nunique()),
        "varying_countries": varying, "positive_share_rows": positive,
        "min_pairs_per_country": MIN_PAIRS_PER_COUNTRY, "old_country_overlap": 0,
        "treatment_years": [int(panel.year.min()), int(panel.year.max())] if len(panel) else [],
    }
    floor = (gate["observations"] >= config["min_observations"]
             and gate["countries"] >= config["min_countries"]
             and varying >= config["min_varying_countries"]
             and (positive is None or positive >= config["min_positive_share_rows"]))
    gate["passed"] = floor
    if not floor:
        return gate, "INCONCLUSIVE", "registered complete-case or exposure-variation floor failed", None
    model = smf.ols("outcome_change ~ treatment + baseline_outcome + log_income + C(country_iso3) + C(year)", data=panel)
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3, "use_correction": True}, use_t=False)
    if fit.model.rank != fit.model.exog.shape[1]:
        return gate, "INCONCLUSIVE", "registered fixed-effect design is rank deficient", None
    beta = float(fit.params["treatment"])
    se = float(fit.bse["treatment"])
    p_value = float(fit.pvalues["treatment"])
    ci95 = [float(x) for x in fit.conf_int().loc["treatment"]]
    r_squared = float(fit.rsquared)
    if not all(math.isfinite(x) for x in (beta, se, p_value, r_squared, *ci95)) or se <= 0 or not 0 <= p_value <= 1:
        return gate, "INCONCLUSIVE", "nonfinite or unidentified clustered estimate", None
    estimate = {
        "coefficient": beta, "std_error": se, "p_value": p_value,
        "ci95": ci95, "n_obs": gate["observations"],
        "n_countries": gate["countries"], "r_squared": r_squared,
        "method": "country/year FE OLS; country-clustered normal-Wald standard errors",
    }
    if p_value <= FAMILY_P_MAX and beta > 0:
        return gate, "SUPPORTED", "positive coefficient clears frozen three-test family threshold", estimate
    if p_value <= FAMILY_P_MAX and beta < 0:
        return gate, "REFUTED", "negative coefficient clears frozen three-test family threshold", estimate
    return gate, "PARTIAL", "estimable association does not clear frozen directional family rule", estimate


def artifacts(hypothesis_id: str, revision: str, gate: dict[str, Any], verdict: str,
              reason: str, estimate: dict[str, Any] | None, stamp: str) -> dict[str, Any]:
    config = COHORT[hypothesis_id]
    spec_rel, steelman_rel, run_rel = relative_paths(hypothesis_id)
    roles = {"treatment": config["exposure"], "outcome": config["outcome"], "income": "income"}
    inputs = [{"role": role, **SOURCE_FILES[name]} for role, name in roles.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "policy_score_credit": 0, "featured_eligible": False}
    limits = [
        "Descriptive country-panel association, not a causal treaty or policy effect.",
        "The old CEPII FTA/WDI result was visible and its entire 61-country roster was excluded.",
        "FTA tests B and C share CEPII coding and are not independent replication.",
        "All three tests share a two-sided Bonferroni threshold; no school or position receives score credit.",
        config["measurement_limit"],
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": revision, "source_lock": LOCK_REL,
        "template": "panel_fe", "preflight": gate, "estimate": estimate,
        "family_id": FAMILY_ID, "family_size": len(COHORT), "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER_REL,
        "preregistration_commit": revision, "source_lock": LOCK_REL,
        "status": verdict, "vintages": inputs, "derived_panel": gate,
        "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_rel, "topic": config["topic"]},
        "preregistration": {"spec_commit": revision, "steelman": steelman_rel,
                            "family_id": FAMILY_ID, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER_REL, "run_dir": run_rel,
                         "command": f"python3 {RUNNER_REL} --verify {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "old_country_overlap": 0,
                 "n_observations": gate["observations"], "n_countries": gate["countries"]},
        "results": estimate, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {revision}; source lock: {LOCK_REL}.\n"
            f"Complete sample: {gate['observations']} country-year pairs, {gate['countries']} countries; "
            "zero overlap with the 61-country old CEPII/WDI roster.\n"
            f"Family threshold: two-sided p <= {FAMILY_P_MAX:.8f} over three tests.\n")
    if estimate is not None:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; clustered SE "
                 f"{estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += "\nMeasurement boundary: " + config["measurement_limit"] + "\nDescriptive calibration only; zero school, policy, featured and causal credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               "raise SystemExit(subprocess.call([sys.executable, "
               f"str(root / {RUNNER_REL!r}), '--verify', {hypothesis_id!r}], cwd=root))\n")
    chart = {"hypothesis_id": hypothesis_id, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None,
             "family_p_max": FAMILY_P_MAX}
    rows = ([{"term": "treatment", **estimate}] if estimate else [])
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart, "rows": rows}


def write_artifacts(hypothesis_id: str, payload: dict[str, Any]) -> None:
    spec_rel, _, run_rel = relative_paths(hypothesis_id)
    folder = ROOT / run_rel
    if folder.exists():
        raise FileExistsError(f"existing result directory: {run_rel}")
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["rows"], columns=COEFFICIENT_COLUMNS).to_parquet(folder / "coefficients.parquet", index=False)


def equal_close(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for index, value in enumerate(expected):
            equal_close(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: number mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(hypothesis_id: str, revision: str) -> None:
    spec_rel, _, run_rel = relative_paths(hypothesis_id)
    folder = ROOT / run_rel
    saved = json.loads((folder / "diagnostics.json").read_text())
    gate, verdict, reason, estimate = estimate_one(hypothesis_id)
    expected = artifacts(hypothesis_id, revision, gate, verdict, reason, estimate, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], f"{hypothesis_id}.diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], f"{hypothesis_id}.manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], f"{hypothesis_id}.packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], f"{hypothesis_id}.chart")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError(f"{hypothesis_id}: stored text differs from exact replay")
    stored_rows = [
        {key: value.tolist() if hasattr(value, "tolist") else value
         for key, value in row.items()}
        for row in pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records")
    ]
    equal_close(stored_rows, [{key: row.get(key) for key in COEFFICIENT_COLUMNS} for row in expected["rows"]], f"{hypothesis_id}.coefficients")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-sources", action="store_true")
    action.add_argument("--write-source-lock", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", nargs="?", const="all", choices=[*COHORT, "all"])
    args = parser.parse_args()
    if args.check_sources:
        check_sources()
        print("Seven measured vintages and CEPII raw archive match tracked source pins; no value columns read.")
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    revision = registration_commit()
    validate_specs()
    check_sources()
    check_source_lock(revision)
    if args.preflight:
        rows = key_preflight()
        print(json.dumps(rows, indent=2, sort_keys=True))
        return 0 if all(row["key_envelope_passed"] for row in rows.values()) else 1
    if args.run:
        if any((ROOT / relative_paths(hypothesis_id)[2]).exists() for hypothesis_id in COHORT):
            raise FileExistsError("at least one family result already exists")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        payloads = {}
        for hypothesis_id in COHORT:
            gate, verdict, reason, estimate = estimate_one(hypothesis_id)
            payloads[hypothesis_id] = artifacts(hypothesis_id, revision, gate, verdict, reason, estimate, stamp)
        for hypothesis_id, payload in payloads.items():
            write_artifacts(hypothesis_id, payload)
            print(hypothesis_id, payload["diagnostics"]["verdict_label"], payload["diagnostics"]["preflight"])
        return 0
    ids = COHORT if args.verify == "all" else [args.verify]
    for hypothesis_id in ids:
        verify_artifacts(hypothesis_id, revision)
        print("verified exact replay", hypothesis_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
