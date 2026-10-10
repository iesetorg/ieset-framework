# Demographic transition and later economic margins: frozen registration

Registration opens only fertility and income treatment/control values plus country-year-indicator keys from outcomes. It does not open outcome values, null masks, or observation statuses. Selected vintages existed in the broader IESET corpus and previous related hypotheses are known; this is a within-lane prospective measurement protocol, not an independent future-data holdout.

One six-test family `demographic_transition_followthrough_2026_10_10`; roster `data/pinned_evidence/demographic_transition_followthrough_2026_key_roster.csv` SHA-256 `fb3590fa3cd5c8557b793962f14cb3badfddbeddbaaf9551938ac56fbceacb50`.
Treatment anchors are 1995 and 2005. The preceding ten-year fertility decline is fertility(t-10) minus fertility(t), births per woman. Outcome is change or log ratio t to t+10. Real GDP per person at t and preceding ten-year growth are controls. Countries must have both complete anchor windows after outcome access.

Treatment/control and outcome-key preflight: 334 pairs in 167 ISO countries; 183 pairs/112 countries have |fertility decline|≥0.5. All six selected outcomes have physical key rows for this roster; this does not assert nonmissing values.

The six distinct margins are female labour-force participation, self-employment share, services-employment share, real output per worker, real private consumption per resident, and fixed-capital-formation share. Labour series can share ILO model inputs. The six packets are one correlated demographic-transition programme and cannot be called six independent replications.

Every case requires ≥250 complete two-window rows, ≥120 countries, ≥100 material rows in ≥65 countries, full-rank treatment residualization and primary model, finite positive country-cluster uncertainty, residualized exposure shares ≤0.3 for the top 1% of rows, ≤0.15 for one country, and ≤0.65 for one anchor year. No value clipping or gate relaxation.

Country and anchor fixed-effects OLS includes baseline log income and prior-decade log income growth. Use CR1 country clustering and two-sided Student t(G-1). Family alpha=0.01; six-test Bonferroni p≤0.0016666666666666668. A directional verdict additionally needs the margin-specific practical size fixed in each YAML. Opposite sign of equal size is REFUTED; other estimable results PARTIAL; failed gates INCONCLUSIVE.

The design is descriptive and ecological. National fertility is not a treatment assignment. Country/anchor effects and prior income do not resolve migration, structural change, social norms, policy, or reverse timing. Labour values are modelled. No causal, policy, school-score, position, or featured credit. The p adjustment covers this declared family only, not the wider IESET search.

## Exact source identities

| Role | WDI indicator | SHA-256 | Tracked fetch manifest |
| --- | --- | --- | --- |
| fertility | SP.DYN.TFRT.IN | `ff1eb90d4033e42ca63bb0de72c27f21044e55b69e44568d65321dd81cd8cfd1` | `data/manifests/fetch_run_2026-04-30T130536Z.yaml` |
| income | NY.GDP.PCAP.KD | `0cf53ee3a334988ded027fbe160a8d8c70773656772daf1c82206eb3f7c02a9f` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| female_lfp | SL.TLF.CACT.FE.ZS | `c3b8ecd5c8a7ac7c1ab2fbf61675494c2f6a88093d3b64dfd808c542e96d1186` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| self_employment | SL.EMP.SELF.ZS | `67abd9aef0cc6ba29de9fc1bea7bbbf6686a310a49fc7b38f782211a22dd330c` | `data/manifests/fetch_run_bootstrap_2026-04-30T121833Z.yaml` |
| services_employment | SL.SRV.EMPL.ZS | `5cc0fcababebe90b69eae253466a6a81beaf0f52f9c0ef5d59b8a2fa34f400c6` | `data/manifests/fetch_run_2026-05-05T210519Z.yaml` |
| worker_productivity | SL.GDP.PCAP.EM.KD | `a4b4194f221b89c5f08ed6c11eb691c66ddb572798948af55c0f9d4b5b284742` | `data/manifests/fetch_run_2026-04-30T141104Z.yaml` |
| private_consumption | NE.CON.PRVT.PC.KD | `e696dc3fd004c69efb8bc783896f3de21a11422757ac9f6a2a0f558788032cfe` | `data/manifests/fetch_run_2026-05-05T200056Z.yaml` |
| fixed_investment | NE.GDI.FTOT.ZS | `fee6f66739512936ab17e82c4b7b788dc3030620ba30a6e5671e972a3a341a21` | `data/manifests/fetch_run_2026-05-05T203305Z.yaml` |

Source-lock manifest must be separately committed after this registration and before selected outcome values are read. A separate measured-result commit follows.
