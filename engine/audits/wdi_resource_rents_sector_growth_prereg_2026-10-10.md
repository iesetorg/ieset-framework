# Prospective World Bank natural-resource rents and later sector growth

This is one correlated eight-cell descriptive family: four modeled rent indicators (total, oil, natural gas, minerals) each paired with real manufacturing and real services value-added growth. The registered Dutch-disease pattern is lower later manufacturing growth but higher later services growth. Opposite outcomes can refute each cell. A total-rent indicator includes the component rents, so these are not independent confirmations. Existing UAE/Norway resource case studies do not evaluate this exact broad country-panel pair of prospective outcomes.

## Key-only freeze

Each cell has 860 source-key rows across 215 ISO3 national codes at anchors 1995, 2000, 2005 and 2010; 6,880 rows across eight cells. WDI files include full country×year grids even where values are missing, so this is only an upper bound. Before this registration, no selected numeric value, null mask, sign or estimate was opened. All eight specs, steelmen, this plan, the runner and key roster are committed together. Eight one-file source-lock commits must precede one measured family result commit.

## Frozen model and gates

At t, require rent in [0,100.0] percent GDP, positive real GDP per person and positive real value-added levels for both sectors at t−5, t and t+5. Retain countries with at least 2 complete anchors. Analyze paired-sector samples for each rent. Outcome is log sector growth t→t+5, with own prior t−5→t growth, baseline log sector scale, baseline log real income, country and anchor fixed effects. Country CR1 cluster t(G−1) inference; 99% interval; five country hash-fold omissions. A meaningful effect is 0.03 log points of cumulative five-year growth per +1 pooled SD rent, approximately 3% growth. Frozen floors: 160 rows, 60 countries, 30 rows each anchor, residual rent SD 0.15, residual growth SD 0.04, top 1% rent/growth residual squared-share <=0.35, top country <=0.25, folds >=110 rows/40 countries, 4/5 sign stability. All eight cells, including inconclusive p=1, enter Holm alpha .05. Failed gates remain INCONCLUSIVE.

## Sources, rights and limits

All seven WDI source parquet bytes are SHA-256 pinned; six have exact tracked fetch entries and the real services-value-added source has only a local SHA pin, so its original fetch transaction cannot be independently reconstructed. The World Bank series glossary defines rents as modeled commodity value minus extraction cost, divided by current GDP, and licenses WDI as CC BY 4.0. This packet cites World Bank and distributes only derived summaries, not raw values. Sector growth can reflect global prices, demand, exchange rates, investment and national-accounts breaks. These are descriptive signals with no causal, policy, school, position or featured credit.

| Rent source | Outcome | Registered sign |
| --- | --- | --- |
| NY.GDP.TOTL.RT.ZS Total natural resource rents | NV.IND.MANF.KD Real manufacturing value added | negative |
| NY.GDP.TOTL.RT.ZS Total natural resource rents | NV.SRV.TOTL.KD Real services value added | positive |
| NY.GDP.PETR.RT.ZS Oil rents | NV.IND.MANF.KD Real manufacturing value added | negative |
| NY.GDP.PETR.RT.ZS Oil rents | NV.SRV.TOTL.KD Real services value added | positive |
| NY.GDP.NGAS.RT.ZS Natural gas rents | NV.IND.MANF.KD Real manufacturing value added | negative |
| NY.GDP.NGAS.RT.ZS Natural gas rents | NV.SRV.TOTL.KD Real services value added | positive |
| NY.GDP.MINR.RT.ZS Mineral rents | NV.IND.MANF.KD Real manufacturing value added | negative |
| NY.GDP.MINR.RT.ZS Mineral rents | NV.SRV.TOTL.KD Real services value added | positive |

Primary definitions: https://databank.worldbank.org/metadataglossary/world-development-indicators/series/NY.GDP.TOTL.RT.ZS ; https://data.worldbank.org/indicator/NV.IND.MANF.KD ; https://data.worldbank.org/indicator/NV.SRV.TOTL.KD .
