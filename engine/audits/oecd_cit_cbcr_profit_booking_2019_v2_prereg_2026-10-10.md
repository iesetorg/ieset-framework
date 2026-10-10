# Blind registration: statutory CIT and CbCR profit booking, 2019

**Case/family:** `oecd_cit_cbcr_profit_booking_2019_v2` (one question).
The exact 2019 source-key join contains **143 tax jurisdictions**. This
includes reporting territories; it is not a country-level movement panel.
Only schemas, country/year/series keys, source code, fetch manifests, and
publisher descriptions were inspected before registration. No selected 2019
tax rate, profit, employee, ratio, finite mask, model, coefficient, or sign
was opened. The key-only roster SHA-256 is
`617e3febe5a7566e2a52669679b996e4f0b93f0bf3b2b3805e5c338f9bed9d86`.

## Source custody and scope

| Role | Pinned relative file | SHA-256 | Fetch manifest SHA-256 |
| --- | --- | --- | --- |
| CbCR derived source | `data/vintages/profit_shifting/profit_shifting_panel@2026-06-29T160050Z.parquet` | `96bad604e38151689d4d31a28f5c86cdec0e0941c7bac310fb8d2cac4472f733` | `data/manifests/fetch_run_2026-06-29T160050Z_profit_shifting.yaml` `1108d0451cf57ae95de814e159f72e69356edf4d795d87ed3333b41662fb98fc` |
| Combined statutory CIT | `data/vintages/oecd/oecd_combined_corporate_income_tax_rate@2026-07-23T153857Z.parquet` | `3e9c5987717087d04d5f82461fc1a3fb5e406ba646fb9f333f8c542e5f3f5ee1` | `data/manifests/fetch_run_2026-07-23T153857Z_oecd_tax_structure.yaml` `6a9172689c2f5561fddfd3b779431bca070d48f54b2f75814ff4e9295fa0ba18` |

The source builder `scripts/build_profit_shifting_panel.py` has SHA-256
`49bedf729b83d0818904a67a96cab41a97994c31a901b31ff705b9fad997ff5d`.
Its manifest records the OECD CbCR endpoint in `extra.oecd_cbcr_url`,
although its top-level URL names the TWZ workbook that the same composite
vintage also contains. No raw CbCR HTTP payload was preserved. This is an
explicit provenance limit; the derived parquet and build code can be
replayed exactly, but the original publisher response cannot be
byte-for-byte checked. The frozen ratio-consistency gate catches arithmetic
inconsistency, not omitted or duplicated source groups.

The [OECD's CbCR description](https://www.oecd.org/en/publications/corporate-tax-statistics-2025_6a915941-en/full-report/component-11.html)
explains that these anonymised, aggregated statistics cover large MNE groups
and have source and comparability limitations. Our 2019-only test avoids
interpreting reporting-population changes as a temporal treatment. The
profit/employee rank is a **partial-coverage risk indicator**, not a global
profit-shifting estimate. The
[OECD corporate-tax statistics database](https://www.oecd.org/en/data/datasets/corporate-tax-statistics-database.html)
provides the statutory CIT series.

## Frozen design and gates

Join the exact 143 roster keys in 2019. Require one CbCR booked-profit,
employees, and derived-ratio cell and one statutory rate per key; allow only
finite values, employees >0 and rates in [0,60] percent. The derived ratio
must match profit/employees within the fixed numerical tolerance, or the
test is INCONCLUSIVE. Keep at least 120 jurisdictions, ten distinct tax
rates, a tax-rate IQR at least 5 percentage points, and 30 distinct ratio
values. No alternate year, source, currency conversion, winsorisation, or
jurisdiction replacement.

The primary statistic is two-sided Spearman rho with average ranks. A fixed
seed permutes outcome ranks 10,000 times; two-sided
`p=(1+count(|rho_perm|>=|rho_obs|))/10001`. Report the leave-one-out
coefficient signs. One-test local threshold: p<=0.01 and |rho|>=0.20, with
at least 95% leave-one-out signs matching. Negative is SUPPORTED; positive
is REFUTED; weaker estimable evidence is PARTIAL; a source or method gate
failure is INCONCLUSIVE. This is one descriptive calibration at most,
with **zero** causal, policy, school, position, or featured credit.

## Chronology

Commit this audit, the exact key-only roster, YAML, steelman, and guarded
runner in one first-addition commit. Commit a narrow source lock in a
separate descendant commit before selected values may be read. Then run,
retain an inconclusive result if a gate fails, and verify exact replay.
The method does not rescue an old CIT/FDI or profit-shifting claim.
