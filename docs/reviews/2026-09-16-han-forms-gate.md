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
