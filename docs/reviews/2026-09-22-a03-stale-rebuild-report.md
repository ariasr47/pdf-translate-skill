# A03: reused rebuild verification report

Local candidate on `codex/a03-stale-rebuild-report`, based on
`b20fadda832b673b61ce8bc4a5f17189edd58209` (v60). Requested by Rodrigo after
coordination with the PDF Translator task **Approve sandbox proposal**.
No consumer source was read or copied. The sandbox is independent of this
candidate and remains on its existing pin.

## Problem and change

`pipeline rebuild` called `retypeset` and returned immediately on failure.
The verifier, which normally invalidates its previous report, never ran.
A success followed by a missing translation therefore left the successful
PDF and its old `verify_report.json` together, although the current mapping
had not built successfully. Invalid mappings could fail even earlier.

The candidate invalidates the default report and the selected `--report`
before loading the mapping. Both report paths are checked before either is
removed. Input/output aliases and unrecognized or unreadable existing files
are refused; recognized schema-1 verification reports are disposable output.
If removing an old report fails, rebuild returns 2 before typesetting and
reports that the retained file does not describe this attempt.

Legacy and typography rendering are unchanged. Early failures and refusals
preserve the previous PDF. A successful retry publishes a fresh report; a
verification failure publishes the current failure verdict. No manifest,
new schema, public result type, or dependency was introduced.

## Observable acceptance

| Outcome | Verify by |
|---|---|
| A real successful legacy build, missing-translation refusal, and repaired retry yield report exit 0 → absent → exit 0; source and prior PDF remain byte-identical during refusal. | `tests.test_rebuild_attempt.RebuildAttemptTests.test_success_refusal_success_in_both_formats` |
| The same sequence in typography uses an overlong authored run to refuse placement, then succeeds with the restored mapping. | Same test, `typography=True` subcase |
| Malformed JSON, unsupported format, and missing mapping remove prior success before rendering. | `test_mapping_load_errors_invalidate_before_rendering` |
| Selecting a custom report invalidates the default; the custom report is also absent after the next early failure. | `test_custom_report_also_invalidates_default_when_switching` |
| Verification failure records current exit 1 instead of old exit 0. | `test_current_verification_failure_replaces_previous_success` |
| An exception or interrupt at mapping, rendering, or verification boundaries cannot retain a previous success report. | `test_interruption_or_unexpected_stage_error_cannot_leave_old_pass` |
| Original/output PDFs, mappings, extraction, fonts, unrelated JSON and hard-link aliases survive unsafe report choices byte-for-byte. | `test_report_aliases_and_unrelated_files_are_never_removed`, `test_default_report_alias_is_rejected_before_source_mutation` |
| Failure to remove the previous report stops the attempt before rendering. | `test_invalidation_failure_aborts_before_typesetting` |

From `pdf-translate/`, using this checkout on `PYTHONPATH`:

```text
python -m unittest tests.test_rebuild_attempt tests.test_verify_report.ReportAndPolicyTests tests.test_typography_pipeline
python -m unittest discover -s tests -t .
```

## Evidence

Environment: Windows, Python 3.14.0, the existing project virtualenv at
`C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`; fixture
fonts copied from the already-verified upstream A01 worktree, not downloaded
or obtained from the product.

- Clean baseline: 15 existing focused tests passed in 14.044s.
- Red: eight new tests produced 22 failing subcases in 13.581s on unchanged
  v60 runtime. Both real refusal sequences retained stale success reports.
- Green: 23 focused tests passed in 27.425s.
- Full discovery: **657 tests passed in 415.069s**, with no failures, errors
  or skips. Existing review/NOTES.md and fontTools file-handle ResourceWarnings
  were printed; those code paths were not changed here.
- After strengthening existing typography refusal tests to use real prior
  PASS reports: 18 affected tests passed in 30.842s. The change prevents an
  unrecognized placeholder report from masking the intended later refusal.
  Full discovery had already imported the earlier test bodies; these focused
  reruns verify the final test-only changes. Runtime behavior was unchanged.
- The existing CLI parity runner's 12 invocations match the v60 archive
  after its path/timing normalization and excluding the package-location
  diagnostic. This covers ordinary behavior, not the deliberately changed
  refusal/report lifecycle or the help text documenting it.

Author logs and parity fixture jobs are in ignored `runs/a03/`.

Independent review found no actionable correctness issues. Its separate
compatibility run passed **339 tests in 91.176s**; after the test strengthening,
it reran **10 typography pipeline tests in 15.850s**, all passing. Commands:

```text
python -m unittest tests.test_rebuild_attempt tests.test_typography_pipeline tests.test_verify_report tests.test_pipeline tests.test_import_surface tests.test_consumer_contract
python -m unittest tests.test_typography_pipeline
python runs/a03-independent/probe.py
python runs/a03-independent/locked_report_probe.py
```

The process probe independently exercised legacy/typography × default/custom
reports: **four real child-process terminations** at a controlled mapping
boundary, with old reports already absent while the child was live. All four
preserved source and prior PDF SHA-256, returned nonzero when terminated, and
recovered successfully. All four also exercised success → malformed-mapping
failure → success. A separate Windows deny-delete-handle probe exercised
**two real locked reports**: both refused with exit 2 and a stale-history
diagnostic, preserving report/source/prior PDF bytes. These are real process
and filesystem probes, in addition to the unit tests' injected exceptions.
Scripts, per-command logs and JSON outcomes remain in `runs/a03-independent/`.

The review explicitly set aside syntax rejection, unsafe report destinations,
unremovable history, other custom report paths, concurrent workspace use,
atomic PDF/sidecar publication, direct API report management, and visual
rendering revalidation. Those exclusions match the scope and limitations
below; they are not claims of additional fixes.

## Limits and integration

Current command status and a fresh report must be consumed together. A
missing report means unavailable verification evidence, including when the
existing verifier returns 0 with a report-write warning. File existence is
not proof of success. Syntax rejection and unsafe-report preflight can leave
prior reports; those commands do not start a rebuild. If the filesystem
prevents invalidation, the command explicitly refuses, and the retained
report is history, not evidence about this call.

Other custom report paths remain caller-owned history. Concurrent jobs need
separate workspaces. This is not transactional publication of PDF/sidecars:
a verification failure can leave a newly built PDF, and interrupted saves
retain the underlying stage's existing filesystem behavior. Direct
`run_retypeset` callers must use its result/exception and cancellation fields;
this candidate does not manage reports for direct API calls.

A01 remains a separate local candidate (`41bdf99`); it is not included here.
A02, A06, typography near-floor capture and B1 remain separate work. Candidate
metadata remains v60: select a release version against current main when
preparing publication. This work does not push, merge, create a PR, publish,
or change the app's pin.
