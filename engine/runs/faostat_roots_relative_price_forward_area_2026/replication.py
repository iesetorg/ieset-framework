#!/usr/bin/env python3
import os
import subprocess
import sys
root = os.environ.get('IESET_RAW_ROOT')
if not root:
    raise SystemExit('set IESET_RAW_ROOT to the matching raw FAOSTAT cache')
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_faostat_relative_price_supply_2026.py', '--source-root', root, '--verify']))
