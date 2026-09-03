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
