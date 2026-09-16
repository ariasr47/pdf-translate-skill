# The per-document verify report (v51)

**Branch:** `feat/verify-report` (off `main` at `73d465c`, v50).
**Spec:** `docs/BRIEF-unattended-delivery.md`, task A and B.
**Ruling:** `docs/DECISIONS.md`, row of 2026-09-16.

Seven tasks, each test-first: `Finding` and `GateResult.findings` (task
1), findings on every gate the CLI can print — form/page gates (2),
script gates (3), leak gates (4), `--translations` gates (5) —
`VerifyVerdict.to_dict()`, `--report`, `--fail-on-review`, pipeline
wiring (6), and this task: version 51, CI, docs, evidence (7).

## The rule

Every PASS/FAIL/REVIEW/SKIP line `verify` prints is one `GateResult`,
and every gate now also carries `findings`: a tuple of `Finding(page,
where, text)` — the page (1-based, or `None` for document-level gates),
the thing named (a field, a font's PostScript name, a script, `lang`, a
`U+XXXX` code point, a `0.85x` scale) and the run, caption, token or
detail, untruncated. The console still prints only the first ten to
thirty; the verdict keeps them all. `verify.py … --report PATH` writes
`verdict.to_dict()` as JSON (`schema` 1, the skill `version`, both
paths, `exit_code`, `gates`); `pipeline.py rebuild` writes it to
`<work>/verify_report.json`. `--fail-on-review` (CLI) or
`fail_on_review=True` (library) turns a run with REVIEW lines and no
FAIL into exit 1. Both are off by default. One console change rides
along: `isolated source-script tokens: none` is PASS, not REVIEW — it
was a REVIEW that fired on every job with no source-script content to
isolate.

## Console output is unchanged apart from one line (measured)

