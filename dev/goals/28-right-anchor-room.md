# Objective: a right-anchored run is measured against the room it will occupy

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (`right_limit`, the `maxw`/`fs2` computation and
> the `core in right` branch), `references/retypeset.md`, and
> `dev/canary/runs/2026-09-03-fable-5.1-fl100.md`. Not FL-150.

## 1. Compass (not done)

For a core in `right`, retypeset first computes the width budget as the
room to the *right* of the original origin (`right_limit − ox`) and
shrinks the run to that, then anchors the shrunk run on the original
right edge. A right-aligned label whose room is to its left — `SUCURSAL:`,
`CIUDAD Y C.P.:`, `Pág. N de 3` on FL-100 — is therefore scaled down when
it need not be, and the author must reword or accept small type.

## 2. Done when — closed bar

1. For a `right` core the budget is the room to the left of the original
   right edge: from the nearest same-row obstacle on the left (a segment's
   right edge, a widget's right edge, the page margin) to `bbox[2]`. The
   run is placed unscaled when it fits there; it shrinks only when it does
   not.
2. `center` and plain runs are unchanged; rotated runs unchanged.
3. Tests: a right-anchored label with free room to its left and a field
   immediately to its right — a longer translation lands at full size
   ending on the original edge; with a neighbour close on the left it
   shrinks to fit between; the existing `right` fixture unchanged.
4. Full unittest + corpus green; `metadata.version` bumped.

## 3. Not done when

- Proposing `right` for anything (row 21 owns that)
- Letting a right-anchored run overlap the obstacle on its left

## 4. Proof

The three placements on the fixture; full unittest + corpus.

## 5. Closing note — 3 September 2026, closed

**Reproduced first, with a before and after on the same fixture.** A
label `BRANCH:` whose right edge is 200.0, a text field from 204 to 400,
and 168 pt of empty page to its left; target `SUCURSAL Y CIUDAD:`, the
core listed in `right`. Driving the shipped stages with the pre-fix
`retypeset.py` and the fixed one, same fixture, same mapping:

| | Free room on the left | Neighbour ending at x=111 |
|---|---|---|
| before | **0.47× — FAIL, no file saved** | 0.47× — FAIL |
| after | **11.0 pt, full size**, right edge 200.0, left edge 88.5 | 8.64 pt (0.79×), right edge 200.0, left edge 112.5 |

The budget had been `right_limit − origin`: on a form that is the width of
the field the label names, which is exactly the space a right-anchored run
is not going to use.

**Done bar, item by item.**

1. A new `left_limit(pno, seg, segs)` mirrors `right_limit`: the nearest
   same-row obstacle's right edge — a segment's, a widget's — or the 32 pt
   page margin, plus the same 1.5 pt gap `right_limit` leaves. For a core
   in `right` the budget is `bbox[2] − left_limit(...)`; it is placed
   unscaled when it fits there and shrinks only when it does not. In the
   bounded case above the run starts at 112.5 against a limit of 112.5 —
   it stops exactly where it was told to.
2. `center`, plain and rotated runs are untouched: rotated still uses
   `direction_limit`, everything else still `right_limit − ox`. A test
   drives the same fixture and the same target *without* `right` and
   asserts the old 0.7× FAIL is still there.
3. **Tests** (`RightAnchorRoomTests`, 3): free room on the left → full
   size, right edge on the original's, nothing in the scaled digest;
   neighbour close on the left → shrinks, still ends on the original edge,
   starts at or after the neighbour's right edge, and *is* in the digest;
   the same label not in `right` → unchanged FAIL.
   `test_right_list_anchors_the_right_edge` (the existing `right` fixture)
   is untouched and passes.
4. `references/retypeset.md` says which side each alignment is measured
   against. 195 tests, no skips, green locally; corpus table unchanged.
   `metadata.version` 40 → 41.

Not done, as the brief asked: nothing new proposes `right` (row 21 owns
that), and the run is bounded by the obstacle on its left rather than
allowed to overlap it. One honest limit, the same one `right_limit` has
always had: the obstacle is measured on the **original's** geometry, so a
neighbour whose own translation grows can still crowd the gap. That is the
author's business and the visual pass's, not the budget's.
