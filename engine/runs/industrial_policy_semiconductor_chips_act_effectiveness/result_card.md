# CHIPS Act / IRA semiconductor industrial policy effectiveness

**Verdict:** inconclusive — Stacked: (4/4) spec-named semi-specific series unavailable on disk (oecd:STAN_INDUSTRY ISIC C26, bls:CES3133, ilostat:semiconductor employment, constructed CHIPS capex), AND post-treatment window is 0 year(s) vs spec horizon 2030 (8-year gap). CHIPS/IRA fab build-out lead-times of 3-5 years mean leading-edge US fabs (TSMC AZ, Intel OH, Samsung TX) are not expected to reach steady-state output until 2026-2028; the spec's 2030 horizon is a deliberate acknowledgement of this. Re-run when semi-specific fetchers land AND post-2022 vintage extends to 2027+.

## Summary

Spec proposes a 2030 multi-metric pattern check on US CHIPS Act + IRA
industrial policy: capacity-VA gain >30%, employment gain <15%,
private capex >$200B. Two stacked obstacles prevent dispositive
evaluation today:

1. **Data gap** — 4/4 spec-named semiconductor-specific series are not available in current
   vintages. The proxy on disk (broad industry VA) is too coarse,
   and for the treated unit (USA) the proxy itself is sparse.
2. **Window too short** — Treatment year is 2022; latest available
   data extends to 2022 (0 post-treatment years vs 4-year minimum).
   CHIPS Act fab build-out lead-times are 3-5 years before
   commissioning; the spec's deliberate 2030 horizon reflects
   that lead-time. Even with perfect data, primary tests are not
   informative until 2027-2028 at the earliest.

## Method

v1 promotion (2026-04-24). The replication encodes:

- A series-availability audit against the four spec-named series,
- A post-treatment window-length check (≥4 years required),
- A best-available proxy probe (world_bank_wdi:NV.IND.TOTL.KD)
  showing the treated unit (USA) has near-zero coverage in the
  post-2018 window even at the broad industry level.

Either obstacle alone would justify inconclusive; both together
make the case unambiguous. The script is structured to re-run
cleanly once the missing series land — primary thresholds
(30% capacity / 15% employment / $200B capex) are pinned as
constants.

## Data

Required (missing — fetcher backlog):

  - `oecd:STAN_INDUSTRY_C26` — OECD STAN ISIC C26 (computer, electronic, optical products) value added
  - `bls:CES3133` — BLS CES semiconductor & other electronic component mfg employment
  - `ilostat:semiconductor_employment` — ILOSTAT cross-country sectoral employment, NACE C26
  - `constructed:chips_act_capex_commitments` — Hand-coded CHIPS Act award announcements + private capex commitments

Available (used for window probe only):

  - (none)

## Reproduction

```
.venv/bin/python3 engine/runs/industrial_policy_semiconductor_chips_act_effectiveness/replication.py
```
