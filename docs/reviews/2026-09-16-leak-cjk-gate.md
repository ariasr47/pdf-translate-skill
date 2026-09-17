# Gate 21 `leak-cjk` — evidence (v55)

Branch `feat/cjk-leak-tell` from `main` (v54). Spec: `docs/BRIEF-cjk-leak-tell.md` (measured 2026-09-16 with
`dev/probes/cjk_leak_tell_probe.py`); task F of `docs/BRIEF-unattended-delivery.md`; the product's work order E2.
Not a rendering change: AGENTS.md Rule 1 does not apply; reviewed on another model.

## Task 1 — the tell, red then green

Red (the module does not exist):

```
test_cjk_leak (unittest.loader._FailedTest.test_cjk_leak) ... ERROR

======================================================================
ERROR: test_cjk_leak (unittest.loader._FailedTest.test_cjk_leak)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_cjk_leak
Traceback (most recent call last):
  File "C:\Users\rodri\AppData\Local\Programs\Python\Python314\Lib\unittest\loader.py", line 137, in loadTestsFromName
    module = __import__(module_name)
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_cjk_leak.py", line 18, in <module>
    from pdf_translate import cjk_tell, han_forms
ImportError: cannot import name 'cjk_tell' from 'pdf_translate' (C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py)


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Green (the eleven-text table exact, the corpus document, the drift fold, the pairs):

```
test_compatibility_ideographs_fold_before_the_tell (tests.test_cjk_leak.TellTests.test_compatibility_ideographs_fold_before_the_tell) ... ok
test_convention_of (tests.test_cjk_leak.TellTests.test_convention_of) ... ok
test_single_characters (tests.test_cjk_leak.TellTests.test_single_characters) ... ok
test_strip_allowed (tests.test_cjk_leak.TellTests.test_strip_allowed) ... ok
test_strong_pairs_and_the_weak_one (tests.test_cjk_leak.TellTests.test_strong_pairs_and_the_weak_one) ... ok
test_tells_in_keeps_order_and_repeats (tests.test_cjk_leak.TellTests.test_tells_in_keeps_order_and_repeats) ... ok
test_the_corpus_japanese_document (tests.test_cjk_leak.TellTests.test_the_corpus_japanese_document) ... ok
test_the_measured_table (tests.test_cjk_leak.TellTests.test_the_measured_table) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.012s

OK
```

## Task 2 — the gate, red then green

Red (before the gate exists — the two echo tests, kept exactly as measured;
the ja→zh echo verifying clean today is the point):

```
======================================================================
ERROR: test_an_echoed_chinese_segment_in_a_japanese_delivery_fails (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_chinese_segment_in_a_japanese_delivery_fails)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_cjk_leak.py", line 234, in test_an_echoed_chinese_segment_in_a_japanese_delivery_fails
    lines, status, findings = verify_mod.cjk_tell_report(doc, 'JP', set(), [], set())
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: module 'pdf_translate.verify' has no attribute 'cjk_tell_report'

======================================================================
FAIL: test_an_echoed_japanese_segment_in_a_chinese_delivery_fails (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_japanese_segment_in_a_chinese_delivery_fails)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_cjk_leak.py", line 205, in test_an_echoed_japanese_segment_in_a_chinese_delivery_fails
    self.assertEqual(rc, 1, lines)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
