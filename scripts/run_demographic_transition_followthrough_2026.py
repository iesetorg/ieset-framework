#!/usr/bin/env python3
"""Frozen six-margin demographic-transition descriptive family.

--prepare reads fertility and income values, but only country/year/indicator
keys from selected outcomes. --run cannot open outcome values or null masks
until the registration and a separate source-lock commit both exist.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pycountry
import statsmodels.formula.api as smf
import yaml
from scipy.stats import t as student_t


ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_demographic_transition_followthrough_2026.py"
PREREG = "engine/audits/demographic_transition_followthrough_prereg_2026-10-10.md"
ROSTER = "data/pinned_evidence/demographic_transition_followthrough_2026_key_roster.csv"
LOCK = "data/pinned_evidence/demographic_transition_followthrough_2026.manifest.json"
SUMMARY = "engine/audits/demographic_transition_followthrough_results_2026-10-10.md"
FAMILY = "demographic_transition_followthrough_2026_10_10"
ISO3 = frozenset(country.alpha_3 for country in pycountry.countries)
ANCHORS = (1995, 2005)
ROSTER_ROWS, ROSTER_COUNTRIES = 334, 167
PREFLIGHT_MATERIAL_ROWS, PREFLIGHT_MATERIAL_COUNTRIES = 183, 112
MATERIAL_FERTILITY_DECLINE = 0.5
MIN_ROWS, MIN_COUNTRIES = 250, 120
MIN_MATERIAL_ROWS, MIN_MATERIAL_COUNTRIES = 100, 65
MAX_TOP_ONE_PERCENT_X_SHARE = 0.30
MAX_COUNTRY_X_SHARE = 0.15
MAX_ANCHOR_X_SHARE = 0.65
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / 6

MANIFESTS = {
    "old": ("data/manifests/fetch_run_2026-04-30T130536Z.yaml", "ab56887949d3a51f3e3001ac1065c62538af1db4d4a722e39e29a774447f511b"),
    "main": ("data/manifests/fetch_run_2026-05-05T200056Z.yaml", "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945"),
    "productivity": ("data/manifests/fetch_run_2026-04-30T141104Z.yaml", "588d991d5f5a2224fe59f6490d06169d80b898dfbefa1d02a43a45e339a355d6"),
    "bootstrap": ("data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml", "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e"),
    "later": ("data/manifests/fetch_run_2026-05-05T210519Z.yaml", "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112"),
    "investment": ("data/manifests/fetch_run_2026-05-05T203305Z.yaml", "53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0"),
}


def source(series: str, stamp: str, digest: str, manifest_key: str) -> dict[str, str]:
    manifest, manifest_sha = MANIFESTS[manifest_key]
    return {"publisher": "world_bank_wdi", "series_id": series,
            "path": f"data/vintages/world_bank_wdi/{series}@{stamp}.parquet",
            "sha256": digest, "manifest": manifest, "manifest_sha256": manifest_sha,
            "url": f"https://api.worldbank.org/v2/country/all/indicator/{series}?format=json"}


SOURCES = {
    "fertility": source("SP.DYN.TFRT.IN", "2026-04-30T130516Z", "ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1", "old"),
    "income": source("NY.GDP.PCAP.KD", "2026-05-05T194645Z", "0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f", "main"),
    "female_lfp": source("SL.TLF.CACT.FE.ZS", "2026-05-05T194807Z", "c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186", "main"),
    "self_employment": source("SL.EMP.SELF.ZS", "2026-04-30T115122Z", "67abd9aef0cc6ba29de9fc1bea7bbbf6686a310a49fc7b38f782211a22dd330c", "bootstrap"),
    "services_employment": source("SL.SRV.EMPL.ZS", "2026-05-05T203741Z", "5cc0fcababebe90b69eae253466a6a81beaf0f52f9c0ef5d59b8a2fa34f400c6", "later"),
    "worker_productivity": source("SL.GDP.PCAP.EM.KD", "2026-04-30T141045Z", "a4b4194f221b89c5f08ed6c11eb691c66ddb572798948af55c0f9d4b5b284742", "productivity"),
    "private_consumption": source("NE.CON.PRVT.PC.KD", "2026-05-05T194704Z", "e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe", "main"),
    "fixed_investment": source("NE.GDI.FTOT.ZS", "2026-05-05T203056Z", "fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21", "investment"),
}

CASES = {
    "female_lfp": {"id": "fertility_decline_female_lfp_decade_forward_2026", "topic": "labour", "label": "female labour-force participation rate", "dimension": "employment_labour", "sign": "+", "minimum": 1.0, "unit": "percentage points", "bounds": (0, 100), "log": False},
    "self_employment": {"id": "fertility_decline_self_employment_decade_forward_2026", "topic": "labour", "label": "self-employment share of total employment", "dimension": "employment_labour", "sign": "-", "minimum": 1.0, "unit": "percentage points", "bounds": (0, 100), "log": False},
    "services_employment": {"id": "fertility_decline_services_employment_decade_forward_2026", "topic": "labour", "label": "services share of employment", "dimension": "employment_labour", "sign": "+", "minimum": 1.0, "unit": "percentage points", "bounds": (0, 100), "log": False},
    "worker_productivity": {"id": "fertility_decline_worker_productivity_decade_forward_2026", "topic": "growth", "label": "real output per employed person", "dimension": "productivity", "sign": "+", "minimum": 0.03, "unit": "ten-year log points", "bounds": (0, float("inf")), "log": True},
    "private_consumption": {"id": "fertility_decline_private_consumption_decade_forward_2026", "topic": "growth", "label": "real private consumption per resident", "dimension": "private_consumption", "sign": "+", "minimum": 0.03, "unit": "ten-year log points", "bounds": (0, float("inf")), "log": True},
    "fixed_investment": {"id": "fertility_decline_fixed_investment_decade_forward_2026", "topic": "growth", "label": "gross fixed capital formation share of GDP", "dimension": "industrial_capability", "sign": "+", "minimum": 0.5, "unit": "percentage points", "bounds": (0, 200), "log": False},
}
MEMBERS = [case["id"] for case in CASES.values()]
CORRECTION = {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
    "family_size": 6, "family_alpha": FAMILY_ALPHA, "bonferroni_p_max": P_MAX,
    "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
    "school_score_eligible": False, "school_score_credit": 0,
    "featured_eligible": False}
LIMITS = [
    "This is one correlated six-margin demographic-transition programme, not six independent confirmations.",
    "Fertility is a modeled period measure, not an intervention; labour outcomes are ILO modeled estimates.",
    "Women entering the labour force need not be employed, and self-employment is not a quality-of-work measure.",
    "Productivity and private consumption are real national aggregates; investment is a GDP share, not capital stock.",
    "Country and anchor effects and earlier income controls do not remove development trends, policy changes, reverse timing, or migration.",
    "Outcome vintages were already in the wider IESET corpus. This is a within-lane value-blind registration, not independent future data or an archive-wide selection correction.",
    "No causal, policy, school, position, or featured credit is assigned.",
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_addition(path: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no committed first addition: {path}")
    return revisions[-1]


def frozen(path: str, revision: str) -> None:
    if (ROOT / path).read_bytes() != git("show", f"{revision}:{path}"):
        raise RuntimeError(f"frozen bytes differ: {path}")
    if git("status", "--porcelain", "--", path).strip():
        raise RuntimeError(f"uncommitted frozen path: {path}")


def spec_path(key: str) -> str:
    return f"hypotheses/{CASES[key]['topic']}/{CASES[key]['id']}.yaml"


def steelman_path(key: str) -> str:
    return f"hypotheses/steelman/{CASES[key]['id']}.md"


def run_dir(key: str) -> str:
    return f"engine/runs/{CASES[key]['id']}"


def raw(role: str, values: bool) -> pd.DataFrame:
    fields = ["country_iso3", "indicator_id", "year"]
    if values:
        fields += ["value", "obs_status"]
    frame = pd.read_parquet(ROOT / SOURCES[role]["path"], columns=fields)
    if len(frame) != 17556 or set(frame.indicator_id.dropna()) != {SOURCES[role]["series_id"]}:
        raise RuntimeError(f"physical source shape or indicator differs: {role}")
    frame = frame.loc[frame.country_iso3.isin(ISO3)].copy()
    if frame.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate country-year key: {role}")
    frame["year"] = frame.year.astype(int)
    return frame


def valid_cell(value: Any, status: Any, lower: float, upper: float) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not (math.isfinite(number) and lower <= number <= upper):
        return None
    if not (pd.isna(status) or str(status).strip() in ("", "A")):
        return None
    return number


def values(role: str, bounds: tuple[float, float]) -> dict[tuple[str, int], float]:
    frame = raw(role, True)
    result = {}
    for c, _, y, v, s in frame.itertuples(index=False, name=None):
        number = valid_cell(v, s, *bounds)
        if number is not None:
            result[(c, int(y))] = number
    return result


def expected_roster() -> tuple[list[tuple[str, int]], dict[str, int]]:
    # Only fertility and income values are opened. Selected outcome projections
    # are restricted to source keys and indicator identity, never null masks.
    fertility = values("fertility", (0.5, 10.0))
    income = values("income", (0.000001, float("inf")))
    outcome_keys = {role: set(zip(frame.country_iso3, frame.year))
                    for role in CASES for frame in [raw(role, False)]}
    rows = []
    changes = {}
    for country in sorted(ISO3):
        for anchor in ANCHORS:
            needed = ((country, anchor - 10), (country, anchor))
            if not all(key in fertility and key in income for key in needed):
                continue
            if not all((country, anchor) in keys and (country, anchor + 10) in keys
                       for keys in outcome_keys.values()):
                continue
            rows.append((country, anchor))
            changes[(country, anchor)] = fertility[needed[0]] - fertility[needed[1]]
    counts = Counter(country for country, _ in rows)
    rows = sorted((country, anchor) for country, anchor in rows if counts[country] == 2)
    material = [(country, anchor) for country, anchor in rows
                if abs(changes[country, anchor]) >= MATERIAL_FERTILITY_DECLINE]
    preflight = {"key_rows": len(rows), "key_countries": len({c for c, _ in rows}),
        "material_treatment_rows": len(material),
        "material_treatment_countries": len({c for c, _ in material}),
        "outcome_values_opened": False, "outcome_null_masks_opened": False}
    if preflight != {"key_rows": ROSTER_ROWS, "key_countries": ROSTER_COUNTRIES,
            "material_treatment_rows": PREFLIGHT_MATERIAL_ROWS,
            "material_treatment_countries": PREFLIGHT_MATERIAL_COUNTRIES,
            "outcome_values_opened": False, "outcome_null_masks_opened": False}:
        raise RuntimeError(f"treatment-only preflight changed: {preflight}")
    return rows, preflight


def roster() -> tuple[list[tuple[str, int]], str]:
    path = ROOT / ROSTER
    lines = path.read_text().splitlines()
    if not lines or lines[0] != "country_iso3,anchor_year":
        raise RuntimeError("invalid key-roster header")
    records = [(row["country_iso3"], int(row["anchor_year"]))
               for row in csv.DictReader(lines)]
    if (records != sorted(set(records)) or len(records) != ROSTER_ROWS
            or len({c for c, _ in records}) != ROSTER_COUNTRIES
            or any(a not in ANCHORS or c not in ISO3 for c, a in records)):
        raise RuntimeError("invalid frozen key roster")
    expected, _ = expected_roster()
    if records != expected:
        raise RuntimeError("key roster differs from treatment/control values and outcome keys")
    return records, sha(path)


def threshold(key: str, roster_sha: str) -> dict[str, Any]:
    case = CASES[key]
    return {"family_id": FAMILY, "family_size": 6, "family_alpha": FAMILY_ALPHA,
        "p_max_two_sided_bonferroni": P_MAX, "expected_beta_sign": case["sign"],
        "meaningful_beta_min_abs": case["minimum"], "meaningful_beta_unit": case["unit"],
        "min_complete_rows": MIN_ROWS, "min_complete_countries": MIN_COUNTRIES,
        "min_material_rows": MIN_MATERIAL_ROWS,
        "min_material_countries": MIN_MATERIAL_COUNTRIES,
        "material_fertility_decline_births_per_woman": MATERIAL_FERTILITY_DECLINE,
        "min_complete_anchors_per_country": 2,
        "max_top_one_percent_partialled_x_share": MAX_TOP_ONE_PERCENT_X_SHARE,
        "max_country_partialled_x_share": MAX_COUNTRY_X_SHARE,
        "max_anchor_partialled_x_share": MAX_ANCHOR_X_SHARE,
        "key_roster_sha256": roster_sha, "source_lock_path": LOCK,
        "source_files": {role: SOURCES[role] for role in ("fertility", "income", key)},
        "causal_credit": 0, "policy_score_eligible": False, "policy_score_credit": 0,
        "school_score_eligible": False, "school_score_credit": 0, "featured_eligible": False}


def spec(key: str, countries: list[str], roster_sha: str) -> dict[str, Any]:
    case = CASES[key]
    sign_word = "increase" if case["sign"] == "+" else "decrease"
    return {
        "hypothesis_id": case["id"], "version": 1, "status": "pre_registered",
        "topic": case["topic"], "claim_direction": case["sign"],
        "claim": (f"In the fixed country/anchor sample, a one-birth-per-woman larger fertility "
                  f"decline in the preceding decade predicts at least a {case['minimum']} "
                  f"{case['unit']} {sign_word} in {case['label']} during the following decade, "
                  "conditional on earlier real income and country/anchor effects."),
        "methodology_note": ("Six-outcome demographic-transition descriptive family. "
            "Source keys, treatment/income preflight, complete-case, influence, and multiplicity "
            f"rules were fixed in {PREREG} before selected outcome values or null masks were opened."),
        "evidence_type": "associational",
        "sample": {"countries": countries, "period": [1985, 2015],
            "temporal_structure": "panel", "exclusion_rules": [
                "Only frozen 1995 and 2005 anchor country keys; require both complete windows per country.",
                "Treat missing, nonfinite, flagged, out-of-range or nonpositive log-input endpoints as absent; no interpolation, winsorization, replacement source, or country substitution.",
                "Only two-window complete countries enter country/anchor fixed-effects fits; no post-outcome threshold changes."]},
        "variables": {"treatment": [{"name": "preceding_decade_fertility_decline",
            "source": "world_bank_wdi:SP.DYN.TFRT.IN",
            "transformation": "Fertility at t-10 minus fertility at t, births per woman; positive means declining fertility.",
            "notes": "Observed national demographic transition, not a policy intervention."}],
            "outcome": [{"name": key, "source": f"world_bank_wdi:{SOURCES[key]['series_id']}",
                "transformation": (f"{case['label']} at t+10 minus t; " +
                    ("natural-log ratio." if case["log"] else "percentage-point difference.")),
                "notes": "Distinct aggregate response margin; no individual-level effect is identified."}],
            "controls": [{"name": "baseline_log_real_income_per_person",
                "source": "world_bank_wdi:NY.GDP.PCAP.KD",
                "transformation": "Natural log real GDP per resident at t."},
                {"name": "preceding_decade_log_income_growth",
                "source": "world_bank_wdi:NY.GDP.PCAP.KD",
                "transformation": "Natural log real GDP per resident at t divided by t-10."}]},
        "estimator": {"template": "panel_fe", "fixed_effects": ["country", "anchor_year"],
            "clustering": "country",
            "notes": "OLS of next-decade outcome change on prior-decade fertility decline, baseline log income, prior log income growth, country and anchor effects. Country-cluster CR1 small-sample correction; two-sided Student t(G-1)."},
        "falsification": {"test": FAMILY,
            "rule": (f"INCONCLUSIVE if a frozen source, chronology, complete-case, material-exposure, "
                f"rank, influence, or finite-uncertainty gate fails. Otherwise SUPPORTED for a "
                f"{case['sign']} oriented beta of at least {case['minimum']} {case['unit']} "
                f"and two-sided p<={P_MAX}; REFUTED for equally large opposite beta at the same p; "
                "all other estimable results PARTIAL. Six tests share one family denominator."),
            "threshold": threshold(key, roster_sha)},
        "prior_confidence": 0.25,
        "disclosure": "This is a correlated descriptive follow-through; migration, development, labour modelling, and reverse timing remain. The family was selected from a previously explored corpus and is not an independent holdout. Zero causal, policy, school, position, and featured credit.",
        "steelman": steelman_path(key),
        "scope": {"period": [1985, 2015], "countries": countries,
            "outcome_dim": [case["dimension"]], "policy_family": ["none"],
            "treatment_tags": []}, "covers_claims": [],
        "linked_hypotheses": [], "linked_conditions": []}


def prereg_text(roster_sha: str) -> str:
    rows = ["# Demographic transition and later economic margins: frozen registration", "",
        "Registration opens only fertility and income treatment/control values plus country-year-indicator keys from outcomes. It does not open outcome values, null masks, or observation statuses. Selected vintages existed in the broader IESET corpus and previous related hypotheses are known; this is a within-lane prospective measurement protocol, not an independent future-data holdout.", "",
        f"One six-test family `{FAMILY}`; roster `{ROSTER}` SHA-256 `{roster_sha}`.",
        "Treatment anchors are 1995 and 2005. The preceding ten-year fertility decline is fertility(t-10) minus fertility(t), births per woman. Outcome is change or log ratio t to t+10. Real GDP per person at t and preceding ten-year growth are controls. Countries must have both complete anchor windows after outcome access.", "",
        f"Treatment/control and outcome-key preflight: {ROSTER_ROWS} pairs in {ROSTER_COUNTRIES} ISO countries; {PREFLIGHT_MATERIAL_ROWS} pairs/{PREFLIGHT_MATERIAL_COUNTRIES} countries have |fertility decline|≥{MATERIAL_FERTILITY_DECLINE}. All six selected outcomes have physical key rows for this roster; this does not assert nonmissing values.", "",
        "The six distinct margins are female labour-force participation, self-employment share, services-employment share, real output per worker, real private consumption per resident, and fixed-capital-formation share. Labour series can share ILO model inputs. The six packets are one correlated demographic-transition programme and cannot be called six independent replications.", "",
        f"Every case requires ≥{MIN_ROWS} complete two-window rows, ≥{MIN_COUNTRIES} countries, ≥{MIN_MATERIAL_ROWS} material rows in ≥{MIN_MATERIAL_COUNTRIES} countries, full-rank treatment residualization and primary model, finite positive country-cluster uncertainty, residualized exposure shares ≤{MAX_TOP_ONE_PERCENT_X_SHARE} for the top 1% of rows, ≤{MAX_COUNTRY_X_SHARE} for one country, and ≤{MAX_ANCHOR_X_SHARE} for one anchor year. No value clipping or gate relaxation.", "",
        f"Country and anchor fixed-effects OLS includes baseline log income and prior-decade log income growth. Use CR1 country clustering and two-sided Student t(G-1). Family alpha=0.01; six-test Bonferroni p≤{P_MAX}. A directional verdict additionally needs the margin-specific practical size fixed in each YAML. Opposite sign of equal size is REFUTED; other estimable results PARTIAL; failed gates INCONCLUSIVE.", "",
        "The design is descriptive and ecological. National fertility is not a treatment assignment. Country/anchor effects and prior income do not resolve migration, structural change, social norms, policy, or reverse timing. Labour values are modelled. No causal, policy, school-score, position, or featured credit. The p adjustment covers this declared family only, not the wider IESET search.", "",
        "## Exact source identities", "",
        "| Role | WDI indicator | SHA-256 | Tracked fetch manifest |", "| --- | --- | --- | --- |"]
    for role, src in SOURCES.items():
        rows.append(f"| {role} | {src['series_id']} | `{src['sha256']}` | `{src['manifest']}` |")
    rows.extend(["", "Source-lock manifest must be separately committed after this registration and before selected outcome values are read. A separate measured-result commit follows.", ""])
    return "\n".join(rows)


def prepare() -> None:
    for path in [PREREG, ROSTER] + [p for key in CASES for p in (spec_path(key), steelman_path(key))]:
        if (ROOT / path).exists():
            raise FileExistsError(path)
    rows, _ = expected_roster()
    path = ROOT / ROSTER
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("country_iso3,anchor_year\n" + "".join(f"{c},{a}\n" for c, a in rows))
    digest = sha(path)
    countries = sorted({c for c, _ in rows})
    for key, case in CASES.items():
        spec_file = ROOT / spec_path(key)
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        spec_file.write_text("# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n" +
            yaml.safe_dump(spec(key, countries, digest), sort_keys=False, allow_unicode=True, width=100))
        steel_file = ROOT / steelman_path(key)
        steel_file.parent.mkdir(parents=True, exist_ok=True)
        steel_file.write_text(f"# Steelman: {case['id']}\n\nA fertility decline can accompany economic modernization without causing {case['label']} to change. Mortality, urbanization, education, migration, state capacity, and labour demand can move fertility and this outcome together. The selected WDI labour series are national ILO-modelled aggregates where relevant. Two anchor windows and country effects do not settle these alternatives. A weak, opposite, or gate-failing result must remain visible.\n")
    (ROOT / PREREG).write_text(prereg_text(digest))
    print(f"prepared six fixed specifications and {len(rows)} value-blind keys; roster sha256={digest}")


def registration_commit() -> tuple[str, str]:
    paths = [RUNNER, PREREG, ROSTER]
    for key in CASES:
        paths += [spec_path(key), steelman_path(key)]
    revisions = {first_addition(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("registration files lack one first-addition commit")
    revision = revisions.pop()
    for path in paths:
        frozen(path, revision)
    if git("ls-tree", "-r", "--name-only", revision, "--", LOCK).strip():
        raise RuntimeError("source lock existed in registration commit")
    rows, roster_sha = roster()
    countries = sorted({c for c, _ in rows})
    if (ROOT / PREREG).read_text() != prereg_text(roster_sha):
        raise RuntimeError("registration text differs from runner")
    for key in CASES:
        observed = yaml.safe_load((ROOT / spec_path(key)).read_text())
        if observed != spec(key, countries, roster_sha):
            raise RuntimeError(f"frozen spec differs from runner contract: {key}")
        if git("ls-tree", "-r", "--name-only", revision, "--", run_dir(key)).strip():
            raise RuntimeError(f"measured result existed in registration commit: {key}")
    return revision, roster_sha


def check_sources() -> dict[str, Any]:
    out = {}
    for role, src in SOURCES.items():
        file = ROOT / src["path"]
        manifest = ROOT / src["manifest"]
        if not file.is_file() or sha(file) != src["sha256"]:
            raise RuntimeError(f"raw source missing or mismatched: {role}")
        if not manifest.is_file() or sha(manifest) != src["manifest_sha256"]:
            raise RuntimeError(f"fetch manifest missing or mismatched: {role}")
        entries = yaml.safe_load(manifest.read_text()).get("entries", [])
        matches = [e for e in entries if e.get("publisher") == src["publisher"]
                   and e.get("series_id") == src["series_id"]
                   and e.get("parquet_path") == src["path"]
                   and e.get("sha256") == src["sha256"]]
        if len(matches) != 1:
            raise RuntimeError(f"fetch manifest has no unique pinned entry: {role}")
        out[role] = {**src, "license": matches[0].get("license"),
                     "fetch_utc": matches[0].get("fetch_utc")}
    return out


def lock_payload(revision: str, roster_sha: str, sources: dict[str, Any]) -> dict[str, Any]:
    return {"family_id": FAMILY, "registration_commit": revision,
        "key_roster_path": ROSTER, "key_roster_sha256": roster_sha,
        "sources": sources, "members": MEMBERS,
        "statement": "Selected outcome values, statuses, and null masks unopened in this registration lane before the separate lock commit."}


def write_lock() -> None:
    revision, roster_sha = registration_commit()
    sources = check_sources()
    path = ROOT / LOCK
    if path.exists():
        raise FileExistsError(LOCK)
    path.write_text(json.dumps(lock_payload(revision, roster_sha, sources), indent=2, sort_keys=True) + "\n")
    print(f"wrote {LOCK}; commit separately before --run")


def check_lock(revision: str, roster_sha: str, sources: dict[str, Any]) -> str:
    lock_commit = first_addition(LOCK)
    if lock_commit == revision or subprocess.run(["git", "merge-base", "--is-ancestor", revision, lock_commit], cwd=ROOT).returncode:
        raise RuntimeError("source lock must follow registration")
    frozen(LOCK, lock_commit)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(revision, roster_sha, sources):
        raise RuntimeError("committed source lock differs from source pins")
    for key in CASES:
        if git("ls-tree", "-r", "--name-only", lock_commit, "--", run_dir(key)).strip():
            raise RuntimeError("measured result existed at source lock")
    return lock_commit


def measured_case(key: str, roster_rows: list[tuple[str, int]], fertility: dict,
                  income: dict) -> tuple[pd.DataFrame, dict[str, Any]]:
    # First selected outcome value/status/null access occurs only after check_lock.
    case = CASES[key]
    outcome = values(key, case["bounds"])
    records = []
    dropped = Counter()
    for country, anchor in roster_rows:
        before, at = fertility[(country, anchor - 10)], fertility[(country, anchor)]
        y0 = outcome.get((country, anchor))
        y1 = outcome.get((country, anchor + 10))
        if y0 is None or y1 is None or (case["log"] and (y0 <= 0 or y1 <= 0)):
            dropped["missing_or_invalid_outcome_endpoint"] += 1
            continue
        g0, g1 = income[(country, anchor - 10)], income[(country, anchor)]
        records.append({"country": country, "anchor_year": anchor,
            "x": before - at, "baseline_log_income": math.log(g1),
            "prior_log_income_growth": math.log(g1 / g0),
            "y": math.log(y1 / y0) if case["log"] else y1 - y0})
    counts = Counter(row["country"] for row in records)
    kept = [row for row in records if counts[row["country"]] == 2]
    panel = pd.DataFrame(kept, columns=["country", "anchor_year", "x",
        "baseline_log_income", "prior_log_income_growth", "y"])
    panel = panel.sort_values(["anchor_year", "country"]).reset_index(drop=True)
    material = panel.x.abs().ge(MATERIAL_FERTILITY_DECLINE)
    gate = {"key_rows": len(roster_rows), "complete_before_two_window_floor": len(records),
        "valid_rows": len(panel), "valid_countries": int(panel.country.nunique()),
        "material_rows": int(material.sum()),
        "material_countries": int(panel.loc[material, "country"].nunique()),
        "dropped": dict(dropped), "outcome_values_read_after_lock": True}
    return panel, gate


def estimate(key: str, panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if gate["valid_rows"] < MIN_ROWS or gate["valid_countries"] < MIN_COUNTRIES:
        failures.append("complete-case rows/countries below frozen floor")
    if gate["material_rows"] < MIN_MATERIAL_ROWS or gate["material_countries"] < MIN_MATERIAL_COUNTRIES:
        failures.append("material fertility-change rows/countries below frozen floor")
    if failures:
        return {"verdict": "INCONCLUSIVE", "reason": "; ".join(failures),
                "gate": gate, "primary": None}
    rhs = "x + baseline_log_income + prior_log_income_growth + C(country) + C(anchor_year)"
    residual_model = smf.ols("x ~ baseline_log_income + prior_log_income_growth + C(country) + C(anchor_year)", data=panel)
    if np.linalg.matrix_rank(residual_model.exog) != residual_model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "treatment residualization lacks full rank", "gate": gate, "primary": None}
    residual_sq = np.square(np.asarray(residual_model.fit().resid, dtype=float))
    total = float(residual_sq.sum())
    if not math.isfinite(total) or total <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "no finite residual fertility variation", "gate": gate, "primary": None}
    shares = panel.assign(residual_sq=residual_sq)
    n_top = max(1, math.ceil(.01 * len(panel)))
    gate.update({
        "top_one_percent_partialled_x_share": float(sum(sorted(residual_sq, reverse=True)[:n_top]) / total),
        "top_country_partialled_x_share": float(shares.groupby("country").residual_sq.sum().max() / total),
        "top_anchor_partialled_x_share": float(shares.groupby("anchor_year").residual_sq.sum().max() / total),
    })
    if (gate["top_one_percent_partialled_x_share"] > MAX_TOP_ONE_PERCENT_X_SHARE
            or gate["top_country_partialled_x_share"] > MAX_COUNTRY_X_SHARE
            or gate["top_anchor_partialled_x_share"] > MAX_ANCHOR_X_SHARE):
        return {"verdict": "INCONCLUSIVE", "reason": "frozen residual-fertility concentration gate failed", "gate": gate, "primary": None}
    model = smf.ols(f"y ~ {rhs}", data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {"verdict": "INCONCLUSIVE", "reason": "primary model lacks full rank", "gate": gate, "primary": None}
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": panel.country,
        "use_correction": True, "df_correction": True}, use_t=True)
    beta, se = float(fit.params["x"]), float(fit.bse["x"])
    countries = int(panel.country.nunique())
    if not math.isfinite(beta) or not math.isfinite(se) or se <= 0:
        return {"verdict": "INCONCLUSIVE", "reason": "country-cluster uncertainty is invalid", "gate": gate, "primary": None}
    p = float(2 * student_t.sf(abs(beta / se), countries - 1))
    critical = float(student_t.ppf(1 - P_MAX / 2, countries - 1))
    if not math.isfinite(p) or not math.isfinite(critical):
        return {"verdict": "INCONCLUSIVE", "reason": "Student t inference is invalid", "gate": gate, "primary": None}
    primary = {"coefficient": beta, "std_error": se, "p_value_two_sided": p,
        "confidence_level_family": 1 - P_MAX,
        "confidence_interval_family": [beta - critical * se, beta + critical * se],
        "n_rows": len(panel), "n_countries": countries, "df_inference": countries - 1,
        "method": "country/anchor FE OLS; baseline log income and prior log income growth; country-cluster CR1; Student t(G-1)"}
    oriented = beta if CASES[key]["sign"] == "+" else -beta
    minimum = CASES[key]["minimum"]
    if p <= P_MAX and oriented >= minimum:
        verdict, reason = "SUPPORTED", "descriptive direction and practical size clear frozen family gates"
    elif p <= P_MAX and oriented <= -minimum:
        verdict, reason = "REFUTED", "opposite descriptive direction and practical size clear frozen family gates"
    else:
        verdict, reason = "PARTIAL", "estimable association does not clear both frozen directional gates"
    return {"verdict": verdict, "reason": reason, "gate": gate, "primary": primary}


def artifact(key: str, result: dict[str, Any], reg: str, lock: str, stamp: str,
             roster_sha: str, sources: dict[str, Any]) -> dict[str, Any]:
    case = CASES[key]
    hid = case["id"]
    verdict, gate, primary = result["verdict"], result["gate"], result["primary"]
    diagnostics = {"hypothesis_id": hid, "family_id": FAMILY, "family_size": 6,
        "verdict": verdict, "verdict_label": verdict, "verdict_reason": result["reason"],
        "run_utc": stamp, "runner": RUNNER, "registration_commit": reg,
        "source_lock_commit": lock, "source_lock": LOCK, "key_roster_sha256": roster_sha,
        "template": "panel_fe", "method": "country/anchor fixed-effects OLS with country-cluster CR1",
        "preflight": gate, "primary": primary,
        "data_status": {"variables_missing": [], "input_vintages": list(sources.values())},
        "limitations": LIMITS, "correction": CORRECTION}
    manifest = {"hypothesis_id": hid, "run_utc": stamp, "runner": RUNNER,
        "preregistration_commit": reg, "source_lock_commit": lock, "source_lock": LOCK,
        "status": verdict, "vintages": list(sources.values()),
        "derived_panel": gate, "correction": CORRECTION}
    packet = {"packet_version": 1, "generated_utc": stamp,
        "hypothesis": {"id": hid, "path": spec_path(key), "topic": case["topic"]},
        "family": {"id": FAMILY, "size": 6, "members": MEMBERS,
                   "alpha": FAMILY_ALPHA, "bonferroni_p_max": P_MAX},
        "preregistration": {"spec_commit": reg, "source_lock_commit": lock,
            "key_roster": ROSTER, "key_roster_sha256": roster_sha,
            "steelman": steelman_path(key)},
        "reproduction": {"runner": RUNNER, "run_dir": run_dir(key),
                         "command": f"python3 {RUNNER} --verify"},
        "verdict": {"raw": verdict, "bucket": verdict.lower(), "reason": result["reason"]},
        "data": {"inputs": sources, "sample": gate},
        "results": {"primary": primary}, "limitations": LIMITS,
        "correction": CORRECTION}
    card = (f"# Result card: {hid}\n\nVerdict: **{verdict}**. {result['reason']}.\n\n"
            f"Registration `{reg}`; source lock `{lock}`.\n\n"
            f"Earlier fertility decline and later {case['label']}. Complete pairs: "
            f"{gate['valid_rows']} / {gate['valid_countries']} countries; "
            f"material fertility changes: {gate['material_rows']} / "
            f"{gate['material_countries']} countries.\n")
    if primary:
        card += (f"\nBeta={primary['coefficient']:+.7g} {case['unit']} per one-birth-per-woman "
                 f"fertility decline; country-cluster SE={primary['std_error']:.7g}; "
                 f"two-sided p={primary['p_value_two_sided']:.7g}; "
                 f"{primary['confidence_level_family']:.4%} family interval="
                 f"{primary['confidence_interval_family']}.\n")
    card += ("\nSix correlated margins share p≤0.01/6. This national association "
             "is no fertility-policy, labour-policy, or causal effect. Zero school, "
             "policy, position, and featured credit.\n")
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
               "root = Path(__file__).resolve().parents[3]\n"
               f"raise SystemExit(subprocess.call([sys.executable, str(root / {RUNNER!r}), '--verify'], cwd=root))\n")
    chart = {"hypothesis_id": hid, "family_id": FAMILY, "verdict": verdict,
             "primary": primary}
    coefficients = [{"term": "prior_decade_fertility_decline", **primary}] if primary else []
    return {"diagnostics": diagnostics, "manifest": manifest, "packet": packet,
            "card": card, "wrapper": wrapper, "chart": chart,
            "coefficients": coefficients}


def summary(results: dict[str, dict[str, Any]], reg: str, lock: str) -> str:
    lines = ["# Demographic transition and later economic margins: frozen result", "",
        f"Registration `{reg}`; separate source lock `{lock}`.", "",
        "| Outcome | Verdict | Complete rows / countries | Material rows / countries | Beta | Two-sided p |",
        "| --- | --- | ---: | ---: | ---: | ---: |"]
    for key, case in CASES.items():
        result = results[key]
        gate, primary = result["gate"], result["primary"]
        beta = f"{primary['coefficient']:+.7g}" if primary else "not estimated"
        p = f"{primary['p_value_two_sided']:.7g}" if primary else "not estimated"
        lines.append(f"| {case['label']} | **{result['verdict']}** | {gate['valid_rows']} / {gate['valid_countries']} | {gate['material_rows']} / {gate['material_countries']} | {beta} | {p} |")
    lines.extend(["", "One correlated six-margin programme; descriptive country/anchor fixed-effects estimates only. Direction requires the margin-specific practical size and family p≤0.01/6. Selected outcomes were not a future-data holdout. No causal, policy, school, position, or featured credit.", ""])
    return "\n".join(lines)


def measure(reg: str, lock: str, roster_sha: str, sources: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows, _ = roster()
    fertility = values("fertility", (0.5, 10.0))
    income = values("income", (0.000001, float("inf")))
    results = {}
    for key in CASES:
        panel, gate = measured_case(key, rows, fertility, income)
        results[key] = estimate(key, panel, gate)
    return results


def write_results(results: dict[str, dict[str, Any]], reg: str, lock: str,
                  roster_sha: str, sources: dict[str, Any]) -> None:
    if (ROOT / SUMMARY).exists() or any((ROOT / run_dir(key)).exists() for key in CASES):
        raise FileExistsError("measured artifacts already exist")
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    for key in CASES:
        folder = ROOT / run_dir(key)
        folder.mkdir(parents=True)
        data = artifact(key, results[key], reg, lock, stamp, roster_sha, sources)
        (folder / "hypothesis.yaml").write_bytes((ROOT / spec_path(key)).read_bytes())
        (folder / "diagnostics.json").write_text(json.dumps(data["diagnostics"], indent=2) + "\n")
        (folder / "manifest.yaml").write_text(yaml.safe_dump(data["manifest"], sort_keys=False))
        (folder / "evidence_packet.yaml").write_text(yaml.safe_dump(data["packet"], sort_keys=False))
        (folder / "result_card.md").write_text(data["card"])
        (folder / "replication.py").write_text(data["wrapper"])
        (folder / "chart_data.json").write_text(json.dumps(data["chart"], indent=2) + "\n")
        pd.DataFrame(data["coefficients"], columns=["term", "coefficient", "std_error",
            "p_value_two_sided", "confidence_level_family", "confidence_interval_family",
            "n_rows", "n_countries", "df_inference", "method"]).to_parquet(
                folder / "coefficients.parquet", index=False)
    (ROOT / SUMMARY).write_text(summary(results, reg, lock))


def compare(actual: Any, expected: Any, label: str) -> None:
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise AssertionError(f"{label}: field mismatch")
        for key, value in expected.items():
            compare(actual[key], value, f"{label}.{key}")
    elif isinstance(expected, list):
        if not isinstance(actual, (list, np.ndarray)) or len(actual) != len(expected):
            raise AssertionError(f"{label}: list mismatch")
        for index, value in enumerate(expected):
            compare(actual[index], value, f"{label}[{index}]")
    elif isinstance(expected, float):
        if not math.isclose(float(actual), expected, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f"{label}: numeric mismatch")
    elif actual != expected:
        raise AssertionError(f"{label}: value mismatch")


def verify_results(results: dict[str, dict[str, Any]], reg: str, lock: str,
                   roster_sha: str, sources: dict[str, Any]) -> None:
    for key in CASES:
        folder = ROOT / run_dir(key)
        saved_diag = json.loads((folder / "diagnostics.json").read_text())
        data = artifact(key, results[key], reg, lock, saved_diag["run_utc"], roster_sha, sources)
        compare(saved_diag, data["diagnostics"], f"{key}.diagnostics")
        compare(yaml.safe_load((folder / "manifest.yaml").read_text()), data["manifest"], f"{key}.manifest")
        compare(yaml.safe_load((folder / "evidence_packet.yaml").read_text()), data["packet"], f"{key}.packet")
        compare(json.loads((folder / "chart_data.json").read_text()), data["chart"], f"{key}.chart")
        compare(pd.read_parquet(folder / "coefficients.parquet").to_dict(orient="records"), data["coefficients"], f"{key}.coefficients")
        if ((folder / "hypothesis.yaml").read_bytes() != (ROOT / spec_path(key)).read_bytes()
                or (folder / "result_card.md").read_text() != data["card"]
                or (folder / "replication.py").read_text() != data["wrapper"]):
            raise AssertionError(f"{key}: text artifacts differ")
    if (ROOT / SUMMARY).read_text() != summary(results, reg, lock):
        raise AssertionError("family summary differs from exact replay")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ("prepare", "preflight", "write-source-lock", "run", "verify"):
        action.add_argument(f"--{name}", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        check_sources()
        prepare()
        return
    if args.preflight:
        rows, blind = expected_roster()
        print(json.dumps({**blind, "rows": len(rows)}, indent=2))
        return
    reg, roster_sha = registration_commit()
    sources = check_sources()
    if args.write_source_lock:
        write_lock()
        return
    lock = check_lock(reg, roster_sha, sources)
    results = measure(reg, lock, roster_sha, sources)
    if args.run:
        write_results(results, reg, lock, roster_sha, sources)
        print(summary(results, reg, lock))
        return
    verify_results(results, reg, lock, roster_sha, sources)
    print("six demographic-transition result packets exactly replayed")


if __name__ == "__main__":
    main()
