# Local Package Integration Gate

P05 does not import source from sibling repositories. Each integration requires a
locally built wheel and a review record with package version, source commit, wheel
SHA-256, compatibility result, and `approved: true`. A dependency must also be
installed and exercised by a contract test before it can enter the release gate.

| Project | Package | Version | Source commit | Artifact SHA-256 | Approved |
| --- | --- | --- | --- | --- | --- |
| P00 | supportops-foundation | 1.0.1 | `607b7603bd40728ffa58745badac0ffd10c70090` | `DF4292756676D02490A908B609B8F9474F35F3C5F56131809F3E4A83659B4795` | Yes |
| P01 | supportops-agents | 0.1.0 | `af06f4c564d2e601ac8009ecb32ae7e529b72c83` | `9F360E98FC1DF9D9D10CCDAB51F0AF0CCEF5F1A17CD49CEFEC9E2E3A8A4BED8B` | Yes |
| P02 | supportops-ai-toolkit | 0.1.0 | `00a5f9b8e1f9c78ea26f09839d24847cfcfbf6f6` | `5B7F1BBD9DD015620D5CB9CBCF6B4B39B1D2DC668805B066E7A2D9A930D48A52` | Yes |
| P03 | supportops-obs | 0.1.0 | `7d78bf63f42b03c510792773ad2c9915015120e9` | `e4e80cd664c97cf38b8fbe5557f10d4c8d247af275412569fb6a1bcbc0f11575` | Yes |
| P04 | supportops-async | 0.1.0 | `d66bf316eedb2a5a810bc0a35ebf80d37f4474ab` | `5210a3c87afa7680c81ac6a7d2e37f16651e2ee06981a4ff9c1bc26c51725e23` | Yes |

P00–P03 are installed from approved local wheels, hash-checked, and exercised by
consumer tests. P04's SQLite/in-memory API was tested from its approved wheel as a
diagnostic using `--no-deps`. Its wheel requires `fastapi==0.137.1`, while P05 pins
`fastapi==0.142.4`; full locked dependency resolution therefore remains `INCOMPLETE`.
The P04 diagnostic does not satisfy its release gate. P04 is omitted from P05's
reproducible dependency lock until a compatible versioned artifact is approved.

Run `uv run --locked python scripts/verify_packages.py` to evaluate the manifest.
Successful package validation is a release prerequisite, not a local unit-test result.
