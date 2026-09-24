# Item 3: a `/Rotate` page rebuilds where its source is, with R-64 — 24 September 2026

**Assignment.** The product ranked this priority 3 of the review
assignment: the `/Rotate 90` blank page, diagnosed first, with R-64. The
request of record is the app's `REQUEST-to-skill-review-2026-09-24`; the rule
behind it is `docs/DECISIONS.md`, 2026-09-24, and the findings are the E12
measurement's blank page and R-64 in `docs/REVIEW-2026-09-24.md`. The
product's acceptance criteria are:
- a test that fails on the unfixed code with a one-defect PDF and passes
  after the fix;
- Rule 1 with a rendered pixel comparison;
- a version bump, and a notice to the app;
- for R-64, a corpus test that builds each `translate` fixture's output and
  checks it, so this class of defect cannot pass CI again.

## The defect

On 2 September (`c297ac2`, v17), extract began reading text through an
annotation-free display list, so that widget values stay out of
`to_translate.json`. Its helper was documented as "same shape as
`get_text('dict')`", and six minutes later `failure-modes.md` §13 said
"`/Rotate` is harmless — origins come back in unrotated space".

A display list, though, reports what a viewer shows. On a `/Rotate` page,
segment origin, bbox and direction came back in the rotated space. Retypeset
draws with `TextWriter`, `insert_htmlbox` and the Story engine in the
unrotated page space. Widget rects, `get_drawings`, `get_text` and every
verify reader are also unrotated.

On `corpus/rotated.pdf` (MediaBox 612 × 792, `/Rotate 90`):
- the source draws `1 0 0 1 60 712 Tm`;
- `segments.json` said origin (712, 60), direction (0, 1);
- the output drew `1 0 0 1 712 552 Tm`, off the 612-wide page, so the page
  was blank.

## Measured before building

This covers every site in extract, retypeset and verify that produces or
consumes a page coordinate, and which space each one uses. It also covers
an end-to-end run on one constructed page saved at `/Rotate` 0, 90, 180
and 270. The content stream is identical in all four files; only `/Rotate`
differs. The page has 13 translated runs: plain labels, a label at the
right edge, a label beside a field, two merges, an override, two
right-aligned amounts, a dot leader and a side label.

**Shipped v63 placed 0 of 13 runs where the source had them on any
rotated page:**
- **90:** runs went off the page. Verify FAILed on ink and missing targets.
- **270:** most runs were visible but turned or upside down. Verify FAILed
  on one run only.
- **180:** every run was point-reflected onto the opposite corner, and
  retypeset and verify both exited 0. For example, a field's label was
  drawn at the far side of the page from its field.

**Other findings:**
- **Legacy verify reads no coordinate from `segments.json`.** Scrambling
  every origin, bbox and direction leaves its verdicts byte-identical. It
  catches a misplaced run only when the run leaves the page.
- **Horizontal-only features silently dropped.** On a rotated page every
  run took the rotated-run path, which drops dot leaders, draws inline
  markup literally and refuses shaped targets.
- **Extract warnings lost.** merge-candidate, narrow-column and
  right-aligned disappeared on rotated pages; right-aligned also compared
  rotated segment boxes with unrotated obstacles.
- **The mirror moved links.** Its link round trip moved links on a rotated
  page even without a flip: `get_links` reports the rotated view and
  `insert_link` reads unrotated.

**Three fix locations were weighed:**
1. **Convert at load, in retypeset.** An override's `x` on a line that is
   vertical on screen is an across-line coordinate, so it cannot be
   converted: the override parts overlapped.
2. **Make the rotated view canonical.** Every drawing call and every verify
   reader would need converting.
3. **Record `segments.json` in the unrotated space.** This one restores the
   documented contract.

An in-memory prototype of option 3, plus an unrotated page frame for width
budgets, placed 13 of 13 at every rotation, identical to the control, with
retypeset and verify at 0. The wild corpus has 0 rotated pages in 449.

## The change

**`pdf_translate/strip_text.py`:**
- `page_textdict_without_annots` and `page_rawdict_without_annots` map every
  block, line, span and character box and origin, and each line direction,
  through `page.derotation_matrix`.
- The result equals `page.get_text('dict'/'rawdict')`. The document is not
  modified.
- At rotation 0 nothing is mapped.

**`pdf_translate/extract_segments.py`:** `segments.json` gains
`"geometry": {"space": "unrotated", "rotated_pages": {"<page>": {"rotation",
"width", "height"}}}`. The key is additive, and the typography
`extraction_id` does not cover it.

**`pdf_translate/retypeset.py`:**
- **`unrotated_frame(page)`** is `page.rect * page.derotation_matrix`. It
  replaces `page.rect` everywhere the legacy path measures a width budget
  or a mirror pivot: `_right_limit`, `direction_limit` (which now takes the
  frame, not a page), the shaped override's room, and every mirror flip.
