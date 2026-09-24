# A15: small README facts corrected

20 September 2026 · facts slice complete locally; broader support wording open

The [root README](../../README.md#run-the-tests) and
[skill README](../../pdf-translate/README.md) now use full unittest discovery,
state the actual 11-file font configuration, and install the declared
requirements through the chosen Python interpreter. Font presence does not
promise zero skips or successful tests. Contributor test commands are explicitly
for a checkout; wheel/sdist contents remain separate packaging work.

The root's repository map points to the current backlog and dated audit, labels
the old HTML checklist historical, and describes the actual CI validation scope.
The unsupported 25-second local/40-second CI timing promise was removed. Its
replacement identifies the existing **19 September v58 Windows/Python 3.14**
measurement of **202.730 seconds**, without extrapolating it to other runs.
The shipped README instructions advance the four version sources to v61 locally.

## Verification

All checks below used the existing repo virtual environment, from
`pdf-translate/`, with `PYTHONUTF8=1`.

- Extracted each README's `python[3] -m unittest` arguments and passed them to
  `unittest.TestProgram` with a collection-only runner. Both discovered **492
  test cases across 11 modules, zero import errors**. Their test-ID sets match
  the CI workflow's explicit module selection. No test bodies were run by this
  check. The old two-module selection collected **230**, omitting **262**.
- Read the fetcher's `FONTS` literal: **11** names. Ran
  `python tools/fetch_test_fonts.py --check`: exit 0, all test fonts present.
  No download, font replacement, hash/provenance assertion or rendering change.
- Compared `requirements.txt` with `pyproject.toml`: the same three constraints
  (`pymupdf>=1.24,<1.30`, `pikepdf>=8.0,<11`, `fonttools>=4.40,<5`).
  `python -m pip install --dry-run --no-index -r requirements.txt` exited 0;
  all requirements were already satisfied. It installed nothing and used no
  package index. This does not prove minimum-version support or a fresh install.
- Re-read `runs/public-readiness-audit-2026-09-19/unittest.log` and the saved
  audit environment record: `Ran 492 tests in 202.730s`, `OK`, zero skips at v58.
  That is prior evidence, not a new full-suite result.
- `python -m unittest tests.test_verify_report.VersionLockstepTests -v`:
  **Ran 1 test in 0.063s; OK**, exit 0. The only Python edits this turn are
  the version constant and its matching test expectation.
- `git diff --check`: exit 0. Before-images are retained in ignored
  `runs/a15-readme-facts-2026-09-20/before/` to separate this slice from prior work.

The revised full-suite command, for a normal contributor run, is:

```bash
python -m unittest discover -s tests -t . -v
```

This slice verified its collection; it did not execute the full suite or start
hosted CI. PDF execution logic, rendering and dependency bounds were not changed. Wider
public-support claims, license disclosures, host onboarding and package contents
remain in their existing backlog scopes. **A15 stays partial** in the
[canonical backlog](../../dev/goals/PROGRAM.md#public-readiness-backlog).

Next smallest recommendation: A21's explicit validation of both Claude manifests.
No commit, push, merge, release, PR edit or app-task message occurred. Read-only
git/gh checks found HEAD `1d4f970` on `codex/b1-design-canvas`, remote main
`a5629fb`, and PRs #12/#13 OPEN at `abc4767` / `1d4f970`, still stacked. All
previous local work was preserved; the product source was not opened and B1
remains deferred.
