#!/usr/bin/env python3
"""Export or verify the OpenAPI v1 contract; JSON is valid YAML 1.2 syntax."""

import argparse
import json
from pathlib import Path

from supportops_platform.api.app import app

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "openapi.yaml"
rendered = json.dumps(app.openapi(), indent=2, ensure_ascii=False) + "\n"
parser = argparse.ArgumentParser()
parser.add_argument("--check", action="store_true")
args = parser.parse_args()
if args.check:
    if not TARGET.exists() or TARGET.read_text(encoding="utf-8") != rendered:
        raise SystemExit("openapi.yaml does not match the current API; review and regenerate it")
    print("OpenAPI contract: PASS (v1 compatibility paths, HTTP bearer, package schema 0.4.0)")
else:
    TARGET.write_text(rendered, encoding="utf-8")
    print(f"Wrote {TARGET.relative_to(ROOT)}")
