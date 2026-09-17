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

## Fix wave after the whole-branch review

Branch `feat/han-forms-gate`, HEAD 40d37ef at the start of this wave. The whole-branch review
(Opus) reproduced one Critical and named three Important items and a triage of minors; brief:
`.superpowers/sdd/fix-wave-brief.md`.

### C1 (Critical) — judge only the faces that drew the page's CJK glyphs

Red on 40d37ef, `tests.test_han_forms -v`, the four new `AttributionTests` (added calling the
new 4-argument `han_forms_report(doc, lang, '', FONTS)` against the still-3-argument function on
40d37ef — the old code has no attribution at all, so every one of the four errors before it can
reach the scenario it reproduces):

```
ERROR: test_a_chinese_face_that_drew_only_latin_does_not_fail_a_japanese_page (tests.test_han_forms.AttributionTests.test_a_chinese_face_that_drew_only_latin_does_not_fail_a_japanese_page)
ERROR: test_a_chinese_face_that_drew_the_japanese_fails_even_beside_a_japanese_face (tests.test_han_forms.AttributionTests.test_a_chinese_face_that_drew_the_japanese_fails_even_beside_a_japanese_face)
ERROR: test_a_probeless_face_that_drew_the_japanese_cannot_hide_behind_another_face (tests.test_han_forms.AttributionTests.test_a_probeless_face_that_drew_the_japanese_cannot_hide_behind_another_face)
ERROR: test_an_unused_chinese_face_does_not_fail_a_japanese_page (tests.test_han_forms.AttributionTests.test_an_unused_chinese_face_does_not_fail_a_japanese_page)
TypeError: han_forms_report() takes from 2 to 3 positional arguments but 4 were given
```

The real-pipeline reproduction of the defect is the new `VerifyGateTests.test_a_chinese_source_translated_to_japanese_passes`
(a genuine zh → ja delivery through `build_delivery`/`retypeset`, calling the *existing* 3-argument
`han_forms_report` via `_execute_verify` unmodified — this one runs the real old logic, not a
signature mismatch), also red on 40d37ef:

```
FAIL: test_a_chinese_source_translated_to_japanese_passes (tests.test_han_forms.VerifyGateTests.test_a_chinese_source_translated_to_japanese_passes)
AssertionError: 'REVIEW' != 'PASS'
- REVIEW
+ PASS
 : GateResult(name='han-forms', status='REVIEW', message='', findings=(Finding(page=1, where='Noto Sans SC Thin', text='no reference of this family: Noto Sans SC Thin differs from both Noto references on 東 (0.027/0.027), which is drawn the same in both conventions; check a render with a reader of the language'), Finding(page=1, where='Noto Sans JP Regular', text='PASS han-forms Japanese: Noto Sans JP Regular draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400)')))
```

