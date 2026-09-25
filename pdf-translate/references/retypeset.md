# What retypeset does with a run — the mechanics behind step 5

Contents: glyph coverage · alignment and weight (`center`, `right`, the
four font roles, inline markup) · document metadata (`lang`, `/Title`,
outline, the structure tree) · rotated lines · every way a build fails.

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

"Rotated" means rotated in the PDF, not on screen. `segments.json` and
every drawing call use the page's unrotated space, so text that reads
across a portrait page with `/Rotate 90` is an ordinary horizontal run. It
gets every feature, and it is measured against the unrotated page, 612 pt
wide rather than the 792 pt of the rotated view. On a landscape page whose
content is counter-rotated to read upright under `/Rotate`, the text is
vertical in the PDF. So every run on it takes this rotated-run path, with
its limits. `failure-modes.md` §13 has the history and the stale-extraction
refusal.

## Every way a build fails

A legacy build refuses for nine kinds of reason. A refused build exits 1
and saves nothing, not even `scale_report.json`, so the output and report
from an earlier build stay on disk as they were: read the exit code, not
whether the file exists. The console prints a `FAIL:` block naming every
refused item; an unmatched merge prints one `!!` line instead. Called from
Python, the refusal is a typed exception whose `refusals` holds every
refused item by kind (`references/consumer-guide.md`).

The checks run in the table's order, and the build stops at the first one
that refuses. Two groups are checked together, and every item of every kind
in them is listed at once: `untranslated` with `unauthored_merges`, and
`overflow` with `glyph_misses` and `rotated_shaped`. In the second group a
missing glyph decides the exception: the build raises `GlyphError`, which
is not a `PlacementError`, and its `refusals` still carries every overflow
and rotated run. Catch `PdfTranslateError` and read `refusals`, or catch
`GlyphError` first.

| `refusals` kind | exception | what refused | fix |
|---|---|---|---|
| `output_aliases` | `MappingError` | the output PDF or scale report would overwrite an input: the stripped PDF, `segments.json`, the mapping, the original or a font | write it somewhere else |
| `stale_extraction` | `MappingError` | `segments.json` names no geometry space and a `/Rotate` page carries segments: it was extracted before v64 (`failure-modes.md` §13) | run extract again |
| `merges` | `MappingError` | a merge's `lines` are not found on its page in order, or its `box` is not four numbers or is empty | copy the lines from `segments.json`; fix the box |
| `untranslated` | `MappingError` | a segment's core has no translation | author it |
| `unauthored_merges` | `MappingError` | a merge's `html` is still `null`, as `propose-merges --accept` leaves it | author the paragraph, or delete the entry |
| `notices` | `PlacementError` | a notice's text is empty, its page is not in the document, or its box is not four numbers or is empty | fix the notice |
| `overflow` | `PlacementError`, or `GlyphError` with a glyph miss | a run scaled below 0.7× of its source size | shorten it; see below |
| `glyph_misses` | `GlyphError` | the face that draws a run lacks one of its characters (glyph coverage, above) | use a font that covers the script |
| `rotated_shaped` | `PlacementError`, or `GlyphError` with a glyph miss | a rotated run's target needs shaping (rotated lines, above) | none draws it rotated: `skip` the span, which drops it, and say so in the delivery |

A missing translation fails loudly: that exit code is your coverage gate,
and missing text must never ship silently. A run below 0.7× is refused
too, because a note is not a ship. Shorten the translation, or list that
core (or a merge's first line) in `allow_scale` if the cell must stay
tiny. A mapping that does not load refuses before any of these, and a
typography-1 mapping has its own refusals (`references/typography.md`).

Short of a refusal, a run that shipped below source size is **reported**.
Every run the fit or the Story engine shrank — a line, a dot-leader label,
a shaped run, a merge, an override part — is printed after the build as
`scaled runs (N)` with its ratio and key, and written to
`scale_report.json` beside the output:

```json
{"schema": 1, "version": "…", "runs": [{"page": 0, "key": "…", "ratio": 0.9778}]}
```

`version` is the library version that wrote the file, and `page` is
0-based, as in the mapping. A build before v58 wrote the bare `runs` list,
and `verify --translations` still reads it. A typography-1 build writes
schema 2, with a `typography` block (`references/typography.md`).

The ratio is **source-relative**: it is the size the page actually shows
divided by the source's size, so you can measure it off the delivered PDF.
A shrunk line, leader label or override part is drawn at exactly the size
that fits its room, and never larger than its source. There is no minimum:
small print can go below 4 pt, and the gate sees that ratio. Until v65
every shrink was lifted to 4 pt. So a source of 5.71 pt or less was drawn
past its room onto its neighbour and passed the 0.7× floor it had failed,
and a source under 4 pt came out larger than it was (`failure-modes.md`
§15).
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

## Capturing evidence when a run refuses below the floor

B1 (wrapping a translation onto a second line, instead of only shrinking or
refusing) cannot be planned because nobody has a real failed job to measure
recovery against — three attempts came back empty, because a refusal used to
print a message and exit without saving anything else
(`docs/reviews/2026-09-19-b1-recovery-probe.md`). Opt in with `capture_dir=`
on `run_retypeset`/`retypeset`, `--capture-dir DIR` on this script, or the
`PDF_TRANSLATE_CAPTURE_DIR` environment variable (checked only when neither
of those is given), and a refusal caused **specifically** by a run scaling
below `SCALE_MIN` writes a timestamped, self-contained, replayable bundle
under that directory: a copy of the source PDF (when `original` was given;
`pipeline.py rebuild` always gives it) and the stripped PDF, the segments and the authored mapping (with its font
paths rewritten to the copies bundled alongside it), the structured refusal
(`exc.to_dict()`, so the command and library version travel with it), the
affected occurrence's page and geometry, and whether a caller-authored box
is on record for it — `null` with a note when it is not, never a guess.

### When your floor is not our floor

`SCALE_MIN` is 0.7, and only a run under it refuses. A consumer holding a
higher floor — say 0.75, applied in its own code — watches a build **succeed**
at 0.72, reverts that core itself, and ships the paragraph in the source
language. Nothing refused, so a hook keyed to a refusal never sees the case
that actually cost them.

`capture_below=RATIO` (or `--capture-below RATIO`, or
`PDF_TRANSLATE_CAPTURE_BELOW`) names that band. With it set, a build that
succeeds still writes **one** bundle for the job when any run landed at or
under the ratio, listing every such core. Unset — the default — only a
refusal captures, which is the behaviour described above and the only
behaviour before this existed.

One bundle per job, keyed by core, not one per run: a core can be scaled
more than once in a pass, and the fact worth keeping is whether it could be
made to fit at all, so the worst ratio it reached is the one recorded. The
manifest's `kind` says which sort of bundle you are holding (`refusal` or
`near-floor`), and `refusal` is `null` on the latter because nothing was
refused.

This is opt-in and off by default on purpose: copying a customer's source
PDF to disk is a side effect nobody should get by surprise. **Off, nothing
about this command changes** — same console output, same exit code, same
files; that parity is enforced by `dev/probes/cli_parity_runner.py`. A
problem writing the bundle (a bad path, a full disk, a permissions error)
is logged and swallowed — it can never mask, replace, or change the
refusal that follows it. See `pdf_translate/capture.py` for the bundle
format, and `references/consumer-guide.md` for the Python-API shape of
`capture_dir=`.

This collects evidence only. It does not implement B1 — no line wrapping,
no placement change, no new rendering — and it never runs unless a refusal
is exactly a below-the-floor scale, the same condition the paragraph above
this one already fails on.
