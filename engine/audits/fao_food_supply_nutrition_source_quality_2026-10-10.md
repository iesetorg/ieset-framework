# FAOSTAT food-supply/nutrition source-quality and credit review

The eight registered national pathways were measured once against the pinned FAOSTAT ZIP. All eight are **PARTIAL** under the frozen 0.01/8 family threshold (`p <= 0.00125`); none supports or refutes its registered direction. The pathways overlap in both country-years and endpoints. The 4,716 admitted row appearances below are not 4,716 independent observations.

## Source flags in every admitted pair

FAOSTAT's source flag codebook defines `E` as **estimated** and `X` as **from an external organization**. The frozen selector allowed `A/E/X` without reading row flags at registration. On the first measured run, *every* admitted food-supply exposure carried `E`; *every* admitted nutrition endpoint carried `X`. No direct-survey or official `A` observation entered these fits. The endpoint estimates are FAO-redistributed UNICEF/WHO/World Bank child indicators or WHO women's anemia estimates. Food supply represents national availability, not an individual's consumption.

| Registered pathway | Verdict | Country-wave pairs / countries | Estimated exposure `E` | External endpoint `X` | Beta, outcome pp per exposure unit | Two-sided p |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Energy adequacy → stunting | PARTIAL | 554 / 139 | 554 | 554 | -0.86201 | 0.09628 |
| Energy adequacy → low birthweight | PARTIAL | 542 / 136 | 542 | 542 | -0.15709 | 0.03420 |
| Total protein → stunting | PARTIAL | 568 / 147 | 568 | 568 | -0.05721 | 0.89960 |
| Total protein → low birthweight | PARTIAL | 566 / 145 | 566 | 566 | -0.03031 | 0.64890 |
| Animal protein → women's anemia | PARTIAL | 672 / 173 | 672 | 672 | -0.13112 | 0.33464 |
| Animal protein → low birthweight | PARTIAL | 566 / 145 | 566 | 566 | +0.01476 | 0.73960 |
| Staple share → women's anemia | PARTIAL | 672 / 173 | 672 | 672 | +0.26114 | 0.47673 |
| Fat supply → child overweight | PARTIAL | 576 / 149 | 576 | 576 | -0.46838 | 0.00895 |

All eight passed the frozen complete-case, country, anchor, material-change, rank, uncertainty and residual-concentration gates. A nonzero beta or a nominal `p < 0.05` is not a familywise finding. National ecological associations cannot establish individual nutrition or causal effects; the two source types, annual model smoothing, shared national drivers and unmeasured confounding limit interpretation.

## Credit rule and custody

The current `scripts/audit_evidence_tiers.py` has no blanket exclusion for estimated `E` or external `X` FAOSTAT flags. It classifies a strictly registered, publicly auditable **descriptive** result as calibration when its other evidence gates pass. The same audit's `school_score_eligible_for_public_run` function requires an explicit `correction.school_score_eligible: false` or `school_score_credit: 0` to exclude even a visible calibration record from school wins, losses, tested counts and scores. Both fields are now in every diagnostic packet, with zero causal, policy, position and featured credit. The local scoped audit recomputed actual Git registration history and returned `verified`, `calibration`, and `school_score_eligible=false` for all eight, with no public exclusion or integrity-detector finding. The integrated public tier audit remains the authority after merge; a failed public gate means **archive**, despite an estimable PARTIAL result. Neither the source flags nor this annotation can elevate a record.

Chronology is preserved in separate commits:

1. `2bf950bbaaaf65d339a9b4993a7fa0b7864530e6` — eight specs, key-only roster, preregistration and frozen numerical runner, before selected values or row flags were opened.
2. `8e4c08c3cba3f274a3e2f64ae9d5692e6c4171ae` — exact raw ZIP source lock, before measurement.
3. `2814f80bac542b6feb52e15e590315352302d66c` — untouched first measured packets and family results.
4. The later output-only adapter adds source-quality and zero-credit metadata to each packet; it checks original bytes against commit 3, replays the frozen numerical calculation, and verifies amended packet bytes. It changes no coefficient, p value, sample, gate or verdict.

Pinned source: SHA256 `725f3592b383fd1a6896981c29c6db9ed85cb34f1687afed3cf4f86c7fef4de4`; [FAOSTAT catalog](https://data.fao.org/catalog/dataset/955d6564-40a9-48b4-b51b-f19d65bb3539); [FAO statistical database terms](https://www.fao.org/contact-us/terms/db-terms-of-use/en). These source records receive descriptive calibration visibility only if the final public tier audit grants it, and **zero school, causal, policy, position and featured credit**.
