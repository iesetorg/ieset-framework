#!/usr/bin/env python3
"""Frozen descriptive WDI electricity-access and later female-LFP study.

The code, specification, source-key roster, and memo enter git before selected
values are read. Original WDI sources and their manifest lock enter a second
commit, followed by measured results in a third commit.
"""
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
import statsmodels.api as sm
import yaml

ROOT = Path(__file__).resolve().parents[1]
ID = 'wdi_electricity_access_female_lfp_forward_2026'
RUNNER = 'scripts/run_wdi_electricity_female_lfp_2026.py'
PREREG = 'engine/audits/wdi_electricity_female_lfp_prereg_2026-10-10.md'
SPEC = f'hypotheses/labour/{ID}.yaml'
STEELMAN = f'hypotheses/steelman/{ID}.md'
ROSTER = 'data/pinned_evidence/wdi_electricity_female_lfp_key_roster.csv'
ROSTER_SHA = 'a7b8e33e420cd1c0ce8160ad4e03e1102440d184842dd450027a446df26e8638'
LOCK = 'data/pinned_evidence/wdi_electricity_female_lfp_2026.manifest.json'
ERRATUM = 'engine/audits/wdi_electricity_female_lfp_source_custody_erratum_2026-10-10.md'
SUMMARY = 'engine/audits/wdi_electricity_female_lfp_results_2026-10-10.md'
RUN_DIR = f'engine/runs/{ID}'
FETCH_MANIFEST = 'data/manifests/fetch_run_2026-05-05T200056Z.yaml'
FETCH_SHA = 'a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945'
SOURCES = {
    'electricity': {
        'series_id': 'EG.ELC.ACCS.ZS',
        'path': 'data/vintages/world_bank_wdi/EG.ELC.ACCS.ZS@2026-05-05T195057Z.parquet',
        'sha256': 'aa564cbe2947b3d1c3499d7ecb9b2c38c6aa5de073d2cc1a797cfe2fe42f2931',
        'rows': 17556,
    },
    'female_lfp': {
        'series_id': 'SL.TLF.CACT.FE.ZS',
        'path': 'data/vintages/world_bank_wdi/SL.TLF.CACT.FE.ZS@2026-05-05T194807Z.parquet',
        'sha256': 'c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186',
        'rows': 17556,
    },
}
MIN_COMPLETE_COUNTRIES = 120
MIN_MATERIAL_GAIN_COUNTRIES = 30
MATERIAL_GAIN_PP = 10.0
MIN_EXPOSURE_P90_P10_SPREAD_PP = 15.0
MIN_BASELINE_BELOW_95_COUNTRIES = 40
MAX_TOP_COUNTRY_RESIDUAL_SHARE = 0.15
MAX_TOP_TEN_COUNTRY_RESIDUAL_SHARE = 0.50
MIN_HOLDOUT_COUNTRIES = 100
MIN_DIRECTIONAL_HOLDOUTS = 4
MEANINGFUL_BETA = 0.10
P_MAX = 0.01
CORRECTION = {
    'disposition': 'descriptive_calibration_only',
    'family_id': ID, 'family_size': 1,
    'family_alpha': 0.01, 'bonferroni_p_max': P_MAX,
    'causal_credit': 0, 'school_score_eligible': False,
    'school_score_credit': 0, 'policy_score_eligible': False,
    'policy_score_credit': 0, 'featured_eligible': False,
}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def first_added(path: str) -> str:
    rows = git('log', '--diff-filter=A', '--format=%H', 'HEAD', '--', path).decode().splitlines()
    if not rows:
        raise RuntimeError(f'no first-addition commit: {path}')
    return rows[-1]


def frozen(path: str, revision: str) -> None:
    p = ROOT / path
    if not p.is_file() or p.read_bytes() != git('show', f'{revision}:{path}'):
        raise RuntimeError(f'frozen-byte mismatch: {path}')
    if git('status', '--porcelain', '--', path).strip():
        raise RuntimeError(f'uncommitted frozen file: {path}')


def ancestor(older: str, newer: str) -> bool:
    return older != newer and subprocess.run(
        ['git', 'merge-base', '--is-ancestor', older, newer], cwd=ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ).returncode == 0


