# Business-entry geographic holdout: provenance and reproduction

This is one new hypothesis, not a 500-case graduation wave. The old
`wdi_business_entry_rule_of_law_growth_panel` result was known before the
follow-up was specified, and the new test excludes all 60 old-sample
countries. The new specification and steelman first entered Git in
`3e2909666fdb37cb17a1394f4a336c1398c7c0d0`; the first run artifacts
entered in the later commit `6acf6500873165aad2a4da368d5f01f4b6e62776`.

The 109-country, 1,234-country-year holdout produced a `PARTIAL` verdict:
interaction coefficient `+0.3522`, country-clustered SE `0.3436`, p-value
`0.3054`, and model-implied p75–p25 marginal gap `+0.3948`. The registered
support and refutation gates both failed. This result is an associational
screen and does not change a public school score or claim mapping by itself.

## Pinned input custody

The four input Parquet files are present in this workspace but ignored by
Git (`.gitignore` excludes `/data/vintages`). Their source fetch manifests
are tracked. The run's `manifest.yaml` and `evidence_packet.yaml` pin exact
paths, source URLs, licenses, and SHA256 hashes.

| Input | Pinned file | Fetch manifest |
| --- | --- | --- |
| New business registrations | `data/vintages/world_bank_wdi/IC.BUS.NREG@2026-05-05T203439Z.parquet` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| Population | `data/vintages/world_bank_wdi/SP.POP.TOTL@2026-05-05T194826Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| Real GDP-per-capita growth | `data/vintages/world_bank_wdi/NY.GDP.PCAP.KD.ZG@2026-05-05T194650Z.parquet` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| WGI rule of law | `data/vintages/wgi/RuleOfLaw@2026-04-30T114246Z.parquet` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |

With these exact files available, run the coverage and hash check without
estimating:

```bash
python3 scripts/run_business_entry_rule_of_law_geographic_holdout_v2.py --preflight
```

The committed `engine/runs/wdi_business_entry_rule_of_law_geographic_holdout_v2/replication.py`
calls the runner with `--run --force` to reproduce the estimate. It rewrites
run timestamps, so use it in a separate checkout when comparing artifacts.

If a pinned file is absent, the registered source can be fetched again with
the repository fetchers:

```bash
python3 scripts/fetch.py world_bank_wdi IC.BUS.NREG
python3 scripts/fetch.py world_bank_wdi SP.POP.TOTL
python3 scripts/fetch.py world_bank_wdi NY.GDP.PCAP.KD.ZG
python3 scripts/fetch.py wgi RuleOfLaw
```

A refetch writes a **new** vintage and may have revised values or a different
hash. It does not recreate the pinned 2026-04/05 bytes automatically. Preserve
or restore those exact files for exact replication and compare their hashes
to the committed run manifest. Never rename a fresh fetch to the old pinned
path or silently swap it into this result. If only a new vintage is
available, register and report a separate vintage-sensitivity run.
