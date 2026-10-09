# Innovation/productivity replay serialization erratum

The first-addition registration and estimator in commit `b66c6805ba9edecc6923e5b26724dec33d248c4e` are
unchanged. Both measured fits ran after the separate source lock in
`95383b3803687de0dc562257b1fecb4c74df5257`, and both result packets were retained as PARTIAL.

The frozen runner's initial read-only `--verify` reached the coefficient
Parquet comparison and stopped because pandas returned its nested `ci95` pair
as a NumPy array while the in-memory expected artifact held a Python list.
This was a container-type mismatch in the verifier, after the model and the
other stored artifacts had been reconstructed; it was not a failed fit or a
different estimate.

`scripts/verify_innovation_productivity_measured_family_2026.py` imports the
unchanged frozen runner, rechecks its first-addition registration and separate
source lock, reruns the identical two fits read-only, and compares diagnostics,
manifest, packet, chart data, coefficient data, copied specification, card,
and wrapper. Only the nested Parquet container type is normalized to a list.
The two packets and their wrappers point to this working verifier. No source,
sample, estimand, model, threshold, coefficient, p-value, or verdict was
changed after results were seen.
