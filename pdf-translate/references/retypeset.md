# What retypeset does with a run — the mechanics behind step 5

Contents: glyph coverage · alignment and weight (`center`, `right`, the
four font roles, inline markup) · document metadata (`lang`, `/Title`,
outline, the structure tree) · rotated lines · the two ways a build fails.

`python3 scripts/retypeset.py stripped.pdf segments.json translations.json
out.pdf`. Every layout decision lives here so every document gets the same
behaviour; the script's own header lists them all.

## Glyph coverage

Every character of every placed run is checked against the exact font
object that will draw it. A character the font lacks **fails the build**:
MuPDF substitutes its own fallback face mid-string, or draws a box, and
reports nothing — the ink gate barely moves and the text layer still reads
correctly. Pick a font that covers the target script
(`references/fonts.md`); the run names the code points.

## Alignment and weight

`center` re-centers on the original midpoint; `right` re-anchors on the
original right edge, and is measured against the room on its **left** —
from the nearest same-row obstacle back there to the original right edge —
because that is where a longer translation goes. (A plain or `center` run
is still measured to the right of its origin.) Use `center` only where the source is centred in its
own box (a column header, a title): a caption flush with a rule or a field
is left-anchored, and centring a wider translation moves it off the thing
it labels — past every gate. `fonts` takes four roles — `regular`, `bold`,
`italic`, `bold_italic` — each falling back to the nearest one you named,
so a Times Italic source no longer comes back upright. A single-line
target may carry inline `<b>`/`<i>` for mixed weights within one line.

A list marker is re-emitted in Helvetica followed by the whitespace the
source printed after it, and the body starts at the offset the source's
own characters had, whatever the marker font (`gap` and `body_dx` in the
segment).

## Document metadata

Set `"lang"` in translations.json to the target BCP-47 tag: retypeset
writes it to `/Lang` and to `dc:language`, and without it the output
still tells screen readers, hyphenation and search that it is in the
source language. The `/Title` and every outline title are translated from
the mapping like any other core. The orphaned `/StructTreeRoot` is
removed and `/MarkInfo /Marked` set false, because those tags describe
text that was stripped — **say in the delivery that the file is no longer
tagged**.

## Rotated lines

Rotated lines (side labels, margin stamps) keep their angle: the extractor
records each line's direction and retypeset morphs the run about its own
origin, so origin, bbox and direction match the source. The width budget
runs along that direction. Dot leaders, `center` and the RTL mirror are
horizontal-only ideas and are skipped on a rotated run; a rotated run
whose target also needs shaping (Arabic, Indic, Thai…) is **refused**,
because the Story engine places shaped text upright and drawing it flat on
a rotated label ships confidently wrong text.

## The two ways a build fails

It fails loudly if any segment lacks a translation — fix and re-run until
it passes; that exit code is your coverage gate, and missing text must
never ship silently. It also **fails** (does not save) if any run scales
below 0.7× versus the original size — a note is not a ship. Shorten the
translation, or list that core (or merge first line) in `allow_scale` if
the cell must stay tiny.

Between those two, a run that shipped below source size is **reported**.
Every run the fit or the Story engine shrank — a line, a dot-leader label,
a shaped run, a merge, an override part — is printed after the build as
`scaled runs (N)` with its ratio and key, and written to
`scale_report.json` beside the output: `[{page, key, ratio}]`, page 0-based
as in the mapping.

The ratio is **source-relative**: it is the size the page actually shows
divided by the source's size, so you can measure it off the delivered PDF.
For a merge that means two things multiplied. A merge is always drawn at a
fit allowance of `0.98` of source size, rounded to the one decimal the CSS
carries, so the Story engine rarely has to shrink a paragraph that already
fits; whatever the engine then takes is applied on top. A 9.0 pt source
prints at 8.8 pt and reports `0.9778` even when the engine never touched it,
so **every merge appears in the report** and `verify --translations` REVIEWs
any job that has one. That is the honest floor for a re-flowed paragraph,
not a warning that something went wrong — read the ratios, not the count. `verify --translations` reads that file back and prints
a REVIEW line (a SKIP when the file is absent, for a build from before it
existed). Nothing new fails; the point is that the author can name what
shrank without re-running the build, which is what the delivery asks for.