AssertionError: 0 != 1 : ['leak scan: source script CJK; output script CJK', 'fields: 0 original / 0 translated', 'PASS field parity', 'SKIP fill round-trip (no fields)', 'PASS page 1 ink ratio: 0.85', 'PASS text layer is visible', 'PASS canonical text layer', 'PASS kinsoku: 5 CJK line(s) break within the rules', 'PASS han-forms Simplified Chinese: Noto Sans SC Thin Regular draws Simplified Chinese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Simplified Chinese/Japanese at wght 400) [page 1]', 'REVIEW leak scan: source and output share the spaceless CJK family; the scan cannot tell them apart. Rely on --translations and the visual pass.', 'PASS no untranslated running text', 'PASS isolated source-script tokens: none', 'PASS no empty translation targets', 'PASS authored translations present', 'PASS button captions', 'PASS caption width', 'PASS document metadata', 'PASS scaled runs: none, everything ships at source size', 'PASS write/find/say identifiers']
```

Two measured facts surfaced while building these fixtures and folded into the
final test data (not defects in the gate):
- `NotoSansJP-VF.ttf` (google/fonts, region-specific) has no glyph for 请
  (U+8BF7) or 栏 (U+680F): an echoed Simplified segment into a Japanese face
  is refused by `retypeset`'s glyph guard before `verify` ever sees it
  (`test_an_echoed_chinese_segment_into_the_japanese_face_is_refused_at_build`).
  The FAIL/REVIEW halves of the gate are instead exercised on a page drawn
  directly with the SC face (a stand-in for a pan-CJK face that draws both
  scripts).
- A `TextWriter` page drawn straight from a reference face, with no
  `retypeset` pass to canonicalise `ToUnicode`, drifts some characters to
  their CJK compatibility-ideograph codepoints on read-back: 年→U+F98E and
  郎→U+F92C were already measured in `docs/BRIEF-cjk-leak-tell.md` §2; 理→U+F9E4
  is the same phenomenon, hit while drawing `ZH_PARA` for the FAIL half above.
  `Finding.text` carries the line as MuPDF reads it back (by design), so the
  test compares NFKC-folded — the same fold `cjk_tell.tells_in` applies.

Green (17 gate tests + 1 Latin/no-lang/weak-pair set, all named):

```
test_a_clean_chinese_delivery_passes_with_the_date_the_name_and_a_drifted_target (tests.test_cjk_leak.LeakCjkGateTests.test_a_clean_chinese_delivery_passes_with_the_date_the_name_and_a_drifted_target) ... ok
test_a_kana_name_fails_at_six_and_is_allowlisted_as_a_phrase (tests.test_cjk_leak.LeakCjkGateTests.test_a_kana_name_fails_at_six_and_is_allowlisted_as_a_phrase) ... ok
test_a_non_cjk_delivery_is_untouched (tests.test_cjk_leak.LeakCjkGateTests.test_a_non_cjk_delivery_is_untouched) ... ok
test_a_single_rare_character_is_review_not_fail (tests.test_cjk_leak.LeakCjkGateTests.test_a_single_rare_character_is_review_not_fail) ... ok
test_a_traditional_source_into_japanese_is_the_weak_pair (tests.test_cjk_leak.LeakCjkGateTests.test_a_traditional_source_into_japanese_is_the_weak_pair) ... ok
test_an_echoed_chinese_segment_in_a_japanese_delivery_fails (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_chinese_segment_in_a_japanese_delivery_fails) ... ok
test_an_echoed_chinese_segment_into_the_japanese_face_is_refused_at_build (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_chinese_segment_into_the_japanese_face_is_refused_at_build) ... ok
test_an_echoed_japanese_segment_in_a_chinese_delivery_fails (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_japanese_segment_in_a_chinese_delivery_fails) ... ok
test_the_gate_is_named_after_leak_scan (tests.test_cjk_leak.LeakCjkGateTests.test_the_gate_is_named_after_leak_scan) ... ok
test_without_a_mapping_lang_the_old_review_line_stays (tests.test_cjk_leak.LeakCjkGateTests.test_without_a_mapping_lang_the_old_review_line_stays) ... ok
test_compatibility_ideographs_fold_before_the_tell (tests.test_cjk_leak.TellTests.test_compatibility_ideographs_fold_before_the_tell) ... ok
test_convention_of (tests.test_cjk_leak.TellTests.test_convention_of) ... ok
test_single_characters (tests.test_cjk_leak.TellTests.test_single_characters) ... ok
test_strip_allowed (tests.test_cjk_leak.TellTests.test_strip_allowed) ... ok
test_strong_pairs_and_the_weak_one (tests.test_cjk_leak.TellTests.test_strong_pairs_and_the_weak_one) ... ok
test_tells_in_keeps_order_and_repeats (tests.test_cjk_leak.TellTests.test_tells_in_keeps_order_and_repeats) ... ok
test_the_corpus_japanese_document (tests.test_cjk_leak.TellTests.test_the_corpus_japanese_document) ... ok
test_the_measured_table (tests.test_cjk_leak.TellTests.test_the_measured_table) ... ok

