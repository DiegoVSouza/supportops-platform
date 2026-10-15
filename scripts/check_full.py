#!/usr/bin/env python3
"""Run real local checks and preserve the separate package integration gate."""

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
commands = [
    [sys.executable, "-m", "compileall", "-q", "supportops_platform", "tests"],
    ["uv", "run", "--locked", "pytest"],
    ["uv", "run", "--locked", "python", "scripts/eval_retrieval.py"],
    [sys.executable, "scripts/verify_packages.py"],
]
failures = []
for command in commands:
    result = subprocess.run(command, cwd=root, text=True, capture_output=True)
    label = " ".join(command)
    print(f"$ {label}\nexit_code={result.returncode}")
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    if result.returncode:
        failures.append((label, result.returncode))
if failures:
    print("check-full: INCOMPLETE; local checks ran and one or more mandatory gates remain unavailable")
    sys.exit(2)
print("check-full: PASS")
