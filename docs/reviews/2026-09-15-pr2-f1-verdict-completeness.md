# PR #2 F1 — `VerifyVerdict.gates` records every printed outcome

**Branch:** `fix/verify-verdict-records-every-gate` (on `main` at `c163cd4`, v49)
**Finding:** `docs/reviews/2026-09-15-pr2-core-library-packaging.md`, F1 (medium).
**Ruling:** `docs/DECISIONS.md`, row of 2026-09-15 "`VerifyVerdict.gates` mirrors the console".

## The symptom, on a real job

A one-line job whose `translations.json` asks for `lang: es` while the
output declares no language. `verify` prints `FAIL document metadata (1)`
and exits 1. The verdict a consumer gets from `run_verify` on `main`:

```
exit=1 gates=10
    field-parity: PASS
    fill-roundtrip: SKIP (no fields)
    ink-ratio: PASS
    visible-text: PASS
    canonical-text: PASS
    leak-running: PASS
    empty-targets: PASS
    placement: PASS
    button-captions: PASS
    identifiers: PASS
```

Ten entries, none of them FAIL, beside an exit code of 1. On this branch:

```
exit=1 gates=15
    …
    caption-width: PASS
    override-markers: SKIP (no segments.json)
    metadata: FAIL (lang)
    scaled-runs: SKIP (no scale_report.json)
    identifiers: PASS
```

## The rule

Every PASS/FAIL/REVIEW/SKIP line the CLI prints is one `GateResult` with
the same status, under a name from `verify.GATE_NAMES` (22 names, in gate
order, exported from the package). A gate that prints nothing for a job
(no fields, no Arabic, no `--translations`) records nothing. The eight
that F1 found missing and their names:

| printed line | name | statuses |
|---|---|---|
| Arabic letterforms joined / drawn unshaped | `arabic-letterforms` | PASS, FAIL |
| leak scan: spaceless family | `leak-scan` | REVIEW |
| isolated source-script tokens | `leak-isolated` | REVIEW (count or `none`) |
| shaped-script targets carry /ActualText | `shaped-actualtext` | PASS, FAIL |
| caption width | `caption-width` | PASS, FAIL |
| override marker gate | `override-markers` | PASS, FAIL, SKIP |
| document metadata | `metadata` | PASS, FAIL |
| document metadata: no "lang" | `metadata-lang` | REVIEW |
| scaled runs | `scaled-runs` | PASS, REVIEW, SKIP |

## Console output and exit codes are unchanged (measured)

The diff to `verify.py` is `record()` calls, the `GATE_NAMES` tuple, and
one `if` restructured so the Arabic PASS line prints under the same
condition as before (`git diff -U0 main -- pdf-translate/pdf_translate/verify.py`).

Nine jobs built once on disk (`dev/probes/verdict_parity_fixtures.py`:
trivial, metadata FAIL and PASS, scaled runs REVIEW and PASS, override
markers PASS and FAIL, Arabic glyph-by-glyph and Arabic through
retypeset) and verified from a worktree of `main` and from this branch
with `dev/probes/verdict_parity_runner.py`:

```
$ python dev/probes/verdict_parity_fixtures.py <dir>
$ PYTHONPATH=<main worktree>/pdf-translate python dev/probes/verdict_parity_runner.py <dir> > main.txt
$ PYTHONPATH=pdf-translate                   python dev/probes/verdict_parity_runner.py <dir> > branch.txt
$ diff main.txt branch.txt && echo IDENTICAL
IDENTICAL: 187 console lines, 9 jobs
```

Exit codes per job, both trees: 0 1 0 0 0 1 1 1 0. Recorded entries,
`main` → branch: 10 → 16, 10 → 15, 10 → 15, 10 → 16, 10 → 16, 10 → 16,
10 → 16, 10 → 17, 10 → 17.

## Tests (red first)

`tests/test_import_surface.py::VerdictCompletenessTests`, six tests,
watched to fail (`FAILED (failures=7, errors=1)`: every assertion
`None != 'FAIL'` or the missing `GATE_NAMES` import), then green:

- the trivial job records the six it prints and, mechanically, as many
  entries as it prints gate lines (16 = 16);
- every recorded name is in `GATE_NAMES`;
- metadata FAIL / PASS, and the `lang` REVIEW only when `lang` is absent;
- scaled runs SKIP / PASS / REVIEW from the report beside the output;
- override markers SKIP / PASS / FAIL from `segments.json` beside the mapping;
- Arabic drawn glyph by glyph: `arabic-letterforms` FAIL and
  `shaped-actualtext` FAIL, exit 1; the library's own retypeset output:
  both PASS, exit 0; a Latin job records neither.

Full suite as CI runs it: `Ran 266 tests — OK`; canary `Ran 11 tests — OK`;
eval fixtures built; `git diff --check` clean; plugin `50.0.0` ==
`metadata.version` 50 == pyproject `50.0.0`.

## Not independently verified, on purpose

AGENTS.md Rule 1 covers rendering, shaping, fonts and layout. This change
touches reporting only — no rendering path, no glyph, no face — and its
evidence is a byte-identical console diff plus the tests above, both
re-runnable from the committed scripts.
