# `--report` never leaves a stale report — evidence (v53)

Branch `fix/stale-verify-report`, stacked on `feat/kinsoku-gate` (PR #6, v52). Origin: the
product's review of PR #5, defect 1, received in full on 2026-09-16 ("section 1"). Not a rendering
change: AGENTS.md Rule 1 does not apply.

## The defect, reproduced red first

`write_report` opened the path for writing and, when that failed, printed and returned. Nothing
removed what was already there, and `pipeline.py rebuild` writes to a fixed path in a work dir
that is reused. Sequence: a passing job writes the report; the file becomes unwritable (here:
`os.chmod(report, stat.S_IREAD)`); a failing job runs to the same path.

`tests.test_verify_report.ReportAndPolicyTests.test_a_refused_report_write_leaves_no_stale_report`,
run before the fix:

```
FAIL: test_a_refused_report_write_leaves_no_stale_report
AssertionError: 0 != 1 : {'schema': 1, 'version': '52', 'original': '...\\good\\orig.pdf',
'output': '...\\good\\out.pdf', 'exit_code': 0, ...}
Ran 1 test in 0.262s
FAILED (failures=1)
```

The process exited 1; the report on disk said `exit_code 0` for the **good** document.

## The fix

`pdf_translate/verify.py`:

- `_remove_stale_report(path)`: before the gates run (`main`, when `--report` is given) any file
  at the path is removed (made writable first, since Windows refuses to unlink a read-only file);
  if that fails the console says so and that what is there does not describe this run.
- `write_report`: the JSON goes to a temp file beside the path (`tempfile.mkstemp`) and is moved
  into place with `os.replace`, so the report is written whole or not at all; on any `OSError` the
  temp file is removed, the same `(could not write …)` line is printed as before, and
  `_remove_stale_report` runs again. The exit code is untouched, as the existing
  `test_unwritable_report_path_keeps_the_exit_code` pins.

After the fix the second run removes the read-only file and writes its own report: the test's
"either no report, or one describing run 2" holds on the second branch.

## Green

```
tests.test_verify_report.ReportAndPolicyTests: Ran 5 tests in 1.251s  OK
tests.test_verify_report + tests.test_import_surface: Ran 49 tests in 10.318s  OK
VersionLockstepTests (53 in four sources): Ran 1 test  OK
Suite as CI runs it (six modules): Ran 323 tests in 54.871s  OK
```

No console change on a run whose report can be written; `verify()` / `run_verify()` do not write
reports and are untouched, so the parity runner's nine jobs are unaffected by construction.

## Docs

`references/gates.md` "As a library" states the write-whole-or-not-at-all and remove-first
behaviour; `docs/DECISIONS.md` carries the row with the reversal condition (a consumer that needs
the previous report kept until the new one is complete). Version 52 → 53 in SKILL.md,
plugin.json, pyproject.toml, `__version__` and the lockstep test literal.
