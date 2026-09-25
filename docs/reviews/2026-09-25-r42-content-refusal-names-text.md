# R-42: a typography content refusal names the text it is about — 25 September 2026

**Assignment.** R-42 is the next of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-42 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads "a typography
preflight refusal names the offending text".

R-42 changes what a refusal reports, not what is drawn. Its bar is the
shared one. Two independent passes ran anyway, because the code it changes
is shared with typography verify. It ships as v72, on `beb4c06`, the head of
#41 (R-40, v71), which merged into `main` as `62e87bf`.

## The defect

Before placing anything, a typography-1 build checks the source's content
streams (`typography_content.inspect_content`). Text that is sheared,
clipped, transparent or painted over cannot be attested, so the build
refuses it with `unsupported-typography-construct`.

The refusal has to say which occurrence it is about. It took the page's
**first** segment, whatever text was at fault
(`next(s for s in segments if s['page'] == issue.page)`). The check itself
kept only the page, not where the text was.

**The app's route.** The app's session checked on 25 September. The app
has not adopted typography-1, and it reads no `refusals` dictionary at all:
its v54 pin has none. So v72 changes nothing there.

## Reproduced before building

**Constructed.** On the typography fixture page, the lines are s0 at y 60
and s1 at y 120:
- a white rectangle painted over s1 was refused as s0;
- a third, sheared line ("Slanted words") was refused with `source_text`
  "Pay NOW", which is s0's;
- a `UserUnit` of 2, a whole-page construct, was also refused as s0.

**Wild.** On the 17 wild PDFs, `inspect_content(source=True)` finds 366
issues:

| kind | count |
|---|---:|
| clipped | 203 |
| transformed | 83 |
| occluded | 75 |
| unsupported paint | 5 |

Each form's typography extraction was attributed with the new rule. For
**235** of the 366, the offending text is in a different segment from the
page's first one. So v71's refusal would have named the wrong line.

## The change

`pdf_translate/typography_content.py`:
- **`ContentIssue` gains `at`:** where the first offending text starts, in
  the extraction's page space (unrotated, top-left, CropBox-relative). It
  is `None` for a whole-page issue. It is declared `compare=False`, so an
  issue's identity, the one-issue-per-page-and-kind deduplication, and
  therefore verify's findings are all unchanged.
- **The content-stream walker tracks the text-line matrix** through `BT`,
  `Tm`, `Td`, `TD`, `T*`, `TL`, `'` and `"`. The shear and clip checks read
  only the linear part, which these operators never change. A malformed one
  marks the position unknown, and nothing else.
- **The position** of a text-showing operator is
  `(e − CropBox.x0, CropBox.y1 − f)`. PyMuPDF's `transformation_matrix` was
  tested and is wrong on a rotated page with a CropBox offset, so it is not
  used.
- **A covered glyph** gives the centre of its box from MuPDF's text trace.
  That trace is already in the segments' space at every rotation and crop
  tested.

`pdf_translate/retypeset.py`: `_content_segment` names the smallest segment
on the page whose box, widened by 1 pt, holds `at`. A whole-page issue, or
text no segment holds, names only the page: `occurrence_id` and
`source_text` are then `None`, and `page` is set.

**Docs:** `references/typography.md`, under "What refuses", says what the
refusal names.

**Records:** a `docs/DECISIONS.md` row, and the quick-wins row in
`docs/REQUESTS-from-product.md`. The version goes from 71 to 72.

## Red, then green

`tests.test_typography_retypeset` has three new tests:
- `test_a_content_refusal_names_the_occurrence_it_is_about`: a rectangle
  over s1 must be refused as s1;
- `test_a_sheared_line_is_named_not_the_first_line`: the sheared third line
  must be named, with its own text;
- `test_a_page_level_content_refusal_names_the_page_and_no_occurrence`:
  `UserUnit` must give page 0 with no occurrence.

**Red.** On `beb4c06` (v71), all three name s0. **Green.** All three pass.
The typography modules (retypeset, verify, acceptance and pipeline) give 71
tests, all passing.

**The wild PDFs on v72:**
- The issues are identical to v71's in page, kind and detail, all 366 of
  them.
- Every issue carries a position.
- 363 name a segment.
- 3 name only the page: `uscis-i9`'s transparent text at points no
  extracted segment covers.

Spot checks name the offending text: the scaled "Form 1040-ES" title, the
clipped "TIP" box on the 1040-ES, the "CAUTION" on the W-4 and "Date of
Birth" on the N-400.

## Suite

These are CI's commands, run on macOS on `d4b0c24`:

| step | result |
|---|---|
| suite | 743 tests: 1 failure, 1 expected failure |
| canary | 15, OK |
| repository | 6, OK |
| eval fixtures | exit 0 |

- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- After the CropBox fix below (`85eb0d7`), the same run gave 744 tests with
  the same outcome. The canary, repository tests and fixtures still pass.

## Independent verification

Two independent passes on a different model (Sonnet) worked in parallel
from `git archive` copies of `beb4c06` (v71) and `d4b0c24` (v72), each with
its own inputs.

**Is the named occurrence the offending text? PASS.**
- **Seven constructed sources,** each with exactly one offending line that
  is not the page's first. They cover every kind:
  - occluded;
  - rotated and sheared;
  - clipped with `W n`;
  - opacity below 1, and stroke mode.

  The lines were placed with `Td`, `TD`, `T*`, `'` and `Tm`, on a page
  with a CropBox offset and on a second page, plus a `UserUnit` page. In
  all seven, v71 names the page's first occurrence and v72 names the
  offending one, or only the page for `UserUnit`.
- **17 wild issues checked against its own content-stream walker,** written
  separately. It found the text operator at the recorded position every
  time (distance 0.0000), with the clip, matrix or paint state that made it
  an issue. Occlusions were checked on rendered crops. It judged all 17
  right.
- **The 3 page-only issues on `uscis-i9`** are invisible text (render
  mode 3). Extraction leaves it out, so naming only the page is correct.
- **Tests.** With the new tests copied into v71, exactly the three new
  tests fail; on v72 all pass.

**Did anything else change? PASS, with one major finding, now fixed.**
- **Unchanged:**
  - typography verify's full gate list on four jobs: clean, `field_fonts`,
    later paint and sheared;
  - `inspect_content`'s issues and drawn fonts on every wild PDF, sampling
    the two long booklets;
  - the `elif`-to-`if` change for `'` and `"`;
  - issue deduplication with `at` excluded;
  - `any()` becoming `next()` in the occlusion check.
- **The finding (major).** The new crop read took four numbers from
  `/CropBox` and caught no `IndexError`. So a `/CropBox` of fewer than four
  numbers crashed `inspect_content`, and with it the retypeset preflight
  and typography verify. v71 never read the box, and ran normally on the
  same file.
  - `_crop_box` now returns `None` for anything but four finite numbers,
    and the offending text is then unplaced.
  - `test_a_malformed_crop_box_leaves_the_position_unknown` covers
    `[0 0 100]`, `[]` and `[0 0 /A 100]`. It failed on `d4b0c24` for the
    first two and passes now.
  - The 15 faster wild PDFs give the same 104 issues, with the same
    positions, as before this fix.
