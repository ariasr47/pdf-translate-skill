# Objective: a merge may take the box the author gives it

> Hand this to a `/goal` session. Self-contained. Read
> `scripts/retypeset.py` (the merge loop: how the rect is built from the
> member lines), `references/translations-format.md` (the `merges` block),
> and the run-2 records for Fable, Sonnet and Opus. Not FL-150.

---

## 1. Compass (not done)

A merge is re-flowed into the union bbox of its member lines. A two-line
English paragraph whose Spanish needs three lines therefore has two
outcomes, both seen tonight on the same fixture with empty space below the
paragraph: the engine shrinks it (Sonnet 0.81×, Opus 0.91×), or the author
declines the merge and translates line by line with the source's wrap
points hard-coded into the target (Fable, and Opus in run 1). Nothing in
the mapping lets the author say "this paragraph may be one line taller".

Geometry must not decide that — a box that grows into a rule or a field
is worse than a shrink — but the author can, and today cannot.

## 2. Done when — closed bar

1. **`merges[].box`** — an optional `[x0, y0, x1, y1]` in the original's
   page coordinates that replaces the union bbox as the re-flow rect.
   Absent: today's behaviour, unchanged. Present: the paragraph is placed
   in that rect at the original size and shrinks only if it does not fit
   *there*.
2. **The gate still counts.** The 0.7× floor, `allow_scale`, the
   placement gate and the canonical layer all apply to a boxed merge
   exactly as to any other.
3. **The extractor proposes, the author decides.** `propose-merges` adds
   `"box": null` to every proposal with a comment that a non-null box is
   the author's, and the merge-candidate warning's `why` says a longer
   translation may need one; nothing computes a box from geometry.
4. **Tests.** A two-line paragraph whose translation needs three lines:
   without `box` it scales below 1.0× (and, made long enough, fails at
   0.7×); with a box one line taller it places at 1.0× and the third line
   lands where the box says; a box that overlaps a widget still places
   (the author chose it) and the visual pass is the check, as the format
   doc must say.
5. `translations-format.md` documents `box`; full unittest + corpus
   green; `metadata.version` bumped.

## 3. Not done when

- Growing any box by geometry, or "into empty space" automatically
- Changing how the union bbox is computed for merges without a box
- A verify gate about boxes

## 4. Method

Constructed two-line paragraph; measure the scale today; add the key;
measure again.

## 5. Invariants

Geometry proposes, the author decides. The gates are unchanged.

## 6. Proof

The two placements on the fixture; the format doc; full unittest + corpus.

## 7. Closing note — 3 September 2026, closed

**Reproduced first, and measured before and after.** A two-line English
paragraph (420 pt page, 9 pt, union bbox ≈ y 52–77) whose Spanish needs
three lines, with empty space below it:

| | Result |
|---|---|
| no `box` | scales past the floor — **FAIL at 0.7×, no file saved** |
| `box: [40, 52, 380, 96]` (one line taller) | places at **1.0×**, three lines at y 52.1, 65.8 and 79.5 |

The third line lands below where the source's last line ended and inside
the rect the author drew. That is the choice run 2 did not have: Sonnet
and Opus shrank the same paragraph (0.81×, 0.91×), Fable declined the
merge and hard-coded the source's wrap points into the target.

**Done bar, item by item.**

1. **`merges[].box`** — `[x0, y0, x1, y1]` in the original's page
   coordinates, replacing the union bbox as the re-flow rect. Absent or
   null: unchanged. Malformed (not four numbers, empty or inverted) is
   refused by name rather than guessed at.
   One deliberate difference: a union bbox is a *measurement* of ink and
   runs tight, so retypeset pads it slightly; an authored box is an
   *instruction* and is used exactly as given.
2. **The gates still count.** Nothing about the merge path changed except
   which rect it re-flows into: the 0.7× floor applies inside the author's
   box, `allow_scale` still opts out, the placement gate and the canonical
   layer are untouched. The boxed build appears in row 25's
   `scale_report.json` like any other run — empty here, because it fits.
3. **The extractor proposes, the author decides.** `propose-merges` writes
   `"box": null` on every proposal and says so on stdout; the
   merge-candidate warning's `why` now mentions that a longer target may
   need a box you choose. Nothing computes a box from geometry.
4. **Tests** (`MergeBoxTests`, 5): no box → the 0.7× FAIL and no file; a
   box one line taller → 1.0×, three lines, the third below the source's
   last and inside the box; a box laid over a widget → still places (the
   author chose it); three malformed boxes → refused, named, no file; and
   proposals carry a null box.
5. `references/translations-format.md` documents `box` — what it is for,
   that no gate judges it, that the render is the check, and that every
   other gate still applies. 200 tests, no skips, green locally; corpus
   table unchanged. `metadata.version` 41 → 42.

**Wild corpus, re-run because the extractor changed** (17 files): every
verdict, segment count and warning count identical to
`dev/wild/results.json`. One difference, in `strip`'s diagnostic list and
not in any behaviour: two nested-XObject entries for page 17 of the IRS
1040 instructions (`/I2`, `/I3` — same page, same block counts, same
depth) come back in the opposite order. That list is built by iterating a
pikepdf `/XObject` dictionary, whose order this code does not pin; strip
was not touched by this row. Recorded here rather than fixed: it is a
reproducibility wart in a report, not a defect in an output.

Not done, as the brief asked: no box is grown by geometry or "into empty
space" automatically, the union bbox is computed exactly as before for
merges without a box, and there is no verify gate about boxes.
