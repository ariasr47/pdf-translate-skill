# Item 6 — CLI input spelling and module logging, 26 September 2026

Base: v86, PR #60 at `0b1b362af99da39c4ba4948c209aa0781d36f912`.
Candidate: v87, `codex/cli-input-logging`,
[PR #61](https://github.com/ariasr47/pdf-translate-skill/pull/61).
Rodrigo authorized the next
assigned CLI pair; items 7–9 remain separate.

## Observed defects and repair

Verify's token reader only recognizes `--flag value`. Passing a missing-target
mapping as `--translations=PATH` silently omitted it and returned 0, while
the separated spelling returned 1 with the missing translation finding.
All eleven value-taking options now reject the equals spelling with exit 2
and a usage line naming `--flag VALUE`, before opening PDFs or touching a
report. An empty equals value is also refused. A separate value such as
`mapping=authored.json` continues to work.

Running retypeset or verify with `python -m` sets `__name__` to `__main__`.
Their loggers therefore did not reach the `pdf_translate` console handler.
They now keep their normal package logger names. Module success, failed
verification, build refusal and usage errors print the same stdout as the
script entry points, apart from elapsed time. Independent review then found
that CP1252 streams dropped Japanese findings and filenames. Two added
regressions reproduced this; module execution now uses the script wrappers'
UTF-8 stream setup, while imported functions do not reconfigure streams.
There is no drawing, shaping,
font or layout change; Rule 1's rendering review does not apply to this
logging/parser repair.

## Observable acceptance

Run `python -m unittest tests.test_cli_input_logging -v` from `pdf-translate/`.

- Every known value-taking verify option in equals form returns 2, names the
  corrected spelling, prints no PASS line, and leaves all input/report bytes
  unchanged. An empty equals value refuses before nonexistent PDFs are read.
- The missing-target mapping produces its named finding with separated
  syntax; equals syntax refuses instead of silently passing. A mapping path
  containing `=` remains accepted as a separate argument.
- Both module entry points match script stdout and status on real success
  and failure cases. Retypeset writes authored targets on success and no PDF
  on refusal; elapsed and gate lines are not duplicated.
- With `PYTHONUTF8=0` and `PYTHONIOENCODING=cp1252`, missing Japanese targets
  and Japanese output filenames print intact without `UnicodeEncodeError`.
- `tests.test_rebuild_attempt.DefaultMappingVerificationTests` checks that
  rebuild forwards the equals refusal (exit 2 and named usage), publishes no
  verification report and removes a previous PASS report. Default and
  separated syntax still exercise the mapping-dependent checks.

## Runs

Windows, Python 3.14.0, PyMuPDF 1.28.2, pikepdf 10.13.0.post1,
fontTools 4.64.0. Interpreter:
`C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`.
All 20 configured test fonts are present (`python tools/fetch_test_fonts.py
--check`, exit 0). Commands below ran from `pdf-translate/` unless stated.
Raw local logs are under `runs/cli-input-logging-2026-09-26/` at repo root.

| Check | Command | Observed output |
|---|---|---|
| Existing baseline | `python -m unittest tests.test_import_surface -v` | `Ran 39 tests in 8.984s`, `OK` |
| Red, new tests against unchanged v86 | `python -m unittest tests.test_cli_input_logging -v` | `Ran 10 tests in 9.023s`, `FAILED (failures=19)` (includes parameterized subtests); separate-value control passed |
| Green | Same command after the two fixes | `Ran 10 tests in 8.946s`, `OK` |
| Compatibility | `python -m unittest tests.test_cli_input_logging tests.test_import_surface tests.test_verify_report tests.test_consumer_contract.OneDocumentThroughEveryStageTests tests.test_typography_pipeline -v` | `Ran 95 tests in 36.647s`, `OK` |
| Encoding red | `python -m unittest tests.test_cli_input_logging.ModuleConsoleTests.test_verify_module_keeps_unicode_findings_on_a_legacy_console tests.test_cli_input_logging.ModuleConsoleTests.test_retypeset_module_keeps_unicode_paths_on_a_legacy_console -v` | `Ran 2 tests in 1.551s`, `FAILED (failures=2)` |
| Final focused compatibility | The compatibility command above plus `tests.test_shipped_docs`, after the encoding repair | `Ran 109 tests in 39.229s`, `OK`, including all 12 new regressions |
| Expanded focused compatibility | Previous command plus `tests.test_rebuild_attempt`, after correcting the obsolete equals expectation and adding the stale-report transition | `Ran 126 tests in 59.130s`, `OK` |
| Existing CLI parity | From repo root, `python dev/probes/cli_parity_runner.py <fresh-work-directory>` before and after repair; compare captured logs | 12 invocations; normalized output and exit codes identical |
| Repository checks | From repo root, `python -m unittest discover -s dev/repo -v` | `Ran 6 tests in 1.618s`, `OK` |
| Canary tests | `python -m unittest discover -s ../dev/canary -v` | `Ran 15 tests in 0.387s`, `OK` |
| Eval fixtures | `python evals/make_fixtures.py --outdir <fresh-directory>` | Wrote both fixture PDFs, exit 0 |
| CI manifest command | From repo root, `claude plugin validate . --strict` | Marketplace validation passed, exit 0 |
| Additional explicit plugin check | `claude plugin validate .claude-plugin/plugin.json --strict`, on candidate and an archive of exact v86 base | Both exit 1 with the same existing warning: root `CLAUDE.md` is not loaded as project context. This file and its policy are unchanged. |

The independent reviewer found the CP1252 issue described above, then
approved the repair with no remaining actionable findings. Its fresh command
was `python -B -m unittest tests.test_cli_input_logging
tests.test_import_surface.CliPathTests.test_importing_the_package_does_not_reconfigure_stdio
-v`: **13 tests in 10.827s, OK, exit 0**. It also inspected the parser's
ordering and confirmed import-time stream behavior is preserved.

Full Linux/Windows discovery runs on PR #61; its current head's checks and
PR description record the hosted results. Full discovery is delegated to
GitHub CI because the preserved checkout's
handover records two host crashes during full-suite runs on this machine.

The first full run, [36280640596](https://github.com/ariasr47/pdf-translate-skill/actions/runs/36280640596),
ran **821 tests** on each platform and found one obsolete expectation:
`test_the_equals_spelling_does_not_switch_the_checks_off` expected the old
ignored option to fall back to default mapping verification (exit 1), while
v87 returned its intended exit-2 usage refusal. Linux: 409.839s, one expected
failure; Windows: 501.105s, one skip and one expected failure. There were no
other failures. The expectation now explicitly requires refusal and no
report; a second test starts with a successful PASS report and proves it
does not survive the refused rebuild. No production behavior was changed
to resolve this expectation. Independent subprocess probes confirmed the
default and separated paths still report `empty-targets` FAIL with exit 1.
The reviewer independently ran `python -B -m unittest
tests.test_rebuild_attempt.DefaultMappingVerificationTests -v`:
**9 tests in 4.791s, OK, exit 0**, and approved the test-only correction.

## Limits

The existing eager-import `runpy` warning may still appear on module stderr;
changing package import architecture is outside this repair. Unknown options
retain their existing parsing. Standalone verify usage errors preserve a
prior report, just as missing-value usage errors already did; a prior report
does not attest the refused invocation. Rebuild retains its existing order:
it invalidates reports and renders before calling verify, so this refusal
leaves no report but may leave a newly built, unverified PDF. Report/version
fields advance to 87,
but drawing and library-call semantics are unchanged. The product remains
on its own separately managed adoption plan.
