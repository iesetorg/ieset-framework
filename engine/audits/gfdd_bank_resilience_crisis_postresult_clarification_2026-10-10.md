# GFDD family: post-result unit and evidence clarification

This note was written after the frozen registration (`46fa6022ad5dd9d0c1128b70e73f8612f98aa628`), eight source-lock commits, and measured result (`3b369628552e94239fa63fa02e9b2e181f9365ab`). It does not alter any registered specification, source lock, runner, threshold, sample, estimate, or result packet.

## Effect-size unit

The registration prose uses the ambiguous phrase “0.03 crisis probability points.” The frozen runner sets `MIN_ABS_BETA=0.03`, models an outcome coded 0 or 1, and compares the coefficient with that numeric threshold. Thus the operational threshold is **0.03 on the 0–1 probability scale, or 3 percentage points per one standard deviation higher baseline indicator**. Bank Z-score estimated +0.0430 (about +4.30 percentage points; opposite its registered negative sign), and bank credit/deposits estimated +0.0612 (about +6.12 percentage points; same as its registered positive sign). Neither estimate passes the family-adjusted significance rule. The six other cells fail frozen design gates; they remain in the eight-cell Holm denominator with p=1.

## Onset and sample limit

GFDD `GFDD.OI.19` is an annual systemic banking-crisis dummy sourced to Laeven–Valencia. The registered sample requires a noncrisis year at anchor t and observed binary flags for all of t+1 through t+5. The runner codes an event only for a 0-to-1 transition in that six-year sequence. This is a future recorded crisis-spell onset within the window, not a claim to identify the first banking crisis in each country's history. The two estimable cells have just **10 onset windows in 10 countries** (Z-score) and **11 in 11** (credit/deposits). The 10-event floor was fixed before values were read, yet samples at this floor are thin descriptive evidence. No causal, regulation, school, policy, position, or featured credit follows.

## Source custody and rights boundary

The local GFDD data and series-metadata parquet bytes are SHA-256 pinned in the registration and locks, with the World Bank's public [GFDD dataset](https://www.worldbank.org/en/publication/gfdr/data/global-financial-development-database) and [crisis-series definition](https://databank.worldbank.org/metadataglossary/global-financial-development/series/GFDD.OI.19) recorded as primary documentation. The GFDD component metadata names Bankscope/Orbis and IMF sources for several indicators. The exact original GFDD download transaction lacks a tracked fetch manifest, and component-source redistribution rights were not separately verified. The packets publish derived summaries and hashes, not raw GFDD values. The WDI real-GDP-per-person control has a separately tracked fetch manifest and source hash.