This diverges from the brief's own narrative in shape, not in substance: the brief describes the
leftover-face reproduction as a printed FAIL (exit 1); what this checkout's `strip_text` actually
leaves behind (the source's un-instanced default-named "Noto Sans SC Thin", i.e. wght 100, not the
job's wght 400) reads 0.027/0.027 on 東 against both references at wght 100 — just outside `OWN_MAX`
— so the old code's per-xref judging returns REVIEW "no reference of this family" for that xref
rather than FAIL. Either way the defect is the same one C1 names: a face that drew nothing on the
page is judged anyway and pollutes the gate's status on a correct delivery. Confirmed by hand: the
same delivery's output page carries both `Noto Sans SC Thin` and `Noto Sans JP Regular` in
`get_fonts(full=True)` (asserted in the test), and only the JP face drew CJK glyphs.

Also red: `test_a_subset_without_the_probes_is_review_cannot_attest`'s wording assertion, updated
to the new "cannot attest" text ahead of the code change (`AssertionError` on the old wording).

Green after `han_forms.font_key`/`program_psname` and `verify._cjk_drawing_fonts` +
`han_forms_report`'s new `(doc, mapping_lang, output_lang, reference_dir=None)` signature:

```
Ran 41 tests in 142.914s
OK
```

(34 pre-existing + 7 new: 4 `AttributionTests`, the zh → ja integration test, the stale-`/Lang`
test (I3), the `prepare_font` REVIEW test (minor 2).)

### I3 (Important) — a stale non-CJK `/Lang` is REVIEW, not silence

Red on 40d37ef: `test_a_stale_non_cjk_output_lang_is_review_not_silence` — `IndexError: list index
out of range` (no `han-forms` gate recorded at all: the old code was silent). Green with the new
signature's `output_lang` branch: `gate.status == 'REVIEW'`, `findings[0].where == 'lang'`,
`'/Lang "en"'` in the text. `test_a_non_cjk_lang_on_a_cjk_page_prints_nothing` (mapping `es`) stays
green — the mapping is still authoritative.

### I4 (Important) — the 東 reason must not over-claim

`judge_program`'s family-REVIEW reason gained "— not a Noto face, or not the same build or weight
as the references (references/fonts.md)". `JudgeTests.test_another_family_is_review_not_the_nearer_reference`
asserts the substring `'no reference of this family'` (`assertIn`, not exact) and stayed green
without modification.

### Parity and suite

Console parity, nine non-CJK jobs against `main` (refreshed archive; commands identical to Task 3
Step 5):

```
# package: .../scratchpad/parity/main/pdf-translate/pdf_translate/__init__.py
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
CONSOLE IDENTICAL
VERDICTS IDENTICAL
```

Seven-module suite: `Ran 364 tests in 191.243s` ... `OK` (357 + 7 new, all in `tests.test_han_forms`).

### Minors fixed in this wave

1. `_face(JP_FACE), _face(SC_FACE)` split into two statements in `JudgeTests.setUpClass` and
   `VerifyGateTests.setUpClass`.
2. `PrepareFontTests.test_another_family_is_reviewed_not_refused` added (MuPDF's bundled Droid
   Sans Fallback face is REVIEW, not refused, `rc == 0`); it passed on the first run, pinning
   existing behaviour rather than reproducing a defect, exactly as the brief anticipated.
3. `han_forms.MIN_SEPARATING` split into `MIN_PROBES_PRESENT = 2` (the SKIP test) and
   `MIN_SEPARATING = 2` (the verdict), each with its own one-line comment.
4. `han_forms.reference_face`'s `tempfile.mkstemp` suffix changed from `.tmp` to `.tmp.ttf` so a
   run killed mid-instancing leaves a file `.gitignore`'s `*.ttf` rule covers.
5. `han_forms.judge_program`'s weight-REVIEW reason: "cannot read OS/2 (a bare CFF or Type 3
   program)" in place of "not a TrueType or OpenType program".
6. `HanResult.line()` docstring: "PASS/FAIL/REVIEW/SKIP style".
7. `HanResult.line()`: one-line comment above `other = CONVENTIONS[OTHER[self.convention]][0]`
   noting that TC/KR never reach it (`reference_status` bounces them to REVIEW first).
8. `tests/test_verify_report.py` `FindingsInvariantTests.test_every_fail_or_review_gate_has_a_finding`:
   left unchanged. Its `expected` tuple (`'metadata', 'metadata-lang', 'scaled-runs',
   'override-markers', 'leak-running', 'leak-scan', 'extractable-text', 'visible-text'`) is a flat
   coverage list checked with `assertIn` across every job the test builds, not a per-job
   enumeration naming which gates the Japanese `spaceless` job must exercise. `han-forms` already
   appears in that test's `seen` set both before and after this fix (the spaceless job's page,
   drawn with MuPDF's bundled CJK face and no `lang` anywhere, is REVIEW "no \"lang\" names the
   convention" either way) — the assertion needed no edit, and the seven-module suite run above
   confirms it still passes.

