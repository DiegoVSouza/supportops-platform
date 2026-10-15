#!/usr/bin/env python3
"""Run real local checks and preserve the separate package integration gate."""

import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
commands = [
    [sys.executable, "-m", "compileall", "-q", "supportops_platform", "tests"],
    ["uv", "run", "--locked", "pytest"],
    ["uv", "run", "--locked", "python", "scripts/eval_retrieval.py"],
    ["uv", "run", "--locked", "python", "scripts/export_openapi.py", "--check"],
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
    print("local-checks: INCOMPLETE; one or more executed checks failed")
    sys.exit(2)
feature_inventory = json.loads(
    (root / "docs/harness/feature_list.json").read_text(encoding="utf-8")
)
outstanding = [
    f"{feature['id']}={feature['status']}"
    for feature in feature_inventory.get("features", [])
    if feature.get("status") != "PASS"
]
if outstanding:
    print("local-checks: PASS")
    print("product-acceptance: INCOMPLETE (" + ", ".join(outstanding) + ")")
    print("check-full: INCOMPLETE; local checks passed but required product features remain")
    sys.exit(2)
print("local-checks: PASS")
print("product-acceptance: PASS")
print("check-full: PASS")
