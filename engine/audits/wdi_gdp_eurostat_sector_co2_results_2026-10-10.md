# Real GDP growth and sectoral CO2: frozen 12-test descriptive result

Preregistration `842ea1491f505205b5144b614e73779cbcfcd154`; source lock `48730de3ad0436351ea8e77c83e1e045e3eb8da7`.
Twelve mutually non-nested CRF source categories; family alpha 0.01; each two-sided p≤0.00083333 and |beta|≥0.005 for direction.

| CRF sector | Verdict | Complete pairs / countries | Material pairs / countries | Beta | Two-sided p |
| --- | --- | ---: | ---: | ---: | ---: |
| CRF1A1A: public electricity and heat | **PARTIAL** | 664 / 29 | 575 / 29 | +0.00209429 | 0.336459 |
| CRF1A2A: iron and steel fuel combustion | **PARTIAL** | 609 / 27 | 525 / 27 | +0.00830566 | 0.314873 |
| CRF1A2C: chemicals fuel combustion | **PARTIAL** | 594 / 26 | 515 / 26 | +0.00741749 | 0.516641 |
| CRF1A2D: pulp, paper and print fuel combustion | **PARTIAL** | 614 / 27 | 529 / 27 | -0.0122203 | 0.377661 |
| CRF1A2E: food, beverages and tobacco fuel combustion | **PARTIAL** | 642 / 28 | 556 / 28 | -0.00185124 | 0.854512 |
| CRF1A2F: non-metallic minerals fuel combustion | **PARTIAL** | 642 / 28 | 556 / 28 | +0.0123667 | 0.00226785 |
| CRF1A2G: other manufacturing and construction fuel combustion | **SUPPORTED** | 641 / 28 | 556 / 28 | +0.0158829 | 7.15784e-05 |
| CRF1A3A: domestic aviation fuel combustion | **PARTIAL** | 663 / 29 | 574 / 29 | +0.00298937 | 0.51341 |
| CRF1A3B: road transport fuel combustion | **SUPPORTED** | 664 / 29 | 575 / 29 | +0.00749382 | 8.45537e-07 |
| CRF1A4A: commercial and institutional fuel combustion | **PARTIAL** | 664 / 29 | 575 / 29 | +0.00853331 | 0.0453587 |
| CRF1A4B: residential fuel combustion | **PARTIAL** | 664 / 29 | 575 / 29 | +0.00473286 | 0.0957227 |
| CRF1A4C: agriculture, forestry and fishing fuel combustion | **PARTIAL** | 664 / 29 | 575 / 29 | +0.00488649 | 0.100883 |

Beta is same-year log sector CO2 change per +1 percentage-point WDI GDP growth. The selected Eurostat vintage lacks cell flags; positive-endpoint filtering for logs cannot identify which zeros represented not occurring versus included elsewhere. These are descriptive calibrations, not sector policy effects; all causal, policy, school-score, position, and featured credit is zero.
