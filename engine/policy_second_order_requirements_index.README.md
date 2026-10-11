# Policy second-order requirements database

`policy_second_order_requirements_index.json.gz` is the current complete
derived lookup. It expands to 113,188,539 bytes with SHA-256
`ea242e3ff4eb1a409abb1e8a6117b03b23ecce4e0b40b1d3b5efe8a6960f2b82`.
The uncompressed JSON is ignored by Git to keep generated files within
repository hosting limits.

To read it locally, run
`gzip -cd engine/policy_second_order_requirements_index.json.gz > engine/policy_second_order_requirements_index.json`
from the repository root. To regenerate it from the source specifications,
run `python3 scripts/generate_policy_second_order_index.py` and compress
the JSON with gzip using `mtime=0`. The companion
`policy_second_order_requirements_index.md` remains a compact summary.
