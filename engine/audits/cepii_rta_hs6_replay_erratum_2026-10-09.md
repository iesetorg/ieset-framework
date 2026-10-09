# CEPII/WITS replay format erratum — 2026-10-09

The original preregistration commit is `42615549dcd47a1b14430b5e56b902d3914a1490`.
The separate source-lock commit is `ccbc26bbfe5aa384a27fcc81293908ce1d8662e5`. The measured PARTIAL
result packet first appeared in commit `e994f00c9f311cf94bffccfccfe324b8f0c943dd`.

The registered runner `scripts/run_cepii_rta_hs6_2026.py` remains byte-for-byte
unchanged at SHA-256
`a77c54bd07c2cdd4dd1d4acd1e992779458cfeb000ddd135af5a6807a1b449f9`.
The original diagnostics and coefficient Parquet files remain byte-for-byte
unchanged at SHA-256
`bb4c059b66dd5c34f220d0732fd48fa4fbb80792cbda8ea422f33a444fe03848`
and `8443ed571d7f3ec25f41e479b88a23ffff1af022ad3a1adcf79c6920e023567c`.

The original `engine/runs/cepii_rta_partner_expansion_export_hs6_change_2026/replication.py`
command reaches the coefficient comparison after recomputing and matching the
JSON, YAML, chart, and text artifacts, then fails with
`AssertionError: coefficients[0].confidence_interval: list length mismatch`.
Pandas returns the saved Parquet confidence-interval list cell as a NumPy
array, whereas the frozen comparator checks for a Python list. This is a
serialization comparison bug, not a changed coefficient, sample, or verdict.

Use `python3 scripts/verify_cepii_rta_hs6_2026.py` for exact replay. The
adapter imports the unchanged registered runner, invokes its registration,
source-lock, key-roster, estimator, and artifact checks, and converts only a
NumPy array to a Python list when the expected comparison field is a list.
The original wrapper still fails; this erratum does not claim otherwise.
No outcome value, model term, threshold, source pin, or result artifact was
altered to repair the comparison.
