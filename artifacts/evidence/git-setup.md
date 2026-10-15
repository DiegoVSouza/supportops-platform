# Git setup verification

Project: `C:\estudo\Golpe\lab\projects\p05`

Commands are executed from the project root. Expected rejection for the invalid hook message is recorded as PASS.

## PASS — `git rev-parse --show-toplevel`
- Exit code: `0`
- stdout: `C:/estudo/Golpe/lab/projects/p05`
- stderr: `(empty)`

## PASS — `git branch --show-current`
- Exit code: `0`
- stdout: `main`
- stderr: `(empty)`

## PASS — `git config --local --get core.hooksPath`
- Exit code: `0`
- stdout: `.githooks`
- stderr: `(empty)`

## PASS — `git var GIT_AUTHOR_IDENT`
- Exit code: `0`
- stdout: `Diego Souza <redacted> 1792074136 -0300`
- stderr: `(empty)`

## PASS — `git rev-parse --verify HEAD`
- Exit code: `0`
- stdout: `07a823a59d17dd2f827d44ab3f419db4a7bc954a`
- stderr: `(empty)`

## PASS — `git hook run commit-msg -- C:\estudo\Golpe\lab\projects\p05\hook-check-_a1jz1i6\invalid.txt`
- Exit code: `1`
- stdout: `(empty)`
- stderr: `Invalid commit. Expected type(scope): imperative English description`

## PASS — `git hook run commit-msg -- C:\estudo\Golpe\lab\projects\p05\hook-check-_a1jz1i6\valid.txt`
- Exit code: `0`
- stdout: `(empty)`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index .env`
- Exit code: `0`
- stdout: `.env`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index .venv/bin/python`
- Exit code: `0`
- stdout: `.venv/bin/python`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index __pycache__/module.pyc`
- Exit code: `0`
- stdout: `__pycache__/module.pyc`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index .pytest_cache/cache`
- Exit code: `0`
- stdout: `.pytest_cache/cache`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index secret.pem`
- Exit code: `0`
- stdout: `secret.pem`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index private.key`
- Exit code: `0`
- stdout: `private.key`
- stderr: `(empty)`

## PASS — `git check-ignore --no-index .env.example`
- Exit code: `1`
- stdout: `(empty)`
- stderr: `(empty)`