----------------------------------------------------------------------
Ran 18 tests in 9.401s

OK
```

Console parity, nine non-CJK jobs against `main` (v54):

```
# package: C:\Users\rodri\AppData\Local\Temp\claude\C--Dev-pdf-translate-skill\f71acf3b-389c-49ff-881b-f6d3f7417505\scratchpad\parity\main\pdf-translate\pdf_translate\__init__.py
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
CONSOLE IDENTICAL
VERDICTS IDENTICAL
```

Suite as CI runs it, eight modules: `Ran 388 tests in 146.280s` `OK`.

### Fix wave

Review finding (Important, reproduced): a single `--allow` token equal to a
whole echoed CJK line has no spaces, so it never reaches the `keep` phrase
path — `strip_allowed` erases every tell and the PASS line then claimed the
line held only characters the target can carry, with no trace that a line
had been allowed away. Fixed: `cjk_tell_report` now counts such a line as
`cleared`, appends it (truncated to 70 chars) to the kept-runs note, and the
PASS line gains ` ({cleared} line(s) cleared by --allow)` when any line was
cleared. Allowed stays allowed; it is no longer silent.

Red (`test_a_single_allow_token_that_clears_a_whole_line_is_said_so` fails on
the PASS line missing the `cleared` suffix; the FAIL/REVIEW combination test
already passed — the status logic needed no change):

```
FAIL: test_a_single_allow_token_that_clears_a_whole_line_is_said_so (tests.test_cjk_leak.LeakCjkGateTests.test_a_single_allow_token_that_clears_a_whole_line_is_said_so)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_cjk_leak.py", line 285, in test_a_single_allow_token_that_clears_a_whole_line_is_said_so
    self.assertIn('PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry (1 line(s) cleared by --allow)', lines)
AssertionError: 'PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry (1 line(s) cleared by --allow)' not found in [... 'PASS leak scan (CJK tell): 5 line(s) hold only characters a Simplified Chinese target can carry', ...]

----------------------------------------------------------------------
Ran 2 tests in 4.569s

FAILED (failures=1)
```

Green, module (12 gate tests + 8 tell tests):

```
test_a_page_with_a_fail_line_and_a_review_line_is_fail_and_lists_both (tests.test_cjk_leak.LeakCjkGateTests.test_a_page_with_a_fail_line_and_a_review_line_is_fail_and_lists_both) ... ok
test_a_single_allow_token_that_clears_a_whole_line_is_said_so (tests.test_cjk_leak.LeakCjkGateTests.test_a_single_allow_token_that_clears_a_whole_line_is_said_so) ... ok

----------------------------------------------------------------------
Ran 20 tests in 10.065s

