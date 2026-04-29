# UK Cameron-Osborne austerity 2010-16: output and debt path

**Verdict:** partial — debt-target check passes (87.3% vs target 67.0%, overshoot +20.3pp) but UK output gap to donor mean = -0.0083 log-pts > -0.02 — output did not fall below counterfactual by the threshold.

## Method

Two-leg dispositive primary: (1) UK − donor-pool-mean log GDP-pc growth gap 2009→2014 <= -0.02 log-pts AND (2) 2015 general-government debt to GDP exceeds 2010 government target (67.0%) by > 5.0pp. Both must hold for SUPPORTED. Donor pool: USA, FRA, JPN, AUS, CAN. Synth-control weighting included as a robustness check on the equal-weighted donor mean.

## Numbers

- UK log GDP-pc growth 2009→2014: +0.0572
- Donor mean log growth: +0.0655 → UK gap -0.0083
- Synth-control log growth: +0.0794 → UK gap -0.0222
- SC donor weights: {'USA': 0.119, 'FRA': 0.026, 'JPN': 0.746, 'AUS': 0.017, 'CAN': 0.091}
- 2015 UK debt/GDP: 87.3; overshoot vs 2010 target 20.299999999999997

## Caveats

- FRA + JPN had their own fiscal consolidations later in the window — biases the test toward not finding an austerity effect (conservative for the hypothesis).
- Debt-target value 67% is the OBR June-2010 trajectory midpoint for PSND/GDP at FY 2014/15; IMF GGXWDG is a slightly broader measure (general gov gross debt) and runs a few pp higher than PSND.
- Synth-control weights are random-search Dirichlet over a 5-donor simplex with pre-window 2007-2009 — short pre-window weakens identification.
