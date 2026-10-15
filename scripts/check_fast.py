#!/usr/bin/env python3
import pathlib, sys
root = pathlib.Path(__file__).resolve().parents[1]
required = ['harness.yaml', 'AGENTS.md', '.harness/modules.lock']
missing = [p for p in required if not (root / p).exists()]
print('check-fast:', 'OK' if not missing else 'FAIL')
for p in missing: print('missing:', p)
sys.exit(bool(missing))
