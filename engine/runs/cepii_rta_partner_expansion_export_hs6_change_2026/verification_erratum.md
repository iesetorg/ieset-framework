# Replay instruction for this result

Run `python3 engine/runs/cepii_rta_partner_expansion_export_hs6_change_2026/replication_erratum.py`
from the repository root. It invokes the exact-replay adapter at
`scripts/verify_cepii_rta_hs6_2026.py` and has passed on the committed
PARTIAL result.

The original `replication.py` and the preregistered runner's `--verify`
command fail **only at the final coefficient Parquet comparison**:
`AssertionError: coefficients[0].confidence_interval: list length mismatch`.
Pandas restores the saved confidence-interval list cell as a NumPy array,
while the frozen comparator expects a Python list. Do not use the original
command as the working replay path. The adapter normalizes that comparison
cell and calls the unchanged runner's registration, source-lock, key-roster,
estimation, and artifact checks.

The preregistered runner and original result files remain byte-for-byte
unchanged. See `engine/audits/cepii_rta_hs6_replay_erratum_2026-10-09.md`
for their SHA-256 pins and commit sequence. This result remains a descriptive
PARTIAL calibration with no school, policy, causal, or featured credit.