def threshold() -> dict:
    return {
        'family_id': ID, 'family_size': 1,
        'family_alpha': 0.01, 'p_max_two_sided': P_MAX,
        'meaningful_beta_min_abs': MEANINGFUL_BETA,
        'min_complete_countries': MIN_COMPLETE_COUNTRIES,
        'min_material_gain_countries': MIN_MATERIAL_GAIN_COUNTRIES,
        'material_electricity_access_gain_pp': MATERIAL_GAIN_PP,
        'min_exposure_p90_p10_spread_pp': MIN_EXPOSURE_P90_P10_SPREAD_PP,
        'min_baseline_below_95_countries': MIN_BASELINE_BELOW_95_COUNTRIES,
        'max_top_country_residualized_exposure_share': MAX_TOP_COUNTRY_RESIDUAL_SHARE,
        'max_top_ten_country_residualized_exposure_share': MAX_TOP_TEN_COUNTRY_RESIDUAL_SHARE,
        'min_leave_one_hash_fold_out_countries': MIN_HOLDOUT_COUNTRIES,
        'min_concordant_holdouts_for_directional_verdict': MIN_DIRECTIONAL_HOLDOUTS,
        'roster_sha256': ROSTER_SHA, 'source_lock_path': LOCK,
        'causal_credit': 0, 'school_score_eligible': False,
        'school_score_credit': 0, 'policy_score_eligible': False,
        'policy_score_credit': 0, 'featured_eligible': False,
    }


def roster() -> list[str]:
    path = ROOT / ROSTER
    if sha(path) != ROSTER_SHA:
        raise RuntimeError('source-key roster hash mismatch')
    rows = list(csv.DictReader(path.open(newline='')))
    codes = [r['country_iso3'] for r in rows]
    if len(codes) != 216 or codes != sorted(set(codes)) or any(len(c) != 3 or not c.isupper() for c in codes):
        raise RuntimeError('source-key roster shape mismatch')
    return codes


def registration_commit() -> str:
    paths = [RUNNER, PREREG, SPEC, STEELMAN, ROSTER]
    revisions = {first_added(p) for p in paths}
    if len(revisions) != 1:
        raise RuntimeError('registration files do not have one first-addition commit')
    rev = revisions.pop()
    for p in paths:
        if p != RUNNER:
            frozen(p, rev)
    corrections = git('log', '--format=%H', f'{rev}..HEAD', '--', RUNNER).decode().splitlines()
    if len(corrections) != 1:
        raise RuntimeError('runner requires exactly one documented pre-value custody correction')
    correction = corrections[0]
    if first_added(ERRATUM) != correction:
        raise RuntimeError('custody correction lacks contemporaneous erratum')
    changed = set(git('diff', '--name-only', f'{correction}^', correction).decode().splitlines())
    if changed != {RUNNER, ERRATUM}:
        raise RuntimeError('custody correction commit changed unrelated files')
    if not ancestor(first_added(LOCK), correction):
        raise RuntimeError('custody correction must follow source lock and precede results')
    frozen(RUNNER, correction)
    frozen(ERRATUM, correction)
    spec = yaml.safe_load((ROOT / SPEC).read_text())
    codes = roster()
    if (spec.get('hypothesis_id') != ID
            or spec.get('status') != 'pre_registered'
            or spec.get('evidence_type') != 'descriptive'
            or spec.get('sample', {}).get('countries') != codes
            or spec.get('scope', {}).get('countries') != codes
            or spec.get('falsification', {}).get('threshold') != threshold()
            or spec.get('covers_claims') != []
            or spec.get('linked_hypotheses') != []):
        raise RuntimeError('frozen specification does not match runner')
    if git('ls-tree', '-r', '--name-only', rev, '--', RUN_DIR).strip():
        raise RuntimeError('measured run entered registration commit')
    if git('ls-tree', '-r', '--name-only', rev, '--', LOCK).strip():
        raise RuntimeError('source lock entered registration commit')
    return rev


def manifest_sources() -> dict:
    if sha(ROOT / FETCH_MANIFEST) != FETCH_SHA:
        raise RuntimeError('fetch-manifest hash mismatch')
    entries = yaml.safe_load((ROOT / FETCH_MANIFEST).read_text())['entries']
    out = {}
    for role, src in SOURCES.items():
        matches = [e for e in entries
                   if e.get('publisher') == 'world_bank_wdi'
                   and e.get('series_id') == src['series_id']
                   and e.get('parquet_path') == src['path']]
        if len(matches) != 1:
            raise RuntimeError(f'fetch-manifest missing or duplicate: {role}')
        e = matches[0]
        if e.get('sha256') != src['sha256'] or e.get('rows') != src['rows'] or e.get('license') != 'CC-BY-4.0':
            raise RuntimeError(f'fetch-manifest mismatch: {role}')
        out[role] = {k: e.get(k) for k in ('publisher', 'series_id', 'parquet_path', 'sha256', 'rows', 'license', 'fetch_utc', 'source_url', 'methodology_url')}
    return out


