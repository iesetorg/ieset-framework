#!/usr/bin/env python3
"""Frozen prospective business-R&D/resident-patenting measured test."""
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
HYPOTHESIS_ID = "business_rd_resident_patenting_forward_2026"
SPEC = f"hypotheses/growth/{HYPOTHESIS_ID}.yaml"
STEELMAN = f"hypotheses/steelman/{HYPOTHESIS_ID}.md"
RUN_DIR = f"engine/runs/{HYPOTHESIS_ID}"
PLAN = "engine/audits/business_rd_resident_patenting_prereg_2026-10-09.md"
RUNNER = "scripts/run_business_rd_resident_patenting_2026.py"
VERIFIER = "scripts/verify_business_rd_resident_patenting_2026.py"
LOCK = "data/pinned_evidence/business_rd_resident_patenting_2026.manifest.json"
FAMILY = "business_rd_selected_two_outcome_screen_2026_10_09"
FAMILY_ALPHA = 0.01
FAMILY_SIZE = 2
P_MAX = FAMILY_ALPHA / FAMILY_SIZE
START_YEAR, END_YEAR = 1995, 2021
MIN_PAIRS, MIN_COUNTRIES, MIN_YEARS, MIN_VARYING = 400, 25, 5, 15
EURO_TO_ISO3 = dict(zip(
    "AT BE BG CH CY CZ DE DK EE EL ES FI FR HR HU IE IS IT LT LU LV ME MK MT NL NO PL PT RO RS SE SI SK TR UK".split(),
    "AUT BEL BGR CHE CYP CZE DEU DNK EST GRC ESP FIN FRA HRV HUN IRL ISL ITA LTU LUX LVA MNE MKD MLT NLD NOR POL PRT ROU SRB SWE SVN SVK TUR GBR".split(),
))
COUNTRIES = frozenset(EURO_TO_ISO3.values())
if len(EURO_TO_ISO3) != 35 or len(COUNTRIES) != 35:
    raise RuntimeError("frozen 35-country roster changed")
SOURCES = {
    "business_rd": {
        "source": "eurostat:rd_e_gerdtot",
        "path": "data/vintages/eurostat/rd_e_gerdtot@2026-05-05T210242Z.parquet",
        "sha256": "fea284d7b17e31a3803749fca052f6a110ed1b8e703a9151964d1d15f58df152",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "series_id": "rd_e_gerdtot",
    },
    "resident_patents": {
        "source": "wipo:patent_applications_resident",
        "path": "data/vintages/wipo/patent_applications_resident@2026-05-19T094854Z.parquet",
        "sha256": "8affaee11a397d965f73eda762d0b3416bc341b7485e6197745700a1dd3bf24e",
        "manifest": "data/manifests/fetch_run_2026-05-19T095056Z.yaml",
        "series_id": "patent_applications_resident",
    },
    "population": {
        "source": "world_bank_wdi:SP.POP.TOTL",
        "path": "data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet",
        "sha256": "6e8ccda8b27d188d08e0fbf036828c975641453c12e6e68d5807657140cd9456",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "SP.POP.TOTL",
    },
}
SELECTOR = {"freq": "A", "sectperf": "BES", "unit": "PC_GDP"}
MEASUREMENT_LIMIT = (
    "Resident patent applications per million are filing counts, not invention quality, "
    "commercial value, or domestic innovation output; population and GDP denominators, "
    "filing practices, and R&D sector mix can move the series."
)


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not commits:
        raise RuntimeError(f"no first-addition commit: {relative}")
    return commits[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def registration_commit() -> str:
    files = [SPEC, STEELMAN, PLAN, RUNNER, VERIFIER]
    commits = {first_addition(relative) for relative in files}
    if len(commits) != 1:
        raise RuntimeError("study lacks one shared first-addition registration commit")
    revision = commits.pop()
    for relative in files:
        committed_unchanged(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN_DIR).strip():
        raise RuntimeError("registration commit contained result artifacts")
    return revision


def validate_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX, "expected_sign": "+",
        "min_observations": MIN_PAIRS, "min_countries": MIN_COUNTRIES,
        "min_pairs_per_country": MIN_YEARS, "min_varying_countries": MIN_VARYING,
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_credit": 0,
    }
    if any(threshold.get(key) != value for key, value in expected.items()):
        raise RuntimeError("frozen threshold differs from runner")
    if threshold.get("source_files") != SOURCES:
        raise RuntimeError("source pins differ from runner")
    if (spec.get("hypothesis_id") != HYPOTHESIS_ID or spec.get("status") != "pre_registered"
            or spec.get("claim_direction") != "+" or spec.get("evidence_type") != "associational"
            or spec["sample"].get("countries") != sorted(COUNTRIES)
            or spec["sample"].get("period") != [START_YEAR, END_YEAR]
            or spec.get("steelman") != STEELMAN or spec.get("covers_claims") != []
            or spec.get("linked_hypotheses") != [] or spec.get("linked_conditions") != []
            or spec["variables"]["treatment"][0]["source"] != SOURCES["business_rd"]["source"]
            or spec["variables"]["outcome"][0]["source"] != SOURCES["resident_patents"]["source"]
            or spec["variables"]["controls"][0]["source"] != SOURCES["resident_patents"]["source"]):
        raise RuntimeError("registration content differs from runner")


