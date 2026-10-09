# OECD working-hours holdout result review — 2026-10-09

Hypothesis: `working_time_employment_oecd_geographic_holdout_v2`.

The design, steelman, and guarded runner were first added in commit
`1f2f18506fbec50bb390f9e97affeb61d52fef4a` before the held-out fit. That commit contains no result artifacts.
The runner's read-only `--check` independently reconstructed the complete
stored packet and returned `replay_verified=true`, `wrote_files=false`.
All six source pins matched their tracked fetch manifest and local SHA-256
files. The fitted sample has 397 country-years in 15 countries excluded from
the old panel, spanning 1991–2019; it clears the registered 150-observation,
10-country, and eight-years-per-country floors.

**Verdict: PARTIAL.** The coefficient of log annual hours on log modeled
employment-to-population ratio is -0.451445. Its country-clustered 90%
confidence interval is [-0.668249, -0.234640], with half-width 0.216805.
The interval crosses the registered -0.5 equivalence boundary, so the result
does **not** support near-neutrality under the frozen two-sided equivalence
rule. The 2008–2010 exclusion sensitivity has no separate verdict and cannot
change this decision.

The stored `evidence_state=PENDING_READ_ONLY_REPLAY` was written at run time;
the successful later check above is the separate replay attestation. The
result is eligible only for associational **calibration** if regular
registration and integrity audits pass. It does not test a shorter-hours
policy effect, the old France event, or a school claim. The prior
finite/nonmissing availability screen, earlier PARTIAL result, and substitution
of WDI modeled employment for the old ILOSTAT identifier remain disclosed.
