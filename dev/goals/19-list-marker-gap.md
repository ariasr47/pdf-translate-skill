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
