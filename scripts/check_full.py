#!/usr/bin/env python3
"""Execute local gates; required omissions fail closed independently of model evals."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--skip-services',action='store_true')
    args=parser.parse_args()
    commands=[
        ([sys.executable,'-m','compileall','-q','supportops_platform','tests'],0,'compile'),
        ([sys.executable,'-m','pytest'],0,'unit/contract/package consumer'),
        ([sys.executable,'scripts/eval_retrieval.py'],0,'retrieval fixture'),
        ([sys.executable,'scripts/export_openapi.py','--check'],0,'OpenAPI'),
        ([sys.executable,'scripts/verify_packages.py'],0,'package provenance'),
        ([sys.executable,'scripts/check_quality.py'],0,'fake control evaluation'),
        ([sys.executable,'scripts/check_quality.py','--degraded'],1,'negative regression rejection'),
    ]
    if not args.skip_services:
        commands.append(([sys.executable,'scripts/check_services.py'],0,'service integration/E2E/crash recovery'))
    failures=[]
    for command,expected,layer in commands:
        result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
        print('$ '+' '.join(command)+f'\nlayer={layer}\nexit_code={result.returncode}; expected={expected}',flush=True)
        print(result.stdout+result.stderr,flush=True)
        if result.returncode!=expected: failures.append(layer)
    if args.skip_services:
        print('required service integration: INCOMPLETE; explicitly omitted')
    print('semantic/model cost/latency evaluation: PENDING; no traceable cassette or authorized model run')
    if failures or args.skip_services:
        print('check-full: INCOMPLETE; '+', '.join(failures))
        return 2
    print('check-full: PASS (authorized local fake-mode acceptance)')
    return 0

if __name__=='__main__': raise SystemExit(main())
