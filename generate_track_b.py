#!/usr/bin/env python3
import os

GROWTH_DIR = "./hypotheses/growth"
STEELMAN_DIR = "./hypotheses/steelman"

os.makedirs(GROWTH_DIR, exist_ok=True)
os.makedirs(STEELMAN_DIR, exist_ok=True)

def write_yaml(hid, content):
    path = os.path.join(GROWTH_DIR, f"{hid}.yaml")
    if os.path.exists(path):
        print(f"SKIP (exists): {path}")
        return
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote YAML: {path}")

def write_steelman(hid, content):
    path = os.path.join(STEELMAN_DIR, f"{hid}.md")
    if os.path.exists(path):
        print(f"SKIP (exists): {path}")
        return
    with open(path, "w") as f:
        f.write(content)
    print(f"Wrote steelman: {path}")

# 11
write_yaml("korea_post_chaebol_liberalisation_frontier_growth", """# yaml-language-server: $schema=../../schemas/hypothesis.schema.json
hypothesis_id: korea_post_chaebol_liberalisation_frontier_growth
version: 1
status: candidate
topic: growth
claim: South Korea's post-1997 liberalisation and governance reforms explain a larger share of post-crisis frontier convergence than earlier heavy-and-chemical industrial policy.
evidence_type: causal
sample:
  countries:
    - KOR
  period: [1961, 2024]
  temporal_structure: time_series
variables:
  outcome:
    - name: real_gdp_per_capita
      source: world_bank_wdi:NY.GDP.PCAP.KD
      transformation: log
    - name: tfp_growth
      source: pwt:rtfpna
      transformation: annual_log_diff
    - name: real_wage_growth
      source: ilo:avg_wage_real
      transformation: annual_log_diff
  treatment:
    - name: post_1997_liberalisation_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 from 1998 onward, reflecting post-IMF reform period including chaebol restructuring, capital-account liberalisation, and governance reforms.
    - name: hci_policy_dummy
      source: constructed:binary_indicator
      transformation: binary
      notes: Coded 1 for 1973-1997 heavy-and-chemical industrialisation drive period.
  controls:
    - name: global_demand_index
      source: imf_weo:world_gdp_growth
      transformation: level
    - name: terms_of_trade
      source: world_bank_wdi:NE.TRD.GNFS.ZS
      transformation: level
      notes: Trade openness as proxy for external conditions.
    - name: r_d_expenditure
      source: world_bank_wdi:GB.XPD.RSDV.GD.ZS
      transformation: level
estimator:
  template: event_study
  fixed_effects: [year]
  clustering: none
  notes: Event-study and structural-break analysis of Korean growth around 1997. Compares cumulative convergence gains in 1998-2024 versus 1973-1997, controlling for global conditions and R&D intensity.
falsification:
  rule: The hypothesis is refuted if the cumulative real GDP-per-capita gain in 1973-1997 exceeds that in 1998-2024 after controlling for initial income level and global conditions, or if TFP growth was stronger in the HCI era than in the post-liberalisation era.
  test: event_study_korea_regime_comparison
  threshold:
    post_1997_gain_exceeds_hci: true
    post_1997_tfp_higher: true
prior_confidence: 0.55
disclosure: Author acknowledges that the 1997 crisis creates a low base for post-crisis growth and that comparing across regimes with different initial conditions is inherently difficult.
steelman: hypotheses/steelman/korea_post_chaebol_liberalisation_frontier_growth.md
scope:
  period: [1961, 2024]
  countries:
    - KOR
  outcome_dim:
    - gdp_growth
    - productivity
    - institutional_quality
  policy_family:
    - institutional_reform
    - industrial_policy
    - competition_policy
  treatment_tags:
    - korea_1997_imf_reforms
    - korea_hci_drive_1973
    - chaebol_restructuring
notes: Single-country time-series analysis requires careful handling of structural breaks. PWT TFP for Korea is available from 1950s. Real wage data from ILOSTAT has gaps before 1990.
""")

write_steelman("korea_post_chaebol_liberalisation_frontier_growth", """# Steelman — Korea Post-Chaebol Liberalisation and Frontier Growth

## Strongest version of the claim
South Korea's convergence toward the technological and income frontier accelerated more after the 1997-1998 crisis reforms than during the celebrated heavy-and-chemical-industry (HCI) drive of 1973-1997. The post-1997 period saw higher TFP growth, stronger real wage growth, and more resilient innovation capacity, suggesting that market-liberal reforms were the more important driver of frontier convergence.

## Key evidence the claim would need
1. A structural-break or event-study showing higher cumulative GDP-per-capita convergence, TFP growth, and real wage growth in 1998-2024 than in 1973-1997, after adjusting for global demand and starting-income level.
2. Evidence that the post-1997 gains were concentrated in sectors most affected by governance reforms rather than in pre-existing industrial champions.
3. Counterfactual construction (synthetic control) showing that a Korea without post-1997 reforms would have grown more slowly.

## Best counterarguments
- **Low-base effect:** The 1997 crisis created a deep trough; post-crisis recovery growth is mechanically high when measured from the bottom.
- **HCI stock vs. flow:** The post-1997 economy inherited the physical and human capital stock built during the HCI era; attributing post-1997 success to liberalisation ignores accumulated industrial capability.
- **Global tech cycle:** Korea's post-1997 growth coincided with the global semiconductor and consumer-electronics boom; sectoral luck may explain more than domestic policy.
- **Democratic transition confound:** Post-1997 Korea was also a more democratic polity; governance improvement may reflect political liberalisation rather than economic reform per se.

## Boundary conditions
- Claim is about relative contribution, not an absolute judgement that HCI was worthless; HCI may have been necessary but not sufficient.
- Post-1997 period includes significant state support for semiconductors and batteries; the market-liberal label should not be overstated.
- Single-country analysis cannot control for all confounds; the result is suggestive rather than dispositive.

## Relation to existing hypotheses
Tensions with `korea_hci_drive_capability_effect` and `industrial_policy_developmentalist_states_growth`. Aligns with `market_reform_duration_growth_persistence` and `frontier_tfp_market_liberal_panel_1970_2024`.
""")

print("Done 11")
