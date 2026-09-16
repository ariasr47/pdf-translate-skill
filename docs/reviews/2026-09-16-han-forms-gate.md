# Gate 20 `han-forms` — evidence (v54)

Branch `feat/han-forms-gate`, stacked on `fix/stale-verify-report` (PR #7, v53) and `feat/kinsoku-gate`
(PR #6, v52). Spec: `docs/BRIEF-han-forms-gate.md` (measured 2026-09-16 with
`dev/probes/han_forms_probe.py`); the product's request 2b, reframed by
`docs/reviews/2026-09-16-cjk-request-assessment.md` §3 item 3 and accepted by its ruling R4.
A rendering change (`prepare_font` embeds four more glyphs; the gate judges rasters): AGENTS.md
Rule 1 applies — see the last section.

## Task 1 — the measurement, red then green

Red (the module does not exist):

```
ERROR: test_han_forms (unittest.loader._FailedTest.test_han_forms)
ImportError: cannot import name 'han_forms' from 'pdf_translate' (C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py)
Ran 1 test in 0.000s
FAILED (errors=1)
```

Green (the brief's rows 1, 3 and 4 within 0.02; the cache; the classifier pinned to verify's):

```
test_a_face_against_itself_is_zero (tests.test_han_forms.MeasurementTests.test_a_face_against_itself_is_zero) ... ok
test_convention_for_lang (tests.test_han_forms.MeasurementTests.test_convention_for_lang) ... ok
test_diff_ratio_edge_cases (tests.test_han_forms.MeasurementTests.test_diff_ratio_edge_cases) ... ok
test_is_cjk_agrees_with_verify (tests.test_han_forms.MeasurementTests.test_is_cjk_agrees_with_verify) ... ok
test_no_reference_without_the_file_the_convention_or_the_axis (tests.test_han_forms.MeasurementTests.test_no_reference_without_the_file_the_convention_or_the_axis) ... ok
test_references_instanced_at_400_reproduce_the_table_and_are_cached (tests.test_han_forms.MeasurementTests.test_references_instanced_at_400_reproduce_the_table_and_are_cached) ... ok
test_the_regions_separate_on_the_probes_and_agree_on_the_control (tests.test_han_forms.MeasurementTests.test_the_regions_separate_on_the_probes_and_agree_on_the_control) ... ok
test_weight_alone_is_as_large_a_difference_as_region (tests.test_han_forms.MeasurementTests.test_weight_alone_is_as_large_a_difference_as_region) ... ok

Ran 8 tests in 12.527s

OK
```

The first green run instanced Noto Sans JP and Noto Sans SC at wght 400 (12.527 s total for the
suite), leaving `NotoSansJP-VF-wght400.ttf` and `NotoSansSC-VF-wght400.ttf` cached beside the
source faces in `tests/fonts/` (`.gitignore` excludes them; `git status --short tests/fonts`
prints nothing). A second run against the warm cache completed the same 8 tests in 0.582 s,
confirming `reference_face` returns the cached path without re-instancing.

## Task 3 — the gate, red then green

Red: before the gate exists, a Japanese job delivered in the Simplified Chinese face verifies
clean (nothing judges the face):

```
FAIL: test_the_gate_is_named_after_kinsoku (tests.test_han_forms.VerifyGateTests.test_the_gate_is_named_after_kinsoku)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_han_forms.py", line 282, in test_the_gate_is_named_after_kinsoku
    self.assertEqual(GATE_NAMES[GATE_NAMES.index('kinsoku') + 1], 'han-forms')
AssertionError: 'leak-scan' != 'han-forms'

FAIL: test_a_japanese_delivery_in_the_chinese_face_fails (tests.test_han_forms.VerifyGateTests.test_a_japanese_delivery_in_the_chinese_face_fails)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_han_forms.py", line 300, in test_a_japanese_delivery_in_the_chinese_face_fails
    self.assertEqual(rc, 1, lines)
AssertionError: 0 != 1 : ['leak scan: source script Latin; output script CJK', 'fields: 0 original / 0 translated',
'PASS field parity', 'SKIP fill round-trip (no fields)', 'PASS page 1 ink ratio: 0.43', 'PASS text layer is visible',
'PASS canonical text layer', 'PASS kinsoku: 1 CJK line(s) break within the rules', 'PASS no untranslated running text',
'PASS isolated source-script tokens: none', 'PASS no empty translation targets', 'PASS authored translations present',
'PASS button captions', 'PASS caption width', 'PASS document metadata', 'PASS scaled runs: none, everything ships at
source size', 'PASS write/find/say identifiers']
```

Two of the brief's twelve `VerifyGateTests` assertions did not match the real pipeline (MuPDF
embeds the face's `/BaseFont` with spaces, and `_with_lang`'s output `/Lang` disagreeing with the
mapping's makes the pre-existing `metadata` gate FAIL on its own); the plan was amended in place
(same commit) to tolerate the space-separated face name and to assert the Traditional Chinese
and Simplified Chinese cases through gate names/status rather than the overall exit code alone.

Green:

```
test_a_latin_face_is_skipped (tests.test_han_forms.JudgeTests.test_a_latin_face_is_skipped) ... ok
test_another_family_is_review_not_the_nearer_reference (tests.test_han_forms.JudgeTests.test_another_family_is_review_not_the_nearer_reference) ... ok
test_document_level_reasons (tests.test_han_forms.JudgeTests.test_document_level_reasons) ... ok
test_fewer_than_two_probes_is_skipped (tests.test_han_forms.JudgeTests.test_fewer_than_two_probes_is_skipped) ... ok
test_judge_file_names_the_face_from_its_program (tests.test_han_forms.JudgeTests.test_judge_file_names_the_face_from_its_program) ... ok
test_the_chinese_reference_both_ways (tests.test_han_forms.JudgeTests.test_the_chinese_reference_both_ways) ... ok
test_the_japanese_reference_draws_japanese_forms (tests.test_han_forms.JudgeTests.test_the_japanese_reference_draws_japanese_forms) ... ok
test_the_japanese_reference_fails_a_simplified_chinese_job (tests.test_han_forms.JudgeTests.test_the_japanese_reference_fails_a_simplified_chinese_job) ... ok
test_a_face_against_itself_is_zero (tests.test_han_forms.MeasurementTests.test_a_face_against_itself_is_zero) ... ok
test_convention_for_lang (tests.test_han_forms.MeasurementTests.test_convention_for_lang) ... ok
test_diff_ratio_edge_cases (tests.test_han_forms.MeasurementTests.test_diff_ratio_edge_cases) ... ok
test_is_cjk_agrees_with_verify (tests.test_han_forms.MeasurementTests.test_is_cjk_agrees_with_verify) ... ok
test_no_reference_without_the_file_the_convention_or_the_axis (tests.test_han_forms.MeasurementTests.test_no_reference_without_the_file_the_convention_or_the_axis) ... ok
test_references_instanced_at_400_reproduce_the_table_and_are_cached (tests.test_han_forms.MeasurementTests.test_references_instanced_at_400_reproduce_the_table_and_are_cached) ... ok
test_the_regions_separate_on_the_probes_and_agree_on_the_control (tests.test_han_forms.MeasurementTests.test_the_regions_separate_on_the_probes_and_agree_on_the_control) ... ok
test_weight_alone_is_as_large_a_difference_as_region (tests.test_han_forms.MeasurementTests.test_weight_alone_is_as_large_a_difference_as_region) ... ok
test_a_bold_delivery_is_judged_at_its_own_weight (tests.test_han_forms.VerifyGateTests.test_a_bold_delivery_is_judged_at_its_own_weight) ... ok
test_a_japanese_delivery_in_the_chinese_face_fails (tests.test_han_forms.VerifyGateTests.test_a_japanese_delivery_in_the_chinese_face_fails) ... ok
test_a_japanese_delivery_in_the_japanese_face_passes (tests.test_han_forms.VerifyGateTests.test_a_japanese_delivery_in_the_japanese_face_passes) ... ok
test_a_non_cjk_lang_on_a_cjk_page_prints_nothing (tests.test_han_forms.VerifyGateTests.test_a_non_cjk_lang_on_a_cjk_page_prints_nothing) ... ok
test_a_subset_without_the_probes_is_review_cannot_attest (tests.test_han_forms.VerifyGateTests.test_a_subset_without_the_probes_is_review_cannot_attest) ... ok
test_missing_reference_faces_are_review (tests.test_han_forms.VerifyGateTests.test_missing_reference_faces_are_review) ... ok
test_no_lang_anywhere_is_review (tests.test_han_forms.VerifyGateTests.test_no_lang_anywhere_is_review) ... ok
test_the_cli_takes_reference_fonts (tests.test_han_forms.VerifyGateTests.test_the_cli_takes_reference_fonts) ... ok
test_the_gate_is_named_after_kinsoku (tests.test_han_forms.VerifyGateTests.test_the_gate_is_named_after_kinsoku) ... ok
test_the_mapping_lang_names_the_convention (tests.test_han_forms.VerifyGateTests.test_the_mapping_lang_names_the_convention) ... ok
test_traditional_chinese_has_no_reference_yet (tests.test_han_forms.VerifyGateTests.test_traditional_chinese_has_no_reference_yet) ... ok
test_without_translations_the_output_lang_is_used (tests.test_han_forms.VerifyGateTests.test_without_translations_the_output_lang_is_used) ... ok

Ran 28 tests in 44.870s

OK
```

Console parity, nine non-CJK jobs against `main` (v51):

```
# package: C:\Users\rodri\AppData\Local\Temp\claude\C--Dev-pdf-translate-skill\f71acf3b-389c-49ff-881b-f6d3f7417505\scratchpad\parity\main\pdf-translate\pdf_translate\__init__.py
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
CONSOLE IDENTICAL
VERDICTS IDENTICAL
```

Suite as CI runs it, seven modules: `Ran 351 tests in 109.079s` ... `OK`.

## Task 4 — prepare_font, red then green

Red: a subset built from 申請書を提出 lacks 直 (the brief's "not drawn"), and a Japanese job set
with the Simplified Chinese face is prepared without complaint:

```
FAIL: test_a_cjk_subset_carries_the_probes (tests.test_han_forms.PrepareFontTests.test_a_cjk_subset_carries_the_probes)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_han_forms.py", line 410, in test_a_cjk_subset_carries_the_probes
    self.assertTrue(font.has_glyph(ord(ch)), f'U+{ord(ch):04X} missing from the subset')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: 0 is not true : U+76F4 missing from the subset

======================================================================
FAIL: test_a_japanese_job_with_the_chinese_face_is_refused (tests.test_han_forms.PrepareFontTests.test_a_japanese_job_with_the_chinese_face_is_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "C:\Dev\pdf-translate-skill\pdf-translate\tests\test_han_forms.py", line 422, in test_a_japanese_job_with_the_chinese_face_is_refused
    self.assertEqual(rc, 1, log)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^
AssertionError: 0 != 1 : OK: C:\Users\rodri\AppData\Local\Temp\tmpf9jy65dq\subset.ttf (20 KB, 124 chars, render check 229 px)
```

Also red, differently from the brief's step-2 narrative: `test_a_japanese_job_with_the_japanese_face_passes`
failed on the missing PASS line, `test_the_cli_takes_reference_fonts` failed `0 != 1`, and
`test_without_lang_or_references_prepare_font_stays_quiet` **errored** (`TypeError: prepare_font() got
an unexpected keyword argument 'reference_fonts'`) rather than passing outright — the brief's Step 2
text says this one "passes already"; in this checkout it does not, because its second call already
passes `reference_fonts=empty` to `prepare_font`, a keyword that does not exist before Step 3. Only
`test_a_latin_subset_is_left_alone` passed unmodified at red. `Ran 6 tests in 63.083s` — `FAILED
(failures=4, errors=1)`.

Green:

```
test_a_cjk_subset_carries_the_probes (tests.test_han_forms.PrepareFontTests.test_a_cjk_subset_carries_the_probes) ... ok
test_a_japanese_job_with_the_chinese_face_is_refused (tests.test_han_forms.PrepareFontTests.test_a_japanese_job_with_the_chinese_face_is_refused) ... ok
test_a_japanese_job_with_the_japanese_face_passes (tests.test_han_forms.PrepareFontTests.test_a_japanese_job_with_the_japanese_face_passes) ... ok
test_a_latin_subset_is_left_alone (tests.test_han_forms.PrepareFontTests.test_a_latin_subset_is_left_alone) ... ok
test_the_cli_takes_reference_fonts (tests.test_han_forms.PrepareFontTests.test_the_cli_takes_reference_fonts) ... ok
test_without_lang_or_references_prepare_font_stays_quiet (tests.test_han_forms.PrepareFontTests.test_without_lang_or_references_prepare_font_stays_quiet) ... ok
[... the pre-existing 28 tests of MeasurementTests, JudgeTests, VerifyGateTests, all ok ...]

Ran 34 tests in 89.212s

OK
```

Suite, seven modules: `Ran 357 tests in 251.755s` ... `OK`.

## Docs and version

`SKILL.md` gate bullet; `references/gates.md` row, name list, consumer paragraph, `where`/`text`
row, flag; `references/fonts.md` on matching builds; `README.md` twenty gates; `docs/DECISIONS.md`
row with the measured table; version 53 → 54 in SKILL.md, plugin.json, pyproject.toml,
`__version__` and the lockstep literal; `tests.test_han_forms` on the CI suite line.

## Rule 1 verification

Appended by the independent verifier's pass, on another model, after the whole-branch review —
not by the implementer of any task. Until that section is here, this gate is not verified.
