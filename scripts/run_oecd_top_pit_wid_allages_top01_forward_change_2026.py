#!/usr/bin/env python3
"""Frozen, source-custodied descriptive OECD/WID forward-change screen."""
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
import pyarrow.dataset as ds
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
from scipy.stats import t as student_t
import yaml


ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_top_pit_wid_allages_top01_forward_change_2026"
SPEC = f"hypotheses/distribution/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
RUNNER = f"scripts/run_{ID}.py"
LOCK = "data/pinned_evidence/oecd_top_pit_wid_allages_2026.manifest.json"
RUN_DIR = f"engine/runs/{ID}"
FAMILY = "selected_top_pit_wid_inequality_2026_10_09"
FAMILY_SIZE, FAMILY_ALPHA, P_MAX = 10, 0.05, 0.005
START, END = 2001, 2023
MIN_ROWS, MIN_COUNTRIES, MIN_YEARS = 550, 25, 15
MIN_CHANGES, MIN_CHANGE_COUNTRIES = 20, 10
WID_VARIABLE, WID_PERCENTILE = "sptincj999", "p99.9p100"
WID_FETCHER = "data/fetchers/wid.py"
WID_FETCHER_SHA = "301e10d90f3e5828d9e38de145510787890b6798bd41c815dba4da50f2c1446c"
# Frozen WID ISO2 to OECD ISO3 crosswalk. In particular GR/GB are GRC/GBR.
ISO2_TO_3 = dict(zip(
    "AU AT BE CA CH CL CO CZ DE DK ES EE FI FR GB GR IE IL IT JP KR MX NL NO NZ PL PT SE TR US".split(),
    "AUS AUT BEL CAN CHE CHL COL CZE DEU DNK ESP EST FIN FRA GBR GRC IRL ISR ITA JPN KOR MEX NLD NOR NZL POL PRT SWE TUR USA".split(),
))
COUNTRIES = tuple(sorted(ISO2_TO_3.values()))
if len(ISO2_TO_3) != 30 or len(set(COUNTRIES)) != 30:
    raise RuntimeError("frozen country crosswalk changed")
SOURCES = {
    "top_pit": {
        "source": "oecd:oecd_top_statutory_pit_rate",
        "path": "data/vintages/oecd/oecd_top_statutory_pit_rate@2026-07-23T153857Z.parquet",
        "sha256": "b500bdc808385c17ace3eb6d78b5698a02dadd28943daf5e7d198d9093f19151",
        "manifest": "data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml",
        "manifest_sha256": "6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18",
        "series_id": "oecd_top_statutory_pit_rate",
    },
    "wid_raw": {
        "source": "wid:wid_all",
        "path": "data/vintages/wid/wid_all@2026-05-05T204054Z.parquet",
        "sha256": "d7a676b332bc7c12f4c48305fc8906c0bd990818d5bc841e266336ac212c1702",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
        "series_id": "wid_all",
    },
}
CORRECTION = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "causal_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Historical, prospectively specified association; neither a causal tax effect nor an independent holdout.",
    "OECD TS_PIT is a combined top statutory rate on gross wage earnings, not the effective tax burden of the WID top 0.1 percent.",
    "WID sptincj999 is the all-ages equal-split pre-tax national-income share; it is not the adult, post-tax, disposable-income, or household-survey series.",
    "Fiscal-record reporting and income timing can change with tax schedules; time-varying reforms and macro shocks can confound the association.",
    "The p<=0.005 rule reserves one of ten local Bonferroni slots; it is not a correction across the whole IESET corpus.",
    "Source Parquet bytes are hash-pinned to tracked fetch manifests but are ignored by Git; replay requires the same bytes.",
    "Zero school, policy, position, and featured credit.",
]


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
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return revisions[-1]


def unchanged_in_first_commit(relative: str, revision: str) -> None:
    if not (ROOT / relative).is_file() or (ROOT / relative).read_bytes() != git("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from first-addition commit: {relative}")
    if git("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted frozen file: {relative}")


def registration_commit() -> str:
    files = [SPEC, STEELMAN, RUNNER]
    revisions = {first_addition(relative) for relative in files}
    if len(revisions) != 1:
        raise RuntimeError("spec, steelman, and runner need one shared first-addition commit")
    revision = revisions.pop()
    for relative in files:
        unchanged_in_first_commit(relative, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK, RUN_DIR).strip():
        raise RuntimeError("registration commit included source lock or result")
    return revision