def lock_data(reg: str) -> dict:
    return {
        'schema': 'ieset-wdi-electricity-female-lfp-source-lock-v1',
        'registration_commit': reg, 'roster_sha256': ROSTER_SHA,
        'runner_sha256': hashlib.sha256(git('show', f'{reg}:{RUNNER}')).hexdigest(),
        'fetch_manifest': FETCH_MANIFEST, 'fetch_manifest_sha256': FETCH_SHA,
        'sources': manifest_sources(),
    }


def source_lock_commit(reg: str) -> str:
    previously_tracked = [s['path'] for s in SOURCES.values()
                          if git('ls-tree', '-r', '--name-only', reg, '--', s['path']).strip()]
    newly_pinned = [s['path'] for s in SOURCES.values() if s['path'] not in previously_tracked]
    revisions = {first_added(p) for p in [LOCK] + newly_pinned}
    if len(revisions) != 1:
        raise RuntimeError('source lock and newly pinned raw files lack one first-addition commit')
    rev = revisions.pop()
    if not ancestor(reg, rev):
        raise RuntimeError('source lock must strictly follow registration')
    for p in [LOCK] + newly_pinned:
        frozen(p, rev)
    for p in previously_tracked:
        frozen(p, reg)
        if git('log', '--format=%H', f'{reg}..HEAD', '--', p).strip():
            raise RuntimeError(f'previously tracked raw source changed after registration: {p}')
    if json.loads((ROOT / LOCK).read_text()) != lock_data(reg):
        raise RuntimeError('source lock metadata mismatch')
    for role, src in SOURCES.items():
        if sha(ROOT / src['path']) != src['sha256']:
            raise RuntimeError(f'raw source hash mismatch: {role}')
    return rev


def read_values(role: str) -> dict[tuple[str, int], float | None]:
    src = SOURCES[role]
    frame = pd.read_parquet(ROOT / src['path'])
    if len(frame) != src['rows']:
        raise RuntimeError(f'raw row count mismatch: {role}')
    selected = frame[frame['country_iso3'].isin(roster())]
    if selected.duplicated(['country_iso3', 'year']).any():
        raise RuntimeError(f'duplicate source keys: {role}')
    values = {}
    for row in selected.itertuples(index=False):
        key = (row.country_iso3, int(row.year))
        status = row.obs_status
        if not (pd.isna(status) or str(status).strip() in ('', 'A')):
            values[key] = None
            continue
        try:
            v = float(row.value)
        except (TypeError, ValueError):
            v = float('nan')
        values[key] = v if math.isfinite(v) else None
    return values


def frame_from_sources(source_values: dict) -> tuple[pd.DataFrame, dict]:
    rows = []
    excluded = {'missing_or_nonfinite_or_status': 0, 'outside_frozen_bounds': 0}
    for c in roster():
        e0 = source_values['electricity'].get((c, 2000))
        e1 = source_values['electricity'].get((c, 2010))
        f0 = source_values['female_lfp'].get((c, 2010))
        f1 = source_values['female_lfp'].get((c, 2020))
        if any(v is None for v in (e0, e1, f0, f1)):
            excluded['missing_or_nonfinite_or_status'] += 1
            continue
        if any(not 0 <= v <= 100 for v in (e0, e1, f0, f1)):
            excluded['outside_frozen_bounds'] += 1
            continue
        rows.append({
            'country_iso3': c,
            'baseline_access': e0,
            'access_gain': e1-e0,
            'baseline_female_lfp': f0,
            'female_lfp_gain': f1-f0,
            'fold': int(hashlib.sha256(c.encode()).hexdigest()[:8], 16) % 5,
        })
    return pd.DataFrame(rows), excluded


