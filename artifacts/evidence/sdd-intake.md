# P05 intake and SDD evidence

- Command: `python -c "import json,pathlib,yaml; root=pathlib.Path('.'); cfg=yaml.safe_load((root/'harness.yaml').read_text()); assert cfg['product']['rag'] and cfg['risk']['governance']=='full'; json.loads((root/'docs/harness/sources.lock.json').read_text()); assert all((root/'.planning/phases'/p/n).is_file() for p in sorted(x.name for x in (root/'.planning/phases').iterdir()) for n in ['SPEC.md','PLAN.md','VERIFY.md']); print('P05 intake/SDD/profile structure: PASS')"`
- Exit code: `0`
- Output: `P05 intake/SDD/profile structure: PASS`
- Plan review: coordinator accepted six phases before product implementation; each PLAN lists 2–4 tasks, owned paths, forbidden changes, checks, and stop condition.
- Product implementation at time of check: not started.