def validate_spec() -> None:
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX, "expected_sign": "-", "min_observations": MIN_ROWS,
        "min_countries": MIN_COUNTRIES, "min_pairs_per_country": MIN_YEARS,
        "min_nonzero_rate_changes": MIN_CHANGES, "min_rate_change_countries": MIN_CHANGE_COUNTRIES,
        "school_score_eligible": False, "school_score_credit": 0,
        "policy_score_eligible": False, "policy_score_credit": 0, "causal_credit": 0,
        "wid_variable": WID_VARIABLE, "wid_percentile": WID_PERCENTILE,
        "wid_fetcher_priority": ["sptincj999", "sptincj992"],
        "wid_fetcher_sha256": WID_FETCHER_SHA, "source_files": SOURCES,
    }
    if threshold != expected:
        raise RuntimeError("frozen threshold differs from runner")
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational" or spec.get("claim_direction") != "-"
            or spec["sample"].get("countries") != list(COUNTRIES)
            or spec["sample"].get("period") != [START, END]
            or spec["variables"]["controls"] != []
            or spec["variables"]["treatment"][0]["source"] != SOURCES["top_pit"]["source"]
            or spec["variables"]["outcome"][0]["source"] != SOURCES["wid_raw"]["source"]
            or spec["estimator"]["template"] != "panel_fe"
            or spec["estimator"]["fixed_effects"] != ["country", "year"]
            or spec["estimator"]["clustering"] != "country"
            or spec.get("steelman") != STEELMAN
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != []):
        raise RuntimeError("registration content differs from runner")
    if P_MAX > FAMILY_ALPHA / FAMILY_SIZE:
        raise RuntimeError("multiplicity cutoff too permissive")


def check_sources() -> None:
    for role, source in SOURCES.items():
        source_path = ROOT / source["path"]
        manifest_path = ROOT / source["manifest"]
        if not source_path.is_file() or sha256(source_path) != source["sha256"]:
            raise RuntimeError(f"missing or mismatched raw source: {role}")
        if sha256(manifest_path) != source["manifest_sha256"]:
            raise RuntimeError(f"mismatched tracked fetch manifest: {role}")
        rows = [row for row in yaml.safe_load(manifest_path.read_text())["entries"]
                if row.get("series_id") == source["series_id"] and row.get("parquet_path") == source["path"]]
        if len(rows) != 1 or rows[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"fetch manifest does not custody exact series: {role}")
    if sha256(ROOT / WID_FETCHER) != WID_FETCHER_SHA:
        raise RuntimeError("WID selector fetcher differs from pinned revision")
    fetcher = (ROOT / WID_FETCHER).read_text()
    if '"variables": ["sptincj999", "sptincj992"]' not in fetcher or '"percentile": "p99.9p100"' not in fetcher:
        raise RuntimeError("WID fetcher no longer documents frozen priority and percentile")


def source_frame(role: str, with_values: bool) -> pd.DataFrame:
    path = ROOT / SOURCES[role]["path"]
    if role == "top_pit":
        columns = ["country_iso3", "year"] + (["value"] if with_values else [])
        frame = pq.read_table(path, columns=columns).to_pandas()
        frame = frame.loc[frame.country_iso3.isin(COUNTRIES) & frame.year.between(START - 1, END + 1)].copy()
    else:
        fields = ["country", "variable", "percentile", "year"] + (["value"] if with_values else [])
        dataset = ds.dataset(path, format="parquet")
        predicate = (ds.field("country").isin(list(ISO2_TO_3))
                     & (ds.field("variable") == WID_VARIABLE)
                     & (ds.field("percentile") == WID_PERCENTILE)
                     & (ds.field("year") >= START - 1)
                     & (ds.field("year") <= END + 1))
        frame = dataset.to_table(columns=fields, filter=predicate).to_pandas()
        if frame.empty:
            raise RuntimeError("WID exact-selector country-year keys absent")
        frame["country_iso3"] = frame.country.map(ISO2_TO_3)
        frame = frame.drop(columns=["country", "variable", "percentile"])
    if frame.empty:
        raise RuntimeError(f"selected source has no country-year keys: {role}")
    frame["year"] = pd.to_numeric(frame.year, errors="raise")
    if not np.isfinite(frame.year.to_numpy(dtype=float)).all() or not (frame.year % 1 == 0).all():
        raise RuntimeError(f"invalid calendar-year keys: {role}")
    frame["year"] = frame.year.astype(int)
    if frame.country_iso3.isna().any() or frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"unmapped or duplicate exact country-year keys: {role}")
    frame = frame.sort_values(["country_iso3", "year"]).reset_index(drop=True)
    if with_values:
        frame["value"] = pd.to_numeric(frame.value, errors="coerce")
    return frame


