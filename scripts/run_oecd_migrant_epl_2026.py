#!/usr/bin/env python3
"""Frozen OECD tertiary migrant/native employment gap and EPL calibration.

Key and source checks never open measured values. The measured run requires a
separate committed preregistration and a later committed source lock.
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
HID = "oecd_migrant_tertiary_employment_gap_epl_forward_2026"
SPEC_REL = f"hypotheses/labour/{HID}.yaml"
STEELMAN_REL = f"hypotheses/steelman/{HID}.md"
PREREG_REL = "engine/audits/oecd_migrant_epl_prereg_2026-10-09.md"
RUNNER_REL = "scripts/run_oecd_migrant_epl_2026.py"
ROSTER_REL = "data/pinned_evidence/oecd_migrant_epl_key_roster_2026.csv"
CROSSWALK_REL = "data/pinned_evidence/oecd_migrant_epl_crosswalk_2026.csv"
LOCK_REL = "data/pinned_evidence/oecd_migrant_epl_2026.manifest.json"
RUN_REL = f"engine/runs/{HID}"
MIG_REL = "data/vintages/oecd/OECD.ELS.IMD_DSD_MIG_DF_MIG_EMP_EDU_1.0@2026-07-23T150450Z.parquet"
EPL_REL = "data/vintages/oecd/OECD.ELS.EMP_DSD_EPL_OV_DF_EPL_OV_1.0@2026-07-23T154113Z.parquet"
MIG_SHA = "96b522cb77e78684c050d96efb7412489773b735243d6ada537e757817c25536"
EPL_SHA = "8a25f91e01153564e8db18723e69ed41298c339255a6ac41b67942dc86022fcd"
ROSTER_SHA = "ac9afc86da547c01e9dc11b73e628f5d147e1be4ef7636196f0fb253ad43b8e5"
CROSSWALK_SHA = "9bc900291ab4ecb0764397964ff4c762b6dfa03adb640c491a136f0c0b1253f3"
P_MAX = 0.005
EFFECT_MIN = 1.0  # Percentage-point gap change per one EPL index point.
MIN_ROWS = 200
MIN_COUNTRIES = 25
MIN_YEARS_PER_COUNTRY = 3
MIN_CHANGING_COUNTRIES = 10
MIN_CHANGE_ROWS = 20
CHANGE_MIN = 0.05  # EPL index point, used only for identification floor.
MIG_DIMS = {
    "CITIZENSHIP": "_Z", "FREQ": "A", "MEASURE": "EMP_WAP",
    "SEX": "_T", "EDUCATION_LEV": "ISCED11_5T8", "UNIT_MEASURE": "PT_POP_SUB",
}
EPL_INDICATOR = "EPR_V1"
SOURCES = {
    "outcome": {"publisher": "oecd", "series_id": "OECD.ELS.IMD,DSD_MIG@DF_MIG_EMP_EDU,1.0",
                "path": MIG_REL, "sha256": MIG_SHA,
                "manifest": "data/manifests/fetch_run_2026-07-23T150922Z.yaml"},
    "treatment": {"publisher": "oecd", "series_id": "OECD.ELS.EMP,DSD_EPL_OV@DF_EPL_OV,1.0",
                  "path": EPL_REL, "sha256": EPL_SHA,
                  "manifest": "data/manifests/fetch_run_2026-07-23T154936Z.yaml"},
}
CORRECTION = {"disposition": "descriptive_calibration_only", "school_score_eligible": False,
              "school_score_credit": 0, "policy_score_eligible": False,
              "policy_score_credit": 0, "featured_eligible": False}
LIMITATIONS = [
    "Foreign-born versus native-born tertiary employment-rate differences are population comparisons, not immigrant arrival-cohort effects or migration flows.",
    "EPR_V1 is regular-worker employment protection (0-6, higher stricter), not immigration policy or an individual migrant treatment.",
    "Country and year effects and a forward window do not remove reform endogeneity, composition changes, or differential COVID-era shocks.",
    "The archived Australia migration-employment and EPL unemployment screens were visible; some older specs mislabel this OECD employment-rate feed as an attainment share.",
    "The two-sided p<=0.005 rule is a conservative local screen, not global family-wise correction of the visible research search.",
    "No school, policy, causal, or featured credit follows from this descriptive association.",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git_output(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(relative: str) -> str:
    lines = git_output("log", "--diff-filter=A", "--format=%H", "HEAD", "--", relative).decode().splitlines()
    if not lines:
        raise RuntimeError(f"missing first-addition commit: {relative}")
    return lines[-1]


def committed_unchanged(relative: str, revision: str) -> None:
    path = ROOT / relative
    if not path.is_file() or path.read_bytes() != git_output("show", f"{revision}:{relative}"):
        raise RuntimeError(f"frozen file differs from its first commit: {relative}")
    if git_output("status", "--porcelain", "--", relative).strip():
        raise RuntimeError(f"uncommitted change to frozen file: {relative}")


def registration_commit() -> str:
    frozen = [SPEC_REL, STEELMAN_REL, PREREG_REL, RUNNER_REL, ROSTER_REL, CROSSWALK_REL]
    revisions = {first_addition(path) for path in frozen}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one shared first-addition commit")
    revision = revisions.pop()
    for path in frozen:
        committed_unchanged(path, revision)
    if git_output("ls-tree", "-r", "--name-only", revision, "--", RUN_REL).strip():
        raise RuntimeError("registration commit already contains run artifacts")
    spec = yaml.safe_load((ROOT / SPEC_REL).read_text())
    threshold = spec["falsification"]["threshold"]
    required = {"p_max_two_sided": P_MAX, "absolute_pp_effect_min": EFFECT_MIN,
                "min_valid_rows": MIN_ROWS, "min_valid_countries": MIN_COUNTRIES,
                "min_years_per_country": MIN_YEARS_PER_COUNTRY,
                "min_changing_countries": MIN_CHANGING_COUNTRIES,
                "min_change_rows": MIN_CHANGE_ROWS,
                "minimum_epl_change_for_variation": CHANGE_MIN,
                "expected_key_rows": 265, "expected_key_countries": 31,
                "roster_sha256": ROSTER_SHA, "crosswalk_sha256": CROSSWALK_SHA,
                "school_score_eligible": False, "school_score_credit": 0,
                "policy_score_eligible": False, "policy_score_credit": 0}
    if any(threshold.get(key) != value for key, value in required.items()):
        raise RuntimeError("registered thresholds differ from frozen runner")
    if (spec.get("hypothesis_id") != HID or spec.get("status") != "pre_registered"
            or spec.get("evidence_type") != "associational"
            or spec.get("covers_claims") != [] or spec.get("linked_hypotheses") != []
            or spec.get("linked_conditions") != [] or spec.get("steelman") != STEELMAN_REL):
        raise RuntimeError("registered descriptive hypothesis content changed")
    for role, source in SOURCES.items():
        if threshold["source_files"][role] != {k: source[k] for k in ("path", "sha256", "manifest")}:
            raise RuntimeError(f"registered source pin differs: {role}")
    return revision


def check_sources() -> None:
    for role, source in SOURCES.items():
        if sha256(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"{role} source SHA-256 mismatch")
        manifest = yaml.safe_load((ROOT / source["manifest"]).read_text())
        matches = [entry for entry in manifest.get("entries", [])
                   if entry.get("publisher") == source["publisher"]
                   and entry.get("series_id") == source["series_id"]
                   and entry.get("parquet_path") == source["path"]]
        if len(matches) != 1 or matches[0].get("sha256") != source["sha256"]:
            raise RuntimeError(f"{role} manifest entry or SHA-256 mismatch")


def load_crosswalk() -> dict[str, str]:
    raw = (ROOT / CROSSWALK_REL).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CROSSWALK_SHA:
        raise RuntimeError("frozen crosswalk SHA-256 mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    pairs = [(r["epl_country"], r["country_iso3"]) for r in records]
    if len(pairs) != 35 or len(set(pairs)) != 35 or len({a for a, _ in pairs}) != 35 or len({b for _, b in pairs}) != 35:
        raise RuntimeError("frozen crosswalk has duplicate or missing countries")
    return dict(pairs)


def load_roster() -> list[tuple[str, int]]:
    raw = (ROOT / ROSTER_REL).read_bytes()
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA or not raw.startswith(b"country_iso3,year\n"):
        raise RuntimeError("frozen key roster SHA-256 or header mismatch")
    records = list(csv.DictReader(io.StringIO(raw.decode())))
    rows = [(r["country_iso3"], int(r["year"])) for r in records]
    if (len(rows) != 265 or len(set(rows)) != len(rows)
            or len({c for c, _ in rows}) != 31
            or rows != sorted(rows, key=lambda x: (x[1], x[0]))
            or any(not 2015 <= y <= 2023 for _, y in rows)):
        raise RuntimeError("frozen key roster invalid")
    return rows


def source_keys() -> tuple[set[tuple[str, int]], set[tuple[str, int]], dict[str, str]]:
    """Read dimensions and keys only, never measured values or status masks."""
    crosswalk = load_crosswalk()
    mcols = ["REF_AREA", "BIRTH_PLACE", "period", *MIG_DIMS]
    migration = pd.read_parquet(ROOT / MIG_REL, columns=mcols)
    if len(migration) != 2711:
        raise RuntimeError("migration raw row count changed")
    selected = migration.copy()
    for column, expected in MIG_DIMS.items():
        selected = selected.loc[selected[column].eq(expected)]
    selected = selected.loc[selected.BIRTH_PLACE.isin(["FB", "NB"])].copy()
    selected["year"] = selected.period.astype(int)
    if len(selected) != 672 or selected.duplicated(["REF_AREA", "year", "BIRTH_PLACE"]).any():
        raise RuntimeError("migration selected dimension/key contract changed")
    grouped = selected.groupby(["REF_AREA", "year"]).BIRTH_PLACE.agg(set)
    migration_keys = {(str(c), int(y)) for (c, y), places in grouped.items() if places == {"FB", "NB"}}
    epl = pd.read_parquet(ROOT / EPL_REL, columns=["country", "year", "indicator", "indicator_label"])
    if (len(epl) != 1355 or epl.indicator.nunique() != 1
            or not epl.indicator.eq(EPL_INDICATOR).all()
            or epl.duplicated(["country", "year", "indicator"]).any()
            or not epl.indicator_label.eq("Employment protection for regular workers, summary indicator, Version 1").all()):
        raise RuntimeError("EPL dimension/key contract changed")
    names = set(epl.country)
    if not set(crosswalk).issubset(names):
        raise RuntimeError("frozen crosswalk names absent from EPL")
    selected_epl = epl.loc[epl.country.isin(crosswalk)]
    epl_keys = {(crosswalk[name], int(year)) for name, year in selected_epl[["country", "year"]].itertuples(index=False, name=None)}
    if len(epl_keys) != len(selected_epl):
        raise RuntimeError("EPL ISO3 crosswalk creates duplicate country-years")
    return migration_keys, epl_keys, crosswalk


def key_preflight() -> dict[str, Any]:
    migration_keys, epl_keys, crosswalk = source_keys()
    allowed = set(crosswalk.values())
    candidates = {(c, y) for c, y in migration_keys if c in allowed and 2015 <= y <= 2023
                  and (c, y + 1) in migration_keys and (c, y - 1) in epl_keys and (c, y) in epl_keys}
    counts = Counter(c for c, _ in candidates)
    chosen = sorted(((c, y) for c, y in candidates if counts[c] >= MIN_YEARS_PER_COUNTRY),
                    key=lambda x: (x[1], x[0]))
    if len(candidates) != 270 or len(counts) != 35 or chosen != load_roster():
        raise RuntimeError("frozen key-only roster differs from source dimensions")
    return {"candidate_key_rows": len(candidates), "candidate_countries": len(counts),
            "roster_rows": len(chosen), "roster_countries": len({c for c, _ in chosen}),
            "roster_years": [min(y for _, y in chosen), max(y for _, y in chosen)],
            "roster_sha256": ROSTER_SHA, "crosswalk_sha256": CROSSWALK_SHA,
            "measured_values_read": False}


def lock_payload(revision: str, preflight: dict[str, Any]) -> dict[str, Any]:
    return {"hypothesis_id": HID, "preregistration_commit": revision,
            "source_files": SOURCES,
            "key_roster": {"path": ROSTER_REL, "sha256": ROSTER_SHA},
            "country_crosswalk": {"path": CROSSWALK_REL, "sha256": CROSSWALK_SHA},
            "key_preflight": preflight, "value_access_before_source_lock": False}


def write_source_lock() -> None:
    revision = registration_commit()
    check_sources()
    preflight = key_preflight()
    path = ROOT / LOCK_REL
    if path.exists():
        raise FileExistsError(f"source lock already exists: {LOCK_REL}")
    path.write_text(json.dumps(lock_payload(revision, preflight), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK_REL}; commit separately before measured values")


def check_source_lock(revision: str, preflight: dict[str, Any]) -> str:
    path = ROOT / LOCK_REL
    if json.loads(path.read_text()) != lock_payload(revision, preflight):
        raise RuntimeError("committed source lock differs from preregistration contract")
    lock_commit = first_addition(LOCK_REL)
    if lock_commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, lock_commit], cwd=ROOT).returncode != 0:
        raise RuntimeError("source lock did not follow registration")
    committed_unchanged(LOCK_REL, lock_commit)
    if git_output("ls-tree", "-r", "--name-only", lock_commit, "--", RUN_REL).strip():
        raise RuntimeError("source-lock commit already contains result artifacts")
    return lock_commit


def finite_range(value: Any, lower: float, upper: float) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numeric if math.isfinite(numeric) and lower <= numeric <= upper else None


def measured_panel(roster: list[tuple[str, int]], crosswalk: dict[str, str]) -> tuple[pd.DataFrame, dict[str, int]]:
    """First numeric access, called only after the two Git custody checks."""
    mcols = ["REF_AREA", "BIRTH_PLACE", "period", "value", *MIG_DIMS]
    migration = pd.read_parquet(ROOT / MIG_REL, columns=mcols)
    for column, expected in MIG_DIMS.items():
        migration = migration.loc[migration[column].eq(expected)]
    migration = migration.loc[migration.BIRTH_PLACE.isin(["FB", "NB"])].copy()
    migration["year"] = migration.period.astype(int)
    mvals = {(str(c), int(y), str(b)): v for c, y, b, v in migration[["REF_AREA", "year", "BIRTH_PLACE", "value"]].itertuples(index=False, name=None)}
    epl = pd.read_parquet(ROOT / EPL_REL, columns=["country", "year", "indicator", "value"])
    epl = epl.loc[epl.indicator.eq(EPL_INDICATOR) & epl.country.isin(crosswalk)]
    evals = {(crosswalk[str(c)], int(y)): v for c, y, v in epl[["country", "year", "value"]].itertuples(index=False, name=None)}
    records = []
    invalid = 0
    for country, year in roster:
        needed_m = {(offset, birth): finite_range(mvals.get((country, year + offset, birth)), 0, 100)
                    for offset in (0, 1) for birth in ("FB", "NB")}
        prev = finite_range(evals.get((country, year - 1)), 0, 6)
        current = finite_range(evals.get((country, year)), 0, 6)
        if prev is None or current is None or any(v is None for v in needed_m.values()):
            invalid += 1
            continue
        gap_t = needed_m[(0, "NB")] - needed_m[(0, "FB")]
        gap_next = needed_m[(1, "NB")] - needed_m[(1, "FB")]
        records.append({"country_iso3": country, "year": year,
                        "forward_gap_change_pp": gap_next - gap_t,
                        "epl_change": current - prev})
    panel = pd.DataFrame.from_records(records, columns=["country_iso3", "year", "forward_gap_change_pp", "epl_change"])
    complete_rows = len(panel)
    complete_countries = int(panel.country_iso3.nunique())
    counts = panel.country_iso3.value_counts()
    panel = panel.loc[panel.country_iso3.map(counts).ge(MIN_YEARS_PER_COUNTRY)].copy()
    change_mask = panel.epl_change.abs().ge(CHANGE_MIN)
    gate = {"roster_rows": len(roster), "invalid_value_key_rows": invalid,
            "complete_case_rows_before_country_floor": complete_rows,
            "complete_case_countries_before_country_floor": complete_countries,
            "valid_rows": len(panel), "valid_countries": int(panel.country_iso3.nunique()),
            "countries_with_material_epl_change": int(panel.loc[change_mask, "country_iso3"].nunique()),
            "country_years_with_material_epl_change": int(change_mask.sum()),
            "measured_values_read_after_lock": True}
    return panel, gate


def clustered_term(panel: pd.DataFrame) -> dict[str, Any] | None:
    if panel.empty:
        return None
    model = smf.ols("forward_gap_change_pp ~ epl_change + C(country_iso3) + C(year)", data=panel)
    if model.exog.shape[0] != len(panel) or np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return None
    countries = panel.country_iso3
    groups = int(countries.nunique())
    if groups <= 1:
        return None
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": countries,
                                                  "use_correction": True,
                                                  "df_correction": True}, use_t=True)
    beta, se = float(fit.params["epl_change"]), float(fit.bse["epl_change"])
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return None
    p = float(2 * student_t.sf(abs(beta / se), groups - 1))
    half = float(student_t.ppf(0.975, groups - 1) * se)
    if not math.isfinite(p) or not math.isfinite(half):
        return None
    return {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
            "confidence_level": 0.95, "confidence_interval": [beta - half, beta + half],
            "n_rows": len(panel), "n_countries": groups, "df_inference": groups - 1,
            "model_rank": int(fit.model.rank),
            "method": "country/year FE OLS, country-cluster CR1 finite correction, Student t(G-1)"}


def estimate(roster: list[tuple[str, int]], crosswalk: dict[str, str]) -> dict[str, Any]:
    panel, gate = measured_panel(roster, crosswalk)
    floor = (gate["valid_rows"] >= MIN_ROWS and gate["valid_countries"] >= MIN_COUNTRIES
             and gate["countries_with_material_epl_change"] >= MIN_CHANGING_COUNTRIES
             and gate["country_years_with_material_epl_change"] >= MIN_CHANGE_ROWS)
    if not floor:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "frozen sample or EPL variation floor failed",
                "primary": None, "pandemic_window_diagnostic": None}
    primary = clustered_term(panel)
    if primary is None:
        return {"gate": gate, "verdict": "INCONCLUSIVE",
                "reason": "country/year fixed-effect rank or country-cluster uncertainty failed",
                "primary": None, "pandemic_window_diagnostic": None}
    # Diagnostic only: omit t=2019-2021, which places the forward window in the pandemic.
    diagnostic = clustered_term(panel.loc[~panel.year.isin([2019, 2020, 2021])].copy())
    beta, p = primary["coefficient"], primary["p_value_two_sided"]
    if beta >= EFFECT_MIN and p <= P_MAX:
        verdict, reason = "SUPPORTED", "positive descriptive association clears frozen magnitude and local p threshold"
    elif beta <= -EFFECT_MIN and p <= P_MAX:
        verdict, reason = "REFUTED", "negative descriptive association clears frozen magnitude and local p threshold"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"gate": gate, "verdict": verdict, "reason": reason,
            "primary": primary, "pandemic_window_diagnostic": diagnostic}


def artifacts(revision: str, lock_commit: str, result: dict[str, Any], stamp: str) -> dict[str, Any]:
    verdict = result["verdict"]
    packet = {"packet_version": 1, "generated_utc": stamp,
              "hypothesis": {"id": HID, "path": SPEC_REL, "topic": "labour"},
              "preregistration": {"spec_commit": revision, "source_lock_commit": lock_commit,
                                  "steelman": STEELMAN_REL, "key_roster": ROSTER_REL,
                                  "key_roster_sha256": ROSTER_SHA,
                                  "country_crosswalk": CROSSWALK_REL,
                                  "country_crosswalk_sha256": CROSSWALK_SHA},
              "reproduction": {"runner": RUNNER_REL, "run_dir": RUN_REL,
                               "command": f"python3 {RUNNER_REL} --verify"},
              "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
              "data": {"inputs": SOURCES, "key_roster": ROSTER_REL, "sample": result["gate"]},
              "results": {"primary": result["primary"],
                          "pandemic_window_diagnostic": result["pandemic_window_diagnostic"]},
              "limitations": LIMITATIONS, "correction": CORRECTION}
    diagnostics = {"hypothesis_id": HID, "verdict": verdict, "verdict_label": verdict,
                   "verdict_reason": result["reason"], "run_utc": stamp, "runner": RUNNER_REL,
                   "preregistration_commit": revision, "source_lock_commit": lock_commit,
                   "source_lock": LOCK_REL, "template": "panel_fe", "preflight": result["gate"],
                   "primary": result["primary"],
                   "pandemic_window_diagnostic": result["pandemic_window_diagnostic"],
                   "p_max_two_sided": P_MAX, "absolute_pp_effect_min": EFFECT_MIN,
                   "data_status": {"variables_missing": [], "input_vintages": list(SOURCES.values())},
                   "limitations": LIMITATIONS, "correction": CORRECTION}
    manifest = {"hypothesis_id": HID, "run_utc": stamp, "runner": RUNNER_REL,
                "preregistration_commit": revision, "source_lock_commit": lock_commit,
                "source_lock": LOCK_REL, "status": verdict, "vintages": list(SOURCES.values()),
                "derived_panel": result["gate"], "correction": CORRECTION}
    card = (f"# Result card: {HID}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Frozen preregistration: `{revision}`; source-lock commit: `{lock_commit}`.\n\n"
            f"Key-only roster: 265 country-years, 31 countries, t=2015–2023. "
            f"Valid complete cases after the predeclared country floor: {result['gate']['valid_rows']} "
            f"rows in {result['gate']['valid_countries']} countries; "
            f"material EPL changes: {result['gate']['country_years_with_material_epl_change']} "
            f"rows in {result['gate']['countries_with_material_epl_change']} countries.\n")
    if result["primary"] is not None:
        primary = result["primary"]
        card += (f"\nPrimary gap-change association: beta={primary['coefficient']:+.6g} percentage points "
                 f"per EPL index point, cluster SE={primary['std_error']:.6g}, "
                 f"two-sided t p={primary['p_value_two_sided']:.6g}, "
                 f"95% CI={primary['confidence_interval']}.\n")
        diagnostic = result["pandemic_window_diagnostic"]
        if diagnostic is not None:
            card += (f"Pandemic-window exclusion (diagnostic only): beta={diagnostic['coefficient']:+.6g}, "
                     f"p={diagnostic['p_value_two_sided']:.6g}, "
                     f"n={diagnostic['n_rows']} in {diagnostic['n_countries']} countries.\n")
        else:
            card += "Pandemic-window exclusion diagnostic was not estimable.\n"
    card += (f"\nDirectional gate: |beta| >= {EFFECT_MIN:g} pp per EPL point and two-sided p <= {P_MAX}; "
             "failed sample or variation floors are INCONCLUSIVE. The pandemic diagnostic cannot change the verdict.\n\n"
             "This is a descriptive country-panel association. It does not identify EPL's causal effect on migrants, "
             "measure migration flows, or evaluate immigration policy. Existing related research was visible. "
             "Zero school, policy, causal, or featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER_REL!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": HID, "verdict": verdict, "primary": result["primary"],
             "pandemic_window_diagnostic": result["pandemic_window_diagnostic"]}
    coeff = [{"term": "epl_change", **result["primary"]}] if result["primary"] is not None else []
    return {"packet": packet, "diagnostics": diagnostics, "manifest": manifest,
            "card": card, "wrapper": wrapper, "chart": chart, "coefficients": coeff}


def write_artifacts(payload: dict[str, Any]) -> None:
    folder = ROOT / RUN_REL
    if folder.exists():
        raise FileExistsError(f"result directory already exists: {RUN_REL}")
    folder.mkdir(parents=True)
    (folder / "hypothesis.yaml").write_bytes((ROOT / SPEC_REL).read_bytes())
    (folder / "diagnostics.json").write_text(json.dumps(payload["diagnostics"], indent=2) + "\n")
    (folder / "manifest.yaml").write_text(yaml.safe_dump(payload["manifest"], sort_keys=False))
    (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(payload["packet"], sort_keys=False))
    (folder / "result_card.md").write_text(payload["card"])
    (folder / "replication.py").write_text(payload["wrapper"])
    (folder / "chart_data.json").write_text(json.dumps(payload["chart"], indent=2) + "\n")
    pd.DataFrame(payload["coefficients"]).to_parquet(folder / "coefficients.parquet", index=False)


def equal_close(actual: Any, expected: Any, label: str) -> None:
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


def verify_artifacts(revision: str, lock_commit: str, result: dict[str, Any]) -> None:
    folder = ROOT / RUN_REL
    saved = json.loads((folder / "diagnostics.json").read_text())
    expected = artifacts(revision, lock_commit, result, saved["run_utc"])
    equal_close(saved, expected["diagnostics"], "diagnostics")
    equal_close(yaml.safe_load((folder / "manifest.yaml").read_text()), expected["manifest"], "manifest")
    equal_close(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), expected["packet"], "evidence_packet")
    equal_close(json.loads((folder / "chart_data.json").read_text()), expected["chart"], "chart_data")
    if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / SPEC_REL).read_bytes()
            or (folder / "result_card.md").read_text() != expected["card"]
            or (folder / "replication.py").read_text() != expected["wrapper"]):
        raise AssertionError("stored study text differs from exact replay")
    equal_close(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"),
                expected["coefficients"], "coefficients")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check-sources", action="store_true")
    action.add_argument("--preflight", action="store_true")
    action.add_argument("--write-source-lock", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    check_sources()
    if args.check_sources:
        print("OECD migration and EPL source SHA-256 pins match; measured values not opened")
        return 0
    if args.preflight:
        print(json.dumps(key_preflight(), indent=2, sort_keys=True))
        return 0
    if args.write_source_lock:
        write_source_lock()
        return 0
    revision = registration_commit()
    preflight = key_preflight()
    lock_commit = check_source_lock(revision, preflight)
    if args.run and (ROOT / RUN_REL).exists():
        raise FileExistsError(f"result directory already exists: {RUN_REL}")
    result = estimate(load_roster(), load_crosswalk())
    if args.run:
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        write_artifacts(artifacts(revision, lock_commit, result, stamp))
        print(HID, result["verdict"], result["reason"])
        return 0
    verify_artifacts(revision, lock_commit, result)
    print("verified exact replay", HID, result["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
