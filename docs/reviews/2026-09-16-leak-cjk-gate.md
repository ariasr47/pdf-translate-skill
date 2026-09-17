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
