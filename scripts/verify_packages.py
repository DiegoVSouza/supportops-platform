#!/usr/bin/env python3
"""Report integration readiness without importing from neighboring repositories."""

import json
import hashlib
from importlib.metadata import PackageNotFoundError, version
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "docs/harness/sources.lock.json").read_text(encoding="utf-8"))
names = {
    "p00_package": "P00 foundation",
    "p01_package": "P01 orchestration",
    "p02_package": "P02 toolkit",
    "p03_package": "P03 observability",
    "p04_package": "P04 async",
}
pending = []
for key, label in names.items():
    item = manifest[key]
    complete = all(
        isinstance(item.get(field), str)
        and item[field] not in ("",)
        and not item[field].startswith("PENDING")
        for field in ("version", "origin_commit", "artifact_sha256")
    )
    ready = complete and item.get("approved") is True
    if ready:
        artifact = ROOT / item["artifact_path"]
        actual_hash = hashlib.sha256(artifact.read_bytes()).hexdigest().upper()
        try:
            actual_version = version(item["name"])
        except PackageNotFoundError:
            actual_version = "NOT_INSTALLED"
        ready = (
            actual_hash == item["artifact_sha256"].upper()
            and actual_version == item["version"]
            and item.get("installed_verified") is True
            and not str(item.get("dependency_resolution", "")).startswith("INCOMPLETE")
        )
        print(f"  version={actual_version} sha256={actual_hash} source_commit={item['origin_commit']}")
    elif item.get("approved") is False:
        print(f"  provenance=awaiting approved package artifact")
    status = "READY" if ready else "INCOMPLETE"
    print(f"{label}: {status}")
    if not ready:
        pending.append(label)
if pending:
    print("Package integration gate: INCOMPLETE (" + ", ".join(pending) + ")")
    sys.exit(2)
print("Package integration gate: PASS")