- **The mirror** maps a link's rect back to unrotated before flipping and
  re-inserting it.
- **Stale extraction.** A `segments.json` without the space marker is
  refused on a rotated page that carries segments, with a stable line,
  documented in `failure-modes.md` §13 so a consumer may match it:
  `FAIL: stale extraction: segments.json names no geometry space and N rotated page(s) carry segments (pP /Rotate R, …); it was extracted before v64 in the rotated space: run extract again.`
  On an unrotated page the two spaces agree, so a file without the marker
  still builds.
- **Unchanged:** `TextWriter(page.rect)`, and the typography path, which
  still refuses rotated pages.

**Docs:**
- `references/failure-modes.md` §13: the regression, the fix, the refusal
  and the landscape limit;
- `references/retypeset.md`, Rotated lines;
- `references/translations-format.md`, Coordinates, with the recipe for a
  point read off a render;
- `references/consumer-guide.md`, the `segments.json` row.

**Records:** `docs/DECISIONS.md`, and in `docs/REQUESTS-from-product.md`
item 3's status plus five proposals. The version goes from 63 to 64.

**Known limit, not a regression: landscape pages**, whose content is
counter-rotated so it reads upright under `/Rotate`.
- Their text is vertical in PDF space, so every run takes the rotated-run
  path.
- Rule 1's own landscape fixture had 12 runs: 8 plain, a dot leader, a
  `right`, a `center` and an override `x`. v64 put all 12 at their source
  origin with the source direction; v63 put none there.
- `right`, `center` and leader filling do nothing on that path. The
  prototype's stricter count, which also required those features, was 6 of
  12.
- The product filed a reading-frame layout as a proposal, not assigned.

## Red, then green

**`tests.test_pipeline.PageRotationTests`** draws one layout once and saves
it at `/Rotate` 0, 90, 180 and 270 (`build_page_rotation_pdf`). The page
carries a title, an edge label that must shrink, a label beside a field, a
merge, an inner-gap override, two `right` amounts against a rule, a dot
leader with a tail, a target with inline bold, a side label, and a link.
The tests check:
- the annotation-free dict and rawdict equal `get_text`, and widget values
  stay out on a rotated page;
- `corpus/rotated.pdf` extracts at (60, 80), (60, 110) and (60, 130),
  reading +x, with the `geometry` key;
- segments and warnings are identical at every rotation;
- one mapping, authored once from `segments.json`, rebuilds every rotation
  with verify at 0, and every drawn run (text, origin, direction, size) and
  every annotation rect equal the `/Rotate 0` control's;
- the same holds with `mirror`, with the link flipped about the unrotated
  width;
- the stale-extraction refusal, and its line marking a page list it cuts short;
- the unrotated frame and `direction_limit`.

**`tests.test_corpus_verdicts`**, R-64:
- `test_every_translate_fixture_rebuilds_in_place` rebuilds all 13
  `translate` fixtures with an identity mapping. It requires that no FAIL
  other than untranslated running text appears, which an identity mapping
  raises by design, and that every run starts within 1.5 pt of its segment.
- `test_right_to_left_source_runs_start_where_the_source_did` is an
  expected failure; see Found here.

**Red.** Against `main` (`0819091`, v63), run from a `git archive` with
these tests copied in, `python -m unittest tests.test_pipeline.PageRotationTests
tests.test_pipeline.RotatedTextTests tests.test_corpus_verdicts` gave 14
failures and 4 errors (exit 1). Without `RotatedTextTests` it gives 3
errors, as the Rule 1 review found; the fourth is
`test_unit_direction_helpers`, which now passes a frame.
- the dicts differ from `get_text` at 90, 180 and 270;
- `rotated.pdf` extracts at (712, 60), reading (0, 1);
- extraction differs from the control at 90, 180 and 270;
- rebuilds differ from the control at 90, 180 and 270:
  - at 90 and 270 a run is refused below the 0.7× floor;
  - at 180, with this fixture, verify finds 2 missing targets only because
    the inline bold was drawn as literal tags;
- the mirror differs at 90, 180 and 270;
- R-64 fails on `rotated.pdf` with `FAIL page 1 ink ratio: 0.00` and
  `FAIL missing translation targets (3)`;
- the errors are the new `geometry` key and the new frame API.

Every `/Rotate 0` control passed on `main`. **Green:** all pass on this
branch, with the one expected failure.

## Suite, probe and Rule 1

**Suite.** CI's 22 modules on this branch, on macOS, ran 714 tests. There
was 1 failure and 1 expected failure, with no errors or skips.
- The failure is the macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  the same on every branch.
- The first run also failed
  `test_typography_extract.test_default_extraction_retains_legacy_shapes`,
  which pins `segments.json`'s top-level keys. It now includes `geometry`,
  and that module passes.
