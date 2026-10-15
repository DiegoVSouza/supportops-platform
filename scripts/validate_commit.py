"""Validate the lab's Conventional Commit header."""
import pathlib
import re
import sys

PATTERN = re.compile(r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)\([a-z0-9][a-z0-9_.,/ -]*\)!?: \S.*$")

if __name__ == '__main__':
    message = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8-sig')
    header = message.splitlines()[0] if message.splitlines() else ''
    if not PATTERN.fullmatch(header):
        print('Invalid commit. Expected type(scope): imperative English description', file=sys.stderr)
        sys.exit(1)
