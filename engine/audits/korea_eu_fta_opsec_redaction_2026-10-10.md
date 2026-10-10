# Korea–EU treaty test: local path redaction

The registered source plan inadvertently contained a developer's local
corpus path in a command example. The audit result note repeated it. These
two prose examples have been changed to a `<local-corpus>` placeholder.
No source file, selected country/year cell, policy date, hypothesis claim,
comparison group, estimator, pretrend gate, result, or run artifact changed.

The original frozen runner rightly rejects any post-registration edit to
the source plan, including this prose-only change. The narrow
`scripts/verify_korea_eu_fta_opsec_redaction.py` adapter checks that the
current plan differs from its first-addition bytes by exactly one local
path-prefix substitution and that every other registered file is identical.
It then invokes the original frozen runner's byte-for-byte result replay
and, when given the local official ZIP, its source re-extraction check.
The run's own replication wrapper still targets the original runner and
therefore requires this documented adapter on the redacted checkout.

The already frozen verdict remains **INCONCLUSIVE** because the pretrend
gap exceeded its registered bound. No public graduation or policy-effect
credit follows. The offending path still exists in local Git history, so
this branch must not be pushed or published as-is.
