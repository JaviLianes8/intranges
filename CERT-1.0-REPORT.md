# intranges 1.0.0 certification report

Progress:
- [x] Resume release/1.0.0 from the existing report commit 18b790f.
- [x] Baseline: 365 tests pass; format and lint pass; strict test typing found three errors.
- [x] Live PyPI query on 2026-11-03: intranges 0.2.0 is published.
- [x] Specifications fetched on 2026-11-03; hashes and URLs in tests/sources.json.
- [x] Stable API, safe errors, bounded parser cache, explicit types and runnable examples.
- [x] Regression contracts, seeded fuzz, README, guide and dated CHANGELOG.
- [ ] Final package inspection, interpreter matrix and upgrade evidence.
- [ ] Mutation round and final four gates.
- [ ] Independent review and five QA lenses (separate stage).
- [ ] PR and release handoff; merge and publication remain pending.

## Preparation scope

The 22 public names from 0.2.0 remain. Changes and resource limits are listed in
CHANGELOG 1.0.0. The HTTP preset is a selection grammar, not full HTTP field validation.
The specification examples in test_sources.py are short cited vectors; the other
handwritten cases are derived contracts. Full external source files stay outside the
repository. scripts/fetch_sources.py recreates the optional source evidence, with
hash verification. Set INTRANGES_SOURCES to that directory to verify it in pytest.

## Baseline

Main f1cd4a6 is version 0.2.0. The existing release branch contained only its initial
report; there were no unfinished edits or earlier QA verdicts. The PyPI JSON endpoint
https://pypi.org/pypi/intranges/json returned HTTP 200 and version 0.2.0 on 2026-11-03.
The actual release was installed into a separate environment for upgrade checks.
