#!/usr/bin/env python3
"""Prospective, source-locked ACS teen-employment calibration.

--preflight reads committed registration and treatment geography/year keys only.
--fetch-lock may open magnitudes only after the registration commit exists.
--run requires a separate committed source lock. --check exactly replays the fit.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import time
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as scipy_stats
import statsmodels.formula.api as smf
import yaml

ROOT = Path(__file__).resolve().parents[1]
HID = "us_state_minimum_wage_bite_teen_employment_2026"
SPEC = f"hypotheses/labour/{HID}.yaml"
STEELMAN = f"hypotheses/steelman/{HID}.md"
PLAN = f"engine/audits/{HID}_prereg_2026-10-10.md"
ROSTER = f"data/pinned_evidence/{HID}_key_roster.csv"
RUNNER = f"scripts/run_{HID}.py"
REGISTRATION = (SPEC, STEELMAN, PLAN, ROSTER, RUNNER)
RAW_DIR = f"data/pinned_evidence/{HID}_acs_raw"
SLICE = f"data/pinned_evidence/{HID}_source_slice.csv"
LOCK = f"data/pinned_evidence/{HID}_source_lock.json"
RUN_DIR = f"engine/runs/{HID}"
YEARS = (2014, 2015, 2016, 2017, 2018, 2021, 2023, 2024)
PREYEARS = tuple(range(2014, 2019))
MANIFEST = "data/manifests/fetch_run_2026-05-14T111058Z.yaml"
MANIFEST_SHA = "1ecb15544dd1bfa84a478ef327d4966cfdda5011cb77150eaf533d0360c841e5"
TREATMENT = "data/vintages/derived/minimum_wage_bite_ratio_state_panel@2026-05-14T111058Z.parquet"
TREATMENT_SHA = "e5da018ddcef55c1b4255e406cfb4e22d987599cce132ecee915648fcf051119"
FIELDS = ("NAME", "S2301_C03_002E", "S2301_C03_002M", "state")
COLUMNS = ("state_fips", "state_abbr", "year", "teen_ep_pct", "teen_ep_moe_pp", "bite_ratio")
FAMILY_P = 0.005


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(relative: str) -> str:
    return digest((ROOT / relative).read_bytes())


def git_bytes(revision: str, relative: str) -> bytes:
    process = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=ROOT, capture_output=True)
    if process.returncode:
        raise ValueError(f"missing committed file {revision}:{relative}")
    return process.stdout


def first_addition(relative: str) -> str:
    process = subprocess.run(
        ["git", "log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    commits = process.stdout.strip().splitlines()
    if len(commits) != 1:
        raise ValueError(f"one first-addition commit required for {relative}")
    return commits[0]


def registered() -> tuple[str, list[dict[str, str]], dict]:
    commits = {first_addition(path) for path in REGISTRATION}
    if len(commits) != 1:
        raise ValueError("spec, steelman, plan, key roster and runner must be first-added together")
    commit = next(iter(commits))
    files = []
    for path in REGISTRATION:
        current = (ROOT / path).read_bytes()
        if git_bytes(commit, path) != current or git_bytes("HEAD", path) != current:
            raise ValueError(f"registration edited after first commit: {path}")
        files.append({"path": path, "sha256": digest(current)})
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    threshold = spec["falsification"]["threshold"]
    expected = {
        "family_id": "us_minwage_age_specific_followup_2026_10_10",
        "family_size": 1, "family_p_max": FAMILY_P,
        "min_observations": 300, "min_states": 45, "min_years_per_state": 5,
        "min_contrast_gap": 0.10, "max_state_residualized_treatment_share": 0.20,
        "preperiod": [2014, 2018], "preperiod_min_observations": 180,
        "preperiod_min_states": 40, "practical_effect_per_0_10_bite_pp": 0.5,
        "fixed_key_upper_bound": 408,
        "source_manifest": {"path": MANIFEST, "sha256": MANIFEST_SHA},
        "treatment_vintage": {"path": TREATMENT, "sha256": TREATMENT_SHA},
        "outcome_field": FIELDS[1], "outcome_moe_field": FIELDS[2],
        "school_score_eligible": False, "school_score_credit": 0,
    }
    if (spec.get("hypothesis_id") != HID or spec.get("status") != "pre_registered"
            or spec.get("claim_direction") != "-" or spec.get("evidence_type") != "associational"
            or spec["sample"]["period"] != [2014, 2024]
            or spec["sample"]["countries"] != ["USA"]
            or threshold != expected
            or spec["estimator"]["template"] != "panel_fe"
            or spec["estimator"]["fixed_effects"] != ["state", "year"]
            or spec["estimator"]["clustering"] != "state"
            or spec["variables"]["outcome"][0]["source"] != "us_census:acs1_subject_S2301_C03_002E"
            or spec["variables"]["treatment"][0]["source"] != "derived:minimum_wage_bite_ratio_state_panel"
            or any(spec.get(k) != [] for k in ("covers_claims", "linked_hypotheses", "linked_conditions"))):
        raise ValueError("frozen design differs from runner")
    if file_sha(MANIFEST) != MANIFEST_SHA or git_bytes("HEAD", MANIFEST) != (ROOT / MANIFEST).read_bytes():
        raise ValueError("treatment source manifest changed")
    return commit, files, spec


def keys() -> list[tuple[str, str, int]]:
    with (ROOT / ROSTER).open(newline="") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == ["state_fips", "state_abbr", "year"]
        rows = [(r["state_fips"], r["state_abbr"], int(r["year"])) for r in reader]
    if (len(rows) != 408 or rows != sorted(set(rows))
            or set(y for _, _, y in rows) != set(YEARS)
            or len({f for f, _, _ in rows}) != 51
            or any(f in {"60", "66", "69", "72", "78"} for f, _, _ in rows)):
        raise ValueError("frozen 408-key roster differs")
    return rows


def preflight() -> dict:
    commit, _, _ = registered()
    roster = keys()
    path = ROOT / TREATMENT
    result = {"preregistration_commit": commit, "fixed_keys": len(roster),
              "states": len({r[0] for r in roster}), "years": list(YEARS),
              "treatment_present": path.exists()}
    if path.exists():
        import pyarrow.parquet as pq
        if file_sha(TREATMENT) != TREATMENT_SHA:
            raise ValueError("treatment vintage hash differs")
        src = pq.read_table(path, columns=["state_fips", "state_abbr", "year"]).to_pylist()
        available = {(str(r["state_fips"]).zfill(2), str(r["state_abbr"]), int(r["year"])) for r in src}
        if not set(roster) <= available:
            raise ValueError("treatment identifier keys missing")
        result["treatment_roster_keys_verified"] = True
    return result


def source_url(year: int) -> str:
    return (f"https://api.census.gov/data/{year}/acs/acs1/subject?"
            "get=NAME,S2301_C03_002E,S2301_C03_002M&for=state:*")


def download(url: str) -> bytes:
    last = None
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "IESET-evidence-audit/1.0"})
            with urllib.request.urlopen(request, timeout=35) as response:
                if response.status != 200:
                    raise ValueError(f"HTTP {response.status}")
                return response.read()
        except Exception as error:
            last = error
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Census download failed: {url}: {last}")


def build_slice() -> dict:
    commit, _, _ = registered()  # must precede any selected value read
    roster = keys()
    if not (ROOT / TREATMENT).exists() or file_sha(TREATMENT) != TREATMENT_SHA:
        raise ValueError("pinned treatment vintage absent or changed")
    if (ROOT / LOCK).exists() or (ROOT / SLICE).exists():
        raise FileExistsError("source lock already exists")
    import pyarrow.parquet as pq
    treatment = pq.read_table(ROOT / TREATMENT,
                              columns=["state_fips", "state_abbr", "year", "bite_ratio"]).to_pylist()
    tr = {}
    for r in treatment:
        key = (str(r["state_fips"]).zfill(2), str(r["state_abbr"]), int(r["year"]))
        if key in tr:
            raise ValueError(f"duplicate treatment key: {key}")
        tr[key] = r["bite_ratio"]
    if not set(roster) <= set(tr):
        raise ValueError("treatment missing fixed roster keys")
    raw = {}
    outcomes = {}
    for year in YEARS:
        body = download(source_url(year))
        payload = json.loads(body)
        if not isinstance(payload, list) or not payload or tuple(payload[0]) != FIELDS:
            raise ValueError(f"unexpected Census API header in {year}")
        annual = {}
        for row in payload[1:]:
            if len(row) != len(FIELDS):
                raise ValueError(f"invalid Census API row in {year}")
            fips = str(row[3]).zfill(2)
            if fips in annual:
                raise ValueError(f"duplicate Census FIPS {fips} in {year}")
            annual[fips] = row
        for fips, _, yy in roster:
            if yy == year:
                outcomes[(fips, year)] = annual.get(fips)
        raw[str(year)] = {"path": f"{RAW_DIR}/{year}.json", "url": source_url(year),
                          "sha256": digest(body), "body": body}
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(COLUMNS)
    for fips, abbr, year in roster:
        row = outcomes.get((fips, year))
        writer.writerow([fips, abbr, year, row[1] if row else "",
                         row[2] if row else "", repr(tr[(fips, abbr, year)])])
    selected = buffer.getvalue().encode()
    lock = {
        "hypothesis_id": HID, "preregistration_commit": commit,
        "registration_sha256": {p: file_sha(p) for p in REGISTRATION},
        "source_manifest": {"path": MANIFEST, "sha256": MANIFEST_SHA},
        "treatment_vintage": {"path": TREATMENT, "sha256": TREATMENT_SHA},
        "fixed_roster": {"path": ROSTER, "sha256": file_sha(ROSTER), "keys": 408},
        "raw_census": [{k: v for k, v in raw[str(y)].items() if k != "body"} for y in YEARS],
        "source_slice": {"path": SLICE, "sha256": digest(selected), "rows": 408},
        "source_note": "ACS one-year survey ratio; raw public Census API responses retained",
    }
    (ROOT / RAW_DIR).mkdir(parents=True, exist_ok=False)
    for entry in raw.values():
        (ROOT / entry["path"]).write_bytes(entry["body"])
    (ROOT / SLICE).write_bytes(selected)
    (ROOT / LOCK).write_text(json.dumps(lock, indent=2) + "\n")
    return {"lock": LOCK, "slice": SLICE, "raw_years": len(raw),
            "fixed_roster_rows": 408, "source_slice_sha256": digest(selected)}


def locked() -> tuple[str, dict, list[dict[str, str]]]:
    commit, registration, _ = registered()
    lock_path = ROOT / LOCK
    lock = json.loads(lock_path.read_text())
    lock_commit = first_addition(LOCK)
    if lock_commit == commit or lock_commit == first_addition(SLICE):
        # The lock and slice must first appear together, after registration.
        if lock_commit == commit:
            raise ValueError("source lock cannot share registration commit")
    if first_addition(SLICE) != lock_commit:
        raise ValueError("source lock and selected slice have different first additions")
    if not subprocess.run(["git", "merge-base", "--is-ancestor", commit, lock_commit],
                          cwd=ROOT).returncode == 0:
        raise ValueError("source lock is not descendant of registration")
    if lock.get("preregistration_commit") != commit:
        raise ValueError("wrong preregistration commit in source lock")
    if lock.get("registration_sha256") != {p: file_sha(p) for p in REGISTRATION}:
        raise ValueError("registration hashes differ in source lock")
    if lock.get("fixed_roster") != {"path": ROSTER, "sha256": file_sha(ROSTER), "keys": 408}:
        raise ValueError("fixed roster differs in source lock")
    if lock.get("source_manifest") != {"path": MANIFEST, "sha256": MANIFEST_SHA}:
        raise ValueError("manifest differs in source lock")
    if lock.get("treatment_vintage") != {"path": TREATMENT, "sha256": TREATMENT_SHA}:
        raise ValueError("treatment pin differs in source lock")
    if lock.get("source_slice") != {"path": SLICE, "sha256": file_sha(SLICE), "rows": 408}:
        raise ValueError("selected slice differs in source lock")
    raw = lock.get("raw_census")
    if not isinstance(raw, list) or len(raw) != len(YEARS):
        raise ValueError("Census raw response list differs")
    for year, entry in zip(YEARS, raw):
        if (entry.get("url") != source_url(year)
                or entry.get("path") != f"{RAW_DIR}/{year}.json"
                or entry.get("sha256") != file_sha(entry["path"])
                or first_addition(entry["path"]) != lock_commit):
            raise ValueError(f"Census response changed: {year}")
    for path in (LOCK, SLICE, *(entry["path"] for entry in raw)):
        if git_bytes("HEAD", path) != (ROOT / path).read_bytes():
            raise ValueError(f"uncommitted source differs: {path}")
    return lock_commit, lock, registration


def numeric(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def fit(df: pd.DataFrame) -> dict:
    model = smf.ols("teen_ep_pct ~ bite_ratio + C(state_fips) + C(year)", data=df)
    design = model.exog
    if np.linalg.matrix_rank(design) != design.shape[1]:
        raise ValueError("rank-deficient fixed-effects fit")
    result = model.fit(cov_type="cluster", cov_kwds={"groups": df["state_fips"],
                       "use_correction": True}, use_t=True)
    beta = float(result.params["bite_ratio"])
    se = float(result.bse["bite_ratio"])
    n_states = int(df["state_fips"].nunique())
    if not all(map(math.isfinite, (beta, se))) or se <= 0:
        raise ValueError("nonfinite or zero clustered standard error")
    p = float(2 * scipy_stats.t.sf(abs(beta / se), n_states - 1))
    residual = smf.ols("bite_ratio ~ C(state_fips) + C(year)", data=df).fit().resid
    squared = pd.Series(np.asarray(residual) ** 2, index=df.index)
    total = float(squared.sum())
    if total <= 0 or not math.isfinite(total):
        raise ValueError("no residualized treatment variation")
    shares = squared.groupby(df["state_fips"]).sum() / total
    return {
        "coefficient": beta, "std_error": se, "p_value": p,
        "n_obs": int(len(df)), "n_states": n_states,
        "r_squared": float(result.rsquared),
        "largest_state_residualized_treatment_share": float(shares.max()),
        "largest_state": str(shares.idxmax()),
        "method": f"state/year FE OLS; state-clustered t({n_states-1}) inference",
    }


def calculate() -> tuple[str, str, dict, dict, pd.DataFrame]:
    lock_commit, lock, _ = locked()
    keyset = set(keys())
    frame = pd.read_csv(ROOT / SLICE, dtype={"state_fips": str, "state_abbr": str})
    if list(frame.columns) != list(COLUMNS):
        raise ValueError("selected slice columns differ")
    observed = {(f.zfill(2), a, int(y)) for f, a, y in
                frame[["state_fips", "state_abbr", "year"]].itertuples(index=False, name=None)}
    if len(frame) != 408 or observed != {(f, a, y) for f, a, y in keyset}:
        raise ValueError("selected slice must match every frozen key exactly")
    frame["state_fips"] = frame["state_fips"].str.zfill(2)
    for col in ("teen_ep_pct", "teen_ep_moe_pp", "bite_ratio"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    complete = frame[np.isfinite(frame["teen_ep_pct"]) & np.isfinite(frame["bite_ratio"])
                     & frame["teen_ep_pct"].between(0, 100)
                     & frame["bite_ratio"].between(0, 1)].copy()
    years_per = complete.groupby("state_fips")["year"].nunique()
    keep_states = set(years_per[years_per >= 5].index)
    complete = complete[complete["state_fips"].isin(keep_states)].copy()
    pre = complete[complete["year"].isin(PREYEARS)].copy()
    contrast = (float(complete["bite_ratio"].quantile(0.9) -
                      complete["bite_ratio"].quantile(0.1)) if len(complete) else float("nan"))
    gate = {
        "fixed_keys": len(keyset), "complete_pairs": int(len(complete)),
        "states": int(complete["state_fips"].nunique()),
        "min_years_per_retained_state": int(years_per.loc[list(keep_states)].min()) if keep_states else 0,
        "year_counts": {str(k): int(v) for k, v in Counter(complete["year"]).items()},
        "bite_p90_p10_gap": contrast, "preperiod_pairs": int(len(pre)),
        "preperiod_states": int(pre["state_fips"].nunique()),
        "source_lock_commit": lock_commit,
    }
    if (len(complete) < 300 or gate["states"] < 45 or
            not math.isfinite(contrast) or contrast < 0.10 or
            len(pre) < 180 or gate["preperiod_states"] < 40):
        return "INCONCLUSIVE", "frozen sample, contrast or preperiod gate failed", gate, {}, complete
    try:
        main = fit(complete)
        sensitivity = fit(pre)
    except (ValueError, np.linalg.LinAlgError) as exc:
        return "INCONCLUSIVE", f"frozen estimator failed: {exc}", gate, {}, complete
    estimates = {"primary": main, "preperiod_2014_2018": sensitivity}
    if main["largest_state_residualized_treatment_share"] > 0.20:
        return "INCONCLUSIVE", "largest state exceeds frozen residualized-treatment share cap", gate, estimates, complete
    effect = 0.10 * main["coefficient"]
    if (main["coefficient"] < 0 and main["p_value"] <= FAMILY_P
            and effect <= -0.5 and sensitivity["coefficient"] <= 0):
        verdict = "SUPPORTED"
    elif (main["coefficient"] > 0 and main["p_value"] <= FAMILY_P
          and effect >= 0.5 and sensitivity["coefficient"] >= 0):
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    return verdict, "frozen descriptive and sensitivity rule applied", gate, estimates, complete


def artifacts(stamp: str, label: str, reason: str, gate: dict, estimates: dict,
              registration: list[dict[str, str]], prereg: str,
              lock_commit: str) -> dict[str, bytes]:
    diag = {
        "hypothesis_id": HID, "verdict": label, "verdict_label": label,
        "verdict_reason": reason, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": prereg, "source_lock_commit": lock_commit,
        "template": "panel_fe", "preflight": gate, "estimate": estimates,
        "family_id": "us_minwage_age_specific_followup_2026_10_10",
        "family_size": 1, "family_p_max": FAMILY_P,
        "data_status": {"variables_missing": [] if estimates else ["frozen_gate_failed"],
                        "input_vintages": [TREATMENT, SLICE]},
        "correction": {"disposition": "new_age_specific_descriptive_followup",
                       "school_score_credit": 0},
        "limitations": [
            "Selected and correlated with earlier all-age state and international youth screens.",
            "ACS teen ratio and OEWS wage denominator use different survey universes.",
            "Missing source years and schooling/local economic confounding limit interpretation.",
            "No policy effect, causal claim, old-case rescue, school or featured credit.",
        ],
    }
    manifest = {
        "hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": prereg, "source_lock_commit": lock_commit,
        "status": label, "registration_files": registration,
        "sources": [{"path": TREATMENT, "sha256": TREATMENT_SHA},
                    {"path": SLICE, "sha256": file_sha(SLICE)}],
    }
    packet = {
        "packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": HID, "path": SPEC, "topic": "labour"},
        "preregistration": {"spec_commit": prereg, "steelman": STEELMAN,
                            "registration_files": registration},
        "reproduction": {"runner": RUNNER, "run_dir": RUN_DIR,
                         "command": f"python3 {RUN_DIR}/replication.py"},
        "verdict": {"raw": label, "bucket": label.lower(), "reason": reason},
        "data": {"source_lock": LOCK, "source_lock_commit": lock_commit,
                 "selected_slice": SLICE}, "results": estimates,
        "credit_ceiling": "descriptive calibration only; no causal/policy/school/featured credit",
    }
    primary = estimates.get("primary", {})
    sensitivity = estimates.get("preperiod_2014_2018", {})
    card = (
        f"# Result card: {HID}\n\nVerdict: **{label}**. {reason}.\n\n"
        f"Preregistration commit: `{prereg}`. Source lock commit: `{lock_commit}`.\n"
        f"Fixed sample: 50 US states plus DC in 2014–2018, 2021, 2023–2024; "
        f"{gate['complete_pairs']} complete pairs, {gate['states']} states.\n"
        "Outcome: Census ACS one-year employment/population ratio, age 16–19. "
        "Treatment: effective state minimum wage / OEWS state median hourly wage.\n"
        "Method: state/year fixed-effects OLS, state-clustered t inference.\n"
    )
    if primary:
        card += (f"Primary bite coefficient: {primary['coefficient']:+.8g} teen employment "
                 f"percentage points per one ratio unit; p={primary['p_value']:.8g}.\n"
                 f"Pre-2019 coefficient: {sensitivity['coefficient']:+.8g}; "
                 f"p={sensitivity['p_value']:.8g}.\n")
    card += ("\nThis is a selected, correlated descriptive test. It does not establish a "
             "minimum-wage effect or rescue the archived DiD claims. No school, causal, "
             "policy or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--check'], cwd=root))\n")
    chart = {"hypothesis_id": HID, "verdict": label,
             "years": list(YEARS), "n_obs": gate["complete_pairs"],
             "beta": primary.get("coefficient"), "p_value": primary.get("p_value")}
    coeff = pd.DataFrame([
        {"term": "bite_ratio_primary", **{k: primary.get(k) for k in
            ("coefficient", "std_error", "p_value", "n_obs", "n_states", "r_squared")},
         "method": primary.get("method")} if primary else {},
        {"term": "bite_ratio_preperiod", **{k: sensitivity.get(k) for k in
            ("coefficient", "std_error", "p_value", "n_obs", "n_states", "r_squared")},
         "method": sensitivity.get("method")} if sensitivity else {},
    ])
    stream = io.BytesIO()
    coeff.to_parquet(stream, index=False)
    return {
        "hypothesis.yaml": (ROOT / SPEC).read_bytes(),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False).encode(),
        "diagnostics.json": (json.dumps(diag, indent=2) + "\n").encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": card.encode(),
        "replication.py": wrapper.encode(),
        "chart_data.json": (json.dumps(chart, indent=2) + "\n").encode(),
        "coefficients.parquet": stream.getvalue(),
    }


def run(check: bool) -> dict:
    prereg, registration, _ = registered()
    lock_commit, _, _ = locked()
    runpath = ROOT / RUN_DIR
    if check:
        if not runpath.is_dir():
            raise FileNotFoundError(RUN_DIR)
        saved = json.loads((runpath / "diagnostics.json").read_text())
        stamp = saved["run_utc"]
    else:
        if runpath.exists():
            raise FileExistsError(f"{RUN_DIR} exists; use --check")
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    verdict, reason, gate, estimates, _ = calculate()
    expected = artifacts(stamp, verdict, reason, gate, estimates,
                         registration, prereg, lock_commit)
    if check:
        for filename, body in expected.items():
            if (runpath / filename).read_bytes() != body:
                raise ValueError(f"exact artifact replay mismatch: {filename}")
    else:
        runpath.mkdir(parents=True)
        for filename, body in expected.items():
            (runpath / filename).write_bytes(body)
    return {"hypothesis_id": HID, "verdict": verdict, "run_dir": RUN_DIR,
            "gate": gate, "estimate": estimates, "exact_replay": check}


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    for flag in ("preflight", "fetch-lock", "run", "check"):
        group.add_argument(f"--{flag}", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        output = preflight()
    elif args.fetch_lock:
        output = build_slice()
    else:
        output = run(args.check)
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
