#!/usr/bin/env python3
"""Four source-pinned OECD social-programme outcome calibrations.

Preflight reads country/year and categorical dimension keys only. Source lock
reads values after the preregistration commit, without computing an estimate.
Results require the source-lock commit to precede the result commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_oecd_programme_matched_outcomes_v2.py"
SLICE = "data/derived/oecd_programme_matched_outcomes_v2_source_slice.json"
FAMILY = "oecd_programme_matched_outcomes_v2_2026_10_09"
FAMILY_SIZE = 4
P_MAX = 0.025  # Two-sided Bonferroni: 0.10 / 4, including inconclusive tests.
MIN_PAIRS = 150
MIN_COUNTRIES = 20
MIN_YEARS_PER_COUNTRY = 4
YEARS = (2000, 2018)
COUNTRIES = frozenset("AUS AUT BEL BGR CAN CHE CHL COL CRI CZE DEU DNK ESP EST FIN FRA GBR GRC HRV HUN IRL ISL ISR ITA JPN KOR LTU LUX LVA MEX NLD NOR NZL PER POL PRT ROU SVK SVN SWE TUR USA".split())

SOURCES: dict[str, dict[str, Any]] = {
    "socx": {
        "source": "oecd:DSD_SOCX@DF_SOCX_AGG",
        "path": "data/vintages/oecd/DSD_SOCX_DF_SOCX_AGG@2026-05-05T210247Z.parquet",
        "sha256": "93e7e29b24dc791baf22833ae5596b4a381a366ddd0d78499bf59f7b80786124",
        "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml",
        "series_id": "DSD_SOCX@DF_SOCX_AGG",
        "key": ["REF_AREA", "period"],
    },
    "idd": {
        "source": "oecd:DSD_IDD@DF_IDD",
        "path": "data/vintages/oecd/DSD_IDD@2026-05-05T200556Z.parquet",
        "sha256": "869fa437691bda1a322f7b5463944ebbbb9066d689d5b76ed3d1a32620beb60e",
        "manifest": "data/manifests/fetch_run_2026-05-05T200618Z.yaml",
        "series_id": "DSD_IDD",
        "key": ["REF_AREA", "period"],
    },
    "mortality": {
        "source": "oecd:OECD.ELS.HD_DSD_HEALTH_STAT_DF_AMENABLE_MORT_1.0",
        "path": "data/vintages/oecd/OECD.ELS.HD_DSD_HEALTH_STAT_DF_AMENABLE_MORT_1.0@2026-05-01T071213Z.parquet",
        "sha256": "e00d243302893fb2bcf455a6d75ab8e5467a208186683d52d291f235a4279f94",
        "manifest": "data/manifests/fetch_run_2026-05-01T071226Z.yaml",
        "series_id": "OECD.ELS.HD,DSD_HEALTH_STAT@DF_AMENABLE_MORT,1.0",
        "key": ["REF_AREA", "period"],
    },
    "housing": {
        "source": "oecd:OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0",
        "path": "data/vintages/oecd/OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0@2026-07-23T150432Z.parquet",
        "sha256": "ac7581cb015748d97a21d4feadd08a3afb16cb1d5912af9e0997913ce4db65db",
        "manifest": "data/manifests/fetch_run_2026-07-23T150922Z.yaml",
        "series_id": "OECD.ELS.HD_DSD_HH_DASH_DF_HSG_INEQ_1.0",
        "key": ["REF_AREA", "period"],
    },
    "income": {
        "source": "world_bank_wdi:NY.GDP.PCAP.KD",
        "path": "data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet",
        "sha256": "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f",
        "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml",
        "series_id": "NY.GDP.PCAP.KD",
        "key": ["country_iso3", "year"],
    },
    "unemployment": {
        "source": "world_bank_wdi:SL.UEM.TOTL.ZS",
        "path": "data/vintages/world_bank_wdi/SL.UEM.TOTL.ZS@2026-05-05T200521Z.parquet",
        "sha256": "dfb2bae82f8ae7d95de21605e2d8c57f835cc7be4eeb53d58f8362da0b9e41c9",
        "manifest": "data/manifests/fetch_run_2026-05-05T200618Z.yaml",
        "series_id": "SL.UEM.TOTL.ZS",
        "key": ["country_iso3", "year"],
    },
}

SOCX_BASE = {
    "FREQ": "A", "MEASURE": "SOCX", "UNIT_MEASURE": "PT_B1GQ",
    "EXPEND_SOURCE": "ES10", "SPENDING_TYPE": "_T", "PRICE_BASE": "_Z",
    "OBS_STATUS": "A",
}
IDD_BASE = {
    "MEASURE": "PR_INC_DISP", "UNIT_MEASURE": "PT_POP",
    "METHODOLOGY": "METH2012", "DEFINITION": "D_CUR",
    "POVERTY_LINE": "PL_50", "OBS_STATUS": "A",
}
CASES: dict[str, dict[str, str]] = {
    "oecd_health_spending_treatable_mortality_panel_v2": {
        "topic": "healthcare", "programme": "TP41", "outcome_role": "mortality",
        "outcome_filter": "TRTM", "outcome_name": "next_year_treatable_deaths_per_100k",
        "treatment_name": "public_health_spending_pct_gdp",
        "old_id": "public_health_spending_avoidable_mortality_panel",
        "old_verdict": "REFUTED",
        "limitation": "Treatable mortality is a selected OECD rate; a spending share is neither service quality nor a policy intervention.",
    },
    "oecd_family_spending_child_poverty_panel_v2": {
        "topic": "distribution", "programme": "TP51", "outcome_role": "idd_child",
        "outcome_filter": "Y_LT18", "outcome_name": "next_year_child_relative_poverty_pct",
        "treatment_name": "public_family_spending_pct_gdp",
        "old_id": "oecd_socx_poverty_reduction_per_spending_point_panel",
        "old_verdict": "SUPPORTED",
        "limitation": "Family spending includes cash and services; relative poverty can change when median income changes without a change in material deprivation.",
    },
    "oecd_old_age_spending_elderly_poverty_panel_v2": {
        "topic": "welfare_architecture", "programme": "TP11", "outcome_role": "idd_elderly",
        "outcome_filter": "Y_GT65", "outcome_name": "next_year_elderly_relative_poverty_pct",
        "treatment_name": "public_old_age_spending_pct_gdp",
        "old_id": "public_pension_generosity_elderly_poverty_fiscal_tradeoff",
        "old_verdict": "PARTIAL",
        "limitation": "Old-age spending includes services and pensions; it does not measure individual benefit generosity or long-run fiscal sustainability.",
    },
    "oecd_housing_spending_cost_overburden_panel_v2": {
        "topic": "housing", "programme": "TP82", "outcome_role": "housing",
        "outcome_filter": "3_3", "outcome_name": "next_year_housing_cost_overburden_pct",
        "treatment_name": "public_housing_spending_pct_gdp",
        "old_id": "oecd_housing_cost_overburden_consumption_drag_panel",
        "old_verdict": "PARTIAL",
        "limitation": "Housing programme outlays may respond to housing stress; the OECD overburden series is a survey-based share, not a rent or supply measure.",
    },
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    p = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    if p.returncode:
        raise ValueError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout.strip()


def first_addition(relative: str) -> str:
    commits = git("log", "--diff-filter=A", "--reverse", "--format=%H", "--", relative).splitlines()
    if len(commits) != 1:
        raise ValueError(f"expected one first-addition commit for {relative}: {commits}")
    return commits[0]


def strict_ancestor(older: str, newer: str) -> bool:
    if older == newer:
        return False
    p = subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT)
    return p.returncode == 0


def spec_path(case: str) -> str:
    return f"hypotheses/{CASES[case]['topic']}/{case}.yaml"


def steelman_path(case: str) -> str:
    return f"hypotheses/steelman/{case}.md"


def source_pins() -> None:
    for role, pin in SOURCES.items():
        path = ROOT / pin["path"]
        if not path.is_file() or digest(path) != pin["sha256"]:
            raise ValueError(f"source missing or changed: {role}: {pin['path']}")
        manifest = yaml.safe_load((ROOT / pin["manifest"]).read_text())
        if not any(row.get("parquet_path") == pin["path"]
                   and row.get("sha256") == pin["sha256"]
                   and row.get("series_id") == pin["series_id"]
                   for row in manifest.get("entries", [])):
            raise ValueError(f"tracked manifest does not pin {role}")


def check_design(*, committed: bool) -> str | None:
    if len(CASES) != FAMILY_SIZE:
        raise ValueError("family size changed")
    for case, cfg in CASES.items():
        spec = yaml.safe_load((ROOT / spec_path(case)).read_text())
        threshold = spec["falsification"]["threshold"]
        source_files = {
            label: {key: SOURCES[role][key]
                    for key in ("source", "path", "sha256", "manifest", "series_id")}
            for label, role in (("treatment", "socx"),
                                ("outcome", source_role(cfg["outcome_role"])),
                                ("income", "income"),
                                ("unemployment", "unemployment"))
        }
        if (spec["hypothesis_id"] != case or spec["status"] != "pre_registered"
                or spec["claim_direction"] != "-" or spec["evidence_type"] != "associational"
                or spec["sample"]["countries"] != sorted(COUNTRIES)
                or spec["sample"]["period"] != list(YEARS)
                or spec["steelman"] != steelman_path(case)
                or spec["covers_claims"] != [] or spec["linked_hypotheses"] != []
                or spec["linked_conditions"] != []
                or threshold["family_id"] != FAMILY or threshold["family_size"] != FAMILY_SIZE
                or threshold["family_alpha"] != 0.10
                or threshold["family_p_max"] != P_MAX
                or threshold["min_observations"] != MIN_PAIRS
                or threshold["min_countries"] != MIN_COUNTRIES
                or threshold["min_pairs_per_country"] != MIN_YEARS_PER_COUNTRY
                or threshold["programme_type"] != cfg["programme"]
                or threshold["outcome_filter"] != cfg["outcome_filter"]
                or threshold["old_hypothesis_id"] != cfg["old_id"]
                or threshold["old_result_bucket"] != cfg["old_verdict"]
                or threshold["school_score_credit"] != 0
                or threshold["school_score_eligible"] is not False
                or threshold["source_files"] != source_files):
            raise ValueError(f"frozen specification changed: {case}")
        if ([(item["name"], item["source"]) for item in spec["variables"]["treatment"]]
                != [(cfg["treatment_name"], SOURCES["socx"]["source"])]) or (
                [(item["name"], item["source"]) for item in spec["variables"]["outcome"]]
                != [(cfg["outcome_name"], SOURCES[source_role(cfg["outcome_role"])]["source"])]) or (
                [(item["name"], item["source"]) for item in spec["variables"]["controls"]]
                != [("log_real_gdp_pc_at_t", SOURCES["income"]["source"]),
                    ("unemployment_pct_at_t", SOURCES["unemployment"]["source"])]):
            raise ValueError(f"measured variable roles changed: {case}")
        if not (ROOT / steelman_path(case)).is_file():
            raise ValueError(f"missing steelman: {case}")
        old_path = ROOT / "engine" / "runs" / cfg["old_id"] / "diagnostics.json"
        if json.loads(old_path.read_text())["verdict_label"] != cfg["old_verdict"]:
            raise ValueError(f"known old result changed: {case}")
    source_pins()
    if not committed:
        return None
    prereg = first_addition(RUNNER)
    frozen_runner = subprocess.run(["git", "show", f"{prereg}:{RUNNER}"], cwd=ROOT,
                                   capture_output=True, check=True).stdout
    if frozen_runner != (ROOT / RUNNER).read_bytes():
        raise ValueError("post-registration runner changed")
    for case in CASES:
        for relative in (spec_path(case), steelman_path(case)):
            if first_addition(relative) != prereg:
                raise ValueError(f"design not committed together: {relative}")
            saved = subprocess.run(["git", "show", f"{prereg}:{relative}"], cwd=ROOT,
                                   capture_output=True, check=True).stdout
            if saved != (ROOT / relative).read_bytes():
                raise ValueError(f"post-registration design changed: {relative}")
    head = git("rev-parse", "HEAD")
    if prereg != head and not strict_ancestor(prereg, head):
        raise ValueError("preregistration is not in the current history")
    return prereg


def filters(role: str) -> dict[str, str]:
    if role in ("TP41", "TP51", "TP11", "TP82"):
        return SOCX_BASE | {"PROGRAMME_TYPE": role}
    if role == "idd_child":
        return IDD_BASE | {"AGE": "Y_LT18"}
    if role == "idd_elderly":
        return IDD_BASE | {"AGE": "Y_GT65"}
    if role == "mortality":
        return {"FREQ": "A", "MEASURE": "TRTM", "UNIT_MEASURE": "DT_10P5HB", "AGE": "_T", "SEX": "_T"}
    if role == "housing":
        return {"MEASURE": "3_3", "UNIT_MEASURE": "PT_POP", "AGE": "_T", "SEX": "_T", "OBS_STATUS": "A"}
    if role == "income":
        return {"indicator_id": "NY.GDP.PCAP.KD"}
    if role == "unemployment":
        return {"indicator_id": "SL.UEM.TOTL.ZS"}
    raise ValueError(role)


def source_role(role: str) -> str:
    return "socx" if role.startswith("TP") else "idd" if role.startswith("idd_") else role


def selected_rows(role: str, *, values: bool) -> list[list[Any]]:
    import pyarrow.parquet as pq
    import pandas as pd

    pin = SOURCES[source_role(role)]
    key = pin["key"]
    selector = filters(role)
    columns = list(dict.fromkeys(key + list(selector) + (["value"] if values else [])))
    frame = pq.read_table(ROOT / pin["path"], columns=columns).to_pandas()
    for column, desired in selector.items():
        frame = frame[frame[column] == desired]
    frame = frame[frame[key[0]].isin(COUNTRIES)].copy()
    frame[key[1]] = pd.to_numeric(frame[key[1]], errors="coerce")
    frame = frame[frame[key[1]].between(2000, 2019)].copy()
    if values:
        frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
        frame = frame[frame["value"].map(math.isfinite)].copy()
    if frame.duplicated(key).any():
        raise ValueError(f"duplicate selected country/year keys in {role}")
    frame = frame.sort_values(key).reset_index(drop=True)
    return [
        [str(row[key[0]]), int(row[key[1]])] + ([float(row["value"])] if values else [])
        for _, row in frame.iterrows()
    ]


def all_roles() -> list[str]:
    return ["TP41", "TP51", "TP11", "TP82", "mortality", "idd_child", "idd_elderly", "housing", "income", "unemployment"]


def preflight() -> None:
    check_design(committed=False)
    keys = {role: {(r[0], r[1]) for r in selected_rows(role, values=False)} for role in all_roles()}
    control = keys["income"] & keys["unemployment"]
    for case, cfg in CASES.items():
        pairs = {(c, y) for c, y in keys[cfg["programme"]] & control
                 if YEARS[0] <= y <= YEARS[1] and (c, y + 1) in keys[cfg["outcome_role"]]}
        counts = Counter(c for c, _ in pairs)
        pairs = {(c, y) for c, y in pairs if counts[c] >= MIN_YEARS_PER_COUNTRY}
        print(f"{case}: key envelope {len(pairs)} pairs / {len({c for c, _ in pairs})} countries; no values read")


def source_payload(prereg: str) -> dict[str, Any]:
    return {
        "schema": "ieset-oecd-programme-matched-outcomes-source-v1",
        "family_id": FAMILY,
        "preregistration_commit": prereg,
        "source_files": {role: {k: pin[k] for k in ("path", "sha256", "manifest", "series_id")}
                         for role, pin in SOURCES.items()},
        "selectors": {role: filters(role) for role in all_roles()},
        "rows": {role: selected_rows(role, values=True) for role in all_roles()},
    }


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def lock_source() -> None:
    prereg = check_design(committed=True)
    path = ROOT / SLICE
    if path.exists():
        raise ValueError("source slice already exists; refusing overwrite")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(source_payload(prereg)))
    print(f"wrote source slice {SLICE}; commit it before fitting any model")


def verify_source() -> dict[str, Any]:
    prereg = check_design(committed=True)
    saved = (ROOT / SLICE).read_bytes()
    current = json_bytes(source_payload(prereg))
    if current != saved:
        raise ValueError("source slice differs from pinned raw files and frozen selectors")
    return json.loads(saved)


def locked_commits() -> tuple[str, str]:
    prereg = check_design(committed=True)
    lock = first_addition(SLICE)
    head = git("rev-parse", "HEAD")
    if not strict_ancestor(prereg, lock) or not (lock == head or strict_ancestor(lock, head)):
        raise ValueError("need separate preregistration, source-lock, and result commits")
    return prereg, lock


def fit_case(case: str, payload: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import pandas as pd
    import statsmodels.formula.api as smf

    cfg = CASES[case]
    rows = payload["rows"]
    treatment = pd.DataFrame(rows[cfg["programme"]], columns=["country", "year", "treatment"])
    outcome = pd.DataFrame(rows[cfg["outcome_role"]], columns=["country", "outcome_year", "outcome"])
    income = pd.DataFrame(rows["income"], columns=["country", "year", "income"])
    unemployment = pd.DataFrame(rows["unemployment"], columns=["country", "year", "unemployment"])
    treatment["outcome_year"] = treatment["year"] + 1
    frame = treatment.merge(outcome, on=["country", "outcome_year"], validate="one_to_one")
    frame = frame.merge(income, on=["country", "year"], validate="one_to_one")
    frame = frame.merge(unemployment, on=["country", "year"], validate="one_to_one")
    frame = frame[frame["year"].between(*YEARS) & (frame["income"] > 0)].copy()
    count = frame.groupby("country")["year"].transform("count")
    frame = frame[count >= MIN_YEARS_PER_COUNTRY].copy()
    frame["log_income"] = np.log(frame["income"])
    n, countries = len(frame), frame["country"].nunique()
    preflight = {"observations": n, "countries": int(countries),
                 "treatment_years": [int(frame.year.min()), int(frame.year.max())] if n else [],
                 "passed": bool(n >= MIN_PAIRS and countries >= MIN_COUNTRIES)}
    if not preflight["passed"]:
        return {"verdict": "INCONCLUSIVE", "reason": "frozen complete-case floor failed", "preflight": preflight, "estimate": None}
    result = smf.ols(
        "outcome ~ treatment + log_income + unemployment + C(country) + C(year)",
        data=frame,
    ).fit(cov_type="cluster", cov_kwds={"groups": frame["country"]}, use_t=True)
    if result.model.rank != len(result.params):
        return {"verdict": "INCONCLUSIVE", "reason": "primary model rank deficient", "preflight": preflight, "estimate": None}
    coefficient, se, p = (float(result.params["treatment"]),
                          float(result.bse["treatment"]), float(result.pvalues["treatment"]))
    ci = [float(x) for x in result.conf_int().loc["treatment"].tolist()]
    if not all(math.isfinite(x) for x in [coefficient, se, p, *ci]) or se <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "primary uncertainty unidentified", "preflight": preflight, "estimate": None}
    verdict = "SUPPORTED" if coefficient < 0 and p <= P_MAX else "REFUTED" if coefficient > 0 and p <= P_MAX else "PARTIAL"
    reason = ("negative measured association clears the frozen four-test threshold" if verdict == "SUPPORTED"
              else "opposite-sign association clears the frozen four-test threshold" if verdict == "REFUTED"
              else "estimable association does not clear the frozen four-test directional rule")
    return {
        "verdict": verdict, "reason": reason, "preflight": preflight,
        "estimate": {"coefficient": coefficient, "std_error": se, "p_value": p,
                     "ci95": ci, "n_obs": n, "n_countries": int(countries),
                     "r_squared": float(result.rsquared),
                     "method": "country/year FE OLS, country-clustered t inference"},
    }


def artifacts(case: str, outcome: dict[str, Any], *, prereg: str, lock: str, run_utc: str) -> dict[str, bytes]:
    cfg = CASES[case]
    role = source_role(cfg["outcome_role"])
    input_roles = ["socx", role, "income", "unemployment"]
    vintages = [
        {"role": x, "source": SOURCES[x]["source"], "vintage_file": SOURCES[x]["path"],
         "sha256": SOURCES[x]["sha256"], "source_manifest": SOURCES[x]["manifest"],
         "series_id": SOURCES[x]["series_id"]} for x in input_roles
    ]
    correction = {"disposition": "descriptive_calibration_only", "school_score_eligible": False, "school_score_credit": 0}
    limitations = [
        "Measured association only; no causal, programme-effect, or policy-effect inference.",
        "The related historical proxy result was visible before this new registration; sample countries can overlap it.",
        "Preflight inspected source dimension keys and numeric availability masks, not magnitudes, signs, or estimates.",
        "All four tests remain in the family correction even if a member is inconclusive.",
        "No school claim or position receives score credit.", cfg["limitation"],
    ]
    diagnostics = {
        "hypothesis_id": case, "verdict": outcome["verdict"], "verdict_label": outcome["verdict"],
        "verdict_reason": outcome["reason"], "run_utc": run_utc, "runner": RUNNER,
        "preregistration_commit": prereg, "source_lock_commit": lock,
        "template": "panel_fe", "preflight": outcome["preflight"], "estimate": outcome["estimate"],
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_p_max": P_MAX,
        "data_status": {"variables_missing": [], "input_vintages": vintages},
        "limitations": limitations, "correction": correction,
    }
    manifest = {
        "hypothesis_id": case, "run_utc": run_utc, "runner": RUNNER,
        "preregistration_commit": prereg, "source_lock_commit": lock,
        "source_slice": SLICE, "source_slice_sha256": digest(ROOT / SLICE),
        "status": outcome["verdict"], "old_hypothesis_id": cfg["old_id"],
        "old_verdict": cfg["old_verdict"], "vintages": vintages,
        "derived_panel": outcome["preflight"], "correction": correction,
    }
    packet = {
        "packet_version": 1, "generated_utc": run_utc,
        "hypothesis": {"id": case, "path": spec_path(case), "topic": cfg["topic"]},
        "preregistration": {"spec_commit": prereg, "steelman": steelman_path(case),
                            "family_id": FAMILY, "family_p_max": P_MAX},
        "reproduction": {"runner": RUNNER, "run_dir": f"engine/runs/{case}",
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": outcome["verdict"], "bucket": outcome["verdict"].lower(),
                    "reason": outcome["reason"]},
        "data": {"inputs": vintages, "source_slice": SLICE, "source_slice_sha256": digest(ROOT / SLICE)},
        "results": outcome["estimate"] or outcome["preflight"],
        "limitations": limitations, "correction": correction,
    }
    estimate = outcome["estimate"]
    estimate_line = (
        f"Coefficient {estimate['coefficient']:+.9g}; clustered SE {estimate['std_error']:.9g}; "
        f"p={estimate['p_value']:.9g}."
        if estimate else "No directional coefficient was interpreted."
    )
    card = (
        f"# Result card: {case}\n\n"
        f"Verdict: **{outcome['verdict']}**. {outcome['reason']}.\n\n"
        f"Known related old proxy: {cfg['old_id']} ({cfg['old_verdict']}); source pair and endpoint differ.\n"
        f"Preregistration commit: {prereg}. Source-lock commit: {lock}.\n"
        f"Complete-case sample: {outcome['preflight']['observations']} country-years, "
        f"{outcome['preflight']['countries']} countries.\n"
        f"Family threshold: two-sided p <= {P_MAX:.3f} across four frozen tests.\n"
        f"{estimate_line}\n\n"
        f"Measurement boundary: {cfg['limitation']}\n"
        "Descriptive calibration only; no causal, policy, or school-score credit.\n"
    )
    replication = (
        "#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root = Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable, str(root / '{RUNNER}'), '--verify'], cwd=root))\n"
    )
    return {
        "diagnostics.json": json_bytes(diagnostics),
        "manifest.yaml": yaml.safe_dump(manifest, sort_keys=False).encode(),
        "evidence_packet.yaml": yaml.safe_dump(packet, sort_keys=False).encode(),
        "result_card.md": card.encode(),
        "replication.py": replication.encode(),
        "hypothesis.yaml": (ROOT / spec_path(case)).read_bytes(),
    }


def run(*, verify: bool) -> None:
    payload = verify_source()
    prereg, lock = locked_commits()
    if payload["preregistration_commit"] != prereg:
        raise ValueError("source slice points to a different preregistration")
    if verify:
        first = ROOT / "engine" / "runs" / next(iter(CASES)) / "diagnostics.json"
        run_utc = json.loads(first.read_text())["run_utc"]
    else:
        run_utc = datetime.now(timezone.utc).isoformat()
    for case in CASES:
        outcome = fit_case(case, payload)
        expected = artifacts(case, outcome, prereg=prereg, lock=lock, run_utc=run_utc)
        run_dir = ROOT / "engine" / "runs" / case
        if verify:
            for name, data in expected.items():
                if (run_dir / name).read_bytes() != data:
                    raise ValueError(f"replay mismatch: {case}/{name}")
            print(f"verified {case}: {outcome['verdict']}")
        else:
            if run_dir.exists():
                raise ValueError(f"run already exists; refusing overwrite: {case}")
            run_dir.mkdir(parents=True)
            for name, data in expected.items():
                (run_dir / name).write_bytes(data)
            print(f"wrote {case}: {outcome['verdict']}; {outcome['preflight']['observations']} pairs / {outcome['preflight']['countries']} countries")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ("preflight", "source-lock", "verify-source", "run", "verify"):
        group.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        preflight()
    elif args.source_lock:
        lock_source()
    elif args.verify_source:
        verify_source()
        print("verified frozen source slice")
    else:
        run(verify=args.verify)


if __name__ == "__main__":
    main()
