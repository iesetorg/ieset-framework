# Result card — Canada real disposable income post-2015 (PROXY)

**Verdict:** WEAKENED — both proxy specs (GDP-pc PPP β=-0.034 p=0.050; GDP-pc constant LCU β=-0.035 p=0.047) show negative Canadian post-2015 trajectory, but the YAML's true two-spec rule requires OECD household disposable income + WDI GNI-per-capita PPP, neither of which is present in the local vintages. Both available proxies measure pre-tax-and-transfer aggregate output rather than household disposable income. Verdict capped at WEAKENED pending v1.1 OECD Household Dashboard fetcher.

## Data gate

The YAML's primary outcome is OECD household net disposable income per capita.
That dataflow is not present in the local vintages and the URN was flagged in
the YAML as v1.1 fetcher requirement. The YAML's secondary proxy WDI GNI per
capita PPP (NY.GNP.PCAP.PP.KD) is also not present in vintages. This run
substitutes the closest available proxy — WDI GDP per capita PPP — and a second
proxy WDI GDP per capita constant LCU. Both are aggregate-output proxies that
do NOT net taxes, transfers, or cross-border income flows. Findings are labelled
PROXY and capped at WEAKENED until OECD Household Dashboard ships.

## Proxy spec 1 — log GDP per capita PPP (constant intl $)

| Term | Estimate | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| canada_post_2015 | -0.0343 | 0.0174 | [-0.069, -0.000] | 0.050 | -1.98 |

n = 168 country-years.

## Proxy spec 2 — log GDP per capita (constant LCU)

| Term | Estimate | SE | 95% CI | p | t |
|---|---:|---:|:---:|---:|---:|
| canada_post_2015 | -0.0345 | 0.0172 | [-0.069, -0.000] | 0.047 | -2.01 |

n = 168 country-years.

## Caveat per YAML pre-registration

Aggregate-output proxies cannot speak to the transfer-share decomposition channel
(CCB enhancement, CPP enhancement, COVID transfers, $10/day childcare) which the
YAML flags as the most important interpretive guard. If those transfers fully
offset pre-tax wage weakness in household disposable income, the household-stagnation
framing would be inaccurate even if aggregate-output stagnation is real. This
decomposition cannot be performed at v1; flagged for v1.1 OECD Household Dashboard run.

## Provenance

Reproduces from vintages in `manifest.yaml`. See `replication.py`.
