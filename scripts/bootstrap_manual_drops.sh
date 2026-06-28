#!/usr/bin/env bash
# Bootstrap empty manual-drop directories for publishers whose automated paths
# are Cloudflare/JS-gated. Each directory gets a README.md documenting exactly
# which file to drop, the source URL, and the expected schema so any operator
# (human or agent) can populate it without reading the fetcher source.
#
# Run from repo root: bash scripts/bootstrap_manual_drops.sh
# Safe to re-run; existing dirs/READMEs are left untouched.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MANUAL="data/manual"
mkdir -p "$MANUAL"

write_readme() {
  local dir="$1"
  local content="$2"
  mkdir -p "$dir"
  if [ ! -f "$dir/README.md" ]; then
    printf '%s\n' "$content" > "$dir/README.md"
    echo "  created $dir/README.md"
  else
    echo "  skip    $dir/README.md (exists)"
  fi
}

echo "Bootstrapping manual-drop directories under $MANUAL/"

# --- IEA ----------------------------------------------------------------
write_readme "$MANUAL/iea/industrial_electricity_price" \
'IEA Energy Prices — industrial electricity price (quarterly, USD/MWh)

Drop the latest IEA Energy Prices industrial electricity CSV or XLSX here.
The fetcher (data/fetchers/iea.py) picks the latest file matching
*.csv / *.xlsx / *.xls in this directory.

Source:     https://www.iea.org/data-and-statistics/data-product/energy-prices
Methodology: https://www.iea.org/reports/energy-prices-2024

Expected columns (any order; fetcher is tolerant):
  country, period (quarter or date), value (USD/MWh), product (electricity),
  sector (industry). Additional columns are preserved as-is.

The fetcher also tries the IEA landing page automatically before reading
this directory; the manual drop is the fallback when Cloudflare blocks
the automated probe.'

write_readme "$MANUAL/iea/fossil_subsidies_estimate" \
'IEA Fossil-Fuel Subsidies tracker — consumption subsidies (annual, USDbn)

Drop the latest IEA Fossil-Fuel Subsidies CSV or XLSX here.

Source: https://www.iea.org/data-and-statistics/data-product/fossil-fuel-subsidies-database

Expected columns: country, year, product (oil/gas/coal/electricity),
value (USD billion). Fetcher parses first/widest sheet if XLSX.'

write_readme "$MANUAL/iea/co2_emissions_from_fuel_combustion" \
'IEA CO2 Emissions from Fuel Combustion — Highlights (annual, Mt CO2)

Drop the latest IEA CO2 Highlights country-year CSV or XLSX here.

Source: https://www.iea.org/data-and-statistics/data-product/greenhouse-gas-emissions-from-energy-highlights

Expected columns: country, year, value (Mt CO2).'

# --- IRENA --------------------------------------------------------------
write_readme "$MANUAL/irena" \
'IRENA manual-drop fallback directory

The IRENA fetcher (data/fetchers/irena.py) tries the PxWeb API first:
  https://pxweb.irena.org/api/v1/en/IRENASTAT/Power Capacity and Generation/

If PxWeb is down or returns 404 for the candidate table list, the fetcher
falls back to files dropped in this directory. Capacity series match on
filename substring (e.g. "solar", "wind", "capacity"); LCOE series expect
the IRENA Renewable Power Generation Costs workbook with a "Fig S.1" sheet.

Supported series:
  installed_capacity_renewable  — total renewable capacity by country/year (MW)
  installed_capacity_solar_pv   — solar PV installed capacity (MW)
  installed_capacity_wind       — wind installed capacity (MW, on+offshore)
  lcoe_solar_pv                 — LCOE solar PV (USD/MWh) [expects Fig S.1 sheet]
  lcoe_wind_onshore             — LCOE onshore wind (USD/MWh) [expects Fig S.1 sheet]

Capacity downloads: https://www.irena.org/Data
LCOE downloads:     https://www.irena.org/Publications  (Renewable Power Generation Costs report)

For capacity series, name files to include the technology hint, e.g.:
  irena_solar_pv_capacity_2024.xlsx
  irena_wind_capacity_2024.xlsx
  irena_total_renewable_capacity_2024.xlsx

For LCOE, drop the full report workbook (it contains the Fig S.1 sheet the
parser expects).'

# --- IMF IFS (manual-drop; public SDMX deprecated) ----------------------
write_readme "$MANUAL/imf_ifs" \
'IMF International Financial Statistics / BOP / AREAER — manual drop

