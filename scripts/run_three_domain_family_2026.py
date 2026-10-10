#!/usr/bin/env python3
"""Frozen, three-question descriptive calibration with source custody and replay."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pycountry
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNNER = "scripts/run_three_domain_family_2026.py"
FAMILY = "three_domain_forward_calibration_2026"
PREREG = "engine/audits/three_domain_family_prereg_2026-10-10.md"
SUMMARY = "engine/audits/three_domain_family_results_2026-10-10.md"
ROSTER = "data/pinned_evidence/three_domain_family_key_roster.csv"
ROSTER_SHA = "8e1b06016aec18f323571785edbe91c228f931744c234e6822a6e2f52cbf62cc"
LOCK = "data/pinned_evidence/three_domain_family_2026.manifest.json"
ALPHA = 0.01
FAMILY_SIZE = 3
P_MAX = ALPHA / FAMILY_SIZE
MIN_HOLDOUT_SIGNS = 4
CREDIT = {
    "causal_credit": 0, "policy_score_eligible": False,
    "policy_score_credit": 0, "school_score_eligible": False,
    "school_score_credit": 0, "featured_eligible": False,
}

MANIFESTS = {
    "data/manifests/fetch_run_2026-05-05T200056Z.yaml": "a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945",
    "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml": "e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e",
    "data/manifests/fetch_run_2026-05-05T210519Z.yaml": "5022cf82e5656d89c54d3c0df1cc3c12718b93896488eebfde3ffa197beef112",
    "data/manifests/fetch_run_2026-04-30T141104Z.yaml": "588d991d5f5a2224fe59f6490d06169d80b898dfbefa1d02a43a45e339a355d6",
}
SOURCES = {
    "law": {"publisher": "wgi", "series_id": "GOV_WGI_RL.EST", "manifest": "data/manifests/fetch_run_2026-05-05T200056Z.yaml", "path": "data/vintages/wgi/GOV_WGI_RL.EST@2026-05-05T195218Z.parquet", "sha256": "63d71d06668ef8e8cff186d11bb9ca948e8ae82b857bf31e1cbb122ae847c91d", "rows": 5616},
    "homicide": {"publisher": "owid", "series_id": "intentional-homicides-per-100000-people", "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml", "path": "data/vintages/owid/intentional-homicides-per-100000-people@2026-04-30T114856Z.parquet", "sha256": "518ca94eb6aa1da5ae0900d984e6dc7f567ebbc21486666b2e37a1843d704694", "rows": 4885},
    "tractor": {"publisher": "faostat", "series_id": "Investment_Machinery", "manifest": None, "path": "data/vintages/faostat/faostat_machinery_main@2026-05-02T212848Z.parquet", "sha256": "81aac0eff6e8aee780fd667637333872a2cff088d61d23ef2d0db0e4e20219c6", "rows": 146834},
    "tractor_archive": {"publisher": "faostat", "series_id": "Investment_Machinery_raw_archive", "manifest": None, "path": "data/vintages/faostat/machinery@2026-05-02T212848Z.zip", "sha256": "3bf291ea8996f3b664bf176cd2926ec3a53b50b94ac75c5d6bcf74f6d2ddb009", "rows": None},
    "food": {"publisher": "world_bank_wdi", "series_id": "AG.PRD.FOOD.XD", "manifest": "data/manifests/fetch_run_2026-05-05T210519Z.yaml", "path": "data/vintages/world_bank_wdi/AG.PRD.FOOD.XD@2026-05-05T203847Z.parquet", "sha256": "05863480f2da10e8d59cb591a008fb54ad23e7b35d1818d1682fd7a673536876", "rows": 17556},
    "self_employment": {"publisher": "world_bank_wdi", "series_id": "SL.EMP.SELF.ZS", "manifest": "data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml", "path": "data/vintages/world_bank_wdi/SL.EMP.SELF.ZS@2026-04-30T115122Z.parquet", "sha256": "67abd9aef0cc6ba29de9fc1bea7bbbf6686a310a49fc7b38f782211a22dd330c", "rows": 17556},
    "productivity": {"publisher": "world_bank_wdi", "series_id": "SL.GDP.PCAP.EM.KD", "manifest": "data/manifests/fetch_run_2026-04-30T141104Z.yaml", "path": "data/vintages/world_bank_wdi/SL.GDP.PCAP.EM.KD@2026-04-30T141045Z.parquet", "sha256": "a4b4194f221b89c5f08ed6c11eb691c66ddb572798948af55c0f9d4b5b284742", "rows": 17556},
}
STUDIES = {
    "law_homicide": {
        "id": "wgi_rule_of_law_homicide_forward_2026", "topic": "institutional_quality",
        "title": "Rule of law and later homicide", "xrole": "law", "yrole": "homicide",
        "xyears": [2000, 2010], "yyears": [2010, 2020], "nkeys": 119,
        "min_complete": 90, "material": 0.15, "min_material": 20, "spread": 0.30,
        "top_one": 0.15, "top_k": 10, "top_k_max": 0.60, "holdout": 70,
        "beta": 0.20, "xunit": "per +1 WGI rule-of-law point", "yunit": "log homicide-rate reduction",
        "claim": "Larger 2000-to-2010 rule-of-law gains predict greater 2010-to-2020 homicide-rate reductions across the frozen country roster.",
        "caveat": "WGI rule of law is a perception-based composite that may itself incorporate crime and enforcement. Homicide reporting and social conditions also vary.",
    },
    "tractor_food": {
        "id": "faostat_tractor_stock_food_production_forward_2026", "topic": "growth",
        "title": "Tractor stock and later food production", "xrole": "tractor", "yrole": "food",
        "xyears": [1990, 2000], "yyears": [2000, 2010], "nkeys": 100,
        "min_complete": 70, "material": 0.10, "min_material": 15, "spread": 0.25,
        "top_one": 0.20, "top_k": 5, "top_k_max": 0.65, "holdout": 55,
        "beta": 0.05, "xunit": "per +1 log(1+tractors) point", "yunit": "log food-production-index growth",
        "claim": "Larger 1990-to-2000 increases in agricultural tractors in use predict greater 2000-to-2010 growth in the food-production index across the frozen country roster.",
        "caveat": "Tractor stock is unscaled by cultivated area and may reflect country size, farm consolidation, or record changes. Rainfall, input use, land and trade can move food output.",
    },
    "self_employment_productivity": {
        "id": "wdi_self_employment_productivity_forward_2026", "topic": "labour",
        "title": "Self-employment share and later worker productivity", "xrole": "self_employment", "yrole": "productivity",
        "xyears": [2000, 2010], "yyears": [2010, 2020], "nkeys": 215,
        "min_complete": 150, "material": 3.0, "min_material": 35, "spread": 8.0,
        "top_one": 0.12, "top_k": 10, "top_k_max": 0.50, "holdout": 120,
        "beta": 0.005, "xunit": "per 1 percentage-point self-employment decline", "yunit": "log GDP-per-worker growth",
        "claim": "Larger 2000-to-2010 declines in the self-employment share predict greater 2010-to-2020 growth in GDP per person employed across the frozen country roster.",
        "caveat": "The modeled self-employment share includes employers and own-account work and does not measure formal employment. Sector mix, capital deepening and GDP accounting can drive both series.",
    },
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def first_added(path: str) -> str:
    revisions = git("log", "--diff-filter=A", "--format=%H", "HEAD", "--", path).decode().splitlines()
    if not revisions:
        raise RuntimeError(f"no first-addition commit: {path}")
    return revisions[-1]


def strict_ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ["git", "merge-base", "--is-ancestor", older, newer], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def frozen(path: str, revision: str) -> None:
    file = ROOT / path
    if (not file.is_file() or file.read_bytes() != git("show", f"{revision}:{path}")
            or git("status", "--porcelain", "--", path).strip()):
        raise RuntimeError(f"frozen-byte mismatch: {path}")


def spec_path(study: str) -> str:
    s = STUDIES[study]
    return f"hypotheses/{s['topic']}/{s['id']}.yaml"


def steelman_path(study: str) -> str:
    return f"hypotheses/steelman/{STUDIES[study]['id']}.md"


def run_dir(study: str) -> str:
    return f"engine/runs/{STUDIES[study]['id']}"


def roster() -> dict[str, list[str]]:
    if sha(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError("frozen roster hash mismatch")
    rows = list(csv.DictReader((ROOT / ROSTER).open(newline="")))
    result = {k: [r["country_iso3"] for r in rows if r["study_id"] == k] for k in STUDIES}
    if len(rows) != sum(s["nkeys"] for s in STUDIES.values()):
        raise RuntimeError("frozen roster row count mismatch")
    for k, countries in result.items():
        if (len(countries) != STUDIES[k]["nkeys"] or countries != sorted(set(countries))
                or any(pycountry.countries.get(alpha_3=c) is None for c in countries)):
            raise RuntimeError(f"frozen roster shape mismatch: {k}")
    return result


def threshold(study: str) -> dict:
    s = STUDIES[study]
    return {
        "family_id": FAMILY, "family_size": FAMILY_SIZE, "family_alpha": ALPHA,
        "bonferroni_p_max_two_sided": P_MAX,
        "meaningful_beta_min_abs": s["beta"],
        "min_complete_countries": s["min_complete"],
        "min_material_exposure_gain_countries": s["min_material"],
        "material_exposure_gain": s["material"],
        "min_exposure_p90_p10_spread": s["spread"],
        "max_top_country_residualized_exposure_share": s["top_one"],
        f"max_top_{s['top_k']}_residualized_exposure_share": s["top_k_max"],
        "min_leave_one_hash_fold_out_countries": s["holdout"],
        "min_concordant_holdouts_for_directional_verdict": MIN_HOLDOUT_SIGNS,
        "roster_sha256": ROSTER_SHA, "source_lock_path": LOCK, **CREDIT,
    }


def make_spec(study: str, countries: list[str]) -> dict:
    s = STUDIES[study]
    return {
        "hypothesis_id": s["id"], "version": 1, "status": "pre_registered",
        "topic": s["topic"], "claim_direction": "+", "claim": s["claim"],
        "evidence_type": "descriptive",
        "methodology_note": "One of a closed three-test descriptive family, fixed before selected values. Family alpha 0.01 with Bonferroni denominator three; source-key rows do not establish non-null values.",
        "sample": {
            "countries": countries, "period": [min(s["xyears"]), max(s["yyears"])],
            "temporal_structure": "cross_section_with_justification",
            "cross_section_justification": "One fixed prior exposure change and one subsequent outcome change per country.",
            "exclusion_rules": [
                f"Only the frozen {s['nkeys']}-country source-key intersection; complete values, admissible statuses and ranges required.",
                "No aggregate geography, duplicate key, alternate endpoint, interpolation, imputation, post-result covariate or country replacement.",
            ],
        },
        "scope": {
            "period": [min(s["xyears"]), max(s["yyears"])], "countries": countries,
            "outcome_dim": [{"law_homicide": "life_expectancy_health", "tractor_food": "gdp_growth", "self_employment_productivity": "productivity"}[study]],
            "policy_family": ["none"], "treatment_tags": [],
        },
        "variables": {
            "treatment": [{"name": "prior_exposure_gain", "source": f"{SOURCES[s['xrole']]['publisher']}:{SOURCES[s['xrole']]['series_id']}", "transformation": exposure_description(study)}],
            "outcome": [{"name": "later_outcome_improvement", "source": f"{SOURCES[s['yrole']]['publisher']}:{SOURCES[s['yrole']]['series_id']}", "transformation": outcome_description(study)}],
            "controls": [
                {"name": "baseline_exposure", "source": f"{SOURCES[s['xrole']]['publisher']}:{SOURCES[s['xrole']]['series_id']}", "transformation": "fixed first exposure endpoint"},
                {"name": "baseline_outcome", "source": f"{SOURCES[s['yrole']]['publisher']}:{SOURCES[s['yrole']]['series_id']}", "transformation": "fixed first outcome endpoint, logged where positive"},
            ],
        },
        "estimator": {"template": "descriptive", "notes": "Equal-country OLS with intercept, prior exposure change, baseline exposure and baseline outcome; HC3 two-sided Student t. Five fixed SHA256(ISO3) hash-fold omissions. No post-result controls."},
        "falsification": {
            "test": f"fixed_{s['id']}",
            "rule": "Any failed frozen complete-case, material-gain, variation, rank, positive finite HC3 uncertainty, residualized-exposure concentration or holdout gate means INCONCLUSIVE. Otherwise SUPPORTED requires positive meaningful slope, two-sided Bonferroni p<=0.01/3 and >=4 positive holdout signs; REFUTED symmetrically requires a negative meaningful slope and >=4 negative holdout signs. Other estimable cases PARTIAL. All three remain in the denominator. Zero causal, policy, school, position and featured credit.",
            "threshold": threshold(study),
        },
        "prior_confidence": 0.30,
        "disclosure": s["caveat"] + " This test is a descriptive association and provides no identified policy or causal effect.",
        "steelman": steelman_path(study),
        "covers_claims": [], "linked_hypotheses": [], "linked_conditions": [],
        "notes": f"Frozen family preregistration: {PREREG}. Exact runner: {RUNNER}. Later source lock: {LOCK}.",
    }


def exposure_description(study: str) -> str:
    return {
        "law_homicide": "WGI rule-of-law estimate in 2010 minus 2000",
        "tractor_food": "log(1+tractors in use in 2000) minus log(1+tractors in use in 1990)",
        "self_employment_productivity": "self-employed share in 2000 minus 2010 percentage points",
    }[study]


def outcome_description(study: str) -> str:
    return {
        "law_homicide": "log(homicide rate in 2010) minus log(rate in 2020)",
        "tractor_food": "log(food-production index in 2010) minus log(index in 2000)",
        "self_employment_productivity": "log(GDP per employed person in 2020) minus log(level in 2010)",
    }[study]


def prereg_text() -> str:
    lines = [
        "# Three-domain forward calibration — frozen preregistration", "",
        "This is a closed three-test family of distinct descriptive public questions: rule of law and later homicide, tractor stock and later food production, and self-employment share and later GDP per worker. Family-wide two-sided alpha is 0.01; all three remain in the Bonferroni denominator, so each p cutoff is 0.01/3. No failed case can be omitted or replaced after values. No policy, causal, school, position or featured credit is allowed.", "",
        f"The key-only roster `{ROSTER}` contains 119, 100 and 215 valid-ISO3 country keys respectively (SHA-256 `{ROSTER_SHA}`). Only schemas, item/element/unit, country/year keys, source hashes, manifest metadata and the FAOSTAT flag legend were opened before this commit. No selected values, null/status masks, variation, sign or fit was opened. Rectangular WDI keys are not evidence of complete measurements.", "",
        "## Pinned sources", "",
        "| Role | Exact source | SHA-256 | Custody |", "| --- | --- | --- | --- |",
    ]
    for role, source in SOURCES.items():
        custody = source["manifest"] or "FAOSTAT archive/derived parquet; no tracked fetch-manifest entry"
        lines.append(f"| {role} | `{source['path']}` | `{source['sha256']}` | {custody} |")
    lines += ["", "The FAOSTAT tractor series is exact item `Agricultural tractors`, element `In Use`, unit `No`, at 1990 and 2000, with flags A (official), E (estimated) and X (international organization) admitted and individually reported. Blank/other flags are excluded. The matching FAOSTAT source archive is pinned, but the derived parquet lacks a tracked fetch-manifest entry; this limits provenance claims. WDI observations require blank/A status. No interpolation, endpoint switch, proxy substitution or imputation is permitted.", "", "## Frozen transformations and gates", ""]
    for key, s in STUDIES.items():
        lines += [
            f"### {s['title']}", "",
            f"Claim: {s['claim']} Source-key roster {s['nkeys']}; exposure {s['xyears'][0]}→{s['xyears'][1]}: {exposure_description(key)}; outcome {s['yyears'][0]}→{s['yyears'][1]}: {outcome_description(key)}. Positive slope means later improvement. Baseline exposure and baseline outcome enter as controls with an intercept. Minimum complete countries {s['min_complete']}; at least {s['min_material']} have exposure gain ≥{s['material']}; p90−p10 exposure-gain spread ≥{s['spread']}. Residualized exposure squared-share concentration: top country ≤{s['top_one']}, top {s['top_k']} ≤{s['top_k_max']}. Each of five deterministic hash-fold omissions requires ≥{s['holdout']} countries and a full-rank, finite, positive-uncertainty fit. Meaningful absolute slope ≥{s['beta']} {s['yunit']} {s['xunit']}. {s['caveat']}", "",
        ]
    lines += [
        "All countries are equally weighted. The fixed fold is `int(SHA256(ISO3)[0:8],16) % 5`. Full and fold fits use OLS of later outcome improvement on exposure gain plus the two baselines, HC3 robust uncertainty, and two-sided Student t. Full rank, finite positive standard error and positive residualized-exposure variation are required. Failed gates produce INCONCLUSIVE. With all gates clear, SUPPORTED requires a positive slope ≥ the meaningful bound, p≤0.01/3 and ≥4/5 positive fold signs; REFUTED requires the symmetric negative result. Other valid estimates are PARTIAL. The three-test correction does not repair archive-wide selection.", "",
        "Admissible ranges: WGI [-3,3], homicide rate (0,300] per 100,000, tractors in use [0,10,000,000], food-production index (0,1000], self-employment share [0,100] percent, and GDP per employed person (0,1,000,000] constant PPP dollars. An endpoint outside the range is excluded, not winsorized.", "",
        "Distinctness check: existing Bukele security cases concern specific 2019–2024 policies, existing government-effectiveness cases concern development outcomes, existing food-production cases concern trade/property rights rather than tractor stock, and existing labour cases do not test self-employment-share change against later GDP per worker. Earlier related tests remain visible; this wave cannot be counted as a policy effect or broad corpus graduation.", "",
    ]
    return "\n".join(lines).rstrip("\n")


def steelman_text(study: str) -> str:
    s = STUDIES[study]
    return f"# Steelman — {s['title']}\n\nThe directional claim is plausible only as a lagged descriptive association. {s['caveat']} Baseline adjustment and fixed country-hash omissions test fragility but cannot identify a causal mechanism. An opposite, null or gate-failed result is retained under the three-test correction, and no result earns policy or school credit.\n"


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def yaml_bytes(value) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()


def make_prereg() -> None:
    codes = roster()
    artifacts = {PREREG: (prereg_text() + "\n").encode()}
    for study in STUDIES:
        artifacts[spec_path(study)] = yaml_bytes(make_spec(study, codes[study]))
        artifacts[steelman_path(study)] = steelman_text(study).encode()
    for relative, blob in artifacts.items():
        path = ROOT / relative
        if path.exists():
            raise RuntimeError(f"refusing to replace preregistration file: {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    print("key-only preregistration files written; commit before copying or reading source values")


def registration_commit() -> str:
    paths = [RUNNER, PREREG, ROSTER] + [p for study in STUDIES for p in (spec_path(study), steelman_path(study))]
    revisions = {first_added(p) for p in paths}
    if len(revisions) != 1:
        raise RuntimeError("preregistration files must first appear in one commit")
    registration = revisions.pop()
    for path in paths:
        frozen(path, registration)
    if git("ls-tree", "-r", "--name-only", registration, "--", LOCK, *[run_dir(k) for k in STUDIES]).strip():
        raise RuntimeError("source lock or results entered registration commit")
    codes = roster()
    if (ROOT / PREREG).read_bytes() != (prereg_text() + "\n").encode():
        raise RuntimeError("preregistration prose differs from frozen design")
    for study in STUDIES:
        if yaml.safe_load((ROOT / spec_path(study)).read_text()) != make_spec(study, codes[study]):
            raise RuntimeError(f"spec differs from frozen design: {study}")
        if (ROOT / steelman_path(study)).read_text() != steelman_text(study):
            raise RuntimeError(f"steelman differs from frozen design: {study}")
    return registration


def manifest_sources() -> dict:
    for manifest, digest in MANIFESTS.items():
        if sha(ROOT / manifest) != digest:
            raise RuntimeError(f"fetch manifest hash mismatch: {manifest}")
    provenance = {}
    for role, source in SOURCES.items():
        if source["manifest"] is None:
            provenance[role] = {
                "publisher": source["publisher"], "series_id": source["series_id"],
                "parquet_or_archive_path": source["path"], "sha256": source["sha256"],
                "rows": source["rows"],
                "vintage_manifest_status": "absent; same-timestamp raw FAOSTAT archive and derived parquet pinned separately",
            }
            continue
        entries = yaml.safe_load((ROOT / source["manifest"]).read_text())["entries"]
        found = [e for e in entries if e.get("publisher") == source["publisher"]
                 and e.get("series_id") == source["series_id"]
                 and e.get("parquet_path") == source["path"]]
        if len(found) != 1 or found[0].get("sha256") != source["sha256"] or found[0].get("rows") != source["rows"]:
            raise RuntimeError(f"manifest source identity mismatch: {role}")
        provenance[role] = {key: found[0].get(key) for key in (
            "publisher", "series_id", "parquet_path", "sha256", "rows", "license",
            "fetch_utc", "source_url", "methodology_url",
        )}
    return provenance


def lock_payload(registration: str) -> dict:
    return {
        "schema": "ieset-three-domain-family-source-lock-v1", "family_id": FAMILY,
        "family_size": FAMILY_SIZE, "family_alpha": ALPHA, "bonferroni_p_max": P_MAX,
        "registration_commit": registration, "roster_sha256": ROSTER_SHA,
        "runner_sha256": hashlib.sha256(git("show", f"{registration}:{RUNNER}")).hexdigest(),
        "manifest_hashes": MANIFESTS, "sources": manifest_sources(),
    }


def make_lock() -> None:
    registration = registration_commit()
    for role, source in SOURCES.items():
        if sha(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"raw source hash mismatch before lock: {role}")
    path = ROOT / LOCK
    if path.exists():
        raise RuntimeError("refusing to replace source lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(json_bytes(lock_payload(registration)))
    print("source lock written; commit with newly pinned raw files before selected-value access")


def source_lock_commit(registration: str) -> str:
    paths = [LOCK] + [source["path"] for source in SOURCES.values()]
    revisions = {first_added(path) for path in paths}
    if len(revisions) != 1:
        raise RuntimeError("source lock and raw files must first appear in one commit")
    lock_revision = revisions.pop()
    if not strict_ancestor(registration, lock_revision):
        raise RuntimeError("source lock must follow registration")
    for path in paths:
        frozen(path, lock_revision)
    if json.loads((ROOT / LOCK).read_text()) != lock_payload(registration):
        raise RuntimeError("source lock metadata mismatch")
    for role, source in SOURCES.items():
        if sha(ROOT / source["path"]) != source["sha256"]:
            raise RuntimeError(f"raw source hash mismatch: {role}")
    return lock_revision


def finite(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def m49_to_iso(value):
    try:
        country = pycountry.countries.get(numeric=f"{int(str(value).strip(chr(39))):03d}")
        return country.alpha_3 if country else None
    except (TypeError, ValueError):
        return None


def read_values(role: str) -> dict:
    source = SOURCES[role]
    path = ROOT / source["path"]
    eligible = set().union(*roster().values())
    if role == "law":
        d = pd.read_parquet(path, columns=["country_iso3", "indicator_id", "year", "value"])
        years = [2000, 2010]
    elif role == "homicide":
        d = pd.read_parquet(path, columns=["country_iso3", "year", "Homicide rate per 100,000 population"])
        d = d.rename(columns={"Homicide rate per 100,000 population": "value"})
        years = [2010, 2020]
    elif role == "tractor":
        d = pd.read_parquet(path, columns=["Area Code (M49)", "Item", "Element", "Unit", "Year", "Value", "Flag"])
        d = d[(d.Item == "Agricultural tractors") & (d.Element == "In Use") & (d.Unit == "No")]
        d = d.rename(columns={"Year": "year", "Value": "value", "Flag": "flag"})
        d["country_iso3"] = d["Area Code (M49)"].map(m49_to_iso)
        years = [1990, 2000]
    elif role == "tractor_archive":
        raise RuntimeError("the raw FAOSTAT archive is a separately pinned custody source, not an estimator series")
    else:
        d = pd.read_parquet(path, columns=["country_iso3", "indicator_id", "year", "value", "obs_status"])
        years = [2000, 2010] if role == "self_employment" else ([2000, 2010] if role == "food" else [2010, 2020])
    if source["rows"] is not None and len(d) != source["rows"] and role != "tractor":
        raise RuntimeError(f"source row count changed: {role}")
    if role not in ("homicide", "tractor") and set(d.indicator_id.dropna().unique()) != {source["series_id"]}:
        raise RuntimeError(f"source indicator identity changed: {role}")
    d = d[d.year.isin(years) & d.country_iso3.isin(eligible)]
    if d.duplicated(["country_iso3", "year"]).any():
        raise RuntimeError(f"duplicate selected source key: {role}")
    out = {}
    for row in d.itertuples(index=False):
        iso = row.country_iso3
        year = int(row.year)
        value = finite(row.value)
        flag = None
        if role == "tractor":
            flag = str(row.flag).strip() if not pd.isna(row.flag) else ""
            if flag not in ("A", "E", "X"):
                value = None
        elif role in ("food", "self_employment", "productivity"):
            status = str(row.obs_status).strip() if not pd.isna(row.obs_status) else ""
            if status not in ("", "A"):
                value = None
        out[(iso, year)] = (value, flag)
    return out


def frame(study: str, values: dict, countries: list[str]):
    s = STUDIES[study]
    x = values[s["xrole"]]
    y = values[s["yrole"]]
    xa, xb = s["xyears"]
    ya, yb = s["yyears"]
    rows = []
    excluded = {"missing_or_nonfinite_or_status": 0, "out_of_range": 0}
    flag_counts = {"A": 0, "E": 0, "X": 0} if study == "tractor_food" else {}
    for iso in countries:
        x0, f0 = x.get((iso, xa), (None, None))
        x1, f1 = x.get((iso, xb), (None, None))
        y0, _ = y.get((iso, ya), (None, None))
        y1, _ = y.get((iso, yb), (None, None))
        if any(v is None for v in (x0, x1, y0, y1)):
            excluded["missing_or_nonfinite_or_status"] += 1
            continue
        if study == "law_homicide":
            okay = -3 <= x0 <= 3 and -3 <= x1 <= 3 and 0 < y0 <= 300 and 0 < y1 <= 300
            change = x1 - x0
            response = math.log(y0) - math.log(y1)
            baseline_x = x0
            baseline_y = math.log(y0)
        elif study == "tractor_food":
            okay = 0 <= x0 <= 10_000_000 and 0 <= x1 <= 10_000_000 and 0 < y0 <= 1000 and 0 < y1 <= 1000
            change = math.log1p(x1) - math.log1p(x0)
            response = math.log(y1) - math.log(y0)
            baseline_x = math.log1p(x0)
            baseline_y = math.log(y0)
        else:
            okay = 0 <= x0 <= 100 and 0 <= x1 <= 100 and 0 < y0 <= 1_000_000 and 0 < y1 <= 1_000_000
            change = x0 - x1
            response = math.log(y1) - math.log(y0)
            baseline_x = x0
            baseline_y = math.log(y0)
        if not okay:
            excluded["out_of_range"] += 1
            continue
        if flag_counts:
            flag_counts[f0] += 1
            flag_counts[f1] += 1
        rows.append({
            "country_iso3": iso, "exposure_gain": change, "x": change,
            "y": response, "baseline_x": baseline_x, "baseline_y": baseline_y,
            "fold": int(hashlib.sha256(iso.encode()).hexdigest()[:8], 16) % 5,
        })
    return pd.DataFrame(rows), excluded, flag_counts


def fit(data: pd.DataFrame, study: str):
    if len(data) < 8:
        return None
    x = data.x.to_numpy(dtype=float)
    y = data.y.to_numpy(dtype=float)
    base = np.column_stack([np.ones(len(data)), data.baseline_x.to_numpy(dtype=float), data.baseline_y.to_numpy(dtype=float)])
    design = np.column_stack([base[:, 0], x, base[:, 1:]])
    if np.linalg.matrix_rank(design) != design.shape[1]:
        return None
    model = sm.OLS(y, design).fit(cov_type="HC3", use_t=True)
    beta, se, p = map(float, (model.params[1], model.bse[1], model.pvalues[1]))
    residual_x = x - base @ np.linalg.lstsq(base, x, rcond=None)[0]
    squares = residual_x ** 2
    total = float(squares.sum())
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0 and math.isfinite(p) and total > 1e-10):
        return None
    shares = np.sort(squares / total)[::-1]
    top_k = STUDIES[study]["top_k"]
    interval = model.conf_int(alpha=P_MAX)[1]
    return {
        "coefficient": beta, "standard_error_hc3": se, "p_two_sided": p,
        "df_resid": int(model.df_resid),
        "familywise_ci_99_6667": [float(interval[0]), float(interval[1])],
        "top_country_residualized_exposure_share": float(shares[0]),
        f"top_{top_k}_residualized_exposure_share": float(shares[:top_k].sum()),
    }


def analyze(study: str, values: dict, countries: list[str]):
    s = STUDIES[study]
    data, excluded, flags = frame(study, values, countries)
    n = len(data)
    failed = []
    if n < s["min_complete"]:
        failed.append("min_complete_countries")
    material = int((data.exposure_gain >= s["material"]).sum()) if n else 0
    if material < s["min_material"]:
        failed.append("min_material_exposure_gain_countries")
    spread = float(np.percentile(data.exposure_gain, 90) - np.percentile(data.exposure_gain, 10)) if n else None
    if spread is None or spread < s["spread"]:
        failed.append("min_exposure_p90_p10_spread")
    estimate = fit(data, study)
    if estimate is None:
        failed.append("full_rank_positive_hc3_uncertainty_and_residual_exposure")
    else:
        if estimate["top_country_residualized_exposure_share"] > s["top_one"]:
            failed.append("max_top_country_residualized_exposure_share")
        if estimate[f"top_{s['top_k']}_residualized_exposure_share"] > s["top_k_max"]:
            failed.append(f"max_top_{s['top_k']}_residualized_exposure_share")
    folds = {}
    for i in range(5):
        subset = data[data.fold != i] if n else data
        model = fit(subset, study) if len(subset) >= s["holdout"] else None
        if len(subset) < s["holdout"]:
            failed.append(f"min_holdout_countries_fold_{i}")
        elif model is None:
            failed.append(f"holdout_estimator_fold_{i}")
        folds[str(i)] = {"countries": len(subset), "coefficient": model["coefficient"] if model else None}
    positive = sum(v["coefficient"] is not None and v["coefficient"] > 0 for v in folds.values())
    negative = sum(v["coefficient"] is not None and v["coefficient"] < 0 for v in folds.values())
    if failed:
        verdict = "INCONCLUSIVE"
    elif estimate["coefficient"] >= s["beta"] and estimate["p_two_sided"] <= P_MAX and positive >= MIN_HOLDOUT_SIGNS:
        verdict = "SUPPORTED"
    elif estimate["coefficient"] <= -s["beta"] and estimate["p_two_sided"] <= P_MAX and negative >= MIN_HOLDOUT_SIGNS:
        verdict = "REFUTED"
    else:
        verdict = "PARTIAL"
    result = {
        "design_id": s["id"], "family_id": FAMILY, "family_size": FAMILY_SIZE,
        "bonferroni_p_max": P_MAX, "verdict": verdict, "analysis_scope": "descriptive_only",
        "source_key_countries": s["nkeys"], "complete_countries": n,
        "excluded_reasons": excluded, "faostat_admitted_flag_readings": flags,
        "material_exposure_gain_countries": material, "exposure_gain_p90_p10_spread": spread,
        "estimate": estimate, "leave_one_hash_fold_out": folds,
        "positive_holdout_signs": positive, "negative_holdout_signs": negative,
        "failed_gates": sorted(set(failed)),
        "credit": {"causal": 0, "policy": 0, "school": 0, "position": 0, "featured": 0},
    }
    return result, data


def parquet_bytes(rows, columns) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=columns).to_parquet(buffer, index=False, engine="pyarrow")
    return buffer.getvalue()


def result_artifacts(study: str, result: dict, data: pd.DataFrame, registration: str, lock_revision: str) -> dict[str, bytes]:
    s = STUDIES[study]
    estimate = result["estimate"] or {}
    beta = estimate.get("coefficient")
    p = estimate.get("p_two_sided")
    failed = ", ".join(result["failed_gates"]) or "none"
    card = (
        f"# {s['title']}\n\n**{result['verdict']}** — descriptive only; zero causal, policy, school, position and featured credit.\n\n"
        f"Complete countries: {result['complete_countries']}/{s['nkeys']}; material gains: {result['material_exposure_gain_countries']}; "
        f"p90−p10 exposure spread: {result['exposure_gain_p90_p10_spread']}. HC3 slope: {beta} {s['yunit']} {s['xunit']}; "
        f"two-sided p: {p}; frozen family p cutoff: {P_MAX}. Failed gates: {failed}. "
        f"Hash-fold signs: +{result['positive_holdout_signs']}/5, −{result['negative_holdout_signs']}/5.\n\n"
        f"{s['caveat']} No identified policy or causal effect. All three tests remain in the Bonferroni denominator. "
        f"Registration `{registration}` preceded source lock `{lock_revision}`. "
        f"Exact replay: `python3 -B {RUNNER} --verify`.\n"
    )
    provenance = manifest_sources()
    roles = [s["xrole"], s["yrole"]] + (["tractor_archive"] if study == "tractor_food" else [])
    manifest = {
        "design_id": s["id"], "family_id": FAMILY, "family_size": FAMILY_SIZE,
        "bonferroni_p_max": P_MAX, "evidence_type": "descriptive",
        "verdict": result["verdict"], "spec_commit": registration,
        "lock_commit": lock_revision, "runner_sha256": sha(ROOT / RUNNER),
        "source_custody": {role: provenance[role] for role in roles},
        "credit": result["credit"],
        "artifacts": ["hypothesis.yaml", "manifest.yaml", "diagnostics.json", "coefficients.parquet", "metric_results.parquet", "chart_data.json", "result_card.md", "replication.py", "evidence_packet.yaml"],
    }
    packet = {
        "design_id": s["id"], "family_id": FAMILY, "family_size": FAMILY_SIZE,
        "bonferroni_p_max": P_MAX, "verdict": result["verdict"],
        "evidence_type": "descriptive", "causal_claim": False,
        "policy_effect_credit": False, "source_hashes_verified": True,
        "strict_spec_lock_chronology_verified": True, "school_claim_links": [],
        "correction": {"disposition": "descriptive_calibration_only", "family_id": FAMILY,
                       "family_size": FAMILY_SIZE, "family_alpha": ALPHA,
                       "bonferroni_p_max": P_MAX, **CREDIT},
        "interpretation": s["title"] + " association; no identified causal or policy effect.",
    }
    chart = {
        "design_id": s["id"], "sample_countries": len(data),
        "country_values_published": False,
        "exposure_gain_quantiles": {str(q): float(np.percentile(data.exposure_gain, q)) for q in (10, 25, 50, 75, 90)} if len(data) else {},
        "outcome_change_quantiles": {str(q): float(np.percentile(data.y, q)) for q in (10, 25, 50, 75, 90)} if len(data) else {},
    }
    replication = (
        "#!/usr/bin/env python3\nimport subprocess,sys\nfrom pathlib import Path\n"
        f"root=Path(__file__).resolve().parents[3]\nraise SystemExit(subprocess.call([sys.executable,'-B',str(root/'{RUNNER}'),'--verify']))\n"
    )
    directory = run_dir(study)
    return {
        f"{directory}/hypothesis.yaml": (ROOT / spec_path(study)).read_bytes(),
        f"{directory}/manifest.yaml": yaml_bytes(manifest),
        f"{directory}/diagnostics.json": json_bytes(result),
        f"{directory}/coefficients.parquet": parquet_bytes([{"term": "prior_exposure_gain", "coefficient": beta, "standard_error_hc3": estimate.get("standard_error_hc3"), "p_two_sided": p, "verdict": result["verdict"]}], ["term", "coefficient", "standard_error_hc3", "p_two_sided", "verdict"]),
        f"{directory}/metric_results.parquet": parquet_bytes([{"metric": "later_outcome_improvement", "value": beta, "p_value": p, "verdict": result["verdict"], "complete_countries": result["complete_countries"]}], ["metric", "value", "p_value", "verdict", "complete_countries"]),
        f"{directory}/chart_data.json": json_bytes(chart),
        f"{directory}/result_card.md": card.encode(),
        f"{directory}/replication.py": replication.encode(),
        f"{directory}/evidence_packet.yaml": yaml_bytes(packet),
    }


def family_summary(results: dict, registration: str, lock_revision: str) -> bytes:
    lines = [
        "# Three-domain forward calibration — locked descriptive family", "",
        f"Registration `{registration}` preceded source lock `{lock_revision}` and results. All three tests stay in the Bonferroni denominator: family α={ALPHA}; n={FAMILY_SIZE}; two-sided p≤{P_MAX}. No selected values or masks were opened before source lock.", "",
        "| Test | Complete / key countries | HC3 beta | Two-sided p | Verdict | Failed gates |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for study, s in STUDIES.items():
        result = results[study]
        estimate = result["estimate"] or {}
        lines.append(f"| {s['id']} | {result['complete_countries']}/{s['nkeys']} | {estimate.get('coefficient')} | {estimate.get('p_two_sided')} | {result['verdict']} | {', '.join(result['failed_gates']) or 'none'} |")
    lines += [
        "", "The FAOSTAT tractor parquet lacks a matching tracked fetch manifest; its same-timestamp raw archive and both exact hashes are pinned, while source-derivation proof remains limited. FAOSTAT A/E/X flag counts are in diagnostics. Key rows and modelled WDI fields do not establish observed complete cases. These are distinct descriptive associations only; no causal, policy, school, position or featured credit. The local three-test correction does not repair archive-wide selection.", "",
        f"Exact replay: `python3 -B {RUNNER} --verify`.", "",
    ]
    return "\n".join(lines).encode()


def reproduce(write: bool) -> None:
    registration = registration_commit()
    lock_revision = source_lock_commit(registration)
    countries = roster()
    values = {role: read_values(role) for role in SOURCES if role != "tractor_archive"}
    results = {}
    expected = {}
    for study in STUDIES:
        result, data = analyze(study, values, countries[study])
        results[study] = result
        expected.update(result_artifacts(study, result, data, registration, lock_revision))
    expected[SUMMARY] = family_summary(results, registration, lock_revision)
    for relative, blob in expected.items():
        path = ROOT / relative
        if write:
            if path.exists():
                raise RuntimeError(f"refusing to overwrite result artifact: {relative}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        elif not path.is_file() or path.read_bytes() != blob:
            raise RuntimeError(f"exact replay mismatch: {relative}")
    for study, result in results.items():
        print(study, result["verdict"], result["complete_countries"], result["estimate"], result["failed_gates"])
    print("family artifacts written" if write else "exact replay passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--make-prereg", action="store_true")
    mode.add_argument("--make-lock", action="store_true")
    mode.add_argument("--run", action="store_true")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.make_prereg:
        make_prereg()
    elif args.make_lock:
        make_lock()
    else:
        reproduce(args.run)


if __name__ == "__main__":
    main()
