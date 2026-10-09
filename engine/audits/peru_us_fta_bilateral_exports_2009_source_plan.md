# Peru–US 2009: prospective source custody and execution plan

This file, the hypothesis YAML, steelman, and runner must first appear together in a Git commit **before any BACI trade-flow value is read**. The runner refuses extraction or analysis until that first-addition commit exists and its registered bytes match the working files. Do not add `engine/runs/peru_us_fta_bilateral_exports_2009/` to that commit. The repository's strict preregistration check also requires the spec commit to precede the first run-artifact commit.

## Frozen source and slice

- Publisher: CEPII, *Gravity database*, version V202211. Source: `https://www.cepii.fr/DATA_DOWNLOAD/gravity/data/Gravity_csv_V202211.zip`; member `Gravity_V202211.csv`. CEPII identifies its license as Etalab Open Licence 2.0; cite Conte, Cotterlaz and Mayer (2022).
- Expected official archive SHA-256: `7ffea0510a536587f2f9295bbafef4a312a36b366acc256eb6d9770fe35e44b1`, already recorded in `data/manifests/fetch_run_2026-05-15T175027Z.yaml`. Verify this exact archive before extraction; a changed download requires a new registration, not a silent substitution.
- Output after registration: `data/pinned_evidence/peru_us_fta_bilateral_exports_2009.csv` plus `.manifest.json`, both small and Git tracked. The 197 MB archive stays in ignored `data/raw/` or at an explicit local `--source-zip` path. Do not add the archive or 84 MB derivative parquet to Git.
- Expect exactly 7 directed dyads × 11 years = 77 rows: USA origin; destinations `PER, ARG, BOL, BRA, ECU, PRY, URY`; years 2004–2014. Preserve source `tradeflow_baci` text, `fta_wto`, country-existence flags, and original CSV record ordinal. If the source selection has missing or duplicate keys, still preserve its raw rows, up to 78; record the total source-match count and an overflow flag. That anomaly yields an `INCONCLUSIVE` result instead of blocking custody. Sort by destination, year, and source record ordinal; write a stable UTF-8 CSV with LF line endings.
- The slice manifest stores the archive hash, member name, extraction code/registration commit, source URL, SHA-256 of the slice, frozen row keys, selection count/overflow flag, and column meanings. The runner requires both slice and manifest bytes to equal their **first-addition commit** before any estimate. The small slice is sufficient for replication without Git shipping the large archive, while the official archive hash and row numbers permit an independent re-extraction.

## Registered comparison

- Effective date 2009-02-01, checked against [USTR](https://ustr.gov/trade-agreements/free-trade-agreements/peru-tpa) and policy record `pe_us_fta_implementation_2009`.
- Primary directed outcome: USA → PER annual CEPII `tradeflow_baci` merchandise value, nominal thousands of US dollars, transformed by natural `log1p`.
- Donors: USA → ARG, BOL, BRA, ECU, PRY, URY. Eligibility requires country-existing unique rows, `fta_wto=0` throughout 2004–2014, and complete finite nonnegative BACI values. The treated dyad must switch from `fta_wto=0` in 2004–2008 to `1` in 2009–2014. No donors may be dropped or replaced after extraction.
- Pre 2004–2008; post 2010–2014; 2009 omitted from means. Contrast: Peru's change in five-year mean log flow minus the median of the six donor changes. Pretrend: absolute Peru-minus-median-donor 2004–2008 OLS log-flow slope gap ≤0.03/year. A failed structural, treatment, outcome, or pretrend gate yields `INCONCLUSIVE` and archive. A custody hash/commit mismatch stops the run without an evidentiary verdict. Passing gate: contrast ≥ln(1.15) `SUPPORTED`; ≤−ln(1.15) `REFUTED`; otherwise `PARTIAL`. These words refer only to the narrow descriptive claim.
- No school claim linkage or score credit. Do not produce a second independent hypothesis from the reverse direction or alternative windows using the same treaty.

## Sequence after review

1. Commit these four registration files and the CEPII publisher entry together, without source slice or results.
2. Run `python3 scripts/run_peru_us_fta_bilateral_exports_2009.py extract --source-zip /absolute/path/to/Gravity_csv_V202211.zip` after registration. Commit the generated small CSV and manifest in a second commit. An independent re-extraction can be checked byte-for-byte with the runner's `verify-source` command and the same `--source-zip` argument.
3. Run `python3 scripts/run_peru_us_fta_bilateral_exports_2009.py run` only after the slice commit. It writes a frozen `hypothesis.yaml`, source/run `manifest.yaml`, `diagnostics.json`, `evidence_packet.yaml`, `result_card.md`, `replication.py`, and meaningful descriptive `chart_data.json` only when the contrast is estimable; it writes no coefficient file. Inspect the result and replicate every artifact byte with `python3 scripts/run_peru_us_fta_bilateral_exports_2009.py verify`; commit results in a third commit, then regenerate the project preregistration and evidence audit indexes.

No step 2 or 3 has been executed in this draft. Structural row and status checks were conducted before registration without opening trade magnitudes; no directional effect has been estimated.
