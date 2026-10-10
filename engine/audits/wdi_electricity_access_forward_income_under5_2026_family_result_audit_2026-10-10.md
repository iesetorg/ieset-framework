# Electricity-access forward family: custody and result audit

## Registration and correction history

The original local-only registration was committed before any selected values were read and passed the full schema check of **6,319** specifications. In the sanitized ancestry, the identical specification and steelman files entered at `3afae0fedaeb05108a40cd65a61353ceadea8ad0`; no treatment, outcome, source, window, threshold, or family rule was changed. The metadata-only source lock at `378172e261446d2cb28493f11b2dd26b21efaba5` pins the same three WDI source hashes, selected country/year key hashes, and **216** ISO3/XKX candidate economy keys. It omits an unnecessary workstation-root field from an earlier local-only lock. This custody rewrite occurred **after a provisional result had been observed** and is not a new blind discovery.

The first local runner attempt stopped at a Git path-following chronology false alarm **before selected values were opened**. After that check was corrected, an uncommitted provisional run exposed a mismatch: its child-health sample checked 2015 income only, while the frozen exclusion rule requires positive real income in **2005, 2015, and 2023**. Its 190-economy child-health estimate (beta +0.711184, HC3 SE 0.306999, p 0.021629) is invalid for the registered sample and receives no credit. The committed replacement runner `02d9a56c2a97ebb60b3981571afa58c60231fcd2` enforces all three income years for both endpoints. The corrected result commit is `a0ae9aea36c729a17a9b2d5a838c63c780edc576`. The post-observation repair follows the precommitted exclusion text and tightens, rather than relaxes, sample eligibility.

## Registered family results

| Endpoint | Complete economies | Exposure floor | Primary estimate per 10-point access gain | Frozen-gate verdict | Public tier |
| --- | ---: | --- | --- | --- | --- |
| Annualized 2015–2023 real GDP-per-person growth | 194/216 | 53 economies gained >=10 pp; IQR 10.925 pp | beta −0.017076 annual log-growth pp; HC3 SE 0.241944; p 0.943809 | All floors pass, influence 0.059786, 194/194 leave-one-out fits. **PARTIAL.** | Calibration, visible |
| Annualized 2015–2023 under-five mortality decline | 186/216 | 53 economies gained >=10 pp; IQR 11.475 pp | beta +0.787387 annual log-improvement pp; HC3 SE 0.305018; p 0.010635 | All floors pass, influence 0.062698, 186/186 leave-one-out fits and every leave-one-out beta positive. **SUPPORTED** under beta >=0.5 and Bonferroni two-sided p <=0.025. | Calibration, visible |

Both corrected runs replayed byte for byte across all nine standard artifacts. Independent NumPy least-squares and HC3 sandwich calculations matched the saved coefficients and standard errors within `1e-9`. The strict registration check reports **829** verified pairs; the live evidence-tier audit counts **579** public cases, up **two** from this branch's remittance baseline of 577. These are two distinct outcomes in **one independent evidence family**. They add zero featured, causal, policy, school, or position credit. The old whole-window electrification claims remain unchanged.

## Interpretation and reproduction

From a checkout with the three pinned local WDI vintages, run `python3 scripts/run_wdi_electricity_access_forward_income_under5_2026_family.py --replay --source-root <SOURCE_ROOT>`. The source SHA-256 values are verified before values are read. Electricity access is a measured development outcome as well as a possible input. This baseline-adjusted forward association does not identify a grid investment effect, and unmeasured development, health-system, sanitation, conflict, and income changes can explain the child-health pattern. The provisional sample result is excluded from all counts.
