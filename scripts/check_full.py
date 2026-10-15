#!/usr/bin/env python3
import pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
result = subprocess.run([sys.executable, str(root / 'scripts/check_fast.py')])
if result.returncode: sys.exit(result.returncode)
print('check-full: INCOMPLETE until the project defines product validation')
