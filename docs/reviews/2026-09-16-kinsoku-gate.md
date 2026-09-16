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

## Fix wave after the whole-branch review

**The review's two measurements.** MuPDF's block grouping, trusted for line
adjacency, drops hand-split lines above about 1.6x leading — the block
cliff: `leading 14 → 1 block FAIL; 15 → 1 block FAIL; 16 → 3 blocks silent
PASS; 24 → 3 blocks silent PASS`. And a hard FAIL refused correct forms —
the false-positive shapes: ・ list, lone ー cell, `）` under a label,
side-by-side cells grouped into one block.

**The controller's geometry table**, measured with the code in
`pdf_translate/verify.py` (`_page_lines`, `STACK_GAP = 1.5`, `_stacks`),
PyMuPDF 1.28.2, bundled CJK face, 10 pt, TextWriter runs — verbatim:

```
hand-split leading 14 (1.4x)   judged=3  findings=[(1,'line-end','申立人は以下の情報を「'), (1,'line-start','。氏名と住所も書いてください')]
hand-split leading 16 (1.6x)   judged=3  findings=[same two]
hand-split leading 24 (2.4x)   judged=3  findings=[same two]
hand-split leading 30 (3.0x)   judged=3  findings=[same two]
hand-split leading 40 (4.0x)   judged=3  findings=[]
nakaten bullet list ・氏名/・住所/・電話番号        judged=3  findings=[]
single ・ mid-paragraph キャッシュ/・サーバー       judged=2  findings=[(1,'line-start','・サーバー')]
lone ー cell 氏名：田中/ー/住所：東京              judged=3  findings=[]
lone 「 line ある文章です/「/続く文章              judged=3  findings=[]
side-by-side cells 項目名 | ）内に記入, 備考 below  judged=3  findings=[]
two-char punctuation line 彼は「はい/」。          judged=2  findings=[(1,'line-start','」。')]
numbered list （1）…/（2）…/（3）…                 judged=3  findings=[]
latin block He said "/hello."                    judged=0  findings=[]
story paragraph (140pt box)                      judged=16 findings=[]
two story columns side by side                   judged=16 findings=[]
Droid line height at 10pt: 13.07; Noto Sans JP: 14.48
```

**Probe after the four members joined** (cl-05 middle dot U+FF65, cl-02
closing bracket U+2986, cl-11 small katakana extension U+31F0-U+31FF,
cl-01 opening bracket U+2985), run against the fetched
`tests/fonts/NotoSansJP-VF.ttf` (`dev/probes/cjk_kinsoku_probe.py`):

```
face: Noto Sans JP Thin (C:\Dev\pdf-translate-skill\pdf-translate\tests\fonts\NotoSansJP-VF.ttf); PyMuPDF 1.28.2
1. Story engine, paragraph at 6 widths: 158 lines drawn; 0 begin with a prohibited character; 0 end with an opener; 0 run past the box
2. naive greedy breaker, same face and widths: 148 lines; 38 begin with a prohibited character; 8 end with an opener
3. per character (Story engine):
   cl-02 closing brackets (never begins a line): protected 14/15  not judged U+2986
   cl-02 half-width closer (never begins a line): protected 1/1
   cl-03 hyphens (never begins a line): protected 5/5
   cl-04 dividing punctuation (never begins a line): protected 6/6
   cl-05 middle dots (never begins a line): protected 4/4
   cl-06 full stops (never begins a line): protected 2/2
   cl-06 half-width (never begins a line): protected 1/1
   cl-07 commas (never begins a line): protected 2/2
   cl-07 half-width (never begins a line): protected 1/1
   cl-09 iteration marks (never begins a line): protected 6/6
   cl-10 prolonged sound mark (never begins a line): protected 1/1
   cl-10 half-width (never begins a line): protected 1/1
   cl-11 small kana, hiragana (never begins a line): protected 12/12
   cl-11 small kana, katakana (never begins a line): protected 12/12
   cl-11 half-width small kana (never begins a line): protected 9/9
   cl-11 small katakana extension (never begins a line): protected 16/16
   cl-01 opening brackets (never ends a line): protected 14/15  not judged U+2985
   cl-01 half-width opener (never ends a line): protected 1/1
kinsoku violations by the Story engine: 0
```

U+2986 and U+2985 read "not judged": `pymupdf.Font(fontfile=...).has_glyph()`
confirms both are 0 in the fetched face — no glyph, not a violation — so
both join the sets under the inclusion rule (protected, or no glyph in
face). Nothing read VIOLATED, so nothing was excluded. Totals: 93/94
line-start and 15/16 line-end members protected (up from 75/75 and 15/15
before these four members; the two-member shortfall from "every member
protected" is exactly the two no-glyph members).

**Module and suite, after the fix.** `python -m unittest tests.test_cjk -v`:

```
Ran 25 tests in 1.510s

OK
```

Six-module suite (`tests.test_pipeline tests.test_corpus_verdicts
tests.test_import_surface tests.test_shaping_probe tests.test_verify_report
tests.test_cjk`), captured and grepped for `^Ran |^OK|^FAILED`:

```
Ran 320 tests in 65.645s
OK
```

**The decision.** The gate now reports REVIEW, never FAIL: a form label can
look exactly like a hand-split line, so the gate cannot attest a defect,
only point at it (`--fail-on-review` / `fail_on_review=True` turns a
recorded REVIEW into exit 1 for consumers who want that). Adjacency is
judged by geometry — lines grouped into stacks by horizontal overlap and a
vertical gap up to `STACK_GAP = 1.5` times the lower line's height, not by
MuPDF's blocks, which split hand-split lines above about 1.6x leading and
let them pass silently. Two shapes a form sets on purpose are exempt: a
single-character line (ー for "none", a bracket after a field, a lone 「),
and a character that begins two or more lines of a stack, each followed by
more text (・ as a list marker). Documented misses: a lone 「 or 。 on its
own line in a hand-split paragraph (single character → exempt); lines set
looser than about three times the line height; vertical (character-stacked)
text; and the prefix/postfix abbreviation classes (JLREQ cl-12, cl-13).