Left as the review said (not touched this wave): the wide `except`s, the `_dir` re-wrap, the
repeated cell format, `ko`, the double `reference_status`, the third `json.load`.

## Fix wave 2

A re-review after fix wave 1 found a second small defect in the same function: a drawing face
that is SKIP (carries no probes) or has no embedded program was swallowed whenever another
drawing face on the same page attested, because the old `attested`/`unattested` bookkeeping was
per-page, not per-face. Also: an empty span font name (`han_forms.font_key` returning `''`) made
`_cjk_drawing_fonts`'s key set empty, which dropped the page out of `cjk_pages` entirely — silence
where an unmatched key should give REVIEW — and the "cannot attest" reason named the wrong remedy
(rebuild the subset) for a face that was never even matched to a drawing key.

Red first, `tests.test_han_forms.AttributionTests`, on the wave-1 commit (`81ecbce`):

```
FAIL: test_a_probeless_drawing_face_is_reported_even_when_another_face_attests
AssertionError: 'PASS' != 'REVIEW'
 : ['PASS han-forms Japanese: Noto Sans JP Thin draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171,
    海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400) [page 1]']
```
(The probe-less Chinese subset drawing 申請書を提出 is swallowed; only the Japanese face's PASS
line survives, so the page reports PASS with one finding instead of PASS+REVIEW with two.)

