#!/usr/bin/env python3
"""Report integration readiness without importing from neighboring repositories."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "docs/harness/sources.lock.json").read_text(encoding="utf-8"))
names = {"p01_package": "P01 orchestration", "p02_package": "P02 toolkit", "p03_package": "P03 observability", "p04_package": "P04 async"}
pending = []
for key, label in names.items():
    item = manifest[key]
    complete = all(item.get(field) not in (None, "", "PENDING") for field in ("version", "origin_commit", "artifact_sha256"))
    ready = complete and item.get("approved") is True and item.get("installed_verified") is True
    status = "READY" if ready else "INCOMPLETE"
    print(f"{label}: {status}")
    if not ready:
        pending.append(label)
if pending:
    print("Package integration gate: INCOMPLETE (" + ", ".join(pending) + ")")
    sys.exit(2)
print("Package integration gate: PASS")