def fit(frame: pd.DataFrame) -> tuple[dict, np.ndarray] | None:
    if len(frame) < 10:
        return None
    x = frame['access_gain'].to_numpy(dtype=float)
    y = frame['female_lfp_gain'].to_numpy(dtype=float)
    baseline = np.column_stack([np.ones(len(frame)), frame['baseline_female_lfp'].to_numpy(dtype=float), frame['baseline_access'].to_numpy(dtype=float)])
    full = np.column_stack([baseline[:,0], x, baseline[:,1:]])
    if np.linalg.matrix_rank(full) != full.shape[1]:
        return None
    fitted = sm.OLS(y, full).fit(cov_type='HC3', use_t=True)
    beta, se, p = map(float, (fitted.params[1], fitted.bse[1], fitted.pvalues[1]))
    residual = x - baseline @ np.linalg.lstsq(baseline, x, rcond=None)[0]
    squares = residual**2
    total = float(squares.sum())
    if not (math.isfinite(beta) and math.isfinite(se) and se > 0 and math.isfinite(p) and total > 1e-10):
        return None
    shares = np.sort(squares/total)[::-1]
    ci = fitted.conf_int(alpha=P_MAX)[1]
    return ({
        'coefficient': beta, 'standard_error_hc3': se, 'p_two_sided': p,
        'df_resid': int(fitted.df_resid),
        'familywise_ci_99': [float(ci[0]), float(ci[1])],
        'top_country_residualized_exposure_share': float(shares[0]),
        'top_ten_country_residualized_exposure_share': float(shares[:10].sum()),
    }, residual)


def analyze(source_values: dict) -> tuple[dict, pd.DataFrame]:
    data, excluded = frame_from_sources(source_values)
    n = len(data)
    failed = []
    if n < MIN_COMPLETE_COUNTRIES:
        failed.append('min_complete_countries')
    material = int((data['access_gain'] >= MATERIAL_GAIN_PP).sum()) if n else 0
    if material < MIN_MATERIAL_GAIN_COUNTRIES:
        failed.append('min_material_gain_countries')
    below_95 = int((data['baseline_access'] < 95).sum()) if n else 0
    if below_95 < MIN_BASELINE_BELOW_95_COUNTRIES:
        failed.append('min_baseline_below_95_countries')
    spread = float(np.percentile(data['access_gain'],90)-np.percentile(data['access_gain'],10)) if n else None
    if spread is None or spread < MIN_EXPOSURE_P90_P10_SPREAD_PP:
        failed.append('min_exposure_p90_p10_spread_pp')
    primary = fit(data)
    if primary is None:
        failed.append('full_rank_positive_hc3_uncertainty_and_residual_exposure')
    else:
        estimate = primary[0]
        if estimate['top_country_residualized_exposure_share'] > MAX_TOP_COUNTRY_RESIDUAL_SHARE:
            failed.append('max_top_country_residualized_exposure_share')
        if estimate['top_ten_country_residualized_exposure_share'] > MAX_TOP_TEN_COUNTRY_RESIDUAL_SHARE:
            failed.append('max_top_ten_country_residualized_exposure_share')
    holdouts = {}
    for fold in range(5):
        subset = data[data['fold'] != fold] if n else data
        if len(subset) < MIN_HOLDOUT_COUNTRIES:
            failed.append(f'min_holdout_countries_fold_{fold}')
            holdouts[str(fold)] = {'countries': len(subset), 'coefficient': None}
            continue
        fitted = fit(subset)
        if fitted is None:
            failed.append(f'holdout_estimator_fold_{fold}')
        holdouts[str(fold)] = {'countries': len(subset), 'coefficient': fitted[0]['coefficient'] if fitted else None}
    positive = sum(v['coefficient'] is not None and v['coefficient'] > 0 for v in holdouts.values())
    negative = sum(v['coefficient'] is not None and v['coefficient'] < 0 for v in holdouts.values())
    estimate = primary[0] if primary else None
    if failed:
        verdict = 'INCONCLUSIVE'
    elif estimate['coefficient'] >= MEANINGFUL_BETA and estimate['p_two_sided'] <= P_MAX and positive >= MIN_DIRECTIONAL_HOLDOUTS:
        verdict = 'SUPPORTED'
    elif estimate['coefficient'] <= -MEANINGFUL_BETA and estimate['p_two_sided'] <= P_MAX and negative >= MIN_DIRECTIONAL_HOLDOUTS:
        verdict = 'REFUTED'
    else:
        verdict = 'PARTIAL'
    result = {
        'design_id': ID, 'verdict': verdict, 'analysis_scope': 'descriptive_only',
        'source_key_countries': 216, 'complete_countries': n,
        'excluded_reasons': excluded,
        'material_access_gain_countries': material,
        'baseline_access_below_95_countries': below_95,
        'access_gain_p90_p10_spread_pp': spread,
        'estimate': estimate, 'leave_one_hash_fold_out': holdouts,
        'positive_holdout_signs': positive, 'negative_holdout_signs': negative,
        'failed_gates': sorted(set(failed)), 'correction': CORRECTION,
        'notes': 'Two WDI/modelled series, cross-country descriptive association. Exact timing and baseline controls do not identify an electricity or policy effect; earlier electricity-to-growth and electricity-to-child-mortality archive tests were visible before selection.',
    }
    return result, data


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n').encode()


