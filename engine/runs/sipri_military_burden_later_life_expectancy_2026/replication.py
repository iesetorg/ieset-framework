#!/usr/bin/env python3
import os
import subprocess
import sys
source_root = os.environ.get('IESET_RAW_ROOT')
if not source_root:
    raise SystemExit('set IESET_RAW_ROOT to the matching local raw cache')
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_sipri_undp_military_burden_2026_packet_hash.py', '--source-root', source_root, '--verify']))
