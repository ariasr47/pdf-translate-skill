# A multi-span line keeps its whole box — 26 September 2026

**Assignment.** This is the product's fourth item, advised on 26 September
and approved by Rodrigo; right-to-left, the third, was parked as out of
scope. It ships as v85, stacked on #58.

## The defect, reproduced

`extract_segments` merges the spans of one text line into a segment. The
merged box kept the first span's left edge: `g['bbox'][0]`. On a `+x` line
each span starts to the right of the last, so that edge is the line's. A
line that advances with a leftward component puts later spans to the
**left**, and the box dropped them.

The probe was a two-span line, "Signature of " in Helvetica then
"applicant" in Helvetica-Bold, drawn at 8 angles. It compared the segment
box with the union of the drawn glyph boxes on v84:

| angle | dir | box width | glyph width |
|---|---|---:|---:|
| 0, 45, 90, 270, 315 | +x or vertical | right | — |
| 135 | (−0.71, −0.71) | 54.8 | 88.9 |
| 180 | (−1, 0) | 62.4 | 110.7 |
| 225 | (−0.71, 0.71) | 54.8 | 89.0 |

Since item 3 (v64), a `/Rotate` page is extracted in its unrotated space.
So the defect now needs a line that is not horizontal in PDF space itself.

## The fix

For a line whose direction is not `+x`, the box's left edge is the leftmost
of its spans' left edges. A `+x` line keeps the old expression, so its
output cannot change. One statement in `pdf_translate/extract_segments.py`.

**Where it reaches:**
- A rotated run is placed from its origin along its direction
  (`direction_limit`), not from its box, so it draws the same.
- `right_limit` and `left_limit` read other segments' boxes as obstacles on
  the same row. So a horizontal neighbour of such a line gets less room.
- Warnings computed from boxes can change.
- The typography `extraction_id` covers the box, so it changes for an
  affected document.

**Red, then green:** `tests/test_multispan_box.py` has 2 tests:
- every angle's box equals the glyph union within 0.5 pt;
- the origin and direction are the first span's.

On v84 the first fails at exactly 135, 180 and 225 degrees.

## Independent verification (Rule 1)

Two passes on Sonnet, a different model, ran on archive trees of `4594b6a`
and `692e984` and printed which package each run imported.

**Identity sweep: confirmed.**
- **Extraction:** all 33 PDFs available, 17 wild and 16 corpus, were
  extracted in both trees. Of 99 output files, 98 are byte-identical. The
  one difference is the IRS W-9's segment 12, "See Specific Instructions
  on page 3.": a vertical line (dir (0, −1)) of 5 spans, three of them
  0.19 pt left of the first. Its box's left edge moved from 44.70 to 44.51,
  as intended.
- **Rebuilds:** all 13 `translate` corpus fixtures were rebuilt with an
  identity mapping in both trees. The PDFs are byte-identical with the
  trailer `/ID` masked, and so are the 150-dpi renders of every page.

**Adversarial pass: confirmed.**
- **Hostile angles:** at 100, 170, 180, 181, 190 and 260 degrees, a
  three-span 180-degree line with a superscript middle span, and a
  180-degree line mixing two fonts and sizes, the old box missed 30–70 pt
  and the new one matches the glyphs within 0.5 pt. A 359-degree line and a
  vertical two-span Japanese line are identical and correct in both trees.
- **A `+x` line cannot present the defect.** MuPDF splits a line into two
  the moment a later span would start left of the first. That was probed
  by sweeping a second span from −0.5 to −30 pt with TextWriter and with a
  raw `Td`.
- **The rotated run itself:** every rebuilt glyph origin and box is
  identical between trees.
- **A neighbour:** a horizontal "Label:" with a long Spanish translation
  sat on the same row as an upside-down two-span line. The old box let the
  label draw at 11 pt over the rotated line's glyphs by 21.4 pt. The fixed
  box shrinks it to about 9.7 pt, and 1.7 pt × 6.1 pt of overlap remains.
- **Typography:** the box and the `extraction_id` change for the
  180-degree fixture; the `occurrence_id` stays `s0`.
- **The full suite in both trees:** the failure sets are identical except
  the 3 new-test failures that only the old tree has. The 48 errors in
  both are archive artefacts: sibling `dev/` directories outside the
  archived subtree.

**Findings:**
- **Minor, not introduced here: the 1.7 pt residual overlap.** A neighbour's
  room is checked against the rotated segment's *source* box, not where
  its translation is drawn. It is filed as its own proposal.
- **Note:** a typography-1 mapping made for an affected document is
  refused as a stale extraction until it is extracted again. That is the
  intended fail-closed behaviour, and the upgrade note states it.

## Suite

CI's commands on macOS, on the fix:
- **Suite:** 800 tests (798 on v84, plus these 2), with 0 ResourceWarnings.
  The one failure is the known macOS-only
  `HotLoopTests.test_rebuild_resolves_verify_arguments_from_the_callers_directory`,
  and there is the right-to-left expected failure.
- **Canary, repository tests and eval fixtures:** all exit 0.