def check_sources() -> None:
    for role, source in SOURCES.items():
        path = ROOT / source["path"]
        if not path.is_file() or sha256(path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched raw source: {role}")
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
    validate_spec()
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
    if git("ls-tree", "-r", "--name-only", lock_revision, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit contained results")


def euro_frame(with_values: bool) -> pd.DataFrame:
    columns = [*SELECTOR, "geo_code", "period"] + (["value"] if with_values else [])
    chunks = []
    for batch in pq.ParquetFile(ROOT / SOURCES["business_rd"]["path"]).iter_batches(
            batch_size=200_000, columns=columns):
        part = batch.to_pandas()
        mask = part.geo_code.isin(EURO_TO_ISO3)
        for key, value in SELECTOR.items():
            mask &= part[key].eq(value)
        if mask.any():
            chunks.append(part.loc[mask, ["geo_code", "period"] + (["value"] if with_values else [])])
    if not chunks:
        raise RuntimeError("selected source has no country-year keys: business_rd")
    frame = pd.concat(chunks, ignore_index=True).rename(columns={"period": "year"})
    frame["country_iso3"] = frame.geo_code.map(EURO_TO_ISO3)
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    frame = frame[["country_iso3", "year"] + (["value"] if with_values else [])]
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate exact country-year-selector keys: business_rd")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def world_bank_frame(role: str, with_values: bool) -> pd.DataFrame:
    columns = ["country_iso3", "year"] + (["value", "obs_status"] if with_values else [])
    chunks = []
    for batch in pq.ParquetFile(ROOT / SOURCES[role]["path"]).iter_batches(
            batch_size=200_000, columns=columns):
        part = batch.to_pandas()
        part = part.loc[part.country_iso3.isin(COUNTRIES)]
        if len(part):
            chunks.append(part)
    if not chunks:
        raise RuntimeError(f"selected source has no country-year keys: {role}")
    frame = pd.concat(chunks, ignore_index=True)
    frame["year"] = pd.to_numeric(frame.year, errors="raise").astype(int)
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate exact country-year keys: {role}")
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
        frame["status_acceptable"] = frame.obs_status.isna() | frame.obs_status.astype(str).str.strip().eq("")
        frame = frame.drop(columns="obs_status")
    return frame


def build_panel(with_values: bool) -> pd.DataFrame:
    rd = euro_frame(with_values).rename(columns={"value": "business_rd"})
    patents = world_bank_frame("resident_patents", with_values).rename(
        columns={"value": "patent_count", "status_acceptable": "patent_status_ok"})
    population = world_bank_frame("population", with_values).rename(
        columns={"value": "population", "status_acceptable": "population_status_ok"})
    patent_intensity = patents.merge(population, on=["country_iso3", "year"], validate="one_to_one")
    future = patent_intensity.rename(columns={
        "patent_count": "future_patent_count", "population": "future_population",
        "patent_status_ok": "future_patent_status_ok", "population_status_ok": "future_population_status_ok",
    })
    future["year"] -= 3
    panel = rd.loc[rd.year.between(START_YEAR, END_YEAR)].merge(
        patent_intensity, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(future, on=["country_iso3", "year"], validate="one_to_one")
    if not with_values:
        return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(
        subset=["business_rd", "patent_count", "population", "future_patent_count", "future_population"]).copy()
    panel = panel.loc[panel.business_rd.between(0, 100)
                      & panel.patent_count.ge(0) & panel.future_patent_count.ge(0)
                      & panel.population.gt(0) & panel.future_population.gt(0)
                      & panel.patent_status_ok & panel.population_status_ok
                      & panel.future_patent_status_ok & panel.future_population_status_ok].copy()
    panel["treatment"] = panel.business_rd
    panel["baseline"] = np.log1p(1_000_000 * panel.patent_count / panel.population)
    panel["outcome"] = np.log1p(1_000_000 * panel.future_patent_count / panel.future_population) - panel.baseline
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    return panel.sort_values(["country_iso3", "year"]).reset_index(drop=True)


def key_preflight() -> dict[str, Any]:
    panel = build_panel(False)
    counts = panel.groupby("country_iso3").size()
    eligible = counts[counts >= MIN_YEARS]
    return {"upper_pairs": int(eligible.sum()), "upper_countries": int(len(eligible)),
            "values_read": False, "null_masks_checked": False,
            "key_envelope_passed": bool(eligible.sum() >= MIN_PAIRS and len(eligible) >= MIN_COUNTRIES)}


def estimate_one() -> tuple[dict[str, Any], str, str, dict[str, Any] | None]:
    panel = build_panel(True)
    varying = int((panel.groupby("country_iso3").treatment.agg(
        lambda values: values.max() - values.min()) > 1e-10).sum()) if len(panel) else 0
    gate = {
        "observations": int(len(panel)), "countries": int(panel.country_iso3.nunique()),
        "varying_countries": varying, "min_pairs_per_country": MIN_YEARS,
        "treatment_years": [int(panel.year.min()), int(panel.year.max())] if len(panel) else [],
        "passed": bool(len(panel) >= MIN_PAIRS and panel.country_iso3.nunique() >= MIN_COUNTRIES
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
    if p <= P_MAX and coefficient > 0:
        return gate, "SUPPORTED", "positive coefficient clears frozen conservative screen threshold", estimate
    if p <= P_MAX and coefficient < 0:
        return gate, "REFUTED", "negative coefficient clears frozen conservative screen threshold", estimate
    return gate, "PARTIAL", "estimable association does not clear frozen directional screen rule", estimate


def artifacts(revision: str, gate: dict[str, Any], verdict: str,
              reason: str, estimate: dict[str, Any] | None, stamp: str) -> dict[str, Any]:
    inputs = [{"role": role, **source} for role, source in SOURCES.items()]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
                  "school_score_credit": 0, "policy_score_credit": 0, "featured_eligible": False}
    limits = [
        "Descriptive country-panel association only; no causal or policy effect identified.",
        "The prior business-R&D to tertiary-employment screen was already visible as PARTIAL (p=0.507052); this selected second R&D outcome uses 0.01/2=0.005. This is no global corpus-wide multiplicity correction.",
        "Older WDI-total-R&D to patent candidate claims and WIPO-outcome studies exist; this business-sector source and forward patent-intensity change are a narrower new estimand, not an independent replication.",
        "Raw source files are hash-pinned to tracked manifests but ignored by Git; replay needs identical bytes.",
        MEASUREMENT_LIMIT,
        "Eurostat raw R&D Parquet has no retained observation-status flags; nonblank WDI-mirror status codes are excluded for patent and population levels.",
        "No school, position, policy, or featured score credit.",
    ]
    diagnostics = {
        "hypothesis_id": HYPOTHESIS_ID, "verdict": verdict, "verdict_label": verdict,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": revision, "source_lock": LOCK,
        "template": "panel_fe", "preflight": gate, "estimate": estimate,
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": limits, "correction": correction,
    }
    manifest = {"hypothesis_id": HYPOTHESIS_ID, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": revision, "source_lock": LOCK,
                "status": verdict, "vintages": inputs, "derived_panel": gate, "correction": correction}
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HYPOTHESIS_ID, "path": SPEC, "topic": "growth"},
        "preregistration": {"spec_commit": revision, "steelman": STEELMAN,
                            "family_id": FAMILY, "family_size": FAMILY_SIZE,
                            "family_alpha": FAMILY_ALPHA, "family_p_max": P_MAX},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                         "command": f"python3 {VERIFIER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
        "data": {"inputs": inputs, "n_observations": gate["observations"],
                 "n_countries": gate["countries"]},
        "results": estimate, "limitations": limits, "correction": correction,
    }
    card = (f"# Result card: {HYPOTHESIS_ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {revision}; source lock: {LOCK}.\n"
            f"Complete sample: {gate['observations']} country-year pairs, {gate['countries']} countries.\n"
            f"Conservative two-sided screen threshold: p <= {P_MAX:.6f}.\n")
    if estimate:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g}; clustered SE "
                 f"{estimate['std_error']:.6g}; p={estimate['p_value']:.6g}.\n")
    card += ("\nMeasurement boundary: " + MEASUREMENT_LIMIT
             + "\nPrevious R&D-employment screen: PARTIAL (p=0.507052), visible before registration; "
             "the second selected screen uses 0.01/2=0.005, without claiming global correction."
             "\nDescriptive calibration only; zero causal, school, policy, position, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               "raise SystemExit(subprocess.call([sys.executable, "
               f"str(root / {VERIFIER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HYPOTHESIS_ID, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None, "family_p_max": P_MAX}
    rows = [{"term": "treatment", **estimate}] if estimate else []
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart, "rows": rows}


def write_artifacts(payload: dict[str, Any]) -> None:
    folder = ROOT / RUN_DIR
    if folder.exists():
        raise FileExistsError(RUN_DIR)
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC).read_bytes())
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
    actions.add_argument("--validate-spec", action="store_true")
    actions.add_argument("--check-sources", action="store_true")
    actions.add_argument("--write-source-lock", action="store_true")
    actions.add_argument("--preflight", action="store_true")
    actions.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.validate_spec:
        validate_spec()
        print("frozen study specification matches runner and source pins")
        return 0
    if args.check_sources:
        check_sources()
        print("three vintages match tracked fetch manifests; measured columns unopened")
        return 0
    if args.write_source_lock:
        write_lock()
        print(f"wrote {LOCK}; commit separately before measured-value access")
        return 0
    revision = registration_commit()
    validate_spec()
    check_sources()
    check_lock(revision)
    if args.preflight:
        report = key_preflight()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["key_envelope_passed"] else 1
    if (ROOT / RUN_DIR).exists():
        raise FileExistsError("result already exists")
    gate, verdict, reason, estimate = estimate_one()
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    write_artifacts(artifacts(revision, gate, verdict, reason, estimate, stamp))
    print(HYPOTHESIS_ID, verdict, gate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