def key_preflight() -> dict[str, Any]:
    pit = source_frame("top_pit", False)
    wid = source_frame("wid_raw", False)
    expected = {(country, year) for country in COUNTRIES for year in range(START - 1, END + 2)}
    pit_keys = set(map(tuple, pit[["country_iso3", "year"]].itertuples(index=False, name=None)))
    wid_keys = set(map(tuple, wid[["country_iso3", "year"]].itertuples(index=False, name=None)))
    model_keys = {(country, year) for country in COUNTRIES for year in range(START, END + 1)
                  if (country, year - 1) in pit_keys and (country, year) in pit_keys
                  and (country, year) in wid_keys and (country, year + 1) in wid_keys}
    canonical = json.dumps(sorted(model_keys), separators=(",", ":"))
    return {
        "oecd_level_keys": len(pit_keys), "wid_all_ages_level_keys": len(wid_keys),
        "expected_level_keys_per_source": len(expected),
        "missing_oecd_level_keys": len(expected - pit_keys),
        "missing_wid_level_keys": len(expected - wid_keys),
        "model_keys": len(model_keys), "expected_model_keys": len(COUNTRIES) * (END - START + 1),
        "model_key_sha256": hashlib.sha256(canonical.encode()).hexdigest(),
        "values_read": False, "null_masks_checked": False,
        "key_envelope_passed": pit_keys == expected and wid_keys == expected
                              and len(model_keys) == len(COUNTRIES) * (END - START + 1),
    }


def lock_payload(revision: str) -> dict[str, Any]:
    return {
        "preregistration_commit": revision, "family_id": FAMILY, "family_size": FAMILY_SIZE,
        "family_p_max": P_MAX, "sources": SOURCES, "wid_fetcher": {"path": WID_FETCHER,
        "sha256": WID_FETCHER_SHA, "variable": WID_VARIABLE,
        "percentile": WID_PERCENTILE, "population": "all ages", "priority": ["sptincj999", "sptincj992"]},
        "wid_iso2_to_oecd_iso3": ISO2_TO_3, "treatment_years": [START, END],
        "key_preflight": key_preflight(),
        "note": "Value-blind exact vintage and key lock; no treatment/outcome values or null masks inspected.",
    }


