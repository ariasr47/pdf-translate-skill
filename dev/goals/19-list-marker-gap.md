# Objective: a list marker keeps the gap the source printed

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/extract_segments.py` (the `MARKER` regex and the segment dict),
> `scripts/retypeset.py` (every `marker + ' '`) and
> `dev/canary/runs/2026-09-02-opus-5.md`. Do not fix the `center` example
> (row 18) or the notice leak (row 20) in this sitting. Not FL-150.

---

## 1. Compass (not done)

The extractor peels a list marker off with `MARKER`, keeps
`marker = m.group(0).strip()`, and throws away the whitespace that followed
it. retypeset then re-emits `marker + ' '` — always exactly one space. Any
source that aligned its list bodies with more than one space loses the
alignment. Measured on the canary fixture, whose notes page uses `1.` plus
two spaces:

| marker | source gap | retypeset writes | shift |
|---|---|---|---|
| `1.` … `5.` | 15.29 pt | 12.23 pt | **3.06 pt left** |

Every gate passes. The text is placed, the ink barely moves, the layer
reads correctly — and five list bodies no longer line up with each other or
with anything else on the page. Opus 5 corrected it with five `overrides`
at measured columns, which is not a thing an author should have to do.

## 2. Done when — closed bar

1. **The gap survives.** A segment records the whitespace between marker and
   core (a new key — do not overload `marker`, it is a lookup key elsewhere).
   retypeset re-emits the source gap instead of one space.
2. **Old segments.json still works.** The key is absent in files written by
   earlier versions; fall back to one space, and say so in a comment. Never
   let a stale work directory crash a rebuild.
3. **Every placement path.** The marker is written in more than one branch
   (plain, dot-leader, shaped, rotated, override). Find them all; a grep for
   `marker` is the checklist.
4. **A test locks the measurement.** Constructed LTR list with a two-space
   gap: the core's x0 in the output equals the core's x0 in the original,
   within 0.5 pt. Confirm it fails before the fix.
5. **No regressions.** Full unittest + corpus green; the existing
   single-space list fixtures must not move at all.

## 3. Not done when

- Normalising the gap to some "nice" width
- Guessing tab stops or inferring a hanging indent
- Changing `MARKER` to match different markers
- Touching rows 18 or 20

## 4. Method

Constructed LTR PDF with `1.` + two spaces + body, and a second list with
one space. Import shipped extract/retypeset. Measure the body x0 against the
original in both.

## 5. Invariants

Provider-neutral. Geometry from the ORIGINAL. Placement at the original
origin. No glossary.

## 6. Proof

Body x0 matches the source before and after, for one-space and two-space
lists. Full unittest + corpus. Bump `metadata.version`.

---

## 7. Closing note — 2 September 2026, closed

**Reproduced first.** A constructed page with `1.  Two spaces after the
marker` and `2. One space after the marker` at 11 pt, both bodies
translated, through the shipped extract → strip → retypeset, measuring the
body's first glyph with per-character geometry (`rawdict`):

| line | source body x0 | output before | output after |
|---|---|---|---|
| two spaces | 87.29 | 84.23 (**3.06 pt left**, the canary's number exactly) | **87.29** |
| one space | 84.23 | 84.23 | **84.23** |

**Done bar, item by item.**

1. `extract_segments.py` records `gap`: the whitespace between the marker
   and the body, verbatim from the source text. `retypeset.py` builds
   `mk = marker + gap` once and writes it in every marker path — plain
   `parts` (which the rotated path consumes), inline markup, dot leaders,
   shaped — and includes it in the placed-characters list for the
   canonical text layer. No `marker + ' '` site is left.
2. A `segments.json` from before the key gets one space, with a comment
   saying why; `test_old_segments_without_gap_fall_back_to_one_space`
   builds from a file with the key deleted and asserts the pre-row-19
   placement (one Helvetica space short) — a stale work directory
   rebuilds rather than crashing.
3. The grep for `marker` was the checklist; overrides carry their own x
   and are untouched; verify's override-marker gate reads
   `seg['marker']` and is untouched.
4. `ListMarkerGapTests` (four tests) locks the extractor's key, the
   measurement within 0.5 pt, the fallback, and a multi-span line after a
   list item (see below). The two-space test failed by 3.06 pt before the
   fix.
5. 162 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 30 → 31.

**What the wild corpus added.** Re-running `dev/wild/probe.py` with the
new extractor into a scratch directory: 17/17 `translate`, and zero
segment, core, warning or verdict differences against the committed run.
Of 1,974 marker segments across the seventeen documents, **449 carry a
multi-space gap** (426 on the GDPR alone, 20 on SF-15, 2 three-space gaps
on the W-4), so this row is not a canary curiosity. The most common
real-world layout — marker and body far apart, as after a tab — arrives
as *two* segments and was already placed by geometry; it never needed
this row.

**A defect this sitting introduced and the corpus caught in seconds.**
The first version named the new local variable `gap`, which shadowed the
extractor's `gap` parameter — the span-merging threshold — so every
multi-span line after a list item raised `TypeError`. All 161 tests
passed, because every fixture line is a single span; all seventeen
corpus files crashed at once. Fixed by naming it `marker_gap`, with a
comment, and locked by
`test_multi_span_line_after_a_marker_still_extracts`, which was run
against the bug re-introduced in place (it fails with the same
`TypeError`) and against the fix (it passes). The lesson is on the
record: the constructed fixtures are single-span lines, and the corpus
re-run belongs in every sitting that touches extract.

**What the whitespace string cannot fix — row 23.** The marker is still
drawn in Helvetica, so the body starts at Helvetica's width of
`marker + gap`. Measured on the corpus with per-character geometry, actual
body x minus that advance on one-space lists: 0.00 pt on the W-9
(Helvetica-metric source), 1.27 pt on Medicare & You, 4.92 pt on
Judicial Council FL-300 — a pre-existing silent PASS with its own brief,
`goals/23-marker-font-metrics.md`, because only the measured position can
carry it.

Not done, as the brief asked: no normalising of the gap, no tab-stop or
hanging-indent inference, `MARKER` unchanged, rows 18 and 20 untouched.
