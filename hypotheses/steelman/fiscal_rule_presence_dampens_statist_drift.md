# Steelman — Fiscal-rule presence dampens statist drift

## The strongest case AGAINST this hypothesis

### 1. Endogeneity: rules don't constrain countries; countries that don't want to spend pass rules

The most damaging objection. Germany passed the Schuldenbremse in 2009
*because* its political culture was already fiscally conservative — the
ordoliberal consensus produced both the rule and the lower drift, not one
causing the other. Same for Switzerland (debt brake reflects long-standing
direct-democratic restraint), Sweden (1996 surplus target reflects the
country's traumatic learning from the 1990–93 banking crisis, not a rule
imposed from outside the political consensus). The correlation between
rule-presence and lower drift could entirely be that countries already
disposed to fiscal restraint also pass rules, and countries already disposed
to expansion don't (USA, France, Italy pre-2012). Without an exogenous
instrument the test is observationally indistinguishable from selection.

### 2. Rules that bite vs rules that don't bite

The hand-coded binary lumps Spain's 2011 constitutional amendment in with
Germany's Schuldenbremse, but Spain's rule has been routinely overridden
under EU "exceptional circumstances" clauses (COVID, energy crisis), while
Germany's bit hard until the 2024 Karlsruhe ruling forced the Sondervermögen
restructuring. Greece's "rule" was IMF-Troika-imposed, not domestic
political — it should arguably be coded as a foreign constraint not a
domestic rule. The binary is too coarse to capture which rules actually
bind, and the result could be driven by the most-binding cases (DE, CH)
even if the median rule-bound country looks similar to rule-free.

### 3. Fiscal rules can be circumvented

The German Sondervermögen €100bn defence fund (2022) and the climate
transformation fund (KTF) are *off-balance-sheet* spending that bypasses
the debt brake. The framework's drift index would record the
spending-expansion moves these vehicles enable, but the fiscal-rule
treatment indicator stays at 1, biasing the test. Similarly for France:
the constitutional-organic-law fiscal-rule provisions are technically
binding but consistently breached without consequence. If rules can be
evaded through SPVs, Special Funds, or sovereign-wealth-fund withdrawal
rules, then the binary signal is meaningless.

### 4. The 26-country sample is small and the test is non-parametric

Mann-Whitney with n_treated = ~14 and n_control = ~12 has limited power.
A null result here doesn't strongly distinguish "no effect" from
"effect exists but the test can't see it." A genuine test requires either
a much larger sample (panel of all OECD + non-OECD democracies) or
within-country pre/post identification (e.g., synthetic control on
Germany pre-2009 vs Germany post-2009 — which the framework's substrate
could compute but doesn't yet).

### 5. The "rule" mechanism may not be what's actually constraining drift

Other binding constraints — EU fiscal surveillance, IMF Article IV
conditionality, sovereign-bond-market discipline (Italy 2011-2013),
domestic constitutional-court doctrine — all act as drift-constraints
without showing up in the binary fiscal-rule indicator. If those are
the real binding mechanisms, the test is mismeasuring the treatment.
The result could be "all binding constraints work; only naming them
'fiscal rule' is arbitrary."

## What would change my mind

A formal IV using the Eurozone-membership shock or the 2008 crisis as an
instrument (rules adopted in response to a common crisis, but the response
is conditional on prior fiscal capacity) would help. So would a
within-country event-study around each rule's introduction. Both belong
in v2 of this hypothesis if v1 produces a meaningful effect; if v1 is
null, the most likely cause is selection / measurement, not absence of
effect.
