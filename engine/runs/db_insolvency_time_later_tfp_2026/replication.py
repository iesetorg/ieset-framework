#!/usr/bin/env python3
import os, subprocess, sys
source_root=os.environ.get('IESET_SOURCE_ROOT')
workbook=os.environ.get('IESET_DB_WORKBOOK')
if not source_root or not workbook: raise SystemExit('set IESET_SOURCE_ROOT and IESET_DB_WORKBOOK')
raise SystemExit(subprocess.call([sys.executable,'scripts/run_doing_business_insolvency_followup_2026_key_adapter.py','--verify','--source-root',source_root,'--workbook',workbook]))
