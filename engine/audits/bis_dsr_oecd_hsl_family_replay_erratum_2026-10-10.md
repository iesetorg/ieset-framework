# Replay adapter for the frozen BIS DSR / OECD HSL family

The first measured run used the committed preregistration `867fd75862c8235837c642c30463c0f010a25d8f` and
source lock `235de008fb7bb57a64ab816368989efbc984d824`. It produced all four result folders without an
execution error. The frozen runner's `--verify` command then compared a
Python `list` confidence interval against the `numpy.ndarray` returned by
`pandas.read_parquet` for the nested `coefficients.parquet` list column. It
stopped at `ends_meet.coefficients[0].confidence_interval: list length mismatch`.
The diagnostics, manifest, evidence packet, chart data, and result-card checks
preceding that comparison had matched.

No registered model, result value, source, threshold, artifact, or frozen
runner was changed after outcome access. Use this post-result, read-only
serialization adapter for full exact replay:

`python3 scripts/verify_bis_dsr_oecd_hsl_2026.py`

It imports the frozen runner, rechecks the two custody commits and raw source
hashes, rebuilds all four panels and estimates, and compares every stored
artifact. Its only difference is converting Arrow-reloaded array values to
Python lists before the coefficient-record comparison. The command inside
original result packets still points to the frozen `--verify`; this erratum
supersedes that command for reproducing those exact stored files.