Nine jobs, built once by `dev/probes/verdict_parity_fixtures.py`
(trivial, metadata FAIL and PASS, scaled runs REVIEW and PASS, override
markers PASS and FAIL, Arabic glyph-by-glyph and Arabic through
retypeset), compared stdout-only between a `main` worktree and this
branch with `dev/probes/verdict_parity_runner.py`, as task 5 recorded
it (task 5 added `findings=` to the `--translations` gates; tasks 1–4
and 6 made no `print` changes, so this diff is still the whole branch's
console delta — task 6 only added a `findings=` count to the parity
runner's *stderr* summary line, not to the compared stdout):

```
$ git worktree add --detach <dir>/main-verify main
$ python dev/probes/verdict_parity_fixtures.py <dir>/f1fx
$ PYTHONPATH=<dir>/main-verify/pdf-translate python dev/probes/verdict_parity_runner.py <dir>/f1fx > main.txt
$ PYTHONPATH=pdf-translate                   python dev/probes/verdict_parity_runner.py <dir>/f1fx > branch.txt
$ diff main.txt branch.txt
```

Nine changed lines, one per job, all the same pair, nothing else:

```
11c11
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
31c31
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
51c51
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
70c70
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
91c91
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
111c111
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
133c133
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
156c156
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
178c178
< REVIEW isolated source-script tokens: none
---
> PASS isolated source-script tokens: none
```

## Tests, red first

Every gate got its `findings=` under a lockstep test written and
watched to fail before the `record(...)` call was touched. One line
each, from the reports at `.superpowers/sdd/task-N-report.md`:

| task | test class | recorded RED |
|---|---|---|
| 1 | `FindingShapeTests` | `ImportError: cannot import name 'Finding' from 'pdf_translate.verify'` (errors=2) |
| 2 | `FormAndPageGateFindingsTests` | empty findings lists throughout: `FAILED (failures=1, errors=4, skipped=1)`, e.g. `AssertionError: [] != [(None, 'missing', 'ApplicantName')]` |
| 3 | `ScriptGateFindingsTests` | `ValueError: not enough values to unpack (expected 1, got 0)` on both gates (errors=2) |
| 4 | `LeakGateFindingsTests` (+ one assertion in `VerdictCompletenessTests`) | `FAILED (failures=2, errors=1)`, e.g. `AssertionError: Lists differ: [] != [(1, 'token', 'alpha')]`; a third failure was the console-change assertion, `AssertionError: 'REVIEW' != 'PASS'` |
| 5 | `TranslationGateFindingsTests` | `FAILED (failures=5, errors=1)`, e.g. `AssertionError: Lists differ: [] != [(None, 'TinyBtn', 'OK')]`, plus an unpack `ValueError` on the shared metadata/scaled-runs/override-markers test |
| 6 | `ReportAndPolicyTests` | `FAILED (failures=2, errors=2)`: `FileNotFoundError` (`--report` ignored, file never written), an assertion failure (`'could not write'` never printed), and `AssertionError: 0 != 1` (`--fail-on-review` ignored) |
| 7 | `VersionLockstepTests` | `AssertionError: '50' != '51'` |

This task's own RED, run from `pdf-translate/` before bumping the four
version files:

```
$ PYTHONUTF8=1 …/python.exe -m unittest tests.test_verify_report.VersionLockstepTests -v
test_four_version_sources_agree ... FAIL
AssertionError: '50' != '51'
Ran 1 test in 0.063s
FAILED (failures=1)
```

GREEN, after bumping `pdf-translate/SKILL.md`, `.claude-plugin/plugin.json`,
`pdf-translate/pyproject.toml` and `pdf-translate/pdf_translate/__init__.py`
to 51 / 51.0.0 / 51.0.0 / 51:

```
$ PYTHONUTF8=1 …/python.exe -m unittest tests.test_verify_report.VersionLockstepTests -v
test_four_version_sources_agree ... ok
Ran 1 test in 0.069s
OK
```

## Suite and canary (Step 4)

Run from `pdf-translate/`:

```
$ PYTHONUTF8=1 …/python.exe -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface tests.test_shaping_probe tests.test_verify_report 2>&1 | tail -3
Ran 289 tests in 53.836s

OK
```

```
$ PYTHONUTF8=1 …/python.exe -m unittest discover -s ../dev/canary -p test_score.py 2>&1 | tail -3
Ran 11 tests in 0.708s

OK
```

289 tests across the five modules (0 failures, 0 errors), 11 canary
tests, both `OK`. `git diff --check` printed nothing (only Git's own
"LF will be replaced by CRLF" `core.autocrlf` notices on the two edited
files, which are checkout-time warnings, not stored line-ending
problems or `diff --check` findings).

## A sample report, both views of the same job

`meta-fail` is one of the nine parity fixtures: a job whose
`translations.json` asks for `lang: es` while the output declares no
language, so `document metadata` FAILs and nothing else does. Console,
then the JSON `--report` wrote for the same run:

```
$ PYTHONUTF8=1 …/python.exe scripts/verify.py <dir>/f1fx/meta-fail/orig.pdf <dir>/f1fx/meta-fail/out.pdf \
    --translations <dir>/f1fx/meta-fail/translations.json --min-ink 0.1 \
    --report <dir>/f1fx/meta-fail/verify_report.json
leak scan: source script Latin; output script Latin
leak scan: same script on both sides; using 2 document words from the original
fields: 0 original / 0 translated
PASS field parity
SKIP fill round-trip (no fields)
PASS page 1 ink ratio: 1.05
PASS text layer is visible
PASS canonical text layer
PASS no untranslated running text
PASS isolated source-script tokens: none
PASS no empty translation targets
PASS authored translations present
PASS button captions
PASS caption width
SKIP override marker gate (no segments.json beside the mapping; pass --segments)
FAIL document metadata (1):
   [lang] translations.json asks for "es", output declares "nothing"
SKIP scaled runs: no scale_report.json beside the output (a build from before it was written)
PASS write/find/say identifiers
elapsed 0.10s
```

`<dir>/f1fx/meta-fail/verify_report.json`, in full — this is what a consumer
gets instead of parsing the console:

```json
{
 "schema": 1,
 "version": "51",
 "original": "<dir>\\f1fx\\meta-fail\\orig.pdf",
 "output": "<dir>\\f1fx\\meta-fail\\out.pdf",
 "exit_code": 1,
 "fail_on_review": false,
 "gates": [
  {
   "name": "field-parity",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "fill-roundtrip",
   "status": "SKIP",
   "message": "no fields",
   "findings": []
  },
  {
   "name": "ink-ratio",
   "status": "PASS",
   "message": "",
   "findings": [
    {
     "page": 1,
     "where": "page",
     "text": "PASS ink ratio 1.05"
    }
   ]
  },
  {
   "name": "visible-text",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "canonical-text",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "leak-running",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "leak-isolated",
   "status": "PASS",
   "message": "none",
   "findings": []
  },
  {
   "name": "empty-targets",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "placement",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "button-captions",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "caption-width",
   "status": "PASS",
   "message": "",
   "findings": []
  },
  {
   "name": "override-markers",
   "status": "SKIP",
   "message": "no segments.json",
   "findings": []
  },
  {
   "name": "metadata",
   "status": "FAIL",
   "message": "lang",
   "findings": [
    {
     "page": null,
     "where": "lang",
     "text": "translations.json asks for \"es\", output declares \"nothing\""
    }
   ]
  },
  {
   "name": "scaled-runs",
   "status": "SKIP",
   "message": "no scale_report.json",
   "findings": []
  },
  {
   "name": "identifiers",
   "status": "PASS",
   "message": "",
   "findings": []
  }
 ]
}
```

One `FAIL` line, one populated `findings` array — `metadata` — and it
names exactly what the console's `[lang] …` line names. Every other
gate that printed `PASS` or `SKIP` on the console has a matching
`GateResult`; `ink-ratio` is the one gate that always records a finding
even on PASS, since the ratio itself is the useful number, not just the
verdict.

## Version lockstep

Four sources, one check: `pdf-translate/SKILL.md`'s `version: "N"`,
`.claude-plugin/plugin.json`'s `"N.0.0"`, `pdf-translate/pyproject.toml`'s
`version = "N.0.0"`, and `pdf_translate.__version__ == "N"`.
`tests.test_verify_report.VersionLockstepTests` checks all four locally;
`.github/workflows/tests.yml`'s "Version sources agree (plugin,
SKILL.md, pyproject, __version__)" step (Python 3.10-compatible,
stdlib `json`/`re` only, no `tomllib`) checks the same four in CI. Both
now read 51 / 51.0.0 / 51.0.0 / 51.

