# R-47: typography verify reads page crops and field rects once — 25 September 2026

**Assignment.** R-47 is the fifth of the review's quick wins, priority 5 of
the assignment. The request of record is the app's
`REQUEST-to-skill-review-2026-09-24`. The finding is R-47 in
`docs/REVIEW-2026-09-24.md`, and the assigned behaviour reads "typography
verify reads page rects once".

R-47 changes a verify gate's cost, not its verdicts, so its bar is the
shared one plus the performance rule: the output must be identical. For a
verify gate the output is the verdict, so identical means the same gate
results, byte for byte, on both trees. It ships as v69, on `7a9d1a5`,
which is in `main` and has the same tree as `main` at `aa54158` (v68).

## The defect

Inside its per-glyph loop, `typography_verify.inspect_output` did two things
for every inked glyph:
- It loaded the page again to read its crop, with `output[target.page].rect`.
- It rebuilt a `Rect` for every source field in the document to test overlap.

After `field_fonts`, a delivered form carries `/NeedAppearances`, and each
page load then rebuilds that page's widget appearances and keeps them. So
the verify's memory grew with glyphs × widgets. The review measured the
documented final-form verify at 1,987 MB for the 3-page FL-100 and 4,101 MB
for the 14-page N-400.

## Reproduced before building

The wild FL-100 and N-400 cannot take a typography-1 mapping: 141 of
FL-100's runs name two ArialMT resources, which the mapping refuses. So
`dev/probes/r47_verify_page_loads.py` draws forms of the same size:
- base-14 Helvetica lines on the left and filled text fields on the right;
- an identity typography-1 mapping, Noto Sans prepared for it, a build, and
  `field_fonts`, which sets NeedAppearances.

| form | pages | widgets | lines | characters |
|---|---:|---:|---:|---:|
| FL-100-sized | 3 | 158 | 150 | 7,525 |
| N-400-sized | 14 | 440 | 840 | 42,139 |

The real FL-100 has 3 pages and 158 widgets, and the N-400 has 14 and 440.

**Measured.** One typography verify per process, with the probe's `measure`
on each tree:
- base: `main` at `aa54158` (v68), a `git archive` copy;
- branch: `118bb75` (v69).

Each form was built once, and both trees verified the same files.
`final.pdf` is after `field_fonts`, so it has NeedAppearances; `out.pdf` is
before it.

| form | PDF | page loads | peak RSS | time |
|---|---|---:|---:|---:|
| FL-100-sized | `final.pdf` | 6,737 → 115 | 1,381 → 116 MB | 7.08 → 3.23 s |
| FL-100-sized | `out.pdf` | 6,737 → 115 | 100 → 101 MB | 4.02 → 3.21 s |
| N-400-sized | `final.pdf` | 37,618 → 533 | 3,054 → 177 MB | 26.39 → 11.76 s |
| N-400-sized | `out.pdf` | 37,618 → 533 | 136 → 135 MB | 14.91 → 11.64 s |

- **Gate results are identical.** The typography gate PASSes on every run.
  Its digest is `140cf60fe5181fe2` for FL-100 and `3602a519fb13ad0e` for
  N-400 on both trees. The digest of every gate is also equal per form and
  PDF.
- **Exit code.** Every run exits 1 on both trees, because an identity
  mapping leaves the source text in place and the `leak-running` gate FAILs.
- **Peak RSS varies between runs.** An earlier run of the same measurement
  gave 1,449 → 113 MB and 3,572 → 167 MB. The page loads and digests were
  identical.
- **Without NeedAppearances**, memory was already flat. The time still
  falls, from the field Rects no longer rebuilt per glyph.
- The review's own numbers, 1,987 and 4,101 MB on the real forms, are of the
  same order. It does not record its method.

## The change

`pdf_translate/typography_verify.py`, before the occurrence loop:
- `crops` holds each output page's crop, padded by the tolerance, read once;
- `source_fields` holds each page's source fields as `(name, Rect)`, built
  once, in the extraction's order.

The per-glyph checks index them. The findings and their order are
unchanged. The mapping loader already validates every field rect
(`mapping.py:179-184`), so building them before the loop cannot raise where
the old in-loop build could. The font-id comprehension at `:197`, also per
glyph, is CPU-only and outside the assignment; it is left as it was.

**Records:** a `docs/DECISIONS.md` row, and the quick-wins row in
`docs/REQUESTS-from-product.md`. The version goes from 68 to 69.

## Red, then green

`tests.test_typography_verify.FilledFormPageLoadTests` builds two filled
forms that differ only in how many glyphs they draw (19 and 51). Each goes
through `field_fonts`, which sets NeedAppearances, and then verify. The
typography gate must PASS on both, and the final PDF's pages must be loaded
the same number of times for both.

