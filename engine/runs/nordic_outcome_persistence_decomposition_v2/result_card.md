# Result card — Nordic outcome persistence decomposition v2

**Verdict:** partially supported (primary outcome improved materially but did not meet 0.30 threshold)

Pre-registered falsifier: v2 residual share on log GDP/cap PPP must be both (a) ≤ 0.30 *and* (b) materially lower than v1's 0.98 (Δ ≥ 0.10). Both must hold for v2 support.

## Coefficient summary

| Outcome | v1 residual | v2 residual | Δ | Threshold | Pass? |
|---|---:|---:|---:|---:|:---:|
| `log_gdp_pc_ppp` | 0.76 | 0.43 | -0.33 | 0.30 | ✗ |
| `gini` | 0.83 | 0.52 | -0.31 | 0.50 | ✗ |
| `unemployment` | 0.09 | 0.38 | +0.30 | 0.50 | ✓ |

Material-delta-on-primary (Δ ≥ 0.10): yes

## Leave-one-out sensitivity (primary outcome)

Drops each v2 channel and reports how much the residual share changes. Channels that are load-bearing should show larger changes when dropped.

| Channel dropped | Nordic coef | Residual share | Contribution |
|---|---:|---:|---:|
| `gov_eff` | +0.230 | 0.47 | +0.04 |
| `rule_of_law` | +0.238 | 0.49 | +0.06 |
| `debt_gdp` | +0.193 | 0.40 | -0.03 |
| `cc` | +0.208 | 0.43 | -0.00 |
| `rq` | +0.222 | 0.46 | +0.03 |
| `net_lending_gdp` | +0.240 | 0.50 | +0.06 |
| `current_account_gdp` | +0.267 | 0.55 | +0.12 |
| `trade_openness` | +0.198 | 0.41 | -0.02 |

## VIFs (multicollinearity diagnostic)

| Variable | VIF |
|---|---:|
| `rule_of_law` | 34.98 |
| `cc` | 20.0 |
| `gov_eff` | 17.99 |
| `rq` | 10.24 |
| `debt_gdp` | 6.37 |
| `log_population` | 4.09 |
| `current_account_gdp` | 2.7 |
| `net_lending_gdp` | 2.48 |
| `trade_openness` | 1.97 |
| `urbanisation` | 1.75 |

**Warning:** max VIF = 35.0, indicates severe multicollinearity. Individual channel coefficients are unreliable even though the residual-share summary is mechanically interpretable.

## Interpretation

v2 reduced the primary-outcome residual from v1's 0.98 to 0.43 (Δ = -0.33) — a meaningful shrinkage but still above the 0.30 pre-registered threshold. Partial support: more channels do explain more of the gap, but the cross-sectional decomposition is still not fully sufficient. Part of the Nordic advantage remains unmeasured on this 10-country × 28-year panel.

Per DISCLOSURE.md commitment, this finding is reported regardless of direction relative to the author's prior.

## Provenance

Reproduces deterministically from the vintages listed in `manifest.yaml`. See `replication.py`. Pre-registration: see `hypotheses/institutional_quality/nordic_outcome_persistence_decomposition_v2.yaml` and its git first-commit timestamp (predates this run).
