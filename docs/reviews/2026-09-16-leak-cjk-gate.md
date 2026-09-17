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
