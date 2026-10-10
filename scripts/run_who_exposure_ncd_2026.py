#!/usr/bin/env python3
"""Frozen, descriptive WHO exposure-to-premature-NCD-mortality family.

The registration commit contains this runner, the two specifications, steelmen,
the preregistration memo, and the source-key roster. No selected source values
are opened until a later source-lock commit pins the three raw WHO vintages.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[1]
FAMILY = 'who_exposure_premature_ncd_mortality_2026_10_10'
RUNNER = 'scripts/run_who_exposure_ncd_2026.py'
PREREG = 'engine/audits/who_exposure_ncd_prereg_2026-10-10.md'
ROSTER = 'data/pinned_evidence/who_exposure_ncd_key_roster.csv'
ROSTER_SHA = 'bb5f8791537b2c6682429f0f65eadfb221fccf03da48a9b391d767ce21542985'
LOCK = 'data/pinned_evidence/who_exposure_ncd_2026.manifest.json'
SUMMARY = 'engine/audits/who_exposure_ncd_results_2026-10-10.md'
FETCH_MANIFEST = 'data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml'
FETCH_SHA = 'e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e'
REGIONS = ('AFR', 'AMR', 'EMR', 'EUR', 'SEAR', 'WPR')
FAMILY_ALPHA = 0.01
P_MAX = FAMILY_ALPHA / 2
MAX_TOP_COUNTRY_SHARE = 0.20
MAX_TOP_REGION_SHARE = 0.45
MIN_COUNTRIES = 100
MIN_REGION_COUNTRIES = 8
MIN_MATERIAL_COUNTRIES = 30
MIN_HOLDOUT_COUNTRIES = 80
MIN_STABLE_HOLDOUTS = 5

SOURCES = {
    'smoking': {
        'series_id': 'M_Est_smk_curr_std',
        'path': 'data/vintages/who_gho/M_Est_smk_curr_std@2026-04-30T114740Z.parquet',
        'sha256': 'd4dba454e3986ca8e6c0ad49507b7e6529c0814f4776d379785f1bbe31661f8d',
        'rows': 5511,
        'dimension': 'SEX_BTSX',
        'source_url': 'https://ghoapi.azureedge.net/api/M_Est_smk_curr_std',
    },
    'mortality': {
        'series_id': 'NCDMORT3070',
        'path': 'data/vintages/who_gho/NCDMORT3070@2026-04-30T114741Z.parquet',
        'sha256': '1ae4713b1f8244ab793787b12379a0e66d14030c5c01c152828e19224ab4f7c9',
        'rows': 12936,
        'dimension': 'SEX_BTSX',
        'source_url': 'https://ghoapi.azureedge.net/api/NCDMORT3070',
    },
    'pm25': {
        'series_id': 'SDGPM25',
        'path': 'data/vintages/who_gho/SDGPM25@2026-04-30T114744Z.parquet',
        'sha256': 'c2cf89f4ab41dc8c4b6b251e7b47651edcd07d826cb45a7d5e1d8ab0ee4c6e34',
        'rows': 10750,
        'dimension': 'RESIDENCEAREATYPE_TOTL',
        'source_url': 'https://ghoapi.azureedge.net/api/SDGPM25',
    },
}
CASES = {
    'smoking': {
        'id': 'who_smoking_decline_premature_ncd_mortality_forward_2026',
        'label': 'age-standardized current tobacco-smoking prevalence decline',
        'exposure_years': (2000, 2010),
        'outcome_years': (2010, 2021),
        'bounds': (0.0, 100.0),
        'material_change': 1.0,
        'min_p90_p10_spread': 2.0,
        'meaningful_beta': 0.05,
        'exposure_unit': 'one percentage-point smoking-prevalence decline',
        'n_source_keys': 161,
    },
    'pm25': {
        'id': 'who_pm25_decline_premature_ncd_mortality_forward_2026',
        'label': 'population-total ambient PM2.5 concentration decline',
        'exposure_years': (2010, 2015),
        'outcome_years': (2015, 2021),
        'bounds': (0.0, 500.0),
        'material_change': 3.0,
        'min_p90_p10_spread': 5.0,
        'meaningful_beta': 0.03,
        'exposure_unit': 'one microgram per cubic metre PM2.5 decline',
        'n_source_keys': 184,
    },
}
CORRECTION = {
    'disposition': 'descriptive_calibration_only',
    'family_id': FAMILY, 'family_size': 2,
    'family_alpha': FAMILY_ALPHA, 'bonferroni_p_max': P_MAX,
    'causal_credit': 0, 'school_score_eligible': False,
    'school_score_credit': 0, 'policy_score_eligible': False,
    'policy_score_credit': 0, 'featured_eligible': False,
}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def first_addition(path: str) -> str:
    commits = git('log', '--diff-filter=A', '--format=%H', 'HEAD', '--', path).decode().splitlines()
    if not commits:
        raise RuntimeError(f'no first-addition commit for {path}')
    return commits[-1]


def frozen(path: str, commit: str) -> None:
    p = ROOT / path
    if not p.exists() or p.read_bytes() != git('show', f'{commit}:{path}'):
        raise RuntimeError(f'frozen bytes differ: {path}')
    if git('status', '--porcelain', '--', path).strip():
        raise RuntimeError(f'uncommitted frozen file: {path}')


def ancestor(before: str, after: str) -> bool:
    return before != after and subprocess.run(
        ['git', 'merge-base', '--is-ancestor', before, after], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def spec_path(case: dict) -> str:
    return f"hypotheses/healthcare/{case['id']}.yaml"


def steelman_path(case: dict) -> str:
    return f"hypotheses/steelman/{case['id']}.md"


def run_path(case: dict) -> str:
    return f"engine/runs/{case['id']}"


def threshold(case: dict) -> dict:
    return {
        'family_id': FAMILY, 'family_size': 2,
        'family_alpha': FAMILY_ALPHA, 'p_max_two_sided_bonferroni': P_MAX,
        'meaningful_beta_min_abs': case['meaningful_beta'],
        'min_complete_countries': MIN_COUNTRIES,
        'min_countries_each_who_region': MIN_REGION_COUNTRIES,
        'min_material_countries': MIN_MATERIAL_COUNTRIES,
        'material_abs_exposure_change': case['material_change'],
        'min_exposure_p90_p10_spread': case['min_p90_p10_spread'],
        'max_top_country_residualized_exposure_share': MAX_TOP_COUNTRY_SHARE,
        'max_top_region_residualized_exposure_share': MAX_TOP_REGION_SHARE,
        'min_leave_one_region_out_countries': MIN_HOLDOUT_COUNTRIES,
        'min_concordant_holdouts_for_directional_verdict': MIN_STABLE_HOLDOUTS,
        'roster_sha256': ROSTER_SHA, 'source_lock_path': LOCK,
        'causal_credit': 0, 'school_score_eligible': False,
        'school_score_credit': 0, 'policy_score_eligible': False,
        'policy_score_credit': 0, 'featured_eligible': False,
    }


def registration_commit() -> str:
    paths = [RUNNER, PREREG, ROSTER]
    for case in CASES.values():
        paths.extend([spec_path(case), steelman_path(case)])
    commits = {first_addition(path) for path in paths}
    if len(commits) != 1:
        raise RuntimeError('registration files do not share one first-addition commit')
    commit = commits.pop()
    for path in paths:
        frozen(path, commit)
    if digest(ROOT / ROSTER) != ROSTER_SHA:
        raise RuntimeError('source-key roster hash mismatch')
    rows = list(csv.DictReader((ROOT / ROSTER).open(newline='')))
    counts = Counter(row['case'] for row in rows)
    if len(rows) != 345 or counts != Counter({k: v['n_source_keys'] for k, v in CASES.items()}):
        raise RuntimeError('source-key roster count mismatch')
    if len({(r['case'], r['country_iso3']) for r in rows}) != len(rows):
        raise RuntimeError('source-key roster duplicate')
    if rows != sorted(rows, key=lambda r: (list(CASES).index(r['case']), r['country_iso3'])):
        raise RuntimeError('source-key roster sort mismatch')
    for key, case in CASES.items():
        spec = yaml.safe_load((ROOT / spec_path(case)).read_text())
        if (spec.get('hypothesis_id') != case['id']
                or spec.get('status') != 'pre_registered'
                or spec.get('evidence_type') != 'descriptive'
                or spec.get('falsification', {}).get('threshold') != threshold(case)
                or spec.get('covers_claims') != []
                or spec.get('linked_hypotheses') != []):
            raise RuntimeError(f'registered specification mismatch: {key}')
        if git('ls-tree', '-r', '--name-only', commit, '--', run_path(case)).strip():
            raise RuntimeError('run entered the registration commit')
    if git('ls-tree', '-r', '--name-only', commit, '--', LOCK).strip():
        raise RuntimeError('source lock entered the registration commit')
    return commit


def source_manifest_entries() -> dict:
    if digest(ROOT / FETCH_MANIFEST) != FETCH_SHA:
        raise RuntimeError('fetch manifest hash mismatch')
    doc = yaml.safe_load((ROOT / FETCH_MANIFEST).read_text())
    entries = doc.get('entries', [])
    found = {}
    for role, src in SOURCES.items():
        matches = [entry for entry in entries
                   if entry.get('publisher') == 'who_gho'
                   and entry.get('series_id') == src['series_id']
                   and entry.get('parquet_path') == src['path']]
        if len(matches) != 1:
            raise RuntimeError(f'fetch manifest entry missing or duplicate: {role}')
        entry = matches[0]
        if (entry.get('sha256') != src['sha256'] or entry.get('rows') != src['rows']
                or entry.get('license') != 'CC-BY-NC-SA-3.0 IGO'):
            raise RuntimeError(f'fetch manifest metadata mismatch: {role}')
        found[role] = {k: entry.get(k) for k in ('publisher', 'series_id', 'parquet_path', 'sha256', 'rows', 'license', 'fetch_utc', 'source_url', 'methodology_url')}
    return found


def expected_lock(reg: str) -> dict:
    return {
        'schema': 'ieset-who-exposure-ncd-source-lock-v1',
        'registration_commit': reg,
        'roster_sha256': ROSTER_SHA,
        'runner_sha256': digest(ROOT / RUNNER),
        'fetch_manifest': FETCH_MANIFEST,
        'fetch_manifest_sha256': FETCH_SHA,
        'sources': source_manifest_entries(),
        'license_hold': 'WHO raw files carry CC-BY-NC-SA-3.0 IGO; review redistribution and attribution before publication.',
    }


def lock_commit(reg: str) -> tuple[str, dict]:
    paths = [LOCK] + [src['path'] for src in SOURCES.values()]
    commits = {first_addition(path) for path in paths}
    if len(commits) != 1:
        raise RuntimeError('all raw WHO files and source lock must first appear together')
    commit = commits.pop()
    if not ancestor(reg, commit):
        raise RuntimeError('source lock must strictly follow registration')
    for path in paths:
        frozen(path, commit)
    expected = expected_lock(reg)
    actual = json.loads((ROOT / LOCK).read_text())
    if actual != expected:
        raise RuntimeError('source lock metadata differs from registered sources')
    for role, src in SOURCES.items():
        if digest(ROOT / src['path']) != src['sha256']:
            raise RuntimeError(f'raw source hash mismatch: {role}')
    return commit, actual


def read_source(role: str) -> dict[tuple[str, int], float | None]:
    src = SOURCES[role]
    table = pd.read_parquet(ROOT / src['path'])
    if len(table) != src['rows']:
        raise RuntimeError(f'raw row count mismatch: {role}')
    rows = table[(table['SpatialDimType'] == 'COUNTRY')
                 & (table['Dim1'] == src['dimension'])
                 & (table['ParentLocationCode'].isin(REGIONS))]
    if role == 'mortality':
        rows = rows[rows['Dim2'] == 'AGEGROUP_YEARS30-69']
    values = {}
    for row in rows.itertuples(index=False):
        key = (row.country_iso3, int(row.year))
        if key in values:
            raise RuntimeError(f'duplicate country-year in {role}: {key}')
        try:
            value = float(row.value)
        except (TypeError, ValueError):
            value = float('nan')
        values[key] = value if math.isfinite(value) else None
    return values


def build_frame(key: str, sources: dict) -> tuple[pd.DataFrame, Counter]:
    case = CASES[key]
    rows = list(csv.DictReader((ROOT / ROSTER).open(newline='')))
    selected = [r for r in rows if r['case'] == key]
    records = []
    removed = Counter()
    for r in selected:
        c = r['country_iso3']
        ex0, ex1 = case['exposure_years']
        y0, y1 = case['outcome_years']
        exposure_start = sources[key].get((c, ex0))
        exposure_end = sources[key].get((c, ex1))
        mortality_start = sources['mortality'].get((c, y0))
        mortality_end = sources['mortality'].get((c, y1))
        if any(v is None for v in (exposure_start, exposure_end, mortality_start, mortality_end)):
            removed['missing_or_nonfinite'] += 1
            continue
        lo, hi = case['bounds']
        if (not lo <= exposure_start <= hi or not lo <= exposure_end <= hi
                or not 0 <= mortality_start <= 100 or not 0 <= mortality_end <= 100):
            removed['outside_frozen_measurement_bounds'] += 1
            continue
        records.append({
            'country_iso3': c, 'who_region': r['who_region'],
            'exposure_start': exposure_start, 'exposure_end': exposure_end,
            'baseline_exposure': exposure_start,
            'exposure_improvement': exposure_start - exposure_end,
            'baseline_mortality': mortality_start,
            'mortality_2021': mortality_end,
            'mortality_improvement': mortality_start - mortality_end,
        })
    return pd.DataFrame(records), removed


def design(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    x = frame['exposure_improvement'].to_numpy(dtype=float)
    y = frame['mortality_improvement'].to_numpy(dtype=float)
    regions = sorted(frame['who_region'].unique())
    dummies = pd.get_dummies(pd.Categorical(frame['who_region'], categories=regions), drop_first=True).to_numpy(dtype=float)
    base = np.column_stack([
        np.ones(len(frame)),
        frame['baseline_mortality'].to_numpy(dtype=float),
        frame['baseline_exposure'].to_numpy(dtype=float),
        dummies,
    ])
    full = np.column_stack([base[:, 0], x, base[:, 1:]])
    return full, base, y


def fit(frame: pd.DataFrame) -> tuple[dict, np.ndarray] | None:
    if len(frame) < 20:
        return None
    full, base, y = design(frame)
    if np.linalg.matrix_rank(full) != full.shape[1]:
        return None
    model = sm.OLS(y, full).fit(cov_type='HC3', use_t=True)
    beta, se, p = map(float, (model.params[1], model.bse[1], model.pvalues[1]))
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0 and math.isfinite(p)):
        return None
    residual_exposure = full[:, 1] - base @ np.linalg.lstsq(base, full[:, 1], rcond=None)[0]
    squares = residual_exposure ** 2
    total = float(squares.sum())
    if not total > 1e-10:
        return None
    region_shares = {
        region: float(squares[frame['who_region'].to_numpy() == region].sum() / total)
        for region in REGIONS
    }
    ci = model.conf_int(alpha=P_MAX)[1]
    return ({
        'beta': beta, 'standard_error_hc3': se, 'p_two_sided': p,
        'df_resid': int(model.df_resid),
        'familywise_ci_99_5': [float(ci[0]), float(ci[1])],
        'max_country_residualized_exposure_share': float(squares.max() / total),
        'max_region_residualized_exposure_share': max(region_shares.values()),
        'region_residualized_exposure_shares': region_shares,
    }, residual_exposure)


def analyse(key: str, sources: dict) -> tuple[dict, pd.DataFrame]:
    case = CASES[key]
    frame, removed = build_frame(key, sources)
    gates = []
    n = len(frame)
    region_counts = Counter(frame['who_region']) if n else Counter()
    if n < MIN_COUNTRIES:
        gates.append('min_complete_countries')
    if any(region_counts[r] < MIN_REGION_COUNTRIES for r in REGIONS):
        gates.append('min_countries_each_who_region')
    material = int((frame['exposure_improvement'].abs() >= case['material_change']).sum()) if n else 0
    if material < MIN_MATERIAL_COUNTRIES:
        gates.append('min_material_exposure_countries')
    spread = (float(np.percentile(frame['exposure_improvement'], 90)
                    - np.percentile(frame['exposure_improvement'], 10)) if n else None)
    if spread is None or spread < case['min_p90_p10_spread']:
        gates.append('min_exposure_p90_p10_spread')
    primary = fit(frame)
    if primary is None:
        gates.append('full_rank_positive_hc3_uncertainty_and_exposure_variance')
    holdouts = {}
    for region in REGIONS:
        subset = frame[frame['who_region'] != region]
        if len(subset) < MIN_HOLDOUT_COUNTRIES:
            gates.append(f'holdout_min_countries_excluding_{region}')
            holdouts[region] = {'countries': len(subset), 'beta': None}
            continue
        fitted = fit(subset)
        if fitted is None:
            gates.append(f'holdout_fit_excluding_{region}')
            holdouts[region] = {'countries': len(subset), 'beta': None}
            continue
        holdouts[region] = {'countries': len(subset), 'beta': fitted[0]['beta']}
    estimate = primary[0] if primary else None
    if estimate:
        if estimate['max_country_residualized_exposure_share'] > MAX_TOP_COUNTRY_SHARE:
            gates.append('max_top_country_residualized_exposure_share')
        if estimate['max_region_residualized_exposure_share'] > MAX_TOP_REGION_SHARE:
            gates.append('max_top_region_residualized_exposure_share')
    stable_positive = sum(v['beta'] is not None and v['beta'] > 0 for v in holdouts.values())
    stable_negative = sum(v['beta'] is not None and v['beta'] < 0 for v in holdouts.values())
    if gates:
        verdict = 'INCONCLUSIVE'
    elif (estimate['beta'] >= case['meaningful_beta'] and estimate['p_two_sided'] <= P_MAX
          and stable_positive >= MIN_STABLE_HOLDOUTS):
        verdict = 'SUPPORTED'
    elif (estimate['beta'] <= -case['meaningful_beta'] and estimate['p_two_sided'] <= P_MAX
          and stable_negative >= MIN_STABLE_HOLDOUTS):
        verdict = 'REFUTED'
    else:
        verdict = 'PARTIAL'
    result = {
        'case': key, 'design_id': case['id'], 'family_id': FAMILY,
        'verdict': verdict, 'analysis_scope': 'descriptive_only',
        'source_key_countries': case['n_source_keys'], 'complete_countries': n,
        'excluded_reasons': dict(sorted(removed.items())),
        'who_region_counts': {r: region_counts[r] for r in REGIONS},
        'material_exposure_countries': material,
        'exposure_p90_p10_spread': spread,
        'estimate': estimate, 'leave_one_who_region_out': holdouts,
        'positive_holdout_signs': stable_positive,
        'negative_holdout_signs': stable_negative,
        'failed_gates': sorted(set(gates)),
        'correction': CORRECTION,
        'notes': 'WHO smoking and NCD series are modelled; 2021 NCD estimates require WHO pandemic caution. Neither time ordering nor region controls identify a causal exposure effect.',
    }
    return result, frame


def dump_json(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def dump_yaml(value: object) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()


def parquet_bytes(rows: list[dict], columns: list[str]) -> bytes:
    df = pd.DataFrame(rows, columns=columns)
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False, engine='pyarrow')
    return buffer.getvalue()


def artifact_bytes(key: str, result: dict, frame: pd.DataFrame, reg: str, lock: str) -> dict[str, bytes]:
    case = CASES[key]
    folder = run_path(case)
    estimate = result['estimate'] or {}
    beta = estimate.get('beta')
    p = estimate.get('p_two_sided')
    lines = [
        f"# {case['label']} and later premature NCD mortality",
        '', f"**Verdict: {result['verdict']}** (descriptive calibration; no causal, policy, school, position, or featured credit).",
        '', f"Source-key countries: {result['source_key_countries']}; complete cases: {result['complete_countries']}.",
        f"Exposure variation p90−p10: {result['exposure_p90_p10_spread']}; material exposure countries: {result['material_exposure_countries']}.",
        f"HC3 adjusted slope: {beta} percentage-point mortality improvement per {case['exposure_unit']}; two-sided p: {p}; family Bonferroni cutoff: {P_MAX}.",
        f"Frozen gate failures: {', '.join(result['failed_gates']) if result['failed_gates'] else 'none'}.",
        f"Leave-one-WHO-region-out positive slopes: {result['positive_holdout_signs']}/6; negative slopes: {result['negative_holdout_signs']}/6.",
        '', 'This is a cross-country association using WHO modelled estimates. Region controls, baseline levels, and forward timing do not remove common causes or measurement error.',
        'The 2021 mortality estimate may be underestimated where death registration was weak during the COVID-19 period. Smoking is age-standardized while mortality is a probability for ages 30–70; PM2.5 uses the total-residence category.',
        'The two tests share the mortality source and overlapping countries, so they are one family with fixed 0.01/2 multiplicity. Broader archive selection is not controlled.',
        '', f"Frozen registration: `{reg}`. Source lock: `{lock}`. Exact replay: `python3 -B {RUNNER} --verify`.",
    ]
    card = ('\n'.join(lines) + '\n').encode()
    manifest = {
        'design_id': case['id'], 'family_id': FAMILY, 'evidence_type': 'descriptive',
        'verdict': result['verdict'], 'spec_commit': reg, 'lock_commit': lock,
        'runner_sha256': digest(ROOT / RUNNER),
        'source_custody': {role: source_manifest_entries()[role] for role in ([key, 'mortality'])},
        'credit': {'causal': 0, 'policy': 0, 'school': 0, 'position': 0, 'featured': 0},
        'artifacts': ['hypothesis.yaml', 'manifest.yaml', 'diagnostics.json', 'coefficients.parquet', 'metric_results.parquet', 'chart_data.json', 'result_card.md', 'replication.py', 'evidence_packet.yaml'],
    }
    packet = {
        'design_id': case['id'], 'verdict': result['verdict'],
        'evidence_type': 'descriptive', 'causal_claim': False,
        'source_hashes_verified': True, 'strict_spec_lock_chronology_verified': True,
        'policy_effect_credit': False, 'school_claim_links': [],
        'correction': CORRECTION,
        'interpretation': f"Later premature NCD mortality association with {case['label']}; no identified exposure or policy effect.",
    }
    coeff = [{
        'term': 'exposure_improvement', 'coefficient': beta,
        'standard_error_hc3': estimate.get('standard_error_hc3'),
        'p_two_sided': p, 'verdict': result['verdict'],
    }]
    metrics = [{
        'metric': 'premature_ncd_mortality_probability_improvement_pp',
        'value': beta, 'p_value': p, 'verdict': result['verdict'],
        'complete_countries': result['complete_countries'],
    }]
    region_plot = []
    if len(frame):
        for region in REGIONS:
            subset = frame[frame['who_region'] == region]
            if len(subset):
                region_plot.append({
                    'who_region': region, 'countries': len(subset),
                    'mean_exposure_improvement': float(subset['exposure_improvement'].mean()),
                    'mean_mortality_improvement': float(subset['mortality_improvement'].mean()),
                })
    replication = f"#!/usr/bin/env python3\nimport subprocess\nimport sys\nfrom pathlib import Path\nroot = Path(__file__).resolve().parents[3]\nraise SystemExit(subprocess.call([sys.executable, '-B', str(root / '{RUNNER}'), '--verify']))\n".encode()
    return {
        f'{folder}/hypothesis.yaml': (ROOT / spec_path(case)).read_bytes(),
        f'{folder}/manifest.yaml': dump_yaml(manifest),
        f'{folder}/diagnostics.json': dump_json(result),
        f'{folder}/coefficients.parquet': parquet_bytes(coeff, ['term', 'coefficient', 'standard_error_hc3', 'p_two_sided', 'verdict']),
        f'{folder}/metric_results.parquet': parquet_bytes(metrics, ['metric', 'value', 'p_value', 'verdict', 'complete_countries']),
        f'{folder}/chart_data.json': dump_json({'design_id': case['id'], 'who_region_summaries': region_plot, 'individual_country_values_published': False}),
        f'{folder}/result_card.md': card,
        f'{folder}/replication.py': replication,
        f'{folder}/evidence_packet.yaml': dump_yaml(packet),
    }


def summary_bytes(results: dict, reg: str, lock: str) -> bytes:
    lines = [
        '# WHO exposure changes and later premature NCD mortality — locked results',
        '', f'Registration `{reg}` strictly preceded source lock `{lock}` and all measured runs.',
        'Three original WHO source files were SHA-256 checked against the tracked bootstrap fetch manifest. Their license is CC-BY-NC-SA-3.0 IGO; redistribution needs review before publishing.',
        'This is one two-test descriptive family, two-sided family alpha 0.01, Bonferroni cutoff 0.005. Both tests remain in the denominator.',
        '', '| Comparison | Source-key countries | Complete | HC3 slope | Two-sided p | Region holdout signs | Gate failures | Verdict |',
        '| --- | ---: | ---: | ---: | ---: | --- | --- | --- |',
    ]
    for key, result in results.items():
        estimate = result['estimate'] or {}
        signs = f"+{result['positive_holdout_signs']}/6, -{result['negative_holdout_signs']}/6"
        lines.append(f"| {key} | {result['source_key_countries']} | {result['complete_countries']} | {estimate.get('beta')} | {estimate.get('p_two_sided')} | {signs} | {', '.join(result['failed_gates']) or 'none'} | **{result['verdict']}** |")
    lines += [
        '', 'Positive exposure and mortality changes both mean a decline. The slope is a percentage-point change in the mortality probability per one-unit exposure decline, adjusting for baseline exposure, baseline mortality, and WHO region.',
        'The smoking series is modelled age-standardized prevalence for both sexes; PM2.5 uses the total-residence category. WHO NCD mortality is a modelled probability for dying between ages 30 and 70 from four major disease groups. WHO cautions that 2020–2021 estimates can undercount pandemic-related NCD deaths where vital registration is weak.',
        'No policy effect, exposure causal effect, school claim, position score, or featured status follows from either result. The two tests share countries and the mortality series; archive-wide selection is unadjusted.',
        '', 'Definitions: [WHO tobacco prevalence](https://www.who.int/data/gho/data/themes/topics/sdg-target-3_a-tobacco-control), [WHO NCD mortality](https://www.who.int/data/gho/data/indicators/indicator-details/GHO/probability-of-dying-between-exact-ages-30-and-70-from-any-of-cardiovascular-disease-cancer-diabetes-or-chronic-respiratory-%28-%29/), [WHO PM2.5](https://data.who.int/indicators/i/87345F3/F810947).',
        '', f'Exact replay: `python3 -B {RUNNER} --verify`.',
    ]
    return ('\n'.join(lines) + '\n').encode()


def reproduce(write: bool) -> None:
    reg = registration_commit()
    locked, _ = lock_commit(reg)
    sources = {role: read_source(role) for role in SOURCES}
    results = {}
    artifacts = {}
    for key in CASES:
        result, frame = analyse(key, sources)
        results[key] = result
        artifacts.update(artifact_bytes(key, result, frame, reg, locked))
    artifacts[SUMMARY] = summary_bytes(results, reg, locked)
    if write:
        for rel, payload in artifacts.items():
            path = ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
    else:
        for rel, payload in artifacts.items():
            path = ROOT / rel
            if not path.is_file() or path.read_bytes() != payload:
                raise RuntimeError(f'exact replay mismatch: {rel}')
    for key, result in results.items():
        estimate = result['estimate'] or {}
        print(key, result['verdict'], result['complete_countries'], estimate.get('beta'), estimate.get('p_two_sided'), result['failed_gates'])
    print('exact replay passed' if not write else 'frozen run artifacts written')


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--make-lock', action='store_true')
    group.add_argument('--run', action='store_true')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.make_lock:
        reg = registration_commit()
        for role, src in SOURCES.items():
            if digest(ROOT / src['path']) != src['sha256']:
                raise RuntimeError(f'raw source hash mismatch: {role}')
        data = expected_lock(reg)
        path = ROOT / LOCK
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(dump_json(data))
        print('source lock written; commit it with raw files before reading selected values')
        return 0
    reproduce(write=args.run)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
