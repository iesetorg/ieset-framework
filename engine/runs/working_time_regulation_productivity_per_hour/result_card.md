# Result card - working_time_regulation_productivity_per_hour

**Verdict:** SUPPORTED - hours reductions predict higher hourly productivity and lower output per worker

## Pre-registration
- **Claim:** Stricter working-time limits predict higher hourly productivity but lower total output per worker, with ambiguous welfare effects.
- **Falsification rule:** SUPPORTED if coefficient > 0 and p < 0.10
- **Falsification test:** not specified in current YAML

## Method
OECD PDB country-year FE panel: GDP per hour and GDP per employed person growth on reductions in average hours worked per employee, with country and year fixed effects clustered by country.

## Estimates
### hourly_productivity_growth
- Sample: n=934, countries=32, years=1990-2023
- R-squared: 0.468
- `hours_reduction`: beta=+0.7044, se=0.08304, p=1.394e-09

### output_per_worker_growth
- Sample: n=934, countries=32, years=1990-2023
- R-squared: 0.440
- `hours_reduction`: beta=-0.3098, se=0.0776, p=0.000374

## Interpretation
The PDB productivity panel directly tests the productivity/output-per-worker pattern, but the policy treatment itself remains proxied by realised hours reductions.

## Variables Loaded
- `hours_reduction` (treatment_proxy): negative of oecd_pdb:HRSAV_GY total economy
- `hourly_productivity_growth` (outcome): oecd_pdb:GDPHRS_GY total economy
- `output_per_worker_growth` (outcome): oecd_pdb:GDPEMP_GY total economy

## Missing Or Proxied
- `statutory working-time limits` (exact_treatment): policy/legal panel not local
- `welfare effects` (welfare_outcome): not tested by PDB productivity data

## Source Paths
- `OECD Productivity Database` -> `data/vintages/oecd/DSD_PDB@2026-05-12T133454Z.parquet`

## Caveats
- Average-hours reductions are an observed-outcome proxy for stricter working-time regulation.
- The result should not be read causally without statutory reform timing or instruments.