def write_lock() -> None:
    revision = registration_commit()
    validate_spec()
    check_sources()
    target = ROOT / LOCK
    if target.exists():
        raise FileExistsError(LOCK)
    payload = lock_payload(revision)
    if not payload["key_preflight"]["key_envelope_passed"]:
        raise RuntimeError("source key envelope failed; cannot lock this design")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def check_lock(revision: str) -> None:
    target = ROOT / LOCK
    if not target.is_file() or json.loads(target.read_text()) != lock_payload(revision):
        raise RuntimeError("source lock differs from frozen source and key custody")
    lock_revision = first_addition(LOCK)
    if lock_revision == revision:
        raise RuntimeError("source lock was not separately committed after registration")
    if subprocess.run(["git", "merge-base", "--is-ancestor", revision, lock_revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock does not descend from registration")
    unchanged_in_first_commit(LOCK, lock_revision)
    if git("ls-tree", "-r", "--name-only", lock_revision, "--", RUN_DIR).strip():
        raise RuntimeError("source-lock commit included result artifacts")


def build_panel() -> pd.DataFrame:
    pit = source_frame("top_pit", True).rename(columns={"value": "rate_t"})
    pit_lag = pit.rename(columns={"rate_t": "rate_t_minus_1"}).copy()
    pit_lag["year"] += 1
    wid = source_frame("wid_raw", True).rename(columns={"value": "share_t"})
    wid_next = wid.rename(columns={"share_t": "share_t_plus_1"}).copy()
    wid_next["year"] -= 1
    panel = pit.loc[pit.year.between(START, END)].merge(pit_lag, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(wid, on=["country_iso3", "year"], validate="one_to_one")
    panel = panel.merge(wid_next, on=["country_iso3", "year"], validate="one_to_one")
    levels = ["rate_t", "rate_t_minus_1", "share_t", "share_t_plus_1"]
    panel = panel.replace([np.inf, -np.inf], np.nan).dropna(subset=levels).copy()
    panel = panel.loc[panel.rate_t.between(0, 100) & panel.rate_t_minus_1.between(0, 100)
                      & panel.share_t.between(0, 1) & panel.share_t_plus_1.between(0, 1)].copy()
    panel["treatment"] = panel.rate_t - panel.rate_t_minus_1
    panel["outcome"] = 100.0 * (panel.share_t_plus_1 - panel.share_t)
    counts = panel.groupby("country_iso3").size()
    panel = panel.loc[panel.country_iso3.isin(counts[counts >= MIN_YEARS].index)].copy()
    return panel[["country_iso3", "year", "treatment", "outcome"]].sort_values(
        ["country_iso3", "year"]).reset_index(drop=True)


def estimate_one() -> tuple[dict[str, Any], str, str, dict[str, Any] | None, pd.DataFrame]:
    panel = build_panel()
    changed = panel.loc[panel.treatment.ne(0)]
    gate = {
        "observations": len(panel), "countries": int(panel.country_iso3.nunique()),
        "treatment_years": [int(panel.year.min()), int(panel.year.max())] if len(panel) else [],
        "nonzero_rate_changes": len(changed), "rate_change_countries": int(changed.country_iso3.nunique()),
        "minimum_pairs_per_country": MIN_YEARS,
        "passed": bool(len(panel) >= MIN_ROWS and panel.country_iso3.nunique() >= MIN_COUNTRIES
                       and len(changed) >= MIN_CHANGES
                       and changed.country_iso3.nunique() >= MIN_CHANGE_COUNTRIES),
    }
    if not gate["passed"]:
        return gate, "INCONCLUSIVE_DATA_PENDING", "registered complete-case or exposure-change floor failed", None, panel
    try:
        fit = smf.ols("outcome ~ treatment + C(country_iso3) + C(year)", data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel.country_iso3, "use_correction": True}, use_t=False)
        if fit.model.rank != fit.model.exog.shape[1]:
            raise ValueError("registered fixed-effect design is rank deficient")
        coefficient, se = float(fit.params["treatment"]), float(fit.bse["treatment"])
        df_clusters = gate["countries"] - 1
        p = float(2 * student_t.sf(abs(coefficient / se), df=df_clusters))
        radius = float(student_t.ppf(0.975, df=df_clusters) * se)
        ci = [coefficient - radius, coefficient + radius]
        r2 = float(fit.rsquared)
        if not all(math.isfinite(v) for v in (coefficient, se, p, r2, *ci)) or se <= 0 or not 0 <= p <= 1:
            raise ValueError("nonfinite or unidentified clustered estimate")
    except (ValueError, KeyError, np.linalg.LinAlgError) as exc:
        return gate, "INCONCLUSIVE_DATA_PENDING", f"registered estimator failed: {exc}", None, panel
    estimate = {"coefficient": coefficient, "std_error": se, "p_value": p, "ci95": ci,
                "r_squared": r2, "n_obs": len(panel), "n_countries": gate["countries"],
                "df_clusters": df_clusters,
                "method": "country and treatment-year fixed-effect OLS; country-clustered Student-t inference with G-1 df"}
    if p <= P_MAX and coefficient < 0:
        return gate, "SUPPORTED", "negative association clears frozen two-sided local screen", estimate, panel
    if p <= P_MAX and coefficient > 0:
        return gate, "REFUTED", "positive association clears frozen two-sided local screen", estimate, panel
    return gate, "PARTIAL", "estimable association does not clear frozen directional screen", estimate, panel


def artifact_bytes(revision: str, stamp: str) -> dict[str, bytes]:
    gate, verdict, reason, estimate, panel = estimate_one()
    inputs = [{"role": role, **source} for role, source in SOURCES.items()]
    diagnostics = {
        "hypothesis_id": ID, "verdict": verdict, "verdict_label": verdict, "verdict_reason": reason,
        "run_utc": stamp, "runner": RUNNER, "preregistration_commit": revision,
        "source_lock": LOCK, "template": "panel_fe", "key_preflight": key_preflight(),
        "preflight": gate, "estimate": estimate,
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": FAMILY_ALPHA,
        "family_p_max": P_MAX, "data_status": {"variables_missing": [], "input_vintages": inputs},
        "limitations": LIMITATIONS, "correction": CORRECTION,
    }
    manifest = {"hypothesis_id": ID, "run_utc": stamp, "runner": RUNNER,
                "preregistration_commit": revision, "source_lock": LOCK, "status": verdict,
                "vintages": inputs, "derived_panel": gate, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": ID, "path": SPEC, "topic": "distribution"},
              "preregistration": {"spec_commit": revision, "steelman": STEELMAN,
                                  "family_id": FAMILY, "family_size": FAMILY_SIZE,
                                  "family_alpha": FAMILY_ALPHA, "family_p_max": P_MAX},
              "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                               "command": f"python3 {RUNNER} --check"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": reason},
              "data": {"inputs": inputs, "n_observations": gate["observations"],
                       "n_countries": gate["countries"]},
              "results": estimate, "limitations": LIMITATIONS, "correction": CORRECTION}
    card = (f"# Result card: {ID}\n\nVerdict: **{verdict}**. {reason}.\n\n"
            f"Preregistration commit: {revision}; source lock: {LOCK}.\n"
            f"Complete sample: {gate['observations']} country-year pairs, {gate['countries']} countries.\n"
            f"Two-sided local ten-slot cutoff: p <= {P_MAX:.6f}.\n")
    if estimate:
        card += (f"Primary coefficient: {estimate['coefficient']:+.6g} percentage points of share change "
                 f"per one percentage point rate change; country-clustered SE {estimate['std_error']:.6g}; "
                 f"p={estimate['p_value']:.6g}.\n")
    card += ("\nAll-ages sptincj999 pre-tax national-income share; historical descriptive association only. "
             "No causal tax-policy inference or school/policy credit.\n")
    chart = {"hypothesis_id": ID, "verdict": verdict,
             "coefficient": estimate["coefficient"] if estimate else None,
             "ci95": estimate["ci95"] if estimate else None, "family_p_max": P_MAX}
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--check'], cwd=root))\n")
    outputs = {
        "hypothesis.yaml": (ROOT / SPEC).read_bytes(),
        "diagnostics.json": (json.dumps(diagnostics, indent=2, sort_keys=True) + "\n").encode(),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False).encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": card.encode(), "replication.py": wrapper.encode(),
        "chart_data.json": (json.dumps(chart, indent=2, sort_keys=True) + "\n").encode(),
    }
    # Coefficients are represented in a deterministic JSON record for bytewise replay.
    outputs["coefficients.json"] = (json.dumps({"term": "treatment", "estimate": estimate,
        "n_panel_rows": len(panel)}, indent=2, sort_keys=True) + "\n").encode()
    return outputs


