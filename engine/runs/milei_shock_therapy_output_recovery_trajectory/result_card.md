# Milei shock-therapy output recovery trajectory

**Verdict:** partial - Level-recovery legs hold (2025 = +3.0%, 2026 = +6.4%) but ARG cumulative 2024-2026 log-deviation +8.1% does NOT exceed peer mean +14.1% — recovery, but not faster than the LatAm peer pool. Note: 2 of 3 post-period years (2025, 2026) are WEO projections (last realised year = 2024).

## Summary

- ARG real-GDP log-level index, 2024 = -1.3%, 2025 = +3.0%, 2026 = +6.4% (2023 = 0% baseline).
- Spec leg A (2025 floor >= -4%): **PASS**.
- Spec leg B (2026 level recovery >= 2023): **PASS**.
- Spec leg C (ARG cum 2024-2026 > LatAm peer mean): ARG = +8.1%, peer mean = +14.1% — **FAIL**.
- Peer-by-peer cumulative log-deviation 2024-2026: BRA=+16.5%, CHL=+14.6%, COL=+11.9%, MEX=+7.0%, PER=+19.8%, URY=+15.1%.

## Method

Dispositive primary test in three legs translated from the spec's
quarterly thresholds to annual under the spec.notes-authorised
annual fallback (quarterly real-GDP series for the LatAm peer pool
are not on disk; the spec explicitly anticipates this).

Annual real-GDP percent change (IMF NGDP_RPCH) is converted to a
log-level index pinned to 0 at 2023 (the pre-Milei baseline year
the spec uses) by cumulating log(1 + g_t/100). The three
thresholds are then evaluated directly:

1. ARG 2025 log-gap vs 2023 must be >= -0.04 (4 log points).
2. ARG 2026 log-gap vs 2023 must be >= 0.00 (level recovery).
3. ARG cumulative log-deviation 2024-2026 must EXCEED the
   unweighted mean of the LatAm peer pool over the same window.

## Caveats

- IMF WEO projection content. As of run date 2026-04-27, the last
  unambiguously realised year in NGDP_RPCH is **2024**.
  Years 2025, 2026 are WEO projections, not outturns. The verdict
  is therefore the joint hypothesis (claim is correct AND IMF
  projects it correctly). When the realised-data window extends,
  re-run with the same script.
- Annual fallback was used in lieu of quarterly GDP per spec.notes.
  Synthetic-DiD with permutation inference (the spec's primary
  estimator) is not run because the annual sample (one ARG
  observation per post-treatment year, six donors) is too thin
  for permutation p-values to be informative; the level-and-peer
  comparison above is the legitimate annualised analogue.

## Data

- imf:NGDP_RPCH (annual real-GDP % change, includes WEO projections)
