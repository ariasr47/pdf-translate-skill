# R-06: text handed to the Story engine lands as written — 24 September 2026

**Assignment.** R-06 is the second of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-06 in
`docs/REVIEW-2026-09-24.md`: text between inline tags is escaped.

R-06 changes what is drawn, so its bar is the shared one plus Rule 1 with
a rendered pixel comparison. It ships with R-05 on the same branch, in v66.

## The defect

A single-line target that carries `<b>`, `<i>`, `<em>` or `<strong>` is
drawn through MuPDF's Story engine. `retypeset` queued the line for
`insert_htmlbox` exactly as authored. So anything else HTML-like on the
line was read as HTML:
- `<usuario@ejemplo.com>` vanished, parsed as an unknown tag;
- `&copy;` became ©;
- `<span>` was swallowed.

This contradicts `references/translations-format.md`, which says only the
four tags count as markup. Verify with the mapping fails the line as
"missing translation targets", without naming a cause.

**Found while fixing it: escaping once is not enough.** MuPDF 1.28.2's
Story engine decodes character references twice. A bare `pymupdf.Story`
draws `&amp;copy;` as ©, `&#38;copy;` as ©, and `&amp;amp;` as &. So the two
places that were already escaped once had the same defect:
- a **notice's text**: a notice containing `Aviso &copy; 2026` drew
  `Aviso © 2026`;
- a **shaped run** (Arabic, Indic and the rest). No shaped-script face in
  the test set has Latin letters, so its glyph check refuses such a string
  before it reaches the engine.

## The change

In `pdf_translate/retypeset.py`, `story_text(text)` escapes `&` twice and
`<` and `>` once. It is used:
- by `inline_markup_html`, for the text between the four inline tags, which
  stay markup;
- by `place_shaped`;
- by the notice body, in both the plain and the `bold_lead` form.

A merge's `html` is authored HTML and is not touched.

`references/translations-format.md` now says what lands as written. A
`docs/DECISIONS.md` row records the escaping rule and what would reverse
it, and the quick-wins row in `docs/REQUESTS-from-product.md` records the
build.

## Red, then green

These tests are in `tests.test_pipeline.AlignmentAndFontRoleTests`:
- `test_text_between_inline_tags_lands_as_written`: the target is
  `Escriba a <usuario@ejemplo.com> sobre el <b>aviso</b> &copy; <span>`. It
  must come out as that text without the `<b>` tags, with no ©, and pass
  verify with the mapping.
- `test_story_text_lands_as_written`: 11 strings rendered through a bare
  Story must come back verbatim. They include `&copy;`, `&amp;`, `&#169;`,
  `&lt;b&gt;`, `&nbsp;`, `R&D`, `a < b > c` and `<span>`. This pins
  MuPDF's double decoding: an engine that decodes once fails here instead
  of drawing `&amp;`.
- `test_notice_text_lands_as_written`: a notice with
  `Aviso &copy; 2026 <www.ejemplo.org> R&D`.

**Red.** Against the committed code without R-06 (`cbc8ba4`), from a
`git archive` with these tests copied in, 2 tests failed and 11 subtests
errored (exit 1):
- the inline line read `Escriba a sobre el aviso ©`;
- the notice read `Aviso © 2026 <www.ejemplo.org> R&D`;
- `story_text` did not exist yet.

**Green.** All pass. So do the related inline, notice and shaped tests: 34
in all.

## Suite

CI's 22 modules on this branch, on macOS, ran 729 tests. There was 1
failure and 1 expected failure, with no errors or skips.
- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.

## Rule 1

An independent pass on a different model (Sonnet) worked from `git archive`
copies of `bf9165c` and `cbc8ba4`, with its own fixtures. Verdict: PASS.
- **The double decoding is confirmed** with a bare `pymupdf.Story`, no
  library code: `&amp;copy;` and `&#38;copy;` draw ©, and `&amp;amp;amp;`
  draws `&amp;`.
- **Inline lines.** It used distinct bold and italic faces and a line
  mixing an address, `&copy;`, `&amp;`, `&#169;`, `&lt;b&gt;`, `a < b > c`,
  `R&D`, `<span>` and `&nbsp;` with `<b>` and `<i>` runs.
  - The branch draws that line verbatim, minus the tags, with the bold and
    italic runs in NotoSans-Bold and NotoSans-Italic. Verify with the
    mapping passes.
  - `main` dropped the address and `<span>`, drew © twice and a real NBSP,
    and verify failed with missing targets and a non-canonical text layer.
- **Notices**, plain and with `bold_lead`: verbatim on the branch. `main`
  drew ©.
- **Shaped runs.**
  - Noto Naskh Arabic and Noto Sans Devanagari have no `&`, so both trees
    refuse such a target identically on glyphs.
  - A Devanagari target with `<` is verbatim on both.
  - Called directly with a face that has `&`, `main`'s `place_shaped` never
    drew the glyphs "copy;" of `&copy; test`; the branch draws all 11.
- **Pixels, at 144 dpi.** Ordinary content with no `&`, `<` or `>` renders
  byte-identical on both trees: 0 differing bytes for an inline line, a
  notice and a shaped run. With the special characters the renders differ
  by 28,125 and 15,258 bytes. Crops show the difference is exactly the
  corrected text.
- **Merges.** A merge's authored `html` renders pixel-identical and extracts
  the same text on both trees.
- **Tests.** The three new tests fail on `cbc8ba4` (2 failures and 11
  errors) and pass on the branch. The new tree's `test_pipeline` fails only
  the known macOS `HotLoopTests` case.

**Note (minor): an oracle for later tests.** `place_shaped` wraps its run in
`/ActualText` with the raw text. So `page.get_text()` reports the intended
string even when glyphs are missing: on `main` it returned `&copy; test`
while the drawn spans were only `&` and ` test`. A shaped-run test must
read `get_text('dict')` spans. The new tests do not rely on the text mode
for shaped runs; the round-trip test uses a bare Story.
