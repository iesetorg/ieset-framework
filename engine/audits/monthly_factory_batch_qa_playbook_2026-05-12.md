# Monthly Factory Batch QA Playbook - 2026-05-12

Use this checklist on every new hypothesis batch before any scoreboard conversion.

## Required Structural Checks

1. File counts
   - One hypothesis YAML per promoted hypothesis.
   - One steelman file per hypothesis.
   - One run directory per executed hypothesis.
   - Run directory contains `diagnostics.json`, `manifest.yaml`, `result_card.md`, `replication.py`.
   - If a coefficient model ran, it should also contain `coefficients.parquet` and `chart_data.json`.

2. Country universe
   - ISO3 country codes must be real countries, plus accepted special cases such as `XKX`.
   - Exclude World Bank aggregate region/income codes such as `AFE`, `AFW`, `ARB`, `CEB`, `CSS`, `EUU`, `HIC`, `LIC`, `LMY`, `MIC`, `OED`, `WLD`.
   - `sample.countries` should match the filtered sample or use an explicit group token such as `GLOBAL`; do not silently truncate country lists.

3. Controls and formula
   - Treatment, outcome, and controls must be unique after de-duplication.
   - Diagnostics must report the actual controls used in the model.
   - The outcome must never appear as its own control.
   - Fixed effects must not absorb the treatment; if they do, redesign the estimator or mark inconclusive.

4. Manifest consistency
   - `manifest.yaml.hypothesis_id` equals the run directory name.
   - `diagnostics.json.hypothesis_id` equals the run directory name.
   - `manifest.yaml.verdict_label` equals `diagnostics.json.verdict_label`.
   - Every vintage path in the manifest exists locally.
   - Every source has publisher, series/dataset, row count or source path, fetch time or vintage id, and hash where available.

5. Schema and link checks
   - Run `python3 scripts/validate_specs.py 2>&1 | rg '<batch_prefix_or_ids>'`.
   - Run `python3 scripts/validate_scope_alignment.py`.
   - If mappings were touched, run `python3 scripts/validate_link_reciprocity.py --summary`.

## Duplicate And Broad-Proxy Checks

Before scoreboard conversion, compute a batch fingerprint from:

- treatment variable
- outcome variable
- sample period
- country/sample universe
- estimator template
- coefficient
- p-value
- verdict reason

Hold any near-duplicate group unless the audit explains why it is independent evidence.

Broad-proxy rules:

- Direct treatment + direct outcome: eligible after mapping.
- Broad treatment + direct outcome: eligible with caveat and duplicate check.
- Direct treatment + broad outcome: eligible at lower confidence.
- Broad treatment + broad outcome: hold or demote to meta-audit.

## Partial Verdict Rules

- Neutral partial: ambiguous direction, zero/mixed effect, or non-estimable uncertainty. Score impact: 0.
- Directional partial: leans clearly toward the claim but misses the full threshold. Score impact: 0.5 after evidence weighting.
- Ambiguous partial: hold in `hold_interpretation_qa`.

Do not let `PARTIAL` move the scoreboard unless direction and interpretation are documented.

## Scoreboard Conversion Checks

Every verdict gets a conversion bucket:

- `scoreboard_ready_existing_mapping`
- `needs_position_claim_mapping`
- `hold_interpretation_qa`
- `hold_duplicate_broad_panel_qa`
- `hold_broad_panel_upgrade`
- `repair_data_or_design`

Required mapping fields before scoring:

- position-side `linked_hypothesis_id`
- `school_prediction`
- `claim_polarity`
- hypothesis-side reciprocal `covers_claims`

Daily conversion caps:

- Max 4 net-new scored links per school.
- Associational panels should contribute no more than 50% of new daily q-weight.
- No single broad panel family should contribute more than 25% of new daily q-weight.

## Handy Commands

```bash
python3 scripts/validate_scope_alignment.py
python3 scripts/validate_specs.py 2>&1 | rg '<batch_prefix_or_ids>'
python3 scripts/validate_link_reciprocity.py --summary
python3 scripts/audit_throughput_scoreboard_conversion.py
python3 scripts/audit_scoreboard_outcomes.py
```

Country/sample sanity check template:

```bash
python3 - <<'PY'
import json, yaml, pycountry
from pathlib import Path

ids = [p.name for p in Path('engine/runs').glob('<prefix>*')]
iso = {c.alpha_3 for c in pycountry.countries}
iso.add('XKX')
bad = []
for hid in ids:
    diag = json.loads((Path('engine/runs') / hid / 'diagnostics.json').read_text())
    manifest = yaml.safe_load((Path('engine/runs') / hid / 'manifest.yaml').read_text())
    if manifest.get('verdict_label') != diag.get('verdict_label'):
        bad.append((hid, 'manifest/diagnostic verdict mismatch'))
    for hyp in Path('hypotheses').glob(f'*/{hid}.yaml'):
        doc = yaml.safe_load(hyp.read_text())
        bad_codes = [c for c in doc.get('sample', {}).get('countries', []) if c not in iso]
        if bad_codes:
            bad.append((hid, 'invalid country codes', bad_codes[:10]))
        controls = [c.get('name') for c in doc.get('variables', {}).get('controls', [])]
        outcomes = [c.get('name') for c in doc.get('variables', {}).get('outcome', [])]
        if set(controls) & set(outcomes):
            bad.append((hid, 'outcome listed as control'))
print('issues', len(bad))
for item in bad:
    print(item)
PY
```