```
ERROR: test_an_unnamed_span_font_is_cannot_attest_not_silence
TypeError: unsupported operand type(s) for &: 'set' and 'tuple'
```
(`_cjk_drawing_fonts` still returned a bare `keys` set; mocking it to `(True, set())` — the shape
the fix requires — breaks the unpacking, confirming the old code has no way to represent "draws
CJK, but no font name to key on" separately from "draws nothing".)

Also red: `VerifyGateTests.test_a_subset_without_the_probes_is_review_cannot_attest`'s updated
wording assertions (`'carries none of the probes'` not present in the old "no embedded face that
drew the page's CJK text carries the probes" reason).

Green after `_cjk_drawing_fonts` returning `(draws, keys)`, `cjk_pages` filtered on `draws`, and
`han_forms_report`'s per-face `matched`/`without_probes`/`unjudgeable`/`unmatched` bookkeeping
(grouped into `unattested: page -> reason`, then `by_reason` for the printed lines):

```
Ran 43 tests in 124.352s
OK
```
(41 wave-1 + 2 new: `test_a_probeless_drawing_face_is_reported_even_when_another_face_attests`,
`test_an_unnamed_span_font_is_cannot_attest_not_silence`.)

Parity re-run (same fixtures and `main` archive as fix wave 1, both runners re-run against this
change): `CONSOLE IDENTICAL`, `VERDICTS IDENTICAL`.

Seven-module suite: `Ran 366 tests in 192.446s` ... `OK` (364 + 2 new, both in
`tests.test_han_forms`).

Docs: `references/gates.md` han-forms row and `docs/DECISIONS.md` han-forms row both gained "A
drawing face that carries no probes, or is not an embedded program, is cannot-attest for that
page even when another drawing face passes" (or the DECISIONS.md parenthetical equivalent),
right after the existing "neither fails nor attests" clause.

Fix wave 3: a residual named by the confirmation pass — `_cjk_drawing_fonts` discarded the empty
key of an unnamed-font CJK span (`keys.discard('')`), so a page drawing one CJK run through an
unnamed span and another through a judgeable named face lost the unnamed drawer silently (the
named face's key fully covered `matched`, leaving `unmatched` empty). Fixed by keying an unnamed
span's contribution as the sentinel `'an unnamed font'` instead of discarding it. The first test
written for this (`test_an_unnamed_drawer_beside_a_named_face_is_reported`, mocking
`_cjk_drawing_fonts`'s return value directly) passed unchanged on the pre-fix code — it exercises
only `han_forms_report`'s consumption of the sentinel, already correct since fix wave 2, not
`_cjk_drawing_fonts`'s production of it — so it does not prove the gap; kept as a report-level
pin, not treated as the red. The real red is the extraction-level
`test_a_span_without_a_font_name_contributes_the_unnamed_key`, run against the pre-fix
`_cjk_drawing_fonts` by reverting only that function's patch (`git apply -R`, not `git stash`) and
restoring it afterward (`git apply`, diffed byte-identical to the original patch before
re-applying):
```
AssertionError: Items in the second set but not the first:
'an unnamed font'
```
Green after restoring the fix: `tests.test_han_forms -v` → `Ran 45 tests in 87.236s` `OK` (43 + 2
new). Parity not re-run: no non-CJK code path changed. Seven-module suite: `Ran 368 tests in
140.984s` `OK` (366 + 2 new).

## Rule 1 verification

Independent pass by Claude Opus 5 (1M context), 2026-09-16, on branch `feat/han-forms-gate` at
`81ad568` with a clean tree — a session that wrote none of this code and started from runs, not
from the diff. Environment: `C:/Dev/pdf-translate-skill/pdf-translate.venv/Scripts/python.exe`
with `PYTHONUTF8=1`, run from `pdf-translate/`; PyMuPDF 1.28.2; the fetched `NotoSansJP-VF.ttf`
and `NotoSansSC-VF.ttf` with their wght 400 instances cached beside them.

**Verdict: Verified.** Every claim below was re-run here; the two 600 dpi rasters agree with the
gate's verdicts; console and verdict parity with `main` is byte-identical. One scoped limitation
is recorded under item 6 — it is a limit of what three probe glyphs can prove, not a false claim
by any gate line, and the gate's own PASS rule in `references/gates.md` describes exactly the
measurement it makes.

### 1. The suites

```
$ python -m unittest tests.test_han_forms -v
Ran 45 tests in 91.826s
OK

$ python -m unittest tests.test_pipeline tests.test_corpus_verdicts tests.test_import_surface \
      tests.test_shaping_probe tests.test_verify_report tests.test_cjk tests.test_han_forms
Ran 368 tests in 140.876s
OK
```

### 2. The runs

`scratchpad/verifier_han_forms.py`, unedited. It first died on an environment collision, not on
its own code: a stale `inspect.py` left in the scratchpad by an earlier session shadows the
stdlib module for any script run from that directory (`AttributeError: module 'inspect' has no
attribute 'signature'`, then `ModuleNotFoundError: No module named 'mupdf'`). Re-run unchanged
with `python -P` (script directory kept off `sys.path`), exit 0:

```
work: C:\Users\rodri\AppData\Local\Temp\han-forms-verify-whpx65bd
faces: True True | pymupdf 1.28.2

== 1. real deliveries, lang ja ==
-- jp face: exit 0
    PASS han-forms Japanese: Noto Sans JP Regular draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400) [page 1]
    render of 直: ...\jp-U76F4-600dpi.png chars found: 1
-- sc face: exit 1
    FAIL han-forms Japanese: Noto Sans SC Regular draws Simplified Chinese forms (直 0.454/0.000, 骨 0.171/0.000, 海 0.212/0.000 vs Japanese/Simplified Chinese at wght 400) [page 1] — a reader of the language sees the other region's shapes; rebuild with a face of the language (references/fonts.md)
    render of 直: ...\sc-U76F4-600dpi.png chars found: 1

== 2. zh -> ja delivery (source face survives strip_text) ==
    fonts in the page resources: ['Noto Sans SC Thin', 'Noto Sans JP Regular']
-- exit 0
    PASS han-forms Japanese: Noto Sans JP Regular draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400) [page 1]

== 3. two drawing faces: SC draws 申請書を提出, JP draws 直骨海東京 (lang ja) ==
   status: FAIL | findings: [(1, 'Noto Sans SC Thin'), (1, 'Noto Sans JP Thin')]
    FAIL han-forms Japanese: Noto Sans SC Thin draws Simplified Chinese forms (直 0.454/0.000, 骨 0.171/0.000, 海 0.212/0.000 vs Japanese/Simplified Chinese at wght 400) [page 1] — ...
    PASS han-forms Japanese: Noto Sans JP Thin draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400) [page 1]

== 4. two drawing faces: probe-less SC subset draws, JP draws (lang ja) ==
   status: REVIEW | findings: [(1, 'Noto Sans JP Thin'), (1, 'JP')]
    PASS han-forms Japanese: Noto Sans JP Thin draws Japanese forms (直 0.000/0.454, 骨 0.000/0.171, 海 0.000/0.212 vs Japanese/Simplified Chinese at wght 400) [page 1]
    REVIEW han-forms Japanese: cannot attest [page 1]: Noto Sans SC Thin Regular drew CJK text but carries none of the probes "直骨海東" — rebuild that subset with prepare_font.py, which adds them
```

All four sections match what the gate claims: exit 0 with a PASS and exit 1 with a FAIL on the
two real deliveries; the leftover Simplified Chinese source face in the zh → ja delivery is not
judged and no FAIL line appears; two drawing faces give both a FAIL and a PASS; the probe-less
drawing face is cannot-attest beside a passing face rather than being swallowed. Cosmetic only:
an instanced reference keeps its source name table, so a face reads "Noto Sans JP Thin" (and
"Noto Sans SC Thin Regular" for the subset) while the judge instanced at wght 400 — the line
states "at wght 400", so no verdict is affected.

### 3. The eye — 直 at 600 dpi, clipped from the two delivered pages

Both PNGs opened and looked at, and the two compared side by side (XOR over the union of ink
between the two clips: 0.426; the files are not byte-identical).

- `jp-U76F4-600dpi.png` (the delivery the gate PASSed) — **the Japanese form.** The lowest
  stroke is one L: a vertical standing to the left of and below the 目 box, running down and
  turning right into a long horizontal that passes under the box and out past its right edge.
  The box floats above that stroke, detached from it, and has three inner white rows.
- `sc-U76F4-600dpi.png` (the delivery the gate FAILed as "draws Simplified Chinese forms") —
  **the Simplified Chinese form.** No hook: the box's own left and right verticals run down to a
  flat horizontal bar under it that extends on both sides, the whole glyph symmetric and wider,
  with four inner white rows.

My eye agrees with the gate on both. The PASS was drawn in Japanese forms; the FAIL was drawn in
Simplified Chinese forms.

### 4. Console parity with `main`, nine non-CJK jobs

```
# package: ...\scratchpad\parity\main\pdf-translate\pdf_translate\__init__.py
# package: C:\Dev\pdf-translate-skill\pdf-translate\pdf_translate\__init__.py
CONSOLE IDENTICAL
VERDICTS IDENTICAL
```

(`main` re-archived for this run; `verdict_parity_fixtures.py` rebuilt; nine `--- verdict` blocks
in each stderr half.)

### 5. The evidence doc's claims against these runs

Supported: `Ran 45` / `Ran 368` `OK`; the ratios quoted in every gate line (直 0.454, 骨 0.171,
海 0.212 at wght 400, 東 0.000) are the brief's §2 row 4, and `MeasurementTests` reproduces the
table within 0.02; `CONSOLE IDENTICAL` / `VERDICTS IDENTICAL`; the warm cache ("0.582 s" for the
8 measurement tests — 0.586 s here); `git status --short tests/fonts` prints nothing, so the
instanced references stay untracked; `han-forms` sits immediately after `kinsoku` in
`GATE_NAMES`; version 54 in `SKILL.md`, `.claude-plugin/plugin.json`, `pyproject.toml` and
`__version__`, with the SKILL.md "Han forms" bullet present.

Two "red" narratives re-run here rather than taken on trust, both against archived trees of the
branch's own earlier commits (`git archive`, never `git stash`), judging the *same* delivered
PDF:

```
### pre-fix 40d37ef ###          (fix wave 1, C1)
# signature: (doc, lang, reference_dir=None)
# fonts in the page resources: ['Noto Sans SC Thin', 'Noto Sans JP Regular']
status: REVIEW
   finding p1 where='Noto Sans SC Thin': no reference of this family: ... on 東 (0.027/0.027) ...
### HEAD 81ad568 ###
# signature: (doc, mapping_lang, output_lang, reference_dir=None)
status: PASS
   finding p1 where='Noto Sans JP Regular': PASS han-forms Japanese: ...
```

```
### pre-fix ab98c09 ###          (fix wave 3, the unnamed-span key)
FAIL: test_a_span_without_a_font_name_contributes_the_unnamed_key
AssertionError: Items in the second set but not the first: 'an unnamed font'
Ran 1 test in 0.002s / FAILED (failures=1)
### HEAD 81ad568 ###
python -m unittest tests.test_han_forms.AttributionTests -v → Ran 8 tests in 1.063s / OK
```

Both reproduce exactly as written, including the doc's note that the C1 reproduction reads
REVIEW (0.027/0.027 on 東 against the un-instanced leftover face) rather than the brief's
predicted FAIL. No claim in this document is unsupported by these runs. Not re-run: the red
states of tasks 1, 3 and 4 and of fix wave 2, which live at commits already rewritten by the
later waves; the reds above are the load-bearing ones.

### 6. My own probe — can a face lie to the gate?

Two hand-built programs, judged both as programs (`han_forms.judge_file`) and through the gate on
a real page (`verify.han_forms_report`). Script: `scratchpad/v1_probe_mine.py`.

**A. Name spoof — honest.** The Simplified Chinese program with its `name` table rewritten to
"Noto Sans JP" / "NotoSansJP-Regular":

```
program PostScript name now: NotoSansJP-Thin
judge_file(lang ja) -> FAIL
FAIL han-forms Japanese: NotoSansJP-Thin draws Simplified Chinese forms (直 0.454/0.000, 骨 0.171/0.000, 海 0.212/0.000 ...)
```

The gate judges outlines, not names: a face that merely claims to be Japanese still FAILs.

**B. Probe forgery — a PASS the face does not deserve.** The Simplified Chinese program with the
outlines of 直 骨 海 東, and only those four, replaced by the Japanese face's (fontTools glyf +
hmtx swap). Every other Han glyph — that is, all the text a delivery actually draws — stays
Simplified Chinese:

```
forged face vs (JP, SC)      probe 直 0.000 / 0.454    probe 骨 0.000 / 0.171
                             probe 海 0.000 / 0.212    probe 東 0.000 / 0.000
ordinary text                真 0.156 / 0.000   者 0.000 / 0.000   令 0.628 / 0.000
                             涼 0.225 / 0.000   道 0.185 / 0.000   言 0.493 / 0.000
                             集 0.188 / 0.000
judge_file(lang ja) -> PASS
status: PASS | findings: [(1, 'Noto Sans SC Thin')]
   PASS han-forms Japanese: Noto Sans SC Thin draws Japanese forms (直 0.000/0.454, ...) [page 1]
```

A page drawn entirely in that face PASSes `lang ja` while every character on it is Simplified
Chinese. This is a limit of the method, not a defect of this implementation: the gate measures
what `references/gates.md` says it measures (two of 直 骨 海, own ≤ 0.02, other ≥ 0.10) and prints
the ratios it measured, so it never guesses — but its PASS generalises from four glyphs to the
whole face, and the printed wording "draws Japanese forms" is broader than that. `prepare_font`
takes the probes from the caller's own face, so the pipeline cannot produce such a hybrid by
accident; a merged or hand-edited multi-source CJK face could. Worth a sentence in `gates.md`
naming the scope ("on the probe glyphs"), and, if the gate is ever hardened, judging a handful of
characters the page actually drew instead of only the four probes. Not a blocker, and not fixed
here: this pass changes no code.

**Verified.**
