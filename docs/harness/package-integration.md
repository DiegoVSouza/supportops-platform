# Local Package Integration Gate

P05 does not import source from sibling repositories. Each integration requires a
locally built wheel and a review record with package version, source commit, wheel
SHA-256, compatibility result, and `approved: true`. A dependency must also be
installed and exercised by a contract test before it can enter the release gate.

| Project | Package | Version | Source commit | Artifact SHA-256 | Approved |
| --- | --- | --- | --- | --- | --- |
| P00 | supportops-foundation | 1.0.1 | `607b7603bd40728ffa58745badac0ffd10c70090` | `DF4292756676D02490A908B609B8F9474F35F3C5F56131809F3E4A83659B4795` | Yes |
| P01 | supportops-agents | 0.1.1 | `4c70b1ea3e23606dfe60ffae77567417de53a3f7` | `DD77E9B91F2D9BA7AC84178BBB557E0EA50BDE954554A528B4632DEC18DDB51F` | Yes; P05 installed version assertion passes |
| P02 | supportops-ai-toolkit | 0.2.0 | `b4966c54fa3feda3ff1eae36ee872e5c407a4102` | `7126517f9c64202b034b8a067dedf29e1313bb3139f15a984e93660654eb4d10` | Yes; P05 installed version assertion passes |
| P03 | supportops-obs | 0.3.1 | `e191f17d4649f40d6dea7057d3b52729dbbb1389` | `82b3a79aacd0ac4faa1082087c0237487264b2a6497d9b77b79c1d6bb86f66a8` | Yes; P05 installed consumer tests pass |
| P04 | supportops-async | 0.1.4 | `f4b5df828b397e7ecbb9fa87c0ef77485d829dca` | `FEFB871993591CABE9F7BABA132E9F430DDBD65DD730C6789E22DC86D4D87C3F` | Yes; P05 Redis Streams/worker recovery E2E passes |

P00, P01, P02, and P04 are installed from versioned local wheels and their P05
consumer checks pass. P05 0.4.3 is released locally; source commit, artifact commit,
wheel SHA-256, and isolated real PostgreSQL migration consumer are recorded in
`sources.lock.json` and `phase-017-wheel-*.txt`. P03 0.3.0 was superseded after its consumer exposed an
OpenTelemetry `NonRecordingSpan.status` failure. The replacement 0.3.1 has exact
upstream source/artifact provenance and passed the isolated producer smoke; P05
consumer verification passes with the non-recording span regression test. P04 0.1.2 declares FastAPI
`>=0.137.1,<0.143.0` and Uvicorn
`==0.46.0`; P05 pins compatible FastAPI 0.142.4 and Uvicorn 0.46.0. PostgreSQL and
Redis Streams-backed P04 integration passes in the named isolated local E2E; it is not an
external deployment or a claim of exactly-once effects outside the product ledger.

Run `uv run --locked python scripts/verify_packages.py` to evaluate the manifest.
Successful package validation is a release prerequisite, not a local unit-test result.
