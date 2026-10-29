from pathlib import Path

root = Path(__file__).resolve().parents[3]
for name in ("run_live_groq_eval.py", "check_live_services.py"):
    path = root / "scripts" / name
    source = path.read_text(encoding="utf-8")
    start = source.index("def main(")
    end = source.index('if __name__ == "__main__":', start)
    guard = '''def main():
    print(json.dumps({"status": "INCOMPLETE", "reason": "accounted_guard_required", "provider_accessed": False, "credentials_read": False}))
    return 2


'''
    path.write_text(source[:start] + guard + source[end:], encoding="utf-8", newline="\n")
