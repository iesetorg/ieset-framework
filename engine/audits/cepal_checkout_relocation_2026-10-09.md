# CEPAL/IMF study checkout relocation — 2026-10-09

The CEPAL national-poverty/IMF inflation study was accidentally registered in
the dirty main checkout instead of this isolated review worktree. The original
registration commit `87bf6a58e63738e148ca5c7ddfdfb3f22ceb3fa5` added only
the specification, steelman, runner, and synthetic tests. The source-lock
commit `e3db724ac4f053a0d3056cfe410e445b05211b3a` added only a narrow
three-source lock. Both commits preceded the first numeric read. That first
run wrote an uncommitted `PARTIAL` packet in the main checkout.

The unchanged registration and lock were copied into this isolated branch by
cherry-picks `37bf99cad9a1e84dcc59c234a2fefb4fc583a45f` and `2599d302f25bcb71ed017844aacabd7e9cef290d`, respectively. These cherry-picks
occurred **after** the first numeric read; the original commits, rather than
their later copies, establish the pre-result design and source chronology.
The three raw parquet files and the broad fetch manifest were copied locally
only after SHA-256 checks. The broad manifest contains unrelated local-path
metadata and is deliberately not committed to this branch. The narrow lock
records its hash and only the selected source entries. The broad manifest
must be supplied from the main checkout at its recorded hash for the original
runner's exact replay; the branch alone is not a self-contained raw-data
archive.

The unchanged runner then wrote a new packet in this isolated branch. Its
saved estimate, sample, data status, and `PARTIAL` verdict match the original
main-checkout packet exactly; `--check` replay passed. The fitted coefficient
is -0.958607 poverty percentage points per one unit of asinh(inflation/10),
with two-sided country-cluster t p=0.726953 over 281 complete country-years
in 14 countries. This is a retrospective descriptive calibration only, with
no causal, school, or policy-score credit. The main checkout's unrelated
working changes were not staged, copied, or modified during relocation.
