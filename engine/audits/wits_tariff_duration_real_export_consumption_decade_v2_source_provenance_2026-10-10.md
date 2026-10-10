# Local source provenance: WDI real export-growth vintage

This note is part of the first-addition blind registration for
`wits_tariff_duration_real_export_consumption_decade_v2`. It was prepared
from paths, file bytes, Parquet footer/schema, and publisher/fetcher
configuration only. No selected `value`, null mask, observation-status
field, coefficient, or model fit was opened.

## Preserved file and custody boundary

- Exact selected local file: `data/vintages/world_bank_wdi/NE.EXP.GNFS.KD.ZG@2026-05-03T054026Z.parquet`
- SHA-256 of original local Parquet bytes: `c6360d9b71f75398e6566284fbda6fd14ed94f2ac31aaf1ba588611b9e08913b`
- Byte length: 99279; Parquet rows: 17556; row groups: 1.
- An earlier same-day full file at `data/vintages/world_bank_wdi/NE.EXP.GNFS.KD.ZG@2026-05-03T053751Z.parquet` has the same byte SHA-256. The 05:35:04 file has only 2,000 rows and is not the selected vintage.
- `data/manifests/baseline_pull.yaml` names the indicator but is a pull configuration, **not** an exact fetch-time manifest. No matching `fetch_run_2026-05-03*.yaml` or original HTTP payload was found locally. This gap means the preserved file's World Bank origin cannot be independently proven from a contemporaneous fetch receipt.
- The file is ignored by Git and must remain available at the exact path and hash for lock creation, run, and replay. Loss or byte drift blocks the registered runner; a fresh API download is not a substitute.

## Publisher and local extraction method

`data/fetchers/publishers.yaml` registers `world_bank_wdi` as World Bank World
Development Indicators with endpoint `https://api.worldbank.org/v2`, catalog
`https://data.worldbank.org/indicator`, revisable vintage behavior, and
fetcher `data.fetchers.world_bank_wdi`. The fetcher requests
`https://api.worldbank.org/v2/country/all/indicator/NE.EXP.GNFS.KD.ZG`
with JSON format, `per_page=1000`, and page iteration; it maps `value`,
`date`→`year`, and `countryiso3code`→`country_iso3`, writes a Parquet
snapshot, and computes the file SHA-256. Its methodology URL form is
`https://data.worldbank.org/indicator/NE.EXP.GNFS.KD.ZG`. These are the
repository's extraction method and intended publisher; without the missing
fetch receipt they do not prove the exact HTTP request that produced these
bytes.

## Raw Parquet footer and schema metadata

`created_by`: `parquet-cpp-arrow version 21.0.0`. Parquet footer key-value metadata
contains the `pandas` key only. Arrow fields:

| Field | Arrow type |
| --- | --- |
| country_iso3 | string |
| country_name | string |
| indicator_id | string |
| year | int64 |
| value | double |
| unit | string |
| obs_status | string |
| decimal | int64 |

Raw `pandas` metadata value from the Parquet schema:

```json
{"index_columns": [], "column_indexes": [], "columns": [{"name": "country_iso3", "field_name": "country_iso3", "pandas_type": "unicode", "numpy_type": "object", "metadata": null}, {"name": "country_name", "field_name": "country_name", "pandas_type": "unicode", "numpy_type": "object", "metadata": null}, {"name": "indicator_id", "field_name": "indicator_id", "pandas_type": "unicode", "numpy_type": "object", "metadata": null}, {"name": "year", "field_name": "year", "pandas_type": "int64", "numpy_type": "Int64", "metadata": null}, {"name": "value", "field_name": "value", "pandas_type": "float64", "numpy_type": "float64", "metadata": null}, {"name": "unit", "field_name": "unit", "pandas_type": "unicode", "numpy_type": "object", "metadata": null}, {"name": "obs_status", "field_name": "obs_status", "pandas_type": "unicode", "numpy_type": "object", "metadata": null}, {"name": "decimal", "field_name": "decimal", "pandas_type": "int64", "numpy_type": "int64", "metadata": null}], "creator": {"library": "pyarrow", "version": "21.0.0"}, "pandas_version": "2.3.3"}
```

The separately committed source lock must record this file's hash, schema
names, and selected country/year-key digest. The runner verifies that lock
against the exact source bytes and a distinct registration commit before
loading selected values. Any result is limited to descriptive calibration
with zero causal, policy, school, position, and featured credit.
