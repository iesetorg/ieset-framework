# OECD PDB sector productivity to next-year real compensation — locked results

Three sectors share the two exact sources, country roster and design. Holm adjustment covers this family only. These are descriptive calibrations with zero causal, policy, school, position and featured credit.

| Sector | Verdict | Rows / countries | Beta | Two-sided p | Holm p | Failed gates |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Manufacturing | PARTIAL | 723 / 27 | -0.014482623069673961 | 0.42860038865596617 | 0.6365960050258174 | none |
| Wholesale and retail trade | PARTIAL | 707 / 26 | 0.03306436436469029 | 0.3182980025129087 | 0.6365960050258174 | none |
| Information and communication | PARTIAL | 724 / 27 | 0.03304809020614474 | 0.17254085777245742 | 0.5176225733173723 | none |

Registration `bfe1c4cd1e40c44a76ae2ed668844e9f69e90435`; final source lock `e6e0801388167120c196d81984bcbc01db23b10c`. PDB SHA-256 `3546c5c773a15933c439a9975bb6436c13f2df1ae250c75419340c2c91032b5c`; WDI CPI SHA-256 `dd4c747352eb0ceab2600a6b6ffeeda048c6080f0097bb6927d9966e5a3242a0`; frozen roster SHA-256 `d3e0e611f9f3407efbc646a5b2d00b3a1a3ccd685d15fd37136d215082cea18b`.

Exact replay: `python3 scripts/run_oecd_pdb_sector_real_compensation_2026_metadata_fix.py verify --source-root /path/to/IESET`.

Real compensation per employee uses OECD nominal compensation growth deflated by WDI broad CPI. Worker composition, hours, wage bargaining and sector demand can confound the relation; these results do not estimate an intervention or median wage effect. Raw and country-level values are not committed.
