# Taiwan ITRI frontier-capability effect

**Verdict:** partial — One primary held but not the other (or magnitudes fell short of the strong-form threshold). TFP gap +87 log-pts (threshold +20, rank 1); GDPpc gap +26 log-pts (threshold +50, rank 4).

## Summary

- Treatment year: 1973 (ITRI founded). End of available data: 2019 (PWT 10.x).
- Donor pool: KOR, PHL, MYS, BRA, MEX, ARG, THA, IDN (n=8); 'market-led-only' subpool excludes KOR.

**Primary 1 — TFP cumulative log-change (PWT rtfpna):**

- Taiwan: **+90** log-pts.
- Donor-pool mean: **+2** log-pts.
- Market-led subpool mean (no KOR): **-7** log-pts.
- Gap vs pool: **+87** log-pts (threshold for SUPPORTED: ≥20 log-pts AND TWN rank ≤ 2).
- Taiwan rank in 9-country sample: **1**.

**Primary 2 — Real GDP per capita cumulative log-change (PWT rgdpe / pop):**

- Taiwan: **+184** log-pts.
- Donor-pool mean: **+158** log-pts.
- Market-led subpool mean (no KOR): **+145** log-pts.
- Gap vs pool: **+26** log-pts (threshold for SUPPORTED: ≥50 log-pts AND TWN rank #1).
- Taiwan rank in 9-country sample: **4**.

## Method

Single-treated-unit cumulative-gap test on PWT 10.x productivity
indicators, 1973 (ITRI founding) to 2019 (last PWT year). The
spec originally requested foundry market-share, semiconductor
patent stock, and the Atlas Economic Complexity Index, but none
of those series are present on disk in a Taiwan-inclusive form
(WIPO ip_statistics_data_center has no TWN rows; OWID economic-
complexity-index file is not present; WDI excludes Taiwan
entirely). PWT is the only on-disk publisher with full TWN
coverage 1955-2019 plus the donor pool. TFP is the closest
available proxy for 'frontier capability' the spec asks about;
real GDP per capita is the closest proxy for 'output of a
frontier industry' that flows to the wider economy.

We do not run a synthetic-control fit. With one treated unit,
9-country donor pool, and only ~17 years of pre-period (1955-
1972), a synth fit on long-horizon outcomes is under-identified;
the dispositive question is the magnitude of Taiwan's gap to a
comparable-income peer mean, which the cumulative-log statistic
answers directly.

## Caveats

- KOR is itself a developmentalist case (HCI drive, chaebol-
  state coordination), not a clean control. The 'market-led
  subpool' diagnostic strips KOR out so a reader can see both
  framings; the headline gap is to the full 8-country donor pool.
- The treatment is 'ITRI strategy' but PWT productivity captures
  *all* sources of Taiwan's TFP catch-up — Cold War US technology
  transfer, returning diaspora engineers, the global pure-play
  foundry shift. The replication cannot isolate the ITRI channel.
- PWT ends 2019, so the 2020s semiconductor boom (TSMC 3nm/N2,
  CHIPS Act spillovers) does not enter the test.
- This is an associational descriptive comparison, not a causal
  identification. The verdict labels a magnitude pattern, not a
  causal estimate.

## Data

- pwt:rtfpna (TFP at constant national prices, 2017 = 1)
- pwt:rgdpe (real GDP at chained PPPs, expenditure-side)
- pwt:pop (population, millions)
