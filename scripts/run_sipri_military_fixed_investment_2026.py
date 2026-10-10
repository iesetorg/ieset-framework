#!/usr/bin/env python3
"""Frozen SIPRI military-burden to later fixed-investment descriptive test.

Registration and source lock read source schemas, hashes, country/year identities
only. The first selected values or missingness masks are opened by measure,
after separate, ordered commits for the registration and exact source lock.
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
import pycountry
import pyarrow.parquet as pq
import statsmodels.formula.api as smf
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
HID = 'sipri_military_burden_future_fixed_investment_2026'
FAMILY = 'sipri_military_burden_fixed_investment_2026_10_10'
RUNNER = 'scripts/run_sipri_military_fixed_investment_2026.py'
SPEC = f'hypotheses/fiscal/{HID}.yaml'
STEELMAN = f'hypotheses/steelman/{HID}.md'
PLAN = 'engine/audits/sipri_military_fixed_investment_prereg_2026-10-10.md'
REPORT = 'engine/audits/sipri_military_fixed_investment_results_2026-10-10.md'
ROSTER = 'data/pinned_evidence/sipri_military_fixed_investment_2026_key_roster.csv'
ROSTER_SHA = '89007d1649c0c35620711b68ece70c20fed43c590ca0545f26e50596b4d7c1b4'
LOCK = f'data/pinned_evidence/{HID}.source.json'
RUN_DIR = f'engine/runs/{HID}'
SOURCES = {
    'military': dict(publisher='sipri', series_id='milex_share_gdp',
        path='data/vintages/sipri/milex_share_gdp@2026-04-30T114417Z.parquet',
        sha256='5ccce854cc3127eb0510b2f9f0e99741fb4a037a5950c745137970e7c618d3be',
        manifest='data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
        manifest_sha256='e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e'),
    'investment': dict(publisher='world_bank_wdi', series_id='NE.GDI.FTOT.ZS',
        path='data/vintages/world_bank_wdi/NE.GDI.FTOT.ZS@2026-05-05T203056Z.parquet',
        sha256='fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21',
        manifest='data/manifests/fetch_run_2026-05-05T203305Z.yaml',
        manifest_sha256='53db8ac480229d4bc8a22d509f4f9b267ad2bed0faa725728ad56822219222e0'),
    'income': dict(publisher='world_bank_wdi', series_id='NY.GDP.PCAP.KD',
        path='data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-05-05T194645Z.parquet',
        sha256='0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f',
        manifest='data/manifests/fetch_run_2026-05-05T200056Z.yaml',
        manifest_sha256='a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945'),
}
ANCHORS = (2000, 2005, 2010, 2015)
ALIASES = {'Brunei': 'BRN', 'Cape Verde': 'CPV', 'Congo, DR': 'COD',
    'Congo, Republic': 'COG', "Cote d'Ivoire": 'CIV', 'Gambia, The': 'GMB',
    'Korea, South': 'KOR', 'Kyrgyz Republic': 'KGZ', 'Laos': 'LAO',
    'Russia': 'RUS', 'Timor Leste': 'TLS'}
EXCLUDED_SOURCE_NAMES = ('Africa', 'Americas', 'Asia & Oceania',
    'Central America and the Caribbean', 'Central Asia', 'Central Europe',
    'Czechoslovakia', 'East Asia', 'Eastern Europe', 'Europe', 'European Union',
    'German Democratic Republic', 'Korea, North', 'Kosovo', 'Middle East',
    'North Africa', 'North America', 'Oceania', 'South America', 'South Asia',
    'South East Asia', 'USSR', 'Western Europe', 'Yemen, North', 'Yugoslavia',
    'sub-Saharan Africa')
KEY_ROWS = 660
KEY_COUNTRIES = 165
MIN_ROWS = 300
MIN_COUNTRIES = 90
MIN_PER_ANCHOR = 45
MIN_MATERIAL_ROWS = 50
MIN_MATERIAL_COUNTRIES = 35
MIN_RESIDUAL_X_SD = 0.20
MIN_RESIDUAL_Y_SD = 1.0
MAX_TOP_ONE_PERCENT_X_SS = 0.30
MAX_TOP_COUNTRY_X_SS = 0.20
MIN_FOLD_ROWS = 200
MIN_FOLD_COUNTRIES = 60
MIN_SAME_SIGN_FOLDS = 4
MATERIAL_CHANGE = 0.5
MAX_MILITARY_LEVEL = 20.0
MAX_ABS_MILITARY_CHANGE = 5.0
MAX_INVESTMENT_LEVEL = 80.0
ALPHA = 0.01
MIN_ABS_BETA = 0.25
CREDIT = dict(disposition='descriptive_calibration_only', causal_credit=0,
    policy_score_eligible=False, policy_score_credit=0,
    school_score_eligible=False, school_score_credit=0, featured_eligible=False)
LIMITS = [
    'SIPRI military expenditure and WDI gross fixed capital formation are both GDP shares; denominator changes can contribute to their movements.',
    'Gross fixed capital formation includes public and private assets and may include defense assets; it is not civilian public investment or a budget appropriation.',
    'Observed military spending changes are not exogenous budget shocks. Security threats, growth, fiscal capacity and accounting changes can confound the later association.',
    'The frozen 0–20 percent military level and 5-point change bounds focus on moderate budget movements and exclude some wars and crises.',
    'Four five-year windows share countries and data sources. One country/anchor fixed-effect test is one descriptive calibration, not four replications.',
    'The SIPRI vintage records no cell-level observation-status field; WDI observation-status cells do not establish within-country methodology continuity.',
    'The claim and negative prior follow visible fiscal crowding-out debates; the local 0.01 rule does not adjust for all IESET archive selection.',
    'No causal, policy, school, position or featured credit is assigned.',
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def js(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False, ensure_ascii=False) + '\n').encode()


def ya(value: Any) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True, width=100).encode()


def git(*args: str) -> bytes:
    proc = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {proc.stderr.decode(errors='replace')}")
    return proc.stdout


def first_add(path: str) -> str:
    commits = git('log', '--diff-filter=A', '--reverse', '--format=%H', 'HEAD', '--', path).decode().splitlines()
    if len(commits) != 1:
        raise RuntimeError(f'expected one first-addition commit for {path}: {commits}')
    return commits[0]


def frozen(path: str, commit: str) -> None:
    if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != git('show', f'{commit}:{path}'):
        raise RuntimeError(f'frozen file changed: {path}')
    if git('status', '--porcelain', '--', path).strip():
        raise RuntimeError(f'uncommitted frozen file: {path}')


def source_paths(source_root: Path) -> dict[str, Path]:
    paths = {}
    for role, source in SOURCES.items():
        path = source_root / source['path']
        manifest = ROOT / source['manifest']
        if not path.is_file() or sha(path) != source['sha256']:
            raise RuntimeError(f'missing or hash-mismatched raw source: {role}')
        if not manifest.is_file() or sha(manifest) != source['manifest_sha256']:
            raise RuntimeError(f'missing or hash-mismatched fetch manifest: {role}')
        rows = yaml.safe_load(manifest.read_text()).get('entries', [])
        matches = [row for row in rows if row.get('publisher') == source['publisher']
            and row.get('series_id') == source['series_id']
            and row.get('parquet_path') == source['path']
            and row.get('sha256') == source['sha256']]
        if len(matches) != 1:
            raise RuntimeError(f'no exact official fetch-manifest entry: {role}')
        required = {'Country', 'year', 'value'} if role == 'military' else {'country_iso3', 'indicator_id', 'year', 'value', 'obs_status'}
        if not required.issubset(pq.ParquetFile(path).schema_arrow.names):
            raise RuntimeError(f'selected source schema mismatch: {role}')
        paths[role] = path
    return paths


def country_map(names: set[str]) -> dict[str, str]:
    mapped = {}
    unresolved = []
    for name in sorted(names):
        if name in EXCLUDED_SOURCE_NAMES:
            continue
        try:
            code = ALIASES.get(name) or pycountry.countries.lookup(name).alpha_3
        except LookupError:
            unresolved.append(name)
            continue
        if code in mapped.values():
            raise RuntimeError(f'duplicate SIPRI country mapping: {code}')
        mapped[name] = code
    if unresolved or set(names) - set(mapped) != set(EXCLUDED_SOURCE_NAMES):
        raise RuntimeError(f'SIPRI country-label universe changed; unresolved={unresolved}')
    return mapped


def key_roster(paths: dict[str, Path]) -> list[tuple[str, str, int]]:
    # Deliberately select keys only; never the selected value or null/status columns.
    sipri = pq.read_table(paths['military'], columns=['Country', 'year']).to_pandas()
    investment = pq.read_table(paths['investment'], columns=['country_iso3', 'indicator_id', 'year']).to_pandas()
    income = pq.read_table(paths['income'], columns=['country_iso3', 'indicator_id', 'year']).to_pandas()
    if sipri.duplicated(['Country', 'year']).any():
        raise RuntimeError('duplicate SIPRI name/year key')
    names = country_map(set(sipri.Country))
    sipri_keys = {(str(name), int(year)) for name, year in zip(sipri.Country, sipri.year)}
    def wdi_keys(frame: pd.DataFrame, series: str) -> set[tuple[str, int]]:
        frame = frame[(frame.indicator_id == series) & frame.country_iso3.ne('')]
        if frame.duplicated(['country_iso3', 'year']).any():
            raise RuntimeError(f'duplicate national WDI key: {series}')
        return {(str(code), int(year)) for code, year in zip(frame.country_iso3, frame.year)}
    inv_keys = wdi_keys(investment, SOURCES['investment']['series_id'])
    income_keys = wdi_keys(income, SOURCES['income']['series_id'])
    rows = [(code, name, anchor) for name, code in names.items() for anchor in ANCHORS
        if (name, anchor - 5) in sipri_keys and (name, anchor) in sipri_keys
        and (code, anchor) in inv_keys and (code, anchor + 5) in inv_keys
        and (code, anchor - 5) in income_keys and (code, anchor) in income_keys]
    rows.sort()
    if len(rows) != KEY_ROWS or len({code for code, _, _ in rows}) != KEY_COUNTRIES:
        raise RuntimeError(f'key-only roster envelope changed: {len(rows)} rows')
    return rows


def roster_bytes(rows: list[tuple[str, str, int]]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(['country_iso3', 'sipri_country', 'anchor_year'])
    writer.writerows(rows)
    return out.getvalue().encode()


def loaded_roster(paths: dict[str, Path]) -> list[tuple[str, str, int]]:
    path = ROOT / ROSTER
    if sha(path) != ROSTER_SHA:
        raise RuntimeError('registered key roster hash mismatch')
    rows = key_roster(paths)
    if path.read_bytes() != roster_bytes(rows):
        raise RuntimeError('registered key roster no longer matches raw key identities')
    return rows


def threshold() -> dict[str, Any]:
    return dict(family_id=FAMILY, family_size=1, family_alpha=ALPHA,
        p_max_two_sided=ALPHA, expected_beta_sign='-', meaningful_beta_min_abs=MIN_ABS_BETA,
        source_key_roster_path=ROSTER, source_key_roster_sha256=ROSTER_SHA,
        source_lock_path=LOCK, source_sha256=SOURCES['military']['sha256'],
        secondary_source_sha256=SOURCES['investment']['sha256'],
        min_valid_rows=MIN_ROWS, min_valid_countries=MIN_COUNTRIES,
        min_rows_per_anchor=MIN_PER_ANCHOR, min_complete_anchors_per_country=2,
        min_material_change_rows=MIN_MATERIAL_ROWS,
        min_material_change_countries=MIN_MATERIAL_COUNTRIES,
        material_change_pp=MATERIAL_CHANGE, max_military_share_pct_gdp=MAX_MILITARY_LEVEL,
        max_abs_five_year_military_change_pp=MAX_ABS_MILITARY_CHANGE,
        max_investment_share_pct_gdp=MAX_INVESTMENT_LEVEL,
        min_residual_treatment_sd_pp=MIN_RESIDUAL_X_SD,
        min_residual_outcome_sd_pp=MIN_RESIDUAL_Y_SD,
        max_top_one_percent_treatment_ss_share=MAX_TOP_ONE_PERCENT_X_SS,
        max_top_country_treatment_ss_share=MAX_TOP_COUNTRY_X_SS,
        min_fold_rows=MIN_FOLD_ROWS, min_fold_countries=MIN_FOLD_COUNTRIES,
        min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,
        causal_credit=0, policy_score_eligible=False, policy_score_credit=0,
        school_score_eligible=False, school_score_credit=0, featured_eligible=False)


def specification(rows: list[tuple[str, str, int]]) -> dict[str, Any]:
    countries = sorted({code for code, _, _ in rows})
    return {'hypothesis_id': HID, 'version': 1, 'status': 'pre_registered',
        'topic': 'fiscal', 'claim_direction': '-',
        'claim': ('Across four frozen five-year national windows, larger rises in SIPRI military '
            'expenditure as a GDP share from t−5 to t predict smaller subsequent changes in WDI '
            'gross fixed capital formation as a GDP share from t to t+5, conditional on baseline '
            'investment, military burden, real income, prior income growth, and country/anchor effects.'),
        'evidence_type': 'associational',
        'methodology_note': ('One prospective descriptive panel test. The 660-row country/year roster '
            'and official source hashes were assembled from metadata and keys only; selected values, '
            'null masks and signs remain unopened before this registration and a separate source lock.'),
        'sample': {'countries': countries, 'period': [1995, 2020], 'temporal_structure': 'panel',
            'exclusion_rules': [
                'Only the frozen SIPRI-name-to-ISO3 key roster at t=2000, 2005, 2010 and 2015; require exact source keys at military t−5/t, WDI investment t/t+5, and WDI real GDP per capita t−5/t.',
                'After registration and source-lock commits, require finite military shares in [0,20] percent GDP at both endpoints and absolute five-year change <=5 points; finite investment shares in [0,80] at t and t+5; positive finite GDP per capita at t−5 and t.',
                'Retain countries with at least two complete anchors. No imputation, interpolation, winsorization, source substitution or post-result window/model/cap change. SIPRI has no cell-status field; WDI blank status is not proof of observed rather than estimated data.'
            ]},
        'variables': {'treatment': [{'name': 'prior_five_year_military_burden_change_pp',
            'source': 'sipri:milex_share_gdp',
            'transformation': 'Military expenditure percent of GDP at t minus percent of GDP at t−5; [0,20] endpoint and <=5-point absolute-change bounds.',
            'notes': 'Descriptive expenditure-share movement, not an exogenous defense budget policy shock.'}],
            'outcome': [{'name': 'later_five_year_fixed_investment_share_change_pp',
                'source': 'world_bank_wdi:NE.GDI.FTOT.ZS',
                'transformation': 'Gross fixed capital formation percent of GDP at t+5 minus percent of GDP at t.',
                'notes': 'Includes public and private fixed assets, potentially defense assets; not civil infrastructure spending.'}],
            'controls': [
                {'name': 'baseline_fixed_investment_share', 'source': 'world_bank_wdi:NE.GDI.FTOT.ZS', 'transformation': 'Percent GDP at t.'},
                {'name': 'baseline_military_burden', 'source': 'sipri:milex_share_gdp', 'transformation': 'Percent GDP at t−5.'},
                {'name': 'baseline_log_real_income', 'source': 'world_bank_wdi:NY.GDP.PCAP.KD', 'transformation': 'Natural log of constant-2015-dollar GDP per capita at t.'},
                {'name': 'prior_real_income_growth', 'source': 'world_bank_wdi:NY.GDP.PCAP.KD', 'transformation': 'Natural log GDP per capita at t minus log at t−5.'}]},
        'estimator': {'template': 'panel_fe', 'fixed_effects': ['country', 'anchor_year'],
            'clustering': 'country',
            'notes': ('Equal-country-anchor OLS of t-to-t+5 investment-share change on prior '
                'military-burden change, four frozen baseline controls, country and anchor-year effects. '
                'Country-cluster CR1 covariance; two-sided Student t(G−1), 99% interval; fixed five-fold '
                'country hash omissions for sign stability. One test, alpha .01.')},
        'falsification': {'test': 'sipri_military_fixed_investment_forward_2026_10_10',
            'rule': ('INCONCLUSIVE if exact-source/chronology, complete-case, anchor, material-change, '
                'residual-variation, concentration, full-rank, cluster-uncertainty or hash-fold coverage '
                'gates fail. SUPPORTED iff beta <= −0.25 investment-share points per +1 military-share '
                'point, two-sided p <= .01, and at least four of five folds are negative. REFUTED iff '
                'beta >= +0.25 with p <= .01 and at least four folds positive. Otherwise PARTIAL.'),
            'threshold': threshold()},
        'prior_confidence': 0.5,
        'disclosure': ('A negative prior reflects fiscal crowding-out debate, but the outcome is total '
            'fixed investment and GDP-share denominators can co-move. Country/year effects and controls '
            'do not identify causation or defense policy effects. Local alpha .01 does not correct '
            'archive-wide selection. Zero causal, policy, school, position and featured credit.'),
        'steelman': STEELMAN, 'scope': {'period': [1995, 2020], 'countries': countries,
            'outcome_dim': ['industrial_capability'], 'policy_family': ['none'],
            'treatment_tags': ['military_expenditure_gdp_share_change']},
        'covers_claims': [], 'linked_hypotheses': [], 'linked_conditions': []}


def plan_text() -> str:
    return f'''# Prospective SIPRI military burden → later fixed-investment share

This registration freezes **one** descriptive, source-distinct test. Four national five-year windows are repeated observations, not four independent hypotheses. The decision to examine fiscal crowding out follows existing visible IESET debates; the local p≤0.01 rule does not erase archive-wide selection.

## Before any selected value or missingness access

Only parquet schemas, fetch manifests and SHA-256 files, categorical SIPRI country labels, WDI indicator identities, and country/year keys were read. The immutable key roster has {KEY_ROWS} country-anchor rows across {KEY_COUNTRIES} countries at 2000, 2005, 2010 and 2015. WDI publishes a full key grid, so this is an upper bound, not a complete-case claim. No selected SIPRI or WDI `value` or `obs_status` column was opened before this registration. Commit this spec, steelman, plan, roster and runner together. Then commit `{LOCK}` separately. Only a later measured commit may open values.

## Locked question and decision

Treatment = SIPRI military expenditure/GDP change over t−5:t. Outcome = WDI gross fixed capital formation/GDP change over t:t+5. Require exact endpoints, moderate-range bounds, at least two anchors per country, baseline investment, baseline military burden, baseline log real GDP per capita and prior income growth. Country and anchor fixed effects; country-cluster CR1 Student-t inference; five fixed country hash-fold omissions. One negative directional test, two-sided alpha .01, meaningful |beta|≥0.25. All sample, variation, concentration, fold and inference gates are in the registered runner and spec. Any gate failure is INCONCLUSIVE; weaker estimable result is PARTIAL. No post-result gate change.

## Rights, limitations and score

The pinned SIPRI manifest says academic/press attribution required; WDI manifests say CC-BY-4.0. This packet publishes derived coefficients and counts, never SIPRI source values. Both measures are GDP shares; investment includes public/private and possibly military assets. A five-year lead, controls and fixed effects do not identify a budget crowd-out mechanism. Descriptive calibration only; no causal, policy, school, position or featured credit.
'''


def steelman_text() -> str:
    return f'''# Steelman: military burden and later fixed investment

**Registered ID:** `{HID}`. A prolonged rise in military expenditure relative to GDP may absorb fiscal capacity, foreign exchange, skilled labor and capital goods, leaving fewer resources for fixed investment over the next five years. The strongest version predicts a negative within-country association after baseline investment and development trends are accounted for. A positive association is also plausible: defense procurement can itself form capital, and stronger states may raise security spending and investment together.

The outcome is total national gross fixed capital formation as a GDP share. This test cannot separate civilian public infrastructure, private construction or defense assets. Threats, wars, recession denominators, commodity cycles and accounting revisions may jointly move both shares. The predefined 0–20 percent military burden and <=5-point change bounds focus on moderate movements; excluded crisis observations remain outside the claim. Source statuses do not certify comparable national methods.

One frozen four-window panel test uses a two-sided .01 cutoff, effect size 0.25 and four-of-five sign-fold gate. A negative passing coefficient supports only the descriptive prediction; a positive passing coefficient refutes that direction; weaker or design-limited results are partial or inconclusive. Neither outcome grants causal or policy credit.
'''


def write_registration(paths: dict[str, Path]) -> None:
    rows = key_roster(paths)
    expected = [SPEC, STEELMAN, PLAN, ROSTER]
    if any((ROOT / relative).exists() for relative in expected):
        raise FileExistsError('registration files already exist')
    raw = roster_bytes(rows)
    if hashlib.sha256(raw).hexdigest() != ROSTER_SHA:
        raise RuntimeError('key-only roster hash differs from frozen constant')
    spec = specification(rows)
    schema = json.loads((ROOT / 'schemas/hypothesis.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    if not Draft202012Validator(schema).is_valid(spec):
        errors = list(Draft202012Validator(schema).iter_errors(spec))
        raise RuntimeError(f'new spec fails schema: {[e.message for e in errors[:5]]}')
    for relative in expected:
        (ROOT / relative).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / SPEC).write_bytes(b'# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n' + ya(spec))
    (ROOT / STEELMAN).write_text(steelman_text())
    (ROOT / PLAN).write_text(plan_text())
    (ROOT / ROSTER).write_bytes(raw)


def registration_commit(paths: dict[str, Path]) -> str:
    files = [SPEC, STEELMAN, PLAN, ROSTER, RUNNER]
    commits = {first_add(path) for path in files}
    if len(commits) != 1:
        raise RuntimeError(f'registration files do not share first-addition commit: {commits}')
    commit = commits.pop()
    for path in files:
        frozen(path, commit)
    if git('ls-tree', '-r', '--name-only', commit, '--', LOCK, RUN_DIR).strip():
        raise RuntimeError('registration commit included source lock or measured result')
    rows = loaded_roster(paths)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    if spec != specification(rows):
        raise RuntimeError('frozen hypothesis differs from registered runner')
    schema = json.loads(git('show', f'{commit}:schemas/hypothesis.schema.json'))
    Draft202012Validator.check_schema(schema)
    if not Draft202012Validator(schema).is_valid(spec):
        raise RuntimeError('first committed spec invalid under registration schema')
    return commit


def source_lock_payload(registration: str) -> dict[str, Any]:
    return {'hypothesis_id': HID, 'family_id': FAMILY, 'family_size': 1,
        'registration_commit': registration, 'source_sha256': SOURCES['military']['sha256'],
        'secondary_source_sha256': SOURCES['investment']['sha256'],
        'key_roster_sha256': ROSTER_SHA, 'key_roster_path': ROSTER,
        'source_files': SOURCES,
        'selected_values_or_null_masks_read_before_lock': False,
        'statement': 'Exact official vintages and key-only roster locked after registration; selected measurements remain sealed.'}


def write_lock(registration: str) -> None:
    if (ROOT / LOCK).exists():
        raise FileExistsError(LOCK)
    (ROOT / LOCK).write_bytes(js(source_lock_payload(registration)))


def lock_commit(registration: str) -> str:
    commit = first_add(LOCK)
    if commit == registration or subprocess.run(['git','merge-base','--is-ancestor',registration,commit],cwd=ROOT).returncode:
        raise RuntimeError('source lock must follow registration commit')
    frozen(LOCK, commit)
    if json.loads((ROOT / LOCK).read_text()) != source_lock_payload(registration):
        raise RuntimeError('source lock differs from frozen exact pins')
    if git('ls-tree','-r','--name-only',commit,'--',RUN_DIR).strip():
        raise RuntimeError('source-lock commit already contained a result')
    return commit


def series_values(path: Path, role: str, roster: list[tuple[str,str,int]]) -> dict[tuple[str,int], float]:
    # First selected value and missingness read occurs only after committed lock checks.
    if role == 'military':
        table = pq.read_table(path, columns=['Country','year','value']).to_pandas()
        names = {name for _,name,_ in roster}
        table = table[table.Country.isin(names)]
        if table.duplicated(['Country','year']).any():
            raise RuntimeError('duplicate selected SIPRI value key')
        return {(str(name),int(year)):float(value) for name,year,value in zip(table.Country,table.year,table.value)}
    table = pq.read_table(path, columns=['country_iso3','indicator_id','year','value','obs_status']).to_pandas()
    countries = {code for code,_,_ in roster}
    table = table[(table.country_iso3.isin(countries)) & (table.indicator_id == SOURCES[role]['series_id'])]
    if table.duplicated(['country_iso3','year']).any():
        raise RuntimeError(f'duplicate selected WDI value key: {role}')
    # Blank and A statuses are admitted, but blanks carry no method-continuity assurance.
    bad = table.obs_status.fillna('').astype(str).map(lambda x: x not in ('','A'))
    table.loc[bad,'value'] = float('nan')
    return {(str(code),int(year)):float(value) for code,year,value in zip(table.country_iso3,table.year,table.value)}


def measured_panel(paths: dict[str,Path], roster: list[tuple[str,str,int]]) -> tuple[pd.DataFrame,dict[str,Any]]:
    military = series_values(paths['military'],'military',roster)
    investment = series_values(paths['investment'],'investment',roster)
    income = series_values(paths['income'],'income',roster)
    rows = []
    dropped = Counter()
    for code,name,t in roster:
        m0,m1 = military[(name,t-5)],military[(name,t)]
        i0,i1 = investment[(code,t)],investment[(code,t+5)]
        g0,g1 = income[(code,t-5)],income[(code,t)]
        if not all(map(math.isfinite,(m0,m1,i0,i1,g0,g1))):
            dropped['missing_or_nonfinite'] += 1
            continue
        if not (0 <= m0 <= MAX_MILITARY_LEVEL and 0 <= m1 <= MAX_MILITARY_LEVEL
            and abs(m1-m0) <= MAX_ABS_MILITARY_CHANGE):
            dropped['military_range'] += 1
            continue
        if not (0 <= i0 <= MAX_INVESTMENT_LEVEL and 0 <= i1 <= MAX_INVESTMENT_LEVEL):
            dropped['investment_range'] += 1
            continue
        if not (g0 > 0 and g1 > 0):
            dropped['income_range'] += 1
            continue
        rows.append(dict(country_iso3=code,anchor_year=t,x=m1-m0,y=i1-i0,
            baseline_investment=i0,baseline_military=m0,
            log_income=math.log(g1),prior_income_growth=math.log(g1/g0)))
    panel = pd.DataFrame(rows,columns=['country_iso3','anchor_year','x','y',
        'baseline_investment','baseline_military','log_income','prior_income_growth'])
    counts = panel.country_iso3.value_counts()
    below = panel.country_iso3.map(counts).lt(2)
    dropped['country_below_two_anchors'] += int(below.sum())
    panel = panel.loc[~below].sort_values(['country_iso3','anchor_year']).reset_index(drop=True)
    material = panel.x.abs().ge(MATERIAL_CHANGE)
    gate = {'key_roster_rows':len(roster),'key_roster_countries':KEY_COUNTRIES,
        'complete_rows_before_country_floor':len(rows),'valid_rows':len(panel),
        'valid_countries':int(panel.country_iso3.nunique()),
        'rows_per_anchor':{str(t):int((panel.anchor_year==t).sum()) for t in ANCHORS},
        'material_change_rows':int(material.sum()),
        'material_change_countries':int(panel.loc[material,'country_iso3'].nunique()),
        'dropped':dict(sorted(dropped.items())),
        'selected_values_read_after_committed_lock':True}
    return panel,gate


def form(outcome: str) -> str:
    return (f'{outcome} ~ x + baseline_investment + baseline_military + log_income + '
        'prior_income_growth + C(country_iso3) + C(anchor_year)')


def residual_form(outcome: str) -> str:
    return (f'{outcome} ~ baseline_investment + baseline_military + log_income + '
        'prior_income_growth + C(country_iso3) + C(anchor_year)')


def estimate(panel: pd.DataFrame, gate: dict[str,Any]) -> dict[str,Any]:
    failures=[]
    if gate['valid_rows'] < MIN_ROWS: failures.append('min_valid_rows')
    if gate['valid_countries'] < MIN_COUNTRIES: failures.append('min_valid_countries')
    if min(gate['rows_per_anchor'].values()) < MIN_PER_ANCHOR: failures.append('min_rows_per_anchor')
    if gate['material_change_rows'] < MIN_MATERIAL_ROWS: failures.append('min_material_change_rows')
    if gate['material_change_countries'] < MIN_MATERIAL_COUNTRIES: failures.append('min_material_change_countries')
    if failures:
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    residual_model=smf.ols(residual_form('x'),data=panel)
    if np.linalg.matrix_rank(residual_model.exog) != residual_model.exog.shape[1]:
        failures.append('residual_design_rank')
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    rx=np.asarray(residual_model.fit().resid,dtype=float)
    ss=rx**2
    total=float(ss.sum())
    xsd=math.sqrt(total/len(rx)) if total > 0 else 0.0
    top_n=max(1,math.ceil(0.01*len(rx)))
    top_share=float(sum(sorted(ss,reverse=True)[:top_n])/total) if total > 0 else 1.0
    by_country=panel.assign(ss=ss).groupby('country_iso3').ss.sum()
    country_share=float(by_country.max()/total) if total > 0 else 1.0
    ry_model=smf.ols(residual_form('y'),data=panel)
    if np.linalg.matrix_rank(ry_model.exog) != ry_model.exog.shape[1]:
        failures.append('outcome_residual_design_rank')
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    ry=np.asarray(ry_model.fit().resid,dtype=float)
    ysd=float(np.sqrt(np.mean(ry**2)))
    gate.update(residual_treatment_sd_pp=xsd,residual_outcome_sd_pp=ysd,
        top_one_percent_treatment_ss_share=top_share,
        top_country_treatment_ss_share=country_share)
    if xsd < MIN_RESIDUAL_X_SD: failures.append('min_residual_treatment_sd')
    if ysd < MIN_RESIDUAL_Y_SD: failures.append('min_residual_outcome_sd')
    if top_share > MAX_TOP_ONE_PERCENT_X_SS: failures.append('top_one_percent_treatment_concentration')
    if country_share > MAX_TOP_COUNTRY_X_SS: failures.append('top_country_treatment_concentration')
    if failures:
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    model=smf.ols(form('y'),data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        failures.append('primary_design_rank')
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    groups=int(panel.country_iso3.nunique())
    fit=model.fit(cov_type='cluster',cov_kwds={'groups':panel.country_iso3,
        'use_correction':True,'df_correction':True},use_t=True)
    beta,se=float(fit.params['x']),float(fit.bse['x'])
    if not (math.isfinite(beta) and math.isfinite(se) and se>0):
        failures.append('finite_cluster_uncertainty')
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    p=float(2*student_t.sf(abs(beta/se),groups-1))
    crit=float(student_t.ppf(0.995,groups-1))
    if not (math.isfinite(p) and math.isfinite(crit)):
        failures.append('finite_t_inference')
        return {'sample':gate,'primary':None,'hash_folds':[],
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    primary={'beta':beta,'country_cluster_se':se,'p_two_sided':p,
        'confidence_level':0.99,'confidence_interval':[beta-crit*se,beta+crit*se],
        'n_rows':len(panel),'n_countries':groups,'df_inference':groups-1,
        'model_rank':int(fit.model.rank),'model_columns':int(model.exog.shape[1]),
        'residual_treatment_sd_pp':xsd,'residual_outcome_sd_pp':ysd,
        'top_one_percent_treatment_ss_share':top_share,
        'top_country_treatment_ss_share':country_share,
        'method':'equal-row country/anchor FE OLS with four baseline controls; country CR1 cluster t(G-1)'}
    folds=[]
    for omitted in range(5):
        subset=panel[panel.country_iso3.map(lambda code:int(hashlib.sha256(code.encode()).hexdigest(),16)%5 != omitted)]
        if len(subset)<MIN_FOLD_ROWS or subset.country_iso3.nunique()<MIN_FOLD_COUNTRIES:
            failures.append(f'fold_{omitted}_coverage')
            continue
        fold_model=smf.ols(form('y'),data=subset)
        if np.linalg.matrix_rank(fold_model.exog) != fold_model.exog.shape[1]:
            failures.append(f'fold_{omitted}_rank')
            continue
        fold_beta=float(fold_model.fit().params['x'])
        if not math.isfinite(fold_beta):
            failures.append(f'fold_{omitted}_finite')
            continue
        folds.append({'omitted_hash_fold':omitted,'rows':len(subset),
            'countries':int(subset.country_iso3.nunique()),'beta':fold_beta})
    if failures:
        return {'sample':gate,'primary':primary,'hash_folds':folds,
            'gate_failures':failures,'verdict':'INCONCLUSIVE'}
    negative=sum(f['beta']<0 for f in folds)
    positive=sum(f['beta']>0 for f in folds)
    if beta<=-MIN_ABS_BETA and p<=ALPHA and negative>=MIN_SAME_SIGN_FOLDS:
        verdict='SUPPORTED'
    elif beta>=MIN_ABS_BETA and p<=ALPHA and positive>=MIN_SAME_SIGN_FOLDS:
        verdict='REFUTED'
    else:
        verdict='PARTIAL'
    return {'sample':gate,'primary':primary,'hash_folds':folds,
        'negative_folds':negative,'positive_folds':positive,
        'gate_failures':[],'verdict':verdict}


def artifacts(result: dict[str,Any],registration: str,locked: str,stamp: str) -> dict[str,bytes]:
    diagnostic={'hypothesis_id':HID,'family_id':FAMILY,'family_size':1,
        'registration_commit':registration,'source_lock_commit':locked,
        'source_sha256':SOURCES['military']['sha256'],
        'secondary_source_sha256':SOURCES['investment']['sha256'],
        'source_key_roster_sha256':ROSTER_SHA,'runner':RUNNER,'run_utc':stamp,
        'thresholds':threshold(),'result':result,'limitations':LIMITS,'correction':CREDIT}
    db=js(diagnostic)
    verdict=result['verdict']
    source={'publisher':'SIPRI Military Expenditure Database plus World Bank WDI',
        'source_sha256':SOURCES['military']['sha256'],
        'secondary_source_sha256':SOURCES['investment']['sha256'],
        'source_lock_commit':locked,'source_lock_manifest':LOCK,
        'key_roster_sha256':ROSTER_SHA,
        'input_vintages':[{'path':s['path'],'sha256':s['sha256'],'manifest':s['manifest']}
            for s in SOURCES.values()],
        'license':'SIPRI academic/press attribution plus World Bank CC BY 4.0',
        'contains_source_values':False}
    manifest={'hypothesis_id':HID,'status':verdict,'run_utc':stamp,'runner':RUNNER,
        'preregistration_commit':registration,'source':source,'family_id':FAMILY,
        'family_size':1,'sample':result['sample'],'correction':CREDIT}
    packet={'packet_version':1,'hypothesis':{'id':HID,'path':SPEC},
        'preregistration':{'commit':registration,'steelman':STEELMAN,'source_plan':PLAN,
            'key_roster':ROSTER},'source':source,
        'family':{'id':FAMILY,'size':1,'members':[HID],'interpretation':'One descriptive test across four repeated anchor windows'},
        'reproduction':{'runner':RUNNER,
            'command':f'python3 {RUNNER} verify --source-root /path/to/IESET',
            'result_sha256':hashlib.sha256(db).hexdigest()},
        'result':result,'limitations':LIMITS,'correction':CREDIT}
    primary=result['primary']
    card=f'# Result card: {HID}\n\nVerdict: **{verdict}**. '
    if result['gate_failures']:
        card+=f"Frozen gate failures: {', '.join(result['gate_failures'])}.\n\n"
    else:
        card+='All frozen design gates passed.\n\n'
    card+=(f"Preregistration `{registration}`; source lock `{locked}`.\n\n"
        f"Key-only roster {KEY_ROWS} / {KEY_COUNTRIES} countries; complete panel "
        f"{result['sample']['valid_rows']} / {result['sample']['valid_countries']} countries. "
        f"Material military-share changes {result['sample']['material_change_rows']} / "
        f"{result['sample']['material_change_countries']} countries.\n")
    if primary is not None:
        card+=(f"\nBeta={primary['beta']:+.6g} later investment-share points per +1 prior military-share point; "
            f"country-cluster SE={primary['country_cluster_se']:.6g}; two-sided p={primary['p_two_sided']:.6g}; "
            f"99% CI={primary['confidence_interval']}.\n")
    card+='\nDescriptive fiscal-allocation calibration only. Zero causal, policy, school, position or featured credit.\n'
    # Avoid format syntax dependent on conditional format specifiers.
    beta_text=f"{primary['beta']:+.6g}" if primary else 'not estimated'
    p_text=f"{primary['p_two_sided']:.6g}" if primary else 'not estimated'
    report=('# SIPRI military burden and later fixed-investment share: frozen result\n\n'
        f'Preregistration `{registration}`; source lock `{locked}`.\n\n'
        '| Verdict | Complete rows / countries | Material rows / countries | Beta | Two-sided p |\n'
        '| --- | ---: | ---: | ---: | ---: |\n'
        f"| **{verdict}** | {result['sample']['valid_rows']} / {result['sample']['valid_countries']} | "
        f"{result['sample']['material_change_rows']} / {result['sample']['material_change_countries']} | "
        f"{beta_text} | {p_text} |\n\n"
        'Beta is future five-year gross fixed-capital-formation/GDP-share change per +1-point prior five-year military-expenditure/GDP-share change. The one-test rule requires p≤.01, |beta|≥.25, and four-of-five stable country-fold signs. Total investment cannot isolate a civilian budget mechanism. Descriptive calibration only; no causal, policy, school, position or featured credit.\n')
    wrapper=("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root=Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
    return {'diagnostics.json':db,'manifest.yaml':ya(manifest),
        'evidence_packet.yaml':ya(packet),'result_card.md':card.encode(),
        'replication.py':wrapper.encode(),'hypothesis.yaml':(ROOT/SPEC).read_bytes(),
        'chart_data.json':js({'hypothesis_id':HID,'family_id':FAMILY,'verdict':verdict,
            'primary':primary}),'_report':report.encode()}


def equal_close(a: Any,b: Any,label: str) -> None:
    if isinstance(b,dict):
        if not isinstance(a,dict) or set(a)!=set(b):
            raise AssertionError(f'{label}: keys differ')
        for k,v in b.items(): equal_close(a[k],v,f'{label}.{k}')
    elif isinstance(b,list):
        if not isinstance(a,list) or len(a)!=len(b): raise AssertionError(f'{label}: list length differs')
        for i,v in enumerate(b): equal_close(a[i],v,f'{label}[{i}]')
    elif isinstance(b,float):
        if not math.isfinite(float(a)) or not math.isclose(float(a),b,rel_tol=1e-9,abs_tol=1e-11):
            raise AssertionError(f'{label}: numeric mismatch')
    elif a!=b: raise AssertionError(f'{label}: value differs')


def write_result(result: dict[str,Any],registration: str,locked: str) -> None:
    if (ROOT/RUN_DIR).exists() or (ROOT/REPORT).exists():
        raise FileExistsError('measured artifact already exists')
    stamp=datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    generated=artifacts(result,registration,locked,stamp)
    (ROOT/RUN_DIR).mkdir(parents=True)
    for name,content in generated.items():
        if name=='_report': (ROOT/REPORT).write_bytes(content)
        else: (ROOT/RUN_DIR/name).write_bytes(content)


def verify_result(result: dict[str,Any],registration: str,locked: str) -> None:
    diag=json.loads((ROOT/RUN_DIR/'diagnostics.json').read_text())
    expected=artifacts(result,registration,locked,diag['run_utc'])
    for name,content in expected.items():
        actual=ROOT/REPORT if name=='_report' else ROOT/RUN_DIR/name
        if name in ('diagnostics.json','manifest.yaml','evidence_packet.yaml','chart_data.json'):
            if name.endswith('.yaml'):
                equal_close(yaml.safe_load(actual.read_text()),yaml.safe_load(content),name)
            else: equal_close(json.loads(actual.read_text()),json.loads(content),name)
        elif actual.read_bytes()!=content:
            raise AssertionError(f'exact replay artifact differs: {name}')


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action',choices=['register','preflight','lock','measure','verify'])
    parser.add_argument('--source-root',type=Path,default=ROOT)
    args=parser.parse_args()
    paths=source_paths(args.source_root)
    if args.action=='register':
        write_registration(paths)
        print('wrote registration files from keys only; commit before lock')
        return 0
    if args.action=='preflight':
        rows=key_roster(paths)
        print(json.dumps({'key_only_rows':len(rows),'key_only_countries':len({x[0] for x in rows}),
            'anchors':dict(Counter(t for _,_,t in rows)),'selected_values_opened':False},sort_keys=True))
        return 0
    registration=registration_commit(paths)
    if args.action=='lock':
        write_lock(registration)
        print('wrote exact source lock; commit separately before measure')
        return 0
    locked=lock_commit(registration)
    panel,gate=measured_panel(paths,loaded_roster(paths))
    result=estimate(panel,gate)
    if args.action=='measure':
        write_result(result,registration,locked)
        print(json.dumps({'hypothesis_id':HID,'verdict':result['verdict'],
            'gate_failures':result['gate_failures'],'sample':gate,'primary':result['primary']},indent=2))
    else:
        verify_result(result,registration,locked)
        print('verified exact replay',HID,result['verdict'])
    return 0


if __name__=='__main__':
    raise SystemExit(main())
