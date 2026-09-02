# Objective: a list body starts at the measured source x, whatever the marker font

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/extract_segments.py` (the segment construction and
> `page_textdict_without_annots`), `scripts/retypeset.py` (every use of
> `mk`, the marker plus gap), `dev/goals/19-list-marker-gap.md` (closing
> note) and `dev/wild/ANALYSIS.md`. Do not change what row 19 records; add
> to it. Not FL-150.

---

## 1. Compass (not done)

Row 19 made retypeset re-emit the whitespace the source printed after a
list marker. The marker itself is still drawn in Helvetica, so the body
starts at `origin + Helvetica width(marker + gap)`: exact when the source
marker was Helvetica-metric, and off by the metric difference otherwise.
Measured on the wild corpus with per-character geometry (`rawdict`),
actual body x minus the Helvetica advance, one-space lists:

| Document | n | median drift |
|---|---|---|
| IRS W-9 (Helvetica-metric) | 40 | 0.00 pt |
| Medicare & You | 17 | 1.27 pt |
| Judicial Council FL-300 | 5 | 4.92 pt |

Every gate passes at 4.9 pt; the bodies of a list simply do not line up
with the rule or the checkbox column they used to. The whitespace string
cannot carry this; only the measured position can.

## 2. Done when — closed bar

1. **The segment records where the body starts.** A new key (for example
   `body_dx`: the distance from the segment origin to the first glyph of
   the core, along the line direction, in the original) measured from
   per-character geometry of the annotation-free text page, not computed
   from any font. `gap` stays as row 19 left it.
2. **retypeset starts the body there.** Every marker path (plain, inline
   markup, dot leaders, shaped, rotated) places the body at
   `origin + body_dx` when the key is present; the marker keeps its
   Helvetica run at the origin. Absent key: row 19 behaviour, unchanged.
3. **A test locks the metric case.** Constructed fixture whose marker
   font is not Helvetica-metric (Times, `pymupdf.Font('tiro')`): the body
   x in the output equals the body x in the original within 0.5 pt, and
   fails before the fix by the metric difference. The row 19 fixtures do
   not move.
4. **Measured on the wild corpus.** Re-run the drift measurement from
   `dev/wild/ANALYSIS.md` on the rebuilt segments; medians in the closing
   note.
5. **No regressions.** Full unittest + corpus green; extraction time on
   the 126-page booklet stays within a few seconds of 37 s.
   `metadata.version` bumped.

## 3. Not done when

- Changing the marker's font (it stays Helvetica; that is a separate
  question about pass-through fonts)
- Removing or reinterpreting `gap`
- Inferring tab stops or hanging indents
- Any change to `MARKER`

## 4. Method

Times fixture with `1. body` at 11 pt; measure body x in the original with
`rawdict`; confirm the drift today; record the position at extract time;
place; re-measure.

## 5. Invariants

Provider-neutral. Geometry from the ORIGINAL. Placement at the original
origin. Old work directories still build.

## 6. Proof

The Times fixture within 0.5 pt; row 19 fixtures unchanged; the corpus
medians before and after; full unittest + corpus.
