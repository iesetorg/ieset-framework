#!/usr/bin/env python3
import subprocess, sys
raise SystemExit(subprocess.call([sys.executable, 'scripts/run_eu_tax_social_holdout_2026.py', '--verify', *sys.argv[1:]]))
