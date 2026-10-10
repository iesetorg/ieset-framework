#!/usr/bin/env python3
import os, subprocess, sys
root=os.environ.get('IESET_RAW_ROOT')
if not root: raise SystemExit('set IESET_RAW_ROOT to the matching raw cache')
raise SystemExit(subprocess.call([sys.executable,'scripts/run_fao_food_supply_nutrition_2026.py','--verify','--source-root',root]))
