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
| P04 | supportops-async | 0.1.1 | `6a074e906b080fdb837907237787f623f17c3e3c` | `250985c33e334b1e8f1c31bf8dcfe770ed8ff20419b96decaa9adf9d05010c1f` | Yes |

P00–P04 are installed from approved local wheels, hash-checked, and exercised by
consumer tests. P04 0.1.1 declares FastAPI `>=0.137.1,<0.143.0` and Uvicorn
`==0.46.0`; P05 pins compatible FastAPI 0.142.4 and Uvicorn 0.46.0. PostgreSQL/SQS
service-backed integration remains `INCOMPLETE`; the local SQLite/in-memory test
does not represent those external services.

Run `uv run --locked python scripts/verify_packages.py` to evaluate the manifest.
Successful package validation is a release prerequisite, not a local unit-test result.
