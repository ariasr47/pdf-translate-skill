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