IMF deprecated all public SDMX endpoints in 2024 in favour of Power BI
Embedded at data.imf.org. There is no programmatic API. Sign in once at
data.imf.org, export the relevant dataset as CSV, and drop it here.

Supported series (data/fetchers/imf_ifs.py):
  IFS series:  FIDR_PA, FIGB_PA, FMA_USD  (policy rates, govt bond yields, money)
  BOP/IIP:     BFOAFA, BFXFA              (financial account, portfolio flows)
  AREAER:      exchange rate regime assessments
  FSI:         financial soundness indicators not in WEO DataMapper

Source: https://data.imf.org/

Name files by dataset, e.g.:
  IFS_QUARTERLY_USA_DEU_JPN_2000_2024.csv
  BOP_ANNUAL_PANEL.csv'

# --- Fraser EFW ---------------------------------------------------------
write_readme "$MANUAL/fraser_efw" \
'Fraser Institute Economic Freedom of the World — manual drop

Cloudflare blocks all automated paths. Download the master xlsx manually:
  https://www.fraserinstitute.org/economic-freedom/dataset

Drop it here with Fraser’s own filename convention, e.g.:
  efotw-2024-master-index-data-for-researchers-iso.xlsx

The fetcher picks the latest-filename match. Annual refresh cadence.'

# --- WID ----------------------------------------------------------------
write_readme "$MANUAL/wid" \
'World Inequality Database (WID) — manual drop

Bulk downloads at wid.world are gated behind a browser flow. Sign in,
download the per-country bulk CSVs, and drop them here.

Source: https://wid.world/data/

Expected: one CSV per country (or a single combined file). Columns per WID
bulk schema (country, year, variable, percentile, value).'

# --- PWT ----------------------------------------------------------------
write_readme "$MANUAL/pwt" \
'Penn World Tables 10.01 — manual drop

GGDC xlsx URLs 404 on automated fetch. Download pwt1001.xlsx from:
  https://www.rug.nl/ggdc/productivity/pwt/

Drop it here. The fetcher expects the standard PWT 10.01 workbook layout.'

# --- Swiss (BAK/KOF/FSO/OBSAN) ------------------------------------------
for d in bak_swiss swiss_fso swiss_obsan; do
  write_readme "$MANUAL/$d" \
"Swiss statistical sources — manual drop ($d)

See data/fetchers/publishers.yaml under publisher '$d' for the exact
series and expected schema. Drop the latest XLSX/CSV exports from the
relevant source (BAK Economics, KOF ETH, Swiss FSO, OBSAN) here, organised
by series_id subdirectory where the fetcher expects it."
done

# --- Singapore / Chile / Australia pension ------------------------------
for d in singapore_cpf singapore_moh chile_spensiones apra; do
  write_readme "$MANUAL/$d" \
"Pension/healthcare outcomes — manual drop ($d)

See data/fetchers/publishers.yaml under publisher '$d' for the exact series.
Drop the latest official statistical release (XLSX/CSV) here."
done

# --- OPEC / SAMA / GASTAT (all JS-gated) --------------------------------
for d in opec sama gastat; do
  write_readme "$MANUAL/$d" \
"Energy/stats publisher — manual drop ($d)

All automated endpoint attempts 404/403. Data is public but requires
headless-browser scrape or manual one-shot capture. Drop the latest
release XLSX/CSV here. See publishers.yaml for series_id conventions."
done

# --- Transparency CPI / WJP (browser-gated) -----------------------------
write_readme "$MANUAL/transparency_cpi" \
'Transparency International Corruption Perceptions Index — manual drop

transparencycdn.org returns 403 on direct XLSX. Available via OWID mirror
in the interim. For the primary-source vintage, download the CSV from:
  https://www.transparency.org/en/cpi
and drop it here.'

write_readme "$MANUAL/wjp_rol" \
'World Justice Project Rule of Law Index — manual drop

WJP downloads page loads data links via AJAX. Download the latest Index
XLSX from:
  https://worldjusticeproject.org/rule-of-law-index/
and drop it here.'

# --- BoJ (form-driven) --------------------------------------------------
write_readme "$MANUAL/boj" \
'Bank of Japan — manual drop

BoJ stat-search is form-driven with session state. JPN M2 is available
via FRED mirror (JPNM2MB) for interim use. For the primary BoJ vintage,
download the relevant statistical release and drop it here.'

echo
echo "Done. Manual-drop directories are ready. Drop the actual files in to"
echo "unlock their publishers. See data/fetchers/publishers.yaml for the"
echo "full publisher registry and each fetcher module for parsing details."
