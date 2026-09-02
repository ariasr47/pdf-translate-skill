# Objective: `center` must stop recommending itself for signature captions

> Hand this to a `/goal` session. Self-contained. Read
> `references/translations-format.md` (the `center` block),
> `scripts/retypeset.py` (the `core in center` branch) and
> `dev/canary/runs/2026-09-02-haiku-4.5.md`. Do not build a verify gate.
> Do not touch `right`. Not FL-150.

---

## 1. Compass (not done)

`translations-format.md` offers `center` for *"column headers, titles,
signature captions"*. A signature caption sits **left-flush under a rule**;
centring it on the original bbox midpoint moves it. Haiku 4.5 read that
example, put `Signature of parent or guardian` and `Date` in `center`, and
shipped this:

| | original x0 | output x0 |
|---|---|---|
| signature caption | 72.0 (flush with the rule at 72) | **64.5** |
| date caption | 360.0 (flush with the rule at 360) | **357.2** |

The Spanish caption is wider, so centring pushed it out both sides and it
now overhangs the left end of its own rule by 7.5 pt. Every gate passed.
The model followed the documentation and got a worse page: **the example is
the defect.**

## 2. Done when — closed bar

1. **The example is corrected.** `center` is for a run whose source is
   centred *in its own box* — a column header over a column, a title over a
   page. Say plainly that a caption flush with a rule or a field is
   **left-anchored**, and that centring it moves it off the thing it labels.
   Name the failure so the next reader recognises it.
2. **SKILL.md agrees.** The alignment paragraph in step 5 says the same in
   one sentence.
3. **A test locks the geometry claim**, not the prose: a left-flush caption
   whose translation is wider, placed with `center`, ends up left of the
   source x0; placed without it, at the source x0. This is the measurement
   that makes the doc change true, and it will keep being true.
4. **No regressions.** Full unittest + corpus green.

## 3. Not done when

- A verify gate for centred runs (see §5)
- Changing what `center` *does*
- Auto-detecting alignment
- Touching `right` (it is correct; the extractor proposes it)

## 4. Method

Constructed LTR PDF: a rule from x=72, a caption at x=72 under it, a
translation ~15 pt wider. Drive shipped retypeset twice, with and without
`center`. Assert the x0s.

## 5. The softer question — decide, then stop

A `center`ed run that ends up **wider than its source bbox** now covers
space the source did not. For a genuine centred title that is correct and
wanted, so it can never be a hard gate. It could be an extractor warning,
or nothing. **Decide in one paragraph in this brief's closing note and do
not build it in this sitting.**

## 6. Invariants

Provider-neutral. Geometry-only. No glossary. Warnings propose, authors
decide.

## 7. Proof

The two x0 measurements, the corrected example, full unittest + corpus.
