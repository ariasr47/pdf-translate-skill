# R-99: the ResourceWarnings are closed — 25 September 2026

**Assignment.** R-99 is the next of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-99 in
`docs/REVIEW-2026-09-24.md`: 45 ResourceWarnings per CI leg, 43 of them from
`review.py`. It also says TTFonts are never closed in `han_forms` and
`prepare_font`.

It ships as v75, stacked on #44 (R-100, v74). It bumps the version because
three shipped modules change.

## Reproduced before building

The last full suite run on v74 printed exactly **45** `ResourceWarning`s:
- **43** were `unclosed file <_io.TextIOWrapper name='…/NOTES.md'>`.
- **2** were `unclosed file <_io.BufferedReader name='…/NotoSansJP-VF-wght400.ttf'>`
  and the same for `NotoSansSC-VF-wght400.ttf`.

**Where each comes from.** Tracing allocations (`PYTHONTRACEMALLOC=12`)
located them:
- The `NOTES.md` handle is `run_review`'s bare
  `open(notes_path).read()`, once per review of a job that has notes.
- The two font handles are **not** from `han_forms` or `prepare_font`. They
  are from this suite's own helper, `tests/test_han_forms.py::_subset`. It
  loads a face with `fontTools.subset.load_font`, which opens it
  `lazy=True` and keeps the file, and never closes it.
- **The review's two library sites held no handle.** In fontTools 4.64
  (`ttFont.py:309-317`), a face opened by path without `lazy=True` is read
  into memory and its file closed at once. Their `TTFont` objects were
  unclosed, but that had no observable effect.

## The change

- **`pdf_translate/review.py`:** `NOTES.md` is read in a `with` block.
- **`tests/test_han_forms.py`:** `_subset` closes its face in a `finally`.
  `tests/test_shaping_probe.py::subset_to`, which had the same shape, uses a
  `with` block.
- **`pdf_translate/han_forms.py`** (`_instance`) and
  **`pdf_translate/prepare_font.py`** (the `--instance` path) open their
  `TTFont` in a `with` block, as the review asked. This is hygiene, as above.

**Records:** the quick-wins row in `docs/REQUESTS-from-product.md`. The
version goes from 74 to 75.

## Red, then green

`tests.test_pipeline.ResourceLeakTests` runs each library path with
`ResourceWarning` shown every time and a `gc.collect()`, and requires none:
- `test_review_closes_the_notes_file` fails on v74 with the `NOTES.md`
  handle, and passes now;
- `test_han_forms_closes_the_face_it_instances` and
  `test_prepare_font_closes_the_face_it_instances` pass on both trees, for
  the reason above. They guard the `with` blocks against a later lazy open,
  and their docstring says so.

The touched modules (`test_han_forms`, `test_review`, `test_shaping_probe`
and the new class) give 125 tests, all passing.

## Suite

These are CI's commands, run on macOS on `5fcc191`:

| step | result | ResourceWarnings |
|---|---|---:|
| suite | 748 tests: 1 failure, 1 expected failure | **0** (v74: 45) |
| canary | 15, OK | 0 |
| repository | 6, OK | 0 |
| eval fixtures | exit 0 | 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- No independent pass ran: this is resource handling, not rendering,
  shaping, fonts or layout. The warning count is the observable outcome.
