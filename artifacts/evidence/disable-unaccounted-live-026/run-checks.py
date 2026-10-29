import json
import os
import subprocess
import sys
from pathlib import Path

project = Path(__file__).resolve().parents[3]
env = os.environ.copy()
env["LLM_MODE"] = "fake"
commands = [[sys.executable, "scripts/check_fast.py"], [sys.executable, "-m", "pytest", "-q", "tests", "--basetemp=artifacts/evidence/disable-unaccounted-live-026/pytest-tmp2"]]
reports = []
for command in commands:
    result = subprocess.run(command, cwd=project, env=env, capture_output=True, text=True, timeout=180)
    reports.append({"command": " ".join(command), "cwd": str(project), "exit_code": result.returncode, "output": result.stdout + result.stderr})
    print(command[1], result.returncode)
    if result.returncode:
        break
(Path(__file__).resolve().parent / "checks-runtime-attempt1.json").write_text(json.dumps(reports, indent=2) + "\n", newline="\n")
sys.exit(any(report["exit_code"] for report in reports))
