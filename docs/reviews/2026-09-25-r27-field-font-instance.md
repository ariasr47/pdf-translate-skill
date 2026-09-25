# R-27: `field_fonts` embeds a variable face as its Regular instance — 25 September 2026

**Assignment.** R-27 is the fourth of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-27 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads
"`field_fonts` refuses a variable face (or instances it)".

R-27 is a font item, so its bar is the shared one plus Rule 1 with a
rendered comparison. It ships as v68, stacked on #36.

## The defect

`field_fonts` embeds a full-coverage face for what users type into a form.
Given a variable face, it embedded the face as it was. A PDF viewer draws a
variable font's default outlines. Noto Sans JP's default is wght 100, so
typed text came out Thin. The variation tables also carried megabytes that
nothing uses. `prepare_font`'s docstring suggested passing the field font
"as-is".

Measured here, on a 1,074 B form with one text field, using Noto Sans JP's
variable face (9.6 MB; one axis, `wght` 100–900, default 100):

| face passed | output | embedded face |
|---|---:|---|
| the variable face (before) | 5,904,493 B | variable, default outlines = Thin |
| a static wght 400 instance | 3,365,385 B | Regular |

## The choice: instance, not refuse

The assignment allowed either. This change instances the face:
- A variable face given for field input has one obviously right reading:
  its Regular instance. That is what a form field wants.
- A refusal would add a new refusal kind to a stage the app may call.
- The cost is time, about 5 s per call for the full JP face, paid only when
  a variable face is passed. A service can avoid it by passing a static
  face it made once. `references/fonts.md` says so.

## The change

`pdf_translate/field_fonts.py`:
- `static_face()` returns a static face untouched. Otherwise it pins every
  axis to the face's "Regular" named instance. A face with no such instance
  keeps its axis defaults, with `wght` set to 400 within the axis's range.
- It renames the result with `prepare_font.name_static_instance`, so the
  embedded name says Regular, not Thin.
- It writes the result to `<out>.tmp_static.ttf`, which is removed after
  embedding.
- `run_field_fonts` embeds that face and logs the pins.
  `FieldFontsResult.instance` records them, for example `wght=400`, or `''`
  for a static face. The field is additive.

`pdf_translate/prepare_font.py`: the name-table fix-up for an instanced face
moves into `name_static_instance`, with unchanged behaviour.

**Docs:**
- `references/fonts.md`, the field-input paragraph;
- `field_fonts`' docstring;
- `references/consumer-guide.md`, the result table.

**Records:** a `docs/DECISIONS.md` row, and the quick-wins row in
`docs/REQUESTS-from-product.md`. The version goes from 67 to 68.

## Red, then green

`tests.test_pipeline.VariableFieldFontTests` works on Noto Sans JP's
variable face cut down to a few glyphs. The cut keeps `fvar` and `gvar`, so
it is still variable, and instancing it takes milliseconds.
- A variable face must be embedded with no `fvar`. Its 山 outline must
  match a wght 400 instance and differ from the default (Thin) outline. Its
  subfamily must be Regular, `result.instance` must be `wght=400`, and no
  temporary file may be left.
- A static face must be embedded as it is: the same PostScript name and
  glyph count, and `instance == ''`.

**Red.** On the unfixed code, the variable face's embedded program still had
`fvar`. The static test failed only on the new `instance` field, because
static embedding is meant to stay unchanged. **Green.** Both pass, with the
field-font guards, `test_results` and `test_consumer_contract`: 41 tests.

**With the full face:** `run_field_fonts` on the 9.6 MB variable face took
5.2 s. It gave 3,365,399 B, a Regular face with no `fvar` or `gvar`, and no
leftover files. That is within 15 B of the static instance's output.

## Suite

CI's 22 modules on this branch, on macOS, ran 732 tests. There was 1
failure and 1 expected failure, with no errors or skips.
- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- The canary, binary integrity and the eval fixtures passed.

**The app's route.** The app's session checked on 25 September.
- It calls no `field_fonts` or `prepare_font` today.
- The one Japanese face it would pass is a static Regular instance, made
  once at build time with no `fvar` or `gvar`.
- So the instancing cost would not apply, and `instance` would read `''`.

## Rule 1

An independent pass on a different model (Sonnet) worked from `git archive`
copies of `9ba9875` and `43ec91c`, with its own forms and fonts. Verdict:
PASS with one major finding, now fixed.

**What held:**
- **The embedded face**, on a form with a text field and a combo box.
  - On the branch: 3,365,928 B, no `fvar` or `gvar`, `usWeightClass` 400,
    named Noto Sans JP Regular, and 山's outline exactly equal to an
    independent wght 400 instance.
  - On v67: 5,905,022 B, variable, `usWeightClass` 100, still named Thin,
    and the default (Thin) outline.
- **Rendered.** Glyphs were drawn with the embedded field face and rendered
  at 144 dpi.
  - The branch's render from the variable face is byte-identical to v67's
    render from a separately made static wght 400 face: 1,105 dark pixels
    each.
  - v67 from the variable face draws Thin: 481 dark pixels.
  - PyMuPDF's `Widget.update()` resets a filled field's `/DA` to Helv, so
    the verifier drew with the embedded face directly rather than through a
    filled field.
- **Other variable faces.** Each was pinned with no `fvar` left, no crash
  and no leftovers:
  - Noto Sans SC gave `wght=400`;
  - Skia, a system face with two axes and a Regular instance, gave
    `wdth=1,wght=1`;
  - STIX Two Text Italic, with no Regular instance, clamped to `wght=400`.
- **A static face** (Noto Sans) gives a byte-identical output PDF, embedded
  program and render on both trees, with `instance` `''`.
- **`prepare_font --instance wght=400`** is unchanged: 17 of 18 font tables
  are byte-identical. The one that differs is `head.modified`, the
  timestamp of when each tree ran.
- The new tests pass on the branch, and the variable-face test fails on v67
  for the `fvar` reason.

**The finding (major): a temp file left behind.** `static_face()` wrote
`<out>.tmp_static.ttf` before the input PDF was opened, outside the
`try`/`finally` that removes it. So a missing or corrupt input with a
variable face left a 5.8 MB file beside the output; v67 left nothing.
- Now the whole call, from the pinned copy's creation on, sits inside one
  `try`/`finally` that removes the copy.
- `test_a_failed_call_leaves_no_temporary_face` fails on the reviewed commit
  (`['out.pdf.tmp_static.ttf']`) and passes now.
- `test_pipeline` and the consumer contract: 290 tests, with only the known
  macOS `HotLoopTests` failure.
