#!/usr/bin/env python3
import os
import subprocess
import sys
source = os.environ.get('IESET_RAW_ROOT')
if not source:
    raise SystemExit('set IESET_RAW_ROOT to the matching local raw cache')
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_cckp_faostat_weather_named_crop_ppi_2026.py', '--source-root', source, '--verify']))
