"""Fetch inputs for batch-2 tests AFTER spec commit b79b1fb1e. Writes gitignored vintages + one tracked manifest."""
import sys, pathlib, json, traceback, datetime, requests
ROOT = pathlib.Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from data.fetchers import fred, eurostat, shiller, eia_v2, imf_weo_sdmx
from data.fetchers._base import write_manifest, utc_now
OK, ERR = [], []
def go(label, fn):
    try: r = fn(); OK.append(r); print("ok", label, getattr(r, "row_count", ""), getattr(r, "path", ""))
    except Exception as e: ERR.append((label, repr(e))); print("ERR", label, repr(e)[:300])
for s in ["PSAVERT","CES0500000003","CPIAUCSL","A229RX0","MEHOINUSA672N","FYOINT","FYFR","FYFSD","MTSDS133FMS","PNGASEUUSDM","DEXUSUK","MORTGAGE30US"]:
    go("fred:"+s, lambda s=s: fred.fetch(s))
EU27 = "AT BE BG HR CY CZ DK EE FI FR DE EL HU IE IT LV LT LU MT NL PL PT RO SK SI ES SE".split()
for tax in ["X_VAT","I_TAX","X_TAX"]:
    go("eurostat:nrg_pc_205 EUR "+tax, lambda tax=tax: eurostat.fetch("nrg_pc_205", params={"nrg_cons":"MWH2000-19999","tax":tax,"currency":"EUR","unit":"KWH","siec":"E7000"}))
go("eurostat:nrg_pc_205 UK NAC", lambda: eurostat.fetch("nrg_pc_205", params={"geo":"UK","tax":"X_VAT","currency":"NAC","unit":"KWH","siec":"E7000"}))
go("eurostat:nrg_bal_peh", lambda: eurostat.fetch("nrg_bal_peh", params={"nrg_bal":"GEP","unit":"GWH","siec":["TOTAL","RA300","RA410","RA420"]}))
go("eurostat:prc_hicp_aind UK", lambda: eurostat.fetch("prc_hicp_aind", params={"geo":"UK","coicop":"CP00","unit":"INX_A_AVG"}))
go("eurostat:sts_inpr_q DE CH", lambda: eurostat.fetch("sts_inpr_q", params={"geo":["DE","CH"],"nace_r2":"C","indic_bt":"PRD","s_adj":"SCA","unit":"I21"}))
go("shiller:home_price_index", lambda: shiller.fetch("home_price_index"))
go("eia_v2 monthly RES", lambda: eia_v2.fetch("electricity/retail-sales", frequency="monthly", data=["price"], facets={"sectorid":["RES"],"stateid":["AL","US"]}, start="2023-01"))
go("imf_weo_sdmx:NGDPRPC", lambda: imf_weo_sdmx.fetch("NGDPRPC"))
go("imf_weo_sdmx:NGDP_R", lambda: imf_weo_sdmx.fetch("NGDP_R"))
go("imf_weo_sdmx:LP", lambda: imf_weo_sdmx.fetch("LP"))
# Census historical poverty Table 2 (official measure) - raw file
try:
    u = "https://www2.census.gov/programs-surveys/cps/tables/time-series/historical-poverty-people/hstpov2.xlsx"
    r = requests.get(u, timeout=60); r.raise_for_status()
    d = ROOT/"data/vintages/us_census"; d.mkdir(parents=True, exist_ok=True)
    p = d/f"hstpov2@{utc_now().strftime('%Y%m%dT%H%M%SZ')}.xlsx"; p.write_bytes(r.content); print("ok census hstpov2", p, len(r.content))
except Exception as e: ERR.append(("census:hstpov2", repr(e))); print("ERR census", e)
try: print("manifest", write_manifest(OK))
except Exception as e: print("manifest ERR", e)
print("errors:", json.dumps(ERR, indent=1))
