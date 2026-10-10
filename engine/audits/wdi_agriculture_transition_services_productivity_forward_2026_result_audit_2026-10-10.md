# Agricultural transition, services productivity, and later growth: v2 result audit

## Direct question and limits

The archived \`agriculture_employment_transition_productivity_panel\` claims that a fall in agricultural employment share predicts stronger per-capita growth only when manufacturing or services productivity rises. Its generic run substituted services GDP share as treatment and the total employment rate as outcome, so that old PARTIAL estimate did not test the stated variables. New ID \`wdi_agriculture_transition_services_productivity_forward_v2\` directly measures the 2005–2015 agricultural-employment-share decline and a concurrent services-productivity-rise condition, then tests later 2015–2023 real GDP-per-person growth. It is a narrower forward test of the services branch only. The old verdict, manufacturing branch, contemporaneous claim, and policy/school mappings remain unchanged.

Real services productivity is constructed as real services value added divided by total employed persons times the services employment share. The WDI sector measures and ILOSTAT total-employment count can differ in classification and revision practice. This is an explicit measurement limit, not a causal design.

## Freeze and source custody

The full specification, steelman, and blind key-only plan first appeared in registration commit \`a4fd27986d4b2296a59108d666070ec4cf32bfee\`. \`scripts/validate_specs.py\` passed on that committed registration before any selected numeric values or null masks were opened (6,321 specs). Metadata-only source lock \`9d61a8b77776f3fe8ce7c6efc810e7e7fc0e9bac\` fixed 186 ISO alpha-3 or XKX national areas, source schemas, SHA-256 hashes, and selected key digests. The runner first appeared in \`98a4392b7f9d682567738985348f2031de2ac24f\`, before result commit \`cd454b26b985b43bd7a0aab1f0e09746c15dcd02\`. The first-registration check reports the new ID as strict and verified.

The five source roles use repository-relative locked paths: WDI agricultural employment share \`SL.AGR.EMPL.ZS\`, WDI services employment share \`SL.SRV.EMPL.ZS\`, WDI real services value added \`NV.SRV.TOTL.KD\`, ILOSTAT total employed persons \`EMP_2EMP_SEX_AGE_NB\` (SEX_T, AGE_YTHADULT_YGE15), and WDI real GDP per person \`NY.GDP.PCAP.KD\`. Four preperiod files each have 372 selected country/year keys; income has 558. The data corpus is supplied at replay time through \`--source-root <SOURCE_ROOT>\`; no machine-specific root is tracked.

## Frozen gates and result

Of 186 source-key candidates, 156 passed all numeric-value rules. Overlapping exclusions: real services value added 28, income 9, and none for the two employment-share series or ILOSTAT total employment. Services productivity rose in 125 and did not rise in 31. Fifty-two had an agricultural employment-share decline of at least 5 percentage points. The within-group exposure IQRs were 5.157 and 4.277 points, both above the 2-point floor. All sample and variation gates passed.

The interaction coefficient was **+0.5978 annualized log-growth percentage point per 10-point agricultural-share decline** (HC3 SE 0.7130, two-sided p=0.4032). The slope among services-productivity-rising areas was +0.5783 (p=0.2839); the non-rising slope was −0.0195 with a 95% upper bound of +1.1675. The maximum single-area share of squared residualized interaction was 0.180, below the frozen 0.20 cap. All 156 leave-one-area-out fits succeeded and retained positive interaction and rising-group slopes. The estimates missed the frozen significance and non-rising upper-bound requirements: **PARTIAL**, not support for the conditional claim.

The frozen runner reproduced all nine artifacts byte-for-byte. An independent NumPy least-squares and HC3 sandwich computation matched the interaction coefficient, SE, p-value, rising slope, rising-slope SE, and p-value to floating-point precision. The temporary preregistration index reports 831 strict pairs; the temporary evidence-tier audit labels this ID \`calibration\`, \`public_visible: true\`, \`registration_status: verified\`, with no exclusion reason. In this source branch, public-visible cases rise **580 → 581 (+1)**. This is one independent family with zero causal, policy, school, position, or featured credit.

Reproduction from the repository root with the pinned data corpus available: \`python3 scripts/run_wdi_agriculture_transition_services_productivity_forward_2026.py --replay --source-root <SOURCE_ROOT>\`. Generated preregistration, evidence, census, and web indexes are left for consolidated regeneration and are not committed here.
