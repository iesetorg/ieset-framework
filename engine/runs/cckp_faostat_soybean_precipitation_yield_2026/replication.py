#!/usr/bin/env python3
import os
import subprocess
import sys
root = os.environ.get('IESET_RAW_ROOT')
if not root:
    raise SystemExit('set IESET_RAW_ROOT to the matching raw cache')
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_cckp_faostat_weather_crop_2026.py', '--source-root', root, '--verify']))
