# Doing Business source-key adapter — before selected values

The first value-blind preflight after registration `1f1b0ca0c9a300cd2272271838513a345adc224e` rejected the
WDI fixed-capital-formation parquet because it has 66 duplicated `(empty
country_iso3, year)` aggregate keys (264 extra rows). Those records cannot
match a three-letter ISO3 in the committed 512-key roster. No selected
Doing Business, WDI, or PWT magnitude had been opened.

The adapter `scripts/run_doing_business_insolvency_followup_2026_key_adapter.py`
removes only rows with an empty country identifier before checking source-key
uniqueness. It preserves every nonempty key and value, the publisher workbook,
the roster, the frozen estimator, model, coverage and verdict gates. Any
duplicate nonempty country/year key still fails. Each source lock will hash
the adapter and the result packet will replay through it. Commit this adapter
before opening selected values; do not edit the registered runner.
