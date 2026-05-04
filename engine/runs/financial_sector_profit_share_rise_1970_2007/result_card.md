# US financial-sector profit share, 1970 vs 2007

**Verdict:** refuted — endpoint outside falsification band: 2007 share = 7.1% < 27% falsify-band. Direction wrong (-6.5pp 1970→2007).

## Summary

- 1970 financial_share = **13.6%** (target ≤ 15%; falsify-band: > 18%).
- 2007 financial_share = **7.1%** (target ≥ 30%; falsify-band: < 27%).
- Δ 1970→2007 = **-6.5pp** (-0.17pp/yr).
- First year with share ≥ 20%: **1981**.
- First year with share ≥ 30%: **1982**.

## Method

Constructed series: `financial_share = A453RC1Q027SBEA / (A453RC1Q027SBEA + A446RC1Q027SBEA)`. Both inputs are quarterly billions-of-dollars NIPA flows (financial corporate profits before tax, and domestic non-financial corporate profits before tax). The annual figure is the simple mean of within-year quarterly observations of each numerator/denominator, then the share is constructed from the annual means.

Endpoint tests:

- PRIMARY (a): share[1970] ≤ 0.15. Falsify-band: > 0.18.
- PRIMARY (b): share[2007] ≥ 0.30. Falsify-band: < 0.27.

If either endpoint sits inside its tolerance band but the direction is correct (Δ ≥ +10pp), the verdict is `partial`. If either is on the wrong side of its falsify-band, the verdict is `refuted`. If the input vintages are missing, the verdict is `inconclusive`.

## Data

- fred:A453RC1Q027SBEA (financial corporate profits before tax, quarterly)
- fred:A446RC1Q027SBEA (domestic non-financial corporate profits before tax, quarterly)
