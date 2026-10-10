# Internet diffusion and later labour outcomes — prospective registration

The five-cell family asks whether earlier national Internet-use growth predicts later changes in unemployment, total labour-force participation, working poverty, the female/male mean hourly earnings ratio, and the female-minus-male participation gap. The first, second, third and fifth are percentage rates or gaps; the earnings ratio is a within-country/year/source local-currency ratio. The outcomes have distinct labour meanings but share the same exposure and overlapping ILO sources. Prior Internet→business registrations, services employment share, high-tech exports and patenting are different directed questions, not independent confirmation. This selected family is descriptive.

## Value-blind source-key freeze

Anchor years t are 2005–2017, so outcomes end in 2019 before COVID. The roster has 9,052 cell-specific structural country-year-source keys. Each ILO cell requires one identical source code at t−2, t and t+2; gender cells require both sexes within the same source/year. WDI files are broad country×year grids even where numeric values are null, so the counts below are upper bounds. Before this registration no selected numeric value, status/null mask, outcome change, sign or estimate was opened. This plan, five specs and steelmen, runner and key roster form one first-add commit. Five separate one-file source-lock commits must follow before any selected value access.

| Later labour outcome | Structural windows / countries | Registered sign | Meaningful beta per +10 Internet points |
| --- | ---: | --- | ---: |
| unemployment rate, age 15+ | 2418 / 186 | - | 0.35 percentage points |
| labour-force participation rate, age 15+ | 2418 / 186 | + | 0.35 percentage points |
| working poverty rate among employed people, age 15+ | 1521 / 117 | - | 0.35 percentage points |
| female-to-male mean hourly earnings ratio | 277 / 41 | + | 0.015 log points |
| female minus male labour-force participation gap, age 15+ | 2418 / 186 | + | 0.35 percentage points |

## Frozen measurement and failure gates

Exposure is (Internet-use percent at t minus percent at t−2)/10. Future response is selected ILO outcome change t→t+2; control its own t−2→t change and level at t plus log real GDP per person at t. Add country and anchor-year effects, two-way country/year clustered CR1 uncertainty, two-sided t with min(country,year clusters)−1 degrees of freedom, 99% descriptive intervals. Keep countries with at least five complete anchors. Require Internet and rate values in [0,100], positive wages, and positive real income. The female/male wage ratio is logged before differencing; female-minus-male participation remains a percentage-point gap. Exact ILO source continuity is required within each outcome window.

Coverage gates are cell-specific because annual national earnings surveys are much sparser than modelled ILO rate panels, but they are frozen before values: unemployment/total participation/gender participation gap ≥500 rows, ≥50 countries, ≥10 years; working poverty ≥400/40/10; hourly earnings ratio ≥150/18/10. The complete-case residual exposure SD must be ≥0.15 units (10 Internet points); residual outcome SD ≥0.15 percentage points for rates/gap, ≥0.005 log points for wages. For both residualized exposure and outcome, top 1% rows may contribute at most 30% squared variation, one country at most 18%, one year at most 35%. Five SHA256(country) mod 5 omission folds need ≥350 rows/35 countries for broad rate and gap cells, ≥280/28 for poverty and ≥105/13 for earnings; four of five slopes must match the registered direction. Rank or two-way cluster uncertainty failure is INCONCLUSIVE. Holm α=0.05 includes all five cells and assigns p=1 to failures. Material opposite sign with Holm and fold support is REFUTED; method-valid but threshold-missing is PARTIAL. No post-result substitution.

## Sources, rights and limits

All six raw parquets and four tracked fetch manifests are SHA-256 pinned. The two World Bank WDI sources and all four ILOSTAT sources are CC BY 4.0 in their exact fetch manifests. ILO unemployment and labour-force participation sources here use XA modelled source codes; working poverty is a modelled SDG rate; hourly earnings are national source observations in local currency. Only derived results are tracked, not raw source values. Source definitions: https://data.worldbank.org/indicator/IT.NET.USER.ZS ; https://ilostat.ilo.org/data/ ; https://ilostat.ilo.org/topics/working%20poverty/ ; https://ilostat.ilo.org/methods/concepts-and-definitions/description-wages-and-working-time-statistics/ .

Internet diffusion, income, education and labour-market change can share causes. The wage ratio is unadjusted for occupation or hours composition, and source continuity does not eliminate methodology changes. Thirteen years are thin for year-cluster inference. Holm is local to this family, not correction across all IESET exploration. All causal, policy, school, position and featured credit remains zero.
