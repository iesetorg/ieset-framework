# OWID four-year conflict: eight registered descriptive contrasts

This family asks whether a recorded state-based conflict in a four-year country window coincides with changes in eight separately named development and economic outcomes. The observation is associative and retrospective. It does not estimate a conflict intervention, policy effect, school score, or independent eightfold replication. The eight outcomes share source and country-year structure; their Bonferroni correction is local to this family, not to IESET's whole research archive.

The eight specifications and value-blind ISO3 key roster first entered Git together at `d332690dd40a3132dec44a465b356b76a38dd119`. The original analysis runner first entered at `cdd57aae47b5adfef9bfee0ee3fee104d523ec18`. Eight exact case source locks were committed separately and sequentially: `10319877e04ae062ccbcb3e3091e2976e78b213b`, `c2a22d16492c6cfbe57c8626b36488ef1a440e1e`, `2af5b8b8f44fd5981dca0d3933fbb05c088816c0`, `ab5e1926cf04178a9997efd8ef1d0dcac2eff910`, `f29f808bc5bc86c1f823dc1d9f2e6462f5f1671b`, `21cadbfd55960e1ecdaf7c29d23a6a33a3f9a355`, `d4f84a662fd54d9846f757bd4bf5638adf9da6f7`, and `bee319b7d3567654f4c38630780f3adc6cf2a680`. The locked source and key hashes are in each case's `.source.json` and saved evidence packet. All registrations and locks precede the first measured invocation.

Two post-lock implementation repairs are retained as separate immutable commits and audits. The geography adapter `a015f3753b26a936df8b4c2feead99dc419fa483` restricted physical source loaders to the preregistered national ISO3 roster; its erratum documents the two stops before selected outcome access. The first run through that adapter fitted and printed four UNDP `PARTIAL` results, then stopped at the WIPO physical indicator guard. The WIPO alias adapter `6840df06f61e0b2c435d361d01ce559149d93915` and its erratum document that opened-result boundary and the key-only inspection of every remaining WIPO/WITS/WDI selector. Neither adapter changes the frozen exposure, outcome transformation, model, coefficient test, sample floor, influence cap, or public-credit rule.

| Registered outcome | Complete country-windows / countries | Frozen verdict | Two-sided p, if estimable | Principal limit |
| --- | ---: | --- | ---: | --- |
| UNDP life expectancy | 1,351 / 193 | PARTIAL | 0.01400 | Misses family p≤0.00125 |
| UNDP mean years of schooling | 1,240 / 187 | PARTIAL | 0.64506 | Misses family p≤0.00125 |
| UNDP expected years of schooling | 1,284 / 189 | PARTIAL | 0.17992 | Misses family p≤0.00125 |
| UNDP GNI per capita | 1,318 / 189 | PARTIAL | 0.09408 | Misses family p≤0.00125 |
| WIPO resident patents per million | 472 / 83 | INCONCLUSIVE | — | 24 within-country switchers, below frozen minimum 25; no qualified coefficient |
| WITS exported HS6 breadth | 922 / 146 | PARTIAL | 0.88476 | Misses family p≤0.00125 |
| WITS export-market concentration | 932 / 147 | PARTIAL | 0.15087 | Misses family p≤0.00125 |
| WDI fixed-investment GDP share | 1,034 / 154 | PARTIAL | 0.04625 | Misses family p≤0.00125 |

The seven estimable cases passed every frozen sample, model, and residual-exposure concentration gate; all are `PARTIAL`, including the smaller nominal p values, because none passed the prespecified eight-test family threshold. The patent case remains archived as `INCONCLUSIVE`, and its failed switcher floor was not relaxed. This contributes seven possible descriptive public calibrations only after the central evidence-tier, preregistration, and site checks; it adds zero causal, policy, school, position, or featured credit. No source-vintage or outcome selection was changed after viewing results.

All eight result directories were produced in one invocation of `python3 scripts/run_owid_conflict_multidomain_2026_wipo_alias_adapter.py --run --source-root <LOCAL_HOME>/IESET`. Each packet's `reproduction.result_sha256` matches its saved `diagnostics.json`. A second invocation with `--verify` against the same exact pinned cache reproduced all seven files in each of the eight directories byte for byte and printed `exact replay passed for all eight cases`. Pinned raw Parquet files remain ignored in the source cache; this branch records their exact hashes and the manifest hashes, not their source values.
