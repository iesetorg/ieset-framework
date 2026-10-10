#!/usr/bin/env python3
"""Frozen WDI energy-import change to later Eurostat household-price test.

Before separate registration and source-lock commits, read only source hashes,
WDI exposure values, and selected Eurostat outcome keys/dimensions. Eurostat
numeric price values and null masks first open after both commits pass.
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
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = "wdi_energy_import_household_price_forward_2026_10_10"
HID = "wdi_energy_import_household_electricity_price_forward_2026"
RUNNER = "scripts/run_wdi_energy_import_household_price_forward_2026.py"
SPEC = f"hypotheses/energy/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PREREG = "engine/audits/wdi_energy_import_household_price_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/wdi_energy_import_household_price_2026_key_roster.csv"
ROSTER_SHA = "87c467a91a398bfee49dba662d410e8e4f774705f30e3c4a76f06a56aaf7f658"
LOCK = "data/pinned_evidence/wdi_energy_import_household_price_2026.manifest.json"
SUMMARY = "engine/audits/wdi_energy_import_household_price_result_2026-10-10.md"
RUN = f"engine/runs/{HID}"
OUTCOME = "data/vintages/eurostat/nrg_pc_204@2026-05-15T170020Z.parquet"
TREATMENT = "data/vintages/world_bank_wdi/EG.IMP.CONS.ZS@2026-04-30T114922Z.parquet"
SOURCES = {
    "treatment": {"publisher": "world_bank_wdi", "series_id": "EG.IMP.CONS.ZS",
                  "path": TREATMENT, "sha256": "73bd820bd30f36db3efe49a8ec79a0ff8ce39893bb6d3e22631e31468eb316e6",
                  "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
                  "manifest_sha256": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"},
    "outcome": {"publisher": "eurostat", "series_id": "nrg_pc_204",
                "path": OUTCOME, "sha256": "f49495b93f06637ac78106f3630005eef7bea6a5a0cd12d431c505f902a7bd2e",
                "manifest": "data/manifests/fetch_run_2026-05-15T170025Z.yaml",
                "manifest_sha256": "f5fbe09f71bafd5bdb83a48cfff2f700f58ff60d0c07388d93ef80a4826df009"},
}
GEO_TO_ISO3 = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "CY": "CYP", "CZ": "CZE", "DE": "DEU",
    "DK": "DNK", "EE": "EST", "EL": "GRC", "ES": "ESP", "FI": "FIN", "FR": "FRA",
    "HR": "HRV", "HU": "HUN", "IE": "IRL", "IS": "ISL", "IT": "ITA", "LT": "LTU",
    "LU": "LUX", "LV": "LVA", "MT": "MLT", "NL": "NLD", "NO": "NOR", "PL": "POL",
    "PT": "PRT", "RO": "ROU", "SE": "SWE", "SI": "SVN", "SK": "SVK",
}
COUNTRIES = ("AUT", "BEL", "BGR", "CZE", "DEU", "DNK", "ESP", "EST", "FIN", "FRA",
             "GRC", "HRV", "HUN", "IRL", "ITA", "LTU", "LUX", "LVA", "NLD", "POL",
             "PRT", "ROU", "SVK", "SVN", "SWE")
ALPHA = 0.01
MEANINGFUL_BETA = 0.001
MIN_YEARS = 5
MIN_ROWS = 180
MIN_COUNTRIES = 22
MIN_ANCHOR_YEARS = 8
MIN_MATERIAL_ROWS = 100
MIN_MATERIAL_COUNTRIES = 20
MATERIAL_DELTA = 2.0
MAX_DELTA = 15.0
MAX_TOP_ONE_PERCENT = 0.30
MAX_TOP_COUNTRY = 0.20
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 1, "family_alpha": ALPHA, "p_max": ALPHA,
              "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
              "school_score_eligible": False, "school_score_credit": 0,
              "featured_eligible": False}
LIMITATIONS = [
    "WDI net energy imports are primary energy imports minus exports as a percent of energy use; negative values can represent net exports. This is not a tariff or enacted energy policy.",
    "Eurostat nrg_pc_204 is the second-semester tax-inclusive EUR/kWh end-user price for medium household consumers (2500-4999 kWh), not an industrial or wholesale price.",
    "Gas prices, hydro and weather, taxes, subsidies, network charges, exchange rates, retail market rules, and demand may confound the association.",
    "The pinned Eurostat Parquet has no provisional or break flags. A blank source status is not inferred.",
    "Country/year fixed effects do not identify a causal energy-import effect. No policy, causal, school-score, position, or featured credit.",
]

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)

def first_addition(rel: str) -> str:
    commits = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", rel).decode().splitlines()
    if not commits:
        raise RuntimeError(f"missing first-addition commit: {rel}")
    return commits[-1]

def committed_unchanged(rel: str, revision: str) -> None:
    path = ROOT / rel
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{rel}"):
        raise RuntimeError(f"frozen file differs from first commit: {rel}")
    if git_output("status", "--porcelain", "--", rel).strip():
        raise RuntimeError(f"uncommitted frozen file: {rel}")

def threshold() -> dict[str, Any]:
    return {
        "family_id": FAMILY, "family_size": 1, "family_alpha": ALPHA,
        "p_max_two_sided": ALPHA, "expected_beta_sign": "+",
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
        "min_anchor_years": MIN_ANCHOR_YEARS,
        "min_material_change_rows": MIN_MATERIAL_ROWS,
        "min_material_change_countries": MIN_MATERIAL_COUNTRIES,
        "material_treatment_change_min_abs": MATERIAL_DELTA,
        "max_abs_treatment_change": MAX_DELTA,
        "min_years_per_country": MIN_YEARS,
        "max_top_one_percent_residual_x_share": MAX_TOP_ONE_PERCENT,
        "max_top_country_residual_x_share": MAX_TOP_COUNTRY,
        "expected_key_rows": 219, "expected_key_countries": 25,
        "roster_sha256": ROSTER_SHA,
        "source_files": {role: {field: source[field]
                               for field in ("path", "sha256", "manifest", "manifest_sha256")}
                         for role, source in SOURCES.items()},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0,
        "featured_eligible": False,
    }

def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER, SPEC, STEELMAN]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if (spec["hypothesis_id"] != HID or spec["status"] != "pre_registered"
            or spec["evidence_type"] != "associational" or spec["steelman"] != STEELMAN
            or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
            or spec["linked_conditions"] != [] or spec["falsification"]["threshold"] != threshold()):
        raise RuntimeError("registered spec mismatch")
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("registration commit already contains measured results")
    return revision

def check_sources() -> dict[str, dict[str, Any]]:
    narrow = {}
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} raw SHA-256 mismatch")
        manifest_path = ROOT / source["manifest"]
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"{role} fetch-manifest SHA-256 mismatch")
        manifest = yaml.safe_load(manifest_path.read_text())
        matches = [e for e in manifest.get("entries", [])
                   if e.get("publisher") == source["publisher"]
                   and e.get("series_id") == source["series_id"]
                   and e.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} selected source entry mismatch")
        entry = matches[0]
        narrow[role] = {**source, "source_url": entry.get("source_url"),
                        "methodology_url": entry.get("methodology_url"),
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow

def load_roster() -> list[tuple[str, int]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("frozen roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    pairs = [(row["country_iso3"], int(row["year"])) for row in records]
    if (len(pairs) != 219 or len(set(pairs)) != 219 or pairs != sorted(pairs)
            or tuple(sorted(set(c for c, _ in pairs))) != COUNTRIES):
        raise RuntimeError("frozen roster ordering, count, countries, or uniqueness mismatch")
    return pairs

def source_keys() -> tuple[dict[tuple[str, int], float], set[tuple[str, int]]]:
    """Open only WDI treatment values and Eurostat dimensions/keys."""
    frame = pd.read_parquet(ROOT / TREATMENT,
                            columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    if (len(frame) != 17556 or not frame.indicator_id.eq("EG.IMP.CONS.ZS").all()
            or not frame.obs_status.fillna("").eq("").all()):
        raise RuntimeError("WDI raw indicator/status contract changed")
    frame = frame.loc[frame.country_iso3.isin(GEO_TO_ISO3.values())]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI national country-year key")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.loc[np.isfinite(frame.value)]
    exposure = {(str(c), int(y)): float(v)
                for c, y, v in frame[["country_iso3", "year", "value"]].itertuples(index=False, name=None)}
    outcome = pd.read_parquet(ROOT / OUTCOME,
                              columns=["freq", "siec", "nrg_cons", "unit", "tax", "currency", "geo_code", "period"])
    if len(outcome) != 65358:
        raise RuntimeError("Eurostat raw row-count contract changed")
    national = outcome.loc[outcome.freq.eq("S") & outcome.siec.eq("E7000")
                           & outcome.nrg_cons.eq("KWH2500-4999") & outcome.unit.eq("KWH")
                           & outcome.tax.eq("I_TAX") & outcome.currency.eq("EUR")
                           & outcome.geo_code.isin(GEO_TO_ISO3)
                           & outcome.period.str.endswith("S2")]
    if len(national) != 544 or national.duplicated(["geo_code", "period"]).any():
        raise RuntimeError("selected Eurostat household-price key contract changed")
    keys = {(GEO_TO_ISO3[g], int(p[:4]))
            for g, p in national[["geo_code", "period"]].itertuples(index=False, name=None)}
    return exposure, keys

def build_roster(exposure: dict[tuple[str, int], float],
                 outcome_keys: set[tuple[str, int]]) -> tuple[list[tuple[str, int]], pd.DataFrame]:
    candidates = []
    for (country, year), value in exposure.items():
        if (not 2008 <= year <= 2016 or (country, year - 2) not in exposure
                or (country, year - 1) not in exposure
                or (country, year) not in outcome_keys or (country, year + 1) not in outcome_keys):
            continue
        baseline = exposure[(country, year - 2)]
        delta = exposure[(country, year - 1)] - baseline
        if abs(delta) <= MAX_DELTA:
            candidates.append((country, year, delta, baseline))
    counts = Counter(c for c, _, _, _ in candidates)
    rows = sorted(row for row in candidates if counts[row[0]] >= MIN_YEARS)
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "x_base"])
    return [(c, int(y)) for c, y, _, _ in rows], panel

def concentration(panel: pd.DataFrame) -> tuple[float, float] | None:
    if len(panel) < 2 or panel.country_iso3.nunique() < 2:
        return None
    fit = smf.ols("x ~ x_base + C(country_iso3) + C(year)", data=panel).fit()
    squared = np.square(np.asarray(fit.resid, dtype=float))
    total = float(squared.sum())
    if not math.isfinite(total) or total <= 0:
        return None
    n_top = max(1, math.ceil(.01 * len(squared)))
    grouped = pd.DataFrame({"country_iso3": panel.country_iso3.to_numpy(), "squared": squared})
    return (float(np.sort(squared)[-n_top:].sum() / total),
            float(grouped.groupby("country_iso3").squared.sum().max() / total))

def key_preflight() -> dict[str, Any]:
    exposure, keys = source_keys()
    generated, panel = build_roster(exposure, keys)
    if generated != load_roster():
        raise RuntimeError("source key preflight differs from frozen roster")
    material = panel.x.abs().ge(MATERIAL_DELTA)
    shares = concentration(panel)
    if shares is None:
        raise RuntimeError("no treatment-only residual variation")
    if (len(panel) != 219 or panel.country_iso3.nunique() != 25
            or int(material.sum()) != 125
            or panel.loc[material, "country_iso3"].nunique() != 24
            or shares[0] > MAX_TOP_ONE_PERCENT or shares[1] > MAX_TOP_COUNTRY):
        raise RuntimeError("treatment-only roster envelope changed")
    return {
        "treatment_values_read": True, "outcome_values_read": False,
        "outcome_null_masks_read": False, "outcome_status_available": False,
        "exact_year_join": True, "national_outcome_keys": len(keys),
        "roster_sha256": ROSTER_SHA,
        "key_rows": len(panel), "key_countries": int(panel.country_iso3.nunique()),
        "anchor_years": [int(panel.year.min()), int(panel.year.max())],
        "treatment_only_material_rows": int(material.sum()),
        "treatment_only_material_countries": int(panel.loc[material, "country_iso3"].nunique()),
        "treatment_only_top_one_percent_residual_x_share": shares[0],
        "treatment_only_top_country_residual_x_share": shares[1],
    }

def lock_payload(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": registration,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}

def write_source_lock() -> None:
    registration = registration_commit()
    narrow = check_sources()
    preflight = key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(registration, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening Eurostat numeric outcome values")

def check_source_lock(registration: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration, narrow, preflight):
        raise RuntimeError("source lock differs from raw pins or frozen preflight")
    commit = first_addition(LOCK)
    if (commit == registration or subprocess.run(["git", "merge-base", "--is-ancestor", registration, commit],
                                                cwd=ROOT).returncode):
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    if git_output("ls-tree", "-r", "--name-only", commit, "--", RUN).strip():
        raise RuntimeError("source-lock commit already contains measured results")
    return commit

def measured_panel(roster: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """First selected outcome value and null-mask access; caller verified both commits."""
    exposure, _ = source_keys()
    raw = pd.read_parquet(ROOT / OUTCOME,
                          columns=["freq", "siec", "nrg_cons", "unit", "tax", "currency", "geo_code", "period", "value"])
    raw = raw.loc[raw.freq.eq("S") & raw.siec.eq("E7000")
                  & raw.nrg_cons.eq("KWH2500-4999") & raw.unit.eq("KWH")
                  & raw.tax.eq("I_TAX") & raw.currency.eq("EUR")
                  & raw.geo_code.isin(GEO_TO_ISO3) & raw.period.str.endswith("S2")]
    if raw.duplicated(["geo_code", "period"]).any():
        raise RuntimeError("duplicate selected national Eurostat household-price key")
    prices = {(GEO_TO_ISO3[g], int(p[:4])): float(v) if pd.notna(v) and math.isfinite(float(v))
              and float(v) > 0 else None
              for g, p, v in raw[["geo_code", "period", "value"]].itertuples(index=False, name=None)}
    rows, missing = [], 0
    for country, year in roster:
        baseline, forward = prices.get((country, year)), prices.get((country, year + 1))
        if baseline is None or forward is None:
            missing += 1
            continue
        x_base = exposure[(country, year - 2)]
        x = exposure[(country, year - 1)] - x_base
        rows.append({"country_iso3": country, "year": year, "x": x, "x_base": x_base,
                     "y": math.log(forward) - math.log(baseline)})
    panel = pd.DataFrame(rows, columns=["country_iso3", "year", "x", "x_base", "y"])
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
    material = panel.x.abs().ge(MATERIAL_DELTA)
    gate = {"roster_rows": len(roster), "dropped_missing_nonpositive_or_invalid_outcome_pairs": missing,
            "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "anchor_years": int(panel.year.nunique()),
            "material_change_rows": int(material.sum()),
            "material_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
            "outcome_values_read_after_lock": True}
    return panel, gate

def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    if (gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES
            or gate["anchor_years"] < MIN_ANCHOR_YEARS
            or gate["material_change_rows"] < MIN_MATERIAL_ROWS
            or gate["material_change_countries"] < MIN_MATERIAL_COUNTRIES):
        return {"reason": "frozen complete-case or material-exposure floor failed", "fit": None}
    shares = concentration(panel)
    if shares is None:
        return {"reason": "no finite residual exposure variation", "fit": None}
    gate["top_one_percent_residual_x_share"], gate["top_country_residual_x_share"] = shares
    if shares[0] > MAX_TOP_ONE_PERCENT or shares[1] > MAX_TOP_COUNTRY:
        return {"reason": "frozen residual-exposure concentration gate failed", "fit": None}
    model = smf.ols("y ~ x + x_base + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"reason": "fixed-effect design lacks full rank", "fit": None}
    groups = int(panel.country_iso3.nunique())
    fitted = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                    "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fitted.params["x"]), float(fitted.bse["x"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"reason": "invalid country-cluster uncertainty", "fit": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(.995, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"reason": "invalid country-cluster t inference", "fit": None}
    return {"reason": "estimable", "fit": {
        "coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level": .99, "confidence_interval": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
        "model_rank": int(fitted.model.rank),
        "method": "country/year FE OLS plus lagged import-share level, country-cluster CR1, Student t(G-1)"}}

def judge(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    result = estimate(panel, gate)
    fit = result["fit"]
    if fit is None:
        verdict = "INCONCLUSIVE"
    elif fit["coefficient"] >= MEANINGFUL_BETA and fit["p_value_two_sided"] <= ALPHA:
        verdict = "SUPPORTED"
    elif fit["coefficient"] <= -MEANINGFUL_BETA and fit["p_value_two_sided"] <= ALPHA:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
        result["reason"] = "estimable but misses frozen magnitude or family p cutoff"
    return {"verdict": verdict, "reason": result["reason"], "gate": gate, "fit": fit}

def artifacts(result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    verdict, fit, gate = result["verdict"], result["fit"], result["gate"]
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "energy"},
        "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                            "family_id": FAMILY, "family_size": 1, "key_roster": ROSTER,
                            "key_roster_sha256": ROSTER_SHA, "steelman": STEELMAN},
        "reproduction": {"runner": RUNNER, "run_dir": RUN,
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": SOURCES, "sample": gate},
        "results": {"primary": fit}, "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    diagnostics = {
        "hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": result["reason"], "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": registration, "source_lock_commit": lock_commit,
        "source_lock": LOCK, "template": "panel_fe",
        "preflight": gate, "primary": fit, "p_max_two_sided": ALPHA,
        "meaningful_beta_min_abs": MEANINGFUL_BETA,
        "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {"hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen registration `{registration}`; source lock `{lock_commit}`.\n\n"
            f"Energy-import exposure at t-2 to t-1; forward Eurostat second-semester household "
            f"electricity price at t to t+1. Complete pairs: {gate['valid_rows']} across "
            f"{gate['valid_countries']} countries.\n")
    if fit:
        card += (f"\nBeta={fit['coefficient']:+.6g}; country-cluster SE={fit['std_error']:.6g}; "
                 f"two-sided t p={fit['p_value_two_sided']:.6g}; 99% CI={fit['confidence_interval']}.\n")
    card += "\nOne prespecified test at two-sided alpha 0.01; descriptive calibration only. No causal, policy, school, position, or featured credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HID, "family_id": FAMILY, "verdict": verdict, "primary": fit}
    coefficients = ([{"term": "treatment_change", **fit}] if fit else [])
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}

def summary_text(result: dict[str, Any], registration: str, lock_commit: str) -> str:
    fit, gate = result["fit"], result["gate"]
    beta = "not estimated" if fit is None else f"{fit['coefficient']:+.6g}"
    p = "not estimated" if fit is None else f"{fit['p_value_two_sided']:.6g}"
    return (f"# Energy-import change and later household electricity price: result\n\n"
            f"Registration `{registration}`; source lock `{lock_commit}`.\n\n"
            "| Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |\n"
            "| --- | ---: | ---: | ---: | ---: |\n"
            f"| **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | "
            f"{gate['material_change_rows']} / {gate['material_change_countries']} | {beta} | {p} |\n\n"
            "Exposure is the t-2 to t-1 net-primary-energy-import-share change in percentage points, "
            "controlling for the t-2 import-share level; outcome is the t to t+1 second-semester "
            "tax-inclusive Eurostat medium-household log electricity-price change. "
            "One family test at two-sided alpha 0.01. Descriptive calibration only; zero "
            "causal, policy, school, position, and featured credit.\n")

def write_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    if (ROOT / RUN).exists() or (ROOT / SUMMARY).exists():
        raise FileExistsError("family result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = artifacts(result, registration, lock_commit, stamp)
    folder = ROOT / RUN
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error",
                 "p_value_two_sided", "confidence_level", "confidence_interval", "n_rows",
                 "n_countries", "df_inference", "model_rank", "method"]).to_parquet(
                     folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(result, registration, lock_commit))

def normalize_arrow(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [normalize_arrow(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: normalize_arrow(item) for key, item in value.items()}
    if isinstance(value, list):
        return [normalize_arrow(item) for item in value]
    return value

def equal_close(actual: Any, expected: Any, label: str) -> None:
    actual = normalize_arrow(actual)
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            equal_close(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")

def verify_artifacts(result: dict[str, Any], registration: str, lock_commit: str) -> None:
    folder = ROOT / RUN
    saved = json.loads((folder / "diagnostics.json").read_text())
    payload = artifacts(result, registration, lock_commit, saved["run_utc"])
    for name in ("diagnostics", "manifest", "packet", "chart", "coefficients"):
        path = folder / {"diagnostics": "diagnostics.json", "manifest": "manifest.yaml",
                         "packet": "evidence_packet.yaml", "chart": "chart_data.json",
                         "coefficients": "coefficients.parquet"}[name]
        actual = (pd.read_parquet(path).to_dict(orient="records") if name == "coefficients"
                  else yaml.safe_load(path.read_text()) if name in ("manifest", "packet")
                  else json.loads(path.read_text()))
        equal_close(actual, payload[name], name)
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC).read_bytes()
            or (folder / "result_card.md").read_text() != payload["card"]
            or (folder / "replication.py").read_text() != payload["wrapper"]):
        raise AssertionError("text artifact mismatch")
    if (ROOT / SUMMARY).read_text() != summary_text(result, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    narrow = check_sources()
    if args.check_sources:
        print("WDI energy imports and Eurostat household-price SHA pins match; outcome values unopened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    registration = registration_commit()
    preflight = key_preflight()
    lock_commit = check_source_lock(registration, narrow, preflight)
    panel, gate = measured_panel(load_roster())
    result = judge(panel, gate)
    if args.run:
        write_artifacts(result, registration, lock_commit)
        print(result["verdict"], result["reason"])
        return 0
    verify_artifacts(result, registration, lock_commit)
    print("verified exact replay", FAMILY, result["verdict"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
