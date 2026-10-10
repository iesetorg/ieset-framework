#!/usr/bin/env python3
"""Exact source-locked replay for the protected-land forest and food family."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pycountry
import statsmodels.api as sm
import yaml
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
FAMILY = 'wdi_protected_land_forward_forest_food_2026_family'
IDS = ('wdi_protected_land_2005_2015_forward_forest_cover_v2',
       'wdi_protected_land_2005_2015_forward_food_per_person_v2')
SPEC = {hid: f'hypotheses/energy/{hid}.yaml' for hid in IDS}
REGISTRATION = '4e9f3eb637bb4f97f4fc7c12201df39f4bffaa47'
SOURCE_LOCK = 'c736d28fafd3eb6961576b936cee6bef32d0ac01'
LOCK_REL = f'prereg/locks/{FAMILY}.json'
RUNNER_REL = f'scripts/run_{FAMILY}.py'
ARTIFACTS = ('hypothesis.yaml', 'manifest.yaml', 'diagnostics.json',
             'coefficients.parquet', 'chart_data.json', 'result_card.md',
             'replication.py', 'evidence_packet.yaml', 'metric_results.parquet')
SOURCE_ROLES = ('protected', 'forest', 'food', 'population', 'income', 'yield')
CONTROLS = {
    'forest': ('protected_2005', 'log_income_2015', 'forest_2015', 'prior_forest_share_trend'),
    'food': ('protected_2005', 'log_income_2015', 'log_food_index_2015',
             'log_population_2015', 'prior_food_per_person_growth'),
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def first_add(path: str) -> str:
    lines = git('log', '--diff-filter=A', '--format=%H', '--', path).splitlines()
    if not lines:
        raise ValueError(f'Missing first-add commit: {path}')
    return lines[-1]


def frozen(path: str, commit: str) -> None:
    working = (ROOT / path).read_bytes()
    registered = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)
    head = subprocess.check_output(['git', 'show', f'HEAD:{path}'], cwd=ROOT)
    if working != registered or working != head:
        raise ValueError(f'Frozen file changed: {path}')


def source_keys(source_root: Path, role: str, ref: dict) -> list[tuple[str, int]]:
    path = source_root / ref['path']
    if role == 'yield':
        table = pq.read_table(path, columns=['Area Code (M49)', 'Item Code',
                                            'Element Code', 'Year', 'Unit'],
                              filters=[('Item Code', '=', 1717), ('Element Code', '=', 5412),
                                       ('Year', 'in', [1995, 2005])])
        m49 = {str(c.numeric).zfill(3): c.alpha_3 for c in pycountry.countries
               if hasattr(c, 'numeric')}
        keys = []
        for row in table.to_pylist():
            if row['Unit'] != 'kg/ha' or row['Year'] not in ref['required_years']:
                continue
            code = str(row['Area Code (M49)']).lstrip("'").zfill(3)
            country = m49.get(code)
            if country:
                keys.append((country, int(row['Year'])))
    else:
        table = pq.read_table(path, columns=['country_iso3', 'year'])
        keys = [(row['country_iso3'], int(row['year'])) for row in table.to_pylist()
                if row['year'] in ref['required_years']]
    return keys


def verify(source_root: Path) -> tuple[dict, dict]:
    if subprocess.run(['git', 'merge-base', '--is-ancestor', REGISTRATION, SOURCE_LOCK],
                      cwd=ROOT).returncode:
        raise ValueError('Registration is not an ancestor of source lock')
    if subprocess.run(['git', 'merge-base', '--is-ancestor', SOURCE_LOCK, 'HEAD'],
                      cwd=ROOT).returncode:
        raise ValueError('Source lock is not an ancestor of HEAD')
    for path in SPEC.values():
        if first_add(path) != REGISTRATION:
            raise ValueError(f'Invalid spec chronology: {path}')
        frozen(path, REGISTRATION)
    if first_add(LOCK_REL) != SOURCE_LOCK:
        raise ValueError('Invalid source-lock chronology')
    frozen(LOCK_REL, SOURCE_LOCK)
    runner_commit = first_add(RUNNER_REL)
    if subprocess.run(['git', 'merge-base', '--is-ancestor', SOURCE_LOCK, runner_commit],
                      cwd=ROOT).returncode:
        raise ValueError('Runner was not committed after source lock')
    frozen(RUNNER_REL, runner_commit)
    lock = json.loads((ROOT / LOCK_REL).read_text())
    specs = {hid: yaml.safe_load((ROOT / SPEC[hid]).read_text()) for hid in IDS}
    if (lock['family_id'] != FAMILY or lock['registration_commit'] != REGISTRATION
            or lock['hypothesis_ids'] != list(IDS) or lock['family_size'] != 2
            or lock['selected_values_read'] is not False):
        raise ValueError('Family lock mismatch')
    roster = lock['country_roster']
    roster_sha = hashlib.sha256(''.join(f'{c}\n' for c in roster).encode()).hexdigest()
    if roster != sorted(roster) or len(roster) != 172 or roster_sha != lock['country_roster_sha256']:
        raise ValueError('Frozen country roster mismatch')
    if set(lock['source_files']) != set(SOURCE_ROLES):
        raise ValueError('Frozen source roles mismatch')
    for hid, spec in specs.items():
        th = spec['falsification']['threshold']
        if (spec['hypothesis_id'] != hid or spec['status'] != 'pre_registered'
                or th['family_id'] != FAMILY or th['family_size'] != 2
                or th['prior_yield_years'] != [1995, 2005]
                or th['treatment_years'] != [2005, 2015]
                or th['outcome_years'] != [2015, 2023]):
            raise ValueError(f'Frozen specification mismatch: {hid}')
        for role, ref in th['source_files'].items():
            item = lock['source_files'][role]
            if ref['path'] != item['path'] or ref['sha256'] != item['sha256']:
                raise ValueError(f'Frozen source mismatch: {role}')
    roster_set = set(roster)
    for role, ref in lock['source_files'].items():
        path = source_root / ref['path']
        if not path.is_file() or sha(path) != ref['sha256']:
            raise ValueError(f'Source bytes unavailable or changed: {role}')
        keys = sorted((c, y) for c, y in source_keys(source_root, role, ref)
                      if c in roster_set)
        if len(keys) != len(set(keys)):
            raise ValueError(f'Duplicate selected source keys: {role}')
        digest = hashlib.sha256(''.join(f'{c},{y}\n' for c, y in keys).encode()).hexdigest()
        if len(keys) != ref['selected_key_count'] or digest != ref['selected_key_sha256']:
            raise ValueError(f'Selected source keys changed: {role}')
    return lock, specs


def finite(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def selected_values(source_root: Path, lock: dict) -> dict:
    values = {}
    roster = set(lock['country_roster'])
    for role, ref in lock['source_files'].items():
        path = source_root / ref['path']
        selected = {}
        if role == 'yield':
            table = pq.read_table(path, columns=['Area Code (M49)', 'Item Code',
                                                 'Element Code', 'Year', 'Unit', 'Value'],
                                  filters=[('Item Code', '=', 1717), ('Element Code', '=', 5412),
                                           ('Year', 'in', [1995, 2005])])
            m49 = {str(c.numeric).zfill(3): c.alpha_3 for c in pycountry.countries
                   if hasattr(c, 'numeric')}
            for row in table.to_pylist():
                if row['Unit'] != 'kg/ha':
                    continue
                country = m49.get(str(row['Area Code (M49)']).lstrip("'").zfill(3))
                key = (country, int(row['Year']))
                if country in roster and key[1] in ref['required_years']:
                    if key in selected:
                        raise ValueError(f'Duplicate selected value: {role} {key}')
                    selected[key] = row['Value']
        else:
            table = pq.read_table(path, columns=['country_iso3', 'year', 'value'])
            for row in table.to_pylist():
                key = (row['country_iso3'], int(row['year']))
                if key[0] in roster and key[1] in ref['required_years']:
                    if key in selected:
                        raise ValueError(f'Duplicate selected value: {role} {key}')
                    selected[key] = row['value']
        values[role] = selected
    return values


def panel_for(lock: dict, values: dict, threshold: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    reasons = {'yield_missing_or_invalid': 0, 'yield_below_prior_condition': 0,
               'protected_missing_or_invalid': 0, 'forest_missing_or_invalid': 0,
               'food_missing_or_invalid': 0, 'population_missing_or_invalid': 0,
               'income_missing_or_invalid': 0}
    for country in lock['country_roster']:
        y95, y05 = (finite(values['yield'].get((country, year))) for year in (1995, 2005))
        p05, p15 = (finite(values['protected'].get((country, year))) for year in (2005, 2015))
        f05, f15, f23 = (finite(values['forest'].get((country, year)))
                          for year in (2005, 2015, 2023))
        q05, q15, q23 = (finite(values['food'].get((country, year)))
                          for year in (2005, 2015, 2023))
        n05, n15, n23 = (finite(values['population'].get((country, year)))
                          for year in (2005, 2015, 2023))
        g15 = finite(values['income'].get((country, 2015)))
        bad_yield = y95 is None or y05 is None or y95 <= 0 or y05 <= 0
        prior_yield = 100 * (math.log(y05) - math.log(y95)) / 10 if not bad_yield else None
        below_yield = not bad_yield and prior_yield < threshold['min_prior_yield_growth_annual_log_pp']
        bad_protected = any(v is None or not 0 <= v <= 100 for v in (p05, p15))
        bad_forest = any(v is None or not 0 <= v <= 100 for v in (f05, f15, f23))
        bad_food = any(v is None or v <= 0 for v in (q05, q15, q23))
        bad_population = any(v is None or v <= 0 for v in (n05, n15, n23))
        bad_income = g15 is None or g15 <= 0
        for key, bad in [('yield_missing_or_invalid', bad_yield),
                         ('yield_below_prior_condition', below_yield),
                         ('protected_missing_or_invalid', bad_protected),
                         ('forest_missing_or_invalid', bad_forest),
                         ('food_missing_or_invalid', bad_food),
                         ('population_missing_or_invalid', bad_population),
                         ('income_missing_or_invalid', bad_income)]:
            if bad:
                reasons[key] += 1
        if any((bad_yield, below_yield, bad_protected, bad_forest,
                bad_food, bad_population, bad_income)):
            continue
        rows.append({
            'country_iso3': country, 'prior_cereal_yield_growth': prior_yield,
            'protected_gain_pp': p15 - p05, 'protected_gain_5pp': (p15 - p05) / 5,
            'protected_2005': p05, 'log_income_2015': math.log(g15),
            'forest_2015': f15, 'prior_forest_share_trend': (f15 - f05) / 10,
            'forest_outcome': (f23 - f15) / 8,
            'log_food_index_2015': math.log(q15), 'log_population_2015': math.log(n15),
            'prior_food_per_person_growth': 100 * ((math.log(q15) - math.log(q05))
                                                   - (math.log(n15) - math.log(n05))) / 10,
            'food_outcome': 100 * ((math.log(q23) - math.log(q15))
                                   - (math.log(n23) - math.log(n15))) / 8,
        })
    panel = pd.DataFrame(rows)
    diag = {'candidate_economies': len(lock['country_roster']),
            'shared_complete_economies': len(rows),
            'excluded_by_reason_overlapping': reasons,
            'source_values_read_after_registration_and_lock': True}
    return panel, diag


def fit(panel: pd.DataFrame, role: str, threshold: dict) -> dict:
    controls = CONTROLS[role]
    x = np.column_stack([np.ones(len(panel)), panel['protected_gain_5pp'].to_numpy(float)] +
                        [panel[name].to_numpy(float) for name in controls])
    y = panel[f'{role}_outcome'].to_numpy(float)
    n, k = x.shape
    if n <= k or np.linalg.matrix_rank(x) != k:
        raise ValueError('Full-rank model unavailable')
    result = sm.OLS(y, x).fit(cov_type='HC3')
    beta, se = float(result.params[1]), float(result.bse[1])
    df = n - k
    covars = x[:, [0, *range(2, k)]]
    residual = x[:, 1] - covars @ np.linalg.lstsq(covars, x[:, 1], rcond=None)[0]
    squared = residual ** 2
    if not all(math.isfinite(v) for v in (beta, se)) or se <= 0 or squared.sum() <= 1e-12:
        raise ValueError('Finite HC3 estimate or identified exposure unavailable')
    estimate = {'coefficient': beta, 'standard_error': se, 'reference_df': df,
                'covariance': 'HC3',
                'max_single_economy_residualized_exposure_share': float(squared.max() / squared.sum())}
    if role == 'forest':
        estimate['p_value'] = float(2 * student_t.sf(abs(beta / se), df=df))
    else:
        margin = threshold['noninferiority_margin_annual_log_pp_per_5pp']
        critical = float(student_t.ppf(1 - threshold['one_sided_alpha'], df=df))
        estimate.update({'p_value': float(student_t.sf((beta + margin) / se, df=df)),
                         'noninferiority_p_value': float(student_t.sf((beta + margin) / se, df=df)),
                         'material_harm_p_value': float(student_t.cdf((beta + margin) / se, df=df)),
                         'one_sided_lower_bound': beta - critical * se,
                         'one_sided_upper_bound': beta + critical * se})
    if not all(math.isfinite(v) for v in estimate.values() if isinstance(v, (float, int))):
        raise ValueError('Nonfinite estimate statistic')
    return estimate


def calculate(panel: pd.DataFrame, diag: dict, threshold: dict, role: str) -> tuple[dict, str]:
    n = len(panel)
    gain = panel['protected_gain_pp'].to_numpy(float) if n else np.array([])
    diag['protected_gain_2pp_economies'] = int((gain >= 2).sum())
    diag['protected_gain_iqr_pp'] = float(np.quantile(gain, .75) - np.quantile(gain, .25)) if n else 0.0
    if (n < threshold['min_shared_complete_economies']
            or diag['protected_gain_2pp_economies'] < threshold['min_protected_gain_2pp_economies']
            or diag['protected_gain_iqr_pp'] < threshold['min_protected_gain_iqr_pp']):
        diag['failed_gate'] = 'shared_sample_or_exposure_floor'
        return {}, 'INCONCLUSIVE'
    try:
        estimate = fit(panel, role, threshold)
        loo = []
        for i in range(n):
            try:
                loo.append(fit(panel.drop(index=i), role, threshold))
            except ValueError:
                continue
    except ValueError as exc:
        diag['failed_gate'] = f'estimator:{exc}'
        return {}, 'INCONCLUSIVE'
    estimate['loo_successes'] = len(loo)
    if (estimate['max_single_economy_residualized_exposure_share']
            > threshold['max_single_economy_residualized_exposure_share']
            or len(loo) < n - threshold['max_loo_failures']):
        diag['failed_gate'] = 'influence_or_loo'
        return estimate, 'INCONCLUSIVE'
    if role == 'forest':
        estimate['loo_positive_share'] = sum(v['coefficient'] > 0 for v in loo) / len(loo)
        estimate['loo_negative_share'] = sum(v['coefficient'] < 0 for v in loo) / len(loo)
        floor = threshold['min_abs_beta_annual_forest_share_pp_per_5pp']
        if (estimate['coefficient'] >= floor and estimate['p_value'] <= threshold['two_sided_p_max']
                and estimate['loo_positive_share'] >= threshold['min_loo_direction_share']):
            return estimate, 'SUPPORTED'
        if (estimate['coefficient'] <= -floor and estimate['p_value'] <= threshold['two_sided_p_max']
                and estimate['loo_negative_share'] >= threshold['min_loo_direction_share']):
            return estimate, 'REFUTED'
    else:
        margin = threshold['noninferiority_margin_annual_log_pp_per_5pp']
        estimate['loo_noninferiority_share'] = sum(v['one_sided_lower_bound'] > -margin
                                                 for v in loo) / len(loo)
        estimate['loo_material_harm_share'] = sum(v['one_sided_upper_bound'] < -margin
                                                 for v in loo) / len(loo)
        if (estimate['one_sided_lower_bound'] > -margin
                and estimate['loo_noninferiority_share'] >= threshold['min_loo_direction_share']):
            return estimate, 'SUPPORTED'
        if (estimate['one_sided_upper_bound'] < -margin
                and estimate['loo_material_harm_share'] >= threshold['min_loo_direction_share']):
            return estimate, 'REFUTED'
    return estimate, 'PARTIAL'


def jwrite(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')


def pwrite(path: Path, columns: dict, schema: pa.Schema) -> None:
    pq.write_table(pa.Table.from_pydict(columns, schema=schema), path,
                   compression='snappy', version='2.6', write_statistics=False)


def emit(directory: Path, hid: str, role: str, lock: dict, panel: pd.DataFrame,
         diag: dict, estimate: dict, verdict: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'hypothesis.yaml').write_bytes((ROOT / SPEC[hid]).read_bytes())
    credit = {'causal': 0, 'policy': 0, 'school': 0, 'position': 0, 'featured': 0}
    manifest = {'design_id': hid, 'family_id': FAMILY, 'family_size': 2,
                'independent_family_count': 1, 'verdict': verdict,
                'evidence_type': 'descriptive', 'spec_commit': REGISTRATION,
                'lock_commit': SOURCE_LOCK, 'spec_sha256': sha(ROOT / SPEC[hid]),
                'lock_sha256': sha(ROOT / LOCK_REL), 'runner_sha256': sha(ROOT / RUNNER_REL),
                'source_files': lock['source_files'], 'artifacts': list(ARTIFACTS), 'credit': credit}
    (directory / 'manifest.yaml').write_text(yaml.safe_dump(manifest, sort_keys=True))
    correction = {'disposition': 'descriptive_calibration_only', 'causal_credit': 0,
                  'policy_score_eligible': False, 'policy_score_credit': 0,
                  'school_score_eligible': False, 'school_score_credit': 0,
                  'featured_eligible': False}
    jwrite(directory / 'diagnostics.json', {**diag, 'verdict': verdict, 'estimate': estimate,
                                            'correction': correction, 'family_id': FAMILY,
                                            'family_size': 2, 'independent_family_count': 1,
                                            'analysis_scope': 'descriptive_only'})
    has_estimate = 'coefficient' in estimate
    pwrite(directory / 'coefficients.parquet', {
        'term': ['protected_gain_5pp'] if has_estimate else [],
        'coefficient': [estimate['coefficient']] if has_estimate else [],
        'standard_error': [estimate['standard_error']] if has_estimate else [],
        'p_value': [estimate['p_value']] if has_estimate else [],
    }, pa.schema([('term', pa.string()), ('coefficient', pa.float64()),
                  ('standard_error', pa.float64()), ('p_value', pa.float64())]))
    jwrite(directory / 'chart_data.json', [
        {key: (str(value) if key == 'country_iso3' else float(value))
         for key, value in row._asdict().items()}
        for row in panel.itertuples(index=False)
    ])
    lines = [f'# {hid}', '', f'**Verdict: {verdict} — descriptive only.**', '',
             f"Shared complete economies: {len(panel)} of {diag['candidate_economies']} source-key candidates.",
             f"2005–2015 protected-share gains >=2 points: {diag['protected_gain_2pp_economies']}; exposure IQR: {diag['protected_gain_iqr_pp']:.6g} points."]
    if has_estimate:
        lines.append(f"Exposure coefficient: {estimate['coefficient']:.6g} per 5-point protected-share gain; HC3 SE {estimate['standard_error']:.6g}; p {estimate['p_value']:.6g}; leave-one-out fits {estimate['loo_successes']}.")
        if role == 'food':
            lines.append(f"One-sided 97.5% interval bounds: lower {estimate['one_sided_lower_bound']:.6g}, upper {estimate['one_sided_upper_bound']:.6g}; frozen noninferiority margin -0.5 annual log point.")
    else:
        lines.append(f"No coefficient was estimated because the frozen gate failed: {diag.get('failed_gate', 'unspecified')}.")
    lines += ['', 'The forest endpoint measures net cover change, not gross deforestation or land-use emissions. The food endpoint measures national food-production-index growth per person, not food access; its noninferiority margin allows a limited penalty and does not establish literal zero harm. These endpoints are one evidence family. No protection policy is identified; zero causal, policy, school, position, or featured credit.', '']
    (directory / 'result_card.md').write_text('\n'.join(lines))
    (directory / 'replication.py').write_text(
        '#!/usr/bin/env python3\nfrom pathlib import Path\nimport subprocess\nimport sys\n'
        'root = Path(__file__).resolve().parents[3]\n'
        f"subprocess.run([sys.executable, str(root / '{RUNNER_REL}'), '--replay', *sys.argv[1:]], check=True)\n"
    )
    packet = {'design_id': hid, 'family_id': FAMILY, 'family_size': 2,
              'independent_family_count': 1, 'verdict': verdict, 'evidence_type': 'descriptive',
              'causal_claim': False, 'school_claim_links': [], 'policy_effect_credit': False,
              'correction': correction, 'source_hashes_verified': True,
              'strict_spec_lock_chronology_verified': True,
              'interpretation': 'Forward protected-land association with distinct net forest-cover and per-person food-output endpoints. The archived proxy verdict remains unchanged.'}
    (directory / 'evidence_packet.yaml').write_text(yaml.safe_dump(packet, sort_keys=True))
    pwrite(directory / 'metric_results.parquet', {
        'verdict': [verdict], 'shared_complete_economies': [len(panel)],
        'protected_gain_2pp_economies': [diag['protected_gain_2pp_economies']],
    }, pa.schema([('verdict', pa.string()), ('shared_complete_economies', pa.int64()),
                  ('protected_gain_2pp_economies', pa.int64())]))
    if tuple(sorted(p.name for p in directory.iterdir())) != tuple(sorted(ARTIFACTS)):
        raise ValueError('Run artifact roster differs')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--run', action='store_true')
    group.add_argument('--replay', action='store_true')
    group.add_argument('--check-lock', action='store_true')
    parser.add_argument('--source-root', type=Path, default=ROOT)
    args = parser.parse_args()
    lock, specs = verify(args.source_root)
    if args.check_lock:
        print(f'{FAMILY}: frozen chronology, source bytes, and key digests verified without selected values')
        return
    values = selected_values(args.source_root, lock)
    threshold = specs[IDS[0]]['falsification']['threshold']
    panel, shared_diag = panel_for(lock, values, threshold)
    for hid in IDS:
        role = specs[hid]['falsification']['threshold']['outcome_role']
        diag = dict(shared_diag)
        estimate, verdict = calculate(panel, diag, specs[hid]['falsification']['threshold'], role)
        target = ROOT / 'engine' / 'runs' / hid
        if args.replay and not target.is_dir():
            raise ValueError(f'No run directory to replay: {hid}')
        if args.run and target.exists():
            raise ValueError(f'Run already exists: {hid}')
        with tempfile.TemporaryDirectory(prefix='ieset_protected_land_family_') as temp:
            generated = Path(temp) / hid
            emit(generated, hid, role, lock, panel, diag, estimate, verdict)
            if args.replay:
                for artifact in ARTIFACTS:
                    if sha(generated / artifact) != sha(target / artifact):
                        raise ValueError(f'Exact replay mismatch: {hid}/{artifact}')
                print(f'{hid}: exact replay matched {len(ARTIFACTS)} artifacts')
            else:
                shutil.copytree(generated, target)
                print(f'{hid}: {verdict}; {len(panel)} shared complete economies; {len(ARTIFACTS)} artifacts')


if __name__ == '__main__':
    main()