def yaml_bytes(value: object) -> bytes:
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode()


def parquet_bytes(rows: list[dict], columns: list[str]) -> bytes:
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=columns).to_parquet(buffer, index=False, engine='pyarrow')
    return buffer.getvalue()


def artifacts(result: dict, data: pd.DataFrame, reg: str, lock: str) -> dict[str, bytes]:
    estimate = result['estimate'] or {}
    beta = estimate.get('coefficient')
    p = estimate.get('p_two_sided')
    card = '\n'.join([
        '# Electricity access gains and later female labour-force participation', '',
        f"**Verdict: {result['verdict']}** — descriptive calibration only; zero causal, policy, school, position, and featured credit.", '',
        f"Source-key economies: 216; complete cases: {result['complete_countries']}.",
        f"At least +10 percentage-point electricity gain: {result['material_access_gain_countries']} countries; p90−p10 gain spread: {result['access_gain_p90_p10_spread_pp']} points.",
        f"HC3 slope: {beta} female participation percentage points per +1 point electricity access; two-sided p: {p}; frozen p cutoff: {P_MAX}.",
        f"Frozen gate failures: {', '.join(result['failed_gates']) or 'none'}.",
        f"Five fixed country-hash holdouts: {result['positive_holdout_signs']} positive, {result['negative_holdout_signs']} negative.", '',
        'Electricity access is population coverage rather than supply reliability. Female labour-force participation is an ILO-modelled 15+ rate including employed and unemployed women, not employment quality or unpaid work. Global development, schooling, fertility, industrial structure, income, and policy changes can shift both series.',
        'Earlier electricity-to-growth and electricity-to-child-mortality tests were visible before this distinct outcome was chosen. A single-test p cutoff does not correct archive-wide selection.',
        f'Frozen registration `{reg}`; later source lock `{lock}`; documented pre-value custody erratum `{first_added(ERRATUM)}`. Exact replay: `python3 -B {RUNNER} --verify`.',
    ])+'\n'
    manifest = {
        'design_id': ID, 'evidence_type': 'descriptive', 'verdict': result['verdict'],
        'spec_commit': reg, 'lock_commit': lock, 'runner_sha256': sha(ROOT/RUNNER),
        'runner_custody_correction_commit': first_added(ERRATUM),
        'source_custody': manifest_sources(),
        'credit': {'causal': 0, 'policy': 0, 'school': 0, 'position': 0, 'featured': 0},
        'artifacts': ['hypothesis.yaml','manifest.yaml','diagnostics.json','coefficients.parquet','metric_results.parquet','chart_data.json','result_card.md','replication.py','evidence_packet.yaml'],
    }
    packet = {
        'design_id': ID, 'verdict': result['verdict'], 'evidence_type':'descriptive',
        'causal_claim': False, 'policy_effect_credit': False,
        'source_hashes_verified': True, 'strict_spec_lock_chronology_verified': True,
        'school_claim_links': [], 'correction': CORRECTION,
        'interpretation':'Later female labour-force participation association with earlier electricity-access expansion; no causal or policy effect.',
    }
    coeff = [{'term':'electricity_access_gain_pp','coefficient':beta,'standard_error_hc3':estimate.get('standard_error_hc3'),'p_two_sided':p,'verdict':result['verdict']}]
    metrics = [{'metric':'female_lfp_2010_2020_change_pp','value':beta,'p_value':p,'verdict':result['verdict'],'complete_countries':result['complete_countries']}]
    chart = {'design_id':ID,'sample_countries':len(data),'country_values_published':False,
             'access_gain_quantiles':{str(q):float(np.percentile(data.access_gain,q)) for q in (10,25,50,75,90)} if len(data) else {},
             'female_lfp_change_quantiles':{str(q):float(np.percentile(data.female_lfp_gain,q)) for q in (10,25,50,75,90)} if len(data) else {}}
    replication = f"#!/usr/bin/env python3\nimport subprocess\nimport sys\nfrom pathlib import Path\nroot = Path(__file__).resolve().parents[3]\nraise SystemExit(subprocess.call([sys.executable, '-B', str(root / '{RUNNER}'), '--verify']))\n"
    summary = '\n'.join([
        '# Electricity access and later female labour-force participation — locked result', '',
        f'Registration `{reg}` strictly preceded source lock `{lock}` and the measured run. A later pre-value custody erratum `{first_added(ERRATUM)}` records the electricity file already tracked in the base; the analysis rule was unchanged.',
        'The two exact WDI raw files were SHA-256 checked against the tracked fetch manifest; WDI metadata lists CC-BY-4.0 and attributes the labour series to ILO modelled estimates.', '',
        f"**Verdict: {result['verdict']}**. Complete countries: {result['complete_countries']}/216; material gain countries: {result['material_access_gain_countries']}; access gain p90−p10 spread: {result['access_gain_p90_p10_spread_pp']} points.",
        f"HC3 slope: {beta} female LFP percentage points per +1 electricity point; two-sided p: {p}; threshold: {P_MAX}; failed gates: {', '.join(result['failed_gates']) or 'none'}.",
        f"Five deterministic hash-fold holdouts: +{result['positive_holdout_signs']}/5, -{result['negative_holdout_signs']}/5.", '',
        'This single descriptive test was selected after visible archive electricity-to-growth and electricity-to-child-mortality studies, which use different outcomes. The p cutoff is not an archive-wide selection correction. No causal, policy, school, position, or featured credit.',
        'World Bank indicator definitions: [access to electricity](https://data.worldbank.org/indicator/EG.ELC.ACCS.ZS), [female labour-force participation](https://data.worldbank.org/indicator/SL.TLF.CACT.FE.ZS).',
        f'Exact replay: `python3 -B {RUNNER} --verify`.',
    ])+'\n'
    return {
        f'{RUN_DIR}/hypothesis.yaml': (ROOT/SPEC).read_bytes(),
        f'{RUN_DIR}/manifest.yaml': yaml_bytes(manifest),
        f'{RUN_DIR}/diagnostics.json': json_bytes(result),
        f'{RUN_DIR}/coefficients.parquet': parquet_bytes(coeff,['term','coefficient','standard_error_hc3','p_two_sided','verdict']),
        f'{RUN_DIR}/metric_results.parquet': parquet_bytes(metrics,['metric','value','p_value','verdict','complete_countries']),
        f'{RUN_DIR}/chart_data.json': json_bytes(chart),
        f'{RUN_DIR}/result_card.md': card.encode(),
        f'{RUN_DIR}/replication.py': replication.encode(),
        f'{RUN_DIR}/evidence_packet.yaml': yaml_bytes(packet),
        SUMMARY: summary.encode(),
    }


def reproduce(write: bool) -> None:
    reg = registration_commit()
    lock = source_lock_commit(reg)
    source_values = {role:read_values(role) for role in SOURCES}
    result, data = analyze(source_values)
    expected = artifacts(result,data,reg,lock)
    for rel,payload in expected.items():
        path = ROOT/rel
        if write:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(payload)
        elif not path.is_file() or path.read_bytes()!=payload:
            raise RuntimeError(f'exact replay mismatch: {rel}')
    print(result['verdict'],result['complete_countries'],result['estimate'],result['failed_gates'])
    print('frozen run artifacts written' if write else 'exact replay passed')


def main() -> int:
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--make-lock',action='store_true')
    group.add_argument('--run',action='store_true')
    group.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.make_lock:
        reg=registration_commit()
        for role,src in SOURCES.items():
            if sha(ROOT/src['path'])!=src['sha256']:
                raise RuntimeError(f'raw source hash mismatch: {role}')
        path=ROOT/LOCK
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(json_bytes(lock_data(reg)))
        print('source lock written; commit raw files and manifest before selected-value access')
    else:
        reproduce(write=args.run)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
