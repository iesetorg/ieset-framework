#!/usr/bin/env python3
"""Frozen two-cell SIPRI military burden to later public-spending intensity study.

Register and lock modes read metadata, hashes and key columns only. Measure is
the first path that selects values or observation-status columns.
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
import pyarrow.parquet as pq
import pycountry
import statsmodels.formula.api as smf
import yaml
from jsonschema import Draft202012Validator
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
RUNNER = 'scripts/run_sipri_wdi_public_budget_2026.py'
FAMILY = 'sipri_military_burden_public_spending_intensity_2026_10_10'
PLAN = 'engine/audits/sipri_wdi_public_budget_prereg_2026-10-10.md'
REPORT = 'engine/audits/sipri_wdi_public_budget_results_2026-10-10.md'
ROSTER = 'data/pinned_evidence/sipri_wdi_public_budget_2026_key_roster.csv'
ROSTER_SHA = '5e911aebf7d38ba3d7bd16c588b6df0a1880d5d4ad2ac37aa2e4d6a4ee3cd9e0'
LOCK = 'data/pinned_evidence/sipri_wdi_public_budget_2026.source.json'
SOURCES = {
    'military': dict(publisher='sipri', series_id='milex_share_gdp',
        path='data/vintages/sipri/milex_share_gdp@2026-04-30T114417Z.parquet',
        sha256='5ccce854cc3127eb0510b2f9f0e99741fb4a037a5950c745137970e7c618d3be',
        manifest='data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml',
        manifest_sha256='e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e',
        url='https://www.sipri.org/sites/default/files/SIPRI-Milex-data-1948-2023.xlsx'),
    'education': dict(publisher='world_bank_wdi', series_id='SE.XPD.TOTL.GD.ZS',
        path='data/vintages/world_bank_wdi/SE.XPD.TOTL.GD.ZS@2026-10-10T153058Z.parquet',
        sha256='ba5ea0a9f827c269201f100b0ec6fc5ec389cc1c09e12c3f965bdbe67c936343',
        manifest='data/manifests/fetch_run_2026-10-10T153104Z.yaml',
        manifest_sha256='ff68e7fafbc9d9610bd07e7c37842714f2724c25f6fe498178815d3dc46b0589',
        url='https://api.worldbank.org/v2/country/all/indicator/SE.XPD.TOTL.GD.ZS?format=json'),
    'health': dict(publisher='world_bank_wdi', series_id='SH.XPD.GHED.GD.ZS',
        path='data/vintages/world_bank_wdi/SH.XPD.GHED.GD.ZS@2026-10-10T152904Z.parquet',
        sha256='ed34f5aa5ca8779ba04393624703fbb50c8802c70ecd99722bb0dd9544d3dcd6',
        manifest='data/manifests/fetch_run_2026-10-10T152949Z.yaml',
        manifest_sha256='ae85a64bda7150b7979bb5d83ddeabf5e5e36a0938c504eb5f33a94e45cc8a2e',
        url='https://api.worldbank.org/v2/country/all/indicator/SH.XPD.GHED.GD.ZS?format=json'),
    'expense': dict(publisher='world_bank_wdi', series_id='GC.XPN.TOTL.GD.ZS',
        path='data/vintages/world_bank_wdi/GC.XPN.TOTL.GD.ZS@2026-10-10T153047Z.parquet',
        sha256='c5a3109a9820ad858aaae8adf974b33ecbcc6e22a2bb49b6849f92fc2f9e6aad',
        manifest='data/manifests/fetch_run_2026-10-10T153052Z.yaml',
        manifest_sha256='aef94604623cb121cac65fc746af3a06b505a3d711a567e791660ebca306be50',
        url='https://api.worldbank.org/v2/country/all/indicator/GC.XPN.TOTL.GD.ZS?format=json'),
    'income': dict(publisher='world_bank_wdi', series_id='NY.GDP.PCAP.KD',
        path='data/vintages/world_bank_wdi/NY.GDP.PCAP.KD@2026-10-10T153109Z.parquet',
        sha256='9399298c8915ec2e05da6cee5c532e7e5c10a8f4df8f6dded026261db36d1381',
        manifest='data/manifests/fetch_run_2026-10-10T153117Z.yaml',
        manifest_sha256='85ea896f0acbf97070725be094751524fafba907a12f8594357a1d8ac14f2c27',
        url='https://api.worldbank.org/v2/country/all/indicator/NY.GDP.PCAP.KD?format=json'),
}
CELLS = (
    dict(role='education', id='sipri_military_burden_later_education_spending_2026',
        topic='fiscal', label='government education expenditure', dimension='fiscal_policy'),
    dict(role='health', id='sipri_military_burden_later_public_health_spending_2026',
        topic='healthcare', label='domestic general government health expenditure', dimension='fiscal_policy'),
)
ANCHORS = tuple(range(2003, 2017))
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
KEY_ROWS = 2310
KEY_COUNTRIES = 165
MIN_ROWS = 300
MIN_COUNTRIES = 50
MIN_ANCHORS = 10
MIN_COUNTRY_ANCHORS = 3
MATERIAL_CHANGE = 0.25
MIN_MATERIAL_ROWS = 60
MIN_MATERIAL_COUNTRIES = 20
MIN_RESIDUAL_X_SD = 0.15
MIN_RESIDUAL_Y_SD = 0.10
MAX_TOP_ONE_PERCENT_SS = 0.25
MAX_TOP_COUNTRY_SS = 0.20
MIN_FOLD_ROWS = 200
MIN_FOLD_COUNTRIES = 35
MIN_SAME_SIGN_FOLDS = 4
ALPHA_FAMILY = 0.01
ALPHA_CELL = ALPHA_FAMILY / len(CELLS)
MIN_ABS_BETA = 0.30
CREDIT = dict(disposition='descriptive_calibration_only', causal_credit=0,
    policy_score_eligible=False, policy_score_credit=0, school_score_eligible=False,
    school_score_credit=0, featured_eligible=False)
LIMITS = [
    'Both public-spending outcomes and SIPRI military expenditure are shares of GDP; denominator changes can jointly move them.',
    'Government education expenditure and domestic government health expenditure are spending intensity proxies, not appropriations or proven budget substitutions.',
    'Security threats, recessions, fiscal capacity, tax changes and national accounting changes remain confounders despite controls and fixed effects.',
    'Overlapping annual three-year windows share observations. Country clustering addresses within-country covariance but does not create independent experiments.',
    'The SIPRI vintage lacks cell-level status; WDI observation flags do not establish stable national definitions.',
    'These two correlated endpoints extend the same visible SIPRI programme. The two-cell correction does not adjust for archive-wide selection.',
    'SIPRI source terms restrict raw redistribution. Only derived diagnostics are published.',
    'No causal, policy, school, position or featured credit is assigned.',
]

def spec_path(cell: dict[str, str]) -> str:
    return f"hypotheses/{cell['topic']}/{cell['id']}.yaml"

def steelman_path(cell: dict[str, str]) -> str:
    return f"hypotheses/steelman/{cell['id']}.md"

def run_dir(cell: dict[str, str]) -> str:
    return f"engine/runs/{cell['id']}"

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
        entries = yaml.safe_load(manifest.read_text()).get('entries', [])
        matches = [row for row in entries if row.get('publisher') == source['publisher']
            and row.get('series_id') == source['series_id']
            and row.get('parquet_path') == source['path']
            and row.get('sha256') == source['sha256']]
        if len(matches) != 1:
            raise RuntimeError(f'no exact official fetch-manifest entry: {role}')
        required = {'Country', 'year', 'value'} if role == 'military' else {
            'country_iso3', 'indicator_id', 'year', 'value', 'obs_status'}
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

def key_roster(paths: dict[str, Path]) -> list[tuple[str, int]]:
    # Key columns only. WDI supplies skeleton keys even when a value is absent.
    sipri = pq.read_table(paths['military'], columns=['Country', 'year']).to_pandas()
    if sipri.duplicated(['Country', 'year']).any():
        raise RuntimeError('duplicate SIPRI name/year key')
    names = country_map(set(sipri.Country))
    military_keys = {(str(name), int(year)) for name, year in zip(sipri.Country, sipri.year)}
    wdi_keys = {}
    for role in ('education', 'health', 'expense', 'income'):
        frame = pq.read_table(paths[role], columns=['country_iso3', 'indicator_id', 'year']).to_pandas()
        frame = frame[(frame.indicator_id == SOURCES[role]['series_id']) & frame.country_iso3.ne('')]
        if frame.duplicated(['country_iso3', 'year']).any():
            raise RuntimeError(f'duplicate national WDI key: {role}')
        wdi_keys[role] = {(str(code), int(year)) for code, year in zip(frame.country_iso3, frame.year)}
    rows = []
    for name, code in names.items():
        for anchor in ANCHORS:
            if (name, anchor - 3) not in military_keys or (name, anchor) not in military_keys:
                continue
            if any((code, year) not in wdi_keys[role]
                   for role in ('education', 'health')
                   for year in (anchor - 3, anchor, anchor + 3)):
                continue
            if (code, anchor) not in wdi_keys['expense'] or (code, anchor) not in wdi_keys['income']:
                continue
            rows.append((code, anchor))
    rows.sort()
    if len(rows) != KEY_ROWS or len({code for code, _ in rows}) != KEY_COUNTRIES:
        raise RuntimeError(f'key-only roster envelope changed: {len(rows)} rows')
    return rows

def roster_bytes(rows: list[tuple[str, int]]) -> bytes:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(['country_iso3', 'anchor_year'])
    writer.writerows(rows)
    return out.getvalue().encode()

def loaded_roster(paths: dict[str, Path]) -> list[tuple[str, int]]:
    path = ROOT / ROSTER
    if sha(path) != ROSTER_SHA:
        raise RuntimeError('registered key roster hash mismatch')
    rows = key_roster(paths)
    if path.read_bytes() != roster_bytes(rows):
        raise RuntimeError('registered key roster differs from source key identities')
    return rows

def threshold() -> dict[str, Any]:
    return dict(family_id=FAMILY, family_size=2, family_alpha=ALPHA_FAMILY,
        p_max_two_sided=ALPHA_CELL, expected_beta_sign='-', meaningful_beta_min_abs=MIN_ABS_BETA,
        source_key_roster_path=ROSTER, source_key_roster_sha256=ROSTER_SHA,
        source_lock_path=LOCK, source_sha256=SOURCES['military']['sha256'],
        min_valid_rows=MIN_ROWS, min_valid_countries=MIN_COUNTRIES,
        min_distinct_anchors=MIN_ANCHORS, min_complete_anchors_per_country=MIN_COUNTRY_ANCHORS,
        min_material_change_rows=MIN_MATERIAL_ROWS, min_material_change_countries=MIN_MATERIAL_COUNTRIES,
        material_change_pp=MATERIAL_CHANGE, max_military_share_pct_gdp=20.0,
        max_abs_three_year_military_change_pp=5.0, max_outcome_share_pct_gdp=20.0,
        max_abs_three_year_outcome_change_pp=5.0, max_government_expense_pct_gdp=100.0,
        min_residual_treatment_sd_pp=MIN_RESIDUAL_X_SD,
        min_residual_outcome_sd_pp=MIN_RESIDUAL_Y_SD,
        max_top_one_percent_treatment_ss_share=MAX_TOP_ONE_PERCENT_SS,
        max_top_country_treatment_ss_share=MAX_TOP_COUNTRY_SS,
        min_fold_rows=MIN_FOLD_ROWS, min_fold_countries=MIN_FOLD_COUNTRIES,
        min_same_sign_hash_folds=MIN_SAME_SIGN_FOLDS,
        causal_credit=0, policy_score_eligible=False, policy_score_credit=0,
        school_score_eligible=False, school_score_credit=0, featured_eligible=False)

def specification(cell: dict[str, str], rows: list[tuple[str, int]]) -> dict[str, Any]:
    countries = sorted({code for code, _ in rows})
    role = cell['role']
    return {'hypothesis_id': cell['id'], 'version': 1, 'status': 'pre_registered',
        'topic': cell['topic'], 'claim_direction': '-',
        'claim': (f"Across frozen annual country anchors 2003–2016, larger rises in SIPRI military "
            f"expenditure as a GDP share from t−3 to t predict smaller subsequent t to t+3 "
            f"changes in WDI {cell['label']} as a GDP share, conditional on prior outcome change, "
            f"baseline outcome and fiscal/income levels, with country and anchor-year fixed effects."),
        'evidence_type': 'associational',
        'methodology_note': ('One of two correlated SIPRI public-spending-intensity extension tests. '
            'The shared 2310-row physical key roster and five official source hashes were assembled '
            'without reading selected values or null masks. Measurement follows separate commits '
            'for registration and exact source lock.'),
        'sample': {'countries': countries, 'period': [2000, 2019], 'temporal_structure': 'panel',
            'exclusion_rules': [
                'Only the frozen national country/anchor roster, t=2003–2016, with physical SIPRI keys at t−3/t, both WDI spending series at t−3/t/t+3, and WDI general expense and income keys at t.',
                'After source lock, retain finite military shares in [0,20] at t−3/t with |change|≤5 points; finite outcome shares in [0,20] at t−3/t/t+3 with both three-year changes ≤5 points; fiscal expense in [0,100] and positive real GDP per capita at t.',
                'Retain countries with at least three complete anchors. No imputation, interpolation, winsorization, status substitution, alternative lag or post-result gate changes. Admit blank/A WDI statuses only; neither certifies accounting comparability.'
            ]},
        'variables': {'treatment': [{'name': 'prior_three_year_military_burden_change_pp',
            'source': 'sipri:milex_share_gdp',
            'transformation': 'Military expenditure percent GDP at t minus t−3; [0,20] endpoints and |change|≤5 points.',
            'notes': 'Prior descriptive spending-share movement; not an exogenous policy shock.'}],
            'outcome': [{'name': f"later_three_year_{cell['dimension']}_change_pp",
                'source': f"world_bank_wdi:{SOURCES[role]['series_id']}",
                'transformation': f"{cell['label'].capitalize()} percent GDP at t+3 minus t.",
                'notes': 'Public spending intensity with a shared GDP denominator, not a budget appropriation.'}],
            'controls': [
                {'name': 'prior_outcome_share_change', 'source': f"world_bank_wdi:{SOURCES[role]['series_id']}",
                    'transformation': 'Percent GDP at t minus t−3.'},
                {'name': 'baseline_outcome_share', 'source': f"world_bank_wdi:{SOURCES[role]['series_id']}",
                    'transformation': 'Percent GDP at t.'},
                {'name': 'baseline_government_expense_share', 'source': 'world_bank_wdi:GC.XPN.TOTL.GD.ZS',
                    'transformation': 'General government expense percent GDP at t.'},
                {'name': 'baseline_log_real_income', 'source': 'world_bank_wdi:NY.GDP.PCAP.KD',
                    'transformation': 'Natural log real GDP per capita at t.'}]},
        'estimator': {'template': 'panel_fe', 'fixed_effects': ['country', 'anchor_year'],
            'clustering': 'country', 'notes': (
                'Equal country-anchor OLS with four frozen controls, country and year FE; '
                'country CR1 cluster SE and two-sided Student t(G−1), 99.5% interval. '
                'Five fixed SHA256 country-fold omissions assess coefficient sign stability. '
                'Both cells remain in the 0.01/2 denominator even if one is inconclusive.')},
        'falsification': {'test': f"sipri_wdi_public_budget_{role}_2026_10_10",
            'rule': ('INCONCLUSIVE if exact source/chronology, complete-row/country/year, material change, '
                'residual variation, concentration, full-rank, uncertainty or five-fold coverage gates fail. '
                'SUPPORTED iff beta≤−0.30 percentage points per +1 military point with two-sided p≤0.005 '
                'and at least four of five fold signs negative. REFUTED iff beta≥+0.30, p≤0.005 '
                'and at least four signs positive. Otherwise PARTIAL.'),
            'threshold': threshold()},
        'prior_confidence': 0.5,
        'disclosure': ('A negative prior follows visible fiscal crowding-out debates. Both outcomes share '
            'a GDP denominator with SIPRI and national accounting can shift. Controls and fixed effects '
            'do not identify causation or a defense-to-civilian substitution. This correlated two-cell '
            'extension is not independent archive replication; zero causal/policy/school/featured credit.'),
        'steelman': steelman_path(cell),
        'scope': {'period': [2000, 2019], 'countries': countries,
            'outcome_dim': [cell['dimension']], 'policy_family': ['none'],
            'treatment_tags': ['military_expenditure_gdp_share_change']},
        'covers_claims': [], 'linked_hypotheses': [], 'linked_conditions': []}

def plan_text() -> str:
    return f'''# Prospective SIPRI military burden → later public-spending intensity

This is a bounded **two-cell correlated extension** of existing SIPRI military-burden hypotheses. It tests education and domestic public-health spending intensities, not independent data sources or causal substitutions. Both cells are retained in the family-wide 0.01/2 multiplicity denominator, including failed cells. The local correction does not repair archive-wide selection.

## Value-blind source and design freeze

Only source metadata, manifests, file hashes, schemas, country identifiers, years and indicator IDs were used. The shared immutable roster has {KEY_ROWS} physical opportunities, {KEY_COUNTRIES} ISO3 countries and annual t=2003–2016 anchors. WDI supplies full country/year skeletons, so these are upper bounds, not complete-case counts. No selected SIPRI/WDI measurements, WDI status columns, value-null masks or signs were opened before this registration. Commit both specs, steelmans, roster, this plan and the runner together. Commit the exact source lock separately. The runner checks both commits before its first value read.

## Locked test

Treatment: SIPRI military expenditure percent GDP change t−3→t. Two separate outcomes: WDI government education expenditure percent GDP, and WHO-sourced WDI domestic general government health expenditure percent GDP, each changing t→t+3. Controls: the same outcome's prior t−3→t change and t level, WDI general government expense percent GDP at t, and log constant-dollar GDP per capita at t. Country and annual anchor fixed effects. Equal rows, country CR1 standard errors, Student t(G−1), two-sided 99.5% intervals. Five fixed country-hash omission folds. Yearly windows overlap.

Complete cases require exact endpoints and blank/A WDI status; finite range 0–20 percent GDP for military/outcome levels, |three-year changes|≤5 percentage points for military and both prior/future outcome changes; general expense 0–100 and real income >0. At least three complete anchors per retained country, 300 complete rows, 50 countries, 10 distinct anchors, 60 material military changes (≥0.25 points) spanning 20 countries; residualized treatment SD≥0.15 and outcome SD≥0.10 points; top 1% rows ≤25% and top country ≤20% of residual treatment sum of squares; full-rank designs and finite CR1 uncertainty. Each omission fold needs 200 rows and 35 countries. Failed gates yield INCONCLUSIVE. Otherwise a beta≤−0.30 (or ≥+0.30), p≤0.005, and ≥4/5 same-sign fold betas is SUPPORTED (or REFUTED); weaker results are PARTIAL.

## Source custody and rights

SIPRI `milex_share_gdp` is derived from [SIPRI Milex XLSX]({SOURCES['military']['url']}); raw redistribution is limited by [SIPRI terms](https://www.sipri.org/about/terms-and-conditions). The October 2026 WDI indicator API vintages are government education `SE.XPD.TOTL.GD.ZS` (UNESCO), domestic public health `SH.XPD.GHED.GD.ZS` (WHO GHED), government expense `GC.XPN.TOTL.GD.ZS`, and constant-dollar income `NY.GDP.PCAP.KD`; WDI metadata states CC BY 4.0. Exact routes, cache SHA-256 and fetch manifest SHA-256 are pinned in the runner and source lock. Raw Parquets remain ignored. Packets contain derived diagnostics only.

The measures share a GDP denominator. Security, fiscal and national-accounting shocks can move both. The two outcomes are related budget-intensity indicators, not proof of a tradeoff, and do not earn causal, policy, school, position or featured credit.
'''

def steelman_text(cell: dict[str, str]) -> str:
    return f'''# Steelman: prior military burden and later {cell['label']}

**Registered ID:** `{cell['id']}`. Sustained military spending may absorb fiscal capacity, making a subsequent slowdown in {cell['label']} plausible. The strongest descriptive prediction is a negative within-country association after its own prior trend, baseline level, fiscal expense, income, and country/year effects. A positive association is equally plausible when stronger or threatened states expand multiple spending categories together.

The outcome is a GDP share, not an appropriation or a direct civilian-versus-defense budget transfer. GDP denominator changes, war, health/education needs, public revenue, external financing and accounting definitions can jointly move both shares. Overlapping annual windows and common SIPRI exposure tie this result to the other family cell and the existing SIPRI programme. A qualifying sign is descriptive only.

The frozen family uses two-sided p≤0.005 per cell, |beta|≥0.30, four-of-five hash-fold sign stability and all sample/influence gates. Failed gates are inconclusive. Neither sign grants causal or policy credit.
'''

def write_registration(paths: dict[str, Path]) -> None:
    rows = key_roster(paths)
    expected = [RUNNER, ROSTER, PLAN] + [p for c in CELLS for p in (spec_path(c), steelman_path(c))]
    if any((ROOT / p).exists() for p in expected if p != RUNNER and p != ROSTER):
        raise FileExistsError('registration file already exists')
    if (ROOT / ROSTER).read_bytes() != roster_bytes(rows) or sha(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError('key-only roster differs from frozen bytes')
    schema = json.loads((ROOT / 'schemas/hypothesis.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    for cell in CELLS:
        spec = specification(cell, rows)
        errors = list(Draft202012Validator(schema).iter_errors(spec))
        if errors:
            raise RuntimeError(f"invalid {cell['id']}: {[e.message for e in errors[:5]]}")
    for cell in CELLS:
        spec, steelman = spec_path(cell), steelman_path(cell)
        (ROOT / spec).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / spec).write_bytes(b'# yaml-language-server: $schema=../../schemas/hypothesis.schema.json\n' + ya(specification(cell, rows)))
        (ROOT / steelman).write_text(steelman_text(cell))
    (ROOT / PLAN).write_text(plan_text())

def registration_commit(paths: dict[str, Path]) -> str:
    files = [RUNNER, ROSTER, PLAN] + [p for c in CELLS for p in (spec_path(c), steelman_path(c))]
    commits = {first_add(p) for p in files}
    if len(commits) != 1:
        raise RuntimeError(f'registration files not added together: {commits}')
    commit = commits.pop()
    for p in files:
        frozen(p, commit)
    if git('ls-tree', '-r', '--name-only', commit, '--', LOCK).strip():
        raise RuntimeError('registration commit contained source lock')
    for cell in CELLS:
        if git('ls-tree', '-r', '--name-only', commit, '--', run_dir(cell)).strip():
            raise RuntimeError('registration commit contained result')
    rows = loaded_roster(paths)
    schema = json.loads(git('show', f'{commit}:schemas/hypothesis.schema.json'))
    for cell in CELLS:
        spec = yaml.safe_load((ROOT / spec_path(cell)).read_text())
        if spec != specification(cell, rows) or list(Draft202012Validator(schema).iter_errors(spec)):
            raise RuntimeError(f"frozen spec differs from runner: {cell['id']}")
    return commit

def source_lock_payload(registration: str) -> dict[str, Any]:
    return {'family_id': FAMILY, 'family_size': 2, 'members': [c['id'] for c in CELLS],
        'registration_commit': registration, 'source_files': SOURCES,
        'key_roster_path': ROSTER, 'key_roster_sha256': ROSTER_SHA,
        'selected_values_or_null_masks_read_before_lock': False,
        'statement': 'Exact official vintages and key-only roster locked after both specifications; selected measurements remain sealed.'}

def write_lock(registration: str) -> None:
    if (ROOT / LOCK).exists():
        raise FileExistsError(LOCK)
    (ROOT / LOCK).write_bytes(js(source_lock_payload(registration)))

def lock_commit(registration: str) -> str:
    commit = first_add(LOCK)
    if commit == registration or subprocess.run(['git', 'merge-base', '--is-ancestor', registration, commit], cwd=ROOT).returncode:
        raise RuntimeError('source lock must follow registration commit')
    frozen(LOCK, commit)
    if json.loads((ROOT / LOCK).read_text()) != source_lock_payload(registration):
        raise RuntimeError('source lock differs from frozen exact pins')
    for cell in CELLS:
        if git('ls-tree', '-r', '--name-only', commit, '--', run_dir(cell)).strip():
            raise RuntimeError('source-lock commit contained result')
    return commit

def series_values(path: Path, role: str, countries: set[str], names: set[str]) -> dict[tuple[str, int], float]:
    # First selected value/status access is after registration_commit and lock_commit.
    if role == 'military':
        table = pq.read_table(path, columns=['Country', 'year', 'value']).to_pandas()
        table = table[table.Country.isin(names)]
        if table.duplicated(['Country', 'year']).any():
            raise RuntimeError('duplicate selected SIPRI value key')
        return {(str(name), int(year)): float(value) for name, year, value in zip(table.Country, table.year, table.value)}
    table = pq.read_table(path, columns=['country_iso3', 'indicator_id', 'year', 'value', 'obs_status']).to_pandas()
    table = table[(table.country_iso3.isin(countries)) & (table.indicator_id == SOURCES[role]['series_id'])]
    if table.duplicated(['country_iso3', 'year']).any():
        raise RuntimeError(f'duplicate selected WDI value key: {role}')
    bad = table.obs_status.fillna('').astype(str).map(lambda x: x not in ('', 'A'))
    table.loc[bad, 'value'] = float('nan')
    return {(str(code), int(year)): float(value) for code, year, value in zip(table.country_iso3, table.year, table.value)}

def measured_panel(paths: dict[str, Path], roster: list[tuple[str, int]], cell: dict[str, str]) -> tuple[pd.DataFrame, dict[str, Any]]:
    countries = {code for code, _ in roster}
    all_names = country_map(set(pq.read_table(paths['military'], columns=['Country']).column('Country').to_pylist()))
    inverse = {code: name for name, code in all_names.items()}
    selected_names = {inverse[code] for code in countries}
    military = series_values(paths['military'], 'military', countries, selected_names)
    outcome = series_values(paths[cell['role']], cell['role'], countries, selected_names)
    expense = series_values(paths['expense'], 'expense', countries, selected_names)
    income = series_values(paths['income'], 'income', countries, selected_names)
    rows = []
    dropped = Counter()
    for code, t in roster:
        name = inverse[code]
        values = (military.get((name, t-3), float('nan')), military.get((name, t), float('nan')),
            outcome.get((code, t-3), float('nan')), outcome.get((code, t), float('nan')),
            outcome.get((code, t+3), float('nan')), expense.get((code, t), float('nan')),
            income.get((code, t), float('nan')))
        if not all(map(math.isfinite, values)):
            dropped['missing_or_nonfinite'] += 1
            continue
        m0, m1, y0, y1, y2, fiscal, inc = values
        if not (0 <= m0 <= 20 and 0 <= m1 <= 20 and abs(m1-m0) <= 5):
            dropped['military_range'] += 1
            continue
        if not (0 <= y0 <= 20 and 0 <= y1 <= 20 and 0 <= y2 <= 20
                and abs(y1-y0) <= 5 and abs(y2-y1) <= 5):
            dropped['outcome_range'] += 1
            continue
        if not (0 <= fiscal <= 100 and inc > 0):
            dropped['control_range'] += 1
            continue
        rows.append(dict(country_iso3=code, anchor_year=t, x=m1-m0, y=y2-y1,
            prior_outcome_change=y1-y0, baseline_outcome=y1, baseline_expense=fiscal,
            log_income=math.log(inc)))
    panel = pd.DataFrame(rows, columns=['country_iso3', 'anchor_year', 'x', 'y',
        'prior_outcome_change', 'baseline_outcome', 'baseline_expense', 'log_income'])
    counts = panel.country_iso3.value_counts()
    below = panel.country_iso3.map(counts).lt(MIN_COUNTRY_ANCHORS)
    dropped['country_below_anchor_floor'] += int(below.sum())
    panel = panel.loc[~below].sort_values(['country_iso3', 'anchor_year']).reset_index(drop=True)
    material = panel.x.abs().ge(MATERIAL_CHANGE)
    gate = {'key_roster_rows': len(roster), 'key_roster_countries': KEY_COUNTRIES,
        'complete_rows_before_country_floor': len(rows), 'valid_rows': len(panel),
        'valid_countries': int(panel.country_iso3.nunique()),
        'distinct_anchors': int(panel.anchor_year.nunique()),
        'rows_per_anchor': {str(t): int((panel.anchor_year == t).sum()) for t in ANCHORS},
        'material_change_rows': int(material.sum()),
        'material_change_countries': int(panel.loc[material, 'country_iso3'].nunique()),
        'dropped': dict(sorted(dropped.items())), 'selected_values_read_after_committed_lock': True}
    return panel, gate

def form(outcome: str) -> str:
    return (f'{outcome} ~ x + prior_outcome_change + baseline_outcome + baseline_expense '
        '+ log_income + C(country_iso3) + C(anchor_year)')

def residual_form(outcome: str) -> str:
    return (f'{outcome} ~ prior_outcome_change + baseline_outcome + baseline_expense '
        '+ log_income + C(country_iso3) + C(anchor_year)')

def estimate(panel: pd.DataFrame, gate: dict[str, Any]) -> dict[str, Any]:
    failures = []
    if gate['valid_rows'] < MIN_ROWS: failures.append('min_valid_rows')
    if gate['valid_countries'] < MIN_COUNTRIES: failures.append('min_valid_countries')
    if gate['distinct_anchors'] < MIN_ANCHORS: failures.append('min_distinct_anchors')
    if gate['material_change_rows'] < MIN_MATERIAL_ROWS: failures.append('min_material_change_rows')
    if gate['material_change_countries'] < MIN_MATERIAL_COUNTRIES: failures.append('min_material_change_countries')
    if failures:
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': failures, 'verdict': 'INCONCLUSIVE'}
    rx_model = smf.ols(residual_form('x'), data=panel)
    ry_model = smf.ols(residual_form('y'), data=panel)
    if np.linalg.matrix_rank(rx_model.exog) != rx_model.exog.shape[1]: failures.append('residual_treatment_rank')
    if np.linalg.matrix_rank(ry_model.exog) != ry_model.exog.shape[1]: failures.append('residual_outcome_rank')
    if failures:
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': failures, 'verdict': 'INCONCLUSIVE'}
    rx = np.asarray(rx_model.fit().resid, dtype=float)
    ry = np.asarray(ry_model.fit().resid, dtype=float)
    ss = rx ** 2
    total = float(ss.sum())
    xsd = math.sqrt(total / len(rx)) if total > 0 else 0.0
    ysd = math.sqrt(float(np.mean(ry ** 2)))
    top_n = max(1, math.ceil(0.01 * len(rx)))
    top_share = float(sum(sorted(ss, reverse=True)[:top_n]) / total) if total > 0 else 1.0
    by_country = panel.assign(ss=ss).groupby('country_iso3').ss.sum()
    country_share = float(by_country.max() / total) if total > 0 else 1.0
    gate.update(residual_treatment_sd_pp=xsd, residual_outcome_sd_pp=ysd,
        top_one_percent_treatment_ss_share=top_share,
        top_country_treatment_ss_share=country_share)
    if xsd < MIN_RESIDUAL_X_SD: failures.append('min_residual_treatment_sd')
    if ysd < MIN_RESIDUAL_Y_SD: failures.append('min_residual_outcome_sd')
    if top_share > MAX_TOP_ONE_PERCENT_SS: failures.append('top_one_percent_treatment_concentration')
    if country_share > MAX_TOP_COUNTRY_SS: failures.append('top_country_treatment_concentration')
    if failures:
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': failures, 'verdict': 'INCONCLUSIVE'}
    model = smf.ols(form('y'), data=panel)
    if np.linalg.matrix_rank(model.exog) != model.exog.shape[1]:
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': ['primary_design_rank'], 'verdict': 'INCONCLUSIVE'}
    groups = int(panel.country_iso3.nunique())
    fit = model.fit(cov_type='cluster', cov_kwds={'groups': panel.country_iso3,
        'use_correction': True, 'df_correction': True}, use_t=True)
    beta, se = float(fit.params['x']), float(fit.bse['x'])
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0):
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': ['finite_cluster_uncertainty'], 'verdict': 'INCONCLUSIVE'}
    p = float(2 * student_t.sf(abs(beta/se), groups-1))
    crit = float(student_t.ppf(1-ALPHA_CELL/2, groups-1))
    if not (math.isfinite(p) and math.isfinite(crit)):
        return {'sample': gate, 'primary': None, 'hash_folds': [], 'gate_failures': ['finite_t_inference'], 'verdict': 'INCONCLUSIVE'}
    primary = {'beta': beta, 'country_cluster_se': se, 'p_two_sided': p,
        'confidence_level': 1-ALPHA_CELL, 'confidence_interval': [beta-crit*se, beta+crit*se],
        'n_rows': len(panel), 'n_countries': groups, 'df_inference': groups-1,
        'model_rank': int(fit.model.rank), 'model_columns': int(model.exog.shape[1]),
        'residual_treatment_sd_pp': xsd, 'residual_outcome_sd_pp': ysd,
        'top_one_percent_treatment_ss_share': top_share,
        'top_country_treatment_ss_share': country_share,
        'method': 'equal-row country/anchor FE OLS with four baseline controls; country CR1 cluster t(G-1)'}
    folds = []
    for omitted in range(5):
        subset = panel[panel.country_iso3.map(
            lambda code: int(hashlib.sha256(code.encode()).hexdigest(), 16) % 5 != omitted)]
        if len(subset) < MIN_FOLD_ROWS or subset.country_iso3.nunique() < MIN_FOLD_COUNTRIES:
            failures.append(f'fold_{omitted}_coverage')
            continue
        fold_model = smf.ols(form('y'), data=subset)
        if np.linalg.matrix_rank(fold_model.exog) != fold_model.exog.shape[1]:
            failures.append(f'fold_{omitted}_rank')
            continue
        fold_beta = float(fold_model.fit().params['x'])
        if not math.isfinite(fold_beta):
            failures.append(f'fold_{omitted}_finite')
            continue
        folds.append({'omitted_hash_fold': omitted, 'rows': len(subset),
            'countries': int(subset.country_iso3.nunique()), 'beta': fold_beta})
    if failures:
        return {'sample': gate, 'primary': primary, 'hash_folds': folds,
            'gate_failures': failures, 'verdict': 'INCONCLUSIVE'}
    negative = sum(f['beta'] < 0 for f in folds)
    positive = sum(f['beta'] > 0 for f in folds)
    verdict = ('SUPPORTED' if beta <= -MIN_ABS_BETA and p <= ALPHA_CELL and negative >= MIN_SAME_SIGN_FOLDS
        else 'REFUTED' if beta >= MIN_ABS_BETA and p <= ALPHA_CELL and positive >= MIN_SAME_SIGN_FOLDS
        else 'PARTIAL')
    return {'sample': gate, 'primary': primary, 'hash_folds': folds,
        'negative_folds': negative, 'positive_folds': positive,
        'gate_failures': [], 'verdict': verdict}

def artifacts(cell: dict[str, str], result: dict[str, Any], registration: str,
              locked: str, stamp: str) -> dict[str, bytes]:
    hid = cell['id']
    diagnostic = {'hypothesis_id': hid, 'family_id': FAMILY, 'family_size': 2,
        'registration_commit': registration, 'source_lock_commit': locked,
        'source_sha256': SOURCES['military']['sha256'],
        'secondary_source_sha256': SOURCES[cell['role']]['sha256'],
        'source_key_roster_sha256': ROSTER_SHA, 'runner': RUNNER, 'run_utc': stamp,
        'thresholds': threshold(), 'result': result, 'limitations': LIMITS, 'correction': CREDIT}
    db = js(diagnostic)
    verdict = result['verdict']
    source = {'publisher': 'SIPRI Military Expenditure Database and World Bank WDI',
        'source_sha256': SOURCES['military']['sha256'],
        'secondary_source_sha256': SOURCES[cell['role']]['sha256'],
        'source_lock_commit': locked, 'source_lock_manifest': LOCK,
        'key_roster_sha256': ROSTER_SHA,
        'input_vintages': [{'path': s['path'], 'sha256': s['sha256'], 'manifest': s['manifest'],
            'url': s['url']} for s in SOURCES.values()],
        'license': 'SIPRI terms and attribution; WDI CC BY 4.0', 'contains_source_values': False}
    manifest = {'hypothesis_id': hid, 'status': verdict, 'run_utc': stamp,
        'runner': RUNNER, 'preregistration_commit': registration, 'source': source,
        'family_id': FAMILY, 'family_size': 2, 'sample': result['sample'], 'correction': CREDIT}
    packet = {'packet_version': 1, 'hypothesis': {'id': hid, 'path': spec_path(cell)},
        'preregistration': {'commit': registration, 'steelman': steelman_path(cell),
            'source_plan': PLAN, 'key_roster': ROSTER},
        'source': source, 'family': {'id': FAMILY, 'size': 2,
            'members': [c['id'] for c in CELLS],
            'interpretation': 'Two correlated SIPRI spending-intensity extension tests; not independent replications'},
        'reproduction': {'runner': RUNNER,
            'command': f'python3 {RUNNER} verify --source-root <local-source-root>',
            'result_sha256': hashlib.sha256(db).hexdigest()},
        'result': result, 'limitations': LIMITS, 'correction': CREDIT}
    primary = result['primary']
    card = f'# Result card: {hid}\n\nVerdict: **{verdict}**. '
    card += (f"Frozen gate failures: {', '.join(result['gate_failures'])}.\n\n"
        if result['gate_failures'] else 'All frozen design gates passed.\n\n')
    card += (f'Preregistration `{registration}`; source lock `{locked}`.\n\n'
        f"Key-only roster {KEY_ROWS} / {KEY_COUNTRIES} countries; complete panel "
        f"{result['sample']['valid_rows']} / {result['sample']['valid_countries']} countries. "
        f"Material military changes {result['sample']['material_change_rows']} / "
        f"{result['sample']['material_change_countries']} countries.\n")
    if primary:
        card += (f"\nBeta={primary['beta']:+.6g} later {cell['label']}/GDP-share points per +1 prior "
            f"military/GDP-share point; country-cluster SE={primary['country_cluster_se']:.6g}; "
            f"two-sided p={primary['p_two_sided']:.6g}; 99.5% CI={primary['confidence_interval']}.\n")
    card += '\nDescriptive spending-intensity calibration only. Shared SIPRI exposure and GDP denominator. Zero causal, policy, school, position or featured credit.\n'
    beta_text = f"{primary['beta']:+.6g}" if primary else 'not estimated'
    p_text = f"{primary['p_two_sided']:.6g}" if primary else 'not estimated'
    report = (f'# SIPRI military burden and later {cell["label"]}: frozen result\n\n'
        f'Preregistration `{registration}`; source lock `{locked}`.\n\n'
        f'**{verdict}**: {result["sample"]["valid_rows"]} complete rows / '
        f'{result["sample"]["valid_countries"]} countries; beta {beta_text}; p {p_text}; '
        f'gate failures {result["gate_failures"]}.\n\n'
        'Two correlated tests use one family-wide 0.01/2 cutoff. The result is descriptive and shares '
        'the SIPRI exposure and GDP denominator with related outcomes. No causal budget-substitution claim '
        'or causal, policy, school, position or featured credit.\n')
    wrapper = ("#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n"
        "root=Path(__file__).resolve().parents[3]\n"
        f"raise SystemExit(subprocess.call([sys.executable,str(root/{RUNNER!r}),'verify',*sys.argv[1:]],cwd=root))\n")
    return {'diagnostics.json': db, 'manifest.yaml': ya(manifest),
        'evidence_packet.yaml': ya(packet), 'result_card.md': card.encode(),
        'replication.py': wrapper.encode(), 'hypothesis.yaml': (ROOT / spec_path(cell)).read_bytes(),
        'chart_data.json': js({'hypothesis_id': hid, 'family_id': FAMILY,
            'verdict': verdict, 'primary': primary}), '_report': report.encode()}

def equal_close(a: Any, b: Any, label: str) -> None:
    if isinstance(b, dict):
        if not isinstance(a, dict) or set(a) != set(b):
            raise AssertionError(f'{label}: keys differ')
        for k, v in b.items(): equal_close(a[k], v, f'{label}.{k}')
    elif isinstance(b, list):
        if not isinstance(a, list) or len(a) != len(b):
            raise AssertionError(f'{label}: list length differs')
        for i, v in enumerate(b): equal_close(a[i], v, f'{label}[{i}]')
    elif isinstance(b, float):
        if not math.isfinite(float(a)) or not math.isclose(float(a), b, rel_tol=1e-9, abs_tol=1e-11):
            raise AssertionError(f'{label}: numeric mismatch')
    elif a != b:
        raise AssertionError(f'{label}: value differs')

def write_result(results: dict[str, dict[str, Any]], registration: str, locked: str) -> None:
    if (ROOT / REPORT).exists() or any((ROOT / run_dir(c)).exists() for c in CELLS):
        raise FileExistsError('measured artifact already exists')
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    reports = []
    for cell in CELLS:
        generated = artifacts(cell, results[cell['role']], registration, locked, stamp)
        path = ROOT / run_dir(cell)
        path.mkdir(parents=True)
        for name, content in generated.items():
            if name == '_report':
                reports.append(content.decode())
            else:
                (path / name).write_bytes(content)
    (ROOT / REPORT).write_text('\n---\n\n'.join(reports))

def verify_result(results: dict[str, dict[str, Any]], registration: str, locked: str) -> None:
    reports = []
    for cell in CELLS:
        path = ROOT / run_dir(cell)
        diag = json.loads((path / 'diagnostics.json').read_text())
        expected = artifacts(cell, results[cell['role']], registration, locked, diag['run_utc'])
        for name, content in expected.items():
            if name == '_report':
                reports.append(content.decode())
                continue
            actual = path / name
            if name.endswith('.json'):
                equal_close(json.loads(actual.read_text()), json.loads(content), name)
            elif name.endswith('.yaml'):
                equal_close(yaml.safe_load(actual.read_text()), yaml.safe_load(content), name)
            elif actual.read_bytes() != content:
                raise AssertionError(f'exact replay artifact differs: {name}')
    if (ROOT / REPORT).read_text() != '\n---\n\n'.join(reports):
        raise AssertionError('exact replay report differs')

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('action', choices=['register', 'preflight', 'lock', 'measure', 'verify'])
    parser.add_argument('--source-root', type=Path, default=ROOT)
    args = parser.parse_args()
    paths = source_paths(args.source_root)
    if args.action == 'preflight':
        rows = key_roster(paths)
        print(json.dumps({'key_only_rows': len(rows), 'key_only_countries': KEY_COUNTRIES,
            'anchors': dict(Counter(t for _, t in rows)), 'selected_values_opened': False}, sort_keys=True))
        return 0
    if args.action == 'register':
        write_registration(paths)
        print('wrote two value-blind registrations; commit before source lock')
        return 0
    registration = registration_commit(paths)
    if args.action == 'lock':
        write_lock(registration)
        print('wrote exact source lock; commit separately before measure')
        return 0
    locked = lock_commit(registration)
    roster = loaded_roster(paths)
    results = {}
    for cell in CELLS:
        panel, gate = measured_panel(paths, roster, cell)
        results[cell['role']] = estimate(panel, gate)
    if args.action == 'measure':
        write_result(results, registration, locked)
        print(json.dumps({c['id']: {'verdict': results[c['role']]['verdict'],
            'gate_failures': results[c['role']]['gate_failures'],
            'sample': results[c['role']]['sample'],
            'primary': results[c['role']]['primary']} for c in CELLS}, indent=2))
    else:
        verify_result(results, registration, locked)
        print('verified exact replay', {c['id']: results[c['role']]['verdict'] for c in CELLS})
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
