# private_credit_manufacturing_share_2022_2024_holdout_v2

**Verdict: PARTIAL** — frozen sample, variation and HC3 estimator gates passed

Descriptive cross-country calibration only. This does not establish that credit causes manufacturing-share change.

- Complete countries: 130 of 181; frozen floor 80.
- Selected WDI vintage: 2026-05-05; outcome change 2022–2024.
- Registration commit: `e3de7847adfbf3387d8dd912fc91fe16d1848c97`; key-only source lock commit: `dc522a4fa730629d8b0f304a6a536d73fd2e7aef`.
- School, policy, causal and featured credit: zero.
- Credit IQR: 44.752680 GDP percentage points; floor 10.
- Beta: +0.100165 manufacturing-share points per 10 credit/GDP points.
- HC3 95% CI: [-0.003167, +0.203496].

The source predates registration and the old 1990–2023 result is known; this is neither independent source replication nor a causal policy test.
The WDI manufacturing series measures a GDP share and may change with relative prices or services output.

Exact replay: `python3 scripts/run_private_credit_manufacturing_2024_v2.py --verify --source-root <root-with-pinned-WDI-vintages>`.
