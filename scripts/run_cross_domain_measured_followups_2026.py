#!/usr/bin/env python3
"""Frozen, source-pinned two-test cross-domain measured family.

Preflight reads only source dimensions and country/year keys. The value path
requires a first-addition registration commit and a later source-lock commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml


ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_cross_domain_measured_followups_2026.py"
VERIFIER = "scripts/verify_cross_domain_measured_followups_2026.py"
PLAN = "engine/audits/cross_domain_measured_followups_prereg_2026-10-09.md"
LOCK = "data/pinned_evidence/cross_domain_measured_followups_2026.manifest.json"
FAMILY = "cross_domain_measured_followups_2026_10_09"
FAMILY_P_MAX = 0.025  # two-sided Bonferroni 0.05 / 2 registered tests
MIN_YEARS = 5
MIN_VARYING = 15
PDB_COUNTRIES = frozenset((
    "AUS AUT BEL BGR CAN CHE COL CRI CZE DEU DNK ESP EST FIN FRA GBR GRC "
    "HRV HUN IRL ISL ISR ITA LTU LUX LVA MEX NLD NOR NZL POL PRT ROU SVK "
    "SVN SWE USA"
).split())
EURO_TO_ISO3 = dict(zip(
    "AT BE BG CH CY CZ DE DK EE EL ES FI FR HR HU IS IT LT LU LV ME MK MT NL NO PL PT RO SE SI SK".split(),
    "AUT BEL BGR CHE CYP CZE DEU DNK EST GRC ESP FIN FRA HRV HUN ISL ITA LTU LUX LVA MNE MKD MLT NLD NOR POL PRT ROU SWE SVN SVK".split(),
))
EURO_COUNTRIES = frozenset(EURO_TO_ISO3.values())
if len(PDB_COUNTRIES) != 37 or len(EURO_TO_ISO3) != 31 or len(EURO_COUNTRIES) != 31:
    raise RuntimeError("frozen country roster changed")

SOURCES = {
    "pdb": {
        "source": "oecd:DSD_PDB",
        "path": "data/vintages/oecd/DSD_PDB@2026-05-19T094612Z.parquet",
        "sha256": "3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c",
        "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
        "series_id": "DSD_PDB",
    },
    "manufactured_share": {
        "source": "world_bank_wdi:TX.VAL.MANF.ZS.UN",
        "path": "data/vintages/world_bank_wdi/TX.VAL.MANF.ZS.UN@2026-04-30T115209Z.parquet",
        "sha256": "c5077c18a1ba1b953bc1cd66ac980f36b5cda7568fc3749126b91587cf17c98b",
        "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml",
        "series_id": "TX.VAL.MANF.ZS.UN",
    },
    "immigration": {
        "source": "eurostat:migr_imm1ctz",
        "path": "data/vintages/eurostat/migr_imm1ctz@2026-05-05T205902Z.parquet",
        "sha256": "b0b178278dd7d1ef68d4a03188e496b580d3e30b61f9fa21c7db13ed547bfeb1",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "series_id": "migr_imm1ctz",
    },
    "population": {
        "source": "eurostat:demo_pjan",
        "path": "data/vintages/eurostat/demo_pjan@2026-05-05T205848Z.parquet",
        "sha256": "c0910d085947e1c95da781ea3679f79909f41cab5c2cf5731db4e8fcf415f3e3",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "series_id": "demo_pjan",
    },
    "gini": {
        "source": "eurostat:ilc_di12",
        "path": "data/vintages/eurostat/ilc_di12@2026-07-23T154401Z.parquet",
        "sha256": "9b1b03caebf74bf79ad77d5373b04841002ea80c017ff6e3cca884485a8adfa6",
        "manifest": "data/manifests/fetch_run_2026-07-23T154936Z.yaml",
        "series_id": "ilc_di12",
    },
}
TESTS = {
    "manufacturing_ulc_export_composition_forward_2026": {
        "topic": "trade", "treatment": "pdb", "outcome": "manufactured_share",
        "countries": PDB_COUNTRIES, "period": (1995, 2021),
        "min_observations": 400, "min_countries": 20, "sign": "-",
        "measurement_limit": (
            "Manufactures are a share of merchandise export value, so commodity-price "
            "denominators, exchange rates, and demand can move the outcome without "
            "a manufacturing-volume change."
        ),
    },
    "foreign_arrivals_disposable_gini_bracket_2026": {
        "topic": "distribution", "treatment": "immigration", "outcome": "gini",
        "countries": EURO_COUNTRIES, "period": (2014, 2023),
        "min_observations": 180, "min_countries": 25, "sign": "+",
        "measurement_limit": (
            "FOR_STLS means foreign-country and stateless arrivals, not foreign-born "
            "or net migration; EU-SILC survey timing and all-resident Gini do not "
            "identify immigrant-specific distributional effects."
        ),
    },
}
PDB_KEYS = ["REF_AREA", "FREQ", "MEASURE", "ACTIVITY", "UNIT_MEASURE", "PRICE_BASE",
            "TRANSFORMATION", "ASSET_CODE", "CONVERSION_TYPE", "period"]
PDB_FILTER = {"FREQ": "A", "MEASURE": "ULCH", "ACTIVITY": "C", "UNIT_MEASURE": "XDC",
              "PRICE_BASE": "V", "TRANSFORMATION": "GY", "ASSET_CODE": "_Z", "CONVERSION_TYPE": "_Z"}
EURO_SELECTORS = {
    "immigration": {"freq": "A", "citizen": "FOR_STLS", "agedef": "REACH", "age": "TOTAL", "unit": "NR", "sex": "T"},
    "population": {"freq": "A", "age": "TOTAL", "sex": "T", "unit": "NR"},
    "gini": {"freq": "A", "age": "TOTAL", "statinfo": "GINI_HND"},
}


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def first_addition(relative: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no first-addition commit: {relative}")
    return revisions[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def paths(hypothesis_id: str) -> tuple[str, str, str]:
    topic = TESTS[hypothesis_id]["topic"]
    return (f"hypotheses/{topic}/{hypothesis_id}.yaml",
            f"hypotheses/steelman/{hypothesis_id}.md", f"engine/runs/{hypothesis_id}")


def registration_commit() -> str:
    files = [RUNNER, VERIFIER, PLAN]
    for hypothesis_id in TESTS:
        spec, steelman, _ = paths(hypothesis_id)
        files.extend([spec, steelman])
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("family lacks one shared first-addition registration commit")
    revision = revisions.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    for hypothesis_id in TESTS:
        if git("ls-tree", "-r", "--name-only", revision, "--", paths(hypothesis_id)[2]).strip():
            raise RuntimeError("registration commit contained result artifacts")
    return revision


def validate_specs() -> None:
    for hypothesis_id, config in TESTS.items():
        spec_rel, steelman_rel, _ = paths(hypothesis_id)
        spec = yaml.safe_load((ROOT / spec_rel).read_text())
        threshold = spec["falsification"]["threshold"]
        expected = {
            "family_id": FAMILY, "family_size": 2, "family_alpha": 0.05,
            "family_p_max": FAMILY_P_MAX, "expected_sign": config["sign"],
            "min_observations": config["min_observations"],
            "min_countries": config["min_countries"],
            "min_pairs_per_country": MIN_YEARS, "min_varying_countries": MIN_VARYING,
            "school_score_eligible": False, "school_score_credit": 0,
            "policy_score_credit": 0,
        }
        if any(threshold.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"frozen threshold mismatch: {hypothesis_id}")
        if threshold.get("source_files") != SOURCES:
            raise RuntimeError(f"source pins differ from runner: {hypothesis_id}")
        if (spec.get("hypothesis_id") != hypothesis_id or spec.get("status") != "pre_registered"
                or spec.get("claim_direction") != config["sign"]
                or spec.get("evidence_type") != "associational"
                or spec["sample"].get("countries") != sorted(config["countries"])
                or spec["sample"].get("period") != list(config["period"])
                or spec.get("steelman") != steelman_rel or spec.get("covers_claims") != []
                or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []):
            raise RuntimeError(f"registration content mismatch: {hypothesis_id}")
        if (spec["variables"]["treatment"][0]["source"] != SOURCES[config["treatment"]]["source"]
                or spec["variables"]["outcome"][0]["source"] != SOURCES[config["outcome"]]["source"]):
            raise RuntimeError(f"registered source pair mismatch: {hypothesis_id}")


def check_sources() -> None:
    for role, source in SOURCES.items():
        path = ROOT / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched source: {role}")
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        rows = [entry for entry in manifest["entries"]
                if entry.get("parquet_path") == source["path"] and entry.get("series_id") == source["series_id"]]
        if len(rows) != 1 or rows[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"tracked fetch manifest does not custody {role}")


def lock_payload(revision: str) -> dict[str, Any]:
    return {"family_id": FAMILY, "preregistration_commit": revision, "sources": SOURCES,
            "note": "Exact fetched vintages locked after registration and before measured-column access."}


def write_lock() -> None:
    revision = registration_commit()
    validate_specs()
    check_sources()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(lock_payload(revision), indent=2, sort_keys=True) + "\n")


def check_lock(revision: str) -> None:
    target = ROOT / LOCK
    if json.loads(target.read_text()) != lock_payload(revision):
        raise RuntimeError("source lock differs from frozen pins")
    lock_revision = first_addition(LOCK)
    if lock_revision == revision:
        raise RuntimeError("source lock was not a separate later commit")
    committed_unchanged(LOCK, lock_revision)
    for hypothesis_id in TESTS:
        if git("ls-tree", "-r", "--name-only", lock_revision, "--", paths(hypothesis_id)[2]).strip():
            raise RuntimeError("source-lock commit contained result artifacts")


def pdb_frame(with_values: bool) -> pd.DataFrame:
    frame = pd.read_parquet(ROOT / SOURCES["pdb"]["path"],
                            columns=PDB_KEYS + (["value"] if with_values else []))
    for key, value in PDB_FILTER.items():
        frame = frame.loc[frame[key].eq(value)]
    frame = frame.rename(columns={"REF_AREA": "country_iso3", "period": "year"})
    frame = frame.loc[frame.country_iso3.isin(PDB_COUNTRIES),
                      ["country_iso3", "year"] + (["value"] if with_values else [])].copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate exact PDB country-year-measure keys")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def manufactured_share_frame(with_values: bool) -> pd.DataFrame:
    frame = pd.read_parquet(ROOT / SOURCES["manufactured_share"]["path"],
                            columns=["country_iso3", "year"] + (["value"] if with_values else []))
    frame = frame.loc[frame.country_iso3.isin(PDB_COUNTRIES)].copy()
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate WDI country-year keys")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def euro_frame(role: str, with_values: bool) -> pd.DataFrame:
    selector = EURO_SELECTORS[role]
    columns = [*selector, "geo_code", "period"] + (["value"] if with_values else [])
    chunks = []
    for batch in pq.ParquetFile(ROOT / SOURCES[role]["path"]).iter_batches(
            batch_size=200_000, columns=columns):
        part = batch.to_pandas()
        mask = part.geo_code.isin(EURO_TO_ISO3)
        for key, value in selector.items():
            mask &= part[key].eq(value)
        if mask.any():
            chunks.append(part.loc[mask, ["geo_code", "period"] + (["value"] if with_values else [])])
    if not chunks:
        raise RuntimeError(f"selected Eurostat source has no country-year keys: {role}")
    frame = pd.concat(chunks, ignore_index=True).rename(columns={"period": "year"})
    frame["country_iso3"] = frame.geo_code.map(EURO_TO_ISO3)
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    frame = frame[["country_iso3", "year"] + (["value"] if with_values else [])]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate exact Eurostat country-year-selector keys: {role}")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def build_panel(hypothesis_id: str, with_values: bool) -> pd.DataFrame:
    config = TESTS[hypothesis_id]
    start, end = config["period"]
    if hypothesis_id == "manufacturing_ulc_export_composition_forward_2026":
        cost = pdb_frame(with_values).rename(columns={"value": "unit_cost_growth"})
        baseline = manufactured_share_frame(with_values).rename(columns={"value": "baseline_share"})
        future = manufactured_share_frame(with_values).rename(columns={"value": "future_share"})
        future["year"] -= 3
        panel = cost.loc[cost.year.between(start, end)].merge(
            baseline, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    else:
        arrivals = euro_frame("immigration", with_values).rename(columns={"value": "arrivals"})
        population = euro_frame("population", with_values).rename(columns={"value": "population"})
        baseline = euro_frame("gini", with_values).rename(columns={"value": "baseline_gini"})
        future = euro_frame("gini", with_values).rename(columns={"value": "future_gini"})
        future["year"] -= 2
        panel = arrivals.loc[arrivals.year.between(start, end)].merge(
            population, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel.merge(baseline, on=["country_iso3", "year"], validate="one_to_one")
        panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    if not with_values:
        return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    value_cols = [name for name in panel if name not in {"country_iso3", "year"}]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=value_cols).copy()
    if hypothesis_id == "manufacturing_ulc_export_composition_forward_2026":
        panel = panel.loc[panel.baseline_share.between(0, 100) & panel.future_share.between(0, 100)].copy()
        panel["treatment"] = panel.unit_cost_growth
        panel["outcome"] = panel.future_share - panel.baseline_share
        panel["baseline"] = panel.baseline_share
    else:
        panel = panel.loc[(panel.arrivals >= 0) & (panel.population > 0)
                          & panel.baseline_gini.between(0, 100)
                          & panel.future_gini.between(0, 100)].copy()
        panel["treatment"] = 1000 * panel.arrivals / panel.population
        panel["outcome"] = panel.future_gini - panel.baseline_gini
        panel["baseline"] = panel.baseline_gini
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=["treatment", "outcome", "baseline"])
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def key_preflight() -> dict[str, dict[str, Any]]:
    output = {}
    for hypothesis_id, config in TESTS.items():
        panel = build_panel(hypothesis_id, False)
        counts = panel.groupby("country_iso3").size()
        eligible = counts[counts >= MIN_YEARS]
        output[hypothesis_id] = {
            "upper_pairs": int(eligible.sum()), "upper_countries": int(len(eligible)),
            "values_read": False, "null_masks_checked": False,
            "key_envelope_passed": bool(eligible.sum() >= config["min_observations"]
                                        and len(eligible) >= config["min_countries"]),
        }
    return output


def estimate_one(hypothesis_id: str) -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    config = TESTS[hypothesis_id]
    panel = build_panel(hypothesis_id, True)
    varying = int((panel.groupby("country_iso3").treatment.agg(
        lambda values: values.max() - values.min()) > 1e-10).sum()) if len(panel) else 0
    gate = {
        "observations": int(len(panel)), "countries": int(panel.country_iso3.nunique()),
        "varying_countries": varying, "min_pairs_per_country": MIN_YEARS,
        "treatment_years": [int(panel.year.min()), int(panel.year.max())] if len(panel) else [],
        "passed": bool(len(panel) >= config["min_observations"]
                       and panel.country_iso3.nunique() >= config["min_countries"]
                       and varying >= MIN_VARYING),
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE", "registered complete-case or treatment-variation floor failed", None
    fit = smf.ols("outcome ~ treatment + baseline + C(country_iso3) + C(year)", data=panel).fit(
        cov_type="cluster", cov_kwds={"groups": panel.country_iso3, "use_correction": True}, use_t=False)
    if fit.model.rank != fit.model.exog.shape[1]:
        return gate, "INCONCLUSIVE", "registered fixed-effect design is rank deficient", None
    coefficient = float(fit.params["treatment"])
    se = float(fit.bse["treatment"])
    p = float(fit.pvalues["treatment"])
    ci = [float(value) for value in fit.conf_int().loc["treatment"]]
    r2 = float(fit.rsquared)
    if not all(math.isfinite(value) for value in (coefficient, se, p, r2, *ci)) or se <= 0 or not 0 <= p <= 1:
        return gate, "INCONCLUSIVE", "nonfinite or unidentified clustered estimate", None
    estimate = {"coefficient": coefficient, "std_error": se, "p_value": p, "ci95": ci,
                "n_obs": gate["observations"], "n_countries": gate["countries"], "r_squared": r2,
                "method": "country/year fixed-effect OLS; country-clustered normal-Wald standard errors"}
    matches = (coefficient < 0) if config["sign"] == "-" else (coefficient > 0)
    if p <= FAMILY_P_MAX and matches:
        return gate, "SUPPORTED", "declared-sign coefficient clears frozen two-test family threshold", estimate
    if p <= FAMILY_P_MAX and not matches and coefficient != 0:
        return gate, "REFUTED", "opposite-sign coefficient clears frozen two-test family threshold", estimate
    return gate, "PARTIAL", "estimable association does not clear frozen directional family rule", estimate


def artifacts(hypothesis_id: str, revision: str, gate: dict[str, Any], verdict: str,
              reason: str, estimate: dict[str, Any] | None, stamp: str) -> dict[str, Any]:
    config = TESTS[hypothesis_id]
    spec_rel, steelman_rel, run_rel = paths(hypothesis_id)
    inputs = [{"role": role, **source} for role, source in SOURCES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "policy_score_credit": 0, "featured_eligible": False}
    limitations = [
        "Descriptive country-panel association only; no causal or policy effect identified.",
        "Two registered cross-domain tests share a fixed two-sided Bonferroni p<=0.025 rule; neither inherits an old verdict.",
        "Prior related source results were visible before registration; no global study independence is claimed.",
        "Raw source files are hash-pinned to tracked fetch manifests but ignored by Git; replay needs identical bytes.",
        config["measurement_limit"],
        "No school, position, policy, or featured score credit.",
    ]
    diagnostics = {
        "hypothesis_id": hypothesis_id, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "estimate": estimate,
        "family_id": FAMILY, "family_size": 2, "family_p_max": FAMILY_P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limitations, "correction": correction,
    }
    manifest = {
        "hypothesis_id": hypothesis_id, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock": LOCK,
        "status": verdict, "vintages": inputs, "derived_panel": gate, "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hypothesis_id, "path": spec_rel, "topic": config["topic"]},
        "preregistration": {"spec_commit": revision, "steelman": steelman_rel,
                            "family_id": FAMILY, "family_p_max": FAMILY_P_MAX},
        "reproduction": {"runner": RUNNER, "run_dir": run_rel,
                         "command": f"python3 {VERIFIER} --verify {hypothesis_id}"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "n_observations": gate["observations"],
                 "n_countries": gate["countries"]},
        "results": estimate, "limitations": limitations, "correction": correction,
    }
    card = (f"# Result card: {hypothesis_id}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {revision}; source lock: {LOCK}.\n"
            f"Complete sample: {gate['observations']} country-year pairs, {gate['countries']} countries.\n"
            f"Family threshold: two-sided p <= {FAMILY_P_MAX:.6f} across two tests.\n")
    if estimate:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; clustered SE "
                 f"{estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += "\nMeasurement boundary: " + config["measurement_limit"] + "\nDescriptive calibration only; zero causal, school, policy, position, or featured credit.\n"
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               "raise SystemExit(subprocess.call([sys.executable, "
               f"str(root / {VERIFIER!r}), '--verify', {hypothesis_id!r}], cwd=root))\n")
    chart = {"hypothesis_id": hypothesis_id, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None, "family_p_max": FAMILY_P_MAX}
    rows = [{"term": "treatment", **estimate}] if estimate else []
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart, "rows": rows}


def write_artifacts(hypothesis_id: str, payload: dict[str, Any]) -> None:
    spec_rel, _, run_rel = paths(hypothesis_id)
    folder = ROOT / run_rel
    if folder.exists():
        raise FileExistsError(run_rel)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / spec_rel).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["rows"], columns=["term", "coefficient", "std_error", "p_value",
                                                "ci95", "n_obs", "n_countries", "r_squared", "method"]).to_parquet(
                                                    folder / "coefficients.parquet", index=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--validate-specs", action="store_true")
    actions.add_argument("--check-sources", action="store_true")
    actions.add_argument("--write-source-lock", action="store_true")
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.validate_specs:
        validate_specs()
        print("two frozen study specifications match runner and source pins")
        return 0
    if args.check_sources:
        check_sources()
        print("five vintages match tracked fetch manifests; measured columns unopened")
        return 0
    if args.write_source_lock:
        write_lock()
        print(f"wrote {LOCK}; commit separately before measured-value access")
        return 0
    revision = registration_commit()
    validate_specs()
    check_sources()
    check_lock(revision)
    if args.preflight:
        report = key_preflight()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if all(item["key_envelope_passed"] for item in report.values()) else 1
    if any((ROOT / paths(hypothesis_id)[2]).exists() for hypothesis_id in TESTS):
        raise FileExistsError("a family result already exists")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payloads = {}
    for hypothesis_id in TESTS:
        gate, verdict, reason, estimate = estimate_one(hypothesis_id)
        payloads[hypothesis_id] = artifacts(hypothesis_id, revision, gate, verdict, reason, estimate, stamp)
    for hypothesis_id, payload in payloads.items():
        write_artifacts(hypothesis_id, payload)
        print(hypothesis_id, payload["diagnostics"]["verdict"], payload["diagnostics"]["preflight"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