## Follow-up from the product side's review of PR #5 (16 September)

The `pdf-translator` session reviewed the PR and found two REVIEW gates that
recorded no finding — `leak-scan` (source and output share a spaceless
family, the zh → ja case the product is working on) and `metadata-lang` —
and that `run_verify` recorded paths as given while the CLI recorded them
absolute. All three fixed, tests first:

| change | test (watched to fail, then pass) |
|---|---|
| `leak-scan` → `Finding(None, 'script', src_script)` | `LeakGateFindingsTests.test_shared_spaceless_family_names_the_script`: two Japanese pages drawn with PyMuPDF's built-in CJK face; `[(None, 'script', 'CJK')]` |
| `metadata-lang` → `Finding(None, 'lang', 'translations.json has no "lang"')` | `TranslationGateFindingsTests.test_missing_lang_review_names_lang` |
| `run_verify` and `main` build the verdict through one helper that takes `os.path.abspath` | `FindingShapeTests.test_run_verify_records_absolute_paths_like_the_cli`: relative paths in, absolute paths out |
| the invariant the review asked for: every FAIL or REVIEW gate carries at least one finding | `FindingsInvariantTests.test_every_fail_or_review_gate_has_a_finding`: nine jobs (trivial, missing lang, scaled run, dropped override marker, running leak, shared spaceless family, the two corpus scans, glyph-by-glyph Arabic); it failed first on `trivial: metadata-lang is REVIEW with no finding` |

The `where`/`text` table in `references/gates.md` now covers all 22 names
in `GATE_NAMES`. No printed line changed: every edit is a `findings=`
argument or the verdict helper. Suite after the follow-up:

```
Ran 295 tests in 46.015s
OK
Ran 11 tests in 0.588s        (canary)
OK
```

## Not independently verified, on purpose

This task is version bump, CI wiring and documentation only — no
`record(...)` call, no console line, no rendering path touched. Its own
evidence is the RED/GREEN pair above, the unchanged suite and canary
counts, and `git diff --check` silent.
