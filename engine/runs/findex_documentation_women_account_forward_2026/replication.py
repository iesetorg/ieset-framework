#!/usr/bin/env python3
import subprocess, sys
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_findex_financial_pathways_2026.py', '--verify', *sys.argv[1:]]))
