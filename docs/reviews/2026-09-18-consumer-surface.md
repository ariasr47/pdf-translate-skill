# E3 — the consumer surface — evidence

Branch `feat/consumer-surface`, stacked on `feat/terminology-loop` (v57). Plan:
`docs/plans/2026-09-18-e3-consumer-surface.md`. Design: `docs/design/E3-consumer-surface/`
(eight artboards). Version 57 → 58.

> The plan says to branch off `main` after row 32 has merged. Row 32 is built but unpushed — merging
> is the operator's — so this stacks on it instead. Same content, same order; nothing about what
> gets built changes. Ruling 1 anticipated exactly this ("If row 32 has not landed when this starts,
> Task 1 adds the foundation instead"), except that row 32 *has* landed on the branch below, so the
> logger foundation and the first compliant stage are already here.

## 1. The design finding that decides the shape

The obvious reading of C1 — "every stage callable without the CLI, nothing printed" — is to silence
the stage functions. Measured, that is wrong. `tests/test_pipeline.py` holds **177**
`redirect_stdout` blocks, and **128 of them wrap a library function directly**:

| call captured | blocks |
| --- | --- |
| `verify.verify(` | 64 |
| `retypeset.retypeset(` | 55 |
| `prepare_font.prepare_font(` | 5 |
| `field_fonts.field_fonts(` | 2 |
| `strip_text.strip_text(` | 1 |
| `pipeline.propose_merges(` | 1 |

Only about 41 wrap a `main()`. Silencing the stage functions breaks every one of those assertions
and every caller written against today's shape.

So E3 **finishes a pattern the repository already has twice** — `verify`/`run_verify` and
`qa_check`/`run_qa` — rather than inventing one. Each stage gains a silent `run_*` twin returning a
result and raising typed exceptions; the bare name keeps its exact signature, its exact printed
bytes and its exact return code, as a thin loud wrapper.

The cost is two entry points per stage, forever. It is recorded in `docs/DECISIONS.md` with its
reversal condition. The alternative cost was the contract.

## 2. The three rulings

Settled by the operator on 2026-09-18 against `docs/design/E3-consumer-surface/DecideFirst.dc.html`.

1. **Row 32 ships first and builds to this surface.** Its `review.py` is already silent, already
   returns a schema-versioned verdict, and `pipeline.py` already has the logger and a re-entrant
   `_console()`. E3 inherits one compliant stage instead of reworking one.
2. **`scale_report.json` breaks in E3.** Its bare-list top level becomes
   `{"schema": 1, "version": …, "runs": [...]}` — cheapest now, before the product pins a version
   and builds goldens on the current shape.
3. **C7 is not in this epic.** Determinism moved to E8. No `timestamp=` parameter here, and
   `apply_document_metadata` is not touched. The probe has since run
   (`docs/BRIEF-determinism.md`) and confirmed the sizing: C7 is a `doc_id=` parameter and a test.

## 3. Task 1 — the result family and the exception family

`pdf_translate/results.py`, `tests/test_results.py`. 13 tests.

- `PdfTranslateError` carries `console_line` and `exit_code`. That is the whole mechanism keeping
  the eleven CLIs byte-identical: the loud wrapper catches, logs the line it would have printed, and
  returns the code it would have returned. `console_line` is settable separately from the message,
  because what a function printed is not always what a service should be told.
- `WidgetTextError`, `MappingError`, `GlyphError`, `PlacementError`, `FontError`. Each carries
  structured attributes and a `details()` a service renders without parsing English —
  `GlyphError(page=3, char='请').page == 3`.
- `WidgetTextError` **moved home, not name**: it is defined in `results.py` and re-exported from
  `strip_text.py`, so everything that catches `strip_text.WidgetTextError` today keeps working.
  Pinned by `test_widget_text_error_is_still_importable_from_strip_text`, which was the one red in
  this task.
- `StripResult`, `ExtractResult`, `FontResult`, `RetypesetResult`, `FieldFontsResult`, all frozen,
  all tuple-valued, all with `to_dict()` carrying `schema` and `version` — mirroring
  `VerifyVerdict.to_dict()` (`verify.py:322`), deferred import and all.
- `RetypesetResult.output` is `None` on a cancelled run, not `''`. A cancelled run has no file, and
  there is one `ez_save` at the end of `retypeset`, so the absence is by construction rather than by
  cleanup.

```
Ran 13 tests in 0.001s       (tests/test_results.py)
OK
Ran 32 tests in 6.079s       (with tests/test_import_surface.py — the re-export holds)
OK
```

## Review

_(the whole-branch reviewer's verdict goes here)_