**Red.** On `7a9d1a5` (v68), with this test file copied in: 34 loads for
the short form and 66 for the long one, one more per extra glyph.
**Green.** Equal on the branch.

Two findings this change touches had no test. Two characterization tests now
pin them, and they pass on both trees:
- `test_glyph_past_the_page_crop_is_a_failure`: a bold NOW drawn across the
  right edge FAILs with "glyph outline extends outside the page crop";
- `test_glyph_over_a_source_field_is_a_failure`: a NOW drawn over a source
  field FAILs with "glyph outline overlaps source field answer".

On `7a9d1a5` the module runs 29 tests, and only the page-load test fails.
On the branch all 29 pass.

## Suite

CI's 22 modules on this branch, on macOS, ran 734 tests. There was 1
failure and 1 expected failure, with no errors or skips.
- The failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`.
- The expected failure is item 3's right-to-left source pin.
- That run loaded the module before the two characterization tests were
  added. Run again afterwards, `test_typography_verify` and
  `test_verify_report` gave 60 tests, all passing.
- The canary (15), binary integrity (3) and the eval fixtures passed.

**The app's route** runs no library verify, and typography-1 is not
adopted. So v69 changes nothing there.

## Found in passing: widths rounded down in a 2,048-unit face

This was found while choosing a face for the measurement, and it is filed
as a proposal in `docs/REQUESTS-from-product.md`, not built.
- **The failure.** On an identity typography-1 build of the FL-100-sized
  form with Arial as the sans face, typography verify FAILed all 150 of 150 correct lines with "Run 0
  is not at its ordered, uniformly scaled position". The same job in Noto
  Sans PASSes.
- **The cause.** MuPDF writes each width to the embedded font's `/W` array
  in whole thousandths of an em, rounded down. Arial Regular's P is
  1366/2048 em, or 666.99 thousandths, and it is embedded as 666. All 20
  embedded widths equal the rounded-down value, and 9 of them differ from
  normal rounding.
- **How it grows.** Verify predicts positions from the font program's exact
  advances. So the drawn glyphs fall behind by about 0.005 pt each at 8 pt,
  and past the 0.05 pt tolerance within about 10–15 glyphs.
- **Why the tests missed it.** The typography-1 tests use only Noto faces,
  whose units-per-em is 1,000.

## Independent verification

The shared bar requires Rule 1 only for the drawing, font and layout items.
R-47 changes a verify gate, so an independent pass ran anyway. It used a
different model (Sonnet) on `git archive` copies of `aa54158` (v68) and
`118bb75` (v69), with its own inputs rather than the probe. Verdict: PASS,
with one minor note.

**What held:**
- **Gate results are byte-identical** on seven independently built
  typography-1 cases, and on a large form. The typography gate and the list
  of every gate were compared by digest, in separate processes. The cases:
  - a 3-page filled form through `field_fonts` (PASS);
  - a glyph past the crop on page 3 (FAIL, "extends outside the page crop");
  - a glyph over a source field on page 3 (FAIL, "overlaps source field
    answer2");
  - a field on page 1 with a glyph at the same coordinates on page 2. Only
    the expected "fields differ" finding fires, with no overlap finding, so
    fields are still filtered by page;
  - three overlapping fields inserted out of page order. The findings come
    in field order, the same on both trees;
  - a page whose CropBox is 20 pt smaller than its MediaBox on every side.
    typography-1 accepts it, and it PASSes;
  - an unresolved output font on page 3 (REVIEW).
- **Its own memory measurement.** A 10-page NeedAppearances form with 320
  widgets and 44,800 glyphs: 40,271 → 381 page loads, 2,563 → 152 MB peak
  RSS and 28.6 → 14.2 s. The typography gate PASSes on both trees, with
  700 occurrences checked, and the digests match.
- **Tests.** With the branch's test file copied into v68, 28 of 29 pass. The
  one failure is the page-load test, at 66 against 34. On the branch all 29
  pass, and `test_verify_report` (31) confirms v69 in all five places.
- **Scope.** Between the trees only `typography_verify.py`, the version
  files and the two test files differ.

**The note (minor): the Rect builds left the per-glyph `try`.** In v68 the
crop and field Rects were built inside the `try` whose `except` turns an
error into a REVIEW finding. In v69 they are built before the loop.
- **It cannot be reached today.** The mapping loader rejects a malformed
  field rect before `inspect_output` runs. The verifier corrupted one,
  recomputed the extraction ID, and both trees raised the same
  `MappingError: invalid field identity` at `mapping.py:184`. Every page's
  rect is also already read by `page_geometry` earlier in the same function.
- **Ruling: no change.** A guard for an unreachable path would be noise.
- **What would reverse it:** a change that lets an unvalidated field
  identity reach `inspect_output`.