- The other CI steps passed: the canary, binary integrity and the eval
  fixtures.

After Rule 1, the stale-extraction line marks a page list it cuts short
(below), and `PageRotationTests` passes (9 tests).

**The wild probe.** It ran into a scratch directory and exited 0 on all 17
files. Against the tracked `dev/wild/results.json` it gives 0 differences
in 1,104 compared values, with only timings left out. The wild corpus has no
rotated page, and this change leaves rotation 0 alone.

**Rule 1.** Three independent passes on a different model (Sonnet), each
working from `git archive` copies of `d30ecde` and of `0819091`, with its
own fixtures and scripts.
- **Reproduce and pixels: PASS.**
  - On `corpus/rotated.pdf`, v63 renders a blank page (ink 0.00, 3 missing
    targets). v64 extracts at (60, 80) reading +x, and the ink ratio passes
    at 0.88.
  - Its own 8-feature page was saved at each rotation. Only `/Rotate`
    differs, so the render of an output at R must equal the `/Rotate 0`
    output's render turned by R; the renders of the sources were checked
    first, with 0 pixels different.
  - At 90, 180 and 270, v63 differs from the turned control by 7,142, 9,351
    and 8,531 pixels (channel delta > 32). At 180, verify passed on v63.
    v64 differs by 0 pixels at every rotation, and by 0 with `mirror`.
  - The output spans on v64 equal the control's with a maximum delta of
    0.0000.
- **Break it: PASS, two minor findings.** v64 holds on:
  - a `/Rotate` inherited from `/Pages`, and `/Rotate` -90 and 450;
  - a MediaBox off the origin with a smaller CropBox, at every rotation;
  - `--pages` subsets of a mixed 0/90/270 document, where
    `rotated_pages` lists exactly the rotated pages extracted;
  - list-marker `body_dx`, the same at every rotation;
  - an in-page rotated line on a rotated page;
  - `mirror` with a widget and a link, where the raw `/Rect`s equal the
    control's.

  **The stale refusal** matches the documented line, and a `geometry`
  naming another space is refused too. **Wild corpus:** all 17
  `segments.json` are byte-identical to v63 apart from `geometry`.
  Identity rebuilds of 5 wild forms render pixel-identical to v63 on all
  37 pages; 5 more refuse identically on both, for glyph coverage.

  The findings:
  - The typography-1 placement budget still reads `page.rect`. It is
    unreachable, because typography-1 refuses rotated pages; it is added to
    that proposal.
  - The stale line cut its page list at 30 with no marker. It now ends in
    `…`, as documented, and a test pins it.
- **Code review: PASS, two minor findings.**
  - The dict and rawdict equal `get_text` at every rotation, including two
    fonts on one line and ligatures. The image-block mapping is correct
    when image blocks are requested; extract never requests them.
  - The link and widget round trips are exact.
  - The stale refusal is byte-for-byte the documented line, with exit 1,
    the refusal data, and no output.
  - The Coordinates recipe lands 2.5 pt from the segment origin, measured
    off a 144 dpi render's ink edge. The wrong matrices land 80 to 115 pt
    away.
  - The new tests fail on v63 for the rotation reasons and pass on v64.
    The right-to-left carve-out covers exactly `ar_source.pdf`'s 3
    misplaced runs.
  - On all 16 corpus fixtures, `segments.json` is identical to v63 except
    on `rotated.pdf`, which also regains the merge-candidate warning the
    rotated space had hidden.

  The findings: this section was still unfilled, and the red error count
  needed its command. Both are fixed here.

## Found here, not assigned

- **Right-to-left sources are rebuilt one source width to the right.**
  - MuPDF reports a right-to-left run's origin at its right end, and
    retypeset draws every run rightward from its origin.
  - On `corpus/ar_source.pdf` the title spans x 60.9–147.6 in the source
    and 140.6–239.9 after an identity rebuild. No gate reads positions.
  - It affects documents whose source is right-to-left, not right-to-left
    targets.
  - Proposed in `REQUESTS-from-product.md`, and pinned as an expected
    failure.
- **Span union.** It keeps the first span's left edge, so a multi-span line
  whose direction is not +x loses width. Proposed.
- **Typography-1 still reads the rotated `page.rect`**, in its placement
  budget and in typography verify. This is latent while typography-1
  refuses rotated pages. Proposed.
- **`python -m pdf_translate.retypeset` and `python -m pdf_translate.verify`
  print nothing.** Rule 1 found that `runpy` re-executes the already
  imported module as `__main__`, whose logger is not under
  `pdf_translate`. The exit code and the output are right, and
  `scripts/*.py` and `pipeline.py` print normally. The same happens on v63.
  Proposed.
- **A CropBox-versus-MediaBox offset of about 8 pt at rotation 0.** A Rule 1
  verifier noticed it on both v63 and v64 and did not investigate it. Not
  measured here; noted only.
