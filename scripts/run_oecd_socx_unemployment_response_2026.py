#!/usr/bin/env python3
"""Frozen OECD unemployment-cash response relative to family spending."""
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
import patsy
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
ID = "oecd_unemployment_cash_cyclical_response_2026"
FAMILY = "oecd_unemployment_cash_cyclical_response_2026_10_10"
SPEC = f"hypotheses/fiscal/{ID}.yaml"
STEELMAN = f"hypotheses/steelman/{ID}.md"
RUNNER = "scripts/run_oecd_socx_unemployment_response_2026.py"
PREREG = "engine/audits/oecd_socx_unemployment_response_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/oecd_socx_unemployment_response_2026_key_roster.csv"
ROSTER_SHA = "e67b06ba296a038f805d848841fdca977cc3d92e2c86e3b68437ae23c72e8549"
LOCK = "data/pinned_evidence/oecd_socx_unemployment_response_2026.source.json"
RUN = f"engine/runs/{ID}"
SUMMARY = "engine/audits/oecd_socx_unemployment_response_results_2026-10-10.md"
SOCX_MANIFEST = "data/manifests/fetch_run_2026-05-05T210519Z.yaml"
WDI_MANIFEST = "data/manifests/fetch_run_2026-05-05T200056Z.yaml"
SOURCES = {
    "socx": {"publisher": "oecd", "series_id": "DSD_SOCX@DF_SOCX_AGG",
             "path": "data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet",
             "sha256": "93e7e29b24dc791baf22833ae5596b4a381a366ddd0d78499bf59f7b80786124",
             "manifest": SOCX_MANIFEST,
             "manifest_sha256": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"},
    "gdp": {"publisher": "world_bank_wdi", "series_id": "NY.GDP.MKTP.KD.ZG",
            "path": "data/vintages/world_bank_wdi/NY.GDP.MKTP.KD.ZG@2026-05-05T194655Z.parquet",
            "sha256": "db76a52909929c6cd3ca1dd3d1fdc4b28d28cbaea92e16cb59e88ee53d3f2e58",
            "manifest": WDI_MANIFEST,
            "manifest_sha256": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"},
}
START, END = 1991, 2018
MIN_YEARS, MIN_ROWS, MIN_COUNTRIES = 10, 800, 30
MIN_DOWNTURN_ROWS, MIN_DOWNTURN_COUNTRIES = 60, 20
MIN_FOLD_ROWS, MIN_FOLD_COUNTRIES = 600, 24
MAX_COUNTRY_SHARE, MAX_TOP_ONE_PERCENT = 0.20, 0.30
GDP_MIN, GDP_MAX = -20.0, 20.0
P_MAX, MEANINGFUL_BETA = 0.01, 0.02
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
              "family_size": 1, "family_alpha": P_MAX, "p_max_two_sided": P_MAX,
              "causal_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "school_score_eligible": False,
              "school_score_credit": 0, "featured_eligible": False}
LIMITS = [
    "The relative spending outcome may move because family spending fell; it does not prove unemployment cash benefits rose.",
    "The OECD TP711 category includes unemployment compensation and severance pay; it is not a claimant count or benefit-law measure.",
    "Real GDP and benefit spending are contemporaneous and jointly determined; country/year effects do not identify causal direction.",
    "Eligibility, discretionary fiscal changes, population, PPP/price conversion and vintage revisions can confound the association.",
    "This family was selected after other IESET results were visible; p=0.01 does not correct archive-wide selection.",
    "No causal, policy, school, position or featured credit is assigned.",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_add(path: str) -> str:
    lines = git("log", "--diff-filter=A", "--reverse", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if len(lines) != 1:
        raise RuntimeError(f"expected exactly one first-addition commit for {path}: {lines}")
    return lines[0]


def frozen(path: str, revision: str) -> None:
    if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"registered bytes changed: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted registered path: {path}")


def registration() -> str:
    paths = [SPEC, STEELMAN, RUNNER, PREREG, ROSTER]
    additions = {first_add(path) for path in paths}
    if len(additions) != 1:
        raise RuntimeError(f"registration paths have different first-addition commits: {additions}")
    revision = additions.pop()
    for path in paths:
        frozen(path, revision)
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("source-key roster hash changed")
    if git("ls-tree", "-r", "--name-only", revision, "--", RUN).strip():
        raise RuntimeError("registration commit already contained measured result")
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec["falsification"]["threshold"]
    if (spec.get("hypothesis_id") != ID or spec.get("status") != "pre_registered"
            or spec.get("claim_direction") != "-" or spec.get("evidence_type") != "associational"
            or spec["sample"]["period"] != [1990, 2018]
            or threshold.get("family_id") != FAMILY or threshold.get("family_size") != 1
            or threshold.get("source_key_roster_sha256") != ROSTER_SHA
            or threshold.get("source_lock_path") != LOCK
            or spec.get("covers_claims") != []):
        raise RuntimeError("frozen spec does not match runner")
    return revision


def source_lock(reg: str) -> str:
    revision = first_add(LOCK)
    frozen(LOCK, revision)
    if subprocess.run(["git", "merge-base", "--is-ancestor", reg, revision], cwd=ROOT).returncode:
        raise RuntimeError("source lock was not committed after registration")
    data = json.loads((ROOT / LOCK).read_text())
    if (data.get("family_id") != FAMILY or data.get("hypothesis_id") != ID
            or data.get("registration_commit") != reg
            or data.get("source_key_roster_sha256") != ROSTER_SHA
            or data.get("sources") != SOURCES):
        raise RuntimeError("source lock differs from registered source roles")
    return revision


def check_sources(source_root: Path) -> None:
    for role, src in SOURCES.items():
        raw, manifest = source_root / src["path"], source_root / src["manifest"]
        if not raw.is_file() or sha256(raw) != src["sha256"]:
            raise RuntimeError(f"raw source hash mismatch: {role}")
        if not manifest.is_file() or sha256(manifest) != src["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest hash mismatch: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [e for e in entries if e.get("publisher") == src["publisher"]
                   and e.get("series_id") == src["series_id"]
                   and e.get("parquet_path") == src["path"]
                   and e.get("sha256") == src["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"no exact source-manifest entry: {role}")


def roster() -> list[tuple[str, int]]:
    if sha256(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("source-key roster hash mismatch")
    with (ROOT / ROSTER).open(newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != ["country_iso3", "year"]:
            raise RuntimeError("source-key roster header changed")
        rows = [(r["country_iso3"], int(r["year"])) for r in reader]
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    countries = set(spec["sample"]["countries"])
    if (len(rows) != 1030 or len(countries) != 39 or {c for c, _ in rows} != countries
            or rows != sorted(rows) or len(set(rows)) != len(rows)
            or any(not START <= y <= END for _, y in rows)):
        raise RuntimeError("source-key roster shape or order changed")
    return rows


def socx_cells(source_root: Path, countries: set[str]) -> dict[str, dict[tuple[str, int], object]]:
    frame = pd.read_parquet(source_root / SOURCES["socx"]["path"], columns=[
        "REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "EXPEND_SOURCE",
        "SPENDING_TYPE", "PROGRAMME_TYPE", "PRICE_BASE", "period", "OBS_STATUS", "value"])
    fixed = (frame.REF_AREA.isin(countries) & frame.FREQ.eq("A") & frame.MEASURE.eq("SOCX")
             & frame.UNIT_MEASURE.eq("USD_PPP_PS") & frame.EXPEND_SOURCE.eq("ES10")
             & frame.PRICE_BASE.eq("Q") & frame.OBS_STATUS.eq("A")
             & frame.period.between(START - 1, END))
    result = {}
    for role, programme, spend_type in (("unemployment", "TP711", "C"),
                                         ("family", "TP51", "_T")):
        part = frame.loc[fixed & frame.PROGRAMME_TYPE.eq(programme)
                         & frame.SPENDING_TYPE.eq(spend_type), ["REF_AREA", "period", "value"]]
        if part.duplicated(["REF_AREA", "period"]).any():
            raise RuntimeError(f"duplicate exact OECD source keys: {role}")
        result[role] = {(c, int(y)): value for c, y, value in part.itertuples(index=False, name=None)}
    return result


def gdp_cells(source_root: Path, countries: set[str]) -> dict[tuple[str, int], tuple[object, object]]:
    frame = pd.read_parquet(source_root / SOURCES["gdp"]["path"], columns=[
        "country_iso3", "indicator_id", "year", "value", "obs_status"])
    frame = frame.loc[frame.country_iso3.isin(countries)]
    if set(frame.indicator_id.dropna()) != {SOURCES["gdp"]["series_id"]}:
        raise RuntimeError("WDI source indicator mismatch")
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError("duplicate national WDI source keys")
    return {(c, int(y)): (value, status) for c, y, value, status in frame.itertuples(index=False, name=None)}


def finite_nonnegative(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def valid_gdp(cell: tuple[object, object] | None) -> float | None:
    if cell is None:
        return None
    value, status = cell
    if status is not None and not pd.isna(status) and str(status).strip() not in ("", "A"):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and GDP_MIN <= number <= GDP_MAX else None


def build_panel(source_root: Path, keys: list[tuple[str, int]]) -> tuple[pd.DataFrame, dict]:
    countries = {c for c, _ in keys}
    spending, growth = socx_cells(source_root, countries), gdp_cells(source_root, countries)
    kept, dropped = [], Counter()
    for country, year in keys:
        u0 = finite_nonnegative(spending["unemployment"].get((country, year - 1)))
        u1 = finite_nonnegative(spending["unemployment"].get((country, year)))
        f0 = finite_nonnegative(spending["family"].get((country, year - 1)))
        f1 = finite_nonnegative(spending["family"].get((country, year)))
        if None in (u0, u1, f0, f1):
            dropped["missing_nonfinite_or_negative_spending_endpoint"] += 1
            continue
        x = valid_gdp(growth.get((country, year)))
        if x is None:
            dropped["missing_status_or_out_of_range_gdp_growth"] += 1
            continue
        du = math.log1p(u1) - math.log1p(u0)
        df = math.log1p(f1) - math.log1p(f0)
        kept.append((country, year, x, du - df, du, df))
    frame = pd.DataFrame(kept, columns=["country", "year", "x", "y", "unemployment_change", "family_change"])
    before_floor = len(frame)
    if not frame.empty:
        count = frame.country.value_counts()
        frame = frame.loc[frame.country.map(count).ge(MIN_YEARS)].copy()
    dropped["country_below_ten_year_floor"] = before_floor - len(frame)
    frame = frame.sort_values(["year", "country"]).reset_index(drop=True)
    downturn = frame.x.lt(0) if not frame.empty else pd.Series(dtype=bool)
    sample = {"key_roster_rows": len(keys), "key_roster_countries": len(countries),
              "complete_rows_before_country_floor": before_floor,
              "valid_rows": len(frame), "valid_countries": int(frame.country.nunique()) if not frame.empty else 0,
              "downturn_rows": int(downturn.sum()),
              "downturn_countries": int(frame.loc[downturn, "country"].nunique()) if not frame.empty else 0,
              "dropped": dict(sorted(dropped.items())),
              "selected_values_read_after_committed_lock": True}
    return frame, sample


def fit(frame: pd.DataFrame) -> dict:
    if len(frame) < 10 or frame.country.nunique() < 5:
        raise ValueError("too few country-years for fixed-effects estimator")
    design = patsy.dmatrix("1 + x + C(country) + C(year)", frame, return_type="dataframe")
    matrix = design.to_numpy(dtype=float)
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != matrix.shape[1]:
        raise ValueError(f"rank-deficient design {rank}/{matrix.shape[1]}")
    ix = list(design.columns).index("x")
    countries = int(frame.country.nunique())
    group = frame.country.to_numpy()
    terms = {}
    for name, column in (("differential", "y"), ("unemployment_component", "unemployment_change"),
                         ("family_component", "family_change")):
        model = sm.OLS(frame[column].to_numpy(dtype=float), matrix).fit(
            cov_type="cluster", cov_kwds={"groups": group,
                                          "use_correction": True, "df_correction": True})
        beta, se = float(model.params[ix]), float(model.bse[ix])
        if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
            raise ValueError(f"nonfinite or nonpositive cluster uncertainty: {name}")
        p = float(2 * student_t.sf(abs(beta / se), df=countries - 1))
        if not math.isfinite(p):
            raise ValueError(f"nonfinite p: {name}")
        terms[name] = {"coefficient": beta, "std_error": se, "p_value_two_sided": p}
    z = patsy.dmatrix("1 + C(country) + C(year)", frame, return_type="dataframe").to_numpy(dtype=float)
    x = frame.x.to_numpy(dtype=float)
    residual = x - z @ np.linalg.lstsq(z, x, rcond=None)[0]
    square = residual**2
    total = float(square.sum())
    if not math.isfinite(total) or total <= 1e-12:
        raise ValueError("no residualized GDP-growth exposure variation")
    shares = pd.DataFrame({"country": group, "square": square})
    country_share = float(shares.groupby("country").square.sum().max() / total)
    top_n = max(1, math.ceil(len(frame) * .01))
    top_row_share = float(np.sort(square)[-top_n:].sum() / total)
    critical = float(student_t.ppf(1 - P_MAX / 2, df=countries - 1))
    diff = terms["differential"]
    diff["confidence_interval_99pct"] = [diff["coefficient"] - critical * diff["std_error"],
                                          diff["coefficient"] + critical * diff["std_error"]]
    return {"terms": terms, "n_rows": len(frame), "n_countries": countries,
            "df_inference": countries - 1, "model_rank": rank,
            "model_columns": matrix.shape[1],
            "top_country_residualized_exposure_share": country_share,
            "top_one_percent_residualized_exposure_share": top_row_share,
            "method": "country/year fixed-effects OLS; country-cluster CR1; Student t(G-1)"}


def fold(country: str) -> int:
    return int(hashlib.sha256(country.encode()).hexdigest()[:8], 16) % 5


def analyze(source_root: Path, run_utc: str, reg: str, lock_commit: str) -> tuple[dict, pd.DataFrame]:
    keys = roster()
    frame, sample = build_panel(source_root, keys)
    failures = []
    if sample["valid_rows"] < MIN_ROWS:
        failures.append("complete_row_floor")
    if sample["valid_countries"] < MIN_COUNTRIES:
        failures.append("complete_country_floor")
    if sample["downturn_rows"] < MIN_DOWNTURN_ROWS:
        failures.append("downturn_row_floor")
    if sample["downturn_countries"] < MIN_DOWNTURN_COUNTRIES:
        failures.append("downturn_country_floor")
    primary = None
    if not frame.empty:
        try:
            primary = fit(frame)
        except ValueError as exc:
            failures.append("primary_estimator: " + str(exc))
    if primary:
        if primary["top_country_residualized_exposure_share"] > MAX_COUNTRY_SHARE:
            failures.append("top_country_residual_concentration")
        if primary["top_one_percent_residualized_exposure_share"] > MAX_TOP_ONE_PERCENT:
            failures.append("top_one_percent_residual_concentration")
    folds = []
    for omitted in range(5):
        part = frame.loc[frame.country.map(fold).ne(omitted)].copy()
        record = {"omitted_hash_fold": omitted, "n_rows": len(part),
                  "n_countries": int(part.country.nunique()) if not part.empty else 0}
        if record["n_rows"] < MIN_FOLD_ROWS or record["n_countries"] < MIN_FOLD_COUNTRIES:
            failures.append(f"fold_{omitted}_sample_floor")
        try:
            estimate = fit(part)["terms"]["differential"]
            record.update({"coefficient": estimate["coefficient"],
                           "std_error": estimate["std_error"],
                           "p_value_two_sided": estimate["p_value_two_sided"]})
        except ValueError as exc:
            record["fit_error"] = str(exc)
            failures.append(f"fold_{omitted}_estimator")
        folds.append(record)
    negative_folds = sum(row.get("coefficient", 0) < 0 for row in folds)
    positive_folds = sum(row.get("coefficient", 0) > 0 for row in folds)
    diff = primary["terms"]["differential"] if primary else None
    if failures:
        verdict, reason = "INCONCLUSIVE", "; ".join(sorted(set(failures)))
    elif diff["coefficient"] <= -MEANINGFUL_BETA and diff["p_value_two_sided"] <= P_MAX and negative_folds >= 4:
        verdict, reason = "SUPPORTED", "relative unemployment-spending response clears negative magnitude, p, and fold gates"
    elif diff["coefficient"] >= MEANINGFUL_BETA and diff["p_value_two_sided"] <= P_MAX and positive_folds >= 4:
        verdict, reason = "REFUTED", "relative spending response clears the opposite positive magnitude, p, and fold gates"
    else:
        verdict, reason = "PARTIAL", "estimable differential misses a directional gate"
    diag = {"hypothesis_id": ID, "family_id": FAMILY, "family_size": 1,
            "run_utc": run_utc, "runner": RUNNER, "registration_commit": reg,
            "source_lock_commit": lock_commit, "source_lock": LOCK,
            "source_key_roster_sha256": ROSTER_SHA,
            "verdict": verdict, "verdict_label": verdict, "verdict_reason": reason,
            "template": "panel_fe", "preflight": sample, "primary": primary,
            "holdout_folds": folds, "negative_fold_signs": negative_folds,
            "positive_fold_signs": positive_folds, "failed_gates": sorted(set(failures)),
            "p_max_two_sided": P_MAX, "meaningful_beta_min_abs": MEANINGFUL_BETA,
            "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
            "correction": CORRECTION, "limitations": LIMITS}
    return diag, frame


def payloads(diag: dict, frame: pd.DataFrame) -> dict[str, bytes]:
    verdict = diag["verdict"]
    manifest = {"hypothesis_id": ID, "run_utc": diag["run_utc"], "runner": RUNNER,
                "preregistration_commit": diag["registration_commit"],
                "source_lock_commit": diag["source_lock_commit"], "source_lock": LOCK,
                "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": diag["preflight"], "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": diag["run_utc"],
              "hypothesis": {"id": ID, "path": SPEC, "topic": "fiscal"},
              "preregistration": {"spec_commit": diag["registration_commit"],
                                  "source_lock_commit": diag["source_lock_commit"],
                                  "family_id": FAMILY, "family_size": 1,
                                  "key_roster": ROSTER, "key_roster_sha256": ROSTER_SHA,
                                  "steelman": STEELMAN},
              "reproduction": {"runner": RUNNER, "run_dir": RUN,
                               "command": f"python3 {RUNNER} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(),
                          "reason": diag["verdict_reason"]},
              "data": {"inputs": SOURCES, "sample": diag["preflight"]},
              "results": {"primary": diag["primary"], "folds": diag["holdout_folds"]},
              "failed_gates": diag["failed_gates"], "limitations": LIMITS,
              "correction": CORRECTION}
    annual = []
    if not frame.empty:
        for year, group in frame.groupby("year", sort=True):
            annual.append({"year": int(year), "n": len(group),
                           "median_gdp_growth_pct": float(group.x.median()),
                           "median_relative_spending_change_log": float(group.y.median())})
    chart = {"hypothesis_id": ID, "interpretation": "descriptive complete-case annual medians only",
             "years": annual}
    primary = diag["primary"] or {"terms": {}}
    coefficients = pd.DataFrame([{"term": name, **estimate,
                                  "n_rows": primary.get("n_rows", 0),
                                  "n_countries": primary.get("n_countries", 0)}
                                 for name, estimate in primary["terms"].items()])
    buf = io.BytesIO()
    coefficients.to_parquet(buf, index=False)
    diff = primary["terms"].get("differential", {})
    beta_text = f"{diff['coefficient']:+.6f}" if diff else "unavailable"
    p_text = f"{diff['p_value_two_sided']:.6g}" if diff else "unavailable"
    card = (f"# {ID}\n\n**{verdict}** — {diag['verdict_reason']}.\n\n"
            f"The locked differential-spending slope is {beta_text} log points per +1 "
            f"percentage point real GDP growth; two-sided country-cluster p={p_text}. "
            f"Complete sample: {diag['preflight']['valid_rows']} country-years in "
            f"{diag['preflight']['valid_countries']} countries. This is a contemporaneous "
            f"descriptive calibration, not a causal or policy effect.\n\n"
            f"Registration: `{diag['registration_commit']}`; source lock: "
            f"`{diag['source_lock_commit']}`. Replay with `python3 {RUNNER} --verify`.\n\n"
            "A negative differential can reflect reduced family spending; TP711 also includes "
            "severance pay. No school, position, policy, causal or featured credit.\n")
    replication = ("#!/usr/bin/env python3\nimport subprocess\nimport sys\n"
                   f"raise SystemExit(subprocess.call([sys.executable, '{RUNNER}', '--verify']))\n")
    def js(value: object) -> bytes:
        return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    def ya(value: object) -> bytes:
        return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()
    return {"hypothesis.yaml": (ROOT / SPEC).read_bytes(), "manifest.yaml": ya(manifest),
            "evidence_packet.yaml": ya(packet), "diagnostics.json": js(diag),
            "chart_data.json": js(chart), "coefficients.parquet": buf.getvalue(),
            "result_card.md": card.encode(), "replication.py": replication.encode()}


def summary(diag: dict) -> str:
    terms = diag["primary"]["terms"] if diag["primary"] else {}
    differential = terms.get("differential", {})
    return ("# OECD unemployment cash spending relative to family spending — locked result\n\n"
            f"**{diag['verdict']}**. {diag['verdict_reason']}.\n\n"
            f"Frozen source-key roster: {diag['preflight']['key_roster_rows']} rows / "
            f"{diag['preflight']['key_roster_countries']} countries. Complete eligible panel "
            f"after the ten-year country floor: {diag['preflight']['valid_rows']} rows / "
            f"{diag['preflight']['valid_countries']} countries. GDP-contraction rows: "
            f"{diag['preflight']['downturn_rows']} across "
            f"{diag['preflight']['downturn_countries']} countries.\n\n"
            f"Differential beta {differential.get('coefficient', 'unavailable')}; "
            f"country-cluster SE {differential.get('std_error', 'unavailable')}; "
            f"two-sided p {differential.get('p_value_two_sided', 'unavailable')}; "
            f"negative/positive country-fold signs {diag['negative_fold_signs']}/"
            f"{diag['positive_fold_signs']}. Component estimates: "
            f"unemployment {terms.get('unemployment_component', {}).get('coefficient', 'unavailable')}, "
            f"family {terms.get('family_component', {}).get('coefficient', 'unavailable')}. "
            f"Failed gates: {diag['failed_gates']}.\n\n"
            "This measures contemporaneous variation in relative real public programme spending, "
            "not statutory automatic-stabilizer activation, claimant counts, an effect on recession "
            "severity, or causality. No policy, school, position, causal or featured credit. "
            "The within-family alpha does not correct archive-wide selection.\n\n"
            f"Spec commit `{diag['registration_commit']}`; source lock commit "
            f"`{diag['source_lock_commit']}`. Exact replay: `python3 {RUNNER} --verify`.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--run", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--source-root", type=Path, default=ROOT)
    args = parser.parse_args()
    reg = registration()
    lock_commit = source_lock(reg)
    check_sources(args.source_root)
    keys = roster()
    if args.preflight:
        print(json.dumps({"registration_commit": reg, "source_lock_commit": lock_commit,
                          "source_key_rows": len(keys),
                          "source_key_countries": len({c for c, _ in keys}),
                          "source_hashes": {role: src["sha256"] for role, src in SOURCES.items()}},
                         sort_keys=True))
        return 0
    out = ROOT / RUN
    if args.verify:
        if not out.is_dir() or not (ROOT / SUMMARY).is_file():
            raise RuntimeError("no saved run to verify")
        previous = json.loads((out / "diagnostics.json").read_text())
        run_utc = previous["run_utc"]
    else:
        if out.exists() or (ROOT / SUMMARY).exists():
            raise RuntimeError("result already exists; use --verify")
        run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    diag, frame = analyze(args.source_root, run_utc, reg, lock_commit)
    files, report = payloads(diag, frame), summary(diag).encode()
    if args.verify:
        for name, data in files.items():
            if (out / name).read_bytes() != data:
                raise RuntimeError(f"exact replay mismatch: {name}")
        if (ROOT / SUMMARY).read_bytes() != report:
            raise RuntimeError("exact replay mismatch: result audit")
        print(f"OK exact replay: {len(files)} run artifacts + result audit; {diag['verdict']}")
        return 0
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    (ROOT / SUMMARY).write_bytes(report)
    diff = diag["primary"]["terms"]["differential"] if diag["primary"] else None
    print(f"{diag['verdict']} beta={diff['coefficient'] if diff else None} "
          f"p={diff['p_value_two_sided'] if diff else None} "
          f"n={diag['preflight']['valid_rows']} countries={diag['preflight']['valid_countries']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
