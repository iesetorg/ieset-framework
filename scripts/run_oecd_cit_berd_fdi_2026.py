#!/usr/bin/env python3
"""Frozen OECD statutory CIT change to BERD and net FDI two-test study.

Before two separate Git commits, this runner reads only source hashes,
metadata, keys, and OECD CIT exposure values. BERD/FDI values and FDI outcome
status are opened only by --run or --verify after both commits are checked.
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
FAMILY = "oecd_cit_berd_fdi_forward_2026_10_10"
RUNNER = "scripts/run_oecd_cit_berd_fdi_2026.py"
PREREG = "engine/audits/oecd_cit_berd_fdi_family_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/oecd_cit_berd_fdi_family_2026_key_roster.csv"
ROSTER_SHA = "2f0318e4d42002772babd3eb1967f90561d1c02ecc1dd7666422745b1900cd01"
LOCK = "data/pinned_evidence/oecd_cit_berd_fdi_family_2026.manifest.json"
SUMMARY = "engine/audits/oecd_cit_berd_fdi_family_results_2026-10-10.md"
CIT = "data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet"
BERD = "data/vintages/eurostat/rd_e_gerdtot@2026-05-05T210242Z.parquet"
FDI = "data/vintages/world_bank_wdi/BX.KLT.DINV.WD.GD.ZS@2026-05-05T195106Z.parquet"
SOURCES = {
    "treatment": {"publisher": "oecd", "series_id": "oecd_combined_corporate_income_tax_rate",
                  "path": CIT, "sha256": "3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1",
                  "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
                  "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18"},
    "berd": {"publisher": "eurostat", "series_id": "rd_e_gerdtot",
             "path": BERD, "sha256": "fea284d7b17e31a3803749fca052f6a110ed1b8e703a9151964d1d15f58df152",
             "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
             "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "fdi": {"publisher": "world_bank_wdi", "series_id": "BX.KLT.DINV.WD.GD.ZS",
            "path": FDI, "sha256": "626691877048dc78d5f7b4f6948dd680d3e111aedff252d1286ca2fd40b8abc5",
            "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
            "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
}
# Exact geo labels observed in the selected Eurostat dimensions. Aggregate
# EA/EU and CN_X_HK keys are intentionally omitted; EL/UK are source aliases.
GEO_TO_ISO3 = dict(x.split(":") for x in (
    "AL:ALB AT:AUT BA:BIH BE:BEL BG:BGR CH:CHE CY:CYP CZ:CZE DE:DEU DK:DNK "
    "EE:EST EL:GRC ES:ESP FI:FIN FR:FRA HR:HRV HU:HUN IE:IRL IS:ISL IT:ITA "
    "JP:JPN KR:KOR LT:LTU LU:LUX LV:LVA ME:MNE MK:MKD MT:MLT NL:NLD NO:NOR "
    "PL:POL PT:PRT RO:ROU RS:SRB RU:RUS SE:SWE SI:SVN SK:SVK TR:TUR UK:GBR US:USA"
).split())
SKIP_GEOS = {"EA20", "EA21", "EU27_2020", "CN_X_HK"}
CASES = {
    "berd": {"id": "oecd_cit_business_rd_forward_2026", "topic": "fiscal",
             "label": "Business-performed R&D expenditure / GDP", "source": "eurostat:rd_e_gerdtot",
             "key_rows": 565, "key_countries": 35, "prelock_material_rows": 128,
             "prelock_material_countries": 32, "floor": (400, 25, 60, 20),
             "meaningful_beta": 0.02},
    "fdi": {"id": "oecd_cit_net_fdi_forward_2026", "topic": "fiscal",
            "label": "FDI net inflows / GDP", "source": "world_bank_wdi:BX.KLT.DINV.WD.GD.ZS",
            "key_rows": 2387, "key_countries": 141, "prelock_material_rows": 382,
            "prelock_material_countries": 122, "floor": (1500, 80, 180, 60),
            "meaningful_beta": 0.2},
}
T_START, T_END, HORIZON, MIN_YEARS = 2001, 2017, 2, 5
MATERIAL_X, FAMILY_ALPHA, P_MAX = 1.0, 0.01, 0.005
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 2, "family_alpha": FAMILY_ALPHA,
              "bonferroni_p_max": P_MAX, "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "The OECD combined statutory CIT rate is a headline central-plus-subcentral rate, not an effective marginal/average tax burden or an R&D tax incentive.",
    "Eurostat BERD is R&D performed in the business-enterprise sector regardless of who funds it; the selected raw series has no observation-status flags.",
    "WDI FDI net inflows as a share of GDP are balance-of-payments flows, may be negative or volatile, and do not isolate greenfield investment.",
    "Both outcomes are GDP shares, so denominator changes can create common movement unrelated to investment or R&D decisions.",
    "Country/year effects and temporal ordering do not identify a causal tax or policy effect; tax reforms and investment may respond to shared shocks.",
    "The two-test Bonferroni correction is local to this prospectively registered batch, not to the visible IESET archive.",
    "No result receives school, policy, causal, or featured credit.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


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
        raise RuntimeError(f"frozen file differs from first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def spec_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/{case['topic']}/{case['id']}.yaml"


def steelman_rel(case: dict[str, Any]) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_rel(case: dict[str, Any]) -> str:
    return f"engine/runs/{case['id']}"


def threshold_for(key: str, case: dict[str, Any]) -> dict[str, Any]:
    n, g, m, mg = case["floor"]
    return {"family_id": FAMILY, "family_size": 2, "family_alpha": FAMILY_ALPHA,
            "p_max_two_sided_bonferroni": P_MAX,
            "expected_beta_sign": "-", "meaningful_beta_min_abs": case["meaningful_beta"],
            "min_valid_rows": n, "min_valid_countries": g,
            "min_material_change_rows": m, "min_material_change_countries": mg,
            "material_cit_change_min_pp": MATERIAL_X,
            "min_years_per_country": MIN_YEARS,
            "expected_key_rows": case["key_rows"], "expected_key_countries": case["key_countries"],
            "roster_sha256": ROSTER_SHA,
            "source_files": {role: {field: source[field] for field in ("path", "sha256", "manifest", "manifest_sha256")}
                             for role, source in (("treatment", SOURCES["treatment"]), ("outcome", SOURCES[key]))},
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_eligible": False, "policy_score_credit": 0}


def registration_commit() -> str:
    frozen = [PREREG, RUNNER, ROSTER]
    for case in CASES.values():
        frozen += [spec_rel(case), steelman_rel(case)]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_rel(case)).read_text())
        if (spec["hypothesis_id"] != case["id"] or spec["status"] != "pre_registered"
                or spec["evidence_type"] != "associational"
                or spec["steelman"] != steelman_rel(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["falsification"]["threshold"] != threshold_for(key, case)):
            raise RuntimeError(f"registered spec mismatch: {key}")
        if git_output("ls-tree", "-r", "--name-only", revision, "--", run_rel(case)).strip():
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
                        "license": entry.get("license"), "fetch_utc": entry.get("fetch_utc"),
                        "rows": entry.get("rows"), "frequency": entry.get("frequency"),
                        "units": entry.get("units")}
    return narrow


def load_roster() -> dict[str, list[tuple[str, int]]]:
    raw = (ROOT / ROSTER).read_bytes()
    if sha256(ROOT / ROSTER) != ROSTER_SHA or not raw.startswith(b"case_id,country_iso3,year\n"):
        raise RuntimeError("frozen roster hash or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    result = {key: [] for key in CASES}
    for record in records:
        if record["case_id"] not in result:
            raise RuntimeError("unexpected case in roster")
        result[record["case_id"]].append((record["country_iso3"], int(record["year"])))
    expected = [(key, c, y) for key in CASES
                for c, y in sorted(result[key], key=lambda item: (item[1], item[0]))]
    observed = [(r["case_id"], r["country_iso3"], int(r["year"])) for r in records]
    if observed != expected or len(observed) != 2952 or len(set(observed)) != len(observed):
        raise RuntimeError("frozen roster ordering, size, or uniqueness mismatch")
    for key, case in CASES.items():
        rows = result[key]
        if len(rows) != case["key_rows"] or len({c for c, _ in rows}) != case["key_countries"]:
            raise RuntimeError(f"frozen roster envelope mismatch: {key}")
    return result


def source_keys() -> tuple[dict[tuple[str, int], float], dict[str, set[tuple[str, int]]]]:
    """Read CIT exposure values and only BERD/FDI keys and dimensions."""
    cit = pd.read_parquet(ROOT / CIT, columns=["country_iso3", "year", "value"])
    if len(cit) != 3640 or cit.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("OECD CIT key contract changed")
    if not cit.country_iso3.str.fullmatch("[A-Z]{3}").all():
        raise RuntimeError("OECD CIT contains non-ISO3 key")
    rates = {(str(c), int(y)): float(v) for c, y, v in cit.itertuples(index=False, name=None)}
    if any(not math.isfinite(v) or v < 0 or v > 100 for v in rates.values()):
        raise RuntimeError("OECD CIT has invalid statutory percentage")
    berd = pd.read_parquet(ROOT / BERD, columns=["freq", "sectperf", "unit", "geo_code", "period"])
    if len(berd) != 43474:
        raise RuntimeError("Eurostat raw row-count contract changed")
    berd = berd.loc[berd.freq.eq("A") & berd.sectperf.eq("BES") & berd.unit.eq("PC_GDP")]
    if berd.duplicated(["geo_code", "period"]).any():
        raise RuntimeError("duplicate selected Eurostat geo-period key")
    if set(berd.geo_code) - set(GEO_TO_ISO3) - SKIP_GEOS:
        raise RuntimeError("unmapped selected Eurostat geo code")
    berd_keys = {(GEO_TO_ISO3[c], int(y)) for c, y in berd[["geo_code", "period"]].itertuples(index=False, name=None)
                 if c in GEO_TO_ISO3}
    fdi = pd.read_parquet(ROOT / FDI, columns=["country_iso3", "indicator_id", "year"])
    if len(fdi) != 17556 or not fdi.indicator_id.eq("BX.KLT.DINV.WD.GD.ZS").all():
        raise RuntimeError("WDI FDI row or indicator contract changed")
    fdi = fdi.loc[fdi.country_iso3.str.fullmatch("[A-Z]{3}")]
    if fdi.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate selected WDI ISO3 country-year key")
    fdi_keys = {(str(c), int(y)) for c, y in fdi[["country_iso3", "year"]].itertuples(index=False, name=None)}
    return rates, {"berd": berd_keys, "fdi": fdi_keys}


def key_preflight() -> dict[str, Any]:
    rates, outcomes = source_keys()
    roster = load_roster()
    report = {"treatment_values_read": True, "outcome_values_read": False,
              "outcome_null_masks_read": False, "outcome_status_read": False,
              "roster_sha256": ROSTER_SHA, "cases": {}}
    for key, case in CASES.items():
        keys = outcomes[key]
        candidates = {(c, y) for c, y in rates if T_START <= y <= T_END
                      and (c, y - 1) in rates and (c, y) in keys and (c, y + HORIZON) in keys}
        counts = Counter(c for c, _ in candidates)
        chosen = sorted(((c, y) for c, y in candidates if counts[c] >= MIN_YEARS),
                        key=lambda item: (item[1], item[0]))
        if chosen != roster[key]:
            raise RuntimeError(f"source key preflight differs from roster: {key}")
        material = [(c, y) for c, y in chosen if abs(rates[(c, y)] - rates[(c, y - 1)]) >= MATERIAL_X]
        if (len(material) != case["prelock_material_rows"]
                or len({c for c, _ in material}) != case["prelock_material_countries"]):
            raise RuntimeError(f"prelocked CIT material-change count differs: {key}")
        report["cases"][key] = {"key_rows": len(chosen), "key_countries": len({c for c, _ in chosen}),
                                "t_years": [min(y for _, y in chosen), max(y for _, y in chosen)],
                                "cit_only_material_rows": len(material),
                                "cit_only_material_countries": len({c for c, _ in material})}
    return report


def lock_payload(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision,
            "sources": narrow, "key_roster": {"path": ROSTER, "sha256": ROSTER_SHA},
            "key_preflight": preflight, "outcome_values_opened_before_lock": False,
            "outcome_null_masks_opened_before_lock": False,
            "whole_fetch_manifests_copied": False}


def write_source_lock() -> None:
    revision = registration_commit()
    narrow = check_sources()
    preflight = key_preflight()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.write_text(json.dumps(lock_payload(revision, narrow, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before opening BERD/FDI outcomes")


def check_source_lock(revision: str, narrow: dict[str, Any], preflight: dict[str, Any]) -> str:
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, narrow, preflight):
        raise RuntimeError("source lock differs from preregistration, raw pins, or key preflight")
    commit = first_addition(LOCK)
    if commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock did not follow registration commit")
    committed_unchanged(LOCK, commit)
    for case in CASES.values():
        if git_output("ls-tree", "-r", "--name-only", commit, "--", run_rel(case)).strip():
            raise RuntimeError("source-lock commit already contains measured results")
    return commit


def finite_value(value: Any, bounded_percentage: bool) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(numeric) or (bounded_percentage and not 0 <= numeric <= 100):
        return None
    return numeric


def measured_panels(roster: dict[str, list[tuple[str, int]]]) -> dict[str, tuple[pd.DataFrame, dict[str, Any]]]:
    """First BERD/FDI numeric and status access; caller checked two Git commits."""
    rates, _ = source_keys()
    berd = pd.read_parquet(ROOT / BERD, columns=["freq", "sectperf", "unit", "geo_code", "period", "value"])
    berd = berd.loc[berd.freq.eq("A") & berd.sectperf.eq("BES") & berd.unit.eq("PC_GDP")]
    berd_values = {(GEO_TO_ISO3[c], int(y)): finite_value(v, True)
                   for c, y, v in berd[["geo_code", "period", "value"]].itertuples(index=False, name=None)
                   if c in GEO_TO_ISO3}
    fdi = pd.read_parquet(ROOT / FDI, columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
    fdi = fdi.loc[fdi.indicator_id.eq("BX.KLT.DINV.WD.GD.ZS")
                  & fdi.country_iso3.str.fullmatch("[A-Z]{3}")]
    fdi_values = {(str(c), int(y)): (finite_value(v, False), "" if pd.isna(s) else str(s).strip())
                  for c, y, v, s in fdi[["country_iso3", "year", "value", "obs_status"]].itertuples(index=False, name=None)}
    results = {}
    for key, case in CASES.items():
        rows = []
        dropped_invalid_or_missing = 0
        dropped_status = 0
        for country, year in roster[key]:
            x = rates[(country, year)] - rates[(country, year - 1)]
            if key == "berd":
                old, new = berd_values.get((country, year)), berd_values.get((country, year + HORIZON))
                status_bad = False
            else:
                old, old_status = fdi_values.get((country, year), (None, ""))
                new, new_status = fdi_values.get((country, year + HORIZON), (None, ""))
                status_bad = bool(old_status or new_status)
            if old is None or new is None:
                dropped_invalid_or_missing += 1
                continue
            if status_bad:
                dropped_status += 1
                continue
            rows.append({"country_iso3": country, "year": year,
                         "cit_change_pp": x, "outcome_forward_change_pp": new - old})
        panel = pd.DataFrame(rows, columns=["country_iso3", "year", "cit_change_pp", "outcome_forward_change_pp"])
        before = len(panel)
        counts = panel.country_iso3.value_counts()
        panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS)].copy()
        material = panel.cit_change_pp.abs().ge(MATERIAL_X)
        gate = {"roster_rows": len(roster[key]),
                "dropped_invalid_or_missing_endpoint_pairs": dropped_invalid_or_missing,
                "dropped_nonblank_wdi_status_pairs": dropped_status,
                "complete_pairs_before_five_year_country_floor": before,
                "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
                "material_cit_change_rows": int(material.sum()),
                "material_cit_change_countries": int(panel.loc[material, "country_iso3"].nunique()),
                "outcome_values_read_after_lock": True}
        results[key] = panel, gate
    return results


def estimate(panel: pd.DataFrame, gate: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    min_n, min_g, min_m, min_mg = case["floor"]
    if (gate["valid_rows"] < min_n or gate["valid_countries"] < min_g
            or gate["material_cit_change_rows"] < min_m
            or gate["material_cit_change_countries"] < min_mg):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "frozen complete-case or material CIT-change floor failed", "primary": None}
    model = smf.ols("outcome_forward_change_pp ~ cit_change_pp + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "fixed-effect design lacks full rank", "primary": None}
    groups = int(panel.country_iso3.nunique())
    if groups <= 1:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "insufficient country clusters", "primary": None}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country_iso3,
                                                  "use_correction": True,
                                                  "df_correction": True}, use_t=True)
    beta, se = float(fit.params["cit_change_pp"]), float(fit.bse["cit_change_pp"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite or nonpositive clustered uncertainty", "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    critical = float(student_t.ppf(0.975, groups - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"gate": gate, "verdict": "INCONCLUSIVE", "reason": "nonfinite country-cluster t inference", "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
               "confidence_level": 0.95, "confidence_interval": [beta - critical * se, beta + critical * se],
               "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
               "model_rank": int(fit.model.rank),
               "method": "country/year FE OLS, country-cluster CR1, Student t(G-1)"}
    magnitude = case["meaningful_beta"]
    if beta <= -magnitude and p <= P_MAX:
        verdict, reason = "SUPPORTED", "negative association clears frozen magnitude and Bonferroni cutoff"
    elif beta >= magnitude and p <= P_MAX:
        verdict, reason = "REFUTED", "opposite association clears frozen magnitude and Bonferroni cutoff"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason, "primary": primary}


def artifact_payload(key: str, case: dict[str, Any], result: dict[str, Any], registration: str, lock_commit: str, stamp: str) -> dict[str, Any]:
    hid, verdict, gate, primary = case["id"], result["verdict"], result["gate"], result["primary"]
    source_inputs = {role: SOURCES[role] for role in ("treatment", key)}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": hid, "path": spec_rel(case), "topic": case["topic"]},
              "preregistration": {"spec_commit": registration, "source_lock_commit": lock_commit,
                                  "family_id": FAMILY, "family_size": 2, "key_roster": ROSTER,
                                  "key_roster_sha256": ROSTER_SHA, "steelman": steelman_rel(case)},
              "reproduction": {"runner": RUNNER, "run_dir": run_rel(case),
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": source_inputs, "sample": gate}, "results": {"primary": primary},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
                   "verdict_label": verdict, "verdict_reason": result["reason"],
                   "run_utc": stamp, "runner": RUNNER,
                   "preregistration_commit": registration, "source_lock_commit": lock_commit,
                   "source_lock": LOCK, "template": "panel_fe", "preflight": gate,
                   "primary": primary, "p_max_two_sided_bonferroni": P_MAX,
                   "meaningful_beta_min_abs": case["meaningful_beta"],
                   "data_status": {"variables_missing": [], "input_vintages": list(source_inputs.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": registration, "source_lock_commit": lock_commit,
                "source_lock": LOCK, "status": verdict, "vintages": list(source_inputs.values()),
                "derived_panel": gate, "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{registration}`; source-lock commit: `{lock_commit}`.\n\n"
            f"Outcome: {case['label']}. Key-only upper bound: {case['key_rows']} country-years / "
            f"{case['key_countries']} countries. Valid complete pairs: {gate['valid_rows']} rows / "
            f"{gate['valid_countries']} countries; material CIT changes: "
            f"{gate['material_cit_change_rows']} rows / {gate['material_cit_change_countries']} countries.\n")
    if primary is not None:
        card += (f"\nPrimary beta={primary['coefficient']:+.6g} outcome percentage points "
                 f"per 1 percentage-point CIT change, country-cluster SE={primary['std_error']:.6g}, "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"95% CI={primary['confidence_interval']}.\n")
    card += (f"\nTwo prespecified tests; Bonferroni family alpha 0.01, each two-sided p <= {P_MAX}; "
             f"a beta magnitude >= {case['meaningful_beta']} is also required. "
             "Negative beta supports the directional claim. This is descriptive calibration only. "
             "No causal, policy, school, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict, "primary": primary}
    coefficients = [{"term": "cit_change_pp", **primary}] if primary is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coefficients}


def summary_text(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> str:
    lines = ["# OECD statutory CIT change to BERD and net FDI: two-test result", "",
             f"Preregistration `{registration}`; source lock `{lock_commit}`.",
             "Both prespecified tests stay in one Bonferroni family (alpha 0.01; each two-sided p <= 0.005).",
             "", "| Outcome | Verdict | Complete pairs / countries | Material CIT-change pairs / countries | Beta | Two-sided p |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.6g}" if primary is not None else "not estimated"
        p = f"{primary['p_value_two_sided']:.6g}" if primary is not None else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_cit_change_rows']} / {gate['material_cit_change_countries']} | {beta} | {p} |")
    lines += ["", "The coefficient is the two-year forward change in each outcome's GDP share per 1 percentage-point statutory CIT rate change. Negative is the preregistered direction; both outcomes share a GDP denominator. These associations are not tax-policy effects.",
              "", "Prior related tax, R&D, and FDI studies were visible. This two-test correction is local to this family. No school, policy, causal, or featured credit.", ""]
    return "\n".join(lines)


def write_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    if any((ROOT / run_rel(case)).exists() for case in CASES.values()) or (ROOT / SUMMARY).exists():
        raise FileExistsError("one or more family result artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for key, case in CASES.items():
        payload = artifact_payload(key, case, results[key], registration, lock_commit, stamp)
        folder = ROOT / run_rel(case)
        folder.mkdir(parents=True)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel(case)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(payload["card"])
        (folder / "replication.py").write_text(payload["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
        pd.DataFrame(payload["coefficients"], columns=["term", "coefficient", "std_error",
                                                       "p_value_two_sided", "confidence_level",
                                                       "confidence_interval", "n_rows", "n_countries",
                                                       "df_inference", "model_rank", "method"]).to_parquet(folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary_text(results, registration, lock_commit))


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
            raise AssertionError(f"{label}: list length mismatch")
        for i, value in enumerate(expected):
            equal_close(actual[i], value, f"{label}[{i}]")
    elif isinstance(expected, float):
        if not math.isfinite(float(actual)) or not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_artifacts(results: dict[str, dict[str, Any]], registration: str, lock_commit: str) -> None:
    for key, case in CASES.items():
        folder = ROOT / run_rel(case)
        saved = json.loads((folder / "diagnostics.json").read_text())
        payload = artifact_payload(key, case, results[key], registration, lock_commit, saved["run_utc"])
        equal_close(saved, payload["diagnostics"], f"{key}.diagnostics")
        equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), payload["manifest"], f"{key}.manifest")
        equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), payload["packet"], f"{key}.packet")
        equal_close(json.loads((folder / "chart_data.json").read_text()), payload["chart"], f"{key}.chart")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_rel(case)).read_bytes()
                or (folder / "result_card.md").read_text() != payload["card"]
                or (folder / "replication.py").read_text() != payload["wrapper"]):
            raise AssertionError(f"{key}: text artifact mismatch")
        equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                    payload["coefficients"], f"{key}.coefficients")
    if (ROOT / SUMMARY).read_text() != summary_text(results, registration, lock_commit):
        raise AssertionError("family summary differs from exact replay")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("check-sources", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    narrow = check_sources()
    if args.check_sources:
        print("OECD CIT, Eurostat BERD, and WDI FDI source SHA pins match; outcomes unopened")
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
    panels = measured_panels(load_roster())
    results = {key: estimate(*panels[key], CASES[key]) for key in CASES}
    if args.run:
        write_artifacts(results, registration, lock_commit)
        for key, result in results.items():
            print(key, result["verdict"], result["reason"])
        return 0
    verify_artifacts(results, registration, lock_commit)
    print("verified exact replay", FAMILY, {key: value["verdict"] for key, value in results.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
