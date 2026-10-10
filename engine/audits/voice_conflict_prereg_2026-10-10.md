# Blind registration: voice and accountability and later state-based conflict

**Family:** `voice_accountability_conflict_forward_2026_10_10`, one
retrospective descriptive test. WGI voice-and-accountability **exposure** and
WDI real-income control values were inspected before this registration. Only
OWID/UCDP country and year **keys** were opened. No selected conflict count,
count-null mask, fitted coefficient, sign, or verdict was read. This
first-addition registration, later exact source lock, and measured run must be
separate commits.

## Question, interpretation, and fixed periods

Across countries with complete keys, does a larger gain in the World Bank WGI
**Voice and Accountability estimate** from `t−4` to `t` predict a lower
probability that OWID/UCDP records **any state-based conflict** in the country
during `t+1` through `t+4`? Anchors are 2004, 2008, 2012, 2016, 2020. The
outcome windows are adjacent and do not overlap. The WGI exposure is in
standard-estimate points, not 0–100 governance-score points; a one-point
change is large. The OWID outcome is a binary indicator derived from its four
annual count columns: internationalized intrastate, non-internationalized
intrastate, extrasystemic, and interstate. A missing category value never
becomes zero. The binary outcome captures recorded state-based conflicts
meeting UCDP/PRIO inclusion criteria; it omits non-state and one-sided
violence. It is neither a battle-death count nor an incidence rate of all
political violence.

The registered directional slope is negative. A country-clustered linear
probability slope **≤−0.15** probability point per +1 WGI estimate point with
two-sided `p≤0.01` SUPPORTS the narrow descriptive prediction. A slope
**≥+0.15** with that p REFUTES it; other estimable results are PARTIAL. One
test uses family alpha 0.01. This local threshold does not account for
selection across the wider IESET archive or earlier governance/conflict
questions.

## Pinned source custody and key-only support

| Role | Exact raw SHA-256 | Tracked fetch manifest SHA-256 |
| --- | --- | --- |
| WGI `GOV_WGI_VA.EST` | `c52d36e90b8b99eaf9d1d5992f4e35d3c145b1c3ef8afb74c060c96097d4f979` | `fetch_run_2026-05-05T200056Z.yaml` `a571d660fd359d245176b77e595b59923a90a1e40a799ea56c13f001a7b09945` |
| WDI real GDP per person `NY.GDP.PCAP.KD` | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | same WDI manifest |
| OWID/UCDP `number-of-state-based-conflicts` | `f79099534287e0b42d93b9ab622eec5e0d8d47c02eebd5dbf79f40138f8f3885` | `fetch_run_bootstrap_2026-04-30T121833Z.yaml` `e4eba4196e874aa69112f5e93420aa1daeffe64225e73ff536b336e33dec282e` |

Raw vintages stay in the ignored local source corpus. The runner verifies
their exact hashes and manifest records before source locking or measurement;
the branch contains only a key roster and aggregate results. The frozen
`data/pinned_evidence/voice_conflict_2026_key_roster.csv` has SHA-256
`8be7467188c3beb3753053031308d12163e3418a87670d8c60f9234ab2c8d663`.
It contains **939 country/anchor rows across 188 ISO3 countries**. Keys
require every OWID country-year from `t−3` through `t+4`, finite WGI
exposure in `[−3,3]` and positive WDI real income with blank/null status at
`t−4,t`, absolute WGI four-year change no more than 2 points, and at least
four key anchors per country. Key presence says nothing about nonmissing
conflict counts. Exposure-only support is **88 rows/73 countries** with WGI
rise ≥0.3 and **233 rows/152 countries** with absolute WGI change ≤0.05.

## Frozen model and no-go gates

After the later committed lock, read only the four named OWID count columns.
Each of the eight annual category vectors must contain four finite,
nonnegative integers, each ≤100. Invalid or missing category data exclude
that country/anchor window; no interpolation or zero filling. Require at least
four complete anchors per retained country. Future `y=1` when at least one
state-based conflict was recorded in `t+1..t+4`; otherwise `y=0`. The model
uses the WGI change `t−4→t`, WGI level at `t−4`, an indicator of any conflict
in `t−3..t`, `log(1+sum of prior conflict counts)`, log real income per person
at `t`, preceding four-year log-income change, country fixed effects, and
anchor fixed effects. Fit a **linear probability projection** with
country-cluster CR1 small-sample covariance and two-sided Student `t(G−1)`.
The slope is descriptive and fitted probabilities need not lie within `[0,1]`.

Require **750 complete rows, 150 countries, all five anchors**; at least
**60 material-rise rows across 45 countries** and **100 flat-exposure rows
across 60 countries**; at least **100 future-conflict windows across 25
countries** and **100 no-future-conflict windows across 25 countries**. Fail
on model rank deficiency, nonfinite or nonpositive clustered uncertainty, or
residualized-exposure squared weight above 25% in the top 1% of rows, 15%
in one country, or 35% in one anchor. Any failure yields **INCONCLUSIVE
archive**, even when a coefficient could otherwise be estimated. A
gate-cleared SUPPORTED, REFUTED, or PARTIAL result receives public
**descriptive calibration only**. Every outcome has zero causal, policy,
school, position, and featured credit.

WGI is a perception-based composite estimate; its scores and input sources
can change. Conflict can affect governance perceptions and vice versa.
Transitions, repression, settlements, neighboring wars, development, and
outside intervention can confound the association. The temporal split,
controls, and fixed effects do not identify a peace-building intervention.
The WGI and OWID source manifests record CC BY licenses; cite both data
providers and UCDP/PRIO provenance when displaying derived results.

Definitions: [World Bank WGI](https://www.worldbank.org/en/publication/worldwide-governance-indicators),
[World Bank WGI methodology](https://www.worldbank.org/en/publication/worldwide-governance-indicators/documentation),
[OWID state-based conflict chart](https://ourworldindata.org/grapher/number-of-state-based-conflicts),
[UCDP downloads](https://ucdp.uu.se/downloads/).
