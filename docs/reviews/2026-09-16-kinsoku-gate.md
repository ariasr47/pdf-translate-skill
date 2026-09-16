# Gate 19 `kinsoku` and the CJK test faces — evidence (v52)

Branch `feat/kinsoku-gate` on `main` at `c28ada9`. Plan:
`docs/plans/2026-09-16-cjk-faces-and-kinsoku-gate.md`. Assessment that
scoped it: `docs/reviews/2026-09-16-cjk-request-assessment.md`.

Not a rendering change: AGENTS.md Rule 1 does not apply. The evidence is
the measurement, the red and green runs, the parity diff and the suite.

## Faces fetched (Task 1)

```
fetching NotoSansJP-VF.ttf
  9365 KB from https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf
  sha256 c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f
fetching NotoSansSC-VF.ttf
  17355 KB from https://raw.githubusercontent.com/google/fonts/main/ofl/notosanssc/NotoSansSC%5Bwght%5D.ttf
  sha256 a3041811a78c361b1de50f953c805e0244951c21c5bd412f7232ef0d899af0da
```

```
all test fonts present in C:\Dev\pdf-translate-skill\pdf-translate\tests\fonts
```
(exit 0)

## Measurement (Task 2, Step 1)

Ran `dev/probes/cjk_kinsoku_probe.py` after adding `\u301c` (WAVE DASH) to
the probe's `'cl-03 hyphens'` entry. The Task 2 report captured this
excerpt of the run, not the full console output (the `...` is the report's
own elision, not this document's):

```
   cl-03 hyphens (never begins a line): protected 5/5
...
kinsoku violations by the Story engine: 0
```

U+301C read fully protected (5/5) and the engine still showed 0 violations
overall, so it stayed in `KINSOKU_LINE_START`'s cl-03 group.

## Red, then green

**`kinsoku_report` itself (Task 2, Step 3).** RED —
`python -m unittest tests.test_cjk -v`, before `verify.py` had the sets or
the function:

```
ERROR: test_cjk (unittest.loader._FailedTest.test_cjk)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_cjk
Traceback (most recent call last):
  ...
    from pdf_translate.verify import GATE_NAMES, kinsoku_report, run_verify, verify
ImportError: cannot import name 'kinsoku_report' from 'pdf_translate.verify' (...)

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

GREEN — same command, after `KINSOKU_LINE_START`/`KINSOKU_LINE_END`,
`_has_cjk` and `kinsoku_report` were added:

```
----------------------------------------------------------------------
Ran 11 tests in 0.055s

OK
```

**The punctuation-only-line fix (Task 2, follow-up).** Reviewer finding:
`kinsoku_report` only judged lines where `_has_cjk(text)` was true, so a
line made solely of punctuation (a lone `「` or `。` left by a hand split —
the exact artefact the gate exists to catch) was never judged. RED — two
new tests added to `KinsokuReportTests`, run before the fix:

```
test_a_line_of_only_punctuation_is_judged_like_any_other ... FAIL
test_a_block_without_any_cjk_letter_is_never_judged ... ok

======================================================================
FAIL: test_a_line_of_only_punctuation_is_judged_like_any_other
----------------------------------------------------------------------
Traceback (most recent call last):
  File "...\tests\test_cjk.py", line 158, in test_a_line_of_only_punctuation_is_judged_like_any_other
    self.assertEqual(status, 'FAIL')
AssertionError: 'PASS' != 'FAIL'

----------------------------------------------------------------------
Ran 2 tests in 0.016s

FAILED (failures=1)
```

Fix: eligibility moved from the line to the block — a block is judged when
any of its lines carries a CJK letter, then every non-empty line of that
block is judged, punctuation-only lines included. GREEN — full module:

```
----------------------------------------------------------------------
Ran 13 tests in 0.055s

OK
```

**Wiring gate 19 into `verify` (Task 3, Step 2).** RED —
`python -m unittest tests.test_cjk.KinsokuVerifyTests -v`, before
`GATE_NAMES`/`_execute_verify` carried `kinsoku`:

```
test_a_broken_delivery_records_kinsoku_fail_and_exits_1 ... ERROR
test_a_clean_delivery_records_kinsoku_pass ... ERROR
test_a_latin_job_prints_no_kinsoku_line_and_records_none ... ok
test_the_console_prints_the_gate_once ... FAIL
test_the_gate_has_a_name ... FAIL

ERROR: test_a_broken_delivery_records_kinsoku_fail_and_exits_1
    KeyError: 'kinsoku'
ERROR: test_a_clean_delivery_records_kinsoku_pass
    KeyError: 'kinsoku'
FAIL: test_the_console_prints_the_gate_once
    AssertionError: 0 != 1 : [...]
FAIL: test_the_gate_has_a_name
    AssertionError: 'kinsoku' not found in ('field-parity', ... 'conjunct-shaping', 'leak-scan', ...)

Ran 5 tests in 0.514s
FAILED (failures=2, errors=2)
```

GREEN — full module, after `GATE_NAMES` and the `record('kinsoku', ...)`
call were added to `_execute_verify`:

```
----------------------------------------------------------------------
Ran 18 tests in 0.531s

OK
```

(The evidence-doc template predicted `Ran 16 tests`; the real run — 13
tests already in the module after the punctuation-only-line fix, plus the
5 new `KinsokuVerifyTests` — came to 18. Pasting the real number per this
task's own instruction to paste real output rather than the template's
prediction.)

## Task 4

The CJK face tests (`NotoSansJpTests`, `CjkFaceTests`) were added against
`test_cjk.py` and, after an amendment correcting the plan's assumption
about embedded font naming (assert on the fonts that actually drew spans,
via `page.get_text('dict')`, not `get_fonts()`, which also lists an unused
`Helvetica` resource `strip_text.py` leaves behind), the full module ran
green:

```
test_a_character_the_japanese_face_lacks_is_refused_not_borrowed ... ok
test_the_japanese_face_lacks_east_and_the_chinese_face_has_it ... ok
... (17 more, all ok) ...
test_a_noto_sans_jp_paragraph_breaks_within_the_rules ... ok

Ran 21 tests in 1.250s

OK
```

Drawing-font set observed for the control job (build → strip → retypeset
without 东, spaces removed from `span['font']`):

```
rc = 0
drawing fonts (spaces removed): {'NotoSansJP-Thin'}
raw get_fonts() base names (for comparison): ['Noto Sans JP Thin', 'Helvetica']
```

Only `NotoSansJP-Thin` actually drew text; the `Helvetica` entry
`get_fonts()` reports is the orphaned, unused resource left in
`/Resources/Font` after `strip_text.py` removes the content-stream text
ops — not a misdrawn line.

## Parity against `main` (Task 3, Step 5)

```
# package: C:\Users\rodri\AppData\Local\Temp\claude\C--Dev-pdf-translate-skill\f71acf3b-389c-49ff-881b-f6d3f7417505\scratchpad\parity\main\pdf-translate\pdf_translate\__init__.py
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
CONSOLE IDENTICAL
VERDICTS IDENTICAL
```

The two `# package:` lines name different directories — the `main` archive
and the branch checkout — proving the two runs imported different package
copies; the diff between their console and verdict output is empty.

## Suite (Task 3, Step 6 and after Task 5)

Task 3, Step 6 (five modules, `test_cjk` at 18 tests, before Task 4's
faces or Task 5's docs): the grepped summary (a literal `tail -5` under
Git Bash interleaves buffered `print()` output ahead of unittest's
unbuffered stderr summary on this machine, so the run was captured to a
file and grepped for `^Ran |^OK|^FAILED` instead):

```
Ran 313 tests in 57.537s

OK
```

After Task 5 (six modules including `test_cjk` at 21 tests, version 52,
run from `pdf-translate/` with the same capture-and-grep method):

```
Ran 316 tests in 59.482s

OK
```
