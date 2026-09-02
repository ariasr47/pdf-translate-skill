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

---

## 7. Closing note — 2 September 2026, closed

**Reproduced first.** A constructed page with `1. Body set in Times`
(Times, 14 pt) and `2. Body set in Courier` (Courier, 14 pt), translated,
bodies measured with per-character geometry. Before the change the Times
body landed 1.57 pt off and the Courier body 9.6 pt off, because the
marker is drawn in Helvetica and the body followed Helvetica's advance.
After: both within 0.5 pt (measured 0.00). The row-19 fixtures did not
move.

**Done bar, item by item.**

1. The segment records `body_dx`: the distance from the origin to the
   first glyph of the core, along the line direction, read from the
   annotation-free text page's own characters
   (`strip_text.page_rawdict_without_annots`, read once per page and
   only on pages that carry a marker). `gap` is untouched.
2. retypeset starts the body at `origin + body_dx` in every marker path —
   plain parts, inline markup, dot leaders, shaped, and rotated (the
   rotated writer takes an explicit advance per part). The marker keeps
   its Helvetica run at the origin. The offset scales with the run when
   it shrinks. Absent key: row-19 placement, locked by a test that drops
   the key and expects Helvetica's advance.
3. `MarkerFontMetricTests`: the extractor's offset equals the source
   font's own advance for `N. ` (Times and Courier, within 0.3 pt); both
   bodies land on the source x; the fallback. The row-19 fallback test now
   drops both keys, since a file from before row 19 has neither.
4. **Wild corpus, re-run with the shipped extractor:** every one of the
   952 marker segments with a body carries `body_dx`. Its difference from
   Helvetica's advance — the drift retypeset used to ship — by file:

   | Document | Marker lines | Median body_dx − Helvetica advance |
   |---|---|---|
   | IRS W-9, W-4; OPM SF-15; FDA 3500 | 114 | 0.00 pt |
   | Medicare & You | 18 | +1.27 pt |
   | USCIS I-9 | 36 | +2.22 pt |
   | IRS 1040-ES | 36 | +2.42 pt |
   | Judicial Council FL-100 | 2 | +3.09 pt |
   | IRS 1040 instructions | 253 | +3.88 pt |
   | Judicial Council FL-300 | 5 | +4.92 pt |
   | GDPR | 482 | −1.79 pt |

   Every count and verdict unchanged on all seventeen files. Extraction
   57.8 → 61.7 s in total; the 126-page booklet 26.0 s against 24.2 s,
   38.9 s end to end.
5. 174 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 34 → 35.

Not done, as the brief asked: the marker's font is still Helvetica;
`gap` is neither removed nor reinterpreted; no tab stops or hanging
indents are inferred; `MARKER` is unchanged.