OK
```

Suite as CI runs it, eight modules: `Ran 390 tests in 145.242s` `OK`. Parity
not re-run: the fix touches only the `same_spaceless`/`leak-cjk` path, never
the nine non-CJK parity jobs.

### Fix wave 2 — the whole-branch review

The Opus review's verdict on the whole branch: "with fixes", every item in the
reporting layer. Fixed: (I1) `leak-scan` no longer claims PASS for a scan the
CJK tell judged — it records SKIP `judged by leak-cjk`, and both the console
line and `cjk_tell_report`'s own PASS line now say a line of Han both
languages share is invisible to the tell; the two vacuous `leak-running`/
`leak-isolated` blocks are skipped once the tell has run, since they never
scanned anything. (I2+I3) The FAIL head names the source's convention
(`cjk_tell_report` gains `source=`) and offers `--allow` for a proper noun,
replacing the old two/three-way `other` guess. (I4) The unclear-source `why`
now says no single repertoire holds every one of the source's characters, or
several do. (M5) `cleared` is renamed `reduced`: a line whose tell count
`--allow` only lowered (not zeroed) joins the kept-runs note and the PASS
suffix. (M6) `cjk_tell.strip_allowed` matches case-insensitively (`verify`
lower-cases single `--allow` tokens). (M7) `cjk_tell._encodable` tolerates a
missing codec (a stripped CPython build) instead of raising.

Red, `LeakCjkGateTests` on the pre-fix-wave code (7 of 14 fail/error — the
3 ERRORs are `cjk_tell_report() got an unexpected keyword argument 'source'`,
since the new/changed tests already called it):

```
ERROR: test_a_page_with_a_fail_line_and_a_review_line_is_fail_and_lists_both (tests.test_cjk_leak.LeakCjkGateTests.test_a_page_with_a_fail_line_and_a_review_line_is_fail_and_lists_both)
ERROR: test_a_traditional_echo_into_a_simplified_target_is_named_traditional (tests.test_cjk_leak.LeakCjkGateTests.test_a_traditional_echo_into_a_simplified_target_is_named_traditional)
ERROR: test_an_echoed_chinese_segment_in_a_japanese_delivery_fails (tests.test_cjk_leak.LeakCjkGateTests.test_an_echoed_chinese_segment_in_a_japanese_delivery_fails)

Ran 14 tests in 10.478s

FAILED (failures=4, errors=3)
```

Red, `TellTests.test_strip_allowed` (the M6 case-insensitive `Nintendo`/カタカナ
assertion) on the pre-fix-wave `cjk_tell.py`:

```
Ran 8 tests in 0.013s

FAILED (failures=1)
```

Two of the brief's new tests needed a fixture correction, caught only after
measuring against the implemented code rather than guessed: the first
`--allow` list for `test_a_partial_allow_that_leaves_tells_is_still_noted`
stripped 8 of `JA[1]`'s 14 tells, landing on exactly `LINE_FAIL` (6) — still
FAIL, not the REVIEW the test wanted; a third token (`に`) strips a 9th,
landing on 5. `test_a_traditional_echo_into_a_simplified_target_is_named_traditional`
compared an NFKC-folded finding against the raw `TC_PARA` constant, which
carries a full-width comma (U+FF0C) that NFKC unconditionally folds to ASCII —
fixed by folding both sides of the comparison. Both corrections were
measured against `cjk_tell.strip_allowed`/`tells_in` directly before being
applied, byte-compared against the corrected fixtures afterward.

Green, module (14 gate tests + 8 tell tests):

```
Ran 22 tests in 10.602s

OK
```

Suite as CI runs it, eight modules: `Ran 392 tests in 154.323s` `OK`. Parity
not re-run: the `else` branch and every non-CJK path in `_execute_verify` are
untouched by this wave — console output of non-CJK jobs is unaffected by
construction. No pre-existing test outside `test_cjk_leak` exercises a CJK↔CJK
job with a usable `lang` through the `leak-running`/`leak-isolated` vacuous
PASS lines (the `test_pipeline.py`/`test_verify_report.py` hits on those two
strings are all Latin-target jobs), so none needed extending; the full
eight-module green run confirms nothing else regressed.

## Docs and version

`SKILL.md`'s Leak scan bullet and `references/gates.md`'s leak-scan section,
name list and `where`/`text` table now describe gate 21 `leak-cjk` in place
of the old "one REVIEW line, no gate" text; `README.md` counts twenty-one
structural gates; the CI suite line (`.github/workflows/tests.yml`) gains
`tests.test_cjk_leak`; the four version sources (`SKILL.md`,
`.claude-plugin/plugin.json`, `pdf-translate/pyproject.toml`,
`pdf_translate/__init__.py`) and the lockstep literal in
`tests/test_verify_report.py` move 54 → 55, red against the old sources
then green; `docs/DECISIONS.md` gains one ledger row for gate 21;
`docs/BRIEF-unattended-delivery.md`'s Task F header and the E2 row in
`docs/REQUESTS-from-product.md` are marked built/merged.

## Review
