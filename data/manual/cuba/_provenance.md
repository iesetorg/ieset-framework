# Cuba manual data — provenance index

Hand-curated Cuba-specific series consumed by the
`cuba_socialist_economy_stagnation_1960_2023` canonical-case multi-metric run.
Each series is sourced from academic monographs, Cuban official-gazette
regulations, or first-line journalistic reporting. The fetcher
`data.fetchers.cuba_manual` reads the YAML inputs in this directory and
writes parquet vintages under `data/vintages/cuba_manual/` so the
multi-metric runner can pick them up via the standard `(publisher:series)`
source-string convention.

## Series

| Series                       | Input file                       | Provenance file                    | Output (CUB row) |
|------------------------------|----------------------------------|------------------------------------|------------------|
| libreta_persistence          | `libreta_persistence.yaml`       | `libreta_persistence.md`           | years_active = (current_year - 1962 + 1) |
| monetary_regime_events       | `monetary_regime_events.yaml`    | `monetary_regime_events.md`        | event_count = 4 (1961, 1994, 2004, 2021) |
| mlc_retail_persistence       | `mlc_retail.yaml`                | `mlc_retail.md`                    | years_active = (current_year - 2019 + 1) |

## Refresh cadence

- **libreta_persistence**: bump `end_year` once per calendar year if the
  libreta is still in force (verify via OnCuba / 14ymedio reporting and the
  Gaceta Oficial RFP archive).
- **monetary_regime_events**: append-only when a new regime change is
  declared (e.g. a future re-monetization).
- **mlc_retail_persistence**: bump `end_year` once per calendar year while
  MLC stores remain operational.

## Why this exists

The runner `scripts/run_multi_metric_checklist.py` short-circuits sources
prefixed `manual:` (treats them as missing data for safety). We register a
real publisher namespace `cuba_manual` instead and route the regulatory /
academic indicators through the standard fetcher pipeline. This keeps the
manifest reproducible (parquet sha256 pinned) and the threshold evaluation
auditable.
