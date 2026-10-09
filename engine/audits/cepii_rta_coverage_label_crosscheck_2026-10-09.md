# CEPII Gravity RTA coverage label cross-check — 2026-10-09

The pinned local `Gravity_csv_V202211.zip` is byte-identical to the SHA-256
`7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`
recorded in `data/manifests/fetch_run_2026-05-15T175027Z.yaml`. Its own member
`Label_rta_coverage_V202211.csv` maps `1=Goods`, `2=Goods & Services`, and
`3=Services`. Known 2015–18 goods-and-services agreement dyads, including
USA–CAN, USA–MEX, FRA–DEU, and AUS–CHN, carry `rta_coverage=2` in the same
CSV. The current builder counts code `2`, matching this version-specific label.

The [CEPII Gravity documentation](https://www.cepii.fr/DATA_DOWNLOAD/gravity/doc/Gravity_documentation.pdf)
and [CEPII working paper](https://cepii.fr/PDF_PUB/wp/2022/wp2022-05.pdf)
describe the semantic categories in a different numeric order: `2=services
only`, `3=goods and services`. That order conflicts with the V202211 CSV
archive's explicit label member. The archive label and linked row codes govern
interpretation of this pinned CSV; the prose discrepancy should be resolved
with CEPII before assigning broader meaning to numeric codes from another
format or vintage.

The affected output names are `gravity_goods_services_rta_partner_count` and
the `goods_services_rta_partner_count` column of `gravity_exposure_panel` in
the May 2026 vintage. A source and result reference scan found **zero** IESET
hypotheses or `engine/runs` using either output. No source file, vintage,
manifest, result, or verdict was changed after this cross-check. The RTA field
is excluded from the new CEPII/WDI hypothesis family pending any further
publisher clarification; that exclusion does not affect the family's separate
`foreign_market_potential`, `fta_market_potential_share`, or
`fta_partner_gdp_share` columns.
