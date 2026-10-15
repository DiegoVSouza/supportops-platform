# Local Package Integration Gate

P05 does not import source from sibling repositories. Each integration requires a
locally built wheel and a review record with package version, source commit, wheel
SHA-256, compatibility result, and `approved: true`. A dependency must also be
installed and exercised by a contract test before it can enter the release gate.

| Project | Package | Version | Source commit | Artifact SHA-256 | Approved |
| --- | --- | --- | --- | --- | --- |
| P01 | PENDING | PENDING | PENDING | PENDING | No |
| P02 | supportops-ai-toolkit | 0.1.0 | `00a5f9b8e1f9c78ea26f09839d24847cfcfbf6f6` | `5B7F1BBD9DD015620D5CB9CBCF6B4B39B1D2DC668805B066E7A2D9A930D48A52` | No |
| P03 | supportops_obs | 0.1.0 | `7d78bf63f42b03c510792773ad2c9915015120e9` | `e4e80cd664c97cf38b8fbe5557f10d4c8d247af275412569fb6a1bcbc0f11575` | No |
| P04 | PENDING | PENDING | PENDING | PENDING | No |

The P02 and P03 provenance values were supplied by the coordinator, but their
contracts/artifacts have not been approved for this consumer. Their integration stays
`INCOMPLETE`; these entries do not enable imports or satisfy the gate.

Run `uv run --locked python scripts/verify_packages.py` to evaluate the manifest.
Successful package validation is a release prerequisite, not a local unit-test result.