def run() -> None:
    revision = registration_commit()
    validate_spec()
    check_sources()
    check_lock(revision)
    if (ROOT / RUN_DIR).exists():
        raise FileExistsError(RUN_DIR)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    outputs = artifact_bytes(revision, stamp)
    folder = ROOT / RUN_DIR
    folder.mkdir(parents=True)
    for name, content in outputs.items():
        (folder / name).write_bytes(content)
    print(json.loads(outputs["diagnostics.json"])["verdict"])


def check() -> None:
    revision = registration_commit()
    validate_spec()
    check_sources()
    check_lock(revision)
    folder = ROOT / RUN_DIR
    saved = json.loads((folder / "diagnostics.json").read_text())
    outputs = artifact_bytes(revision, saved["run_utc"])
    present = {path.name for path in folder.iterdir() if path.is_file()}
    if present != set(outputs):
        raise RuntimeError(f"result file set differs: {present ^ set(outputs)}")
    for name, content in outputs.items():
        if (folder / name).read_bytes() != content:
            raise RuntimeError(f"exact replay mismatch: {name}")
    print(f"Verified {ID}: {saved['verdict']} (exact bytewise replay)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate-spec", action="store_true")
    group.add_argument("--write-source-lock", action="store_true")
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.validate_spec:
        validate_spec()
        print("Frozen spec and runner agree")
    elif args.write_source_lock:
        write_lock()
        print(f"Wrote value-blind source lock: {LOCK}")
    elif args.preflight:
        revision = registration_commit()
        validate_spec()
        check_sources()
        check_lock(revision)
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
    elif args.run:
        run()
    else:
        check()


if __name__ == "__main__":
    main()
